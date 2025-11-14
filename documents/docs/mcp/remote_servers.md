# Remote MCP Servers

Remote MCP servers run as separate processes or on different machines, communicating with UFO² over HTTP or stdio. This enables **cross-platform automation**, process isolation, and distributed workflows.

**Cross-Platform Automation:** Remote servers enable **Windows UFO² agents to control Linux systems, mobile devices, and hardware** through HTTP MCP servers running on those platforms.

## Deployment Models

### HTTP Servers

HTTP MCP servers run as standalone HTTP services, accessible via REST-like endpoints.

**Advantages:**
- Cross-platform communication (Windows ↔ Linux, Windows ↔ Hardware)
- Language-agnostic (server can be in Python, Go, Rust, etc.)
- Network-accessible (local or remote deployment)
- Stateless design (each request is independent)

**Use Cases:**
- Linux command execution from Windows
- Hardware device control (Arduino, robot arms, test fixtures)
- Mobile device automation (Android, iOS via robot arm)
- Distributed multi-machine workflows

### Stdio Servers

Stdio MCP servers run as child processes, communicating via stdin/stdout.

**Advantages:**
- Process isolation (sandboxed execution)
- Clean resource management (process lifetime)
- Standard protocol (works with any language)

**Use Cases:**
- Custom Python/Node.js tools running in separate environments
- Third-party MCP servers
- Sandboxed execution for security


---

## Built-in Remote Servers

### HardwareExecutor

**Type**: Action (HTTP deployment)  
**Purpose**: Control hardware devices (Arduino HID, BB-8 test fixture, robot arm, mobile devices)  
**Deployment**: HTTP server on hardware controller machine  
**Agent**: HardwareAgent  
**Tools**: 30+ hardware control tools

**[→ See complete HardwareExecutor documentation](servers/hardware_executor.md)** for all hardware control tools, deployment instructions, and usage examples.

---

### BashExecutor

**Type**: Action (HTTP deployment)  
**Purpose**: Execute shell commands on Linux systems  
**Deployment**: HTTP server on Linux machine  
**Agent**: LinuxAgent  
**Tools**: 2 tools for command execution and system info

**[→ See complete BashExecutor documentation](servers/bash_executor.md)** for Linux command execution, security guidelines, and systemd setup.

---

### MobileExecutor

**Type**: Action + Data Collection (HTTP deployment, dual-server)  
**Purpose**: Android device automation via ADB  
**Deployment**: HTTP servers on machine with ADB access  
**Agent**: MobileAgent  
**Ports**: 8020 (data collection), 8021 (action)  
**Tools**: 13+ tools for Android automation

**Architecture**: Runs as **two HTTP servers** that share a singleton state manager for coordinated operations:
- **Mobile Data Collection Server** (port 8020): Screenshots, UI tree, device info, app list, controls
- **Mobile Action Server** (port 8021): Tap, swipe, type, launch apps, press keys, control clicks

**[→ See complete MobileExecutor documentation](servers/mobile_executor.md)** for all Android automation tools, dual-server architecture, deployment instructions, and usage examples.

---

## Configuration Reference

### HTTP Server Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | String | ✅ Yes | Unique server identifier |
| `type` | String | ✅ Yes | Must be `"http"` |
| `host` | String | ✅ Yes | Server hostname or IP |
| `port` | Integer | ✅ Yes | Server port number |
| `path` | String | ✅ Yes | HTTP endpoint path |
| `reset` | Boolean | ❌ No | Reset on context switch (default: `false`) |

### Stdio Server Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | String | ✅ Yes | Unique server identifier |
| `type` | String | ✅ Yes | Must be `"stdio"` |
| `command` | String | ✅ Yes | Executable command |
| `start_args` | List[String] | ❌ No | Command-line arguments |
| `env` | Dict | ❌ No | Environment variables |
| `cwd` | String | ❌ No | Working directory |
| `reset` | Boolean | ❌ No | Reset on context switch (default: `false`) |

---

## Example Configurations

### HTTP: Hardware Control

```yaml
HardwareAgent:
  default:
    action:
      - namespace: HardwareExecutor
        type: http
        host: "192.168.1.100"
        port: 8006
        path: "/mcp"
```

**Server Start:**
```bash
python -m ufo.client.mcp.http_servers.hardware_mcp_server --host 0.0.0.0 --port 8006
```

See the [HardwareExecutor documentation](servers/hardware_executor.md) for complete deployment instructions.

### HTTP: Linux Command Execution

```yaml
LinuxAgent:
  default:
    action:
      - namespace: BashExecutor
        type: http
        host: "192.168.1.50"
        port: 8010
        path: "/mcp"
```

**Server Start:**
```bash
python -m ufo.client.mcp.http_servers.linux_mcp_server --host 0.0.0.0 --port 8010
```

See the [BashExecutor documentation](servers/bash_executor.md) for systemd service setup.

### HTTP: Android Device Automation

```yaml
MobileAgent:
  default:
    data_collection:
      - namespace: MobileDataCollector
        type: http
        host: "192.168.1.60"  # Android automation server
        port: 8020
        path: "/mcp"
    action:
      - namespace: MobileExecutor
        type: http
        host: "192.168.1.60"
        port: 8021
        path: "/mcp"
```

**Server Start:**
```bash
# Start both servers (recommended - they share state)
python -m ufo.client.mcp.http_servers.mobile_mcp_server --server both --host 0.0.0.0 --data-port 8020 --action-port 8021
```

See the [MobileExecutor documentation](servers/mobile_executor.md) for complete deployment instructions and ADB setup.

### Stdio: Custom Python Server

```yaml
CustomAgent:
  default:
    action:
      - namespace: CustomProcessor
        type: stdio
        command: "python"
        start_args: ["-m", "custom_mcp_server"]
        env:
          API_KEY: "secret_key"
        cwd: "/path/to/server"
```

---

## Best Practices

**Recommended Practices:**

- ✅ **Use HTTP for cross-platform automation**
- ✅ **Use stdio for process isolation**
- ✅ **Validate remote server connectivity** before deployment
- ✅ **Set appropriate timeouts** for long-running commands
- ✅ **Use environment variables** for sensitive credentials

**Anti-Patterns to Avoid:**

- ❌ **Don't expose HTTP servers to public internet** without authentication
- ❌ **Don't hardcode credentials** in configuration files
- ❌ **Don't forget to start remote servers** before client connection

---

## See Also

- [MCP Overview](./overview.md) - MCP architecture and deployment models
- [Local Servers](./local_servers.md) - In-process servers
- [MCP Configuration](./configuration.md) - Complete configuration reference
- [Action Servers](./action.md) - Action execution overview
- **[Creating Custom MCP Servers Tutorial](../tutorials/creating_mcp_servers.md)** - Step-by-step guide for HTTP/Stdio servers
- [HardwareExecutor](servers/hardware_executor.md) - Complete hardware control reference
- [BashExecutor](servers/bash_executor.md) - Complete Linux command reference
