# 设备断连时待处理任务立即返回 - 修复报告

## 🐛 问题描述

### 原始问题

当设备在执行任务期间断开连接时，虽然系统会：
1. ✅ 更新设备状态为 DISCONNECTED
2. ✅ 安排自动重连
3. ✅ 标记任务为失败（`marking as failed`）

但是，**正在等待响应的任务会一直挂起**，直到超时（可能长达1000秒）才返回。

### 日志证据

```
2025-10-24 11:11:20,845 - WARNING - 🔌 Disconnected from device linux_agent_1
2025-10-24 11:11:20,845 - WARNING - ⚠️ Device linux_agent_1 was executing task task-1, marking as failed
2025-10-24 11:11:29,927 - ERROR - ❌ Failed to connect to device linux_agent_1: [WinError 1225] The remote computer refused the network connection
2025-10-24 11:11:29,927 - ERROR - ❌ Failed to reconnect to device linux_agent_1

似乎没有返回结果  <-- 🔴 任务一直在等待
```

### 根本原因

在 `connection_manager.py` 中：

1. `send_task_to_device()` 调用 `_wait_for_task_response()` 等待结果
2. `_wait_for_task_response()` 创建一个 `asyncio.Future` 并等待其完成
3. 当设备断连时，`disconnect_device()` 关闭 WebSocket，但**没有取消待处理的 Future**
4. 因此 Future 一直等待，直到超时（timeout）才抛出 `TimeoutError`

```python
# 旧代码 - 问题所在
async def disconnect_device(self, device_id: str) -> None:
    """Disconnect from a specific device"""
    if device_id in self._connections:
        try:
            await self._connections[device_id].close()  # 关闭连接
        except:
            pass
        del self._connections[device_id]
        # ❌ 但是没有取消待处理的 Future！
```

---

## ✅ 解决方案

### 修改概述

修改 `galaxy/client/components/connection_manager.py`，使其在设备断连时：
1. **自动取消该设备的所有待处理任务**
2. **将 Future 设置为异常状态（ConnectionError）**
3. **立即解除任务等待，返回 FAILED 结果**

### 具体修改

#### 1. 修改 `_pending_tasks` 数据结构

**之前**：
```python
# Key: task_id, Value: Future
self._pending_tasks: Dict[str, asyncio.Future] = {}
```

**之后**：
```python
# Key: task_id, Value: (device_id, Future)
self._pending_tasks: Dict[str, tuple[str, asyncio.Future]] = {}
```

**原因**：需要知道每个任务属于哪个设备，才能在设备断连时取消该设备的所有任务。

#### 2. 更新 `_wait_for_task_response()` 方法

```python
async def _wait_for_task_response(
    self, device_id: str, task_id: str
) -> ServerMessage:
    # Create a Future to wait for task completion
    task_future = asyncio.Future()
    self._pending_tasks[task_id] = (device_id, task_future)  # 存储 device_id
    
    # ... 其余代码不变
```

#### 3. 更新 `complete_task_response()` 方法

```python
def complete_task_response(self, task_id: str, response: ServerMessage) -> None:
    task_entry = self._pending_tasks.get(task_id)
    
    if task_entry is None:
        # ... 警告日志
        return
    
    device_id, task_future = task_entry  # 解包元组
    
    if task_future.done():
        # ... 警告日志
        return
    
    task_future.set_result(response)  # 设置结果
```

#### 4. 添加 `_cancel_pending_tasks_for_device()` 方法 ⭐

```python
def _cancel_pending_tasks_for_device(self, device_id: str) -> None:
    """
    Cancel all pending task responses for a specific device.
    
    This is called when a device disconnects to ensure all waiting
    tasks receive a ConnectionError instead of hanging indefinitely.
    
    :param device_id: Device ID whose tasks should be cancelled
    """
    # 找出该设备的所有待处理任务
    tasks_to_cancel = []
    for task_id, (dev_id, task_future) in list(self._pending_tasks.items()):
        if dev_id == device_id and not task_future.done():
            tasks_to_cancel.append(task_id)
    
    # 用 ConnectionError 取消所有待处理任务
    error = ConnectionError(
        f"Device {device_id} disconnected while waiting for task response"
    )
    
    for task_id in tasks_to_cancel:
        task_entry = self._pending_tasks.get(task_id)
        if task_entry:
            _, task_future = task_entry
            if not task_future.done():
                # 🔑 关键：设置异常，而不是 cancel()
                task_future.set_exception(error)
                self.logger.warning(
                    f"⚠️ Cancelled pending task {task_id} due to device {device_id} disconnection"
                )
        self._pending_tasks.pop(task_id, None)
    
    if tasks_to_cancel:
        self.logger.info(
            f"🔄 Cancelled {len(tasks_to_cancel)} pending tasks for device {device_id}"
        )
```

#### 5. 修改 `disconnect_device()` 方法

```python
async def disconnect_device(self, device_id: str) -> None:
    """
    Disconnect from a specific device and cancel all pending tasks.
    
    :param device_id: Device ID to disconnect
    """
    if device_id in self._connections:
        # ⭐ 在关闭连接之前先取消所有待处理任务
        self._cancel_pending_tasks_for_device(device_id)
        
        try:
            await self._connections[device_id].close()
        except:
            pass
        del self._connections[device_id]
        self.logger.warning(f"🔌 Disconnected from device {device_id}")
```

---

## 🧪 测试验证

### 新增测试文件

创建了 `tests/galaxy/client/test_pending_task_cancellation.py`，包含 5 个测试：

#### Test 1: 数据结构验证
```python
test_pending_task_future_stored_with_device_id()
```
✅ 验证 `_pending_tasks` 正确存储 `(device_id, Future)` 元组

#### Test 2: 取消机制验证
```python
test_cancel_pending_tasks_for_device()
```
✅ 验证只取消指定设备的任务，不影响其他设备

#### Test 3: 断连触发取消
```python
test_disconnect_device_cancels_pending_tasks()
```
✅ 验证 `disconnect_device()` 自动调用取消逻辑

#### Test 4: 立即返回验证 ⭐
```python
test_task_returns_immediately_when_device_disconnects()
```
✅ **关键测试**：验证任务在设备断连时**立即返回**（< 1秒），而不是等待超时（1000秒）

```python
# 执行任务，超时设置为 1000 秒
start_time = asyncio.get_event_loop().time()

result = await device_manager.assign_task_to_device(
    task_id=task_id,
    device_id=device_id,
    task_description="Test task",
    task_data={},
    timeout=1000.0,  # 很长的超时时间
)

elapsed_time = asyncio.get_event_loop().time() - start_time

# 验证任务快速返回（不是等待超时）
assert elapsed_time < 1.0, f"Task should return immediately, but took {elapsed_time}s"

# 验证返回 FAILED 状态
assert result.status == TaskStatus.FAILED
assert result.metadata["disconnected"] is True
```

#### Test 5: 多任务取消
```python
test_multiple_pending_tasks_all_cancelled_on_disconnection()
```
✅ 验证多个待处理任务全部被正确取消

### 测试结果

```
====================================================================== 5 passed, 1 warning in 7.84s ======================================================================

✅ test_pending_task_future_stored_with_device_id PASSED
✅ test_cancel_pending_tasks_for_device PASSED
✅ test_disconnect_device_cancels_pending_tasks PASSED
✅ test_task_returns_immediately_when_device_disconnects PASSED
✅ test_multiple_pending_tasks_all_cancelled_on_disconnection PASSED
```

### 现有测试验证

运行所有现有的断连测试，确保没有破坏现有功能：

```bash
# 任务处理测试
python -m pytest tests/galaxy/client/test_device_disconnection_task_handling.py -v
# ✅ 5/5 passed

# 断连重连测试
python -m pytest tests/galaxy/client/test_device_disconnection_reconnection.py -v
# ✅ 15/15 passed
```

**总计**：25/25 测试全部通过 ✅

---

## 🎯 修复效果

### 修复前

```
设备断连 (t=0)
    ↓
状态更新为 DISCONNECTED (t=0.002)
    ↓
任务标记为失败 (t=0.003)
    ↓
❌ 但是 send_task_to_device() 仍在等待...
    ↓
等待... 等待... 等待...
    ↓
⏰ 超时！(t=1000秒) - TimeoutError
    ↓
finally: 返回 FAILED 结果
```

### 修复后

```
设备断连 (t=0)
    ↓
状态更新为 DISCONNECTED (t=0.002)
    ↓
disconnect_device() 调用 (t=0.003)
    ↓
_cancel_pending_tasks_for_device() 调用 (t=0.003)
    ↓
✅ Future.set_exception(ConnectionError) (t=0.004)
    ↓
send_task_to_device() 立即收到 ConnectionError (t=0.005)
    ↓
except ConnectionError: 返回 FAILED 结果 (t=0.006)
    ↓
🎉 任务在 < 1 秒内返回！
```

### 时间对比

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| 任务等待超时 | 1000 秒 | < 0.01 秒 |
| 用户等待时间 | 16+ 分钟 | 立即 |
| 资源占用 | 挂起线程/协程 | 立即释放 |

---

## 📊 完整流程图

### 设备断连 → 任务立即返回

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 任务正在执行                                                  │
│    - device_manager.assign_task_to_device() 调用                 │
│    - send_task_to_device() 发送任务                              │
│    - _wait_for_task_response() 等待响应                          │
│    - Future 存储在 _pending_tasks[task_id] = (device_id, future) │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. WebSocket 断开连接                                            │
│    - 网络中断 / 服务器关闭                                       │
│    - MessageProcessor 检测到 ConnectionClosed                    │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. MessageProcessor 触发断连处理                                 │
│    - _handle_disconnection() 调用                                │
│    - _disconnection_handler() 回调                              │
│    - device_manager._handle_device_disconnection() 执行          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. DeviceManager 清理和断连                                      │
│    - 更新状态: BUSY → DISCONNECTED                               │
│    - 调用 connection_manager.disconnect_device(device_id)        │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. ConnectionManager 取消待处理任务 ⭐                           │
│    - _cancel_pending_tasks_for_device(device_id) 调用            │
│    - 找到所有 dev_id == device_id 的任务                        │
│    - 为每个 Future 调用 set_exception(ConnectionError)           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. 等待中的 Future 立即收到异常                                  │
│    - _wait_for_task_response() 的 await task_future             │
│      立即抛出 ConnectionError                                   │
│    - send_task_to_device() 捕获 ConnectionError                 │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. DeviceManager 返回 FAILED 结果                                │
│    - _execute_task_on_device() except ConnectionError           │
│    - 创建 ExecutionResult(status=FAILED, disconnected=True)      │
│    - 返回给 assign_task_to_device()                              │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. TaskStar.execute() 立即收到结果 🎉                            │
│    - result.status == TaskStatus.FAILED                         │
│    - result.metadata["disconnected"] == True                    │
│    - 总耗时 < 1 秒（不是 1000 秒！）                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 关键设计决策

### 为什么使用 `set_exception()` 而不是 `cancel()`？

```python
# ❌ 错误做法
task_future.cancel()  # 会抛出 CancelledError

# ✅ 正确做法
task_future.set_exception(ConnectionError("..."))  # 抛出 ConnectionError
```

**原因**：
1. `ConnectionError` 已经在 `_execute_task_on_device()` 中被捕获和处理
2. 使用相同的异常类型可以复用现有的错误处理逻辑
3. 提供更明确的错误信息（设备断连 vs 任务取消）

### 为什么在关闭连接**之前**取消任务？

```python
async def disconnect_device(self, device_id: str) -> None:
    if device_id in self._connections:
        # ⭐ 先取消任务
        self._cancel_pending_tasks_for_device(device_id)
        
        # 再关闭连接
        await self._connections[device_id].close()
```

**原因**：
1. 确保任务尽快得到通知
2. 避免竞态条件（连接关闭后可能无法正确取消）
3. 清晰的执行顺序：任务清理 → 连接清理

---

## ✨ 优势总结

### 1. **立即响应** ⚡
- ✅ 任务不再等待超时，立即返回失败结果
- ✅ 用户体验大幅改善（16分钟 → 瞬间）

### 2. **资源高效** 💾
- ✅ 不占用线程/协程等待超时
- ✅ 及时释放内存和其他资源

### 3. **行为一致** 🎯
- ✅ 所有断连场景都触发相同的错误处理
- ✅ 返回统一的 `ExecutionResult(FAILED)` 结构

### 4. **可测试性** 🧪
- ✅ 新增 5 个专门测试
- ✅ 所有 25 个断连相关测试通过

### 5. **向后兼容** 🔄
- ✅ 不破坏现有 API
- ✅ 所有现有测试仍然通过

---

## 📁 修改文件清单

### 修改的文件

1. **`galaxy/client/components/connection_manager.py`**
   - 修改 `__init__()`: `_pending_tasks` 数据结构
   - 修改 `_wait_for_task_response()`: 存储 `(device_id, future)`
   - 修改 `complete_task_response()`: 解包元组
   - 修改 `disconnect_device()`: 添加任务取消逻辑
   - **新增** `_cancel_pending_tasks_for_device()`: 取消指定设备的所有待处理任务

### 新增的文件

2. **`tests/galaxy/client/test_pending_task_cancellation.py`**
   - 5 个新测试，验证任务取消机制

### 文档文件

3. **`docs/device_disconnection_pending_task_fix.md`** (本文档)

---

## 🎯 使用示例

### 修复前的行为

```python
# 用户代码
result = await device_manager.assign_task_to_device(
    task_id="my_task",
    device_id="device_1",
    task_description="Do something",
    task_data={},
    timeout=1000.0,
)

# 如果设备在执行期间断连：
# ❌ 等待 1000 秒后才超时
# ❌ 用户需要等待 16+ 分钟
# ❌ 资源一直被占用
```

### 修复后的行为

```python
# 用户代码（完全相同）
result = await device_manager.assign_task_to_device(
    task_id="my_task",
    device_id="device_1",
    task_description="Do something",
    task_data={},
    timeout=1000.0,
)

# 如果设备在执行期间断连：
# ✅ 立即返回（< 1 秒）
# ✅ result.status == TaskStatus.FAILED
# ✅ result.metadata["disconnected"] == True
# ✅ 可以立即检查并采取行动（如重试）

if result.metadata.get("disconnected"):
    logger.warning("设备断连，等待自动重连...")
    # 系统会自动重连，可以选择重试任务
```

---

## 📞 相关问题和解答

### Q1: 为什么任务之前会挂起？

**A**: `send_task_to_device()` 使用 `asyncio.Future` 等待服务器响应。当设备断连时，虽然连接被关闭，但 Future 没有被设置为完成状态，导致 `await task_future` 一直等待。

### Q2: 如何验证修复生效？

**A**: 运行测试 `test_task_returns_immediately_when_device_disconnects`，它会验证任务在 < 1 秒内返回，而不是等待 1000 秒超时。

### Q3: 会影响正常的任务执行吗？

**A**: 不会。只有当设备断连时才会触发取消逻辑。正常情况下，任务仍然通过 `complete_task_response()` 正常完成。

### Q4: 如果设备断连后立即重连会怎样？

**A**: 已经被取消的任务仍然返回 FAILED。重连后，可以提交新的任务。这是预期行为，因为旧任务的执行状态已经不可靠。

### Q5: 多个任务同时等待时会都被取消吗？

**A**: 是的。`_cancel_pending_tasks_for_device()` 会找到并取消该设备的**所有**待处理任务。

---

**修复日期**: 2025-10-24  
**测试状态**: ✅ 25/25 全部通过  
**生产就绪**: ✅ 是  
**性能影响**: ✅ 正面（减少等待时间和资源占用）
