# Galaxy Client Components

Galaxy Client is built from focused, single-responsibility components that work together to provide device management capabilities. This document explains how these components interact and what each one does.

**Related Documentation:**

- [Overview](./overview.md) - Overall architecture and workflow
- [DeviceManager](./device_manager.md) - How components are orchestrated
- [ConstellationClient](./constellation_client.md) - Component usage in coordination layer

---

## Component Architecture Overview

Galaxy Client uses 8 modular components divided into three categories: **Device Management**, **Display & UI**, and **Orchestration Support**. Understanding how these components work together is key to understanding Galaxy Client's design.

### The Big Picture: How Components Collaborate

When DeviceManager needs to manage a device connection, it doesn't do everything itself. Instead, it delegates specific responsibilities to specialized components:

```mermaid
graph TB
    DM[DeviceManager<br/>Orchestrator]
    
    subgraph "State Management"
        DR[DeviceRegistry<br/>Device State Storage]
    end
    
    subgraph "Connection Layer"
        WS[WebSocketConnectionManager<br/>Network Communication]
        HM[HeartbeatManager<br/>Health Monitoring]
        MP[MessageProcessor<br/>Message Handling]
    end
    
    subgraph "Task Layer"
        TQ[TaskQueueManager<br/>Task Scheduling]
    end
    
    DM --> DR
    DM --> WS
    DM --> HM
    DM --> MP
    DM --> TQ
    
    WS -.->|updates| DR
    HM -.->|reads| DR
    HM -.->|uses| WS
    MP -.->|updates| DR
    MP -.->|uses| WS
    
    style DM fill:#e1f5ff
    style DR fill:#fff4e1
```

This diagram shows the component relationships. DeviceManager acts as the orchestrator, creating and coordinating all other components. DeviceRegistry serves as the single source of truth for device state. WebSocketConnectionManager, HeartbeatManager, and MessageProcessor all depend on both DeviceRegistry (for state) and each other (for operations). TaskQueueManager works independently, managing task queues.

**Key Design Principles:**

1. **Single Source of Truth**: DeviceRegistry is the only component that stores device state. All other components read from or write to DeviceRegistry, never maintaining their own state.

2. **Dependency Injection**: DeviceManager creates all components and injects dependencies. For example, HeartbeatManager receives references to both WebSocketConnectionManager (to send heartbeats) and DeviceRegistry (to update timestamps).

3. **Background Services**: HeartbeatManager and MessageProcessor run as independent asyncio tasks. They operate continuously in the background without blocking the main execution flow.

4. **Component Independence**: Each component can be tested and understood in isolation. Changing one component's implementation doesn't affect others as long as the interface remains the same.

---

## Device Management Components

These components handle the core device lifecycle: registration, connection, monitoring, and task execution.

### DeviceRegistry: The Single Source of Truth

**Purpose**: DeviceRegistry is the central repository for all device information. Every component that needs to know about device state queries DeviceRegistry.

**What It Stores**: Each device is represented by an `AgentProfile` object containing:

```python
@dataclass
class AgentProfile:
    device_id: str              # Unique device identifier
    server_url: str             # WebSocket endpoint
    os: str                     # Operating system (windows/linux/mac)
    status: DeviceStatus        # Current state (DISCONNECTED/CONNECTING/CONNECTED/IDLE/BUSY/FAILED)
    capabilities: List[str]     # What the device can do (["office", "web", "email"])
    metadata: Dict[str, Any]    # Custom device properties
    last_heartbeat: datetime    # Last successful heartbeat timestamp
    connection_attempts: int    # Number of connection attempts made
    max_retries: int           # Maximum reconnection attempts allowed
    current_task_id: str       # Task being executed (None if idle)
    system_info: Dict          # Hardware/software details from device
```

The `status` field is particularly important as it drives the system's behavior. When a device is IDLE, it can accept new tasks. When BUSY, tasks are queued. When DISCONNECTED, reconnection is attempted.

**Key Operations**:

```python
# Registration and lookup
registry.register_device(device_id, server_url, os, capabilities, metadata)
profile = registry.get_device(device_id)
all_devices = registry.get_all_devices(connected=True)

# Status management
registry.update_device_status(device_id, DeviceStatus.CONNECTED)
is_busy = registry.is_device_busy(device_id)
registry.set_device_busy(device_id, task_id)
registry.set_device_idle(device_id)

# Health tracking
registry.update_heartbeat(device_id)
registry.increment_connection_attempts(device_id)
registry.reset_connection_attempts(device_id)
```

**Why It Matters**: Having a single registry prevents state inconsistencies. Without DeviceRegistry, each component might have its own view of device state, leading to race conditions and bugs. For example, HeartbeatManager might think a device is connected while MessageProcessor thinks it's disconnected.

### WebSocketConnectionManager: Network Communication Handler

**Purpose**: Manages the low-level WebSocket connections to Agent Server and handles message transmission.

**Connection Lifecycle**:

When `connect_to_device()` is called, WebSocketConnectionManager performs these steps:

1. **Establish WebSocket**: Uses `websockets.connect()` to create a connection to the device's server_url. This is an async operation that may timeout or fail due to network issues.

2. **Send REGISTER**: Immediately sends an AIP REGISTER message to identify this client to the server. The server responds with a confirmation once registration succeeds.

3. **Store Connection**: Saves the WebSocket object in an internal dictionary `{device_id: websocket}`. Other components retrieve this WebSocket when they need to send messages.

4. **Start Message Handler**: Crucially, this happens *before* waiting for REGISTER confirmation to prevent race conditions. If the server sends a response before we start listening, we'd miss it.

**Task Execution**:

When sending a task to a device, WebSocketConnectionManager:

```python
async def send_task_to_device(device_id, task_request):
    # 1. Get WebSocket connection
    websocket = self.connections[device_id]
    
    # 2. Create AIP TASK message
    task_msg = ClientMessage(
        type=ClientMessageType.TASK,
        client_id=self.client_id,
        target_id=device_id,
        session_id=task_request.task_id,
        request=task_request.request,
        ...
    )
    
    # 3. Send message
    await websocket.send(task_msg.model_dump_json())
    
    # 4. Wait for response (handled by MessageProcessor)
    result = await self._wait_for_task_completion(device_id, task_request.task_id)
    
    return result
```

The `_wait_for_task_completion()` method creates an asyncio.Future that MessageProcessor will complete when it receives the TASK_END message from the device.

**Error Handling**: WebSocketConnectionManager catches connection errors (InvalidURI, WebSocketException, OSError, TimeoutError) and returns False, allowing DeviceManager to trigger reconnection logic.

### HeartbeatManager: Connection Health Monitor

**Purpose**: Continuously monitors device health by sending periodic heartbeat messages. This detects connection failures much faster than waiting for a task to timeout.

**How It Works**:

For each connected device, HeartbeatManager starts an independent background task:

```python
async def _send_heartbeat_loop(device_id):
    while True:
        try:
            # Get WebSocket connection
            websocket = self.connection_manager.get_connection(device_id)
            
            # Create heartbeat message
            heartbeat_msg = ClientMessage(
                type=ClientMessageType.HEARTBEAT,
                client_id=device_id,
                timestamp=datetime.now().isoformat()
            )
            
            # Send and wait for response
            await websocket.send(heartbeat_msg.model_dump_json())
            response = await asyncio.wait_for(
                websocket.recv(),
                timeout=self.heartbeat_interval * 2
            )
            
            # Update last heartbeat timestamp
            self.device_registry.update_heartbeat(device_id)
            
            # Wait before next heartbeat
            await asyncio.sleep(self.heartbeat_interval)
            
        except asyncio.TimeoutError:
            # Device didn't respond - trigger disconnection
            await self._handle_heartbeat_timeout(device_id)
            break
```

**Timeout Detection**: The timeout is set to `2 × heartbeat_interval`. For a 30-second interval, if no response arrives within 60 seconds, the device is considered disconnected. This gives enough time for network latency while still detecting failures relatively quickly.

**Why Not Just Use TCP Keepalive?**: WebSocket runs over TCP, which has its own keepalive mechanism. However, TCP keepalive operates at a much longer timescale (typically 2 hours by default) and only detects network-level failures, not application-level hangs. HeartbeatManager detects if the device agent is responsive, not just if the TCP connection is alive.

### MessageProcessor: Message Router and Handler

**Purpose**: Runs a continuous message receiving loop for each device, dispatching incoming AIP messages to appropriate handlers.

**The Message Loop**:

```python
async def _process_messages(device_id, websocket):
    while True:
        try:
            # Receive raw message from WebSocket
            msg = await websocket.recv()
            
            # Parse as AIP message
            data = ClientMessage.model_validate_json(msg)
            
            # Route to specific handler based on message type
            if data.type == ClientMessageType.TASK_END:
                await self._handle_task_end(device_id, data)
            elif data.type == ClientMessageType.COMMAND_RESULTS:
                await self._handle_command_results(device_id, data)
            elif data.type == ClientMessageType.HEARTBEAT_ACK:
                # Heartbeat handled by HeartbeatManager
                pass
            elif data.type == ClientMessageType.ERROR:
                await self._handle_error(device_id, data)
                
        except websockets.ConnectionClosed:
            # Connection dropped - trigger disconnection handling
            await self.disconnection_handler(device_id)
            break
```

**Task Completion Handling**: When a TASK_END message arrives, MessageProcessor completes the corresponding future that WebSocketConnectionManager is waiting on:

```python
async def _handle_task_end(device_id, message):
    task_id = message.session_id
    
    # Create ExecutionResult from message
    result = ExecutionResult(
        task_id=task_id,
        status=message.status,
        result=message.result,
        error=message.error,
        metadata=message.metadata
    )
    
    # Complete the waiting future
    if task_id in self.pending_tasks[device_id]:
        future = self.pending_tasks[device_id][task_id]
        future.set_result(result)
        del self.pending_tasks[device_id][task_id]
```

**Why Run in Background**: The message loop runs continuously as an asyncio task. This allows it to receive messages asynchronously while the main execution flow (e.g., sending tasks) continues unblocked. Without this, we'd need to alternate between sending and receiving, making the code much more complex.

### TaskQueueManager: Task Scheduling and Queuing

**Purpose**: Manages per-device task queues, ensuring tasks execute sequentially when devices are busy.

**Queue Behavior**:

When a task is assigned to a device that's already executing another task:

```python
# In DeviceManager.assign_task_to_device()
if self.device_registry.is_device_busy(device_id):
    # Device is BUSY - enqueue task
    future = self.task_queue_manager.enqueue_task(device_id, task_request)
    # Wait for task to complete
    result = await future
    return result
else:
    # Device is IDLE - execute immediately
    return await self._execute_task_on_device(device_id, task_request)
```

**How Queuing Works**:

TaskQueueManager maintains a dictionary of queues: `{device_id: queue}`. Each queue is a list of `(task_request, future)` tuples. When a task is enqueued:

```python
def enqueue_task(device_id, task_request):
    # Create a future for this task
    future = asyncio.Future()
    
    # Add to device's queue
    self.queues[device_id].append((task_request, future))
    
    # Return future so caller can await result
    return future
```

When a device completes a task and becomes IDLE, DeviceManager calls:

```python
async def _process_next_queued_task(device_id):
    if self.task_queue_manager.has_queued_tasks(device_id):
        task_request = self.task_queue_manager.dequeue_task(device_id)
        # Execute next task (don't await to avoid blocking)
        asyncio.create_task(self._execute_task_on_device(device_id, task_request))
```

**Why Futures?**: Using asyncio.Future allows the calling code to await task completion even though the task is queued. The caller doesn't need to know whether the task executed immediately or was queued—it just awaits the future and gets the result when ready.

---

## Display Component

### ClientDisplay: User Interface and Console Output

**Purpose**: Provides Rich-based console output for interactive mode and status reporting. This component is only used by GalaxyClient, not by ConstellationClient or DeviceManager.

**Key Features**:

**Banner and Branding**: Shows ASCII art banner when GalaxyClient starts, creating a visual identity for the framework.

**Progress Indication**: Uses Rich Progress bars for long-running operations like initialization:

```python
with display.show_initialization_progress() as progress:
    task = progress.add_task("[cyan]Initializing...", total=None)
    # ... initialization work ...
    progress.update(task, description="[green]Complete!")
```

**Result Display**: Formats execution results in readable tables:

```python
display.display_result({
    "status": "completed",
    "execution_time": 23.45,
    "rounds": 2,
    "constellation": {"task_count": 5}
})
```

This creates a formatted table showing status, time, rounds, and task count in color-coded output.

**Interactive Input**: Provides user input prompts with styling:

```python
user_input = display.get_user_input("UFO[0]")
```

**Colored Messages**: Semantic color coding for different message types:
- Green (success): Task completed, connection established
- Red (error): Task failed, connection error
- Yellow (warning): Device disconnected, timeout
- Cyan (info): Status updates, progress

**Why Separate Component?**: Keeping display logic separate from business logic makes it easy to replace or disable. For example, a web-based frontend could replace ClientDisplay without touching any other components.

---

## Orchestration Components

These components support higher-level orchestration by providing status aggregation and event handling capabilities.

### StatusManager: System-Wide Status Aggregation

**Purpose**: Provides consolidated views of system health and performance across all devices. While DeviceRegistry stores individual device status, StatusManager aggregates this into system-wide metrics.

**Health Summary Example**:

```python
summary = status_manager.get_device_health_summary()
# Returns:
{
    "total_devices": 5,
    "connected_devices": 3,
    "disconnected_devices": 2,
    "connection_rate": 0.6,  # 60% connected
    "devices_by_status": {
        "CONNECTED": 2,
        "IDLE": 1,
        "DISCONNECTED": 1,
        "FAILED": 1
    },
    "devices_with_issues": [
        {
            "device_id": "device_3",
            "issue": "multiple_connection_attempts",
            "attempts": 4,
            "max_retries": 5
        }
    ]
}
```

**Task Statistics**:

```python
stats = status_manager.get_task_statistics()
# Returns:
{
    "total_tasks_executed": 127,
    "successful_tasks": 120,
    "failed_tasks": 7,
    "success_rate": 0.945,
    "average_execution_time": 15.3,  # seconds
    "tasks_by_device": {
        "windows_pc": 65,
        "linux_server": 62
    }
}
```

**Why This Matters**: In production, you need to monitor system health. StatusManager provides the data needed for dashboards, alerts, and capacity planning. For example, if connection_rate drops below 80%, you might trigger an alert.

### ClientEventHandler: Custom Event Callbacks

**Purpose**: Allows applications to register custom handlers for client-level events like device connection, disconnection, and task completion.

**Event Types**:

**Connection Events**: Fired when a device successfully connects:

```python
async def on_device_connected(device_id, device_info):
    logger.info(f"Device {device_id} connected with capabilities: {device_info.capabilities}")
    # Send notification to monitoring system
    await monitoring.report_device_online(device_id)

event_handler.add_connection_handler(on_device_connected)
```

**Disconnection Events**: Fired when a device disconnects (whether gracefully or due to error):

```python
async def on_device_disconnected(device_id):
    logger.warning(f"Device {device_id} disconnected")
    # Trigger alert if critical device
    if device_id in CRITICAL_DEVICES:
        await alert_system.send_alert(f"Critical device {device_id} offline")

event_handler.add_disconnection_handler(on_device_disconnected)
```

**Task Completion Events**: Fired when any task completes (success or failure):

```python
async def on_task_completed(device_id, task_id, result):
    # Log to metrics system
    await metrics.record_task(
        device_id=device_id,
        task_id=task_id,
        status=result.status,
        duration=result.metadata.get("execution_time")
    )

event_handler.add_task_completion_handler(on_task_completed)
```

**Why Extensibility Matters**: Different applications have different monitoring and notification needs. By providing event callbacks, Galaxy Client allows applications to integrate with their existing infrastructure (logging systems, metrics collection, alerting platforms) without modifying Galaxy Client's code.

---

## How Components Work Together: A Complete Example

Let's trace what happens when you call `device_manager.connect_device("windows_pc")`:

**Step 1: DeviceManager Initiates Connection**

```python
# DeviceManager.connect_device()
device_info = self.device_registry.get_device(device_id)  # Get device details
self.device_registry.update_device_status(device_id, DeviceStatus.CONNECTING)  # Update status
```

**Step 2: WebSocketConnectionManager Establishes Connection**

```python
# WebSocketConnectionManager.connect_to_device()
websocket = await websockets.connect(device_info.server_url)  # Create WebSocket
self.connections[device_id] = websocket  # Store connection

# Start message handler BEFORE sending REGISTER to avoid race condition
self.message_processor.start_message_handler(device_id, websocket)

# Send REGISTER message
await websocket.send(register_msg.model_dump_json())
```

**Step 3: MessageProcessor Starts Background Loop**

```python
# MessageProcessor.start_message_handler()
task = asyncio.create_task(self._process_messages(device_id, websocket))
self.message_handlers[device_id] = task  # Store task for later cancellation
```

Now MessageProcessor is running in the background, ready to receive messages.

**Step 4: Device Registration Completes**

The device sends back REGISTER_CONFIRMATION, which MessageProcessor receives and handles. Then WebSocketConnectionManager requests device info:

```python
# WebSocketConnectionManager.request_device_info()
await websocket.send(device_info_request.model_dump_json())
# Wait for response (received by MessageProcessor)
device_info = await self._wait_for_device_info_response(device_id)
```

**Step 5: DeviceRegistry Updated with System Info**

```python
# DeviceManager.connect_device() continues
self.device_registry.update_device_system_info(device_id, device_system_info)
self.device_registry.update_device_status(device_id, DeviceStatus.CONNECTED)
self.device_registry.set_device_idle(device_id)  # Ready for tasks
```

**Step 6: HeartbeatManager Starts Monitoring**

```python
# HeartbeatManager.start_heartbeat()
task = asyncio.create_task(self._send_heartbeat_loop(device_id))
self.heartbeat_tasks[device_id] = task
```

Now HeartbeatManager is running in the background, sending heartbeats every 30 seconds.

**Step 7: Connection Complete**

All components are now working together:
- DeviceRegistry knows the device is IDLE and ready
- WebSocketConnectionManager has an active WebSocket
- MessageProcessor is listening for incoming messages
- HeartbeatManager is monitoring connection health
- TaskQueueManager is ready to queue tasks if device becomes busy

This coordinated setup ensures reliable device communication.

---

## Component Dependencies

Understanding component dependencies helps when debugging or extending the system:

```
DeviceManager (creates all components)
├── DeviceRegistry (no dependencies - foundational)
├── WebSocketConnectionManager (depends on: DeviceRegistry for task name)
├── HeartbeatManager (depends on: WebSocketConnectionManager, DeviceRegistry)
├── MessageProcessor (depends on: DeviceRegistry, HeartbeatManager, WebSocketConnectionManager)
└── TaskQueueManager (no dependencies - independent)
```

**Construction Order**: DeviceManager must create components in dependency order:

```python
def __init__(self, task_name, heartbeat_interval, reconnect_delay):
    # 1. DeviceRegistry first (no dependencies)
    self.device_registry = DeviceRegistry()
    
    # 2. WebSocketConnectionManager (needs task_name only)
    self.connection_manager = WebSocketConnectionManager(task_name)
    
    # 3. HeartbeatManager (depends on connection_manager and device_registry)
    self.heartbeat_manager = HeartbeatManager(
        self.connection_manager,
        self.device_registry,
        heartbeat_interval
    )
    
    # 4. MessageProcessor (depends on all previous components)
    self.message_processor = MessageProcessor(
        self.device_registry,
        self.heartbeat_manager,
        self.connection_manager
    )
    
    # 5. TaskQueueManager (independent)
    self.task_queue_manager = TaskQueueManager()
```

**Why This Order Matters**: If we created MessageProcessor before HeartbeatManager, we'd get an error because MessageProcessor's constructor expects HeartbeatManager to exist. The dependency graph dictates construction order.

---

## Testing Components

The modular design makes components easy to test in isolation:

**Testing DeviceRegistry**:

```python
# No external dependencies needed
registry = DeviceRegistry()
registry.register_device("test_device", "ws://localhost:5000", "windows", ["test"])
assert registry.is_device_registered("test_device")
```

**Testing WebSocketConnectionManager**:

```python
# Mock the WebSocket connection
mock_websocket = AsyncMock()
connection_manager = WebSocketConnectionManager("test")
connection_manager.connections["test_device"] = mock_websocket

# Test message sending
await connection_manager.send_task_to_device("test_device", task_request)
mock_websocket.send.assert_called_once()
```

**Testing HeartbeatManager**:

```python
# Inject mock dependencies
mock_connection_manager = Mock()
mock_registry = Mock()
heartbeat_manager = HeartbeatManager(mock_connection_manager, mock_registry, 30.0)

# Test heartbeat loop
heartbeat_manager.start_heartbeat("test_device")
await asyncio.sleep(0.1)  # Let loop run
assert mock_connection_manager.get_connection.called
```

**Why Testability Matters**: Complex systems are hard to test. By breaking DeviceManager into 5 focused components, we can write targeted unit tests for each component's specific behavior, making bugs easier to find and fix.

---

## Summary

Galaxy Client's component architecture demonstrates several important design principles:

**Single Responsibility**: Each component does one thing well. DeviceRegistry stores state, WebSocketConnectionManager handles networking, HeartbeatManager monitors health, MessageProcessor routes messages, TaskQueueManager manages queues.

**Dependency Injection**: DeviceManager creates components and injects dependencies, making the system flexible and testable. Want to replace WebSocketConnectionManager with a different implementation? Just swap it out while keeping the interface.

**Separation of Concerns**: Business logic (in DeviceManager) is separate from display logic (in ClientDisplay) and orchestration support (in StatusManager and ClientEventHandler). Each layer can evolve independently.

**Asynchronous Background Services**: HeartbeatManager and MessageProcessor run as independent asyncio tasks, enabling concurrent operations without blocking the main execution flow.

This design makes Galaxy Client maintainable, extensible, and testable. When you understand how components collaborate, you can confidently modify or extend the system.

**Related Documentation**:

- [DeviceManager Reference](./device_manager.md) - See how DeviceManager orchestrates components
- [ConstellationClient](./constellation_client.md) - Learn how components are used in the coordination layer
- [Overview](./overview.md) - Understand the broader system architecture
