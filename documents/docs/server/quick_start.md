# Quick Start

This guide will help you quickly set up and run the UFO Agent Server.

## Prerequisites

- Python 3.10 or higher
- UFO² installed and configured
- Network connectivity for WebSocket connections

## Starting the Server

### Basic Startup

Start the server with default settings (port 8000):

```bash
python -m ufo.server.app
```

The server will start and display:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Custom Port

Specify a custom port:

```bash
python -m ufo.server.app --port 5005
```

### Local Mode

Run in local mode (only accept connections from localhost):

```bash
python -m ufo.server.app --local
```

### All Options

```bash
python -m ufo.server.app --port 5005 --local
```

!!!tip
    Use `--local` mode during development to restrict connections to your machine only.

## Connecting a Device Client

Once the server is running, connect a device agent using the command line:

### Windows Device

```bash
python -m ufo.client.client --ws --ws-server ws://127.0.0.1:8000/ws --client-id my_windows_device
```

### Linux Device

```bash
python -m ufo.client.client --ws --ws-server ws://127.0.0.1:8000/ws --client-id my_linux_device --platform linux
```

### macOS Device

```bash
python -m ufo.client.client --ws --ws-server ws://127.0.0.1:8000/ws --client-id my_mac_device --platform darwin
```

!!!tip "Client Documentation"
    For detailed client setup and configuration, see the [Agent Client Quick Start Guide](../client/quick_start.md).

### Connection Parameters

| Parameter | Description | Example | Required |
|-----------|-------------|---------|----------|
| `--ws` | Enable WebSocket mode | (flag) | ✅ Yes |
| `--ws-server` | Server WebSocket URL | `ws://127.0.0.1:8000/ws` | ✅ Yes |
| `--client-id` | Unique device identifier | `device_windows_001` | ✅ Yes |
| `--platform` | Platform type | `windows`, `linux`, `darwin` | Optional (auto-detected) |

!!!success "Registration Success"
    When connected successfully, the server logs will show:
    ```
    INFO: [WS] ✅ Registered device client: my_windows_device
    ```

### How Client Registration Works

When a client connects, it follows this flow:

1. **WebSocket Connection**: Client establishes WebSocket connection to `/ws` endpoint
2. **Registration Message**: Client sends a `REGISTER` message with `client_id` and `platform`
3. **Server Validation**: Server validates the client ID is unique and platform is valid
4. **Confirmation**: Server sends `REGISTER_CONFIRM` message back to client
5. **Connection Established**: Client is now registered and can send/receive tasks

```
Client                          Server
  │                               │
  │  1. WebSocket Connect         │
  ├──────────────────────────────>│
  │                               │
  │  2. REGISTER Message          │
  │  {client_id, platform}        │
  ├──────────────────────────────>│
  │                               │
  │  3. Validation                │
  │     - Unique client_id        │
  │     - Valid platform          │
  │                               │
  │  4. REGISTER_CONFIRM          │
  │<──────────────────────────────┤
  │                               │
  │  ✅ Connection Established     │
```

!!!info "Platform Auto-Detection"
    If you don't specify `--platform`, the client will auto-detect the operating system. However, it's recommended to explicitly set it for clarity.

## Connecting a Constellation Client

Connect a constellation orchestrator to coordinate tasks:

```bash
python -m galaxy.constellation.constellation --ws --ws-server ws://127.0.0.1:8000/ws --target-id my_windows_device
```

### Constellation Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--ws` | Enable WebSocket mode | Required flag |
| `--ws-server` | Server WebSocket URL | `ws://127.0.0.1:8000/ws` |
| `--target-id` | Target device ID | `my_windows_device` |

!!!warning
    The target device must be connected before starting the constellation client.

## Verifying the Setup

### Check Connected Clients

Use the HTTP API to verify connections:

```bash
curl http://localhost:8000/api/clients
```

Expected response:

```json
{
  "clients": [
    {
      "client_id": "my_windows_device",
      "type": "device",
      "platform": "windows",
      "connected_at": 1730736000.0,
      "uptime_seconds": 120
    }
  ],
  "total": 1
}
```

### Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "uptime_seconds": 300,
  "connected_clients": 1,
  "active_sessions": 0
}
```

## Dispatching Your First Task

Use the HTTP API to dispatch a task:

```bash
curl -X POST http://localhost:8000/api/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "my_windows_device",
    "task": "Open Notepad and type Hello World"
  }'
```

Response:

```json
{
  "status": "success",
  "session_id": "session_20251104_143022_abc123",
  "message": "Task dispatched to my_windows_device"
}
```

### Check Task Result

Poll for the result:

```bash
curl http://localhost:8000/api/task_result/session_20251104_143022_abc123
```

While running:

```json
{
  "status": "pending",
  "message": "Task is still running"
}
```

When completed:

```json
{
  "status": "completed",
  "result": {
    "action_taken": "Opened Notepad and typed 'Hello World'",
    "screenshot": "base64_encoded_image..."
  },
  "session_id": "session_20251104_143022_abc123"
}
```

## Common Issues

### Port Already in Use

If you see `Address already in use`, choose a different port:

```bash
python -m ufo.server.app --port 5005
```

### Connection Refused

Ensure the server is running and the WebSocket URL is correct:

- Check server logs for startup confirmation
- Verify the port matches in both server and client commands
- If using `--local`, ensure you're connecting from localhost

### Device Not Connected

If dispatching fails with "Device not connected":

1. Verify the device client is running
2. Check the `client_id` matches exactly
3. Use `/api/clients` to see connected devices

### Firewall Issues

If clients can't connect from other machines:

- Ensure the server is not in `--local` mode
- Check firewall rules allow incoming connections on the server port
- Verify network connectivity between machines

## Next Steps

Now that you have the server running:

- [Learn about the architecture](./overview.md)
- [Explore the HTTP API](./api.md)
- [Monitor connections](./monitoring.md)
- [Configure advanced settings](../configurations/overview.md)

## Production Deployment

For production deployments, consider:

**Use a Process Manager**

```bash
# Using systemd (Linux)
sudo systemctl start ufo-server

# Using PM2 (Node.js process manager)
pm2 start "python -m ufo.server.app --port 8000" --name ufo-server
```

**Enable Logging**

```bash
python -m ufo.server.app --port 8000 > server.log 2>&1
```

**Run Behind a Reverse Proxy**

Use nginx or Apache to handle SSL/TLS termination and load balancing.

**Monitor Health**

Set up monitoring to poll `/api/health` regularly.

!!!danger
    Never expose the server directly to the internet without proper security measures (authentication, SSL/TLS, rate limiting).
