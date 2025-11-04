# HTTP API Reference

The Agent Server provides a RESTful HTTP API for task dispatch, client monitoring, and health checks. All endpoints are prefixed with `/api`.

## Overview

The HTTP API provides:

- Task dispatch from external systems
- Client connection monitoring
- Task result retrieval
- Health checks for monitoring

## Endpoints

### POST /api/dispatch

Dispatch a task to a connected device.

**Request Body**

```json
{
  "device_id": "device_windows_001",
  "task": "Open Chrome and navigate to github.com",
  "mode": "normal",
  "plan": []
}
```

**Request Schema**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `device_id` | string | Yes | Target device identifier |
| `task` | string | Yes | Natural language task description |
| `mode` | string | No | Execution mode: "normal" or "follower" (default: "normal") |
| `plan` | list | No | Predefined action plan (default: []) |

**Success Response (200)**

```json
{
  "status": "success",
  "session_id": "session_20240115_143022_abc123",
  "message": "Task dispatched to device_windows_001"
}
```

**Error Responses**

**Device Not Connected (400)**

```json
{
  "status": "error",
  "message": "Device device_windows_001 is not connected"
}
```

**Invalid Request (422)**

```json
{
  "detail": [
    {
      "loc": ["body", "device_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Implementation**

```python
@router.post("/api/dispatch")
async def dispatch_task(request: DispatchRequest):
    """Dispatch a task to a device."""
    
    # Validate device connection
    if not ws_manager.is_device_connected(request.device_id):
        raise HTTPException(
            status_code=400,
            detail=f"Device {request.device_id} is not connected"
        )
    
    # Generate session ID
    session_id = generate_session_id()
    
    # Get device WebSocket
    device_ws = ws_manager.get_client(request.device_id)
    
    # Get platform
    platform = ws_manager.get_client_info(request.device_id).platform
    
    # Execute task asynchronously
    await session_manager.execute_task_async(
        session_id=session_id,
        task_name=request.task,
        request=request.dict(),
        websocket=device_ws,
        platform_override=platform
    )
    
    return {
        "status": "success",
        "session_id": session_id,
        "message": f"Task dispatched to {request.device_id}"
    }
```

!!!tip
    Use the returned `session_id` to retrieve task results via `/api/task_result/{session_id}`.

### GET /api/clients

Get information about all connected clients.

**Response (200)**

```json
{
  "clients": [
    {
      "client_id": "device_windows_001",
      "type": "device",
      "platform": "windows",
      "connected_at": 1705324822.123,
      "uptime_seconds": 3600
    },
    {
      "client_id": "constellation_coordinator_001",
      "type": "constellation",
      "platform": "linux",
      "connected_at": 1705325422.456,
      "uptime_seconds": 3000
    }
  ],
  "total": 2
}
```

**Response Schema**

| Field | Type | Description |
|-------|------|-------------|
| `clients` | array | List of connected clients |
| `clients[].client_id` | string | Unique client identifier |
| `clients[].type` | string | Client type: "device" or "constellation" |
| `clients[].platform` | string | OS platform: "windows", "linux", "darwin" |
| `clients[].connected_at` | float | Unix timestamp of connection time |
| `clients[].uptime_seconds` | float | Time since connection in seconds |
| `total` | integer | Total number of connected clients |

**Implementation**

```python
@router.get("/api/clients")
async def get_clients():
    """Get information about all connected clients."""
    
    clients_info = ws_manager.get_all_clients()
    current_time = time.time()
    
    clients = [
        {
            "client_id": info.client_id,
            "type": info.client_type.value,
            "platform": info.platform,
            "connected_at": info.connect_time,
            "uptime_seconds": current_time - info.connect_time
        }
        for info in clients_info
    ]
    
    return {
        "clients": clients,
        "total": len(clients)
    }
```

!!!info
    This endpoint is useful for monitoring which devices are available for task dispatch.

### GET /api/task_result/{task_name}

Retrieve the result of a completed task.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_name` | string | Session ID or task identifier |

**Success Response (200)**

```json
{
  "status": "completed",
  "result": {
    "action_taken": "Opened Chrome and navigated to github.com",
    "screenshot": "base64_encoded_image_data",
    "control_selected": {
      "label": "Address bar",
      "control_text": "github.com"
    }
  },
  "session_id": "session_20240115_143022_abc123"
}
```

**Pending Response (202)**

```json
{
  "status": "pending",
  "message": "Task is still running"
}
```

**Not Found Response (404)**

```json
{
  "detail": "Task session_invalid not found"
}
```

**Implementation**

```python
@router.get("/api/task_result/{task_name}")
async def get_task_result(task_name: str):
    """Get the result of a task."""
    
    # Try to get session
    session = session_manager.get_session(task_name)
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_name} not found"
        )
    
    # Check if task is complete
    if session.is_running():
        return {
            "status": "pending",
            "message": "Task is still running"
        }
    
    # Get result
    result = session.get_result()
    
    return {
        "status": "completed",
        "result": result,
        "session_id": task_name
    }
```

!!!warning
    Results may be cleared after a certain time period. Poll this endpoint periodically if needed.

### GET /api/health

Health check endpoint for monitoring and load balancers.

**Response (200)**

```json
{
  "status": "healthy",
  "uptime_seconds": 86400,
  "connected_clients": 5,
  "active_sessions": 2
}
```

**Implementation**

```python
@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    
    return {
        "status": "healthy",
        "uptime_seconds": time.time() - server_start_time,
        "connected_clients": ws_manager.get_online_count(),
        "active_sessions": session_manager.get_active_session_count()
    }
```

!!!success
    This endpoint is useful for Kubernetes liveness/readiness probes and monitoring systems.

## Usage Examples

### Python

**Dispatch Task**

```python
import requests

response = requests.post(
    "http://localhost:8000/api/dispatch",
    json={
        "device_id": "device_windows_001",
        "task": "Open Notepad and type Hello World"
    }
)

result = response.json()
session_id = result["session_id"]
```

**Get Task Result**

```python
import time

while True:
    response = requests.get(
        f"http://localhost:8000/api/task_result/{session_id}"
    )
    
    result = response.json()
    
    if result["status"] == "completed":
        print("Task completed:", result["result"])
        break
    
    time.sleep(1)
```

**List Connected Clients**

```python
response = requests.get("http://localhost:8000/api/clients")
clients = response.json()["clients"]

for client in clients:
    print(f"{client['client_id']} ({client['platform']})")
```

### cURL

**Dispatch Task**

```bash
curl -X POST http://localhost:8000/api/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device_windows_001",
    "task": "Open Calculator"
  }'
```

**Get Clients**

```bash
curl http://localhost:8000/api/clients
```

**Get Task Result**

```bash
curl http://localhost:8000/api/task_result/session_20240115_143022_abc123
```

**Health Check**

```bash
curl http://localhost:8000/api/health
```

### JavaScript (fetch)

```javascript
// Dispatch task
const response = await fetch('http://localhost:8000/api/dispatch', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    device_id: 'device_windows_001',
    task: 'Open Chrome'
  })
});

const {session_id} = await response.json();

// Poll for result
while (true) {
  const result_response = await fetch(
    `http://localhost:8000/api/task_result/${session_id}`
  );
  
  const result = await result_response.json();
  
  if (result.status === 'completed') {
    console.log('Task completed:', result.result);
    break;
  }
  
  await new Promise(resolve => setTimeout(resolve, 1000));
}
```

## Error Handling

**Standard Error Response**

All endpoints return errors in a consistent format:

```json
{
  "detail": "Error message description"
}
```

**Common Status Codes**

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Request succeeded |
| 202 | Accepted | Task pending (for /api/task_result) |
| 400 | Bad Request | Device not connected, invalid parameters |
| 404 | Not Found | Task/resource not found |
| 422 | Unprocessable Entity | Invalid request body schema |
| 500 | Internal Server Error | Unexpected server error |

## Best Practices

**Check Device Availability**

Always verify device connection before dispatching:

```python
# Get available devices
clients_response = requests.get("http://localhost:8000/api/clients")
available_devices = [
    c["client_id"] for c in clients_response.json()["clients"]
    if c["type"] == "device"
]

if target_device in available_devices:
    # Dispatch task
    ...
```

**Handle Async Results**

Implement proper polling with backoff:

```python
import time

max_wait = 300  # 5 minutes
poll_interval = 2
waited = 0

while waited < max_wait:
    response = requests.get(f"/api/task_result/{session_id}")
    result = response.json()
    
    if result["status"] == "completed":
        return result["result"]
    
    time.sleep(poll_interval)
    waited += poll_interval

raise TimeoutError("Task did not complete in time")
```

**Use Health Checks**

Implement health monitoring:

```python
def is_server_healthy():
    try:
        response = requests.get(
            "http://localhost:8000/api/health",
            timeout=5
        )
        return response.status_code == 200
    except:
        return False
```

**Handle Errors Gracefully**

```python
try:
    response = requests.post("/api/dispatch", json=request_data)
    response.raise_for_status()
    return response.json()
except requests.HTTPError as e:
    if e.response.status_code == 400:
        print("Device not available")
    elif e.response.status_code == 422:
        print("Invalid request:", e.response.json())
    else:
        print("Server error")
```

## Integration Points

### WebSocket Handler

API endpoints coordinate with WebSocket handler for task dispatch:

```python
# API dispatches via WebSocket handler
device_ws = ws_manager.get_client(device_id)
await session_manager.execute_task_async(
    session_id=session_id,
    task_name=task,
    request=request_data,
    websocket=device_ws,
    platform_override=platform
)
```

### Session Manager

API retrieves task results from session manager:

```python
# Get session result
session = session_manager.get_session(session_id)
result = session.get_result()
```

### WebSocket Manager

API queries client status from WebSocket manager:

```python
# Check device availability
is_connected = ws_manager.is_device_connected(device_id)

# Get all clients
clients = ws_manager.get_all_clients()
```

## API Reference

```python
from ufo.server.services.api import router

# Include in FastAPI app
app.include_router(router)
```

**Request Models**

```python
from pydantic import BaseModel

class DispatchRequest(BaseModel):
    device_id: str
    task: str
    mode: str = "normal"
    plan: list = []
```

For more information:

- [Overview](./overview.md) - Server architecture
- [WebSocket Handler](./websocket_handler.md) - WebSocket communication
- [Session Manager](./session_manager.md) - Session lifecycle
- [WebSocket Manager](./websocket_manager.md) - Connection management
