# Quick Start

Get your device connected to the UFO² Agent Server in minutes.

## Prerequisites

- Python 3.10 or higher
- UFO² installed with dependencies
- Access to a running [Agent Server](../server/quick_start.md)

!!!tip "Server First"
    Make sure the Agent Server is running before connecting clients. See the [Server Quick Start Guide](../server/quick_start.md).

## Starting a Device Client

### Basic Connection

Connect to a local server (default: `ws://localhost:5000/ws`):

```bash
python -m ufo.client.client --ws --client-id my_device
```

### Connect to Remote Server

Connect to a server on a different machine:

```bash
python -m ufo.client.client \
  --ws \
  --ws-server ws://192.168.1.100:8000/ws \
  --client-id device_windows_001
```

### Specify Platform

Override platform auto-detection:

```bash
python -m ufo.client.client \
  --ws \
  --ws-server ws://127.0.0.1:8000/ws \
  --client-id my_linux_device \
  --platform linux
```

### All Options Example

```bash
python -m ufo.client.client \
  --ws \
  --ws-server ws://192.168.1.100:8000/ws \
  --client-id device_windows_prod_01 \
  --platform windows \
  --max-retries 10 \
  --log-level INFO
```

## Connection Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--ws` | ✅ Yes | - | Enable WebSocket mode |
| `--ws-server` | No | `ws://localhost:5000/ws` | Server WebSocket URL |
| `--client-id` | No | `client_001` | Unique device identifier |
| `--platform` | No | Auto-detect | Platform: `windows` or `linux` |
| `--max-retries` | No | 5 | Connection retry limit |
| `--log-level` | No | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

!!!warning "Unique Client IDs"
    Each device must have a unique `--client-id`. Duplicate IDs will cause connection conflicts.

## Successful Connection

When connected successfully, you'll see:

```
INFO - Platform detected/specified: windows
INFO - UFO Client initialized for platform: windows
INFO - [WS] Connecting to ws://127.0.0.1:8000/ws (attempt 1/5)
INFO - [WS] [AIP] Collected device info: platform=windows, cpu=8, memory=16.0GB
INFO - [WS] [AIP] Attempting to register as device_windows_001
INFO - [WS] [AIP] ✅ Successfully registered as device_windows_001
```

On the server side, you'll see:

```
INFO - [WS] ✅ Registered device client: device_windows_001
```

## Verify Connection

### Check Server API

From the server machine or any network-accessible machine:

```bash
curl http://localhost:8000/api/clients
```

You should see your device in the response:

```json
{
  "clients": [
    {
      "client_id": "device_windows_001",
      "type": "device",
      "platform": "windows",
      "connected_at": 1730736000.0,
      "uptime_seconds": 45
    }
  ],
  "total": 1
}
```

### Monitor Heartbeats

The client sends heartbeat messages every 120 seconds by default. You'll see:

```
DEBUG - [WS] [AIP] Heartbeat sent
```

## Running Your First Task

Once connected, dispatch a task from the server using the HTTP API:

```bash
curl -X POST http://localhost:8000/api/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device_windows_001",
    "task": "Open Notepad and type Hello from UFO"
  }'
```

Server response:

```json
{
  "status": "success",
  "session_id": "session_20251104_143022_abc123",
  "message": "Task dispatched to device_windows_001"
}
```

On the client, you'll see:

```
INFO - [WS] Starting task: Open Notepad and type Hello from UFO
INFO - [WS] [AIP] Sent task request with platform: windows
INFO - Executing 3 actions in total
INFO - [WS] [AIP] Sent client result for prev_response_id: resp_abc123
INFO - [WS] Task session_20251104_143022_abc123 completed
```

## Common Issues

### Connection Refused

**Symptom:**

```
ERROR - [WS] Unexpected error: [Errno 10061] Connect call failed
ERROR - [WS] Max retries reached. Exiting.
```

**Solutions:**

1. Verify server is running: `curl http://localhost:8000/api/health`
2. Check server URL and port match
3. Ensure firewall allows connections
4. If server uses `--local` flag, connect from localhost only

### Registration Failed

**Symptom:**

```
ERROR - [WS] [AIP] ❌ Failed to register as device_windows_001
RuntimeError: Registration failed for device_windows_001
```

**Solutions:**

1. Check for duplicate client ID
2. Verify server is accepting connections
3. Check server logs for error details
4. Ensure client has network access to server

### Platform Detection Issues

**Symptom:**

```
WARNING - Platform not detected correctly
```

**Solution:**

Explicitly set platform:

```bash
python -m ufo.client.client \
  --ws \
  --ws-server ws://127.0.0.1:8000/ws \
  --client-id my_device \
  --platform windows
```

### Heartbeat Timeout

**Symptom:**

```
ERROR - [WS] Connection closed: ConnectionClosedError
```

**Solutions:**

1. Check network stability
2. Verify server is still running
3. Check for network proxies blocking WebSocket
4. Increase `--max-retries` for unreliable networks

## Multiple Devices

Connect multiple devices to the same server:

**Device 1 (Windows):**

```bash
python -m ufo.client.client \
  --ws \
  --ws-server ws://192.168.1.100:8000/ws \
  --client-id device_windows_001
```

**Device 2 (Linux):**

```bash
python -m ufo.client.client \
  --ws \
  --ws-server ws://192.168.1.100:8000/ws \
  --client-id device_linux_001 \
  --platform linux
```

**Device 3 (Windows Laptop):**

```bash
python -m ufo.client.client \
  --ws \
  --ws-server ws://192.168.1.100:8000/ws \
  --client-id device_windows_laptop_002
```

Verify all connected:

```bash
curl http://192.168.1.100:8000/api/clients
```

## Running as Background Service

### Linux (systemd)

Create `/etc/systemd/system/ufo-client.service`:

```ini
[Unit]
Description=UFO Device Client
After=network.target

[Service]
Type=simple
User=ufouser
WorkingDirectory=/home/ufouser/UFO2
ExecStart=/usr/bin/python3 -m ufo.client.client \
  --ws \
  --ws-server ws://192.168.1.100:8000/ws \
  --client-id device_linux_prod_01 \
  --platform linux
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ufo-client
sudo systemctl start ufo-client
sudo systemctl status ufo-client
```

### Windows (NSSM)

1. Download [NSSM](https://nssm.cc/)
2. Install service:

```powershell
nssm install UFOClient "C:\Python310\python.exe" `
  "-m" "ufo.client.client" `
  "--ws" `
  "--ws-server" "ws://192.168.1.100:8000/ws" `
  "--client-id" "device_windows_prod_01"
```

3. Start service:

```powershell
nssm start UFOClient
```

### PM2 (Cross-platform)

Install PM2:

```bash
npm install -g pm2
```

Start client:

```bash
pm2 start "python -m ufo.client.client --ws --ws-server ws://192.168.1.100:8000/ws --client-id device_001" --name ufo-client
pm2 save
pm2 startup
```

## Production Deployment

**Use Descriptive IDs:**

```bash
--client-id production_windows_server_datacenter_rack1_slot3
```

**Enable Structured Logging:**

```bash
--log-level INFO > /var/log/ufo-client.log 2>&1
```

**Configure Automatic Restart:**

Use systemd, PM2, or NSSM with restart policies.

**Monitor Connection Health:**

Set up alerting for connection failures and registration errors.

**Use Secure WebSocket:**

For production, use WSS (WebSocket Secure):

```bash
--ws-server wss://ufo-server.example.com/ws
```

!!!danger "Security"
    Never expose client devices to the internet without proper security measures (WSS, authentication, firewall rules).

## Next Steps

Now that your client is connected:

- [Understand registration flow](../server/quick_start.md#connecting-a-device-client)
- [Learn about device info](./device_info.md)
- [Explore WebSocket client](./websocket_client.md)
- [Configure MCP servers](./mcp_integration.md)
- [Read AIP protocol details](../aip/overview.md)

## Troubleshooting Commands

**Test server connectivity:**

```bash
curl http://localhost:8000/api/health
```

**Check connected clients:**

```bash
curl http://localhost:8000/api/clients | python -m json.tool
```

**Monitor client logs:**

```bash
# Increase verbosity
python -m ufo.client.client --ws --client-id my_device --log-level DEBUG
```

**Test WebSocket connection:**

```bash
# Install wscat
npm install -g wscat

# Test connection
wscat -c ws://localhost:8000/ws
```
