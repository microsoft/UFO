# MCP Configuration Reference

This document describes the Model Context Protocol (MCP) server configuration system in UFO2.

!!!info "What is MCP?"
    The Model Context Protocol (MCP) provides a standardized way for agents to interact with external tools and services. MCP servers handle data collection and action execution for different agents and applications.

## Overview

**File**: `config/ufo/mcp.yaml`

MCP configuration defines which servers are available to each agent for data collection and action execution. Servers can be either:
- **Local (stdio)** - Run as local processes with stdio communication
- **HTTP** - Accessed over HTTP protocol

## Configuration Structure

!!!note "Agent-Based Organization"
    MCP servers are organized by agent type and application, allowing fine-grained control over which tools are available in different contexts.

```yaml
AgentName:              # e.g., "HostAgent", "AppAgent", "HardwareAgent"
  sub_type:             # "default" or specific app (e.g., "WINWORD.EXE")
    data_collection:    # Servers for collecting data/observations
      - namespace: ...
        type: ...
        # ... server config
    action:             # Servers for executing actions
      - namespace: ...
        type: ...
        # ... server config
```

## Server Configuration Fields

### Common Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | String | ? Yes | Unique identifier for the MCP server |
| `type` | String | ? Yes | Server type: `"local"` or `"http"` |
| `reset` | Boolean | No | Whether to reset server when switching contexts (default: `false`) |

### Local Server Fields

```yaml
    - namespace: UICollector
      type: local
      start_args: []
      reset: false
    ```

| Field | Type | Description |
|-------|------|-------------|
| `start_args` | List[String] | Command-line arguments to pass when starting the server process |

### HTTP Server Fields

```yaml
    - namespace: HardwareCollector
      type: http
      host: "localhost"
      port: 8006
      path: "/mcp"
      reset: false
    ```

| Field | Type | Description |
|-------|------|-------------|
| `host` | String | Server hostname or IP address |
| `port` | Integer | Server port number |
| `path` | String | HTTP endpoint path |

## Agent Types

### HostAgent

Controls desktop-level operations and application coordination.

```yaml
    HostAgent:
      default:
        data_collection:
          - namespace: UICollector
            type: local
            start_args: []
            reset: false
        action:
          - namespace: HostUIExecutor
            type: local
            start_args: []
            reset: false
          - namespace: CommandLineExecutor
            type: local
            start_args: []
            reset: false
    ```

**Available Servers**:
- **UICollector** - Collects UI element information from desktop
- **HostUIExecutor** - Executes desktop-level UI actions
- **CommandLineExecutor** - Executes command-line commands

### AppAgent

Controls application-specific operations.

#### Default Configuration

```yaml
    AppAgent:
      default:
        data_collection:
          - namespace: UICollector
            type: local
            start_args: []
            reset: false
        action:
          - namespace: AppUIExecutor
            type: local
            start_args: []
            reset: false
          - namespace: CommandLineExecutor
            type: local
            start_args: []
            reset: false
    ```

**Available Servers**:
- **UICollector** - Collects UI element information from applications
- **AppUIExecutor** - Executes application-level UI actions
- **CommandLineExecutor** - Executes command-line commands

#### Application-Specific Configurations

!!!tip "Custom App Configurations"
    Override the default configuration for specific applications by using the app's process name as the sub_type.

##### Microsoft Word (WINWORD.EXE)

```yaml
WINWORD.EXE:
  data_collection:
    - namespace: UICollector
      type: local
      start_args: []
      reset: false
  action:
    - namespace: AppUIExecutor
      type: local
      start_args: []
      reset: false
    - namespace: WordCOMExecutor
      type: local
      start_args: []
      reset: true  # Reset when switching documents
```

**Additional Server**: **WordCOMExecutor** - Word COM API automation

##### Microsoft Excel (EXCEL.EXE)

```yaml
EXCEL.EXE:
  data_collection:
    - namespace: UICollector
      type: local
      start_args: []
      reset: false
  action:
    - namespace: AppUIExecutor
      type: local
      start_args: []
      reset: false
    - namespace: ExcelCOMExecutor
      type: local
      start_args: []
      reset: true
```

**Additional Server**: **ExcelCOMExecutor** - Excel COM API automation

##### Microsoft PowerPoint (POWERPNT.EXE)

```yaml
POWERPNT.EXE:
  data_collection:
    - namespace: UICollector
      type: local
      start_args: []
      reset: false
  action:
    - namespace: AppUIExecutor
      type: local
      start_args: []
      reset: false
    - namespace: PowerPointCOMExecutor
      type: local
      start_args: []
      reset: true
```

**Additional Server**: **PowerPointCOMExecutor** - PowerPoint COM API automation

##### Windows Explorer (explorer.exe)

```yaml
explorer.exe:
  data_collection:
    - namespace: UICollector
      type: local
      start_args: []
      reset: false
  action:
    - namespace: AppUIExecutor
      type: local
      start_args: []
      reset: false
    - namespace: PDFReaderExecutor
      type: local
      start_args: []
      reset: true
```

**Additional Server**: **PDFReaderExecutor** - PDF file operations

### ConstellationAgent

Manages multi-device coordination and constellation editing.

```yaml
    ConstellationAgent:
      default:
        action:
          - namespace: ConstellationEditor
            type: local
            start_args: []
            reset: false
    ```

**Available Servers**:
- **ConstellationEditor** - Edits device constellations and task assignments

### HardwareAgent

Controls hardware devices via HTTP MCP servers.

```yaml
    HardwareAgent:
      default:
        data_collection:
          - namespace: HardwareCollector
            type: http
            host: "localhost"
            port: 8006
            path: "/mcp"
            reset: false
        action:
          - namespace: HardwareExecutor
            type: http
            host: "localhost"
            port: 8006
            path: "/mcp"
            reset: false
    ```

**Available Servers**:
- **HardwareCollector** - Collects hardware device status and information
- **HardwareExecutor** - Executes actions on hardware devices

!!!warning "HTTP Server Required"
    HardwareAgent requires a running MCP HTTP server on the specified host and port.

### LinuxAgent

Controls Linux systems via HTTP MCP servers.

```yaml
    LinuxAgent:
      default:
        action:
          - namespace: BashExecutor
            type: http
            host: "localhost"
            port: 8010
            path: "/mcp"
            reset: false
    ```

**Available Servers**:
- **BashExecutor** - Executes bash commands on Linux systems

!!!warning "Cross-Platform Remote Execution"
    LinuxAgent enables Windows-based UFO2 to control remote Linux systems through HTTP MCP servers.

## Server Reset Behavior

!!!note "Reset Field Behavior"
    The `reset` field determines whether an MCP server should be reset when the agent switches contexts (e.g., switching between different documents or applications).

- **`reset: false`** - Server persists across context switches (default)
- **`reset: true`** - Server is restarted when switching contexts

!!!tip "When to Use Reset"
    Set `reset: true` for servers that maintain application-specific state:
    - COM executors (Word, Excel, PowerPoint) that track open documents
    - Application-specific tools that need clean state per task

## Adding Custom MCP Servers

```yaml
    AppAgent:
      MyApp.exe:  # Your application's process name
        data_collection:
          - namespace: UICollector
            type: local
            start_args: []
            reset: false
        action:
          - namespace: AppUIExecutor
            type: local
            start_args: []
            reset: false
          # Your custom server
          - namespace: MyCustomExecutor
            type: local
            start_args: ["--config", "path/to/config.json"]
            reset: true
    ```

### For Local Servers

1. Implement the MCP server protocol
2. Add server configuration to `mcp.yaml`
3. Ensure server executable is in PATH or provide full path in `start_args`

### For HTTP Servers

1. Run your MCP HTTP server
2. Add server configuration with correct `host`, `port`, and `path`
3. Ensure server is accessible from UFO2

## Access Patterns

```python
    from config.config_loader import get_ufo_config

    config = get_ufo_config()

    # Access MCP configuration
    mcp_config = config.MCP  # or config["MCP"]
    
    # Get agent-specific MCP config
    host_agent_mcp = mcp_config.get("HostAgent", {})
    app_agent_mcp = mcp_config.get("AppAgent", {})
    
    # Get app-specific config
    word_config = app_agent_mcp.get("WINWORD.EXE", app_agent_mcp.get("default", {}))
    ```

## Best Practices

!!!tip "DO - Recommended Practices"
    - ? **Use `reset: true`** for stateful COM executors
    - ? **Keep default configuration** for common cases
    - ? **Group related servers** by agent type
    - ? **Document custom servers** with comments in YAML
    - ? **Test server connectivity** before deploying

!!!danger "DON'T - Anti-Patterns"
    - ? **Don't hardcode credentials** - use environment variables
    - ? **Don't expose MCP HTTP servers** to public networks without authentication
    - ? **Don't forget to start HTTP servers** before using them
    - ? **Don't use `reset: true`** for shared infrastructure servers

## Troubleshooting

### Server Connection Issues

!!!bug "Cannot Connect to Local Server"
    **Symptoms**: "Failed to start MCP server" errors
    
    **Solutions**:
    - Verify server executable is in PATH
    - Check `start_args` are correct
    - Review server logs for startup errors

!!!bug "HTTP Server Not Responding"
    **Symptoms**: Connection timeout or refused errors
    
    **Solutions**:
    - Verify HTTP server is running: `curl http://localhost:PORT/PATH`
    - Check firewall rules allow the connection
    - Verify `host`, `port`, and `path` are correct

### Reset Issues

!!!bug "Server State Persists Unexpectedly"
    **Symptoms**: Server uses data from previous contexts
    
    **Solution**: Set `reset: true` for the affected server

## Next Steps

!!!note "Learn More"
    - **[Field Reference](./field_reference.md)** - Complete configuration field documentation
    - **[Extending Configuration](./extending.md)** - Add custom MCP servers
    - **[Configuration Overview](./overview.md)** - Understanding the config system
