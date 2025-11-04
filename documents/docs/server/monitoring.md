# Monitoring

Monitor the health and performance of your Agent Server deployment.

## Health Checks

### Health Endpoint

The `/api/health` endpoint provides server status:

```bash
curl http://localhost:8000/api/health
```

Response:

```json
{
  "status": "healthy",
  "uptime_seconds": 86400,
  "connected_clients": 5,
  "active_sessions": 2
}
```

### Automated Monitoring

**Kubernetes Liveness Probe**

```yaml
livenessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

**Prometheus Scraping**

```yaml
scrape_configs:
  - job_name: 'ufo-server'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/health'
```

**Uptime Monitoring Script**

```python
import requests
import time

def check_health():
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Healthy - {data['connected_clients']} clients, {data['active_sessions']} sessions")
            return True
        else:
            print(f"❌ Unhealthy - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Check every 30 seconds
while True:
    check_health()
    time.sleep(30)
```

## Client Monitoring

### Connected Clients

Query all connected clients:

```bash
curl http://localhost:8000/api/clients
```

Response:

```json
{
  "clients": [
    {
      "client_id": "device_windows_001",
      "type": "device",
      "platform": "windows",
      "connected_at": 1730736000.0,
      "uptime_seconds": 3600
    },
    {
      "client_id": "constellation_orchestrator",
      "type": "constellation",
      "platform": "linux",
      "connected_at": 1730737000.0,
      "uptime_seconds": 2600
    }
  ],
  "total": 2
}
```

### Client Statistics

**Count by Type**

```python
import requests

response = requests.get("http://localhost:8000/api/clients")
clients = response.json()["clients"]

devices = [c for c in clients if c["type"] == "device"]
constellations = [c for c in clients if c["type"] == "constellation"]

print(f"Devices: {len(devices)}")
print(f"Constellations: {len(constellations)}")
```

**Count by Platform**

```python
from collections import Counter

platforms = Counter(c["platform"] for c in clients)

print("Clients by platform:")
for platform, count in platforms.items():
    print(f"  {platform}: {count}")
```

**Average Uptime**

```python
if clients:
    avg_uptime = sum(c["uptime_seconds"] for c in clients) / len(clients)
    print(f"Average uptime: {avg_uptime / 60:.1f} minutes")
```

## Server Logs

### Log Levels

Configure logging verbosity:

```python
import logging

# Set log level
logging.basicConfig(level=logging.INFO)

# For debugging
logging.basicConfig(level=logging.DEBUG)
```

### Log Events

**Connection Events**

```
INFO: [WS] ✅ Registered device client: device_windows_001
INFO: [WS] 🌟 Constellation constellation_orchestrator requesting task on device_windows_001
INFO: [WS] 🔌 Removed client: device_windows_001
```

**Task Events**

```
INFO: [Session] Created session session_20251104_143022_abc123
INFO: [Session] Executing task in background: Open Notepad
INFO: [Session] Task completed: session_20251104_143022_abc123
```

**Error Events**

```
ERROR: [WS] ❌ Failed to send result for session_20251104_143022_abc123: Connection closed
WARNING: [Session] Task cancelled: session_20251104_143022_abc123 (reason: device_disconnected)
```

### Log Aggregation

**File Logging**

```bash
python -m ufo.server.app --port 8000 > server.log 2>&1
```

**Structured Logging**

```python
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": record.created,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module
        }
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.root.addHandler(handler)
```

**Log Rotation**

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "server.log",
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
logging.root.addHandler(handler)
```

## Performance Metrics

### Request Latency

Track API response times:

```python
import time
import requests

def measure_latency(endpoint):
    start = time.time()
    response = requests.get(f"http://localhost:8000{endpoint}")
    latency = (time.time() - start) * 1000  # ms
    
    print(f"{endpoint}: {latency:.2f} ms")
    return latency

# Measure endpoints
measure_latency("/api/health")
measure_latency("/api/clients")
```

### Task Throughput

Monitor task completion rate:

```python
from collections import deque
import time

class ThroughputMonitor:
    def __init__(self, window_seconds=60):
        self.window = window_seconds
        self.completions = deque()
    
    def record_completion(self):
        now = time.time()
        self.completions.append(now)
        
        # Remove old completions outside window
        cutoff = now - self.window
        while self.completions and self.completions[0] < cutoff:
            self.completions.popleft()
    
    def get_rate(self):
        """Tasks per minute."""
        return len(self.completions) * (60 / self.window)

monitor = ThroughputMonitor()

# Record each completion
monitor.record_completion()

# Get current rate
print(f"Throughput: {monitor.get_rate():.1f} tasks/min")
```

### Connection Stability

Track disconnection rate:

```python
class ConnectionMonitor:
    def __init__(self):
        self.total_connections = 0
        self.total_disconnections = 0
    
    def on_connect(self):
        self.total_connections += 1
    
    def on_disconnect(self):
        self.total_disconnections += 1
    
    def get_stability(self):
        if self.total_connections == 0:
            return 1.0
        return 1 - (self.total_disconnections / self.total_connections)

monitor = ConnectionMonitor()
print(f"Connection stability: {monitor.get_stability() * 100:.1f}%")
```

## Alerting

### Alert Conditions

**No Connected Devices**

```python
def check_devices():
    response = requests.get("http://localhost:8000/api/clients")
    clients = response.json()["clients"]
    devices = [c for c in clients if c["type"] == "device"]
    
    if not devices:
        send_alert("No devices connected!")
```

**High Error Rate**

```python
import re

def analyze_logs(log_file):
    error_count = 0
    total_count = 0
    
    with open(log_file) as f:
        for line in f:
            total_count += 1
            if "ERROR" in line or "WARNING" in line:
                error_count += 1
    
    error_rate = error_count / total_count if total_count > 0 else 0
    
    if error_rate > 0.1:  # 10% error rate
        send_alert(f"High error rate: {error_rate * 100:.1f}%")
```

**Slow Response Times**

```python
def check_latency():
    latency = measure_latency("/api/health")
    
    if latency > 1000:  # 1 second
        send_alert(f"Slow response: {latency:.0f} ms")
```

### Alert Delivery

**Email Alerts**

```python
import smtplib
from email.message import EmailMessage

def send_alert(message):
    msg = EmailMessage()
    msg['Subject'] = 'UFO Server Alert'
    msg['From'] = 'alerts@example.com'
    msg['To'] = 'admin@example.com'
    msg.set_content(message)
    
    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)
```

**Slack Alerts**

```python
import requests

def send_alert(message):
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    
    payload = {
        "text": f"🚨 UFO Server Alert: {message}"
    }
    
    requests.post(webhook_url, json=payload)
```

**PagerDuty Integration**

```python
import requests

def send_alert(message, severity="error"):
    api_key = "YOUR_PAGERDUTY_API_KEY"
    
    payload = {
        "routing_key": api_key,
        "event_action": "trigger",
        "payload": {
            "summary": message,
            "severity": severity,
            "source": "ufo-server"
        }
    }
    
    requests.post(
        "https://events.pagerduty.com/v2/enqueue",
        json=payload
    )
```

## Dashboard

### Simple Web Dashboard

```html
<!DOCTYPE html>
<html>
<head>
    <title>UFO Server Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric { padding: 10px; margin: 10px; border: 1px solid #ccc; }
        .healthy { background-color: #d4edda; }
        .warning { background-color: #fff3cd; }
    </style>
</head>
<body>
    <h1>UFO Server Dashboard</h1>
    
    <div id="health" class="metric">
        <h2>Health Status</h2>
        <p id="status">Loading...</p>
    </div>
    
    <div id="clients" class="metric">
        <h2>Connected Clients</h2>
        <ul id="client-list"></ul>
    </div>
    
    <script>
        async function updateDashboard() {
            // Health check
            const health = await fetch('/api/health').then(r => r.json());
            document.getElementById('status').textContent = 
                `Status: ${health.status} | Uptime: ${Math.floor(health.uptime_seconds / 60)} min | Clients: ${health.connected_clients}`;
            
            // Clients
            const clients = await fetch('/api/clients').then(r => r.json());
            const list = document.getElementById('client-list');
            list.innerHTML = clients.clients.map(c => 
                `<li>${c.client_id} (${c.type}, ${c.platform})</li>`
            ).join('');
        }
        
        // Update every 5 seconds
        setInterval(updateDashboard, 5000);
        updateDashboard();
    </script>
</body>
</html>
```

## Best Practices

**Regular Health Checks**

Poll `/api/health` every 30-60 seconds.

**Client Monitoring**

Track client connection/disconnection events to detect instability.

**Log Analysis**

Regularly analyze logs for errors and warnings.

**Performance Baselines**

Establish baseline metrics for latency and throughput to detect anomalies.

**Alerting Thresholds**

Set reasonable thresholds to avoid alert fatigue:
- No devices connected for > 5 minutes
- Error rate > 10%
- Response time > 2 seconds
- Session failure rate > 20%

**Retention Policies**

Rotate and archive logs regularly:
- Keep detailed logs for 7 days
- Keep summary logs for 30 days
- Archive monthly summaries

## Next Steps

- [Quick Start](./quick_start.md) - Get the server running
- [HTTP API](./api.md) - API endpoint reference
- [WebSocket Handler](./websocket_handler.md) - Connection management
- [Session Manager](./session_manager.md) - Task execution tracking
