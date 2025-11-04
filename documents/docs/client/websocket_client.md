# WebSocket Client

The **WebSocket Client** implements the AIP (Agent Interaction Protocol) for reliable, bidirectional communication between the device client and the Agent Server.

## Overview

The WebSocket client provides:

- **Connection Management** - Persistent WebSocket connection with automatic retry
- **AIP Protocol Implementation** - Structured message handling via Registration, Heartbeat, and Task Execution protocols
- **Device Registration** - Automatic registration with device information on connect
- **Heartbeat Monitoring** - Regular keepalive messages to maintain connection health
- **Message Routing** - Dispatch incoming messages to appropriate handlers
- **Error Handling** - Graceful error recovery and reporting

## Architecture

```
┌──────────────────────────────────────────────────────┐
│          UFOWebSocketClient                          │
├──────────────────────────────────────────────────────┤
│  Connection Management:                              │
│  • connect_and_listen() - Main connection loop       │
│  • Retry with exponential backoff                    │
│  • Connection state tracking                         │
├──────────────────────────────────────────────────────┤
│  AIP Protocol Handlers:                              │
│  • RegistrationProtocol - Client registration        │
│  • HeartbeatProtocol - Connection keepalive          │
│  • TaskExecutionProtocol - Task request/result       │
├──────────────────────────────────────────────────────┤
│  Message Handling:                                   │
│  • recv_loop() - Receive incoming messages           │
│  • handle_message() - Route to handlers              │
│  • handle_commands() - Execute server commands       │
│  • handle_task_end() - Process task completion       │
└──────────────────────────────────────────────────────┘
```

## Connection Lifecycle

### Connection Flow

```
Start → Connect → Register → Heartbeat Loop → Listen for Messages
  │         │          │            │                │
  │         │          │            │                │
Retry    WebSocket   Device     Keep-Alive      Command
Logic    Establish   Profile     Monitor        Dispatch
         & AIP Init  Push
```

### Initialization

```python
from ufo.client.websocket import UFOWebSocketClient
from ufo.client.ufo_client import UFOClient

# Create UFO client
ufo_client = UFOClient(
    mcp_server_manager=mcp_manager,
    computer_manager=computer_manager,
    client_id="device_windows_001",
    platform="windows"
)

# Create WebSocket client
ws_client = UFOWebSocketClient(
    ws_url="ws://localhost:8000/ws",
    ufo_client=ufo_client,
    max_retries=5,
    timeout=120
)

# Connect and start listening
await ws_client.connect_and_listen()
```

### Connection Establishment

**Step 1: WebSocket Connection**

```python
async with websockets.connect(
    self.ws_url,
    ping_interval=20,      # Keepalive ping every 20s
    ping_timeout=180,      # Wait 3 minutes for pong
    close_timeout=10,      # Close handshake timeout
    max_size=100 * 1024 * 1024  # 100MB max message
) as ws:
    self._ws = ws
    # Initialize AIP protocols
    self.transport = WebSocketTransport(ws)
    self.registration_protocol = RegistrationProtocol(self.transport)
    self.heartbeat_protocol = HeartbeatProtocol(self.transport)
    self.task_protocol = TaskExecutionProtocol(self.transport)
```

!!!info "Connection Parameters"
    - **ping_interval**: 20s for frequent keepalive
    - **ping_timeout**: 180s to handle long-running operations
    - **max_size**: 100MB to support large screenshots and data

**Step 2: Client Registration**

```python
await self.register_client()
```

See [Registration Flow](#registration-flow) for details.

**Step 3: Message Handling**

```python
await self.handle_messages()
```

Starts two concurrent loops:
- `recv_loop()` - Receives and processes messages
- `heartbeat_loop()` - Sends periodic heartbeats

## Registration Flow

### Device Information Collection

The client collects comprehensive device information:

```python
from ufo.client.device_info_provider import DeviceInfoProvider

system_info = DeviceInfoProvider.collect_system_info(
    client_id=self.ufo_client.client_id,
    custom_metadata=None
)

# System info includes:
# - platform (windows/linux/darwin)
# - os_version
# - cpu_count
# - memory_total_gb
# - hostname
# - ip_address
# - supported_features
# - platform_type
```

See [Device Info Provider](./device_info.md) for complete details.

### Registration Message

The client sends a REGISTER message via AIP:

```python
metadata = {
    "system_info": system_info.to_dict(),
    "registration_time": datetime.now(timezone.utc).isoformat()
}

success = await self.registration_protocol.register_as_device(
    device_id=self.ufo_client.client_id,
    metadata=metadata,
    platform=self.ufo_client.platform
)
```

!!!success "Push Model"
    The client uses a **push model** - device information is sent during registration, not requested later. This reduces latency for constellation clients.

### Registration Response

**Success:**

```
INFO - [WS] [AIP] ✅ Successfully registered as device_windows_001
```

The `connected_event` is set, allowing task requests to proceed.

**Failure:**

```
ERROR - [WS] [AIP] ❌ Failed to register as device_windows_001
RuntimeError: Registration failed for device_windows_001
```

The connection is closed and retry logic engages.

## Heartbeat Mechanism

### Heartbeat Loop

The client sends periodic heartbeats to prove connection health:

```python
async def heartbeat_loop(self, interval: float = 120) -> None:
    """Send periodic heartbeat messages."""
    while True:
        await asyncio.sleep(interval)
        try:
            await self.heartbeat_protocol.send_heartbeat(
                self.ufo_client.client_id
            )
            self.logger.debug("[WS] [AIP] Heartbeat sent")
        except (ConnectionError, IOError) as e:
            self.logger.debug(f"[WS] [AIP] Heartbeat failed: {e}")
            break  # Exit loop if connection closed
```

**Default Interval:** 120 seconds

**Heartbeat Message:**

```json
{
  "type": "HEARTBEAT",
  "client_id": "device_windows_001",
  "timestamp": "2025-11-04T14:30:22.123Z"
}
```

!!!tip "Tuning Heartbeat"
    Adjust the interval in the `handle_messages()` call:
    ```python
    await self.heartbeat_loop(interval=60)  # 60 second heartbeats
    ```

## Message Handling

### Message Dispatcher

The client routes incoming messages by type:

```python
async def handle_message(self, msg: str):
    """Dispatch messages based on their type."""
    data = ServerMessage.model_validate_json(msg)
    msg_type = data.type
    
    if msg_type == ServerMessageType.TASK:
        await self.start_task(data.user_request, data.task_name)
    elif msg_type == ServerMessageType.HEARTBEAT:
        self.logger.info("[WS] Heartbeat received")
    elif msg_type == ServerMessageType.TASK_END:
        await self.handle_task_end(data)
    elif msg_type == ServerMessageType.ERROR:
        self.logger.error(f"[WS] Server error: {data.error}")
    elif msg_type == ServerMessageType.COMMAND:
        await self.handle_commands(data)
    else:
        self.logger.warning(f"[WS] Unknown message type: {msg_type}")
```

### Task Start

When the server requests a task:

```python
async def start_task(self, request_text: str, task_name: str | None):
    """Start a new task."""
    
    # Check if another task is running
    if self.current_task is not None and not self.current_task.done():
        self.logger.warning("[WS] Task still running, ignoring new task")
        return
    
    # Reset client state
    async with self.ufo_client.task_lock:
        self.ufo_client.reset()
        
        # Send task request via AIP
        await self.task_protocol.send_task_request(
            request=request_text,
            task_name=task_name or str(uuid4()),
            session_id=self.ufo_client.session_id,
            client_id=self.ufo_client.client_id,
            metadata={"platform": self.ufo_client.platform}
        )
```

!!!warning "Single Task Execution"
    The client only executes one task at a time. New task requests while a task is running are ignored.

### Command Execution

When the server sends commands to execute:

```python
async def handle_commands(self, server_response: ServerMessage):
    """Handle commands from server."""
    
    response_id = server_response.response_id
    task_status = server_response.status
    self.session_id = server_response.session_id
    
    # Execute commands via UFO Client
    action_results = await self.ufo_client.execute_step(server_response)
    
    # Send results back via AIP
    await self.task_protocol.send_task_result(
        session_id=self.session_id,
        prev_response_id=response_id,
        action_results=action_results,
        status=task_status,
        client_id=self.ufo_client.client_id
    )
    
    # Check for task completion
    if task_status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        await self.handle_task_end(server_response)
```

### Task Completion

```python
async def handle_task_end(self, server_response: ServerMessage):
    """Handle task end messages."""
    
    if server_response.status == TaskStatus.COMPLETED:
        self.logger.info(f"[WS] Task {self.session_id} completed")
    elif server_response.status == TaskStatus.FAILED:
        self.logger.error(f"[WS] Task {self.session_id} failed: {server_response.error}")
```

## Error Handling

### Connection Errors

**Automatic Retry with Exponential Backoff:**

```python
async def connect_and_listen(self):
    """Connect with automatic retry."""
    while self.retry_count < self.max_retries:
        try:
            async with websockets.connect(...) as ws:
                await self.register_client()
                self.retry_count = 0  # Reset on success
                await self.handle_messages()
        except (ConnectionClosedError, ConnectionClosedOK) as e:
            self.logger.error(f"[WS] Connection closed: {e}")
            self.retry_count += 1
            await self._maybe_retry()
        except Exception as e:
            self.logger.error(f"[WS] Unexpected error: {e}", exc_info=True)
            self.retry_count += 1
            await self._maybe_retry()
    
    self.logger.error("[WS] Max retries reached. Exiting.")
```

**Exponential Backoff:**

```python
async def _maybe_retry(self):
    """Exponential backoff before retry."""
    if self.retry_count < self.max_retries:
        wait_time = 2 ** self.retry_count  # 1s, 2s, 4s, 8s, 16s...
        self.logger.info(f"[WS] Retrying in {wait_time}s...")
        await asyncio.sleep(wait_time)
```

### Message Parsing Errors

```python
try:
    data = ServerMessage.model_validate_json(msg)
    # Process message
except Exception as e:
    self.logger.error(f"[WS] Error handling message: {e}", exc_info=True)
    # Send error report via AIP
    error_msg = ClientMessage(
        type=ClientMessageType.ERROR,
        error=str(e),
        client_id=self.ufo_client.client_id,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    await self.transport.send(error_msg.model_dump_json().encode())
```

### Registration Errors

If device info collection fails:

```python
try:
    system_info = DeviceInfoProvider.collect_system_info(...)
    metadata = {"system_info": system_info.to_dict()}
except Exception as e:
    self.logger.error(f"[WS] [AIP] Error collecting device info: {e}")
    # Continue with minimal metadata
    metadata = {"registration_time": datetime.now(timezone.utc).isoformat()}
```

## AIP Protocol Integration

The WebSocket client uses three AIP protocols:

### Registration Protocol

```python
from aip.protocol.registration import RegistrationProtocol

self.registration_protocol = RegistrationProtocol(self.transport)

# Register as device
success = await self.registration_protocol.register_as_device(
    device_id="device_windows_001",
    metadata={"system_info": {...}},
    platform="windows"
)
```

See [AIP Registration Protocol](../aip/protocols.md#registration-protocol) for details.

### Heartbeat Protocol

```python
from aip.protocol.heartbeat import HeartbeatProtocol

self.heartbeat_protocol = HeartbeatProtocol(self.transport)

# Send heartbeat
await self.heartbeat_protocol.send_heartbeat("device_windows_001")
```

See [AIP Heartbeat Protocol](../aip/protocols.md#heartbeat-protocol) for details.

### Task Execution Protocol

```python
from aip.protocol.task_execution import TaskExecutionProtocol

self.task_protocol = TaskExecutionProtocol(self.transport)

# Send task request
await self.task_protocol.send_task_request(
    request="Open Notepad",
    task_name="task_001",
    session_id=None,
    client_id="device_windows_001"
)

# Send task result
await self.task_protocol.send_task_result(
    session_id="session_123",
    prev_response_id="resp_456",
    action_results=[...],
    status=TaskStatus.COMPLETED,
    client_id="device_windows_001"
)
```

See [AIP Task Execution Protocol](../aip/protocols.md#task-execution-protocol) for details.

## Connection State

### State Checking

```python
def is_connected(self) -> bool:
    """Check if WebSocket is connected."""
    return (
        self.connected_event.is_set()
        and self._ws is not None
        and not self._ws.closed
    )
```

**Usage:**

```python
if ws_client.is_connected():
    await ws_client.start_task("Open Calculator", "task_calc")
else:
    logger.error("Not connected to server")
```

### Connected Event

The `connected_event` is an `asyncio.Event` that signals successful registration:

```python
# Wait for connection
await ws_client.connected_event.wait()

# Now safe to send task requests
await ws_client.start_task("Open Notepad", "task_notepad")
```

## Best Practices

**Handle Connection Loss Gracefully**

```python
try:
    await ws_client.connect_and_listen()
except Exception as e:
    logger.error(f"WebSocket client error: {e}")
    # Implement your recovery strategy
```

**Use Appropriate Retry Limits**

For unreliable networks, increase max retries:

```python
ws_client = UFOWebSocketClient(
    ws_url="ws://...",
    ufo_client=ufo_client,
    max_retries=10  # More retries for unstable connections
)
```

**Monitor Connection Health**

Log heartbeat success/failure:

```python
try:
    await self.heartbeat_protocol.send_heartbeat(...)
    self.logger.debug("[WS] ✅ Heartbeat sent successfully")
except Exception as e:
    self.logger.error(f"[WS] ❌ Heartbeat failed: {e}")
```

**Clean State on Reconnection**

The client automatically resets state on new tasks:

```python
async with self.ufo_client.task_lock:
    self.ufo_client.reset()  # Clear session state
    # Send new task request
```

## Integration Points

### UFO Client

The WebSocket client delegates command execution to the UFO Client:

```python
action_results = await self.ufo_client.execute_step(server_response)
```

See [UFO Client](./ufo_client.md) for execution details.

### Device Info Provider

Collects device information for registration:

```python
system_info = DeviceInfoProvider.collect_system_info(
    client_id=self.ufo_client.client_id,
    custom_metadata=None
)
```

See [Device Info Provider](./device_info.md) for profiling details.

### AIP Transport

All communication goes through the WebSocket transport:

```python
from aip.transport.websocket import WebSocketTransport

self.transport = WebSocketTransport(ws)
```

See [AIP Transport Layer](../aip/transport.md) for transport details.

## Next Steps

- [Quick Start](./quick_start.md) - Connect your client
- [UFO Client](./ufo_client.md) - Command execution
- [Device Info Provider](./device_info.md) - System profiling
- [AIP Protocol Guide](../aip/protocols.md) - Protocol details
- [Server Quick Start - Client Registration](../server/quick_start.md#connecting-a-device-client) - Server-side registration
