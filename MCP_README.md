# UFO2 MCP Server Guide

## Overview

The UFO2 project implements a comprehensive Model Context Protocol (MCP) server architecture that enables AI agents to interact with Microsoft Office applications and system operations through standardized interfaces. This guide provides complete instructions for running, configuring, and managing the MCP servers.

## Architecture

The UFO2 MCP implementation consists of **6 specialized servers**:

- **Core MCP Server** (port 8000) - Core UFO operations and coordination
- **PowerPoint MCP Server** (port 8001) - Microsoft PowerPoint automation
- **Word MCP Server** (port 8002) - Microsoft Word document manipulation  
- **Excel MCP Server** (port 8003) - Microsoft Excel spreadsheet operations
- **Web MCP Server** (port 8004) - Web browser automation
- **Shell MCP Server** (port 8005) - Shell command execution and system operations

## Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Microsoft Office applications** (for Office servers)
3. **Required Python packages** installed:
   ```pwsh
   pip install -r requirements.txt
   ```

### Starting All Servers

The simplest way to start all MCP servers:

```pwsh
python launch_mcp_servers.py --start-all
```

This will start servers in the optimized order:
1. Core server (8000)
2. Shell server (8005) 
3. Web server (8004)
4. Excel server (8003)
5. Word server (8002)
6. PowerPoint server (8001)

### Starting Specific Servers

Start individual servers:
```pwsh
# Start a single server
python launch_mcp_servers.py --start powerpoint

# Start multiple specific servers
python launch_mcp_servers.py --servers shell web excel
```

### Checking Server Status

```pwsh
# Check all server status
python launch_mcp_servers.py --status

# Check server health
python launch_mcp_servers.py --health

# List available servers
python launch_mcp_servers.py --list
```

### Stopping Servers

```pwsh
# Stop all servers
python launch_mcp_servers.py --stop-all

# Stop specific server
python launch_mcp_servers.py --stop word
```

## Running UFO Tasks with MCP Servers

### Overview

UFO tasks can be executed using the MCP server architecture to handle core functions. This provides better isolation, modularity, and specialized handling for different application types.

### Method 1: Using UFO Web Client with MCP Integration

The `UFOWebClient` can be configured to route actions through the Core MCP Server:

```python
from ufo.cs.web_client import UFOWebClient

# Create client with MCP integration enabled
client = UFOWebClient(
    server_url="http://localhost:5000",
    use_core_mcp_server=True,        # Enable MCP integration
    core_mcp_host="localhost",       # MCP server host
    core_mcp_port=8000              # MCP server port
)

# Run a task
success = client.run_task("open PowerPoint and create a new presentation")
```

### Method 2: Command Line with MCP Integration

Run UFO tasks from the command line with MCP server support:

```pwsh
# Basic usage with MCP integration
python -m ufo.cs.web_client --use-core-mcp --request "open notepad and write hello world"

# Specify custom MCP server details
python -m ufo.cs.web_client --use-core-mcp --core-mcp-host localhost --core-mcp-port 8000 --request "create a PowerPoint presentation"

# Office application tasks
python -m ufo.cs.web_client --use-core-mcp --request "open Excel and create a budget spreadsheet"
```

### Method 3: Direct MCP Client Usage

Use the `CoreMCPClient` directly for more control:

```python
from ufo.mcp.core_mcp_client import CoreMCPClient
from ufo.contracts.contracts import CaptureDesktopScreenshotAction

# Initialize MCP client
mcp_client = CoreMCPClient(host="localhost", port=8000)

# Execute actions through MCP
action = CaptureDesktopScreenshotAction()
result = mcp_client.run_action(action)
```

### Method 4: Session-Based Execution with MCP

For complex multi-step tasks, use sessions with MCP integration:

```python
from uuid import uuid4
from ufo.cs.service_session import ServiceSession
from ufo.cs.computer import Computer

# Create session
session_id = str(uuid4())
session = ServiceSession(task=session_id, should_evaluate=False, id=session_id)
session.init(request="open PowerPoint and create a presentation with 3 slides")

# Computer with MCP support
computer = Computer('localhost', use_mcp_servers=True)

# Execute session with MCP integration
is_finished = session.is_finished()
while not is_finished:
    session.step_forward()
    actions = session.get_actions()
    
    action_results = {}
    for action in actions:
        # Computer automatically routes to appropriate MCP server
        result = computer.run_action(action)
        action_results[action.call_id] = result
    
    session.update_session_state_from_action_results(action_results)
    is_finished = session.is_finished()
```

### Prerequisites for Running UFO Tasks

1. **Start Required MCP Servers**:
   ```pwsh
   # Start all servers
   python launch_mcp_servers.py --start-all
   
   # Or start specific servers based on your task
   python launch_mcp_servers.py --servers core powerpoint  # For PowerPoint tasks
   python launch_mcp_servers.py --servers core word excel  # For Office document tasks
   ```

2. **Verify Server Status**:
   ```pwsh
   python launch_mcp_servers.py --status
   python launch_mcp_servers.py --health
   ```

3. **Check Server Endpoints**:
   ```pwsh
   # Test Core MCP Server
   Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
   
   # Test PowerPoint MCP Server (if needed)
   Invoke-RestMethod -Uri "http://localhost:8001/health" -Method Get
   ```

### Application-Specific MCP Routing

The system automatically routes actions to appropriate MCP servers based on the target application:

| Task Type | Target Application | MCP Server Used | Port |
|-----------|-------------------|-----------------|------|
| PowerPoint automation | POWERPNT.EXE | powerpoint | 8001 |
| Word document tasks | WINWORD.EXE | word | 8002 |
| Excel operations | EXCEL.EXE | excel | 8003 |
| Web browser tasks | msedge.exe, chrome.exe | web | 8004 |
| System/shell commands | cmd.exe, pwsh.exe | shell | 8005 |
| Core UFO operations | Any | core | 8000 |

### Error Handling and Fallback

The UFO system includes robust error handling:

1. **MCP Server Unavailable**: Falls back to direct computer execution
2. **Action Execution Failure**: Retries with alternative methods
3. **Network Issues**: Automatic retry with exponential backoff

```python
# Example with error handling
try:
    if self.use_core_mcp_server and self.mcp_client is not None:
        result = self.mcp_client.run_action(action)
    else:
        result = self.computer.run_action(action)
except Exception as e:
    logger.error(f"Failed to execute action {action.name}: {str(e)}")
    # Fallback to direct execution if MCP fails
    if self.use_core_mcp_server:
        result = self.computer.run_action(action)
```

### Benefits of Using MCP for UFO Tasks

1. **Modular Execution**: Each application type handled by specialized servers
2. **Better Isolation**: Application-specific operations isolated from core logic
3. **Improved Reliability**: Fallback mechanisms ensure task completion
4. **Enhanced Logging**: Detailed logs for each server component
5. **Scalability**: Servers can be distributed across multiple machines
6. **Development**: Easier debugging and testing of specific components

### Monitoring UFO Task Execution

Monitor your UFO tasks running through MCP servers:

```pwsh
# Watch Core MCP Server logs
Get-Content -Path "logs\mcp_core.log" -Tail 50 -Wait

# Monitor specific application server (e.g., PowerPoint)
Get-Content -Path "logs\mcp_powerpoint.log" -Tail 50 -Wait

# Check all MCP server logs
Get-ChildItem -Path "logs\mcp_*.log" | ForEach-Object {
    Write-Host "=== $($_.Name) ===" -ForegroundColor Yellow
    Get-Content $_.FullName -Tail 5
}
```

### Example UFO Tasks with MCP

Here are common UFO task examples using MCP servers:

```pwsh
# PowerPoint presentation task
python -m ufo.cs.web_client --use-core-mcp --request "create a PowerPoint presentation about AI trends with 5 slides"

# Excel data analysis task
python -m ufo.cs.web_client --use-core-mcp --request "open Excel, create a sales report with charts and formulas"

# Word document creation
python -m ufo.cs.web_client --use-core-mcp --request "create a Word document with company letterhead and write a business proposal"

# Multi-application workflow
python -m ufo.cs.web_client --use-core-mcp --request "extract data from Excel, create charts in PowerPoint, and summarize in Word"

# Web automation task
python -m ufo.cs.web_client --use-core-mcp --request "open a web browser, search for market data, and save results to Excel"
```

## Command Line Reference

### Basic Commands

| Command | Description |
|---------|-------------|
| `--start-all` | Start all servers in optimized order |
| `--stop-all` | Stop all running servers |
| `--status` | Show status of all servers |
| `--health` | Perform health checks on all servers |
| `--list` | List all available servers |

### Individual Server Management

| Command | Description |
|---------|-------------|
| `--start SERVER` | Start specific server (e.g., `--start word`) |
| `--stop SERVER` | Stop specific server (e.g., `--stop excel`) |
| `--servers SERVER1 SERVER2` | Start multiple servers |

### Advanced Options

| Command | Description |
|---------|-------------|
| `--interactive` | Launch interactive management console |
| `--daemon` | Run in daemon mode (keeps running after start-all) |
| `--development` | Enable development mode |
| `--verbose` | Enable verbose output |
| `--config-path PATH` | Use custom configuration file |

### Examples

```pwsh
# Start all servers and keep running
python launch_mcp_servers.py --start-all --daemon

# Start only Office applications
python launch_mcp_servers.py --servers powerpoint word excel

# Development mode with verbose output
python launch_mcp_servers.py --start-all --development --verbose

# Interactive management
python launch_mcp_servers.py --interactive
```

## Configuration Files

### Server Configuration (`ufo/config/mcp_servers.yaml`)

This file defines the endpoints and settings for each MCP server:

```yaml
mcp_servers:
  powerpoint:
    name: "PowerPoint MCP Server"
    endpoint: "http://localhost:8001"
    timeout: 30
    retry_count: 3
    health_check_endpoint: "/health"
    enabled: true
  # ... other servers
```

**Key Configuration Values:**

- **`endpoint`**: Server URL (http://localhost:PORT)
- **`timeout`**: Request timeout in seconds (default: 30)
- **`retry_count`**: Number of retry attempts (default: 3)
- **`health_check_endpoint`**: Health check URL path (default: "/health")
- **`enabled`**: Whether server is active (true/false)

### Launcher Configuration (`ufo/config/mcp_launcher.yaml`)

Controls server startup behavior and management:

```yaml
startup_config:
  startup_order:
    - "core"
    - "shell" 
    - "web"
    - "excel"
    - "word"
    - "powerpoint"
  startup_delay: 2        # Seconds between server starts
  startup_timeout: 30     # Max startup time per server
  health_check_retries: 5 # Health check attempts
```

**Server Configuration:**
```yaml
servers:
  powerpoint:
    name: "PowerPoint MCP Server"
    port: 8001
    module_path: "ufo.mcp.app_servers.powerpoint_mcp_server"
    log_file: "logs/mcp_powerpoint.log"
```

### Global Configuration

**Connection Settings:**
- `connection_timeout`: 10 seconds
- `read_timeout`: 30 seconds 
- `max_retries`: 3 attempts
- `retry_delay`: 1.0 seconds

**Logging Settings:**
- `log_requests`: true (log all requests)
- `log_responses`: true (log all responses)
- `log_level`: "INFO"
- `log_directory`: "logs/"

**Security Settings:**
- `verify_ssl`: true
- `allowed_hosts`: ["localhost", "127.0.0.1"]

## Application Mapping

The system automatically maps applications to their corresponding MCP servers:

| Application | Process Name | MCP Server |
|-------------|--------------|------------|
| PowerPoint | POWERPNT.EXE | powerpoint |
| Word | WINWORD.EXE | word |
| Excel | EXCEL.EXE | excel |
| Edge/Chrome/Firefox | msedge.exe, chrome.exe, firefox.exe | web |
| Command Prompt/PowerShell | cmd.exe, powershell.exe, pwsh.exe | shell |

## Server Details

### Core MCP Server (Port 8000)
- **Purpose**: Central coordination and core UFO operations
- **Module**: `ufo.mcp.core_mcp_server`
- **Log File**: `logs/mcp_core.log`

### PowerPoint MCP Server (Port 8001)
- **Purpose**: Microsoft PowerPoint automation and control
- **Capabilities**: Presentation creation, slide manipulation, content management
- **Module**: `ufo.mcp.app_servers.powerpoint_mcp_server`
- **Log File**: `logs/mcp_powerpoint.log`

### Word MCP Server (Port 8002)
- **Purpose**: Microsoft Word document manipulation
- **Capabilities**: Document creation, formatting, content editing
- **Module**: `ufo.mcp.app_servers.word_mcp_server`
- **Log File**: `logs/mcp_word.log`

### Excel MCP Server (Port 8003)
- **Purpose**: Microsoft Excel spreadsheet operations
- **Capabilities**: Workbook manipulation, data analysis, formula operations
- **Module**: `ufo.mcp.app_servers.excel_mcp_server`
- **Log File**: `logs/mcp_excel.log`

### Web MCP Server (Port 8004)
- **Purpose**: Web browser automation and interaction
- **Capabilities**: Page navigation, element interaction, data extraction
- **Module**: `ufo.mcp.app_servers.web_mcp_server`
- **Log File**: `logs/mcp_web.log`

### Shell MCP Server (Port 8005)
- **Purpose**: Shell command execution and system operations
- **Capabilities**: File operations, system commands, process management
- **Module**: `ufo.mcp.app_servers.shell_mcp_server`
- **Log File**: `logs/mcp_shell.log`

## Health Monitoring

### Automatic Health Checks

The system performs automatic health monitoring:

```yaml
health_monitoring:
  enabled: true
  check_interval: 60  # seconds
  failure_threshold: 3
  recovery_threshold: 2
  alert_on_failure: true
```

### Manual Health Checks

Check server health manually:

```pwsh
# Check all servers
python launch_mcp_servers.py --health

# In interactive mode
python launch_mcp_servers.py --interactive
# Then use 'health' command
```

Health checks use these endpoints:
- **Primary**: `/health` 
- **Fallback**: `/sse` (Server-Sent Events)

### Health Check Process

1. **HTTP GET** request to `{server_endpoint}/health`
2. **Timeout**: 5 seconds per check
3. **Retries**: Up to 5 attempts with 2-second intervals
4. **Success Criteria**: HTTP 200 response
5. **Failure Handling**: Log error and mark server as unhealthy

## Logging

### Log Files

All servers write logs to the `logs/` directory:

```
logs/
├── mcp_core.log        # Core server logs
├── mcp_powerpoint.log  # PowerPoint server logs
├── mcp_word.log        # Word server logs
├── mcp_excel.log       # Excel server logs
├── mcp_web.log         # Web server logs
└── mcp_shell.log       # Shell server logs
```

### Log Configuration

- **Level**: INFO (configurable)
- **Max Size**: 10MB per file
- **Backup Count**: 5 files retained
- **Console Output**: Enabled by default

### Viewing Logs

```pwsh
# View logs in PowerShell
Get-Content -Path "logs\mcp_powerpoint.log" -Tail 50 -Wait

# View all server logs
Get-ChildItem -Path "logs\mcp_*.log" | ForEach-Object { 
    Write-Host "=== $($_.Name) ===" -ForegroundColor Cyan
    Get-Content $_.FullName -Tail 10
}
```

## Troubleshooting

### Common Issues

**1. Port Already in Use**
```
Error: [Errno 10048] Only one usage of each socket address is normally permitted
```
**Solution**: Stop existing processes or change ports in configuration

**2. Module Import Errors**
```
ModuleNotFoundError: No module named 'ufo.mcp'
```
**Solution**: Ensure you're running from the UFO2 root directory

**3. Office Application Not Found**
```
Office application not available or not responding
```
**Solution**: Ensure Microsoft Office is installed and not already running

**4. Health Check Failures**
```
Health check failed for server: powerpoint
```
**Solution**: Check server logs, restart individual server

### Diagnostic Commands

```pwsh
# Check if ports are available
netstat -an | findstr ":800"

# Check running Python processes
Get-Process python | Select-Object Id, ProcessName, StartTime

# Test server endpoints directly
Invoke-RestMethod -Uri "http://localhost:8001/health" -Method Get

# View recent logs
Get-Content -Path "logs\mcp_powerpoint.log" -Tail 20
```

### Recovery Procedures

**Restart Single Server:**
```pwsh
python launch_mcp_servers.py --stop powerpoint
python launch_mcp_servers.py --start powerpoint
```

**Full System Restart:**
```pwsh
python launch_mcp_servers.py --stop-all
# Wait 5 seconds
python launch_mcp_servers.py --start-all
```

**Clean Restart (Development):**
```pwsh
python launch_mcp_servers.py --stop-all
Remove-Item -Path "logs\*" -Force
python launch_mcp_servers.py --start-all --development
```

## Development Mode

### Enabling Development Mode

```pwsh
python launch_mcp_servers.py --start-all --development --verbose
```

**Development Features:**
- **Verbose Logging**: Detailed debug information
- **Auto-reload**: Restart on code changes (if configured)
- **Mock Mode**: Use test responses instead of real applications
- **Debug Endpoints**: Additional debugging endpoints

### Development Configuration

```yaml
development:
  debug_mode: false
  verbose_logging: false
  auto_reload: false
  watch_directories:
    - "ufo/mcp"
    - "ufo/config"
  mock_mode: false
```

## API Endpoints

Each MCP server exposes standard endpoints:

### Standard Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/tools` | GET | List available tools |
| `/execute_tool` | POST | Execute specific tool |
| `/sse` | GET | Server-sent events (alternative health check) |

### Example API Usage

```pwsh
# List available tools
$response = Invoke-RestMethod -Uri "http://localhost:8001/tools" -Method Get
$response | ConvertTo-Json -Depth 3

# Execute a tool
$body = @{
    tool_name = "create_presentation"
    parameters = @{
        title = "Test Presentation"
        template = "blank"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/execute_tool" -Method Post -Body $body -ContentType "application/json"
```

## Interactive Mode

Launch the interactive management console:

```pwsh
python launch_mcp_servers.py --interactive
```

**Available Commands:**
- `start [server]` - Start server(s)
- `stop [server]` - Stop server(s)
- `status` - Show server status
- `health` - Check server health
- `logs [server]` - View server logs
- `restart [server]` - Restart server(s)
- `help` - Show available commands
- `quit` - Exit interactive mode

## Security Considerations

### Network Security
- Servers bind to `localhost` only
- No external network access by default
- SSL verification enabled

### Authentication
- No authentication required by default
- Can be enabled in configuration:
```yaml
security:
  require_authentication: true
  api_keys: ["your-api-key-here"]
```

### CORS Settings
```yaml
security:
  cors_enabled: false
  cors_origins: ["http://localhost:*"]
```

## Performance Optimization

### Resource Monitoring

The launcher monitors system resources:

```yaml
monitoring:
  monitor_memory: true
  memory_threshold: 500  # MB
  monitor_cpu: true
  cpu_threshold: 80      # percentage
```

### Connection Pooling

```yaml
global_config:
  connection_pool_size: 10
  keep_alive: true
```

### Startup Optimization

- **Startup Delay**: 2 seconds between servers (configurable)
- **Startup Order**: Optimized for dependencies
- **Health Check Retries**: 5 attempts to ensure reliability

## Testing

### Validation Scripts

```pwsh
# Test MCP configuration
powershell -ExecutionPolicy Bypass -File "tests\validate_mcp_config.ps1"

# Verify MCP system
python tests\verify_mcp_system.py

# Simple MCP test
python tests\test_mcp_simple.py
```

### Unit Tests

```pwsh
# Run all MCP tests
python -m pytest tests/test_mcp_*.py -v

# Test specific server
python -m pytest tests/test_powerpoint_mcp_server.py -v
```

## Support

### Log Analysis
- Check `logs/` directory for detailed server logs
- Use `--verbose` flag for detailed output
- Monitor health checks for early problem detection

### Configuration Validation
- Validate YAML syntax in configuration files
- Check port availability before starting servers
- Verify Python module paths are correct

### Community Resources
- See `CONTRIBUTING.md` for contribution guidelines
- Check `SECURITY.md` for security reporting
- Review existing issues and documentation

---

**Last Updated**: June 2025
**UFO2 Version**: Compatible with current MCP implementation
