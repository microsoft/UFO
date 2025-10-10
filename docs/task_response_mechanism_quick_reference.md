# Task Response Mechanism - Quick Reference

## 核心概念

**问题**: 如何让 `send_task_to_device()` 等待异步任务完成?

**解决方案**: 使用 `asyncio.Future` 模式

```
发送任务 → 创建Future → 等待Future → MessageProcessor完成Future → 返回结果
```

## API 快速参考

### ConnectionManager

```python
async def send_task_to_device(device_id: str, task_request: TaskRequest) -> ServerMessage:
    """发送任务并等待响应"""
    
async def _wait_for_task_response(device_id: str, task_id: str) -> ServerMessage:
    """等待任务响应 (内部使用)"""
    
def complete_task_response(task_id: str, response: ServerMessage) -> None:
    """完成任务响应 (由 MessageProcessor 调用)"""
```

### MessageProcessor

```python
def set_connection_manager(connection_manager: WebSocketConnectionManager) -> None:
    """设置 ConnectionManager 引用"""
    
async def _handle_task_completion(device_id: str, server_msg: ServerMessage) -> None:
    """处理任务完成消息"""
```

## 关键实现细节

### 1. Future 注册

```python
# ConnectionManager._wait_for_task_response()
task_future = asyncio.Future()
self._pending_tasks[task_id] = task_future
await task_future  # 阻塞直到完成
```

### 2. Future 完成

```python
# ConnectionManager.complete_task_response()
task_future = self._pending_tasks.get(task_id)
if task_future and not task_future.done():
    task_future.set_result(response)
```

### 3. 资源清理

```python
try:
    response = await task_future
    return response
finally:
    self._pending_tasks.pop(task_id, None)
```

## 重要注意事项

### ⚠️ 使用 response_id 而非 request_id

```python
# ❌ 错误
task_id = server_msg.request_id  # ServerMessage 没有这个属性!

# ✅ 正确
task_id = server_msg.response_id  # 使用 response_id
```

### ⚠️ 设置 ConnectionManager 引用

```python
# 创建组件
connection_manager = WebSocketConnectionManager(constellation_id)
message_processor = MessageProcessor(device_registry, heartbeat_manager, event_manager)

# ✅ 必须设置引用
message_processor.set_connection_manager(connection_manager)
```

### ⚠️ 超时后清理 Future

```python
except asyncio.TimeoutError:
    # ✅ 必须清理
    self._pending_tasks.pop(task_request.task_id, None)
    raise ConnectionError(f"Task {task_request.task_id} timed out")
```

## 常见问题

### Q: Future 如何被完成?

A: MessageProcessor 收到 TASK_END 消息时调用 `complete_task_response()`

### Q: 如果任务超时会怎样?

A: `asyncio.wait_for()` 抛出 TimeoutError,Future 被清理,抛出 ConnectionError

### Q: 多个任务可以同时等待吗?

A: 可以!每个任务有自己的 Future,互不干扰

### Q: ServerMessage 和 ClientMessage 的 ID 对应关系?

```
ClientMessage.request_id  ←→  ServerMessage.response_id
```

## 测试命令

```bash
# 运行所有测试
python -m pytest tests/galaxy/client/test_task_response_mechanism.py -v

# 运行单个测试
python -m pytest tests/galaxy/client/test_task_response_mechanism.py::TestTaskResponseMechanism::test_send_task_to_device_end_to_end -v

# 详细输出
python -m pytest tests/galaxy/client/test_task_response_mechanism.py -v -s
```

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                  GalaxyClient                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │          ConnectionManager                        │  │
│  │                                                   │  │
│  │  _pending_tasks: Dict[str, Future]                │  │
│  │  ├── "task_1" → Future<ServerMessage>            │  │
│  │  ├── "task_2" → Future<ServerMessage>            │  │
│  │  └── "task_3" → Future<ServerMessage>            │  │
│  │                                                   │  │
│  │  send_task_to_device(device_id, task_request)    │  │
│  │    ├─→ 发送 WebSocket 消息                        │  │
│  │    └─→ await _wait_for_task_response()           │  │
│  │         └─→ 创建 Future,等待完成                  │  │
│  │                                                   │  │
│  │  complete_task_response(task_id, response)       │  │
│  │    └─→ Future.set_result(response)               │  │
│  └───────────────┬───────────────────────────────────┘  │
│                  │                                       │
│                  │ set_connection_manager()              │
│                  ▼                                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │          MessageProcessor                         │  │
│  │                                                   │  │
│  │  _handle_device_messages()                        │  │
│  │    └─→ 接收 WebSocket 消息                        │  │
│  │                                                   │  │
│  │  _process_server_message()                        │  │
│  │    └─→ 根据类型路由消息                           │  │
│  │                                                   │  │
│  │  _handle_task_completion()                        │  │
│  │    ├─→ connection_manager.complete_task_response()│  │
│  │    └─→ event_manager.notify_task_completed()     │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 示例代码

### 发送任务并等待

```python
# 创建任务请求
task_request = TaskRequest(
    task_id="task_001",
    device_id="device_001",
    task_name="open_app",
    request="open notepad",
    timeout=30.0
)

# 发送并等待
try:
    result = await connection_manager.send_task_to_device(
        "device_001",
        task_request
    )
    
    if result.status == TaskStatus.COMPLETED:
        print(f"✅ Success: {result.result}")
    else:
        print(f"❌ Error: {result.error}")
        
except ConnectionError as e:
    print(f"⏰ Timeout: {e}")
```

### 处理任务完成

```python
# MessageProcessor 自动处理
async def _handle_task_completion(device_id, server_msg):
    task_id = server_msg.response_id
    
    # 完成 Future (唤醒等待中的 send_task_to_device)
    if self.connection_manager:
        self.connection_manager.complete_task_response(task_id, server_msg)
    
    # 触发事件
    await self.event_manager.notify_task_completed(device_id, task_id, result)
```

## 相关文件

- `galaxy/client/components/connection_manager.py`
- `galaxy/client/components/message_processor.py`
- `tests/galaxy/client/test_task_response_mechanism.py`
- `docs/task_response_mechanism_implementation.md`
