# WebSocket Handler

The **UFOWebSocketHandler** implements the Agent Interaction Protocol (AIP) for structured, reliable communication between the server and clients. It handles registration, task dispatch, heartbeat monitoring, and device information exchange.

## Overview

The WebSocket handler provides:

- AIP-based structured messaging
- Client registration and validation
- Task execution coordination
- Heartbeat monitoring
- Device information management
- Error handling and recovery

## AIP Protocol Integration

The handler uses multiple AIP protocol implementations:

```python
self.registration_protocol = RegistrationProtocol(transport)
self.heartbeat_protocol = HeartbeatProtocol(transport)
self.device_info_protocol = DeviceInfoProtocol(transport)
self.task_protocol = TaskExecutionProtocol(transport)
```

Each protocol handles a specific aspect of communication, providing clean separation of concerns.

## Client Registration

### Registration Flow

**1. WebSocket Connection**

```python
await websocket.accept()
```

**2. Initialize AIP Transport**

```python
self.transport = WebSocketTransport(websocket)
```

**3. Receive Registration Message**

```python
reg_data = await self.transport.receive()
reg_info = ClientMessage.model_validate_json(reg_data)
```

**4. Validate Registration**

```python
if not reg_info.client_id:
    raise ValueError("Client ID required")
if reg_info.type != ClientMessageType.REGISTER:
    raise ValueError("First message must be REGISTER")
```

**5. Type-Specific Validation**

For constellation clients:

```python
if client_type == ClientType.CONSTELLATION:
    # Verify target device is connected
    if not ws_manager.is_device_connected(target_id):
        await self.registration_protocol.send_registration_error(
            "Target device not connected"
        )
        raise ValueError(...)
```

**6. Register Client**

```python
ws_manager.add_client(
    client_id,
    platform,
    websocket,
    client_type,
    metadata
)
```

**7. Send Confirmation**

```python
await self.registration_protocol.send_registration_confirmation()
```

!!!success
    The AIP registration protocol provides structured, validated registration with clear error messages.

## Message Handling

### Message Dispatcher

The handler routes incoming messages to appropriate handlers:

```python
async def handle_message(self, msg: str, websocket: WebSocket):
    data = ClientMessage.model_validate_json(msg)
    
    msg_type = data.type
    
    if msg_type == ClientMessageType.TASK:
        await self.handle_task_request(data, websocket)
    elif msg_type == ClientMessageType.COMMAND_RESULTS:
        await self.handle_command_result(data)
    elif msg_type == ClientMessageType.HEARTBEAT:
        await self.handle_heartbeat(data, websocket)
    elif msg_type == ClientMessageType.ERROR:
        await self.handle_error(data, websocket)
    elif msg_type == ClientMessageType.DEVICE_INFO_REQUEST:
        await self.handle_device_info_request(data, websocket)
    # ...
```

### Task Request Handling

**Device Client Request**

```python
# Direct execution on requesting device
target_ws = websocket
platform = ws_manager.get_client_info(client_id).platform
```

**Constellation Client Request**

```python
# Execution on target device
target_device_id = data.target_id
target_ws = ws_manager.get_client(target_device_id)
platform = ws_manager.get_client_info(target_device_id).platform

# Track constellation session
ws_manager.add_constellation_session(client_id, session_id)
ws_manager.add_device_session(target_device_id, session_id)
```

**Background Execution**

```python
await session_manager.execute_task_async(
    session_id=session_id,
    task_name=task_name,
    request=data.request,
    websocket=target_ws,
    platform_override=platform,
    callback=send_result
)
```

**Immediate Acknowledgment**

```python
await self.task_protocol.send_ack(session_id=session_id)
```

!!!info
    Tasks execute in the background while the handler continues processing heartbeats and other messages.

### Command Result Handling

When a device completes command execution:

```python
async def handle_command_result(self, data: ClientMessage):
    response_id = data.prev_response_id
    session_id = data.session_id
    
    # Get session's command dispatcher
    session = session_manager.get_or_create_session(session_id)
    command_dispatcher = session.context.command_dispatcher
    
    # Set result (unblocks waiting dispatcher)
    await command_dispatcher.set_result(response_id, data)
```

### Heartbeat Handling

```python
async def handle_heartbeat(self, data: ClientMessage, websocket: WebSocket):
    # Send acknowledgment via AIP protocol
    await self.heartbeat_protocol.send_heartbeat_ack()
```

!!!tip
    Heartbeats are lightweight and processed quickly to maintain connection health.

### Device Info Handling

**Request from Constellation**

```python
async def handle_device_info_request(self, data: ClientMessage, websocket: WebSocket):
    device_id = data.target_id
    request_id = data.request_id
    
    # Get device info from WSManager
    device_info = await self.get_device_info(device_id)
    
    # Send via AIP protocol
    await self.device_info_protocol.send_device_info_response(
        device_info=device_info,
        request_id=request_id
    )
```

## Client Disconnection

### Disconnection Detection

```python
try:
    while True:
        msg = await websocket.receive_text()
        await self.handle_message(msg, websocket)
except WebSocketDisconnect as e:
    # Client disconnected
    await self.disconnect(client_id)
```

### Cleanup Process

**For Device Clients**

```python
# Get all sessions running on this device
session_ids = ws_manager.get_device_sessions(client_id)

# Cancel all sessions
for session_id in session_ids:
    await session_manager.cancel_task(
        session_id,
        reason="device_disconnected"
    )

# Clean up mappings
ws_manager.remove_device_sessions(client_id)
```

**For Constellation Clients**

```python
# Get all sessions initiated by constellation
session_ids = ws_manager.get_constellation_sessions(client_id)

# Cancel all sessions
for session_id in session_ids:
    await session_manager.cancel_task(
        session_id,
        reason="constellation_disconnected"
    )

# Clean up mappings
ws_manager.remove_constellation_sessions(client_id)
```

**Remove from Registry**

```python
ws_manager.remove_client(client_id)
```

!!!warning
    Proper cleanup is critical to prevent orphaned sessions and resource leaks.

## Result Callback

The handler defines a callback that sends results when tasks complete:

```python
async def send_result(sid: str, result_msg: ServerMessage):
    """Send task result to client when session completes."""
    
    # Check constellation client still connected
    constellation_connected = (
        ws_manager.get_client(data.client_id) is not None
    )
    
    if not constellation_connected:
        # Skip callback if client disconnected
        return
    
    # Send to constellation client
    if websocket.client_state == WebSocketState.CONNECTED:
        await websocket.send_text(result_msg.model_dump_json())
    
    # Also send to target device (if constellation)
    if client_type == ClientType.CONSTELLATION:
        if target_ws and target_ws.client_state == WebSocketState.CONNECTED:
            await target_ws.send_text(result_msg.model_dump_json())
```

!!!success
    The callback checks connection state before sending to prevent errors when clients disconnect during execution.

## Error Handling

### Connection Errors

```python
try:
    await self.heartbeat_protocol.send_heartbeat_ack()
except (ConnectionError, IOError) as e:
    # Connection closed - log but don't fail
    logger.debug(f"Could not send heartbeat ack: {e}")
```

### Message Parsing Errors

```python
try:
    data = ClientMessage.model_validate_json(msg)
except Exception as e:
    # Invalid message format
    await self.task_protocol.send_error(str(e))
```

### Task Execution Errors

```python
try:
    await self.handle_task_request(data, websocket)
except Exception as e:
    # Log error and send error message
    logger.error(f"Error handling task: {e}")
    await self.task_protocol.send_error(str(e))
```

## Best Practices

**Validate Early**

Validate all client messages immediately after parsing:

```python
if not data.client_id:
    raise ValueError("Client ID required")
if data.type != expected_type:
    raise ValueError(f"Expected {expected_type}")
```

**Check Connection State**

Always check WebSocket state before sending:

```python
from starlette.websockets import WebSocketState

if websocket.client_state == WebSocketState.CONNECTED:
    await websocket.send_text(msg)
```

**Handle Cancellation Gracefully**

Distinguish between different cancellation reasons:

```python
if reason == "constellation_disconnected":
    # Don't send callback
    return
elif reason == "device_disconnected":
    # Send callback to notify orchestrator
    await callback(session_id, failure_msg)
```

**Log Appropriately**

Use structured logging with context:

```python
logger.info(
    f"[WS] 🌟 Constellation {client_id} requesting task on {target_id}"
)
logger.error(
    f"[WS] ❌ Failed to send result for {session_id}: {error}"
)
```

## Integration Points

### Session Manager

Creates and executes sessions:

```python
await session_manager.execute_task_async(...)
```

### WebSocket Manager

Manages client registry and session mappings:

```python
ws_manager.add_client(...)
ws_manager.add_constellation_session(...)
ws_manager.get_device_sessions(...)
```

### AIP Protocols

Structured communication:

```python
await registration_protocol.send_registration_confirmation()
await heartbeat_protocol.send_heartbeat_ack()
await device_info_protocol.send_device_info_response(...)
await task_protocol.send_ack(...)
```

## API Reference

```python
from ufo.server.ws.handler import UFOWebSocketHandler

# Initialize
handler = UFOWebSocketHandler(
    ws_manager=ws_manager,
    session_manager=session_manager,
    local=False
)

# FastAPI endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await handler.handler(websocket)
```

For more information:

- [Overview](./overview.md) - Server architecture
- [Session Manager](./session_manager.md) - Session lifecycle
- [WebSocket Manager](./websocket_manager.md) - Connection management
- [AIP Protocol](../aip/protocols.md) - Protocol details
