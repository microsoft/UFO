# Device Disconnection Handling - Implementation Summary

## 概述

本文档描述了 agent server 断连时的完整处理流程，包括状态更新、自动重连和错误处理。

## 🔍 断连检测机制

### 1. WebSocket 连接监控
- **位置**: `MessageProcessor._handle_device_messages()`
- **触发条件**:
  - `websockets.ConnectionClosed` 异常
  - 其他未预期的异常

### 2. 心跳超时检测
- **位置**: `HeartbeatManager._heartbeat_loop()`
- **触发条件**: 心跳发送失败或设备无响应

## 🔄 断连处理流程

### 阶段 1: 检测断连
```
WebSocket 连接关闭
    ↓
MessageProcessor._handle_device_messages() 捕获异常
    ↓
调用 _handle_disconnection(device_id)
```

### 阶段 2: 本地清理
```
MessageProcessor._handle_disconnection()
    ↓
1. 停止心跳监控
    ↓
2. 调用 DeviceManager._handle_device_disconnection()
```

### 阶段 3: 设备管理器处理
```
DeviceManager._handle_device_disconnection()
    ↓
1. 停止消息处理器
2. 更新设备状态为 DISCONNECTED
3. 清理 WebSocket 连接
4. 取消正在执行的任务（如果有）
5. 通知断连事件处理器
6. 判断是否需要重连
```

### 阶段 4: 自动重连（如果符合条件）
```
判断: connection_attempts < max_retries
    ↓ (是)
调用 _schedule_reconnection(device_id)
    ↓
等待 reconnect_delay 秒
    ↓
调用 connect_device(device_id)
    ↓
成功 → 重置 connection_attempts
失败 → 递增 connection_attempts，继续重试
```

## 📋 状态转换图

```
CONNECTED/IDLE/BUSY
    ↓ (断连检测)
DISCONNECTED
    ↓ (connection_attempts < max_retries)
CONNECTING
    ↓ (重连成功)
CONNECTED → IDLE
    ↓ (重连失败 && 超过重试次数)
FAILED
```

## 💡 关键功能

### 1. 断连后更新设备状态 ✅

**实现位置**: `DeviceManager._handle_device_disconnection()`

```python
# 更新设备状态为 DISCONNECTED
self.device_registry.update_device_status(device_id, DeviceStatus.DISCONNECTED)
```

**状态流转**:
- `CONNECTED/IDLE/BUSY` → `DISCONNECTED`

### 2. 自动尝试重连按照设定 ✅

**实现位置**: `DeviceManager._handle_device_disconnection()`

**重连条件**:
```python
if device_info.connection_attempts < device_info.max_retries:
    self._schedule_reconnection(device_id)
```

**重连参数**:
- `max_retries`: 最大重试次数（默认 5 次）
- `reconnect_delay`: 重连延迟（默认 5 秒）
- `connection_attempts`: 当前连接尝试次数

**重连流程**:
1. 等待 `reconnect_delay` 秒
2. 调用 `connect_device(device_id)`
3. 递增 `connection_attempts`
4. 如果成功，重置 `connection_attempts` 为 0

### 3. 重连后更新设备状态 ✅

**实现位置**: `DeviceManager.connect_device()` 和 `_reconnect_device()`

**成功重连**:
```python
# 1. 更新状态为 CONNECTING
self.device_registry.update_device_status(device_id, DeviceStatus.CONNECTING)

# 2. 建立连接
await self.connection_manager.connect_to_device(...)

# 3. 更新状态为 CONNECTED
self.device_registry.update_device_status(device_id, DeviceStatus.CONNECTED)

# 4. 设置为 IDLE（准备接受任务）
self.device_registry.set_device_idle(device_id)

# 5. 重置连接尝试次数
self.device_registry.reset_connection_attempts(device_id)
```

**失败重连**:
```python
# 如果超过最大重试次数
if device_info.connection_attempts >= device_info.max_retries:
    self.device_registry.update_device_status(device_id, DeviceStatus.FAILED)
```

## 🔧 任务处理

### 正在执行的任务

断连时，如果设备正在执行任务：

```python
current_task_id = device_info.current_task_id
if current_task_id:
    # 标记任务失败
    error = ConnectionError(f"Device {device_id} disconnected during task execution")
    self.task_queue_manager.fail_task(device_id, current_task_id, error)
    # 清除当前任务
    device_info.current_task_id = None
```

### 队列中的任务

- **保留策略**: 队列中的任务会被保留
- **重连后**: 设备重连后会自动处理队列中的任务
- **手动取消**: 可以调用 `shutdown()` 取消所有队列任务

## 📊 事件通知

### 断连事件

```python
await self.event_manager.notify_device_disconnected(device_id)
```

### 重连事件

```python
await self.event_manager.notify_device_connected(device_id, device_info)
```

## 🛡️ 错误处理

### 异常捕获

所有断连处理都包含在 try-except 块中：

```python
try:
    # 断连处理逻辑
    ...
except Exception as e:
    self.logger.error(f"❌ Error handling disconnection for device {device_id}: {e}")
```

### 日志记录

完整的日志追踪：
- `🔌 Connection to device {device_id} closed` - 检测到断连
- `🔌 Device {device_id} disconnected, cleaning up...` - 开始清理
- `🔄 Scheduling reconnection for device {device_id}` - 调度重连
- `🔄 Attempting to reconnect to device {device_id}` - 尝试重连
- `✅ Successfully reconnected to device {device_id}` - 重连成功
- `❌ Device {device_id} exceeded max reconnection attempts` - 超过重试次数

## 📝 使用示例

### 注册设备并启用自动重连

```python
# 初始化设备管理器（设置重连参数）
device_manager = ConstellationDeviceManager(
    task_name="my_task",
    heartbeat_interval=30.0,  # 心跳间隔
    reconnect_delay=5.0,      # 重连延迟
)

# 注册设备（max_retries 在 DeviceRegistry 中设置，默认 5 次）
await device_manager.register_device(
    device_id="device_1",
    server_url="ws://localhost:8000",
    os="Windows",
    auto_connect=True,
)
```

### 监听断连和重连事件

```python
async def on_disconnect(device_id: str):
    print(f"Device {device_id} disconnected!")

async def on_reconnect(device_id: str, device_info):
    print(f"Device {device_id} reconnected!")

device_manager.add_disconnection_handler(on_disconnect)
device_manager.add_connection_handler(on_reconnect)
```

### 检查设备状态

```python
status = device_manager.get_device_status("device_1")
print(f"Status: {status['status']}")
print(f"Connection attempts: {status['connection_attempts']}/{status['max_retries']}")
```

## 🎯 改进要点

相比之前的实现，新的断连处理机制提供了：

1. ✅ **完整的状态管理**: 断连时立即更新状态为 `DISCONNECTED`
2. ✅ **自动重连**: 按照 `max_retries` 和 `reconnect_delay` 配置自动重连
3. ✅ **状态同步**: 重连成功后自动更新状态为 `CONNECTED` → `IDLE`
4. ✅ **任务处理**: 断连时自动取消正在执行的任务
5. ✅ **事件通知**: 通过 EventManager 通知所有监听器
6. ✅ **连接计数**: 跟踪连接尝试次数，成功后自动重置
7. ✅ **清理机制**: 停止心跳、消息处理器等后台服务

## 🔍 测试建议

### 场景 1: 正常断连重连
1. 启动设备并连接
2. 手动关闭 UFO server
3. 观察断连检测和状态更新
4. 重启 UFO server
5. 验证自动重连和状态恢复

### 场景 2: 超过重试次数
1. 设置 `max_retries=2`
2. 关闭 UFO server
3. 观察 2 次重连尝试
4. 验证最终状态为 `FAILED`

### 场景 3: 任务执行中断连
1. 分配长时间运行的任务
2. 在任务执行过程中关闭 server
3. 验证任务被标记为失败
4. 验证队列中的任务被保留

### 场景 4: 快速重连
1. 关闭 server 后立即重启
2. 验证第一次重连尝试成功
3. 验证 `connection_attempts` 被重置为 0

## 📚 相关代码文件

- `galaxy/client/device_manager.py` - 主要协调器
- `galaxy/client/components/message_processor.py` - 消息处理和断连检测
- `galaxy/client/components/device_registry.py` - 设备状态管理
- `galaxy/client/components/connection_manager.py` - WebSocket 连接管理
- `galaxy/client/components/heartbeat_manager.py` - 心跳监控
- `galaxy/client/components/event_manager.py` - 事件通知
