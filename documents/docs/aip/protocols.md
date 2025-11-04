# AIP Protocol Reference

This document details the protocol implementations that power AIP's communication layer. Each protocol handles a specific aspect of the agent interaction lifecycle.

## Protocol Architecture

AIP's protocol stack is layered for modularity and extensibility:

```
┌─────────────────────────────────────────┐
│   Specialized Protocols                 │
│   - RegistrationProtocol                │
│   - TaskExecutionProtocol               │
│   - CommandProtocol                     │
│   - HeartbeatProtocol                   │
│   - DeviceInfoProtocol                  │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│   Core Protocol (AIPProtocol)           │
│   - Message serialization               │
│   - Middleware pipeline                 │
│   - Message routing                     │
│   - Error handling                      │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│   Transport Layer                       │
│   - WebSocket, HTTP/3, gRPC, etc.       │
└─────────────────────────────────────────┘
```

## Core Protocol: AIPProtocol

The `AIPProtocol` class provides the foundation for all AIP communication. It is transport-agnostic and handles message serialization, middleware processing, and error management.

### Initialization

```python
from aip.protocol import AIPProtocol
from aip.transport import WebSocketTransport

transport = WebSocketTransport()
protocol = AIPProtocol(transport)
```

### Sending Messages

**Basic send:**

```python
from aip.messages import ClientMessage, ClientMessageType, TaskStatus

msg = ClientMessage(
    type=ClientMessageType.HEARTBEAT,
    client_id="device_001",
    status=TaskStatus.OK
)

await protocol.send_message(msg)
```

!!!tip
    The protocol automatically serializes Pydantic models to JSON before transmission.

### Receiving Messages

**Basic receive:**

```python
from aip.messages import ServerMessage

server_msg = await protocol.receive_message(ServerMessage)
```

### Middleware Support

Add middleware to intercept and modify messages:

```python
from aip.protocol.base import ProtocolMiddleware

class LoggingMiddleware(ProtocolMiddleware):
    async def process_outgoing(self, msg):
        print(f"Sending: {msg}")
        return msg
    
    async def process_incoming(self, msg):
        print(f"Received: {msg}")
        return msg

protocol.add_middleware(LoggingMiddleware())
```

**Middleware execution order:**

- Outgoing: Applied in order (first added → first executed)
- Incoming: Applied in reverse order (last added → first executed)

### Message Handler Registration

Register handlers for specific message types:

```python
async def handle_task(msg):
    print(f"Handling task: {msg.task_name}")
    # Process task...

protocol.register_handler("task", handle_task)
```

**Dispatching messages:**

```python
# Automatically routes to registered handler
await protocol.dispatch_message(server_msg)
```

### Error Handling

**Send error (server-side):**

```python
await protocol.send_error(
    error_msg="Task execution failed: timeout",
    response_id="resp_123"
)
```

**Send acknowledgment (server-side):**

```python
await protocol.send_ack(
    session_id="session_abc",
    response_id="resp_456"
)
```

### Connection Management

**Check connection status:**

```python
if protocol.is_connected():
    await protocol.send_message(msg)
```

**Close protocol:**

```python
await protocol.close()
```

## Registration Protocol

The `RegistrationProtocol` handles agent registration and capability advertisement.

### Device Registration

**Client-side registration:**

```python
from aip.protocol import RegistrationProtocol

reg_protocol = RegistrationProtocol(transport)

success = await reg_protocol.register_as_device(
    device_id="windows_agent_001",
    metadata={
        "platform": "windows",
        "os_version": "Windows 11",
        "cpu": "Intel i7",
        "ram_gb": 16,
        "capabilities": ["ui_automation", "file_operations", "web_browsing"]
    },
    platform="windows"
)

if success:
    print("Device registered successfully")
```

!!!info
    The protocol automatically adds a registration timestamp to metadata.

### Constellation Registration

**Constellation client registration:**

```python
success = await reg_protocol.register_as_constellation(
    constellation_id="orchestrator_001",
    target_device="windows_agent_001",
    metadata={
        "orchestrator_version": "2.0.0",
        "max_concurrent_tasks": 10
    }
)
```

!!!warning
    Constellation clients must specify a `target_device` to indicate which device they will coordinate.

### Server-Side Registration Handling

**Send confirmation:**

```python
await reg_protocol.send_registration_confirmation(
    response_id="resp_001"
)
```

**Send error:**

```python
await reg_protocol.send_registration_error(
    error="Device ID already registered",
    response_id="resp_001"
)
```

### Registration Flow

```
┌──────────┐                           ┌──────────┐
│  Client  │                           │  Server  │
└────┬─────┘                           └────┬─────┘
     │                                      │
     │ REGISTER (device_id, metadata)      │
     │─────────────────────────────────────>│
     │                                      │
     │                        (Validate)    │
     │                        (Store profile)
     │                                      │
     │ HEARTBEAT (OK) / ERROR               │
     │<─────────────────────────────────────│
     │                                      │
```

## Task Execution Protocol

The `TaskExecutionProtocol` handles task assignment, command execution, and result reporting.

### Client-Side: Sending Task Request

```python
from aip.protocol import TaskExecutionProtocol
from aip.messages import ClientType

task_protocol = TaskExecutionProtocol(transport)

await task_protocol.send_task_request(
    request="Open Notepad and create a file named test.txt",
    task_name="create_notepad_file",
    session_id="session_123",
    client_id="windows_agent_001",
    client_type=ClientType.DEVICE,
    metadata={"priority": "high"}
)
```

### Server-Side: Sending Task Assignment

```python
await task_protocol.send_task_assignment(
    user_request="Open Notepad and create a file",
    task_name="create_notepad_file",
    session_id="session_123",
    response_id="resp_001",
    agent_name="AppAgent",
    process_name="notepad.exe"
)
```

### Server-Side: Sending Commands

**Method 1: Using ServerMessage object:**

```python
from aip.messages import ServerMessage, ServerMessageType, Command

server_msg = ServerMessage(
    type=ServerMessageType.COMMAND,
    status=TaskStatus.CONTINUE,
    session_id="session_123",
    response_id="resp_002",
    actions=[
        Command(
            tool_name="launch_application",
            parameters={"app_name": "notepad"},
            tool_type="action",
            call_id="cmd_001"
        ),
        Command(
            tool_name="type_text",
            parameters={"text": "Hello World"},
            tool_type="action",
            call_id="cmd_002"
        )
    ]
)

await task_protocol.send_command(server_msg)
```

**Method 2: Using send_commands:**

```python
await task_protocol.send_commands(
    actions=[
        Command(tool_name="save_file", parameters={"path": "test.txt"}, 
                tool_type="action", call_id="cmd_003")
    ],
    session_id="session_123",
    response_id="resp_003",
    status=TaskStatus.CONTINUE,
    agent_name="AppAgent"
)
```

!!!tip
    Batch multiple commands in a single message to reduce network overhead.

### Client-Side: Sending Command Results

```python
from aip.messages import Result, ResultStatus

await task_protocol.send_command_results(
    action_results=[
        Result(
            status=ResultStatus.SUCCESS,
            result={"app_launched": True},
            namespace="ui_automation",
            call_id="cmd_001"
        ),
        Result(
            status=ResultStatus.SUCCESS,
            result={"text_entered": True, "length": 11},
            namespace="ui_automation",
            call_id="cmd_002"
        )
    ],
    session_id="session_123",
    client_id="windows_agent_001",
    prev_response_id="resp_002",
    status=TaskStatus.CONTINUE
)
```

### Server-Side: Sending Task Completion

**Success:**

```python
await task_protocol.send_task_end(
    session_id="session_123",
    status=TaskStatus.COMPLETED,
    result={
        "file_created": True,
        "path": "C:\\Users\\user\\test.txt",
        "size_bytes": 11
    },
    response_id="resp_999"
)
```

**Failure:**

```python
await task_protocol.send_task_end(
    session_id="session_123",
    status=TaskStatus.FAILED,
    error="Notepad failed to launch: Access denied",
    response_id="resp_999"
)
```

### Client-Side: Acknowledging Task End

```python
await task_protocol.send_task_end_ack(
    session_id="session_123",
    client_id="windows_agent_001",
    status=TaskStatus.OK
)
```

### Task Execution Flow

```
Constellation  ConstellationAgent  Server  DeviceClient
     │                │              │           │
     │ TASK           │              │           │
     │───────────────>│              │           │
     │                │ TASK         │           │
     │                │─────────────>│           │
     │                │              │ TASK      │
     │                │              │──────────>│
     │                │              │           │
     │                │              │ (Execute) │
     │                │              │           │
     │                │              │ COMMAND   │
     │                │              │<──────────│
     │                │ COMMAND      │           │
     │                │<─────────────│           │
     │                │              │           │
     │                │ (Plan)       │           │
     │                │              │           │
     │                │ COMMAND      │           │
     │                │─────────────>│           │
     │                │              │ COMMAND   │
     │                │              │──────────>│
     │                │              │           │
     │                │              │ (Execute) │
     │                │              │           │
     │                │              │ RESULTS   │
     │                │              │<──────────│
     │                │ RESULTS      │           │
     │                │<─────────────│           │
     │                │              │           │
     │                │ (Complete)   │           │
     │                │              │           │
     │                │ TASK_END     │           │
     │                │─────────────>│           │
     │                │              │ TASK_END  │
     │                │              │──────────>│
     │ TASK_END       │              │           │
     │<───────────────│              │           │
```

## Command Protocol

The `CommandProtocol` provides fine-grained command validation.

### Command Validation

**Single command:**

```python
from aip.protocol import CommandProtocol

cmd_protocol = CommandProtocol(transport)

cmd = Command(
    tool_name="click_button",
    parameters={"button_id": "submit"},
    tool_type="action"
)

if cmd_protocol.validate_command(cmd):
    # Command is valid
    pass
```

**Batch validation:**

```python
commands = [cmd1, cmd2, cmd3]

if cmd_protocol.validate_commands(commands):
    await task_protocol.send_commands(commands, ...)
```

### Result Validation

**Single result:**

```python
result = Result(
    status=ResultStatus.SUCCESS,
    result={"clicked": True}
)

if cmd_protocol.validate_result(result):
    # Result is valid
    pass
```

**Batch validation:**

```python
results = [result1, result2, result3]

if cmd_protocol.validate_results(results):
    await task_protocol.send_command_results(results, ...)
```

!!!warning
    Always validate commands and results before transmission to catch protocol errors early.

## Heartbeat Protocol

The `HeartbeatProtocol` manages periodic keepalive messages to monitor connection health.

### Sending Heartbeat (Client-Side)

```python
from aip.protocol import HeartbeatProtocol

heartbeat_protocol = HeartbeatProtocol(transport)

await heartbeat_protocol.send_heartbeat(
    client_id="windows_agent_001",
    session_id="session_123"
)
```

### Sending Heartbeat (Server-Side)

```python
await heartbeat_protocol.send_heartbeat_response(
    session_id="session_123",
    response_id="resp_hb_001"
)
```

### Heartbeat Flow

```
Client                     Server
  │                          │
  │ HEARTBEAT (client_id)    │
  │─────────────────────────>│
  │                          │
  │        (Check alive)     │
  │                          │
  │ HEARTBEAT (OK)           │
  │<─────────────────────────│
  │                          │
```

!!!info
    Heartbeats are typically sent every 20-30 seconds. The `HeartbeatManager` automates this process.

## Device Info Protocol

The `DeviceInfoProtocol` handles device information requests and responses.

### Requesting Device Info (Server-Side)

```python
from aip.protocol import DeviceInfoProtocol

info_protocol = DeviceInfoProtocol(transport)

await info_protocol.request_device_info(
    device_id="windows_agent_001",
    request_id="req_info_001"
)
```

### Responding with Device Info (Client-Side)

```python
device_info = {
    "os": "Windows 11",
    "cpu": "Intel i7-12700K",
    "ram_gb": 32,
    "gpu": "NVIDIA RTX 3080",
    "disk_free_gb": 500,
    "active_processes": 145,
    "network_status": "connected"
}

await info_protocol.send_device_info_response(
    device_info=device_info,
    request_id="req_info_001",
    client_id="windows_agent_001"
)
```

### Device Info Flow

```
Server                     Client
  │                          │
  │ DEVICE_INFO_REQUEST      │
  │─────────────────────────>│
  │                          │
  │        (Collect info)    │
  │                          │
  │ DEVICE_INFO_RESPONSE     │
  │<─────────────────────────│
  │                          │
```

## Protocol Patterns

### Multi-Turn Conversations

Use `prev_response_id` to maintain conversation context:

```python
# Turn 1: Server sends command
await protocol.send_message(ServerMessage(
    type=ServerMessageType.COMMAND,
    response_id="resp_001",
    ...
))

# Turn 2: Client sends results
await protocol.send_message(ClientMessage(
    type=ClientMessageType.COMMAND_RESULTS,
    request_id="req_001",
    prev_response_id="resp_001",  # Links to previous
    ...
))

# Turn 3: Server sends next command
await protocol.send_message(ServerMessage(
    type=ServerMessageType.COMMAND,
    response_id="resp_002",
    ...
))
```

### Session-Based Communication

All messages in a task share the same session_id:

```python
SESSION_ID = "session_abc123"

# All messages use the same session ID
task_msg.session_id = SESSION_ID
command_msg.session_id = SESSION_ID
results_msg.session_id = SESSION_ID
task_end_msg.session_id = SESSION_ID
```

### Error Recovery

**Protocol-level errors:**

```python
try:
    await protocol.send_message(msg)
except ConnectionError:
    # Transport disconnected
    await reconnect()
except IOError as e:
    # I/O error during send
    log_error(e)
```

**Application-level errors:**

```python
# Send error message through protocol
await protocol.send_error(
    error_msg="Invalid command: tool_name missing",
    response_id=msg.response_id
)
```

## Best Practices

**Use Specialized Protocols**

Use specialized protocols (RegistrationProtocol, TaskExecutionProtocol, etc.) instead of manually constructing messages with AIPProtocol.

**Validate Messages**

Always validate commands and results before transmission.

**Maintain Session Context**

Always set session_id for all task-related messages.

**Correlate Messages**

Use request_id, response_id, and prev_response_id to maintain conversation flow.

**Handle Errors Gracefully**

Distinguish between protocol-level errors (connection issues) and application-level errors (task failures).

**Leverage Middleware**

Use middleware for cross-cutting concerns like logging, metrics, and authentication.

**Close Cleanly**

Always close protocols when done to release resources.

## API Reference

Import all protocols:

```python
from aip.protocol import (
    AIPProtocol,
    RegistrationProtocol,
    TaskExecutionProtocol,
    CommandProtocol,
    HeartbeatProtocol,
    DeviceInfoProtocol,
)
```

For more information:

- [Message Reference](./messages.md) - Message types and structures
- [Transport Layer](./transport.md) - WebSocket implementation
- [Endpoints](./endpoints.md) - Protocol usage in endpoints
- [Resilience](./resilience.md) - Connection management
