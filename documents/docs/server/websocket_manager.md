# WebSocket Manager

The **WSManager** maintains the registry of connected clients, tracks active sessions, and provides efficient lookup mechanisms for client information, device info, and session mapping.

## Overview

The WebSocket Manager provides:

- Client connection registry
- Session tracking and mapping
- Device information management
- Connection state monitoring
- Client statistics

## Core Data Structures

### ClientInfo

Each connected client is represented by a `ClientInfo` object:

```python
@dataclass
class ClientInfo:
    """Information about a connected client."""
    client_id: str              # Unique client identifier
    platform: str               # OS platform (windows, linux)
    websocket: WebSocket        # WebSocket connection
    client_type: ClientType     # DEVICE or CONSTELLATION
    metadata: dict              # Additional client metadata
    connect_time: float         # Connection timestamp
```

!!!info
    The `ClientInfo` structure provides all essential client information for routing and management.

## Client Registry

### Adding Clients

```python
def add_client(
    self,
    client_id: str,
    platform: str,
    websocket: WebSocket,
    client_type: ClientType,
    metadata: dict
):
    """Register a new client connection."""
    
    # Create client info
    client_info = ClientInfo(
        client_id=client_id,
        platform=platform,
        websocket=websocket,
        client_type=client_type,
        metadata=metadata,
        connect_time=time.time()
    )
    
    # Add to registry
    self.clients[client_id] = client_info
    self.online_clients.add(client_id)
    
    logger.info(f"[WS] ✅ Registered {client_type} client: {client_id}")
```

### Retrieving Clients

**Get WebSocket Connection**

```python
def get_client(self, client_id: str) -> WebSocket | None:
    """Get WebSocket connection for a client."""
    client_info = self.clients.get(client_id)
    return client_info.websocket if client_info else None
```

**Get Full Client Info**

```python
def get_client_info(self, client_id: str) -> ClientInfo | None:
    """Get complete information about a client."""
    return self.clients.get(client_id)
```

**Get All Connected Clients**

```python
def get_all_clients(self) -> list[ClientInfo]:
    """Get information about all connected clients."""
    return list(self.clients.values())
```

### Removing Clients

```python
def remove_client(self, client_id: str):
    """Remove a client from the registry."""
    
    # Remove from registry
    if client_id in self.clients:
        del self.clients[client_id]
    
    # Remove from online set
    self.online_clients.discard(client_id)
    
    logger.info(f"[WS] 🔌 Removed client: {client_id}")
```

## Connection State Checking

### Device Connection

```python
def is_device_connected(self, device_id: str) -> bool:
    """Check if a device client is currently connected."""
    
    client_info = self.clients.get(device_id)
    
    if not client_info:
        return False
    
    # Verify it's a device client (not constellation)
    return client_info.client_type == ClientType.DEVICE
```

!!!tip
    Use `is_device_connected()` before dispatching tasks to ensure the target device is available.

### Online Status

```python
def is_online(self, client_id: str) -> bool:
    """Check if a client is currently online."""
    return client_id in self.online_clients
```

## Session Mapping

The WSManager tracks which sessions are associated with each client for proper cleanup and result routing.

### Constellation Session Mapping

Track sessions initiated by constellation clients:

```python
def add_constellation_session(self, constellation_id: str, session_id: str):
    """Map a session to its constellation orchestrator."""
    
    if constellation_id not in self.constellation_sessions:
        self.constellation_sessions[constellation_id] = set()
    
    self.constellation_sessions[constellation_id].add(session_id)
```

```python
def get_constellation_sessions(self, constellation_id: str) -> set[str]:
    """Get all sessions for a constellation client."""
    return self.constellation_sessions.get(constellation_id, set())
```

```python
def remove_constellation_sessions(self, constellation_id: str):
    """Remove all session mappings for a constellation."""
    self.constellation_sessions.pop(constellation_id, None)
```

### Device Session Mapping

Track sessions executing on device clients:

```python
def add_device_session(self, device_id: str, session_id: str):
    """Map a session to the device executing it."""
    
    if device_id not in self.device_sessions:
        self.device_sessions[device_id] = set()
    
    self.device_sessions[device_id].add(session_id)
```

```python
def get_device_sessions(self, device_id: str) -> set[str]:
    """Get all sessions running on a device."""
    return self.device_sessions.get(device_id, set())
```

```python
def remove_device_sessions(self, device_id: str):
    """Remove all session mappings for a device."""
    self.device_sessions.pop(device_id, None)
```

### Individual Session Removal

```python
def remove_session(self, session_id: str):
    """Remove a specific session from all mappings."""
    
    # Remove from constellation mappings
    for constellation_id in self.constellation_sessions:
        self.constellation_sessions[constellation_id].discard(session_id)
    
    # Remove from device mappings
    for device_id in self.device_sessions:
        self.device_sessions[device_id].discard(session_id)
```

!!!warning
    Always clean up session mappings when tasks complete or are cancelled to prevent memory leaks.

## Device Information Management

### Storing Device Info

```python
def set_device_info(self, device_id: str, device_info: dict):
    """Store device information for a client."""
    self.device_info_cache[device_id] = device_info
```

### Retrieving Device Info

```python
def get_device_info(self, device_id: str) -> dict | None:
    """Get cached device information."""
    return self.device_info_cache.get(device_id)
```

### Device Info Structure

The cached device info typically contains:

```python
{
    "os": "Windows",
    "os_version": "10.0.22631",
    "processor": "Intel64 Family 6 Model 140 Stepping 1",
    "memory_total": 17014632448,
    "memory_available": 8459743232,
    "screen_resolution": "1920x1080",
    "applications": [...],
    "window_info": [...]
}
```

## Client Statistics

### Connection Count

```python
def get_online_count(self) -> int:
    """Get number of currently connected clients."""
    return len(self.online_clients)
```

### Type-Based Filtering

```python
def get_clients_by_type(self, client_type: ClientType) -> list[ClientInfo]:
    """Get all clients of a specific type."""
    return [
        info for info in self.clients.values()
        if info.client_type == client_type
    ]
```

### Platform-Based Filtering

```python
def get_clients_by_platform(self, platform: str) -> list[ClientInfo]:
    """Get all clients on a specific platform."""
    return [
        info for info in self.clients.values()
        if info.platform.lower() == platform.lower()
    ]
```

## Usage Patterns

### Registration Validation

```python
# Before allowing constellation registration
target_device_id = constellation_request.target_id

if not ws_manager.is_device_connected(target_device_id):
    raise ValueError(f"Target device {target_device_id} not connected")
```

### Task Routing

```python
# Get target WebSocket for task execution
target_ws = ws_manager.get_client(target_device_id)

if not target_ws:
    raise ValueError(f"Device {target_device_id} not found")
```

### Session Cleanup

```python
# When constellation disconnects
constellation_id = "constellation_abc"
session_ids = ws_manager.get_constellation_sessions(constellation_id)

for session_id in session_ids:
    # Cancel each session
    await session_manager.cancel_task(session_id, "constellation_disconnected")

# Clean up mappings
ws_manager.remove_constellation_sessions(constellation_id)
```

### Device Info Caching

```python
# Cache device info on first request
device_info = await device_client.get_device_info()
ws_manager.set_device_info(device_id, device_info)

# Later retrieval from cache
cached_info = ws_manager.get_device_info(device_id)
if cached_info:
    return cached_info
else:
    # Re-request if not cached
    ...
```

## Thread Safety

The WSManager is designed for use in async contexts. For concurrent access, consider:

```python
from asyncio import Lock

class WSManager:
    def __init__(self):
        self.clients = {}
        self.online_clients = set()
        self._lock = Lock()
    
    async def add_client(self, ...):
        async with self._lock:
            # Thread-safe client addition
            ...
```

!!!tip
    In practice, FastAPI's single-event-loop architecture typically doesn't require explicit locking for the WSManager.

## Best Practices

**Clean Up Comprehensively**

When removing a client, clean up all associated data:

```python
async def full_cleanup(client_id: str):
    # Cancel all sessions
    sessions = ws_manager.get_device_sessions(client_id)
    sessions.update(ws_manager.get_constellation_sessions(client_id))
    
    for sid in sessions:
        await session_manager.cancel_task(sid)
    
    # Remove session mappings
    ws_manager.remove_device_sessions(client_id)
    ws_manager.remove_constellation_sessions(client_id)
    
    # Remove client
    ws_manager.remove_client(client_id)
```

**Validate Before Dispatch**

Always check device availability:

```python
if not ws_manager.is_device_connected(target_id):
    return {"error": "Target device not available"}
```

**Cache Effectively**

Cache device info to reduce network overhead:

```python
# Check cache first
info = ws_manager.get_device_info(device_id)
if not info:
    # Request and cache
    info = await request_device_info(device_id)
    ws_manager.set_device_info(device_id, info)
```

**Monitor Connection Health**

Track connection statistics:

```python
total = ws_manager.get_online_count()
devices = len(ws_manager.get_clients_by_type(ClientType.DEVICE))
constellations = len(ws_manager.get_clients_by_type(ClientType.CONSTELLATION))

logger.info(f"Online: {total} ({devices} devices, {constellations} constellations)")
```

## Integration Points

### WebSocket Handler

Uses WSManager for client lookup and session tracking:

```python
# Registration
ws_manager.add_client(client_id, platform, websocket, client_type, metadata)

# Task routing
target_ws = ws_manager.get_client(target_device_id)

# Disconnection
ws_manager.remove_client(client_id)
```

### Session Manager

Coordinates with WSManager for cleanup:

```python
# Get affected sessions
sessions = ws_manager.get_device_sessions(device_id)

# Cancel each session
for sid in sessions:
    await session_manager.cancel_task(sid)
```

### API Router

Queries WSManager for client information:

```python
@router.get("/api/clients")
async def get_clients():
    clients = ws_manager.get_all_clients()
    return [
        {
            "id": c.client_id,
            "type": c.client_type.value,
            "platform": c.platform,
            "connected_at": c.connect_time
        }
        for c in clients
    ]
```

## API Reference

```python
from ufo.server.services.ws_manager import WSManager

# Initialize
ws_manager = WSManager()

# Client management
ws_manager.add_client(client_id, platform, websocket, client_type, metadata)
client_info = ws_manager.get_client_info(client_id)
ws = ws_manager.get_client(client_id)
ws_manager.remove_client(client_id)

# Connection checking
is_connected = ws_manager.is_device_connected(device_id)
is_online = ws_manager.is_online(client_id)

# Session mapping
ws_manager.add_constellation_session(constellation_id, session_id)
ws_manager.add_device_session(device_id, session_id)
sessions = ws_manager.get_constellation_sessions(constellation_id)
sessions = ws_manager.get_device_sessions(device_id)
ws_manager.remove_session(session_id)

# Device info
ws_manager.set_device_info(device_id, device_info)
info = ws_manager.get_device_info(device_id)

# Statistics
count = ws_manager.get_online_count()
clients = ws_manager.get_all_clients()
devices = ws_manager.get_clients_by_type(ClientType.DEVICE)
```

For more information:

- [Overview](./overview.md) - Server architecture
- [WebSocket Handler](./websocket_handler.md) - AIP protocol handling
- [Session Manager](./session_manager.md) - Session lifecycle
