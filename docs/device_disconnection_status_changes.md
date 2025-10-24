# 设备断连时的状态变化详解

## ✅ 是的，断连设备状态**会改变**！

## 📊 完整的状态流转图

```
┌─────────────────────────────────────────────────────────────┐
│                    正常运行状态                              │
│  CONNECTED (已连接) / IDLE (空闲) / BUSY (执行任务中)        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ 🔌 检测到断连
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    立即更新状态                              │
│              DISCONNECTED (已断连)                           │
│  📍 代码位置: device_manager.py:232                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ 判断: connection_attempts < max_retries?
                         │
            ┌────────────┴────────────┐
            │ YES                     │ NO
            ↓                         ↓
┌───────────────────────┐  ┌──────────────────────┐
│   调度自动重连        │  │   放弃重连           │
│   CONNECTING          │  │   FAILED             │
│   📍 line 140         │  │   📍 line 183/263    │
└──────┬────────────────┘  └──────────────────────┘
       │
       │ 尝试连接
       │
       ├──────┬──────────┐
       │ 成功 │          │ 失败
       ↓      │          ↓
┌──────────────┐    ┌─────────────────┐
│  CONNECTED   │    │ connection_     │
│  📍 line 152 │    │ attempts++      │
└──────┬───────┘    │ 继续重试        │
       │            └────────┬────────┘
       ↓                     │
┌──────────────┐            │
│    IDLE      │            │
│  准备接受    │←───────────┘
│  新任务      │   (直到成功或超过max_retries)
│  📍 line 173 │
└──────────────┘
```

## 🔍 关键代码位置

### 1. 断连时更新为 DISCONNECTED

**文件**: `galaxy/client/device_manager.py`  
**行号**: 230-233

```python
# Update device status to DISCONNECTED
self.device_registry.update_device_status(
    device_id, DeviceStatus.DISCONNECTED
)
```

**触发条件**:
- WebSocket 连接关闭 (`ConnectionClosed`)
- 消息处理异常
- 手动断连

### 2. 重连时更新为 CONNECTING

**文件**: `galaxy/client/device_manager.py`  
**行号**: 138-141

```python
# Update status and increment attempts
self.device_registry.update_device_status(
    device_id, DeviceStatus.CONNECTING
)
```

**触发条件**:
- 自动重连触发
- 手动调用 `connect_device()`

### 3. 连接成功更新为 CONNECTED

**文件**: `galaxy/client/device_manager.py`  
**行号**: 151-153

```python
# Update status to connected
self.device_registry.update_device_status(device_id, DeviceStatus.CONNECTED)
self.device_registry.update_heartbeat(device_id)
```

### 4. 设置为 IDLE（准备接受任务）

**文件**: `galaxy/client/device_manager.py`  
**行号**: 172-174

```python
# Set device to IDLE (ready to accept tasks)
self.device_registry.set_device_idle(device_id)
```

### 5. 超过重试次数更新为 FAILED

**文件**: `galaxy/client/device_manager.py`  
**行号**: 259-264

```python
else:
    self.logger.error(
        f"❌ Device {device_id} exceeded max reconnection attempts "
        f"({device_info.max_retries}), giving up"
    )
    self.device_registry.update_device_status(device_id, DeviceStatus.FAILED)
```

## 📋 状态定义

所有状态定义在 `galaxy/client/components/types.py`:

```python
class DeviceStatus(str, Enum):
    """Device connection status"""
    DISCONNECTED = "disconnected"    # 未连接
    CONNECTING = "connecting"        # 连接中
    CONNECTED = "connected"          # 已连接
    IDLE = "idle"                    # 空闲（已连接且可接受任务）
    BUSY = "busy"                    # 忙碌（正在执行任务）
    FAILED = "failed"                # 失败（超过最大重试次数）
```

## 🎯 状态变化时间线示例

假设设备在执行任务时断连：

```
T0: 设备正常运行
    └─ 状态: BUSY (正在执行 task_001)

T1: 检测到断连 (WebSocket ConnectionClosed)
    └─ 状态: BUSY → DISCONNECTED
    └─ 任务: task_001 被标记为失败
    └─ 日志: 🔌 Device device_001 disconnected, cleaning up...

T2: 清理完成，调度重连 (reconnect_delay = 5秒)
    └─ 状态: DISCONNECTED
    └─ 连接尝试: 0 → 1
    └─ 日志: 🔄 Scheduling reconnection...

T3: 开始重连尝试 (5秒后)
    └─ 状态: DISCONNECTED → CONNECTING
    └─ 日志: 🔄 Attempting to reconnect to device device_001

T4: 重连成功
    └─ 状态: CONNECTING → CONNECTED → IDLE
    └─ 连接尝试: 1 → 0 (重置)
    └─ 日志: ✅ Successfully reconnected to device device_001

T5: 准备接受新任务
    └─ 状态: IDLE
    └─ 可以分配新任务
```

## 🧪 测试验证

测试文件已验证所有状态变化：

**文件**: `tests/galaxy/client/test_device_disconnection_reconnection.py`

### 测试 1: 断连后状态更新
```python
async def test_disconnection_updates_status():
    # 初始状态: IDLE
    assert device_info.status == DeviceStatus.IDLE
    
    # 触发断连
    await device_manager._handle_device_disconnection(device_id)
    
    # 验证状态: DISCONNECTED
    assert device_info.status == DeviceStatus.DISCONNECTED
```
✅ **通过**

### 测试 2: 重连后状态更新
```python
async def test_reconnection_updates_status_to_idle():
    # 断连状态
    device_info.status = DeviceStatus.DISCONNECTED
    
    # 重连
    success = await device_manager.connect_device(device_id)
    
    # 验证状态: IDLE
    assert device_info.status == DeviceStatus.IDLE
```
✅ **通过**

### 测试 3: 超过重试次数
```python
async def test_max_retry_limit_stops_reconnection():
    # 设置连接尝试次数 = max_retries
    device_info.connection_attempts = device_info.max_retries
    
    # 触发断连
    await device_manager._handle_device_disconnection(device_id)
    
    # 验证状态: FAILED
    assert device_info.status == DeviceStatus.FAILED
```
✅ **通过**

## 📊 状态查询方法

可以通过以下方法查询设备状态：

### 1. 获取设备信息
```python
device_info = device_manager.get_device_info(device_id)
print(f"状态: {device_info.status}")
print(f"连接尝试: {device_info.connection_attempts}/{device_info.max_retries}")
```

### 2. 获取设备状态（详细）
```python
status = device_manager.get_device_status(device_id)
print(f"状态: {status['status']}")
print(f"连接尝试: {status['connection_attempts']}")
print(f"最大重试: {status['max_retries']}")
print(f"当前任务: {status['current_task_id']}")
```

### 3. 检查是否连接
```python
connected_devices = device_manager.get_connected_devices()
is_connected = device_id in connected_devices
```

## 🔔 事件通知

状态变化时会触发事件通知：

### 断连事件
```python
# 在 _handle_device_disconnection() 中
await self.event_manager.notify_device_disconnected(device_id)
```

### 重连事件
```python
# 在 connect_device() 中
await self.event_manager.notify_device_connected(device_id, device_info)
```

### 注册事件监听器
```python
# 监听断连
async def on_disconnect(device_id: str):
    print(f"设备 {device_id} 已断连")
    # 检查状态
    status = device_manager.get_device_status(device_id)
    print(f"当前状态: {status['status']}")  # 输出: DISCONNECTED

device_manager.add_disconnection_handler(on_disconnect)

# 监听重连
async def on_reconnect(device_id: str, device_info):
    print(f"设备 {device_id} 已重连")
    print(f"当前状态: {device_info.status}")  # 输出: IDLE

device_manager.add_connection_handler(on_reconnect)
```

## ✅ 总结

**回答您的问题**：是的，断连时设备状态**一定会改变**！

1. ✅ **断连时**: 立即更新为 `DISCONNECTED`
2. ✅ **重连时**: 更新为 `CONNECTING`
3. ✅ **成功后**: 更新为 `CONNECTED` → `IDLE`
4. ✅ **失败后**: 更新为 `FAILED`（如果超过重试次数）

**保证**:
- ✅ 状态更新是**同步的**，断连时立即执行
- ✅ 状态变化会触发**事件通知**
- ✅ 所有状态变化都有**日志记录**
- ✅ 已通过**15个测试**验证

**查看详细实现**:
- 📄 `galaxy/client/device_manager.py` (行 230-233, 138-141, 151-153, 172-174, 259-264)
- 📊 `docs/device_disconnection_handling.md`
- 🧪 `tests/galaxy/client/test_device_disconnection_reconnection.py`

---

**最后更新**: 2025-10-24  
**测试状态**: ✅ 15/15 通过
