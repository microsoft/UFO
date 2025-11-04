# Session Manager

The **SessionManager** is responsible for managing agent session lifecycles, coordinating background task execution, and maintaining execution state across the server.

## Overview

The SessionManager provides:

- Platform-agnostic session creation (Windows/Linux)
- Background task execution without blocking WebSocket event loop
- Session state tracking and result storage
- Graceful task cancellation
- Concurrent session management

## Core Functionality

### Session Creation

The SessionManager uses **SessionFactory** to create platform-specific sessions:

```python
session = session_manager.get_or_create_session(
    session_id="session_123",
    task_name="create_file",
    request="Open Notepad and create a file",
    websocket=ws,
    platform_override="windows"
)
```

**Session Types:**

**Service Sessions**

For remote WebSocket clients:

- Platform-specific implementations (WindowsServiceSession, LinuxServiceSession)
- WebSocket-based command dispatcher
- Remote tool execution via MCP servers

**Local Sessions**

For local testing and development:

- Direct execution without WebSocket
- Simplified command dispatcher
- Useful for debugging

!!!tip
    The SessionFactory automatically selects the appropriate session type based on the `local` flag and platform.

### Background Execution

The SessionManager executes tasks asynchronously to prevent blocking:

```python
await session_manager.execute_task_async(
    session_id=session_id,
    task_name=task_name,
    request=user_request,
    websocket=websocket,
    platform_override="windows",
    callback=result_callback
)
```

**Benefits of background execution:**

- WebSocket ping/pong continues uninterrupted
- Heartbeat messages flow during task execution
- Multiple sessions can run concurrently
- No event loop blocking

!!!success
    Background execution is critical for maintaining WebSocket connection health during long-running tasks.

### Callback Mechanism

When a task completes, the SessionManager invokes the registered callback:

```python
async def send_result(session_id: str, result_msg: ServerMessage):
    """Called when task completes."""
    await websocket.send_text(result_msg.model_dump_json())

await session_manager.execute_task_async(
    ...,
    callback=send_result
)
```

**Callback execution flow:**

1. Task completes (success, failure, or cancellation)
2. Results are collected and formatted
3. ServerMessage (TASK_END) is constructed
4. Callback is invoked with session_id and message
5. Results are persisted for retrieval

### Task Cancellation

The SessionManager supports graceful task cancellation:

```python
await session_manager.cancel_task(
    session_id="session_123",
    reason="device_disconnected"
)
```

**Cancellation Reasons:**

**constellation_disconnected**

- Constellation client disconnected
- Don't send callback (client already gone)
- Mark tasks as FAILED

**device_disconnected**

- Target device disconnected
- Send callback to constellation (notify orchestrator)
- Allow task reassignment

!!!warning
    Cancellation is asynchronous - the task may complete before cancellation takes effect.

## Session Lifecycle

### 1. Creation

```python
# Session creation via get_or_create_session
session = session_manager.get_or_create_session(
    session_id="abc123",
    task_name="demo_task",
    request="User request text",
    platform_override="windows"
)
```

### 2. Execution

```python
# Background execution
await session_manager.execute_task_async(...)

# Session runs in background
# Event loop continues processing other messages
```

### 3. Completion

```python
# Session completes naturally
# Results collected: session.results

# Callback invoked
await callback(session_id, result_message)

# Results persisted
session_manager.set_results(session_id)
```

### 4. Cleanup

```python
# Session removed after result retrieval
session_manager.remove_session(session_id)
```

## State Management

### Session Storage

Sessions are stored in a thread-safe dictionary:

```python
self.sessions: Dict[str, BaseSession] = {}
```

**Thread safety:**

- Uses threading.Lock for concurrent access
- Safe for multi-threaded environments
- Prevents race conditions

### Result Storage

Results are cached after completion:

```python
self.results: Dict[str, Dict[str, Any]] = {}
```

**Result retrieval:**

```python
# By session ID
result = session_manager.get_result("session_123")

# By task name
result = session_manager.get_result_by_task("demo_task")
```

### Task Tracking

Background tasks are tracked for cancellation:

```python
self._running_tasks: Dict[str, asyncio.Task] = {}
```

## Platform Support

### Windows Sessions

Created when `platform_override="windows"`:

- Uses Windows-specific UI automation
- COM/Win32 API integration
- Windows MCP tools

### Linux Sessions

Created when `platform_override="linux"`:

- Uses X11/Wayland automation
- DBus integration
- Linux MCP tools

!!!info
    Platform is auto-detected from `platform.system()` if not specified.

## Error Handling

### Session Errors

```python
try:
    await session.run()
except Exception as e:
    # Error logged
    # Status set to FAILED
    # Error message included in results
```

### Callback Errors

```python
try:
    await callback(session_id, result_message)
except Exception as e:
    # Error logged but doesn't fail session
    # Prevents callback errors from breaking execution
```

## Best Practices

**Set Appropriate Timeouts**

Configure session timeouts based on task complexity:

```python
# Short tasks: 60-120 seconds
# Medium tasks: 120-300 seconds  
# Long tasks: 300-600 seconds
```

**Monitor Session Count**

Prevent resource exhaustion:

```python
active_count = len(session_manager.sessions)
if active_count > MAX_SESSIONS:
    # Reject new sessions or cancel old ones
```

**Clean Up Results**

Remove old results to prevent memory growth:

```python
# After retrieving results
session_manager.remove_session(session_id)
```

**Handle Cancellation Gracefully**

Different cancellation reasons require different handling:

```python
if reason == "constellation_disconnected":
    # Don't send callback
    pass
elif reason == "device_disconnected":
    # Send callback to constellation
    await callback(session_id, failure_message)
```

## Integration with Server Components

### WebSocket Handler

Handler creates sessions and registers callbacks:

```python
await session_manager.execute_task_async(
    session_id=session_id,
    callback=lambda sid, msg: self.send_result(sid, msg)
)
```

### WebSocket Manager

Tracks session-to-client mappings:

```python
# Constellation session
ws_manager.add_constellation_session(client_id, session_id)

# Device session
ws_manager.add_device_session(device_id, session_id)
```

### Session Factory

Creates platform-specific sessions:

```python
session = session_factory.create_service_session(
    task=task_name,
    platform_override=platform,
    websocket=websocket
)
```

## API Reference

```python
from ufo.server.services.session_manager import SessionManager

# Initialize
manager = SessionManager(platform_override="windows")

# Create session
session = manager.get_or_create_session(
    session_id="abc",
    task_name="task",
    request="request text",
    websocket=ws
)

# Execute async
await manager.execute_task_async(
    session_id="abc",
    task_name="task",
    request="request",
    websocket=ws,
    platform_override="windows",
    callback=my_callback
)

# Cancel task
await manager.cancel_task("abc", reason="device_disconnected")

# Get results
result = manager.get_result("abc")
result = manager.get_result_by_task("task")

# Remove session
manager.remove_session("abc")
```

For more information:

- [Overview](./overview.md) - Server architecture
- [WebSocket Handler](./websocket_handler.md) - Message handling
- [WebSocket Manager](./websocket_manager.md) - Connection management
