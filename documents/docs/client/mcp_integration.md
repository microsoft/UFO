# MCP Integration in Agent Client

The **MCP (Model Context Protocol) Integration** enables the Agent Client to execute tools through a unified interface. This document explains how the client integrates with MCP servers.

!!!info "Complete MCP Documentation"
    For comprehensive MCP documentation, see the [MCP Section](../mcp/overview.md) which covers:
    
    - [MCP Overview](../mcp/overview.md) - Architecture and concepts
    - [Data Collection Servers](../mcp/data_collection.md) - Observation tools
    - [Action Servers](../mcp/action.md) - Execution tools  
    - [Configuration Guide](../mcp/configuration.md) - How to configure MCP
    - [Local Servers](../mcp/local_servers.md) - Built-in servers
    - [Remote Servers](../mcp/remote_servers.md) - HTTP/Stdio deployment

## MCP in Client Architecture

MCP provides the **tool execution layer** in the UFO² client:

- **Computer** manages MCP servers and routes commands to tools
- **MCP Server Manager** handles server lifecycle and registration
- **MCP Registry** stores server factories for local servers

## Client Execution Flow

```
AIP Command → UFOClient → Computer → MCP Tool → Result
     │           │           │          │         │
     │           │           │          │         │
  Server      Execute    Route to   Execute   Return to
  Request     Step       Tool       in Thread  Server
```

See [Computer](computer.md) for detailed tool execution.

## Key Integration Points

### Computer Class

The `Computer` class manages MCP servers and tool execution:

```python
# Computer initializes MCP servers
computer = Computer(
    name="my_computer",
    process_name="notepad.exe",
    mcp_server_manager=mcp_manager,
    data_collection_servers_config=[...],
    action_servers_config=[...]
)

await computer.async_init()  # Registers all tools
```

### Tool Registration

Tools are automatically registered during computer initialization:

```python
# Register data collection servers
await computer.register_mcp_servers(
    data_collection_servers,
    tool_type="data_collection"
)

# Register action servers
await computer.register_mcp_servers(
    action_servers,
    tool_type="action"
)
```

### Tool Execution

Tools are executed through the Computer interface:

```python
from aip.messages import Command

# Server sends command
command = Command(
    tool_name="take_screenshot",
    tool_type="data_collection",
    parameters={"region": "active_window"}
)

# Client executes via Computer
tool_call = computer.command2tool(command)
result = await computer.run_actions([tool_call])
```

See [Computer](./computer.md) for tool execution details.

## Configuration

MCP servers are configured in `config/ufo/mcp.yaml`:

```yaml
HostAgent:
  default:
    data_collection:
      - namespace: UICollector
        type: local
        reset: false
    action:
      - namespace: HostUIExecutor
        type: local
        reset: false
```

!!!tip "Configuration Details"
    For complete configuration guide, see [MCP Configuration](../mcp/configuration.md).

## Related Client Components

- [Computer](computer.md) - MCP tool execution layer
- [Computer Manager](computer_manager.md) - Multi-computer management
- [UFO Client](ufo_client.md) - Command execution orchestration

## Related MCP Documentation

- [MCP Overview](../mcp/overview.md) - Architecture and concepts
- [Data Collection Servers](../mcp/data_collection.md) - Observation tools
- [Action Servers](../mcp/action.md) - Execution tools  
- [Configuration Guide](../mcp/configuration.md) - How to configure MCP
- [Local Servers](../mcp/local_servers.md) - Built-in servers
- [Remote Servers](../mcp/remote_servers.md) - HTTP/Stdio deployment
