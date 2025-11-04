# Agent Interaction Protocol (AIP) - Overview

The **Agent Interaction Protocol (AIP)** is the communication backbone of UFO², enabling seamless coordination between distributed agents across devices. AIP provides a lightweight, persistent, and extensible messaging layer optimized for multi-agent orchestration in dynamic, heterogeneous environments.

## Why AIP?

Traditional HTTP-based coordination protocols (e.g., A2A, ACP) assume short-lived, stateless interactions, making them unsuitable for persistent, bidirectional control over evolving workflows. UFO²'s orchestration model demands a communication layer capable of:

- **Tolerating continuous DAG evolution**: Task graphs are dynamically modified during execution
- **Supporting dynamic agent participation**: Agents join, leave, and reconnect unpredictably
- **Enabling fine-grained event propagation**: Real-time updates on task status, command results, and system state

AIP addresses these requirements by adopting **WebSocket** as its transport layer, providing long-lived, low-latency communication channels that support continuous event streaming, session-aware task management, and seamless recovery from transient disconnections.

## Design Philosophy

AIP functions as the **nervous system** of UFO², unifying registration, task dispatch, command execution, and result reporting into a single protocol that is both human-readable and machine-verifiable.

### Core Principles

**Minimalism with Extensibility**

AIP provides a stable protocol core while allowing custom extensions through capability descriptors and dynamic message handlers.

**Transport Agnostic**

While WebSocket is the primary transport, AIP's layered architecture supports future extensions (HTTP/3, gRPC, etc.).

**Session-Aware Communication**

Long-lived sessions span multiple task executions, maintaining context and reducing overhead.

**Resilient by Design**

Built-in reconnection strategies, heartbeat monitoring, and timeout management ensure reliability.

**Developer Friendly**

Strongly-typed messages using Pydantic, clear error propagation, and comprehensive logging.

## Three-Layer Architecture

AIP's logical architecture consists of three interconnected layers that work together to enable distributed agent orchestration:

```
┌─────────────────────────────────────────────────────────┐
│           ConstellationClient (Orchestrator)            │
│  - Global agent registry (AgentProfile management)      │
│  - Task assignment and DAG coordination                 │
│  - Multi-device scheduling                              │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ WebSocket (AIP Protocol)
                 │
┌────────────────▼────────────────────────────────────────┐
│         Device Agent Service (Server-Side)              │
│  - WebSocket connection management                      │
│  - Task dispatch to device clients                      │
│  - Command execution coordination                       │
│  - Result aggregation and reporting                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ WebSocket (AIP Protocol)
                 │
┌────────────────▼────────────────────────────────────────┐
│         Device Agent Client (Client-Side)               │
│  - Local task execution                                 │
│  - MCP tool/action execution                            │
│  - System telemetry reporting                           │
│  - Result streaming                                     │
└─────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**ConstellationClient (Orchestrator)**

The ConstellationClient maintains a global registry of active agents and coordinates task distribution across the constellation. It merges information from multiple sources to create comprehensive AgentProfiles for intelligent scheduling.

**Device Agent Service (Server-Side)**

Each device agent service exposes a WebSocket endpoint implementing the AIP protocol. It manages connections to one or more device clients, dispatches tasks, and aggregates execution results.

**Device Agent Client (Client-Side)**

Device clients execute tasks locally, invoke MCP tools/actions, collect system telemetry, and stream results back to the service layer.

## Core Capabilities

AIP provides three fundamental capabilities that power UFO²'s distributed orchestration:

### 1. Agent Registration and Profiling

Every agent in the constellation is represented by an **AgentProfile** that consolidates information from three sources:

**User-Specified Registration (ConstellationClient)**

Administrators provide endpoint identities and user preferences through configuration files.

**Service-Level Manifest (Device Agent Service)**

Each agent advertises its supported tools, capabilities, and operational metadata, declaring what it can contribute to the constellation.

**Client-Side Telemetry (Device Agent Client)**

Local clients continuously report runtime metrics including OS information, hardware specifications, GPU availability, and environment status.

The ConstellationClient merges these inputs into a unified, dynamically refreshed AgentProfile. This multi-level profiling pipeline:

- Improves task allocation accuracy through comprehensive capability discovery
- Enables transparent adaptation to environmental drift without administrator intervention
- Maintains fresh and consistent metadata across all distributed agents
- Supports informed scheduling decisions even as the system scales

### 2. Task Dispatch and Result Delivery

AIP orchestrates task execution through persistent **sessions** that connect the orchestrator to device agents.

**Task Assignment Flow**

1. ConstellationClient assigns a Task★ to target device
2. Sends serialized `TASK` message to device agent service
3. Service resolves logical device ID and establishes/reuses session
4. Task payload streams to target client
5. Client executes task using local resources and MCP tools

**Result Reporting Flow**

1. Device agent service aggregates execution outcomes
2. Emits structured `TASK_END` message with status, logs, and evaluator outputs
3. ConstellationClient updates TaskConstellation state
4. Notifies ConstellationAgent for potential DAG revision

This unified approach enables asynchronous computation, dynamic planning, and result propagation through a single protocol.

### 3. Command Execution

At a finer granularity, AIP provides a unified **command execution model**.

**Command Structure**

Each `COMMAND` message carries:

- Unique identifier for correlation
- Target function or tool name
- Ordered list of typed arguments
- Tool type (data_collection or action)

**Execution Guarantees**

Within a session, device agents execute commands sequentially to ensure determinism. Commands can be batched in a single request to reduce network overhead and support multi-action workflows.

**Result Handling**

Each command returns a structured `Result` object containing:

- Status code (SUCCESS, FAILURE, SKIPPED, NONE)
- Return value with actual data
- Error metadata when applicable
- Namespace and call_id for correlation

Timeouts and exceptions are explicitly propagated through the same channel, allowing precise recovery or reassignment strategies.

## Message Protocol

AIP uses strongly-typed messages (Pydantic models) that flow bidirectionally between clients and servers.

### Message Types

**Client → Server**

- `REGISTER`: Initial registration with capability advertisement
- `TASK`: Request to execute a task
- `COMMAND_RESULTS`: Return results of executed commands
- `TASK_END`: Notify task completion
- `HEARTBEAT`: Periodic keepalive signal
- `DEVICE_INFO_REQUEST/RESPONSE`: Device information exchange
- `ERROR`: Report error conditions

**Server → Client**

- `TASK`: Task assignment to device
- `COMMAND`: Command(s) to execute
- `TASK_END`: Task completion notification
- `HEARTBEAT`: Keepalive acknowledgment
- `DEVICE_INFO_REQUEST/RESPONSE`: Device information exchange
- `ERROR`: Error notification

### Session Management

Sessions are identified by unique `session_id` values and maintain context across multiple message exchanges. Each message includes:

- `timestamp`: ISO 8601 formatted timestamp
- `request_id` or `response_id`: Unique message identifier
- `prev_response_id`: For correlating request-response chains

## Resilient Connection Protocol

AIP defines a comprehensive **Resilient Connection Protocol** to ensure stable communication and consistent orchestration across the distributed agent constellation.

### Connection State Management

**Device Disconnection Handling**

When a Device Agent becomes unreachable:

1. Orchestrator immediately marks agent as `DISCONNECTED`
2. Agent becomes invisible to ConstellationAgent scheduler
3. Excluded from new task assignments
4. Automatic reconnection routine triggered in background

**Successful Reconnection**

- Agent transitions back to `CONNECTED` state
- Resumes participation in scheduling
- Previous context restored where possible

**Disconnection During Task Execution**

- All tasks running on affected device marked as `TASK_FAILED`
- Failure events propagated to ConstellationAgent
- Initiates constellation edit cycle
- Global task graph synchronized with runtime state

### Bidirectional Fault Handling

**ConstellationClient Disconnection**

When the ConstellationClient disconnects:

1. Device Agent Server receives termination signal
2. Proactively aborts all ongoing tasks tied to that client
3. Prevents resource leakage and inconsistent states
4. Maintains end-to-end consistency across client-server boundary

This symmetric approach ensures:

- Continuous coordination under network instability
- Rapid recovery from transient failures
- Synchronized task state reflection across all layers
- No orphaned tasks or zombie processes

## Extensibility

AIP's design emphasizes extensibility at multiple levels:

### Protocol Middleware

Developers can add custom middleware to the protocol pipeline for cross-cutting concerns:

```python
from aip.protocol.base import ProtocolMiddleware

class CustomLoggingMiddleware(ProtocolMiddleware):
    async def process_outgoing(self, msg):
        # Log or modify outgoing messages
        return msg
    
    async def process_incoming(self, msg):
        # Log or modify incoming messages
        return msg

protocol.add_middleware(CustomLoggingMiddleware())
```

### Custom Message Handlers

Register handlers for specific message types:

```python
async def handle_custom_message(msg):
    # Process custom message type
    pass

protocol.register_handler("custom_type", handle_custom_message)
```

### Transport Abstraction

While WebSocket is the default, AIP's transport layer is pluggable. Future implementations can add HTTP/3, gRPC, or custom transports by implementing the `Transport` interface.

## Integration with UFO² Ecosystem

AIP seamlessly integrates with other UFO² components:

**MCP (Model Context Protocol)**

AIP's command execution model aligns directly with MCP server message formats, unifying system-level actions and model-generated tool calls under a consistent interface.

**TaskConstellation**

The orchestrator uses AIP to maintain real-time synchronization between the planning DAG and distributed execution state.

**Configuration System**

Agent endpoints, capabilities, and connection parameters are managed through UFO²'s modular configuration system.

**Logging and Monitoring**

Comprehensive logging at all protocol layers enables debugging, performance monitoring, and audit trails.

## Key Benefits

**Persistence**

Long-lived connections reduce overhead and maintain context across multiple interactions.

**Low Latency**

WebSocket's full-duplex communication enables real-time event propagation aligned with orchestrator's scheduling loop.

**Standardization**

Any device agent service implementing the TASK-TASK_END protocol can seamlessly integrate into UFO².

**Reliability**

Built-in resilience mechanisms ensure graceful handling of network failures and device disconnections.

**Scalability**

Multiplexed connections and efficient message batching support large-scale multi-agent deployments.

**Developer Experience**

Strongly-typed messages, clear error handling, and comprehensive documentation reduce integration effort.

## Getting Started

To use AIP in your UFO² deployment:

1. **Device Server Setup**: Use `DeviceServerEndpoint` to expose WebSocket endpoints
2. **Device Client Connection**: Use `DeviceClientEndpoint` to connect clients to services
3. **Constellation Orchestration**: Use `ConstellationEndpoint` for multi-device coordination

For detailed implementation guides, see:

- [Message Reference](./messages.md) - Complete message type documentation
- [Protocol Guide](./protocols.md) - Protocol implementation details
- [Transport Layer](./transport.md) - WebSocket transport configuration
- [Endpoints](./endpoints.md) - Endpoint setup and usage
- [Resilience](./resilience.md) - Connection management and recovery

## Summary

AIP transforms distributed workflow execution into a coherent, safe, and adaptive system where reasoning and execution converge seamlessly across diverse agents and environments. By abstracting away network and device heterogeneity, AIP enables the orchestrator to treat all agents as first-class citizens in a single, event-driven control plane.
