# AIP Message Reference

This document provides a complete reference for all message types, data structures, and validation rules in the Agent Interaction Protocol (AIP).

## Message Architecture

AIP uses **strongly-typed messages** built with Pydantic for automatic validation, serialization, and documentation. All messages are transmitted as JSON over the WebSocket transport layer.

### Message Flow

```
Client → Server: ClientMessage
    - REGISTER
    - TASK
    - COMMAND_RESULTS
    - TASK_END
    - HEARTBEAT
    - DEVICE_INFO_REQUEST/RESPONSE
    - ERROR

Server → Client: ServerMessage
    - TASK
    - COMMAND
    - TASK_END
    - HEARTBEAT
    - DEVICE_INFO_REQUEST/RESPONSE
    - ERROR
```

## Core Data Structures

### Rect

Represents rectangle coordinates for UI elements.

**Fields:**

- `x` (int): X-coordinate of top-left corner
- `y` (int): Y-coordinate of top-left corner
- `width` (int): Width in pixels
- `height` (int): Height in pixels

**Example:**

```python
rect = Rect(x=100, y=200, width=300, height=150)
```

### ControlInfo

Information about a UI control element.

**Fields:**

- `annotation_id` (str, optional): Unique annotation identifier
- `name` (str, optional): Control name
- `title` (str, optional): Control title
- `handle` (int, optional): Windows handle (HWND)
- `class_name` (str, optional): UI class name
- `rectangle` (Rect, optional): Bounding rectangle
- `control_type` (str, optional): Type of control (Button, TextBox, etc.)
- `automation_id` (str, optional): UI Automation ID
- `is_enabled` (bool, optional): Whether control is enabled
- `is_visible` (bool, optional): Whether control is visible
- `source` (str, optional): Data source identifier
- `text_content` (str, optional): Text content of control

### WindowInfo

Information about a window, extends ControlInfo.

**Additional Fields:**

- `process_id` (int, optional): Process ID (PID)
- `process_name` (str, optional): Process name (e.g., "notepad.exe")
- `is_minimized` (bool, optional): Whether window is minimized
- `is_maximized` (bool, optional): Whether window is maximized
- `is_active` (bool, optional): Whether window has focus

### AppWindowControlInfo

Complete window with controls.

**Fields:**

- `window_info` (WindowInfo): Window information
- `controls` (List[ControlInfo], optional): List of controls in window

## Tool and Command Structures

### MCPToolInfo

Information about an MCP tool registered with the system.

**Fields:**

- `tool_key` (str): Unique key (e.g., "namespace.tool_name")
- `tool_name` (str): Tool name
- `title` (str, optional): Human-readable title
- `namespace` (str): MCP namespace
- `tool_type` (str): Type ("action" or "data_collection")
- `description` (str, optional): Tool description
- `input_schema` (dict, optional): JSON schema for inputs
- `output_schema` (dict, optional): JSON schema for outputs
- `meta` (dict, optional): Metadata
- `annotations` (dict, optional): Additional annotations

### Command

Represents a command to be executed by an agent.

**Fields:**

- `tool_name` (str): Name of the tool to execute
- `parameters` (dict, optional): Parameters for the tool
- `tool_type` (Literal["data_collection", "action"]): Type of tool
- `call_id` (str, optional): Unique identifier for this command call

**Example:**

```python
cmd = Command(
    tool_name="click_element",
    parameters={"control_id": "btn_submit"},
    tool_type="action",
    call_id="cmd_12345"
)
```

!!!tip
    Use `call_id` to correlate commands with their results in the `Result` object.

### ResultStatus

Enumeration of command execution statuses.

**Values:**

- `SUCCESS`: Command executed successfully
- `FAILURE`: Command failed with error
- `SKIPPED`: Command was skipped (e.g., conditional execution)
- `NONE`: No status (initial state)

### Result

Represents the result of a command execution.

**Fields:**

- `status` (ResultStatus): Execution status
- `error` (str, optional): Error message if failed
- `result` (Any): Result payload (type depends on tool)
- `namespace` (str, optional): Namespace of the executed tool
- `call_id` (str, optional): ID matching the Command.call_id

**Example:**

```python
result = Result(
    status=ResultStatus.SUCCESS,
    result={"element_found": True, "clicked": True},
    namespace="ui_automation",
    call_id="cmd_12345"
)
```

!!!warning
    Always check `status` before accessing `result`. If status is `FAILURE`, the `error` field will contain diagnostic information.

## Status Enumerations

### TaskStatus

Represents the status of a task in the AIP protocol.

**Values:**

- `CONTINUE`: Task is ongoing, more steps needed
- `COMPLETED`: Task finished successfully
- `FAILED`: Task encountered an error
- `OK`: Acknowledgment or health check passed
- `ERROR`: Protocol-level error occurred

**State Transitions:**

```
CONTINUE → CONTINUE (multi-step task)
CONTINUE → COMPLETED (task done)
CONTINUE → FAILED (error occurred)
OK ← HEARTBEAT (keepalive)
ERROR (terminal state)
```

!!!info
    `CONTINUE` status enables multi-turn task execution where the agent can request additional commands before completion.

## Client Message Types

### ClientMessageType

Enumeration of message types sent from client to server.

**Registration & Health:**

- `REGISTER`: Initial registration with server
- `HEARTBEAT`: Periodic keepalive signal

**Task Execution:**

- `TASK`: Request to execute a task
- `TASK_END`: Notify task completion
- `COMMAND_RESULTS`: Return results of executed commands

**Device Info:**

- `DEVICE_INFO_REQUEST`: Request device information
- `DEVICE_INFO_RESPONSE`: Response with device information

**Error Handling:**

- `ERROR`: Report an error condition

### ClientMessage

Message sent from client to server.

**Fields:**

- `type` (ClientMessageType): Message type
- `status` (TaskStatus): Current task status
- `client_type` (ClientType): Type of client (DEVICE or CONSTELLATION)
- `session_id` (str, optional): Unique session identifier
- `task_name` (str, optional): Human-readable task name
- `client_id` (str, optional): Unique client identifier
- `target_id` (str, optional): Target device ID (for constellation clients)
- `request` (str, optional): Request text (for TASK messages)
- `action_results` (List[Result], optional): Command execution results
- `timestamp` (str, optional): ISO 8601 timestamp
- `request_id` (str, optional): Unique request identifier
- `prev_response_id` (str, optional): Previous response ID for correlation
- `error` (str, optional): Error message
- `metadata` (dict, optional): Additional metadata

**REGISTER Example:**

```python
register_msg = ClientMessage(
    type=ClientMessageType.REGISTER,
    client_type=ClientType.DEVICE,
    client_id="windows_agent_001",
    status=TaskStatus.OK,
    timestamp="2024-11-04T10:30:00Z",
    metadata={
        "platform": "windows",
        "os_version": "Windows 11",
        "capabilities": ["ui_automation", "file_operations"]
    }
)
```

**COMMAND_RESULTS Example:**

```python
results_msg = ClientMessage(
    type=ClientMessageType.COMMAND_RESULTS,
    client_id="windows_agent_001",
    session_id="session_123",
    prev_response_id="resp_456",
    status=TaskStatus.CONTINUE,
    action_results=[
        Result(status=ResultStatus.SUCCESS, result={"data": "value"}),
        Result(status=ResultStatus.SUCCESS, result={"count": 42})
    ],
    timestamp="2024-11-04T10:31:00Z",
    request_id="req_789"
)
```

## Server Message Types

### ServerMessageType

Enumeration of message types sent from server to client.

**Task Execution:**

- `TASK`: Task assignment to device
- `COMMAND`: Command(s) to execute
- `TASK_END`: Task completion notification

**Health & Info:**

- `HEARTBEAT`: Keepalive acknowledgment
- `DEVICE_INFO_REQUEST`: Request for device information
- `DEVICE_INFO_RESPONSE`: Device information response

**Error Handling:**

- `ERROR`: Error notification

### ServerMessage

Message sent from server to client.

**Fields:**

- `type` (ServerMessageType): Message type
- `status` (TaskStatus): Current task status
- `user_request` (str, optional): Original user request
- `agent_name` (str, optional): Name of the agent handling the task
- `process_name` (str, optional): Process name for execution context
- `root_name` (str, optional): Root application name
- `actions` (List[Command], optional): Commands to execute
- `messages` (List[str], optional): Log messages
- `error` (str, optional): Error description
- `session_id` (str, optional): Unique session identifier
- `task_name` (str, optional): Human-readable task name
- `timestamp` (str, optional): ISO 8601 timestamp
- `response_id` (str, optional): Unique response identifier
- `result` (Any, optional): Result payload

**TASK Example:**

```python
task_msg = ServerMessage(
    type=ServerMessageType.TASK,
    status=TaskStatus.CONTINUE,
    user_request="Open Notepad and create a new file",
    task_name="create_notepad_file",
    session_id="session_123",
    response_id="resp_001",
    agent_name="AppAgent",
    process_name="notepad.exe",
    timestamp="2024-11-04T10:30:00Z"
)
```

**COMMAND Example:**

```python
command_msg = ServerMessage(
    type=ServerMessageType.COMMAND,
    status=TaskStatus.CONTINUE,
    session_id="session_123",
    response_id="resp_456",
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
    ],
    timestamp="2024-11-04T10:30:30Z"
)
```

**TASK_END Example:**

```python
task_end_msg = ServerMessage(
    type=ServerMessageType.TASK_END,
    status=TaskStatus.COMPLETED,
    session_id="session_123",
    response_id="resp_999",
    result={
        "file_created": True,
        "path": "C:\\Users\\user\\document.txt"
    },
    timestamp="2024-11-04T10:35:00Z"
)
```

## Client Types

### ClientType

Type of client in the AIP system.

**Values:**

- `DEVICE`: A device agent that executes tasks locally
- `CONSTELLATION`: An orchestrator that manages multiple devices

**Usage:**

```python
# Device client registration
device_msg = ClientMessage(
    type=ClientMessageType.REGISTER,
    client_type=ClientType.DEVICE,
    client_id="device_001"
)

# Constellation client registration
constellation_msg = ClientMessage(
    type=ClientMessageType.REGISTER,
    client_type=ClientType.CONSTELLATION,
    client_id="orchestrator_001",
    target_id="device_001"  # Target device for this constellation
)
```

!!!note
    Constellation clients specify a `target_id` to indicate which device they want to coordinate.

## Message Validation

AIP provides built-in validation for all messages through the `MessageValidator` class.

### Registration Validation

```python
from aip.messages import MessageValidator

valid = MessageValidator.validate_registration(client_message)
```

**Requirements:**

- Message type must be `REGISTER`
- `client_id` must be present
- For constellation clients, `target_id` is recommended

### Task Request Validation

```python
valid = MessageValidator.validate_task_request(client_message)
```

**Requirements:**

- Message type must be `TASK`
- `request` field must be present
- `client_id` must be present

### Command Results Validation

```python
valid = MessageValidator.validate_command_results(client_message)
```

**Requirements:**

- Message type must be `COMMAND_RESULTS`
- `prev_response_id` must be present (for correlation)
- `action_results` must not be None

### Server Message Validation

```python
valid = MessageValidator.validate_server_message(server_message)
```

**Requirements:**

- `type` must be present
- `status` must be present
- For `COMMAND` type: `actions` and `response_id` required

!!!warning
    Always validate messages before processing to prevent protocol errors and ensure data integrity.

## Message Correlation

AIP uses a chain of identifiers to correlate requests and responses:

### Request-Response Chain

```
Client Request:
    request_id: "req_001"

Server Response:
    response_id: "resp_001"
    
Client Follow-up:
    request_id: "req_002"
    prev_response_id: "resp_001"  ← Links to previous response

Server Next Response:
    response_id: "resp_002"
```

### Session Tracking

All messages within a task execution share the same `session_id`:

```python
# Task start
task_msg.session_id = "session_abc"

# Command execution
command_msg.session_id = "session_abc"

# Results
results_msg.session_id = "session_abc"

# Task end
task_end_msg.session_id = "session_abc"
```

!!!tip
    Use session IDs to group related messages together for logging, debugging, and state management.

## Best Practices

**Always Set Timestamps**

Use ISO 8601 format for consistency:

```python
from datetime import datetime, timezone

timestamp = datetime.now(timezone.utc).isoformat()
```

**Use Unique Identifiers**

Generate UUIDs for request_id, response_id, and call_id:

```python
import uuid

request_id = str(uuid.uuid4())
```

**Validate Before Sending**

Always validate messages before transmission to catch errors early.

**Handle Errors Gracefully**

Check `Result.status` before accessing result data, and always provide meaningful error messages.

**Leverage Metadata**

Use the `metadata` field for extensibility without breaking protocol compatibility.

**Correlate Messages**

Always set `prev_response_id` in follow-up messages to maintain conversation context.

## API Reference

For programmatic access to message classes:

```python
from aip.messages import (
    ClientMessage,
    ServerMessage,
    ClientMessageType,
    ServerMessageType,
    ClientType,
    TaskStatus,
    Command,
    Result,
    ResultStatus,
    MessageValidator,
)
```

For detailed implementation examples, see:

- [Protocol Guide](./protocols.md) - How protocols use these messages
- [Endpoints](./endpoints.md) - How endpoints construct and handle messages
- [Overview](./overview.md) - High-level message flow architecture
