# 设备断连完整流程说明

## ✅ 是的！你的理解完全正确

当设备断连时，系统会**同时**进行三件事：

1. ✅ **状态被改变** - 设备状态从 IDLE/BUSY → DISCONNECTED
2. ✅ **开始自动重连** - 根据配置（最多5次，间隔5秒）自动尝试重连
3. ✅ **正在跑的任务立刻返回 FAILED** - 返回 `ExecutionResult(status=FAILED)` 而不是抛出异常

---

## 📊 完整流程图

### 场景：设备正在执行任务时突然断连

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 任务正在执行                                                  │
│    - 设备状态: BUSY                                              │
│    - TaskStar.execute() 等待结果                                 │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. WebSocket 断开连接                                            │
│    - websockets.ConnectionClosed 异常                            │
│    - 发生在 connection_manager.send_task_to_device()             │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. ConnectionManager 转换异常                                    │
│    - 捕获 websockets.ConnectionClosed                           │
│    - 抛出 ConnectionError                                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├──────────────────────────────────────┐
                 │                                      │
                 ▼                                      ▼
┌────────────────────────────────────┐  ┌──────────────────────────────────┐
│ 4a. MessageProcessor 检测到断连     │  │ 4b. DeviceManager 捕获异常       │
│     (在消息循环中)                  │  │     (在 _execute_task_on_device)│
│                                    │  │                                  │
│  - 调用 _handle_disconnection()    │  │  - except ConnectionError        │
│  - 触发 _disconnection_handler     │  │  - 创建 ExecutionResult(FAILED)  │
│    回调                            │  │  - result.metadata.disconnected  │
└─────────────┬──────────────────────┘  │    = True                       │
              │                         │  - 返回失败结果                  │
              ▼                         └────────────┬─────────────────────┘
┌────────────────────────────────────┐               │
│ 5. DeviceManager 处理断连           │               │
│    (_handle_device_disconnection)  │               │
│                                    │               │
│  - 停止消息处理器                   │               │
│  - 更新状态: BUSY → DISCONNECTED    │◄──────────────┘
│  - 清理连接                        │
│  - 取消当前任务 (fail_task)         │
│  - 通知事件管理器                   │
│  - 安排自动重连                     │
└─────────────┬──────────────────────┘
              │
              ├────────────────────────────────┐
              │                                │
              ▼                                ▼
┌────────────────────────────┐  ┌─────────────────────────────────┐
│ 6a. 任务立刻返回 FAILED     │  │ 6b. 开始自动重连                 │
│                            │  │                                 │
│  TaskStar.execute() 收到:  │  │  - 等待 5 秒                    │
│  ExecutionResult(          │  │  - 调用 connect_device()        │
│    status=FAILED,          │  │  - 最多尝试 5 次                │
│    metadata={              │  │                                 │
│      disconnected: True,   │  │  成功:                          │
│      error_category:       │  │    - 重置连接次数               │
│        "connection_error"  │  │    - 状态: DISCONNECTED →       │
│    }                       │  │            CONNECTING →         │
│  )                         │  │            CONNECTED → IDLE     │
│                            │  │                                 │
│  - 可以检查 disconnected   │  │  失败:                          │
│    标志                    │  │    - 继续重试                   │
│  - 可以实现重试逻辑        │  │    - 超过5次后状态变为 FAILED   │
└────────────────────────────┘  └─────────────────────────────────┘
```

---

## 🔍 关键代码位置

### 1. 任务执行时捕获断连异常

**文件**: `galaxy/client/device_manager.py`  
**方法**: `_execute_task_on_device()` (行 363-506)

```python
async def _execute_task_on_device(
    self, device_id: str, task_request: TaskRequest
) -> ExecutionResult:
    try:
        # 设置设备为 BUSY
        self.device_registry.set_device_busy(device_id, task_request.task_id)
        
        # 执行任务
        result = await self.connection_manager.send_task_to_device(
            device_id, task_request
        )
        
        return result
        
    except ConnectionError as e:
        # 🔴 设备断连 - 立刻返回 FAILED
        self.logger.error(
            f"❌ Device {device_id} disconnected during task {task_request.task_id}: {e}"
        )
        
        result = ExecutionResult(
            task_id=task_request.task_id,
            status=TaskStatus.FAILED,
            error=str(e),
            result={
                "error_type": "device_disconnection",
                "message": f"Device {device_id} disconnected during task execution",
                "device_id": device_id,
                "task_id": task_request.task_id,
            },
            metadata={
                "device_id": device_id,
                "disconnected": True,  # 🔍 关键标志
                "error_category": "connection_error",
            },
        )
        
        # 通知任务队列管理器任务失败
        self.task_queue_manager.fail_task(device_id, task_request.task_id, e)
        
        return result  # 返回失败结果，不抛出异常
        
    finally:
        # 设备回到 IDLE 状态
        self.device_registry.set_device_idle(device_id)
```

### 2. 断连处理和自动重连

**文件**: `galaxy/client/device_manager.py`  
**方法**: `_handle_device_disconnection()` (行 208-278)

```python
async def _handle_device_disconnection(self, device_id: str) -> None:
    """设备断连时的清理和重连逻辑"""
    
    # 1️⃣ 停止消息处理器
    self.message_processor.stop_message_handler(device_id)
    
    # 2️⃣ 更新设备状态为 DISCONNECTED
    self.device_registry.update_device_status(
        device_id, DeviceStatus.DISCONNECTED
    )
    
    # 3️⃣ 清理连接
    await self.connection_manager.disconnect_device(device_id)
    
    # 4️⃣ 取消当前任务（如果有）
    current_task_id = device_info.current_task_id
    if current_task_id:
        self.logger.warning(
            f"⚠️ Device {device_id} was executing task {current_task_id}, "
            f"marking as failed"
        )
        error = ConnectionError(
            f"Device {device_id} disconnected during task execution"
        )
        self.task_queue_manager.fail_task(device_id, current_task_id, error)
        device_info.current_task_id = None
    
    # 5️⃣ 通知断连事件
    await self.event_manager.notify_device_disconnected(device_id)
    
    # 6️⃣ 安排自动重连（如果未超过重试次数）
    if device_info.connection_attempts < device_info.max_retries:
        self.logger.info(
            f"🔄 Scheduling reconnection for device {device_id} "
            f"(attempt {device_info.connection_attempts + 1}/{device_info.max_retries})"
        )
        self._schedule_reconnection(device_id)  # 开始重连
    else:
        self.logger.error(
            f"❌ Device {device_id} exceeded max reconnection attempts, giving up"
        )
        self.device_registry.update_device_status(device_id, DeviceStatus.FAILED)
```

### 3. 重连逻辑

**文件**: `galaxy/client/device_manager.py`  
**方法**: `_reconnect_device()` (行 286-307)

```python
async def _reconnect_device(self, device_id: str) -> None:
    """自动重连设备"""
    try:
        # ⏰ 等待 5 秒后重连
        await asyncio.sleep(self.reconnect_delay)  # 默认 5.0 秒
        
        self.logger.info(f"🔄 Attempting to reconnect to device {device_id}")
        
        # 尝试重新连接
        success = await self.connect_device(device_id)
        
        if success:
            self.logger.info(f"✅ Successfully reconnected to device {device_id}")
            # ✨ 重连成功 - 重置连接次数
            self.device_registry.reset_connection_attempts(device_id)
            # 状态变化: DISCONNECTED → CONNECTING → CONNECTED → IDLE
        else:
            self.logger.error(f"❌ Failed to reconnect to device {device_id}")
            # 重试会继续（直到达到 max_retries）
            
    except Exception as e:
        self.logger.error(f"❌ Reconnection failed for device {device_id}: {e}")
    finally:
        self._reconnect_tasks.pop(device_id, None)
```

---

## 📋 状态转换详解

### 正常执行任务

```
IDLE → BUSY → IDLE
```

### 任务执行中断连

```
BUSY → DISCONNECTED → CONNECTING → CONNECTED → IDLE
 ↓                      (5秒后)      (重连成功)
任务立刻返回 FAILED
```

### 断连后重连失败（超过5次）

```
BUSY → DISCONNECTED → CONNECTING → DISCONNECTED → ... → FAILED
 ↓                      (尝试1)       (失败)            (第5次)
任务立刻返回 FAILED
```

---

## 🎯 三件事的时间线

假设设备在 `t=0` 时刻断开连接：

| 时间 | 发生的事情 |
|------|-----------|
| **t=0** | WebSocket 连接断开 |
| **t=0.001** | ❶ MessageProcessor 检测到断连，调用 `_handle_device_disconnection()` |
| **t=0.002** | ❷ 状态更新: BUSY → **DISCONNECTED** |
| **t=0.003** | ❸ 正在执行的任务收到 ConnectionError |
| **t=0.004** | ❹ 任务**立刻返回** `ExecutionResult(status=FAILED, disconnected=True)` |
| **t=0.005** | ❺ 安排重连任务（将在 5 秒后执行） |
| **t=5.000** | ❻ **第1次重连尝试** |
| **t=5.100** | ❼ 重连成功 → 状态: DISCONNECTED → CONNECTING → CONNECTED → **IDLE** |
| **t=5.101** | ❽ 连接次数重置为 0，设备可以接收新任务 |

---

## ✅ 验证结果

### 测试覆盖

所有 5 个测试全部通过：

```
✅ test_device_disconnection_during_task_execution_returns_failed_result
   - 验证断连返回 FAILED + disconnected=True

✅ test_task_timeout_returns_failed_result_with_timeout_info
   - 验证超时返回 FAILED + timeout 信息

✅ test_websocket_connection_closed_exception_during_task
   - 验证 WebSocket 异常正确转换

✅ test_general_exception_returns_failed_result
   - 验证一般错误返回 FAILED

✅ test_successful_task_execution_returns_completed_result
   - 验证成功情况仍然正常工作
```

### 关键验证点

1. ✅ **任务返回 FAILED 而不是抛出异常**
   ```python
   result = await device_manager.assign_task_to_device(...)
   assert result.status == TaskStatus.FAILED
   # 不需要 try-except！
   ```

2. ✅ **包含断连标志**
   ```python
   assert result.metadata["disconnected"] is True
   assert result.metadata["error_category"] == "connection_error"
   ```

3. ✅ **错误信息完整**
   ```python
   assert result.result["error_type"] == "device_disconnection"
   assert "disconnected" in result.result["message"].lower()
   ```

---

## 💡 使用示例

### 在 TaskStar.execute() 中检查断连

```python
async def execute(
    self, device_manager: ConstellationDeviceManager
) -> ExecutionResult:
    """执行任务，自动处理断连"""
    
    result = await device_manager.assign_task_to_device(
        task_id=self.task_id,
        device_id=self.target_device_id,
        task_description=self.to_request_string(),
        task_data=self.task_data or {},
        timeout=self._timeout or 1000.0,
    )
    
    # ✅ 方法1: 检查 disconnected 标志（最简单）
    if result.metadata.get("disconnected"):
        self.logger.error(f"❌ 设备断连，任务失败")
        # 系统会自动重连，可以考虑重试任务
        
    # ✅ 方法2: 检查 error_type
    elif result.result and result.result.get("error_type") == "device_disconnection":
        self.logger.error(f"❌ 设备断连类型错误")
        
    return result
```

---

## 🔧 配置参数

这些参数控制断连处理行为：

```python
device_manager = ConstellationDeviceManager(
    task_name="my_task",
    heartbeat_interval=30.0,    # 心跳间隔（秒）
    reconnect_delay=5.0,        # 重连延迟（秒）- 每次重试等待时间
)

# 设备级别配置
device_info.max_retries = 5     # 最大重连次数（默认5次）
```

---

## 📊 总结

### ✅ 是的，你的理解 100% 正确！

当设备断连时：

1. **状态会被改变** ✅
   - BUSY → DISCONNECTED (立刻)
   - DISCONNECTED → CONNECTING → CONNECTED → IDLE (重连成功后)

2. **开始自动重连** ✅
   - 等待 5 秒后开始第一次重连
   - 最多尝试 5 次
   - 成功后重置计数器

3. **正在跑的任务立刻返回 FAILED** ✅
   - 不抛出异常，返回 `ExecutionResult(status=FAILED)`
   - `metadata.disconnected = True` 标识是断连导致
   - `result.error_type = "device_disconnection"` 说明错误类型

### 🎯 设计优势

- **不需要 try-except** - 统一通过 ExecutionResult 返回
- **信息丰富** - 可以区分断连、超时、一般错误
- **自动恢复** - 断连后自动重连，不需要手动干预
- **任务可靠** - 立刻通知任务失败，避免长时间等待

---

**文档日期**: 2025-10-24  
**实现版本**: v2.0  
**测试状态**: ✅ 5/5 全部通过
