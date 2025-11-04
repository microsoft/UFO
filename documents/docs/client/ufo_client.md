# UFO Client

The **UFO Client** is the execution orchestrator that receives commands from the server, routes them to appropriate tools, and aggregates results for transmission back.

## Overview

The UFO Client provides:

- **Command Execution** - Processes server commands deterministically
- **Session Management** - Tracks session state and metadata
- **Result Aggregation** - Collects and structures tool execution results
- **Thread Safety** - Ensures safe concurrent execution
- **State Management** - Maintains agent, process, and root names

!!!info "Stateless Execution"
    The UFO Client executes commands without reasoning. All decision-making happens on the server.

## Architecture

```
┌────────────────────────────────────────────────┐
│             UFOClient                          │
├────────────────────────────────────────────────┤
│  Session State:                                │
│  • session_id - Current session identifier     │
│  • agent_name - Active agent name              │
│  • process_name - Process context              │
│  • root_name - Root operation name             │
├────────────────────────────────────────────────┤
│  Execution:                                    │
│  • execute_step() - Process server message     │
│  • execute_actions() - Run command list        │
│  • reset() - Clear session state               │
├────────────────────────────────────────────────┤
│  Dependencies:                                 │
│  • CommandRouter - Route commands to tools     │
│  • ComputerManager - Manage computer instances │
│  • MCPServerManager - Manage MCP servers       │
└────────────────────────────────────────────────┘
```

## Initialization

```python
from ufo.client.ufo_client import UFOClient
from ufo.client.computer import ComputerManager
from ufo.client.mcp.mcp_server_manager import MCPServerManager

# Initialize managers
mcp_server_manager = MCPServerManager()
computer_manager = ComputerManager(
    ufo_config.to_dict(),
    mcp_server_manager
)

# Create UFO client
client = UFOClient(
    mcp_server_manager=mcp_server_manager,
    computer_manager=computer_manager,
    client_id="device_windows_001",
    platform="windows"
)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `mcp_server_manager` | MCPServerManager | Manages MCP server lifecycle |
| `computer_manager` | ComputerManager | Manages computer instances |
| `client_id` | str (optional) | Unique client identifier (default: `"client_001"`) |
| `platform` | str (optional) | Platform type: `"windows"` or `"linux"` |

## Session State

The client maintains state for the current session:

### Session ID

```python
# Set session ID
client.session_id = "session_20251104_143022_abc123"

# Get session ID
current_session = client.session_id

# Clear session ID
client.reset()  # Sets session_id to None
```

!!!warning "Thread Safety"
    Session state is protected by `task_lock` to prevent concurrent modifications.

### Agent Name

Identifies the active agent (HostAgent, AppAgent, etc.):

```python
# Set agent name
client.agent_name = "HostAgent"

# Get agent name
agent = client.agent_name
```

### Process Name

Identifies the process context:

```python
# Set process name
client.process_name = "notepad.exe"

# Get process name
process = client.process_name
```

### Root Name

Identifies the root operation:

```python
# Set root name
client.root_name = "open_application"

# Get root name
root = client.root_name
```

## Command Execution

### Execute Step

Processes a complete step from the server:

```python
from aip.messages import ServerMessage

# Receive server message
server_response = ServerMessage.model_validate_json(msg)

# Execute step
action_results = await client.execute_step(server_response)

# action_results is a list of Result objects
```

**Workflow:**

```
Server Message → Extract Metadata → Execute Actions → Return Results
      │                │                  │                │
      │                │                  │                │
  Actions List    agent_name         CommandRouter      Result[]
                  process_name        Execution
                  root_name
```

**Implementation:**

```python
async def execute_step(self, response: ServerMessage) -> List[Result]:
    """Perform a single step execution."""
    
    # Extract metadata from server response
    self.agent_name = response.agent_name
    self.process_name = response.process_name
    self.root_name = response.root_name
    
    # Execute actions
    action_results = await self.execute_actions(response.actions)
    
    return action_results
```

### Execute Actions

Executes a list of commands:

```python
from aip.messages import Command

commands = [
    Command(
        action="click",
        parameters={"control_label": "Start", "x": 10, "y": 10}
    ),
    Command(
        action="type_text",
        parameters={"text": "notepad"}
    ),
    Command(
        action="press_key",
        parameters={"key": "enter"}
    )
]

# Execute all commands
results = await client.execute_actions(commands)

# results contains Result object for each command
```

**Delegation to Command Router:**

```python
async def execute_actions(self, commands: Optional[List[Command]]) -> List[Result]:
    """Execute the actions provided by the server."""
    
    action_results = []
    
    if commands:
        self.logger.info(f"Executing {len(commands)} actions in total")
        
        # Delegate to CommandRouter
        action_results = await self.command_router.execute(
            agent_name=self.agent_name,
            process_name=self.process_name,
            root_name=self.root_name,
            commands=commands
        )
    
    return action_results
```

See [Computer Manager](./computer_manager.md) for command routing details.

## State Reset

Resets all session state and dependent managers:

```python
def reset(self):
    """Reset session state and dependent managers."""
    
    # Clear session state
    self._session_id = None
    self._agent_name = None
    self._process_name = None
    self._root_name = None
    
    # Reset managers
    self.computer_manager.reset()
    self.mcp_server_manager.reset()
    
    self.logger.info("Client state has been reset.")
```

**When to Reset:**

- Before starting a new task
- On task completion
- On task failure
- On server disconnection

!!!tip "Automatic Reset"
    The WebSocket client automatically calls `reset()` before starting new tasks.

## Thread Safety

The client uses an asyncio lock for thread-safe execution:

```python
# In WebSocket client
async with client.task_lock:
    client.reset()
    await client.execute_step(server_response)
```

**Protected Operations:**

- Session state modifications
- Command execution
- State reset

## Property Validation

All session properties validate their inputs:

```python
# Valid assignment
client.session_id = "session_123"  # ✅

# Invalid assignment
client.session_id = 12345  # ❌ ValueError: Session ID must be a string or None

# Valid clearing
client.session_id = None  # ✅

# Similar validation for agent_name, process_name, root_name
```

**Error Example:**

```python
try:
    client.agent_name = 123  # Not a string
except ValueError as e:
    print(e)  # "Agent name must be a string or None."
```

## Integration with Command Router

The client delegates execution to the `CommandRouter`:

```python
from ufo.client.computer import CommandRouter

self.command_router = CommandRouter(
    computer_manager=self.computer_manager
)

# Execute commands
results = await self.command_router.execute(
    agent_name="HostAgent",
    process_name="explorer.exe",
    root_name="open_folder",
    commands=[...]
)
```

**Command Router Responsibilities:**

- Route commands to appropriate computer instances
- Execute commands via MCP tools
- Handle tool failures and timeouts
- Aggregate results

See [Computer Manager](./computer_manager.md) for routing details.

## Execution Flow

### Complete Execution Pipeline

```
1. WebSocket receives COMMAND message
   │
   ▼
2. WebSocket calls client.execute_step(server_response)
   │
   ▼
3. Client extracts metadata (agent_name, process_name, root_name)
   │
   ▼
4. Client calls execute_actions(commands)
   │
   ▼
5. Client delegates to CommandRouter.execute()
   │
   ▼
6. CommandRouter routes to Computer instances
   │
   ▼
7. Computer executes via MCP tools
   │
   ▼
8. Results bubble back up to client
   │
   ▼
9. Client returns results to WebSocket
   │
   ▼
10. WebSocket sends COMMAND_RESULTS via AIP
```

## Error Handling

### Command Execution Errors

```python
try:
    results = await client.execute_actions(commands)
except Exception as e:
    logger.error(f"Command execution failed: {e}", exc_info=True)
    # Error will be included in Result objects
```

**Error Results:**

Individual command failures are captured in Result objects:

```python
from aip.messages import Result, ResultStatus

error_result = Result(
    action="click",
    status=ResultStatus.ERROR,
    error_message="Control not found",
    observation="Failed to locate control with label 'Start'"
)
```

### Property Validation Errors

```python
try:
    client.session_id = 12345  # Invalid type
except ValueError as e:
    logger.error(f"Invalid session ID: {e}")
```

## Logging

The client logs execution progress:

**Initialization:**

```
INFO - UFO Client initialized for platform: windows
```

**Session State Changes:**

```
INFO - Session ID set to: session_20251104_143022_abc123
INFO - Agent name set to: HostAgent
INFO - Process name set to: notepad.exe
INFO - Root name set to: open_application
```

**Execution:**

```
INFO - Executing 5 actions in total
```

**Reset:**

```
INFO - Client state has been reset.
```

## Usage Example

### Complete Workflow

```python
import asyncio
from ufo.client.ufo_client import UFOClient
from aip.messages import ServerMessage, Command

async def main():
    # Initialize client
    client = UFOClient(
        mcp_server_manager=mcp_manager,
        computer_manager=computer_manager,
        client_id="device_windows_001",
        platform="windows"
    )
    
    # Simulate server message
    server_msg = ServerMessage(
        type=ServerMessageType.COMMAND,
        session_id="session_123",
        response_id="resp_456",
        agent_name="HostAgent",
        process_name="explorer.exe",
        root_name="navigate_folder",
        actions=[
            Command(action="click", parameters={"label": "File"}),
            Command(action="click", parameters={"label": "New Folder"})
        ],
        status=TaskStatus.PROCESSING
    )
    
    # Execute step
    results = await client.execute_step(server_msg)
    
    # Process results
    for result in results:
        print(f"Action: {result.action}")
        print(f"Status: {result.status}")
        print(f"Observation: {result.observation}")
    
    # Reset for next task
    client.reset()

asyncio.run(main())
```

## Best Practices

**Always Reset Between Tasks**

```python
async with client.task_lock:
    client.reset()
    await client.execute_step(new_server_response)
```

**Use Property Setters**

```python
# Good - validates input
client.session_id = "session_123"

# Bad - bypasses validation
client._session_id = "session_123"
```

**Log Execution Progress**

```python
self.logger.info(f"Executing {len(commands)} actions for {self.agent_name}")
```

**Handle Errors Gracefully**

```python
try:
    results = await client.execute_actions(commands)
except Exception as e:
    # Log and report error
    self.logger.error(f"Execution failed: {e}", exc_info=True)
    # Error is captured in results
```

## Integration Points

### WebSocket Client

The WebSocket client uses UFO Client for execution:

```python
action_results = await self.ufo_client.execute_step(server_response)
```

See [WebSocket Client](./websocket_client.md) for communication details.

### Command Router

The UFO Client delegates to the CommandRouter:

```python
action_results = await self.command_router.execute(
    agent_name=self.agent_name,
    process_name=self.process_name,
    root_name=self.root_name,
    commands=commands
)
```

See [Computer Manager](./computer_manager.md) for routing details.

### Computer Manager

Manages computer instances that execute commands:

```python
self.computer_manager.reset()  # Called during client reset
```

See [Computer Manager](./computer_manager.md) for management details.

### MCP Server Manager

Manages MCP server lifecycle:

```python
self.mcp_server_manager.reset()  # Called during client reset
```

See [MCP Integration](./mcp_integration.md) for MCP details.

## Next Steps

- [WebSocket Client](./websocket_client.md) - Communication layer
- [Computer Manager](./computer_manager.md) - Command routing
- [Device Info Provider](./device_info.md) - System profiling
- [MCP Integration](./mcp_integration.md) - Tool management
- [AIP Messages](../aip/messages.md) - Message structures
