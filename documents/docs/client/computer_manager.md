# Computer Manager

The **Computer Manager** manages multiple computer instances, each representing a different execution namespace with its own set of MCP servers and tools.

## Overview

The Computer Manager provides:

- **Multi-Computer Management** - Create and manage multiple computer instances
- **Namespace Isolation** - Separate tool namespaces for different contexts
- **Command Routing** - Route commands to appropriate computer instances
- **MCP Server Configuration** - Configure data collection and action servers
- **Lifecycle Management** - Initialize, reset, and tear down computers

## Architecture

```
┌────────────────────────────────────────────────────┐
│            ComputerManager                         │
├────────────────────────────────────────────────────┤
│  Computer Instances:                               │
│  • default_agent - Default computer instance       │
│  • process_specific - Per-process computers        │
│  • custom_contexts - Custom computer instances     │
├────────────────────────────────────────────────────┤
│  Command Routing:                                  │
│  • CommandRouter - Route by agent/process/root     │
│  • Namespace resolution                            │
│  • Tool lookup and execution                       │
├────────────────────────────────────────────────────┤
│  Configuration:                                    │
│  • Data collection servers config                  │
│  • Action servers config                           │
│  • MCP server manager integration                  │
└────────────────────────────────────────────────────┘
```

## Computer Instances

Each computer instance is an isolated execution environment with its own:

- **MCP Servers** - Data collection and action servers
- **Tool Registry** - Available tools and their configurations
- **Meta Tools** - Built-in computer operations
- **Execution Context** - Agent name, process name, root name

### Computer Namespaces

**Data Collection Namespace:**
- Tools for gathering information
- Screenshot capture
- UI element detection
- Application state queries

**Action Namespace:**
- Tools for performing actions
- GUI automation (click, type, etc.)
- Application control
- File system operations

!!!info "Namespace Isolation"
    Each namespace can have different MCP servers, allowing fine-grained control over data collection vs. action execution.

## Initialization

```python
from ufo.client.computer import ComputerManager
from ufo.client.mcp.mcp_server_manager import MCPServerManager
from config.config_loader import get_ufo_config

# Get UFO configuration
ufo_config = get_ufo_config()

# Initialize MCP server manager
mcp_server_manager = MCPServerManager()

# Create computer manager
computer_manager = ComputerManager(
    ufo_config.to_dict(),
    mcp_server_manager
)
```

**Configuration Structure:**

The `ufo_config` contains:

```python
{
    "data_collection_servers": [
        {
            "namespace": "screenshot_collector",
            "type": "local",
            "module": "ufo.client.mcp.local_servers.screenshot_server",
            "reset": False
        },
        {
            "namespace": "ui_collector",
            "type": "local",
            "module": "ufo.client.mcp.local_servers.ui_server",
            "reset": False
        }
    ],
    "action_servers": [
        {
            "namespace": "gui_automator",
            "type": "local",
            "module": "ufo.client.mcp.local_servers.automation_server",
            "reset": False
        }
    ]
}
```

## Command Router

The `CommandRouter` routes commands to the appropriate computer instance and tool:

```python
from ufo.client.computer import CommandRouter
from aip.messages import Command, Result

router = CommandRouter(computer_manager=computer_manager)

# Execute commands
results = await router.execute(
    agent_name="HostAgent",
    process_name="explorer.exe",
    root_name="navigate_folder",
    commands=[
        Command(action="click", parameters={"label": "File"}),
        Command(action="type_text", parameters={"text": "Hello"})
    ]
)
```

### Routing Logic

```
Command → Resolve Computer → Lookup Tool → Execute → Return Result
    │           │               │            │           │
    │           │               │            │           │
Agent/       Computer        MCP Tool      Isolated   Result
Process/     Instance        Registry      Thread     Object
Root Name                                  Pool
```

**Step-by-Step:**

1. **Resolve Computer Instance**
   - Based on `agent_name`, `process_name`, `root_name`
   - Falls back to default computer if not found

2. **Lookup Tool**
   - Search in tool registry by action name
   - Raise error if tool not found

3. **Execute Tool**
   - Run in isolated thread pool with timeout
   - Capture result or error

4. **Return Result**
   - Structured Result object with status, observation, error

### Command Execution

```python
async def execute(
    self,
    agent_name: str,
    process_name: str,
    root_name: str,
    commands: List[Command]
) -> List[Result]:
    """Execute a list of commands."""
    
    results = []
    
    for command in commands:
        try:
            # Get computer instance
            computer = self.computer_manager.get_computer(
                agent_name, process_name, root_name
            )
            
            # Execute command
            result = await computer.execute_command(command)
            results.append(result)
            
        except Exception as e:
            # Create error result
            error_result = Result(
                action=command.action,
                status=ResultStatus.ERROR,
                error_message=str(e),
                observation=f"Failed to execute {command.action}"
            )
            results.append(error_result)
    
    return results
```

## Computer Lifecycle

### Creation

Computers are created on demand:

```python
def get_or_create_computer(
    self,
    agent_name: str,
    process_name: str,
    root_name: str
) -> Computer:
    """Get existing computer or create new one."""
    
    key = f"{agent_name}_{process_name}_{root_name}"
    
    if key not in self.computers:
        computer = Computer(
            name=key,
            process_name=process_name,
            mcp_server_manager=self.mcp_server_manager,
            data_collection_servers_config=self.data_collection_config,
            action_servers_config=self.action_config
        )
        await computer.async_init()  # Initialize MCP servers
        self.computers[key] = computer
    
    return self.computers[key]
```

### Initialization

Each computer initializes its MCP servers asynchronously:

```python
class Computer:
    async def async_init(self) -> None:
        """Asynchronous initialization."""
        
        # Initialize data collection servers
        self._data_collection_servers = self._init_data_collection_servers()
        
        # Initialize action servers
        self._action_servers = self._init_action_servers()
        
        # Register MCP servers in parallel
        await asyncio.gather(
            self.register_mcp_servers(
                self._data_collection_servers,
                tool_type="data_collection"
            ),
            self.register_mcp_servers(
                self._action_servers,
                tool_type="action"
            )
        )
```

!!!tip "Parallel Initialization"
    MCP servers are registered in parallel for faster startup.

### Reset

Reset clears all computer instances and their state:

```python
def reset(self):
    """Reset all computer instances."""
    
    # Clear all computers
    for computer in self.computers.values():
        computer.cleanup()
    
    self.computers.clear()
    
    self.logger.info("Computer manager has been reset.")
```

**When to Reset:**

- Before starting a new task
- On task completion/failure
- On client reconnection

## Tool Registry

Each computer maintains a registry of available tools:

```python
class Computer:
    def __init__(self, ...):
        self._tools_registry: Dict[str, MCPToolCall] = {}
    
    async def register_mcp_servers(
        self,
        servers: Dict[str, BaseMCPServer],
        tool_type: str
    ):
        """Register MCP servers and their tools."""
        
        for namespace, server in servers.items():
            # Get tools from server
            tools = await server.list_tools()
            
            # Register each tool
            for tool in tools:
                tool_name = f"{namespace}.{tool.name}"
                self._tools_registry[tool_name] = MCPToolCall(
                    mcp_server=server,
                    tool_name=tool.name,
                    namespace=namespace,
                    tool_type=tool_type
                )
```

### Tool Lookup

```python
def get_tool(self, action: str) -> MCPToolCall:
    """Look up tool by action name."""
    
    if action in self._tools_registry:
        return self._tools_registry[action]
    
    # Try namespace-qualified lookup
    for namespace in self._action_servers.keys():
        qualified_name = f"{namespace}.{action}"
        if qualified_name in self._tools_registry:
            return self._tools_registry[qualified_name]
    
    raise ValueError(f"Tool '{action}' not found in registry")
```

## Tool Execution

### Isolated Execution

Tools are executed in isolated thread pools to prevent blocking:

```python
class Computer:
    def __init__(self, ...):
        # Thread pool for isolating blocking MCP tool calls
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=10,
            thread_name_prefix="mcp_tool_"
        )
        
        # Tool execution timeout (seconds)
        self._tool_timeout = 6000  # 100 minutes
```

### Execute Command

```python
async def execute_command(self, command: Command) -> Result:
    """Execute a single command."""
    
    try:
        # Lookup tool
        tool = self.get_tool(command.action)
        
        # Execute with timeout
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            self._executor,
            tool.execute,
            command.parameters
        )
        
        result = await asyncio.wait_for(
            future,
            timeout=self._tool_timeout
        )
        
        return Result(
            action=command.action,
            status=ResultStatus.SUCCESS,
            observation=result.observation,
            data=result.data
        )
        
    except asyncio.TimeoutError:
        return Result(
            action=command.action,
            status=ResultStatus.ERROR,
            error_message=f"Tool execution timeout ({self._tool_timeout}s)",
            observation="Tool execution exceeded time limit"
        )
    
    except Exception as e:
        return Result(
            action=command.action,
            status=ResultStatus.ERROR,
            error_message=str(e),
            observation=f"Tool execution failed: {e}"
        )
```

!!!warning "Timeout Protection"
    Tools have a default 100-minute timeout. Adjust `_tool_timeout` for different needs.

## Meta Tools

Computers support meta tools - built-in operations that don't require MCP servers:

```python
class Computer:
    @Computer.meta_tool("get_system_info")
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            "cpu_count": os.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / (1024**3),
            "platform": platform.system()
        }
    
    @Computer.meta_tool("ping")
    def ping(self) -> str:
        """Health check."""
        return "pong"
```

**Meta Tool Registration:**

```python
def __init__(self, ...):
    # Register meta tools
    for attr in dir(self):
        method = getattr(self, attr)
        if callable(method) and hasattr(method, "_meta_tool_name"):
            name = getattr(method, "_meta_tool_name")
            self._meta_tools[name] = method
```

## Configuration

### MCP Server Configuration

**Data Collection Servers:**

```yaml
data_collection_servers:
  - namespace: screenshot_collector
    type: local
    module: ufo.client.mcp.local_servers.screenshot_server
    reset: false
    
  - namespace: ui_detector
    type: local
    module: ufo.client.mcp.local_servers.ui_detection_server
    reset: false
```

**Action Servers:**

```yaml
action_servers:
  - namespace: gui_automator
    type: local
    module: ufo.client.mcp.local_servers.automation_server
    reset: false
    
  - namespace: file_ops
    type: local
    module: ufo.client.mcp.local_servers.file_server
    reset: false
```

### Server Types

**Local MCP Servers:**
- Run in same process via FastMCP
- Fastest execution
- Shared memory with client

**Remote MCP Servers:**
- Connect via HTTP
- Can run on different machines
- Useful for resource-intensive tools

See [MCP Integration](./mcp_integration.md) for MCP server details.

## Best Practices

**Use Unique Namespaces**

```python
# Good - clear namespace separation
data_collection_servers:
  - namespace: screenshot_collector
  - namespace: ui_detector

# Bad - generic namespaces
data_collection_servers:
  - namespace: default
  - namespace: default_2
```

**Configure Appropriate Timeouts**

```python
# For long-running operations
computer._tool_timeout = 600  # 10 minutes

# For quick operations
computer._tool_timeout = 30  # 30 seconds
```

**Handle Tool Failures Gracefully**

```python
result = await computer.execute_command(command)

if result.status == ResultStatus.ERROR:
    logger.error(f"Tool failed: {result.error_message}")
    # Implement recovery logic
```

**Reset Between Tasks**

```python
computer_manager.reset()  # Clear all computers and state
```

## Integration Points

### UFO Client

The UFO Client uses the Command Router:

```python
action_results = await self.command_router.execute(
    agent_name=self.agent_name,
    process_name=self.process_name,
    root_name=self.root_name,
    commands=commands
)
```

See [UFO Client](./ufo_client.md) for execution details.

### MCP Server Manager

The Computer Manager uses MCP Server Manager to create servers:

```python
mcp_server = self.mcp_server_manager.create_or_get_server(
    mcp_config=server_config,
    reset=False,
    process_name=process_name
)
```

See [MCP Integration](./mcp_integration.md) for MCP details.

## Next Steps

- [UFO Client](./ufo_client.md) - Execution orchestration
- [MCP Integration](./mcp_integration.md) - MCP server management
- [Quick Start](./quick_start.md) - Get started with client
- [Configuration](../configurations/overview.md) - UFO configuration
