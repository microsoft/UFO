# 🎯 UFO Client

!!!quote "The Execution Orchestrator"
    The **UFO Client** is the pure execution engine that receives commands from the server, routes them to appropriate tools via the CommandRouter, and aggregates results—**no reasoning, just deterministic execution**.

The UFO Client is the bridge between network communication and local tool execution.

---

## 📋 Overview

!!!info "Core Responsibilities"
    The UFO Client focuses exclusively on **stateless command execution**, delegating all decision-making to the server.

**Key Capabilities:**

| Capability | Description | Implementation |
|------------|-------------|----------------|
| **Command Execution** | Processes server commands deterministically | `execute_step()`, `execute_actions()` |
| **Session Management** | Tracks session state and metadata | Session ID, agent/process/root names |
| **Result Aggregation** | Collects and structures tool execution results | Returns `List[Result]` |
| **Thread Safety** | Ensures safe concurrent execution | `asyncio.Lock` (`task_lock`) |
| **State Management** | Maintains agent, process, and root names | Property setters with validation |
| **Manager Coordination** | Orchestrates ComputerManager and MCPServerManager | `reset()` cascades to all managers |

!!!success "Stateless Execution Philosophy"
    The UFO Client **never makes decisions**. It:
    
    - ✅ Executes commands sent by the server
    - ✅ Routes commands to the appropriate tools
    - ✅ Returns execution results
    - ❌ Does **not** decide which commands to run
    - ❌ Does **not** interpret user requests
    - ❌ Does **not** store long-term state

**Architectural Position:**

```mermaid
graph LR
    subgraph "Server Side (Orchestration)"
        Server[Agent Server]
        LLM[LLM Reasoning]
    end
    
    subgraph "Network Layer"
        WSC[WebSocket Client]
    end
    
    subgraph "Client Side (Execution)"
        UFC[UFO Client]
        CR[Command Router]
        Tools[MCP Tools]
    end
    
    Server -->|Commands| WSC
    WSC -->|execute_step| UFC
    UFC -->|execute| CR
    CR -->|tool calls| Tools
    Tools -->|results| CR
    CR -->|results| UFC
    UFC -->|results| WSC
    WSC -->|results| Server
    
    LLM -->|planning| Server
    
    style Server fill:#ffe0b2
    style UFC fill:#bbdefb
    style Tools fill:#c8e6c9
```

---

## 🏗️ Architecture

!!!success "Simple and Focused Design"
    The UFO Client has a minimal API surface—just initialization, execution, and reset.

### Component Structure

```mermaid
graph TB
    subgraph "UFOClient"
        State[Session State]
        Execution[Execution Methods]
        Dependencies[Manager Dependencies]
    end
    
    subgraph "Session State"
        State1[session_id]
        State2[agent_name]
        State3[process_name]
        State4[root_name]
        State5[task_lock]
    end
    
    subgraph "Execution Methods"
        Exec1[execute_step]
        Exec2[execute_actions]
        Exec3[reset]
    end
    
    subgraph "Dependencies"
        Dep1[CommandRouter]
        Dep2[ComputerManager]
        Dep3[MCPServerManager]
    end
    
    State --> State1
    State --> State2
    State --> State3
    State --> State4
    State --> State5
    
    Execution --> Exec1
    Execution --> Exec2
    Execution --> Exec3
    
    Dependencies --> Dep1
    Dependencies --> Dep2
    Dependencies --> Dep3
    
    Exec1 --> Exec2
    Exec2 --> Dep1
    Exec3 --> Dep2
    Exec3 --> Dep3
    
    style State fill:#e3f2fd
    style Execution fill:#f1f8e9
    style Dependencies fill:#fff3e0
```

**Class Attributes:**

| Attribute | Type | Purpose |
|-----------|------|---------|
| `mcp_server_manager` | `MCPServerManager` | Manages MCP server lifecycle |
| `computer_manager` | `ComputerManager` | Manages computer instances (tool namespaces) |
| `command_router` | `CommandRouter` | Routes commands to appropriate computers |
| `task_lock` | `asyncio.Lock` | Ensures thread-safe execution |
| `client_id` | `str` | Unique identifier for this client (default: `"client_001"`) |
| `platform` | `str` | Platform type (`"windows"` or `"linux"`) |
| `session_id` | `Optional[str]` | Current session identifier |
| `agent_name` | `Optional[str]` | Active agent (e.g., `"HostAgent"`, `"AppAgent"`) |
| `process_name` | `Optional[str]` | Process context (e.g., `"notepad.exe"`) |
| `root_name` | `Optional[str]` | Root operation name |

---

## 🚀 Initialization

!!!example "Creating a UFO Client"
    The UFO Client requires two manager instances: MCPServerManager and ComputerManager.

```python
from ufo.client.ufo_client import UFOClient
from ufo.client.computer import ComputerManager
from ufo.client.mcp.mcp_server_manager import MCPServerManager

# 1. Initialize MCP Server Manager
mcp_server_manager = MCPServerManager()
mcp_server_manager.create_servers_from_config()  # Load from config_dev.yaml

# 2. Initialize Computer Manager
computer_manager = ComputerManager(
    ufo_config.to_dict(),
    mcp_server_manager
)

# 3. Create UFO Client
client = UFOClient(
    mcp_server_manager=mcp_server_manager,
    computer_manager=computer_manager,
    client_id="device_windows_001",
    platform="windows"
)
```

**Constructor Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `mcp_server_manager` | `MCPServerManager` | ✅ Yes | - | MCP server lifecycle manager |
| `computer_manager` | `ComputerManager` | ✅ Yes | - | Computer instance manager |
| `client_id` | `str` | No | `"client_001"` | Unique client identifier |
| `platform` | `str` | No | Auto-detected | Platform type: `"windows"` or `"linux"` |

**Initialization Side Effects:**

1. Creates `CommandRouter` instance (delegates to ComputerManager)
2. Initializes `task_lock` (`asyncio.Lock()`)
3. Sets session state to `None` (session_id, agent_name, process_name, root_name)

---

## 📊 Session State Management

!!!info "Metadata Tracking"
    The UFO Client maintains contextual metadata for the current execution session.

### Session ID

**Purpose:** Unique identifier for the current task session

```python
# Set session ID (typically set by server)
client.session_id = "session_20251104_143022_abc123"

# Get session ID
current_session = client.session_id  # "session_20251104_143022_abc123"

# Clear session ID
client.reset()  # Sets session_id to None
```

**Validation:**

```python
# ✅ Valid
client.session_id = "session_123"
client.session_id = None

# ❌ Invalid - raises ValueError
client.session_id = 12345  # Not a string
```

### Agent Name

**Purpose:** Identifies the active agent (HostAgent, AppAgent, etc.)

```python
# Set agent name (from server message)
client.agent_name = "HostAgent"

# Get agent name
agent = client.agent_name  # "HostAgent"
```

**Common Agent Names:**

| Agent Name | Purpose |
|------------|---------|
| `HostAgent` | OS-level operations (start apps, manage files) |
| `AppAgent` | Application-specific operations (UI automation) |
| `FollowerAgent` | Follow predefined workflows |

### Process Name

**Purpose:** Identifies the process context

```python
# Set process name (from server message)
client.process_name = "notepad.exe"

# Get process name
process = client.process_name  # "notepad.exe"
```

**Usage:** Helps route commands to the correct application context

### Root Name

**Purpose:** Identifies the root operation name

```python
# Set root name (from server message)
client.root_name = "open_application"

# Get root name
root = client.root_name  # "open_application"
```

**Property Validation:**

All properties validate their inputs:

```python
try:
    client.agent_name = 123  # Not a string
except ValueError as e:
    print(e)  # "Agent name must be a string or None."
```

**Validation Table:**

| Property | Valid Types | Raises on Invalid |
|----------|-------------|-------------------|
| `session_id` | `str`, `None` | `ValueError` |
| `agent_name` | `str`, `None` | `ValueError` |
| `process_name` | `str`, `None` | `ValueError` |
| `root_name` | `str`, `None` | `ValueError` |

---

## ⚙️ Command Execution

### Execute Step (Main Entry Point)

!!!info "Single-Step Execution"
    `execute_step()` processes one complete server message, extracting metadata and executing all commands.

**Signature:**

```python
async def execute_step(self, response: ServerMessage) -> List[Result]:
    """
    Perform a single step execution.
    :param response: The ServerMessage instance to process.
    :return: A list of Result instances.
    """
```

**Execution Flow:**

```mermaid
sequenceDiagram
    participant WSC as WebSocket Client
    participant UFC as UFO Client
    participant CR as Command Router
    participant Tools
    
    WSC->>UFC: execute_step(ServerMessage)
    
    Note over UFC: 1. Extract Metadata
    UFC->>UFC: self.agent_name = response.agent_name
    UFC->>UFC: self.process_name = response.process_name
    UFC->>UFC: self.root_name = response.root_name
    
    Note over UFC: 2. Execute Actions
    UFC->>UFC: execute_actions(response.actions)
    
    UFC->>CR: command_router.execute(<br/>agent_name, process_name,<br/>root_name, commands)
    
    CR->>Tools: Route commands to tools
    Tools-->>CR: Results
    CR-->>UFC: List[Result]
    
    UFC-->>WSC: List[Result]
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

**Example Usage:**

```python
from aip.messages import ServerMessage

# Receive server message
server_response = ServerMessage.model_validate_json(msg)

# Execute step
action_results = await client.execute_step(server_response)

# action_results is List[Result]
for result in action_results:
    print(f"Action: {result.action}, Status: {result.status}")
```

### Execute Actions

!!!info "Batch Command Execution"
    `execute_actions()` executes a list of commands via the CommandRouter.

**Signature:**

```python
async def execute_actions(self, commands: Optional[List[Command]]) -> List[Result]:
    """
    Execute the actions provided by the server.
    :param commands: List of actions to execute.
    :returns: Results of the executed actions.
    """
```

**Implementation:**

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

**Example:**

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

**Command Execution Table:**

| Step | Action | Component |
|------|--------|-----------|
| 1 | Receive commands | UFO Client |
| 2 | Log command count | UFO Client |
| 3 | Call CommandRouter | UFO Client |
| 4 | Route to Computer | CommandRouter |
| 5 | Execute via MCP | Computer |
| 6 | Collect results | CommandRouter |
| 7 | Return results | UFO Client |

See [Computer Manager](./computer_manager.md) for command routing details.

---

## 🔄 State Reset

!!!warning "Critical for Multi-Task Execution"
    Always reset state between tasks to prevent data leakage between sessions.

**Signature:**

```python
def reset(self):
    """Reset session state and dependent managers."""
```

**Implementation:**

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

**Reset Cascade:**

```mermaid
graph TD
    Reset[client.reset]
    
    Reset --> S1[session_id = None]
    Reset --> S2[agent_name = None]
    Reset --> S3[process_name = None]
    Reset --> S4[root_name = None]
    
    Reset --> M1[computer_manager.reset]
    Reset --> M2[mcp_server_manager.reset]
    
    M1 --> C1[Clear computer instances]
    M2 --> M3[Reset MCP servers]
    
    style Reset fill:#ffcdd2
    style M1 fill:#fff9c4
    style M2 fill:#fff9c4
```

**When to Reset:**

| Scenario | Why Reset |
|----------|-----------|
| **Before starting new task** | Clear previous task state |
| **On task completion** | Prepare for next task |
| **On task failure** | Clean up failed state |
| **On server disconnection** | Reset to known good state |

!!!tip "Automatic Reset"
    The WebSocket client automatically calls `reset()` before starting new tasks:
    
    ```python
    async with self.ufo_client.task_lock:
        self.ufo_client.reset()  # Automatic
        await self.task_protocol.send_task_request(...)
    ```

---

## 🔒 Thread Safety

!!!success "Async-Safe Execution"
    The UFO Client uses `asyncio.Lock` to prevent concurrent state modifications.

**Lock Implementation:**

```python
# In UFOClient.__init__
self.task_lock = asyncio.Lock()
```

**Usage in WebSocket Client:**

```python
# In WebSocket client
async with client.task_lock:
    client.reset()
    await client.execute_step(server_response)
```

**Protected Operations:**

| Operation | Protected By | Reason |
|-----------|--------------|--------|
| Session state modifications | `task_lock` | Prevent race conditions |
| Command execution | `task_lock` | Ensure one task at a time |
| State reset | `task_lock` | Atomic reset operation |

!!!warning "Single Task Execution"
    The lock ensures only **one task executes at a time**. Attempting concurrent execution will block until the lock is released.

---

## 📋 Complete Execution Pipeline

```mermaid
sequenceDiagram
    participant Server
    participant WSC as WebSocket Client
    participant UFC as UFO Client
    participant CR as Command Router
    participant CM as Computer Manager
    participant Comp as Computer
    participant Tool as MCP Tool
    
    Note over Server,Tool: Full Execution Pipeline
    
    Server->>WSC: COMMAND message
    WSC->>UFC: execute_step(ServerMessage)
    
    Note over UFC: Extract Metadata
    UFC->>UFC: agent_name = "HostAgent"
    UFC->>UFC: process_name = "explorer.exe"
    UFC->>UFC: root_name = "navigate"
    
    Note over UFC: Execute Actions
    UFC->>CR: execute(agent, process, root, commands)
    
    CR->>CM: Route commands
    CM->>Comp: Get computer instance
    Comp->>Tool: Execute tool
    
    Tool-->>Comp: Result
    Comp-->>CM: Result
    CM-->>CR: List[Result]
    CR-->>UFC: List[Result]
    
    UFC-->>WSC: List[Result]
    WSC->>Server: COMMAND_RESULTS (via AIP)
```

---

## ⚠️ Error Handling

### Command Execution Errors

!!!info "Error Capture in Results"
    Individual command failures are captured in `Result` objects, not thrown as exceptions.

**Error Result Structure:**

```python
from aip.messages import Result, ResultStatus

error_result = Result(
    action="click",
    status=ResultStatus.ERROR,
    error_message="Control not found",
    observation="Failed to locate control with label 'Start'"
)
```

**Handling Execution Errors:**

```python
try:
    results = await client.execute_actions(commands)
    
    # Check each result
    for result in results:
        if result.status == ResultStatus.ERROR:
            logger.error(f"Action {result.action} failed: {result.error_message}")
        else:
            logger.info(f"Action {result.action} succeeded")
            
except Exception as e:
    # Unexpected error (not tool failure)
    logger.error(f"Command execution failed: {e}", exc_info=True)
```

### Property Validation Errors

```python
try:
    client.session_id = 12345  # Invalid type
except ValueError as e:
    logger.error(f"Invalid session ID: {e}")
    # ValueError: Session ID must be a string or None.
```

**Error Handling Table:**

| Error Type | Raised By | Handling |
|------------|-----------|----------|
| Tool execution error | MCP tools | Captured in `Result.error_message` |
| Property validation error | Property setters | `ValueError` exception |
| Unexpected errors | Any component | Logged, may propagate |

---

## 📝 Logging

!!!info "Execution Visibility"
    The UFO Client logs all major events for debugging and monitoring.

**Log Examples:**

**Initialization:**

```log
INFO - UFO Client initialized for platform: windows
```

**Session State Changes:**

```log
INFO - Session ID set to: session_20251104_143022_abc123
INFO - Agent name set to: HostAgent
INFO - Process name set to: notepad.exe
INFO - Root name set to: open_application
```

**Execution:**

```log
INFO - Executing 5 actions in total
```

**Reset:**

```log
INFO - Client state has been reset.
```

**Log Level Recommendations:**

| Environment | Level | Rationale |
|-------------|-------|-----------|
| Development | `DEBUG` | See all operations |
| Staging | `INFO` | Track execution flow |
| Production | `INFO` | Monitor without spam |
| Troubleshooting | `DEBUG` | Diagnose issues |

---

## 💡 Usage Example

### Complete Workflow

!!!example "End-to-End Execution"
    This example shows how to use the UFO Client in a typical workflow.

```python
import asyncio
from ufo.client.ufo_client import UFOClient
from aip.messages import ServerMessage, Command, ServerMessageType, TaskStatus

async def main():
    # 1. Initialize client
    client = UFOClient(
        mcp_server_manager=mcp_manager,
        computer_manager=computer_manager,
        client_id="device_windows_001",
        platform="windows"
    )
    
    # 2. Simulate server message
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
    
    # 3. Execute step
    async with client.task_lock:  # Thread-safe execution
        results = await client.execute_step(server_msg)
    
    # 4. Process results
    for result in results:
        print(f"Action: {result.action}")
        print(f"Status: {result.status}")
        print(f"Observation: {result.observation}")
        if result.status == ResultStatus.ERROR:
            print(f"Error: {result.error_message}")
    
    # 5. Reset for next task
    client.reset()

asyncio.run(main())
```

---

## ✅ Best Practices

### Development Best Practices

!!!tip "Defensive Programming"
    
    **1. Always Reset Between Tasks**
    ```python
    async with client.task_lock:
        client.reset()  # Clear previous state
        await client.execute_step(new_server_response)
    ```
    
    **2. Use Property Setters (Not Direct Assignment)**
    ```python
    # ✅ Good - validates input
    client.session_id = "session_123"
    
    # ❌ Bad - bypasses validation
    client._session_id = "session_123"
    ```
    
    **3. Log Execution Progress**
    ```python
    self.logger.info(f"Executing {len(commands)} actions for {self.agent_name}")
    ```
    
    **4. Handle Errors Gracefully**
    ```python
    try:
        results = await client.execute_actions(commands)
    except Exception as e:
        self.logger.error(f"Execution failed: {e}", exc_info=True)
        # Error is also captured in results
    ```

### Production Best Practices

!!!success "Reliability and Monitoring"
    
    **1. Use Thread Locks Consistently**
    ```python
    # Always use task_lock for state operations
    async with client.task_lock:
        client.reset()
        results = await client.execute_step(msg)
    ```
    
    **2. Monitor Execution Times**
    ```python
    import time
    
    start = time.time()
    results = await client.execute_actions(commands)
    duration = time.time() - start
    
    if duration > 60:  # Alert if > 1 minute
        logger.warning(f"Slow execution: {duration}s for {len(commands)} commands")
    ```
    
    **3. Validate Results**
    ```python
    # Check for failures
    failed_actions = [r for r in results if r.status == ResultStatus.ERROR]
    if failed_actions:
        logger.error(f"{len(failed_actions)} actions failed")
        # Report to monitoring system
    ```

---

## 🔗 Integration Points

### WebSocket Client Integration

!!!info "Network Communication Layer"
    The WebSocket client uses UFO Client for all command execution.

**Integration:**

```python
# In WebSocket client
action_results = await self.ufo_client.execute_step(server_response)
```

See [WebSocket Client](./websocket_client.md) for communication details.

### Command Router Integration

!!!info "Command Delegation"
    The UFO Client delegates all execution to the CommandRouter.

**Integration:**

```python
action_results = await self.command_router.execute(
    agent_name=self.agent_name,
    process_name=self.process_name,
    root_name=self.root_name,
    commands=commands
)
```

See [Computer Manager](./computer_manager.md) for routing details.

### Computer Manager Integration

!!!info "Computer Instance Management"
    The Computer Manager maintains computer instances for tool execution.

**Integration:**

```python
# Reset cascades to computer manager
self.computer_manager.reset()
```

See [Computer Manager](./computer_manager.md) for management details.

### MCP Server Manager Integration

!!!info "MCP Server Lifecycle"
    The MCP Server Manager handles MCP server creation and cleanup.

**Integration:**

```python
# Reset cascades to MCP server manager
self.mcp_server_manager.reset()
```

See [MCP Integration](./mcp_integration.md) for MCP details.

---

## 🚀 Next Steps

!!!tip "Continue Learning"
    
    **1. Understand Network Communication**
    
    Learn how the WebSocket client uses UFO Client:
    
    👉 [WebSocket Client](./websocket_client.md)
    
    **2. Explore Command Routing**
    
    See how commands are routed to the right tools:
    
    👉 [Computer Manager](./computer_manager.md)
    
    **3. Study Device Profiling**
    
    Understand device information collection:
    
    👉 [Device Info Provider](./device_info.md)
    
    **4. Learn About MCP Integration**
    
    Deep dive into MCP server management:
    
    👉 [MCP Integration](./mcp_integration.md)
    
    **5. Master AIP Messages**
    
    Understand message structures:
    
    👉 [AIP Messages](../aip/messages.md)

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
