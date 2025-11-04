# Agent Client Overview

The **Agent Client** runs on target devices and serves as the execution layer of UFO²'s distributed agent system. It manages MCP (Model Context Protocol) servers, executes commands deterministically, and communicates with the Agent Server through the Agent Interaction Protocol (AIP).

!!!tip "Quick Start"
    Ready to run a client? Jump to the [Quick Start Guide](./quick_start.md) to connect your device in minutes. Make sure the [Agent Server](../server/quick_start.md) is running first.

## What is the Agent Client?

The Agent Client is a stateless execution agent that:

- **Executes Commands** - Translates server directives into concrete actions
- **Manages MCP Servers** - Orchestrates local and remote tool interfaces
- **Reports Device Info** - Provides hardware and software profile to the server
- **Communicates via AIP** - Maintains persistent WebSocket connection with server
- **Remains Stateless** - Executes directives without high-level reasoning

!!!info "Stateless Design"
    The client focuses purely on execution. All reasoning and decision-making happens on the server, allowing independent updates to server logic and client tools.

## Architecture

The client implements a layered architecture separating communication, execution, and tool management:

```
┌────────────────────────────────────────────────────────┐
│              WebSocket Client (AIP)                    │
│  • Registration & Connection Management                │
│  • Heartbeat Monitoring                                │
│  • Message Handling (Task/Command/Result)              │
└──────────────┬─────────────────────────────────────────┘
               │
       ┌───────┴────────┬────────────────────┐
       │                │                    │
┌──────▼───────┐  ┌────▼────────┐  ┌────────▼─────────┐
│  UFO Client  │  │  Computer   │  │  Device Info     │
│              │  │  Manager    │  │  Provider        │
│ • Session    │  │             │  │                  │
│   tracking   │  │ • Command   │  │ • System info    │
│ • Command    │  │   routing   │  │   collection     │
│   execution  │  │ • Computer  │  │ • Hardware       │
│ • Result     │  │   instances │  │   detection      │
│   aggregation│  │ • Namespace │  │ • Platform       │
│              │  │   mgmt      │  │   capabilities   │
└──────┬───────┘  └─────┬───────┘  └──────────────────┘
       │                │
       │         ┌──────▼────────┐
       │         │   Computer    │
       │         │   Instance    │
       │         ├───────────────┤
       │         │ • MCP Server  │
       │         │   registration│
       │         │ • Tool        │
       │         │   registry    │
       │         │ • Execution   │
       │         │   isolation   │
       │         └───┬───────────┘
       │             │
       └─────────────┴──────────────────┐
                     │                  │
           ┌─────────▼────────┐  ┌──────▼──────────┐
           │ MCP Server       │  │ MCP Server      │
           │ Manager          │  │ Instances       │
           │                  │  │                 │
           │ • Server         │  │ • Local MCP     │
           │   lifecycle      │  │   servers       │
           │ • Configuration  │  │ • Remote MCP    │
           │   loading        │  │   servers       │
           │ • Connection     │  │ • Tool APIs     │
           │   pooling        │  │                 │
           └──────────────────┘  └─────────────────┘
```

### Core Components

| Component | Responsibility | Details |
|-----------|---------------|---------|
| **WebSocket Client** | AIP communication | Connection management, registration, heartbeat, message routing |
| **UFO Client** | Execution orchestration | Session tracking, command execution, result aggregation |
| **Computer Manager** | Multi-computer abstraction | Manages multiple computer instances with different namespaces |
| **Computer** | Tool management | MCP server registration, tool registry, command routing |
| **MCP Server Manager** | MCP lifecycle | Server creation, configuration, connection pooling |
| **Device Info Provider** | System profiling | Hardware detection, capability reporting, platform identification |

For detailed component documentation:

- [WebSocket Client](./websocket_client.md) - AIP protocol implementation
- [UFO Client](./ufo_client.md) - Execution orchestration
- [Computer Manager](./computer_manager.md) - Multi-computer management
- [Device Info Provider](./device_info.md) - System profiling
- [MCP Integration](./mcp_integration.md) - MCP server management (brief overview)

## Key Capabilities

### 1. Deterministic Command Execution

The client executes commands without interpretation or reasoning:

```
Server Command → Command Router → Tool Selection → Execution → Result
      │               │               │              │           │
      │               │               │              │           │
  Structured      Namespace       MCP Tool        Isolated   Structured
  AIP Message     Resolution       Lookup         Execution   Result
```

**Execution Flow:**
1. Receive structured command from server
2. Route to appropriate computer instance
3. Look up tool in MCP registry
4. Execute in isolated thread pool
5. Aggregate results and return via AIP

!!!success "Reliability"
    All tool calls are executed in isolated thread pools with timeouts, ensuring one failed tool doesn't crash the entire client.

### 2. MCP Server Management

The client manages a collection of MCP servers for diverse tool access:

**Data Collection Servers**
- System information gathering
- Application state querying
- Screenshot capture
- UI element detection

**Action Servers**
- GUI automation (keyboard, mouse)
- Application control
- File system operations
- Command execution

**Server Types:**
- **Local MCP Servers** - Run in same process via FastMCP
- **Remote MCP Servers** - Connect via HTTP to external services

See [MCP Integration](./mcp_integration.md) for MCP server details (high-level overview only).

### 3. Device Profiling

The client automatically collects and reports device information:

```python
{
    "device_id": "device_windows_001",
    "platform": "windows",
    "os_version": "10.0.22631",
    "cpu_count": 8,
    "memory_total_gb": 16.0,
    "hostname": "DESKTOP-ABC123",
    "ip_address": "192.168.1.100",
    "supported_features": ["gui", "cli", "browser", "office", "windows_apps"],
    "platform_type": "computer"
}
```

This information is sent to the server during registration and integrated into the server's AgentProfile for intelligent task assignment.

### 4. Resilient Communication

Built on [AIP (Agent Interaction Protocol)](../aip/overview.md):

**Connection Management:**
- Automatic registration on connect
- Exponential backoff retry on failure
- Heartbeat monitoring (configurable interval)
- Graceful reconnection

**Message Handling:**
- Strongly-typed Pydantic messages
- Command acknowledgment
- Result streaming
- Error reporting

See [AIP Protocol Guide](../aip/overview.md) for protocol details.

## Workflow Examples

### Client Initialization & Registration

```
Client Start → WebSocket Connect → Registration → Heartbeat Loop
      │              │                   │              │
      │              │                   │              │
  Load Config    AIP Transport      Device Info    Keep-Alive
  Initialize     Establishment      Collection     Monitoring
  MCP Servers
```

**Step-by-Step:**
1. Parse command-line arguments
2. Load UFO configuration
3. Initialize MCP server manager
4. Create computer manager with MCP servers
5. Connect to WebSocket server
6. Collect and send device info
7. Start heartbeat loop
8. Listen for commands

See [Server Quick Start - Client Registration](../server/quick_start.md#connecting-a-device-client) for server-side registration details.

### Command Execution Flow

```
Server                    Client                    MCP Server
  │                         │                            │
  │  COMMAND (AIP)          │                            │
  ├────────────────────────>│                            │
  │                         │                            │
  │                         │ Route to Computer          │
  │                         ├─────────┐                  │
  │                         │         │                  │
  │                         │<────────┘                  │
  │                         │                            │
  │                         │ Lookup Tool                │
  │                         ├─────────┐                  │
  │                         │         │                  │
  │                         │<────────┘                  │
  │                         │                            │
  │                         │  Call Tool                 │
  │                         ├───────────────────────────>│
  │                         │                            │
  │                         │                            │ Execute
  │                         │                            ├────┐
  │                         │                            │    │
  │                         │                            │<───┘
  │                         │                            │
  │                         │  Tool Result               │
  │                         │<───────────────────────────┤
  │                         │                            │
  │                         │ Aggregate Results          │
  │                         ├─────────┐                  │
  │                         │         │                  │
  │                         │<────────┘                  │
  │                         │                            │
  │  COMMAND_RESULTS (AIP)  │                            │
  │<────────────────────────┤                            │
```

## Platform Support

The client supports multiple platforms with platform-specific tool implementations:

| Platform | Status | Features |
|----------|--------|----------|
| **Windows** | ✅ Full Support | UI automation, COM API, Office integration, Windows apps |
| **Linux** | ✅ Full Support | Bash automation, GUI tools, Linux apps |
| **macOS** | 🚧 In Development | macOS apps, Automator integration |
| **Mobile** | 🔮 Planned | Touch interface, mobile apps |

Platform is auto-detected but can be overridden via `--platform` flag.

## Configuration

The client is configured through command-line arguments and UFO configuration files.

### Command-Line Arguments

```bash
python -m ufo.client.client [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--client-id` | `client_001` | Unique client identifier |
| `--ws-server` | `ws://localhost:5000/ws` | WebSocket server URL |
| `--ws` | False | Enable WebSocket mode (required flag) |
| `--max-retries` | 5 | Connection retry limit |
| `--platform` | Auto-detect | Platform override (windows/linux) |
| `--log-level` | INFO | Logging verbosity |

### UFO Configuration

The client inherits configuration from `config_dev.yaml`:

- MCP server definitions (data collection and action servers)
- Tool configurations and parameters
- Logging settings
- Platform-specific settings

See [Configuration Guide](../configurations/overview.md) for details.

## Error Handling

The client handles various failure scenarios gracefully:

**Connection Failures:**
- Exponential backoff retry (2^n seconds)
- Maximum retry limit (configurable)
- Automatic reconnection on disconnect

**Tool Execution Failures:**
- Timeout protection (default: 100 minutes per tool)
- Isolated execution (thread pool)
- Structured error reporting via AIP

**Server Disconnection:**
- Graceful shutdown of ongoing tasks
- Connection state monitoring
- Automatic reconnection attempts

## Best Practices

**Development:**
- Use unique `--client-id` for each device
- Start with `INFO` log level, use `DEBUG` for troubleshooting
- Test MCP server connectivity before production

**Production:**
- Use descriptive client IDs (e.g., `device_windows_prod_01`)
- Configure automatic restart on crash
- Monitor connection health via logs
- Use process manager (systemd/PM2)

**Security:**
- Use WSS (WebSocket Secure) for production
- Restrict MCP server access to trusted tools
- Validate server certificates
- Run with minimum required privileges

## Documentation Map

**Getting Started:**
- [Quick Start](./quick_start.md) - Connect your device quickly
- [Server Quick Start - Client Registration](../server/quick_start.md#connecting-a-device-client) - How registration works

**Components:**
- [WebSocket Client](./websocket_client.md) - AIP communication layer
- [UFO Client](./ufo_client.md) - Execution orchestration
- [Computer Manager](./computer_manager.md) - Multi-computer abstraction
- [Device Info Provider](./device_info.md) - System profiling
- [MCP Integration](./mcp_integration.md) - MCP server overview

**Related:**
- [Agent Server](../server/overview.md) - Server architecture
- [AIP Protocol](../aip/overview.md) - Communication protocol
- [Configuration](../configurations/overview.md) - UFO configuration

## Client vs. Server

Understanding the separation of concerns:

| Aspect | Client | Server |
|--------|--------|--------|
| **Role** | Execution | Orchestration |
| **State** | Stateless (executes directives) | Stateful (maintains sessions) |
| **Reasoning** | None (deterministic execution) | Full (high-level decision-making) |
| **Tools** | MCP servers (local/remote) | Agent strategies, prompts, LLMs |
| **Communication** | Device-to-server (AIP) | Multi-client coordination |
| **Updates** | Tool implementation changes | Strategy and logic updates |

!!!info "Decoupled Architecture"
    This separation allows updating server logic or client tools independently without disrupting workflows.

## Next Steps

1. **Run the client** - Follow the [Quick Start Guide](./quick_start.md)
2. **Understand registration** - Read [Server Quick Start - Client Registration](../server/quick_start.md#connecting-a-device-client)
3. **Learn about tools** - Explore [MCP Integration](./mcp_integration.md)
4. **Configure MCP servers** - See [Configuration Guide](../configurations/overview.md)
5. **Master the protocol** - Study [AIP Protocol](../aip/overview.md)
