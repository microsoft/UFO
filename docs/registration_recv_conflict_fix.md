# Registration `recv()` Conflict Fix

**Date:** October 27, 2025  
**Issue:** `cannot call recv while another coroutine is already waiting for the next message`  
**Component:** Galaxy Client - Connection Manager & Message Processor

---

## 🐛 Problem Description

### Error Message
```
ERROR - ❌ Error validating registration response: 
cannot call recv while another coroutine is already waiting for the next message
```

### Root Cause

The initial fix for target device validation introduced a **recv() conflict**:

1. **`MessageProcessor`** is started and begins listening: `async for message in websocket:`
2. **`_validate_registration_response()`** also tries to read: `await websocket.recv()`
3. **WebSocket protocol** doesn't allow multiple concurrent `recv()` calls on the same socket

```python
# ❌ PROBLEM CODE (Initial Fix)
async def _register_constellation_client(...):
    # Start MessageProcessor (begins recv() loop)
    message_processor.start_message_handler(device_id, websocket)
    
    # Send registration
    await websocket.send(registration_message.model_dump_json())
    
    # ❌ CONFLICT: Try to recv() while MessageProcessor is also recv()ing
    success = await self._validate_registration_response(websocket, ...)
    #                    └─> calls websocket.recv() ❌
```

### Timeline of the Conflict

```
t0: MessageProcessor starts
    ↓ async for message in websocket:  ← waiting for recv()
t1: Send REGISTER message
t2: _validate_registration_response() called
    ↓ await websocket.recv()  ← CONFLICT! ❌
t3: ERROR: cannot call recv while another coroutine is already waiting
```

---

## ✅ Solution: Future-Based Coordination

Instead of calling `recv()` directly in `_register_constellation_client()`, we use an **asyncio.Future** that MessageProcessor will complete when it receives the registration response.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Connection Manager                          │
│                                                               │
│  _register_constellation_client():                           │
│    1. Create Future                                           │
│    2. Store in _pending_registration[device_id]              │
│    3. Send REGISTER message                                   │
│    4. await Future (with 10s timeout)  ⏳                    │
│    5. Return result                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Message Flow
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  Message Processor                           │
│                                                               │
│  _handle_device_messages():                                  │
│    async for message in websocket:  ← Only recv() here       │
│      ↓                                                        │
│    _process_server_message():                                │
│      if HEARTBEAT + status=OK:                               │
│        → complete_registration_response(device_id, True)     │
│      if ERROR:                                                │
│        → complete_registration_response(device_id, False)    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Completes Future
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  Connection Manager                          │
│                                                               │
│  complete_registration_response(device_id, success):         │
│    1. Get Future from _pending_registration[device_id]       │
│    2. future.set_result(success)  ← Unblocks await           │
│    3. _register_constellation_client() returns result        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation

### 1. Add Future Tracking

```python
# connection_manager.py
class WebSocketConnectionManager:
    def __init__(self, task_name: str):
        # ...existing code...
        
        # ✅ NEW: Dictionary to track pending registration responses
        # Key: device_id, Value: Future that will be resolved with registration result (bool)
        self._pending_registration: Dict[str, asyncio.Future] = {}
```

### 2. Use Future Instead of Direct recv()

```python
# connection_manager.py
async def _register_constellation_client(...) -> bool:
    # Send registration message
    await websocket.send(registration_message.model_dump_json())
    
    # ✅ NEW: Create Future and wait for MessageProcessor to resolve it
    registration_future = asyncio.Future()
    self._pending_registration[device_info.device_id] = registration_future
    
    try:
        # Wait for MessageProcessor to resolve the registration result
        success = await asyncio.wait_for(registration_future, timeout=10.0)
        return success
        
    except asyncio.TimeoutError:
        self.logger.error(f"⏰ Timeout waiting for registration response")
        return False
    finally:
        # Clean up
        self._pending_registration.pop(device_info.device_id, None)
```

### 3. Add Completion Method

```python
# connection_manager.py
def complete_registration_response(
    self, device_id: str, success: bool, error_message: Optional[str] = None
) -> None:
    """
    Complete a pending registration request with the response from the server.
    
    This method is called by MessageProcessor when it receives the first HEARTBEAT
    or ERROR message after registration.
    """
    registration_future = self._pending_registration.get(device_id)
    
    if registration_future is None:
        # No pending registration - this is a regular message, not a registration response
        return
    
    if registration_future.done():
        return  # Already completed (duplicate message)
    
    # ✅ Resolve the Future
    registration_future.set_result(success)
```

### 4. Call from MessageProcessor

```python
# message_processor.py
async def _process_server_message(self, device_id: str, server_msg: ServerMessage):
    if server_msg.type == ServerMessageType.ERROR:
        # ✅ Check if this is a registration error response
        self.connection_manager.complete_registration_response(
            device_id, success=False, error_message=server_msg.error
        )
        await self._handle_error_message(device_id, server_msg)
        
    elif server_msg.type == ServerMessageType.HEARTBEAT:
        # ✅ Check if this is a registration success response
        if server_msg.status == TaskStatus.OK:
            self.connection_manager.complete_registration_response(
                device_id, success=True
            )
        self.heartbeat_manager.handle_heartbeat_response(device_id)
```

---

##  Benefits

### 1. No recv() Conflicts ✅
- Only **one place** calls `recv()`: MessageProcessor's message loop
- All other components wait via Futures

### 2. Consistent Pattern ✅
- Same pattern as `send_task_to_device()` and `request_device_info()`
- Easy to understand and maintain

### 3. Proper Async Coordination ✅
- Uses asyncio primitives correctly
- Clean separation of concerns

### 4. Timeout Handling ✅
- 10-second timeout prevents hanging forever
- Clear error messages on timeout

---

## 📊 Message Flow Example

### Success Case

```
ConnectionManager              MessageProcessor              Server
      |                              |                          |
      | Start MessageProcessor       |                          |
      |----------------------------->|                          |
      |                              | async for msg in ws:     |
      |                              |------------------------->|
      | Create Future                |                          |
      | Send REGISTER                |                          |
      |------------------------------------------------------------>
      | await Future ⏳             |                          |
      |                              |                          |
      |                              |    HEARTBEAT (status=OK) |
      |                              |<-------------------------|
      |                              | complete_registration()  |
      |<-----------------------------|                          |
      | Future.set_result(True) ✅  |                          |
      | return True                  |                          |
```

### Failure Case

```
ConnectionManager              MessageProcessor              Server
      |                              |                          |
      | Start MessageProcessor       |                          |
      |----------------------------->|                          |
      |                              | async for msg in ws:     |
      |                              |------------------------->|
      | Create Future                |                          |
      | Send REGISTER                |                          |
      |------------------------------------------------------------>
      | await Future ⏳             |                          |
      |                              |                          |
      |                              |    ERROR (not connected) |
      |                              |<-------------------------|
      |                              | complete_registration()  |
      |<-----------------------------|                          |
      | Future.set_result(False) ❌ |                          |
      | return False                 |                          |
```

---

## 🧪 Testing Implications

Tests need to be updated to mock the MessageProcessor behavior:

```python
# Test needs to simulate MessageProcessor calling complete_registration_response

# Mock MessageProcessor to process the mock response
async def mock_message_handler(device_id, websocket):
    # Simulate receiving and processing the server response
    response = await websocket.recv()
    server_msg = ServerMessage.model_validate_json(response)
    
    # Call complete_registration_response based on response
    if server_msg.status == TaskStatus.ERROR:
        connection_manager.complete_registration_response(device_id, False, server_msg.error)
    else:
        connection_manager.complete_registration_response(device_id, True)

# Patch MessageProcessor.start_message_handler
with patch.object(message_processor, 'start_message_handler', side_effect=mock_message_handler):
    success = await device_manager.connect_device(device_id)
```

---

## 🔗 Related Issues

- **Original Issue**: Target device not registered returns false success
- **Initial Fix**: Wait for server response in `_validate_registration_response()`
- **New Issue**: `recv()` conflict between ConnectionManager and MessageProcessor
- **This Fix**: Use Future-based coordination instead of direct `recv()`

---

## 📝 Summary

| Aspect | Before (Direct recv) | After (Future-based) |
|--------|---------------------|----------------------|
| recv() calls | 2 (conflict ❌) | 1 (MessageProcessor only ✅) |
| Coordination | Direct recv() | asyncio.Future |
| Timeout | Yes (10s) | Yes (10s) |
| Error handling | Exception-based | Result-based |
| Pattern consistency | Different from other methods | Same as task/device_info ✅ |
| Complexity | Lower | Slightly higher |
| Maintainability | Poor (conflicts) | Good (clear pattern) ✅ |

---

**Status:** ✅ Implemented  
**Next Step:** Update tests to work with new Future-based approach
