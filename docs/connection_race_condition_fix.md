# WebSocket 连接竞态条件修复

## 问题描述

**症状**: WebSocket 连接在注册后立即断开,导致无法发送任务。问题不是必现,是一个竞态条件。

**根本原因**: 
客户端在建立 WebSocket 连接和启动消息处理器之间存在时间窗口:

```
时间线问题:
T1: connect_to_device() 建立连接
T2: _register_constellation_client() 发送注册消息
T3: 服务器收到注册,发送 HEARTBEAT 确认
T4: [竞态窗口] - 如果此时没有监听器,消息丢失
T5: connect_to_device() 返回到 device_manager
T6: device_manager.connect_device() 启动 message_processor ❌ 太晚了!
T7: 服务器因为没收到心跳响应而断开连接
```

**为什么不是必现**:
- 如果服务器响应慢,MessageProcessor 在消息到达前就启动了 → ✅ 成功
- 如果服务器响应快,消息在 MessageProcessor 启动前到达 → ❌ 失败

## 解决方案

**在建立连接后、发送注册消息前启动 MessageProcessor**,确保所有服务器响应都能被及时处理。

### 修改内容

#### 1. `connection_manager.py` - `connect_to_device()` 方法

**修改前**:
```python
async def connect_to_device(
    self, device_info: AgentProfile
) -> WebSocketClientProtocol:
    websocket = await websockets.connect(...)
    self._connections[device_info.device_id] = websocket
    
    # 发送注册消息
    success = await self._register_constellation_client(device_info, websocket)
    return websocket
```

**修改后**:
```python
async def connect_to_device(
    self, device_info: AgentProfile, message_processor=None
) -> WebSocketClientProtocol:
    websocket = await websockets.connect(...)
    self._connections[device_info.device_id] = websocket
    
    # ⚠️ CRITICAL: Start message handler BEFORE sending registration
    if message_processor:
        message_processor.start_message_handler(device_info.device_id, websocket)
        await asyncio.sleep(0.05)  # 确保监听器已启动
    
    # 发送注册消息
    success = await self._register_constellation_client(device_info, websocket)
    return websocket
```

#### 2. `connection_manager.py` - `_register_constellation_client()` 方法

**修改前**:
```python
await websocket.send(registration_message.model_dump_json())

# 等待服务器响应验证注册
registration_success = await self._validate_registration_response(
    websocket, constellation_client_id, device_info.device_id
)

return registration_success
```

**修改后**:
```python
await websocket.send(registration_message.model_dump_json())

# ⚠️ 不等待响应 - MessageProcessor 会处理它
# 这避免了竞态条件,如果注册失败,服务器会关闭连接
self.logger.debug(
    f"📝 Registration sent, MessageProcessor will handle response"
)

return True
```

#### 3. `device_manager.py` - `connect_device()` 方法

**修改前**:
```python
# 建立连接
websocket = await self.connection_manager.connect_to_device(device_info)

# 更新状态
self.device_registry.update_device_status(device_id, DeviceStatus.CONNECTED)

# 启动消息处理器 ❌ 太晚了!
self.message_processor.start_message_handler(device_id, websocket)
self.heartbeat_manager.start_heartbeat(device_id)
```

**修改后**:
```python
# 建立连接,传入 message_processor
websocket = await self.connection_manager.connect_to_device(
    device_info, 
    message_processor=self.message_processor  # ✅ 在注册前启动
)

# 更新状态
self.device_registry.update_device_status(device_id, DeviceStatus.CONNECTED)

# ⚠️ Message handler already started in connect_to_device()
# 不再重复启动
# self.message_processor.start_message_handler(device_id, websocket)
self.heartbeat_manager.start_heartbeat(device_id)
```

## 新的时间线(修复后)

```
T1: connect_to_device() 建立连接
T2: start_message_handler() 启动监听 ✅ 在注册前启动
T3: asyncio.sleep(0.05) 确保监听器就绪
T4: _register_constellation_client() 发送注册消息
T5: 服务器收到注册,发送 HEARTBEAT 确认
T6: MessageProcessor 收到并处理 HEARTBEAT ✅ 不会丢失
T7: 连接保持稳定,可以接收后续消息
```

## 测试验证

修复后应该:
1. ✅ 连接不再随机断开
2. ✅ 注册响应能正确接收
3. ✅ 心跳机制正常工作
4. ✅ 可以稳定发送和接收任务

## 相关文件

- `galaxy/client/components/connection_manager.py` - 连接管理器
- `galaxy/client/device_manager.py` - 设备管理器
- `galaxy/client/components/message_processor.py` - 消息处理器

## 日期

2025-10-15
