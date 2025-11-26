# MCP Configuration Reference

This document provides a quick reference for MCP (Model Context Protocol) server configuration in UFO².

For comprehensive MCP configuration guide with examples, best practices, and detailed explanations, see:

- **[MCP Configuration Guide](../../mcp/configuration.md)** - Complete configuration documentation
- [MCP Overview](../../mcp/overview.md) - Architecture and concepts
- [Data Collection Servers](../../mcp/data_collection.md) - Observation tools
- [Action Servers](../../mcp/action.md) - Execution tools

## Quick Reference

**Configuration File**: `config/ufo/mcp.yaml`

### Structure

```yaml
AgentName:              # e.g., "HostAgent", "AppAgent"
  SubType:              # "default" or app name (e.g., "WINWORD.EXE")
    data_collection:    # Data collection servers (read-only)
      - namespace: ...
        type: ...       # "local", "http", or "stdio"
    action:             # Action servers (state-changing)
      - namespace: ...
        type: ...
```

### Server Types

| Type | Description | Use Case |
|------|-------------|----------|
| `local` | In-process server | Fast, built-in tools |
| `http` | Remote HTTP server | Cross-machine, language-agnostic |
| `stdio` | Child process via stdin/stdout | Process isolation |

### Common Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | String | ✅ Yes | Unique server identifier |
| `type` | String | ✅ Yes | Server type: `local`, `http`, or `stdio` |
| `reset` | Boolean | ❌ No | Reset on context switch (default: `false`) |

### Local Server Example

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
        reset: false
```

### HTTP Server Example

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
```

### Stdio Server Example

```yaml
CustomAgent:
  default:
    action:
      - namespace: CustomProcessor
        type: stdio
        command: "python"
        start_args: ["-m", "custom_mcp_server"]
        env: {"API_KEY": "secret"}
        cwd: "/path/to/server"
```

## Built-in Agent Configurations

### HostAgent (System-Level)

- **Data Collection**: UICollector
- **Actions**: HostUIExecutor, CommandLineExecutor

### AppAgent (Application-Level)

**Default**: UICollector, AppUIExecutor, CommandLineExecutor

**App-Specific**:
- **WINWORD.EXE**: + WordCOMExecutor
- **EXCEL.EXE**: + ExcelCOMExecutor
- **POWERPNT.EXE**: + PowerPointCOMExecutor
- **explorer.exe**: + PDFReaderExecutor

### ConstellationAgent

- **Actions**: ConstellationEditor

### HardwareAgent

- **Data Collection**: HardwareCollector (HTTP)
- **Actions**: HardwareExecutor (HTTP)

### LinuxAgent

- **Actions**: BashExecutor (HTTP)

## Reset Behavior

!!!tip "When to Use `reset: true`"
    - **COM executors** (Word, Excel, PowerPoint) - Prevents state leakage between documents
    - **Stateful tools** - Requires clean state per task
    
    **Default: `false`** - Server persists across context switches

## Access in Code

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()
mcp_config = config.MCP

# Get agent-specific config
host_agent = mcp_config.get("HostAgent", {})
app_agent = mcp_config.get("AppAgent", {})

# Get sub-type config
word_config = app_agent.get("WINWORD.EXE", app_agent.get("default", {}))
```

## Complete Documentation

For detailed configuration guide including:
- Complete field reference for all server types
- Agent-specific configuration examples
- Best practices and anti-patterns
- Configuration validation
- Debugging and troubleshooting
- Migration guide

See **[MCP Configuration Guide](../../mcp/configuration.md)**

!!!tip "Creating Custom MCP Servers"
    Want to create your own MCP servers? See the **[Creating Custom MCP Servers Tutorial](../../tutorials/creating_mcp_servers.md)** for step-by-step instructions on building local, HTTP, and stdio servers.

## Related Documentation

- [MCP Overview](../../mcp/overview.md) - MCP architecture
- [Data Collection Servers](../../mcp/data_collection.md) - Read-only tools
- [Action Servers](../../mcp/action.md) - State-changing tools
- [Local Servers](../../mcp/local_servers.md) - Built-in servers
- [Remote Servers](../../mcp/remote_servers.md) - HTTP/Stdio deployment
- **[Creating Custom MCP Servers Tutorial](../../tutorials/creating_mcp_servers.md)** - Build your own servers
- [Configuration Overview](./overview.md) - General configuration system
- [System Configuration](./system_config.md) - MCP-related system settings

