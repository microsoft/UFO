# AIP Endpoints

Endpoints combine protocol, transport, and resilience components to provide complete client/server implementations for AIP communication.

## Endpoint Architecture

```
┌──────────────────────────────────────┐
│         AIPEndpoint (Base)           │
│  - Protocol management               │
│  - Session tracking                  │
│  - Resilience (reconnection,         │
│    heartbeat, timeout)               │
└──────────────┬───────────────────────┘
               │
       ┌───────┴──────┬────────────────┐
       │              │                │
┌──────▼─────┐ ┌──────▼──────┐ ┌──────▼────────┐
│ Device     │ │ Device      │ │Constellation  │
│ Server     │ │ Client      │ │ Endpoint      │
│ Endpoint   │ │ Endpoint    │ │               │
└────────────┘ └─────────────┘ └───────────────┘
```

## Base Endpoint: AIPEndpoint

All endpoints inherit from `AIPEndpoint`, which provides core functionality:

### Core Components

**Protocol**: Message handling and serialization
**Reconnection Strategy**: Automatic reconnection with backoff
**Timeout Manager**: Operation timeout management
**Session Handlers**: Per-session state tracking

### Common Methods

```python
from aip.endpoints.base import AIPEndpoint

# Start endpoint
await endpoint.start()

# Stop endpoint
await endpoint.stop()

# Check connection
if endpoint.is_connected():
    await endpoint.handle_message(msg)

# Send with timeout
await endpoint.send_with_timeout(msg, timeout=30.0)

# Receive with timeout
msg = await endpoint.receive_with_timeout(ServerMessage, timeout=30.0)
```

## Device Server Endpoint

The `DeviceServerEndpoint` wraps UFO's server-side WebSocket handler with AIP protocol support.

### Initialization

```python
from aip.endpoints import DeviceServerEndpoint

endpoint = DeviceServerEndpoint(
    ws_manager=ws_manager,           # WebSocket manager
    session_manager=session_manager, # Session manager
    local=False                       # Local vs remote mode
)
```

### Usage with FastAPI

```python
from fastapi import FastAPI, WebSocket
from aip.endpoints import DeviceServerEndpoint

app = FastAPI()
endpoint = DeviceServerEndpoint(ws_manager, session_manager)

@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    await endpoint.handle_websocket(websocket)
```

### Features

**Multiplexed Connections**

Handles multiple client connections simultaneously.

**Session Management**

Tracks active sessions per device.

**Task Dispatching**

Routes tasks to appropriate device clients.

**Result Aggregation**

Collects and formats execution results.

!!!info
    The Device Server Endpoint maintains backward compatibility with UFO's existing WebSocket handler.

### Task Cancellation

When a device disconnects, the server cancels all pending tasks:

```python
# Automatically called on disconnection
await endpoint.cancel_device_tasks(
    device_id="device_001",
    reason="device_disconnected"
)
```

## Device Client Endpoint

The `DeviceClientEndpoint` wraps UFO's client-side WebSocket client with AIP protocol support.

### Initialization

```python
from aip.endpoints import DeviceClientEndpoint

endpoint = DeviceClientEndpoint(
    ws_url="ws://localhost:8000/ws",
    ufo_client=ufo_client,
    max_retries=3,
    timeout=120.0
)
```

### Starting the Client

```python
# Start and connect
await endpoint.start()

# Wait for connection
# (automatically handled internally)
```

### Stopping the Client

```python
# Stop heartbeat and close connection
await endpoint.stop()
```

### Automatic Heartbeat

Device clients automatically send heartbeat messages:

```python
# Heartbeat started automatically on connection
# Interval: 20 seconds (configurable)
```

### Message Handling

Messages are handled by the underlying UFO client:

```python
# Automatically routes to appropriate handler
await endpoint.handle_message(server_msg)
```

### Reconnection

Automatic reconnection on disconnection:

```python
# Configured during initialization
reconnection_strategy = ReconnectionStrategy(
    max_retries=3,
    initial_backoff=2.0,
    max_backoff=60.0
)
```

## Constellation Endpoint

The `ConstellationEndpoint` enables orchestrator-side communication with multiple devices.

### Initialization

```python
from aip.endpoints import ConstellationEndpoint

endpoint = ConstellationEndpoint(
    task_name="multi_device_task",
    message_processor=processor  # Optional message processor
)
```

### Connecting to Devices

```python
# Connect to a device
connection = await endpoint.connect_to_device(
    device_info=agent_profile,  # AgentProfile object
    message_processor=processor
)
```

### Sending Tasks

```python
# Send task to device
result = await endpoint.send_task_to_device(
    device_id="device_001",
    task_request={
        "request": "Open Notepad",
        "task_name": "open_notepad",
        "session_id": "session_123"
    }
)
```

### Querying Device Info

```python
# Request device information
device_info = await endpoint.request_device_info("device_001")

if device_info:
    print(f"OS: {device_info['os']}")
    print(f"CPU: {device_info['cpu']}")
```

### Managing Connections

**Check connection status:**

```python
if endpoint.is_device_connected("device_001"):
    await endpoint.send_task_to_device(...)
```

**Disconnect device:**

```python
await endpoint.disconnect_device("device_001")
```

**Disconnect all:**

```python
await endpoint.stop()  # Disconnects all devices
```

### Device Disconnection Handling

When a device disconnects:

```python
# Automatically triggered
await endpoint.on_device_disconnected("device_001")

# Cancels pending tasks
await endpoint.cancel_device_tasks(
    device_id="device_001",
    reason="device_disconnected"
)

# Attempts reconnection (if enabled)
success = await endpoint.reconnect_device("device_001")
```

## Endpoint Lifecycle

### Typical Server Lifecycle

```python
# 1. Initialize
endpoint = DeviceServerEndpoint(ws_manager, session_manager)

# 2. Start
await endpoint.start()

# 3. Handle connections
@app.websocket("/ws")
async def handle_ws(websocket: WebSocket):
    await endpoint.handle_websocket(websocket)

# 4. Stop (on shutdown)
await endpoint.stop()
```

### Typical Client Lifecycle

```python
# 1. Initialize
endpoint = DeviceClientEndpoint(ws_url, ufo_client)

# 2. Connect
await endpoint.start()

# 3. Handle messages
# (automatically handled by UFO client)

# 4. Disconnect
await endpoint.stop()
```

### Typical Constellation Lifecycle

```python
# 1. Initialize
endpoint = ConstellationEndpoint(task_name)

# 2. Start
await endpoint.start()

# 3. Connect to devices
await endpoint.connect_to_device(device_info1)
await endpoint.connect_to_device(device_info2)

# 4. Send tasks
await endpoint.send_task_to_device(device_id, task_request)

# 5. Cleanup
await endpoint.stop()  # Disconnects all devices
```

## Resilience Features

All endpoints include built-in resilience:

### Reconnection Strategy

```python
from aip.resilience import ReconnectionStrategy, ReconnectionPolicy

strategy = ReconnectionStrategy(
    max_retries=5,
    initial_backoff=1.0,
    max_backoff=60.0,
    backoff_multiplier=2.0,
    policy=ReconnectionPolicy.EXPONENTIAL_BACKOFF
)

endpoint = DeviceClientEndpoint(
    ws_url=url,
    ufo_client=client,
    reconnection_strategy=strategy
)
```

### Timeout Management

```python
# Send with custom timeout
await endpoint.send_with_timeout(msg, timeout=30.0)

# Receive with custom timeout
msg = await endpoint.receive_with_timeout(ServerMessage, timeout=60.0)
```

### Heartbeat Management

Heartbeats are automatically managed for device clients:

```python
# Configured via HeartbeatManager (internal)
# Default interval: 20-30 seconds
```

## Error Handling

### Connection Errors

```python
try:
    await endpoint.start()
except ConnectionError as e:
    logger.error(f"Failed to connect: {e}")
    # Reconnection handled automatically if enabled
```

### Task Execution Errors

```python
try:
    result = await endpoint.send_task_to_device(device_id, task)
except TimeoutError:
    logger.error("Task execution timeout")
except Exception as e:
    logger.error(f"Task failed: {e}")
```

### Disconnection Handling

```python
# Override for custom behavior
class CustomEndpoint(DeviceClientEndpoint):
    async def on_device_disconnected(self, device_id: str) -> None:
        logger.warning(f"Device {device_id} disconnected")
        # Custom cleanup logic
        await self.custom_cleanup(device_id)
        # Call parent implementation
        await super().on_device_disconnected(device_id)
```

## Best Practices

**Use Appropriate Endpoint Type**

- Server-side: `DeviceServerEndpoint`
- Client-side: `DeviceClientEndpoint`
- Orchestrator-side: `ConstellationEndpoint`

**Configure Resilience**

Always set appropriate reconnection and timeout parameters based on your deployment environment.

**Handle Disconnections**

Implement custom `on_device_disconnected` handlers for application-specific cleanup.

**Monitor Connection Health**

Regularly check `is_connected()` before critical operations.

**Clean Up Resources**

Always call `stop()` during shutdown to prevent resource leaks.

**Use Message Processors**

Provide message processors for custom message handling:

```python
class MyProcessor:
    async def process_message(self, msg):
        # Custom processing
        pass

endpoint = ConstellationEndpoint(
    task_name="task",
    message_processor=MyProcessor()
)
```

## API Reference

```python
from aip.endpoints import (
    AIPEndpoint,           # Base class
    DeviceServerEndpoint,  # Server-side
    DeviceClientEndpoint,  # Client-side
    ConstellationEndpoint, # Orchestrator-side
)
```

For more information:

- [Protocol Reference](./protocols.md) - Protocol implementations used by endpoints
- [Transport Layer](./transport.md) - Transport configuration
- [Resilience](./resilience.md) - Reconnection and heartbeat management
- [Overview](./overview.md) - System architecture
