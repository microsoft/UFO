# AIP 设备通信快速参考

## 服务器端 (UFOWebSocketHandler)

### 初始化 AIP 协议
```python
# 在 connect() 方法中
self.transport = WebSocketTransport(websocket)
self.registration_protocol = RegistrationProtocol(self.transport)
self.heartbeat_protocol = HeartbeatProtocol(self.transport)
self.device_info_protocol = DeviceInfoProtocol(self.transport)
self.task_protocol = TaskExecutionProtocol(self.transport)
```

### 处理心跳
```python
async def handle_heartbeat(self, data: ClientMessage, websocket: WebSocket):
    await self.heartbeat_protocol.send_heartbeat()
```

### 处理设备信息请求
```python
async def handle_device_info_request(self, data: ClientMessage, websocket: WebSocket):
    device_info = await self.get_device_info(data.target_id)
    await self.device_info_protocol.send_device_info_response(
        device_info=device_info, 
        request_id=data.request_id
    )
```

## 客户端 (UFOWebSocketClient)

### 初始化 AIP 协议
```python
# 在 connect_and_listen() 中
self.transport = WebSocketTransport(ws)
self.registration_protocol = RegistrationProtocol(self.transport)
self.heartbeat_protocol = HeartbeatProtocol(self.transport)
self.task_protocol = TaskExecutionProtocol(self.transport)
```

### 注册客户端
```python
async def register_client(self):
    metadata = {...}  # 设备信息
    await self.registration_protocol.register_as_device(
        client_id=self.ufo_client.client_id,
        metadata=metadata
    )
```

### 发送心跳
```python
async def heartbeat_loop(self, interval: float = 30):
    while True:
        await asyncio.sleep(interval)
        await self.heartbeat_protocol.send_heartbeat()
```

### 发送任务结果
```python
async def handle_commands(self, server_response: ServerMessage):
    action_results = await self.ufo_client.execute_step(server_response)
    
    await self.task_protocol.send_task_result(
        session_id=self.session_id,
        prev_response_id=server_response.response_id,
        action_results=action_results,
        status=task_status,
        client_id=self.ufo_client.client_id
    )
```

## Command Dispatcher (WebSocketCommandDispatcher)

### 初始化
```python
def __init__(self, session: "BaseSession", ws: WebSocket):
    self.transport = WebSocketTransport(ws)
    self.protocol = TaskExecutionProtocol(self.transport)
```

### 执行命令
```python
async def execute_commands(self, commands: List[Command], timeout: float = 6000):
    server_message = self.make_server_response(commands)
    fut = asyncio.get_event_loop().create_future()
    self.pending[server_message.response_id] = fut
    
    # 使用 AIP 协议发送
    await self.protocol.send_command(server_message)
    
    # 等待结果
    result = await asyncio.wait_for(fut, timeout)
    return result
```

### 设置结果
```python
async def set_result(self, response_id: str, result: ClientMessage):
    fut = self.pending.get(response_id)
    if fut and not fut.done():
        fut.set_result(result.action_results)
```

## 常见模式

### 错误处理
```python
try:
    await self.protocol.send_command(server_message)
except Exception as e:
    self.logger.error(f"[AIP] Error sending commands: {e}")
    return self.generate_error_results(commands, e)
```

### 日志记录
```python
self.logger.info(f"[AIP] Sent commands via TaskExecutionProtocol: {response_id}")
self.logger.debug(f"[AIP] Heartbeat sent")
self.logger.error(f"[AIP] Error sending commands: {error}")
```

## 测试

### Mock WebSocket
```python
class MockWebSocket:
    def __init__(self):
        self.sent_messages = []
    
    async def send_text(self, message: str):
        self.sent_messages.append(message)
```

### 测试 Dispatcher
```python
mock_ws = MockWebSocket()
dispatcher = WebSocketCommandDispatcher(mock_session, mock_ws)

# 手动设置为已连接
from aip.transport.base import TransportState
dispatcher.transport._state = TransportState.CONNECTED

commands = [Command(...)]
await dispatcher.execute_commands(commands, timeout=1.0)

# 验证消息已发送
assert len(mock_ws.sent_messages) > 0
```

## 调试提示

1. **查找 AIP 日志**: 搜索 `[AIP]` 标记
2. **检查连接状态**: `transport._state`
3. **验证消息格式**: 使用 `Message.model_validate_json()`
4. **追踪 response_id**: 从发送到接收的完整流程

## 性能考虑

- Transport 自动处理 WebSocket ping/pong
- 大消息支持 (默认 100MB)
- 连接超时可配置
- 异步非阻塞操作

## 兼容性

- ✅ 向后兼容旧的 contracts.py 导入
- ✅ 保持现有 API 签名
- ✅ 支持服务器和客户端模式
- ✅ FastAPI 和 websockets 库兼容
