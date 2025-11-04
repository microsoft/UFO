# AIP Resilience

AIP's resilience layer ensures stable communication and consistent orchestration across distributed agent constellations. This document covers connection management, reconnection strategies, heartbeat monitoring, and timeout handling.

## Resilient Connection Protocol

The **Resilient Connection Protocol** governs how connection disruptions are detected, handled, and recovered between ConstellationClient and Device Agents.

### Connection State Management

#### Device Disconnection Workflow

When a Device Agent becomes unreachable:

**1. Detection**

Connection failure detected via:
- WebSocket close event
- Heartbeat timeout
- Network error during send/receive

**2. State Transition**

```
CONNECTED → DISCONNECTED
```

Agent becomes invisible to ConstellationAgent scheduler and is excluded from new task assignments.

**3. Task Failure Propagation**

All tasks running on the affected device are immediately marked as `TASK_FAILED`. Failure events propagate to ConstellationAgent.

**4. Automatic Reconnection**

Background reconnection routine triggered with exponential backoff.

**5. Recovery**

On successful reconnection:

```
DISCONNECTED → CONNECTED
```

Agent resumes participation in scheduling.

!!!warning
    During disconnection, no new tasks are assigned to the affected agent. Existing tasks fail immediately.

#### ConstellationClient Disconnection

When the ConstellationClient disconnects:

**1. Detection**

Device Agent Server receives termination signal (WebSocket close).

**2. Task Abortion**

Server proactively aborts all ongoing tasks tied to that client:

```python
# Server-side automatic cleanup
await device_server.cancel_all_tasks_for_client(client_id)
```

**3. Resource Cleanup**

Prevents resource leakage and inconsistent states.

!!!success
    Bidirectional fault handling ensures end-to-end consistency across the client-server boundary.

## Reconnection Strategy

The `ReconnectionStrategy` manages automatic reconnection with configurable backoff policies.

### Configuration

```python
from aip.resilience import ReconnectionStrategy, ReconnectionPolicy

strategy = ReconnectionStrategy(
    max_retries=5,                    # Maximum reconnection attempts
    initial_backoff=1.0,              # Initial backoff (seconds)
    max_backoff=60.0,                 # Maximum backoff (seconds)
    backoff_multiplier=2.0,           # Exponential multiplier
    policy=ReconnectionPolicy.EXPONENTIAL_BACKOFF
)
```

### Reconnection Policies

**EXPONENTIAL_BACKOFF (Default)**

Backoff time doubles after each failed attempt:

```
Attempt 1: 1.0s
Attempt 2: 2.0s
Attempt 3: 4.0s
Attempt 4: 8.0s
Attempt 5: 16.0s
```

Capped at `max_backoff`.

**LINEAR_BACKOFF**

Backoff time increases linearly:

```
Attempt 1: 1.0s
Attempt 2: 2.0s
Attempt 3: 3.0s
Attempt 4: 4.0s
Attempt 5: 5.0s
```

**IMMEDIATE**

No backoff, immediate retry:

```
All attempts: 0s delay
```

!!!danger
    `IMMEDIATE` policy can overwhelm servers. Use only for testing.

**NONE**

No automatic reconnection:

```
Reconnection disabled
```

### Reconnection Workflow

```python
async def handle_disconnection(
    endpoint: AIPEndpoint,
    device_id: str,
    on_reconnect: Optional[Callable] = None
):
    # Step 1: Cancel pending tasks
    await strategy._cancel_pending_tasks(endpoint, device_id)
    
    # Step 2: Notify upper layers
    await strategy._notify_disconnection(endpoint, device_id)
    
    # Step 3: Attempt reconnection
    reconnected = await strategy.attempt_reconnection(endpoint, device_id)
    
    # Step 4: Call reconnection callback
    if reconnected and on_reconnect:
        await on_reconnect()
```

### Attempt Reconnection

```python
async def attempt_reconnection(
    endpoint: AIPEndpoint,
    device_id: str
) -> bool:
    retry_count = 0
    
    while retry_count < max_retries:
        # Calculate backoff
        backoff = calculate_backoff(retry_count)
        
        # Wait
        await asyncio.sleep(backoff)
        
        # Try to reconnect
        success = await endpoint.reconnect_device(device_id)
        
        if success:
            return True
        
        retry_count += 1
    
    # Max retries reached
    return False
```

### Custom Reconnection Callback

```python
async def on_reconnected():
    print("Device reconnected, resuming tasks")
    # Resume pending operations
    await resume_task_queue()

await strategy.handle_disconnection(
    endpoint=endpoint,
    device_id="device_001",
    on_reconnect=on_reconnected
)
```

## Heartbeat Manager

The `HeartbeatManager` sends periodic keepalive messages to monitor connection health.

### Initialization

```python
from aip.resilience import HeartbeatManager
from aip.protocol import HeartbeatProtocol

heartbeat_protocol = HeartbeatProtocol(transport)
heartbeat_manager = HeartbeatManager(
    protocol=heartbeat_protocol,
    default_interval=30.0  # 30 seconds
)
```

### Starting Heartbeat

```python
# Start heartbeat for a client
await heartbeat_manager.start_heartbeat(
    client_id="device_001",
    interval=20.0  # Override default
)
```

### Stopping Heartbeat

```python
# Stop for specific client
await heartbeat_manager.stop_heartbeat("device_001")

# Stop all heartbeats
await heartbeat_manager.stop_all()
```

### Checking Status

```python
# Check if heartbeat running
if heartbeat_manager.is_running("device_001"):
    print("Heartbeat active")

# Get interval
interval = heartbeat_manager.get_interval("device_001")
print(f"Heartbeat interval: {interval}s")
```

### Heartbeat Loop

Internally, the manager runs an async loop per client:

```python
async def _heartbeat_loop(client_id: str, interval: float):
    while True:
        await asyncio.sleep(interval)
        
        if protocol.is_connected():
            await protocol.send_heartbeat(client_id)
        else:
            # Connection lost
            break
```

### Failure Detection

If heartbeat fails to send (e.g., connection closed), the loop exits and triggers disconnection handling.

!!!tip
    Set shorter intervals (10-20s) for quick failure detection, longer intervals (30-60s) to reduce network overhead.

## Timeout Manager

The `TimeoutManager` enforces timeouts on protocol operations.

### Initialization

```python
from aip.resilience import TimeoutManager

timeout_manager = TimeoutManager(
    default_timeout=120.0  # 120 seconds
)
```

### Using Timeouts

**With default timeout:**

```python
result = await timeout_manager.with_timeout(
    protocol.send_message(msg),
    operation_name="send_message"
)
```

**With custom timeout:**

```python
result = await timeout_manager.with_timeout(
    protocol.receive_message(ServerMessage),
    timeout=60.0,
    operation_name="receive_message"
)
```

### Timeout Handling

```python
from asyncio import TimeoutError

try:
    result = await timeout_manager.with_timeout(
        long_running_operation(),
        timeout=30.0
    )
except TimeoutError:
    logger.error("Operation timed out after 30 seconds")
    # Handle timeout
```

### Recommended Timeouts

**Registration**: 10-30 seconds
**Task dispatch**: 30-60 seconds
**Command execution**: 60-300 seconds (depends on complexity)
**Heartbeat**: 5-10 seconds
**Disconnection**: 5-15 seconds

## Integration with Endpoints

Endpoints automatically integrate resilience components:

```python
from aip.endpoints import DeviceClientEndpoint
from aip.resilience import ReconnectionStrategy

# Create endpoint with reconnection
endpoint = DeviceClientEndpoint(
    ws_url="ws://localhost:8000/ws",
    ufo_client=client,
    reconnection_strategy=ReconnectionStrategy(
        max_retries=3,
        initial_backoff=2.0,
        max_backoff=60.0
    )
)

# Resilience handled automatically
await endpoint.start()
```

### Automatic Features

**Reconnection on Disconnect**

Triggered automatically when connection fails.

**Heartbeat Management**

Device clients automatically start heartbeat on connection.

**Timeout Enforcement**

All protocol operations subject to configurable timeouts.

**Task Cancellation**

Pending tasks canceled automatically on disconnection.

## Best Practices

### Configure for Network Environment

**Local Network (Low Latency, High Reliability)**

```python
strategy = ReconnectionStrategy(
    max_retries=3,
    initial_backoff=1.0,
    max_backoff=10.0,
    policy=ReconnectionPolicy.LINEAR_BACKOFF
)
heartbeat_interval = 20.0  # Quick detection
```

**Internet (Variable Latency, Moderate Reliability)**

```python
strategy = ReconnectionStrategy(
    max_retries=5,
    initial_backoff=2.0,
    max_backoff=60.0,
    policy=ReconnectionPolicy.EXPONENTIAL_BACKOFF
)
heartbeat_interval = 30.0  # Balance overhead and detection
```

**Unreliable Network (High Latency, Low Reliability)**

```python
strategy = ReconnectionStrategy(
    max_retries=10,
    initial_backoff=5.0,
    max_backoff=300.0,  # Up to 5 minutes
    policy=ReconnectionPolicy.EXPONENTIAL_BACKOFF
)
heartbeat_interval = 60.0  # Reduce overhead
```

### Monitor Connection Health

```python
import logging

# Enable resilience logging
logging.getLogger("aip.resilience").setLevel(logging.INFO)

# Log reconnection events
logger.info(f"Device {device_id} reconnected after {retry_count} attempts")
```

### Handle Reconnection Events

Override endpoint methods for custom behavior:

```python
class CustomEndpoint(DeviceClientEndpoint):
    async def on_device_disconnected(self, device_id: str) -> None:
        # Custom cleanup
        await self.cleanup_resources(device_id)
        
        # Call parent
        await super().on_device_disconnected(device_id)
    
    async def reconnect_device(self, device_id: str) -> bool:
        # Custom reconnection logic
        success = await self.custom_reconnect(device_id)
        
        if success:
            await self.restore_state(device_id)
        
        return success
```

### Graceful Degradation

When reconnection fails after max retries:

```python
if not await strategy.attempt_reconnection(endpoint, device_id):
    logger.error(f"Failed to reconnect {device_id} after max retries")
    
    # Graceful degradation
    await notify_operator(f"Device {device_id} offline")
    await reassign_tasks_to_other_devices(device_id)
```

### Test Resilience

Simulate failures to test resilience:

```python
# Simulate disconnection
await transport.close()

# Verify reconnection
assert await endpoint.reconnect_device(device_id)

# Verify heartbeat resumes
assert heartbeat_manager.is_running(device_id)
```

## Error Scenarios

### Scenario 1: Transient Network Failure

**Problem**: Network glitch disconnects client briefly.

**Resolution**:

1. Disconnection detected via heartbeat timeout
2. Automatic reconnection triggered (1st attempt after 2s)
3. Connection restored successfully
4. Heartbeat resumes
5. Tasks continue

### Scenario 2: Prolonged Outage

**Problem**: Device offline for extended period.

**Resolution**:

1. Initial disconnection detected
2. Multiple reconnection attempts (exponential backoff)
3. All attempts fail (max retries reached)
4. Tasks marked as FAILED
5. ConstellationAgent notified
6. Tasks reassigned to other devices

### Scenario 3: Server Restart

**Problem**: Server restarts, all clients disconnect.

**Resolution**:

1. All clients detect disconnection simultaneously
2. Each client begins reconnection (with jitter to avoid thundering herd)
3. Server restarts and accepts new connections
4. Clients reconnect and re-register
5. Task execution resumes

### Scenario 4: Heartbeat Timeout

**Problem**: Heartbeat not received within timeout.

**Resolution**:

1. HeartbeatManager detects missing pong
2. Connection marked as potentially dead
3. Disconnection handling triggered
4. Reconnection attempted
5. If successful, heartbeat resumes

## API Reference

```python
from aip.resilience import (
    ReconnectionStrategy,
    ReconnectionPolicy,
    HeartbeatManager,
    TimeoutManager,
)
```

For more information:

- [Endpoints](./endpoints.md) - How endpoints use resilience
- [Transport Layer](./transport.md) - Transport-level connection management
- [Protocol Reference](./protocols.md) - Protocol-level error handling
- [Overview](./overview.md) - System architecture
