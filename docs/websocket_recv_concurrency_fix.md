# WebSocket recv() Concurrency Issue - Fix Documentation

## 🐛 Problem Description

### Error Message
```
❌ Error requesting device info for client_001: cannot call recv while another coroutine is already waiting for the next message
```

### Root Cause

在 WebSocket 连接上，**不能同时有多个协程调用 `recv()`**。这是 WebSocket 的基本限制。

在我们的架构中：
1. **MessageProcessor** 已经在持续监听 WebSocket 消息（通过 `async for message in websocket`）
2. **ConnectionManager.request_device_info()** 尝试直接调用 `websocket.recv()`
3. 这导致两个协程同时等待同一个 WebSocket 的消息 → **冲突** ❌

```python
# MessageProcessor (持续运行)
async def _handle_device_messages(self, device_id, websocket):
    async for message in websocket:  # ← 已经在监听
        # 处理消息...

# ConnectionManager (同时调用)
async def request_device_info(self, device_id):
    response = await websocket.recv()  # ← 冲突！
```

## ✅ Solution: Future-Based Pattern

### 设计原理

使用 **asyncio.Future** 模式，让 MessageProcessor 成为**唯一的消息接收者**，其他组件通过 Future 等待结果。

```
┌─────────────────────────────────────────────────────┐
│               WebSocket Connection                  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │      MessageProcessor (唯一监听者)            │  │
│  │                                              │  │
│  │  async for message in websocket:            │  │
│  │      - TASK_END → complete_task_response()  │  │
│  │      - DEVICE_INFO_RESPONSE →               │  │
│  │          complete_device_info_response()    │  │
│  │      - ERROR, HEARTBEAT, etc.               │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
                      ↓
    ┌─────────────────────────────────────────┐
    │    ConnectionManager (等待 Future)      │
    │                                         │
    │  _pending_tasks: Dict[str, Future]     │
    │  _pending_device_info: Dict[str, Future]│
    │                                         │
    │  request_device_info():                │
    │    1. Create Future                    │
    │    2. Send request                     │
    │    3. await Future (等待 MessageProcessor)│
    └─────────────────────────────────────────┘
```

### Implementation Details

#### 1. ConnectionManager 添加 Future 跟踪

```python
class WebSocketConnectionManager:
    def __init__(self, constellation_id: str):
        # ...
        # 跟踪待处理的设备信息请求
        self._pending_device_info: Dict[str, asyncio.Future] = {}
```

#### 2. request_device_info() 使用 Future 模式

**Before (错误的方式):**
```python
async def request_device_info(self, device_id: str):
    # ❌ 直接调用 recv() - 会与 MessageProcessor 冲突
    response_text = await websocket.recv()
    response = ServerMessage.model_validate_json(response_text)
    return response.result
```

**After (正确的方式):**
```python
async def request_device_info(self, device_id: str):
    # ✅ 创建 Future 并等待 MessageProcessor 完成
    request_id = f"device_info_{device_id}_{timestamp}"
    info_future = asyncio.Future()
    self._pending_device_info[request_id] = info_future
    
    # 发送请求
    await websocket.send(request_message.model_dump_json())
    
    # 等待 Future 被 MessageProcessor 完成
    try:
        device_info = await asyncio.wait_for(info_future, timeout=10.0)
        return device_info
    finally:
        self._pending_device_info.pop(request_id, None)
```

#### 3. ConnectionManager 添加完成方法

```python
def complete_device_info_response(
    self, request_id: str, device_info: Optional[Dict[str, Any]]
) -> None:
    """
    由 MessageProcessor 调用以完成设备信息请求
    """
    info_future = self._pending_device_info.get(request_id)
    if info_future and not info_future.done():
        info_future.set_result(device_info)
```

#### 4. MessageProcessor 处理 DEVICE_INFO_RESPONSE

```python
async def _process_server_message(self, device_id: str, server_msg: ServerMessage):
    if server_msg.type == ServerMessageType.TASK_END:
        await self._handle_task_completion(device_id, server_msg)
    # ...
    elif server_msg.type == ServerMessageType.DEVICE_INFO_RESPONSE:
        await self._handle_device_info_response(device_id, server_msg)

async def _handle_device_info_response(
    self, device_id: str, server_msg: ServerMessage
) -> None:
    request_id = server_msg.request_id
    device_info = server_msg.result if server_msg.result else None
    
    # 完成 ConnectionManager 中的 Future
    if self.connection_manager:
        self.connection_manager.complete_device_info_response(
            request_id, device_info
        )
```

## 🔄 Data Flow

### Complete Request-Response Flow

```
1. ConnectionManager.request_device_info(device_id)
   └─> Create Future and store in _pending_device_info[request_id]
   └─> Send DEVICE_INFO_REQUEST message via WebSocket
   └─> await Future (blocks until MessageProcessor completes it)

2. Server receives DEVICE_INFO_REQUEST
   └─> Looks up device info in WSManager
   └─> Sends DEVICE_INFO_RESPONSE message back

3. MessageProcessor receives DEVICE_INFO_RESPONSE
   └─> Extracts request_id and device_info from message
   └─> Calls connection_manager.complete_device_info_response()
   └─> Resolves the Future with device_info

4. ConnectionManager.request_device_info() unblocks
   └─> Returns device_info to caller
   └─> Cleans up _pending_device_info[request_id]
```

## 🎯 Key Benefits

### 1. No recv() Conflicts
- ✅ **单一接收者**: Only MessageProcessor calls `recv()`
- ✅ **Future 协调**: Other components wait via Futures

### 2. Consistent Pattern
- ✅ Same pattern as `send_task_to_device()` (uses `_pending_tasks`)
- ✅ Same pattern as `request_device_info()` (uses `_pending_device_info`)

### 3. Better Error Handling
- ✅ Timeout support: `asyncio.wait_for(future, timeout=10.0)`
- ✅ Cleanup: Always remove Future from dict in `finally` block
- ✅ Duplicate detection: Check if Future already done

### 4. Scalability
- ✅ Multiple concurrent requests supported
- ✅ Each request has unique `request_id`
- ✅ No race conditions

## 📊 Comparison

| Aspect | Direct recv() (❌ Wrong) | Future Pattern (✅ Correct) |
|--------|-------------------------|----------------------------|
| **Concurrency** | Cannot handle multiple requests | Supports multiple concurrent requests |
| **Architecture** | Violates single receiver principle | Clean separation of concerns |
| **Error Handling** | Complex, prone to deadlocks | Clean timeout and error handling |
| **Consistency** | Different from task sending | Same pattern as task sending |
| **Testability** | Hard to mock | Easy to test with AsyncMock |

## 🧪 Testing

All tests pass after fix:

```bash
✅ tests/unit/test_device_info_provider.py:       11/11 passed
✅ tests/unit/test_ws_manager_device_info.py:      10/10 passed
✅ tests/integration/test_device_info_flow.py:      5/5 passed
✅ tests/galaxy/client/test_device_manager_info_update.py: 4/4 passed

Total: 30/30 tests passed ✨
```

## 📝 Code Changes Summary

### Modified Files

1. **galaxy/client/components/connection_manager.py**
   - ➕ Added `_pending_device_info: Dict[str, asyncio.Future]`
   - ✏️ Modified `request_device_info()` to use Future pattern
   - ➕ Added `complete_device_info_response()` method

2. **galaxy/client/components/message_processor.py**
   - ✏️ Added `DEVICE_INFO_RESPONSE` handling in `_process_server_message()`
   - ➕ Added `_handle_device_info_response()` method

### No Breaking Changes
- ✅ All existing tests pass
- ✅ API remains the same
- ✅ Only internal implementation changed

## 🚀 Lessons Learned

### WebSocket Best Practices

1. **Single Receiver Principle**
   - Only one coroutine should call `recv()` on a WebSocket
   - Use a dedicated message processor/router

2. **Future Pattern for Request-Response**
   - Create Future before sending request
   - Store Future with unique ID
   - Message processor completes Future when response arrives

3. **Timeout Management**
   - Always use `asyncio.wait_for()` with timeout
   - Clean up Futures in `finally` block

4. **Request ID Management**
   - Use unique IDs (e.g., timestamp-based)
   - Include request ID in both request and response
   - Check for duplicate/unknown request IDs

## 🔍 Related Patterns

This fix follows the same pattern as:
- `send_task_to_device()` → `complete_task_response()` (for TASK_END messages)
- Heartbeat handling (fire-and-forget, no Future needed)
- Error message handling (no Future needed, just logging)

---

**Fix Date**: 2024-10-13  
**Issue**: WebSocket recv() concurrency conflict  
**Solution**: Future-based message routing pattern  
**Status**: ✅ Fixed and tested
