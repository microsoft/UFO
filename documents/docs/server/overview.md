# Agent Server Overview

The **Agent Server** is the central orchestration engine of UFO²'s distributed agent system. It manages device agent lifecycles, coordinates multi-device workflows, and provides robust communication infrastructure using the Agent Interaction Protocol (AIP).

!!!tip "Quick Start"
    New to the Agent Server? Start with the [Quick Start Guide](./quick_start.md) to get up and running in minutes.

## What is the Agent Server?

The Agent Server is a FastAPI-based WebSocket server that:

- **Manages Connections** - Tracks device and constellation client connections
- **Orchestrates Tasks** - Coordinates task execution across distributed devices  
- **Maintains State** - Manages session lifecycles and execution contexts
- **Provides APIs** - Offers both WebSocket (AIP) and HTTP (REST) interfaces
- **Ensures Resilience** - Handles disconnections, timeouts, and failures gracefully

## Architecture

The server implements a three-tier architecture:

```
┌──────────────────────────────────────────────────────┐
│              FastAPI Application                     │
│  • HTTP REST API (/api/*)                           │
│  • WebSocket endpoint (/ws)                         │
│  • Health checks and monitoring                     │
└───────────┬──────────────────────────────────────────┘
            │
    ┌───────┴────────┬─────────────────┐
    │                │                 │
┌───▼────────┐  ┌───▼─────────┐  ┌───▼──────────┐
│ WebSocket  │  │  Session    │  │  WebSocket   │
│ Manager    │  │  Manager    │  │  Handler     │
│            │  │             │  │              │
│ • Client   │  │ • Lifecycle │  │ • AIP        │
│   registry │  │   mgmt      │  │   protocol   │
│ • Device   │  │ • Background│  │ • Message    │
│   info     │  │   execution │  │   routing    │
│ • Session  │  │ • Results   │  │ • Task       │
│   tracking │  │   storage   │  │   dispatch   │
└────────────┘  └─────────────┘  └──────────────┘
```

### Core Components

| Component | Responsibility | Details |
|-----------|---------------|---------|
| **FastAPI App** | Web service layer | HTTP endpoints, WebSocket endpoint, argument parsing |
| **WebSocket Manager** | Connection registry | Client tracking, session mapping, device info cache |
| **Session Manager** | Execution lifecycle | Session creation, background async execution, results |
| **WebSocket Handler** | Protocol implementation | AIP message handling, registration, heartbeat, dispatch |

For detailed component documentation:

- [Session Manager](./session_manager.md) - Session lifecycle and execution
- [WebSocket Manager](./websocket_manager.md) - Connection and registry management
- [WebSocket Handler](./websocket_handler.md) - AIP protocol handling
- [HTTP API](./api.md) - REST endpoint reference

## Key Capabilities

### 1. Multi-Client Coordination

The server supports two types of clients:

**Device Clients**
- Execute tasks locally on Windows/Linux machines
- Report device information and status
- Respond to commands in real-time

**Constellation Clients**  
- Orchestrate multi-device workflows
- Dispatch tasks to target devices
- Coordinate complex cross-device operations

See [Quick Start - Client Registration](./quick_start.md#connecting-a-device-client) for registration details.

### 2. Session Lifecycle Management

Each task creates a session with platform-specific implementation:

```
Create Session → Background Execution → Results → Cleanup
      │                  │                 │         │
      │                  │                 │         │
   Windows/          Async Task        Callback   Release
   Linux Agent        Execution        Delivery  Resources
```

The session manager handles:
- Platform-specific session creation (Windows/Linux)
- Background async execution without blocking
- Callback-based result delivery
- Graceful cancellation on disconnection

### 3. Resilient Communication

Built on [AIP (Agent Interaction Protocol)](../aip/overview.md):

- **Structured Messages** - Strongly-typed Pydantic models
- **Connection Health** - Heartbeat monitoring and timeout detection
- **Error Recovery** - Automatic reconnection with backoff strategies
- **State Tracking** - Session-to-client mapping for cleanup

### 4. Dual API Interface

**WebSocket API (AIP-based)**
- Real-time bidirectional communication
- Task dispatch and result streaming
- Heartbeat and connection monitoring
- Device information exchange

**HTTP REST API**
- Task dispatch from external systems
- Client status monitoring (`/api/clients`)
- Task result retrieval (`/api/task_result/{id}`)
- Health checks (`/api/health`)

See [HTTP API Reference](./api.md) for endpoint details.

## Workflow Example

### Task Dispatch Flow

```
External System          Server              Device Client
      │                    │                       │
      │  POST /api/dispatch│                       │
      ├───────────────────>│                       │
      │                    │                       │
      │                    │ Create Session        │
      │                    │ (SessionManager)      │
      │                    ├─────────┐             │
      │                    │         │             │
      │                    │<────────┘             │
      │                    │                       │
      │  200 {session_id}  │                       │
      │<───────────────────┤                       │
      │                    │                       │
      │                    │ TASK message (AIP)    │
      │                    ├──────────────────────>│
      │                    │                       │
      │                    │ ACK                   │
      │                    │<──────────────────────┤
      │                    │                       │
      │                    │                       │ Execute
      │                    │                       │ Task
      │                    │                       ├────┐
      │                    │                       │    │
      │                    │                       │<───┘
      │                    │                       │
      │                    │ COMMAND_RESULTS       │
      │                    │<──────────────────────┤
      │                    │                       │
      │                    │ Callback: Send RESULT │
      │                    ├──────────────────────>│
      │                    │                       │
      │ GET /task_result   │                       │
      ├───────────────────>│                       │
      │                    │                       │
      │  200 {result}      │                       │
      │<───────────────────┤                       │
```

## Platform Support

The server is platform-agnostic and supports:

- **Windows** - Full UI automation, COM API integration
- **Linux** - Bash automation, GUI tools
- **macOS** - (In development)

Device clients identify their platform during registration, and the server creates appropriate session implementations.

## Configuration

The server uses minimal configuration:

**Command-Line Arguments**

```bash
python -m ufo.server.app [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--port` | 8000 | Server port |
| `--local` | False | Restrict to localhost only |

**UFO Configuration**

The server inherits UFO configuration from `config_dev.yaml`:

- Agent strategies and prompts
- LLM model settings
- Automator configurations
- Logging settings

See [Configuration Guide](../configurations/overview.md) for details.

## Monitoring

Monitor server health and performance:

```bash
# Health check
curl http://localhost:8000/api/health

# Connected clients
curl http://localhost:8000/api/clients
```

See [Monitoring Guide](./monitoring.md) for comprehensive monitoring strategies.

## Error Handling

The server handles common failure scenarios:

**Device Disconnection**
- Cancel all running sessions on that device
- Notify constellation clients of failures
- Clean up session mappings

**Constellation Disconnection**
- Continue executing tasks on devices
- Skip result callbacks to disconnected constellation
- Clean up constellation session mappings

**Task Failures**
- Capture error details in session results
- Send error messages via AIP
- Log failures for debugging

## Best Practices

**Development**
- Use `--local` flag to restrict connections
- Monitor logs for connection events
- Test with single device before scaling

**Production**
- Run behind reverse proxy (nginx/Apache)
- Enable SSL/TLS for WebSocket connections
- Implement authentication middleware
- Set up health check monitoring
- Use process manager (systemd/PM2)

**Scaling**
- Monitor `/api/health` for load metrics
- Distribute devices across multiple servers
- Use load balancer for HTTP endpoints
- Consider horizontal scaling for high loads

## Documentation Map

**Getting Started**
- [Quick Start](./quick_start.md) - Get server running in minutes
- [Quick Start - Client Registration](./quick_start.md#connecting-a-device-client) - How clients connect

**Components**
- [Session Manager](./session_manager.md) - Task execution lifecycle
- [WebSocket Manager](./websocket_manager.md) - Connection registry
- [WebSocket Handler](./websocket_handler.md) - AIP protocol handling
- [HTTP API](./api.md) - REST endpoint reference

**Operations**
- [Monitoring](./monitoring.md) - Health checks and metrics

**Related**
- [AIP Protocol](../aip/overview.md) - Communication protocol
- [Configuration](../configurations/overview.md) - UFO configuration
- [Agents](../agents/overview.md) - Agent architecture

## Next Steps

1. **Run the server** - Follow the [Quick Start Guide](./quick_start.md)
2. **Connect clients** - Learn about [Client Registration](./quick_start.md#connecting-a-device-client)
3. **Dispatch tasks** - Use the [HTTP API](./api.md)
4. **Monitor health** - Set up [Monitoring](./monitoring.md)
5. **Understand AIP** - Read the [AIP Protocol Guide](../aip/overview.md)
