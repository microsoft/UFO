# BashExecutor Server

## Overview

**BashExecutor** provides Linux shell command execution with output capture and system information retrieval via HTTP MCP server.

**Server Type:** Action  
**Deployment:** HTTP (remote Linux server)  
**Default Port:** 8010  
**LLM-Selectable:** ✅ Yes

## Server Information

| Property | Value |
|----------|-------|
| **Namespace** | `BashExecutor` |
| **Server Name** | `Linux Bash MCP Server` |
| **Platform** | Linux |
| **Tool Type** | `action` |
| **Deployment** | HTTP server (stateless) |

## Tools

### execute_command

Execute a shell command on Linux and return stdout/stderr with exit code.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `command` | `str` | ✅ Yes | - | Shell command to execute (valid bash/sh command) |
| `timeout` | `int` | No | `30` | Maximum execution time in seconds (default: 30, max: any) |
| `cwd` | `str` | No | `None` | Working directory path (absolute path recommended) |

#### Returns

**Type**: `Dict[str, Any]`

```python
{
    "success": bool,        # True if exit code == 0
    "exit_code": int,       # Process exit code
    "stdout": str,          # Standard output
    "stderr": str,          # Standard error output
    # OR
    "error": str           # Error message if execution failed
}
```

#### Example

```python
# Simple command
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::execute_command",
        tool_name="execute_command",
        parameters={
            "command": "ls -la /home",
            "timeout": 30
        }
    )
])

# Output:
# {
#     "success": True,
#     "exit_code": 0,
#     "stdout": "total 12\ndrwxr-xr-x  3 root root 4096 ...",
#     "stderr": ""
# }

# Command with specific working directory
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::execute_command",
        tool_name="execute_command",
        parameters={
            "command": "python script.py --arg value",
            "timeout": 60,
            "cwd": "/home/user/project"
        }
    )
])

# Check system info
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::execute_command",
        tool_name="execute_command",
        parameters={"command": "cat /etc/os-release"}
    )
])
```

#### Security Blocklist

Dangerous commands are automatically blocked:

| Blocked Command | Reason |
|-----------------|--------|
| `rm -rf /` | System destruction |
| `:(){ :\|:& };:` | Fork bomb |
| `mkfs` | Filesystem formatting |
| `dd if=/dev/zero` | Disk overwrite |
| `shutdown` | System shutdown |
| `reboot` | System reboot |

**Returns**: `{"success": False, "error": "Blocked dangerous command."}`

#### Timeout Handling

If command exceeds timeout:

```python
{
    "success": False,
    "error": "Timeout after {timeout}s."
}
```

#### Error Handling

If execution fails:

```python
{
    "success": False,
    "error": "{exception_details}"
}
```

---

### get_system_info

Get basic Linux system information (uname, uptime, memory, disk).

#### Parameters

None

#### Returns

**Type**: `Dict[str, Any]`

```python
{
    "uname": str,      # System and kernel info (uname -a)
    "uptime": str,     # System uptime and load averages
    "memory": str,     # Memory usage statistics (free -h)
    "disk": str        # Disk space usage (df -h)
}
```

#### Example

```python
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::get_system_info",
        tool_name="get_system_info",
        parameters={}
    )
])

# Output:
# {
#     "uname": "Linux server 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux",
#     "uptime": " 10:30:45 up 5 days,  2:15,  3 users,  load average: 0.52, 0.58, 0.59",
#     "memory": "              total        used        free      shared  buff/cache   available\nMem:           15Gi       4.2Gi       7.8Gi       123Mi       3.0Gi        10Gi\nSwap:         2.0Gi          0B       2.0Gi",
#     "disk": "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       100G   45G   50G  48% /"
# }
```

#### Error Handling

If command fails, value is error message:

```python
{
    "uname": "Linux ubuntu ...",
    "uptime": "Error: No such file or directory",
    "memory": "...",
    "disk": "..."
}
```

## Configuration

### Client Configuration

```yaml
# Windows client connecting to Linux server
HostAgent:
  default:
    action:
      - namespace: BashExecutor
        type: http
        host: "192.168.1.100"  # Linux server IP
        port: 8010
        path: "/mcp"

# Linux client (local)
HostAgent:
  default:
    action:
      - namespace: BashExecutor
        type: http
        host: "localhost"
        port: 8010
        path: "/mcp"
```

## Deployment

### Starting the Server

```bash
# Start Bash MCP server on Linux
python -m ufo.client.mcp.http_servers.linux_mcp_server --host 0.0.0.0 --port 8010

# Output:
# ==================================================
# UFO Linux Bash MCP Server
# Linux command execution via Model Context Protocol
# Running on 0.0.0.0:8010
# ==================================================
```

### Command-Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--host` | `localhost` | Host to bind server to |
| `--port` | `8010` | Port to run server on |

### Systemd Service (Optional)

```ini
# /etc/systemd/system/ufo-bash-mcp.service
[Unit]
Description=UFO Bash MCP Server
After=network.target

[Service]
Type=simple
User=ufo
WorkingDirectory=/home/ufo/UFO2
ExecStart=/usr/bin/python3 -m ufo.client.mcp.http_servers.linux_mcp_server --host 0.0.0.0 --port 8010
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ufo-bash-mcp
sudo systemctl start ufo-bash-mcp
sudo systemctl status ufo-bash-mcp
```

## Best Practices

### 1. Use Absolute Paths

```python
# ✅ Good: Absolute paths
await computer.run_actions([
    MCPToolCall(
        tool_key="action::execute_command",
        parameters={
            "command": "ls /home/user/project",
            "cwd": "/home/user"
        }
    )
])

# ❌ Bad: Relative paths may fail
await computer.run_actions([
    MCPToolCall(
        tool_key="action::execute_command",
        parameters={
            "command": "ls project",  # May fail if cwd unclear
            "cwd": None
        }
    )
])
```

### 2. Set Appropriate Timeouts

```python
# Quick commands: short timeout
await computer.run_actions([
    MCPToolCall(
        tool_key="action::execute_command",
        parameters={"command": "ls -la", "timeout": 5}
    )
])

# Long-running: increase timeout
await computer.run_actions([
    MCPToolCall(
        tool_key="action::execute_command",
        parameters={"command": "python train_model.py", "timeout": 3600}  # 1 hour
    )
])
```

### 3. Check Exit Codes

```python
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::execute_command",
        parameters={"command": "grep 'pattern' file.txt"}
    )
])

if result[0].data["success"]:
    logger.info(f"Found: {result[0].data['stdout']}")
else:
    logger.warning(f"Not found (exit code {result[0].data['exit_code']})")
```

### 4. Validate Commands

```python
def safe_execute(command: str, allowed_commands: List[str]):
    """Whitelist-based command validation"""
    cmd_base = command.split()[0]
    
    if cmd_base not in allowed_commands:
        raise ValueError(f"Command not allowed: {cmd_base}")
    
    return MCPToolCall(
        tool_key="action::execute_command",
        tool_name="execute_command",
        parameters={"command": command}
    )

# Usage
allowed = ["ls", "cat", "grep", "find", "python3"]
await computer.run_actions([safe_execute("ls -la /home", allowed)])
```

## Use Cases

### 1. System Monitoring

```python
# Get system info
info = await computer.run_actions([
    MCPToolCall(tool_key="action::get_system_info", parameters={})
])

# Parse disk usage
disk_info = info[0].data["disk"]
if "98%" in disk_info:
    logger.warning("Disk almost full!")
```

### 2. Log Analysis

```python
# Search logs
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::execute_command",
        parameters={
            "command": "grep ERROR /var/log/application.log | tail -20",
            "timeout": 10
        }
    )
])

errors = result[0].data["stdout"]
```

### 3. File Operations

```python
# Create directory
await computer.run_actions([
    MCPToolCall(
        tool_key="action::execute_command",
        parameters={"command": "mkdir -p /tmp/workspace/data"}
    )
])

# Copy files
await computer.run_actions([
    MCPToolCall(
        tool_key="action::execute_command",
        parameters={"command": "cp source.txt /tmp/workspace/"}
    )
])
```

### 4. Script Execution

```python
# Run Python script
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::execute_command",
        parameters={
            "command": "python3 process_data.py --input data.csv --output results.json",
            "timeout": 300,
            "cwd": "/home/user/scripts"
        }
    )
])

if result[0].data["success"]:
    logger.info("Script completed successfully")
else:
    logger.error(f"Script failed: {result[0].data['stderr']}")
```

## Comparison with CommandLineExecutor

| Feature | CommandLineExecutor | BashExecutor |
|---------|---------------------|--------------|
| **Platform** | Windows/Cross-platform | Linux only |
| **Output Capture** | ❌ No | ✅ Yes (stdout/stderr) |
| **Exit Code** | ❌ No | ✅ Yes |
| **Timeout** | Fixed 5s | ✅ Configurable |
| **Working Directory** | ❌ No | ✅ Yes |
| **Deployment** | Local | HTTP (remote) |
| **Security** | ⚠️ No blocklist | ✅ Dangerous commands blocked |

## Security Considerations

!!!danger "Security Warning"
    - **Command injection risk**: Always validate/sanitize commands
    - **Privilege escalation**: Server runs with user permissions
    - **Network exposure**: Use firewall rules to limit access
    - **Sensitive data**: Stdout/stderr may contain secrets

### Recommendations

1. **Use firewall**: Restrict access to trusted IPs
   ```bash
   sudo ufw allow from 192.168.1.0/24 to any port 8010
   ```

2. **Run as limited user**: Don't run server as root
   ```bash
   useradd -m -s /bin/bash ufo
   sudo -u ufo python3 -m ufo.client.mcp.http_servers.linux_mcp_server
   ```

3. **Implement command whitelist**: Don't execute arbitrary commands

4. **Use HTTPS**: For production, add TLS encryption

## Related Documentation

- [CommandLineExecutor](./command_line_executor.md) - Windows command execution
- [HardwareExecutor](./hardware_executor.md) - Hardware control via HTTP
- [Remote Servers](../remote_servers.md) - HTTP deployment guide
- [Action Servers](../action.md) - Action server concepts
