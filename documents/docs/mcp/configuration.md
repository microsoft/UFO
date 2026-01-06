# MCP Configuration Guide

## Overview

MCP configuration in UFO² uses a **hierarchical YAML structure** that maps agents to their MCP servers. The configuration file is located at:

```
config/ufo/mcp.yaml
```

For complete field documentation, see [MCP Reference](../configuration/system/mcp_reference.md).

## Configuration Structure

```yaml
AgentName:                    # Name of the agent
  SubType:                    # Sub-type (e.g., "default", "WINWORD.EXE")
    data_collection:          # Data collection servers
      - namespace: ...        # Server namespace
        type: ...             # Server type (local/http/stdio)
        ...                   # Additional server config
    action:                   # Action servers
      - namespace: ...
        type: ...
        ...
```

### Hierarchy Levels

1. **Agent Name** - Top-level agent identifier (e.g., `HostAgent`, `AppAgent`)
2. **Sub-Type** - Context-specific configuration (e.g., `default`, `WINWORD.EXE`)
3. **Tool Type** - `data_collection` or `action`
4. **Server List** - Array of MCP server configurations

```
AgentName
  └─ SubType
      ├─ data_collection
      │   ├─ Server 1
      │   ├─ Server 2
      │   └─ ...
      └─ action
          ├─ Server 1
          ├─ Server 2
          └─ ...
```

**Default Sub-Type:** Always define a `default` sub-type as a fallback configuration. If a specific sub-type is not found, the agent will use `default`.

## Server Configuration Fields

### Common Fields

All MCP servers share these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | `string` | ✅ Yes | Unique identifier for the server |
| `type` | `string` | ✅ Yes | Server type: `local`, `http`, or `stdio` |
| `reset` | `boolean` | ❌ No | Whether to reset server state (default: `false`) |
| `start_args` | `array` | ❌ No | Arguments passed to server initialization |

### Local Server Fields

For `type: local`:

```yaml
- namespace: UICollector
  type: local
  start_args: []
  reset: false
```

| Field | Description |
|-------|-------------|
| `start_args` | Arguments passed to server factory function |

Local servers are retrieved from the `MCPRegistry` and run in-process.

### HTTP Server Fields

For `type: http`:

```yaml
- namespace: HardwareCollector
  type: http
  host: "localhost"
  port: 8006
  path: "/mcp"
  reset: false
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `host` | `string` | ✅ Yes | Server hostname or IP |
| `port` | `integer` | ✅ Yes | Server port number |
| `path` | `string` | ✅ Yes | URL path to MCP endpoint |

HTTP servers run on remote machines and are accessed via REST API.

### Stdio Server Fields

For `type: stdio`:

```yaml
- namespace: CustomProcessor
  type: stdio
  command: "python"
  start_args: ["-m", "custom_mcp_server"]
  env: {"API_KEY": "secret"}
  cwd: "/path/to/server"
  reset: false
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | `string` | ✅ Yes | Executable command |
| `start_args` | `array` | ❌ No | Command-line arguments |
| `env` | `object` | ❌ No | Environment variables |
| `cwd` | `string` | ❌ No | Working directory |

Stdio servers run as child processes and communicate via stdin/stdout.

## Agent Configurations

### HostAgent

System-level agent for OS-wide automation:

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

**Tools Available**:
- **Data Collection**: UI detection, screenshots
- **Actions**: System-wide clicks, window management, CLI execution

### AppAgent

Application-specific agent:

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

#### Word-Specific Configuration

```yaml
AppAgent:
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
        reset: true  # Reset COM state when switching documents
```

**Tools Available**:
- **Data Collection**: Same as default
- **Actions**: App UI automation + Word COM API (insert_table, select_text, etc.)

**Reset Flag:** Set `reset: true` for stateful tools (like COM executors) to prevent state leakage between contexts (e.g., different documents).

#### Excel-Specific Configuration

```yaml
AppAgent:
  EXCEL.EXE:
    data_collection:
      - namespace: UICollector
        type: local
        reset: false
    action:
      - namespace: AppUIExecutor
        type: local
        reset: false
      - namespace: ExcelCOMExecutor
        type: local
        reset: true
```

#### PowerPoint-Specific Configuration

```yaml
AppAgent:
  POWERPNT.EXE:
    data_collection:
      - namespace: UICollector
        type: local
        reset: false
    action:
      - namespace: AppUIExecutor
        type: local
        reset: false
      - namespace: PowerPointCOMExecutor
        type: local
        reset: true
```

#### File Explorer Configuration

```yaml
AppAgent:
  explorer.exe:
    data_collection:
      - namespace: UICollector
        type: local
        reset: false
    action:
      - namespace: AppUIExecutor
        type: local
        reset: false
      - namespace: PDFReaderExecutor
        type: local
        reset: true
```

### ConstellationAgent

Multi-device coordination agent:

```yaml
ConstellationAgent:
  default:
    action:
      - namespace: ConstellationEditor
        type: local
        start_args: []
        reset: false
```

**Tools Available**:
- **Actions**: Create tasks, assign devices, check task status

### HardwareAgent

Remote hardware monitoring agent:

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

**Tools Available**:
- **Data Collection**: CPU info, memory info, disk info
- **Actions**: Hardware control commands

**Remote Deployment:** For remote servers, ensure the HTTP MCP server is running on the target machine. See [Remote Servers](remote_servers.md) for deployment guide.

### LinuxAgent

Linux system agent:

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

**Tools Available**:
- **Actions**: Bash command execution

## Configuration Examples

### Example 1: Local-Only Agent

```yaml
SimpleAgent:
  default:
    data_collection:
      - namespace: UICollector
        type: local
        reset: false
    action:
      - namespace: SimpleExecutor
        type: local
        reset: false
```

### Example 2: Hybrid Agent (Local + Remote)

```yaml
HybridAgent:
  default:
    data_collection:
      # Local UI detection
      - namespace: UICollector
        type: local
        reset: false
      
      # Remote hardware monitoring
      - namespace: HardwareCollector
        type: http
        host: "192.168.1.100"
        port: 8006
        path: "/mcp"
        reset: false
    
    action:
      # Local UI automation
      - namespace: UIExecutor
        type: local
        reset: false
      
      # Remote command execution
      - namespace: RemoteExecutor
        type: http
        host: "192.168.1.100"
        port: 8007
        path: "/mcp"
        reset: false
```

### Example 3: Multi-Context Agent

```yaml
MultiContextAgent:
  # Default configuration
  default:
    data_collection:
      - namespace: BasicCollector
        type: local
    action:
      - namespace: BasicExecutor
        type: local
  
  # Specialized for Chrome
  chrome.exe:
    data_collection:
      - namespace: BasicCollector
        type: local
      - namespace: WebCollector
        type: local
    action:
      - namespace: BasicExecutor
        type: local
      - namespace: BrowserExecutor
        type: local
        reset: true
  
  # Specialized for VS Code
  Code.exe:
    data_collection:
      - namespace: BasicCollector
        type: local
      - namespace: IDECollector
        type: local
    action:
      - namespace: BasicExecutor
        type: local
      - namespace: CodeExecutor
        type: local
        reset: true
```

## Best Practices

### 1. Use Descriptive Namespaces

```yaml
# ✅ Good: Clear and descriptive
namespace: WindowsUICollector
namespace: ExcelCOMExecutor
namespace: LinuxBashExecutor

# ❌ Bad: Generic and unclear
namespace: Collector1
namespace: Server
namespace: Tools
```

### 2. Group Related Servers

```yaml
# ✅ Good: Logical grouping
HostAgent:
  default:
    data_collection:
      - namespace: UICollector      # All UI-related
      - namespace: ScreenshotTaker
    action:
      - namespace: UIExecutor       # All UI actions
      - namespace: WindowManager

# ❌ Bad: Mixed purposes
HostAgent:
  default:
    data_collection:
      - namespace: UICollector
      - namespace: HardwareMonitor  # Different purpose
```

### 3. Reset Stateful Servers

```yaml
# ✅ Good: Reset COM servers
WordCOMExecutor:
  type: local
  reset: true  # Prevents state leakage

# ❌ Bad: Not resetting can cause issues
WordCOMExecutor:
  type: local
  reset: false  # May retain state from previous document
```

### 4. Validate Remote Server Availability

```yaml
# When using remote servers, ensure they're accessible
HardwareCollector:
  type: http
  host: "192.168.1.100"  # ✅ Verify this host is reachable
  port: 8006             # ✅ Verify port is open
  path: "/mcp"           # ✅ Verify endpoint exists
```

### 5. Use Environment Variables for Secrets

```yaml
# ✅ Good: Use environment variables
- namespace: SecureAPI
  type: http
  host: "${API_HOST}"
  port: "${API_PORT}"
  auth:
    token: "${API_TOKEN}"

# ❌ Bad: Hardcoded secrets
- namespace: SecureAPI
  type: http
  host: "api.example.com"
  auth:
    token: "secret123"  # Don't commit this!
```

## Loading Configuration

### From File

```python
import yaml
from pathlib import Path

# Load MCP configuration
config_path = Path("config/ufo/mcp.yaml")
with open(config_path) as f:
    mcp_config = yaml.safe_load(f)

# Access agent configuration
host_agent_config = mcp_config["HostAgent"]["default"]
```

### Programmatically

```python
from ufo.config import get_config

# Get full configuration
configs = get_config()

# Access MCP section
mcp_config = configs.get("mcp", {})

# Get specific agent
host_agent = mcp_config.get("HostAgent", {}).get("default", {})
```

## Validation

### Schema Validation

UFO² validates MCP configuration on load:

```python
from ufo.config.config_schemas import MCPConfigSchema

# Validate configuration
try:
    MCPConfigSchema.validate(mcp_config)
    print("✅ Configuration is valid")
except ValidationError as e:
    print(f"❌ Configuration error: {e}")
```

### Common Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing required field: namespace` | Server missing namespace | Add `namespace` field |
| `Invalid server type: unknown` | Unsupported type | Use `local`, `http`, or `stdio` |
| `Missing host for http server` | HTTP server without host | Add `host` and `port` |
| `Duplicate namespace` | Same namespace used twice | Use unique namespaces |

## Debugging Configuration

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ufo.client.mcp")

# Will show server creation and registration
# DEBUG: Creating MCP server 'UICollector' of type local
# DEBUG: Registered MCP server 'UICollector' with 15 tools
```

### Check Loaded Servers

```python
from ufo.client.mcp.mcp_server_manager import MCPServerManager

# List all registered servers
servers = MCPServerManager._servers_mapping
for namespace, server in servers.items():
    print(f"Server: {namespace}, Type: {type(server).__name__}")
```

### Test Server Connectivity

```python
async def test_server(config):
    """Test if MCP server is accessible."""
    try:
        server = MCPServerManager.create_mcp_server(config)
        print(f"✅ Server '{config['namespace']}' is accessible")
        
        # List tools
        if hasattr(server, 'server'):
            from fastmcp.client import Client
            async with Client(server.server) as client:
                tools = await client.list_tools()
                print(f"   Tools: {[tool.name for tool in tools]}")
    except Exception as e:
        print(f"❌ Server '{config['namespace']}' failed: {e}")
```

## Migration Guide

### From Old Configuration Format

If you're migrating from an older UFO configuration:

**Old Format** (config.yaml):
```yaml
MCP_SERVERS:
  - name: ui_collector
    module: ufo.mcp.ui_server
```

**New Format** (mcp.yaml):
```yaml
HostAgent:
  default:
    data_collection:
      - namespace: UICollector
        type: local
```

For detailed migration instructions, see [Configuration Migration Guide](../configuration/system/migration.md).

## Related Documentation

- [MCP Overview](overview.md) - High-level MCP architecture
- [Data Collection Servers](data_collection.md) - Data collection configuration
- [Action Servers](action.md) - Action server configuration
- [Local Servers](local_servers.md) - Built-in local MCP servers
- [Remote Servers](remote_servers.md) - HTTP and Stdio deployment
- [Creating Custom MCP Servers Tutorial](../tutorials/creating_mcp_servers.md) - Build your own servers
- [MCP Reference](../configuration/system/mcp_reference.md) - Complete field reference
- [Configuration Guide](../configuration/system/overview.md) - General configuration guide
- [HostAgent Overview](../ufo2/host_agent/overview.md) - HostAgent configuration examples
- [AppAgent Overview](../ufo2/app_agent/overview.md) - AppAgent configuration examples

**Configuration Philosophy:**

MCP configuration follows the **convention over configuration** principle:

- **Sensible defaults** - Minimal configuration required
- **Explicit when needed** - Full control when customization is necessary
- **Type-safe** - Validated on load to catch errors early
- **Hierarchical** - Inherit from defaults, override as needed
