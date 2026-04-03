# CommandLineExecutor Server

## Overview

**CommandLineExecutor** provides shell command execution capabilities for launching applications and running system commands.

**Server Type:** Action  
**Deployment:** Local (in-process)  
**Agent:** HostAgent, AppAgent  
**LLM-Selectable:** ✅ Yes

## Server Information

| Property | Value |
|----------|-------|
| **Namespace** | `CommandLineExecutor` |
| **Server Name** | `UFO CLI MCP Server` |
| **Platform** | Cross-platform (Windows, Linux, macOS) |
| **Tool Type** | `action` |

## Tools

### run_shell

Execute a shell command to launch applications or perform system operations.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bash_command` | `str` | ✅ Yes | Command to execute in shell |

#### Returns

`None` - Command is launched asynchronously (5-second wait after execution)

#### Example

```python
# Launch Notepad
await computer.run_actions([
    MCPToolCall(
        tool_key="action::run_shell",
        tool_name="run_shell",
        parameters={"bash_command": "notepad.exe"}
    )
])

# Launch PowerPoint with a file
await computer.run_actions([
    MCPToolCall(
        tool_key="action::run_shell",
        tool_name="run_shell",
        parameters={"bash_command": "powerpnt \"Desktop\\test.pptx\""}
    )
])

# Launch File Explorer
await computer.run_actions([
    MCPToolCall(
        tool_key="action::run_shell",
        tool_name="run_shell",
        parameters={"bash_command": "explorer.exe"}
    )
])
```

#### Error Handling

Raises `ToolError` if:
- Command is empty
- Execution fails

```python
# Error: Empty command
ToolError("Bash command cannot be empty.")

# Error: Execution failed
ToolError("Failed to launch application: {error_details}")
```

#### Implementation Details

- Commands are parsed into an argument list via `shlex.split()`
- Uses `subprocess.Popen` with `shell=False` to prevent shell injection
- Shell metacharacters (`|`, `&`, `;`, `` ` ``, `$()`, etc.) are **not** interpreted
- Shell built-in commands (e.g., `start`, `dir`, `cd`) are **not** available — only executable binaries can be launched
- Waits 5 seconds after launch for application to start
- Non-blocking: Returns immediately after launch

!!!info "Security Note"
    Commands are executed **without a shell** (`shell=False`). This means:
    
    - Shell injection via metacharacters is not possible
    - Only direct executable binaries can be invoked
    - Shell built-ins (`start`, `dir`, `cd`, `copy`, etc.) will **not** work
    - Command chaining (`&&`, `||`, `|`, `;`) has no effect
    
    **Best Practice**: Use an allow-list to restrict which executables may be launched.

## Configuration

```yaml
HostAgent:
  default:
    action:
      - namespace: HostUIExecutor
        type: local
      - namespace: CommandLineExecutor
        type: local  # Enable shell execution

AppAgent:
  default:
    action:
      - namespace: AppUIExecutor
        type: local
      - namespace: CommandLineExecutor
        type: local  # Enable if app needs to launch child processes
```

## Best Practices

### 1. Validate Commands

Since `run_shell` executes commands with `shell=False`, shell injection is already mitigated. However, it is still recommended to restrict which executables can be launched:

```python
def safe_run_shell(command: str):
    """Allow-list-based command validation"""
    import shlex
    allowed_commands = [
        "notepad.exe", "notepad",
        "calc.exe", "calc",
        "mspaint.exe", "mspaint",
        "code", "code.exe",
        "explorer", "explorer.exe",
    ]
    
    tokens = shlex.split(command)
    cmd_base = tokens[0].lower()
    if cmd_base not in allowed_commands:
        raise ValueError(f"Command not allowed: {cmd_base}")
    
    return MCPToolCall(
        tool_key="action::run_shell",
        tool_name="run_shell",
        parameters={"bash_command": command}
    )

# Usage
await computer.run_actions([safe_run_shell("notepad.exe test.txt")])
```

### 2. Wait for Application Launch

```python
# Launch application
await computer.run_actions([
    MCPToolCall(
        tool_key="action::run_shell",
        parameters={"bash_command": "notepad.exe"}
    )
])

# Wait for launch (5 seconds built-in + extra)
await asyncio.sleep(2)

# Get window list
windows = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::get_desktop_app_info", ...)
])

# Find Notepad window
notepad_windows = [w for w in windows[0].data if "Notepad" in w["name"]]
```

### 3. Platform-Specific Commands

```python
import platform

def get_platform_command(app_name: str) -> str:
    """Get platform-specific command"""
    if platform.system() == "Windows":
        commands = {
            "notepad": "notepad.exe",
            "terminal": "cmd.exe",
            "browser": "start msedge"
        }
    elif platform.system() == "Darwin":  # macOS
        commands = {
            "notepad": "open -a TextEdit",
            "terminal": "open -a Terminal",
            "browser": "open -a Safari"
        }
    else:  # Linux
        commands = {
            "notepad": "gedit",
            "terminal": "gnome-terminal",
            "browser": "firefox"
        }
    
    return commands.get(app_name, app_name)

# Usage
await computer.run_actions([
    MCPToolCall(
        tool_key="action::run_shell",
        parameters={"bash_command": get_platform_command("notepad")}
    )
])
```

### 4. Handle Launch Failures

```python
try:
    result = await computer.run_actions([
        MCPToolCall(
            tool_key="action::run_shell",
            parameters={"bash_command": "nonexistent.exe"}
        )
    ])
    
    if result[0].is_error:
        logger.error(f"Failed to launch: {result[0].content}")
        # Retry with alternative command
        
except Exception as e:
    logger.error(f"Command execution exception: {e}")
```

## Use Cases

### 1. Application Launching

```python
# Launch text editor
await computer.run_actions([
    MCPToolCall(
        tool_key="action::run_shell",
        parameters={"bash_command": "notepad.exe"}
    )
])

# Launch browser
await computer.run_actions([
    MCPToolCall(
        tool_key="action::run_shell",
        parameters={"bash_command": "msedge.exe https://www.example.com"}
    )
])
```

### 2. Open Files with Applications

```python
# Open a document in Word
await computer.run_actions([
    MCPToolCall(
        tool_key="action::run_shell",
        parameters={"bash_command": "winword.exe report.docx"}
    )
])

# Open a spreadsheet in Excel
await computer.run_actions([
    MCPToolCall(
        tool_key="action::run_shell",
        parameters={"bash_command": "excel.exe data.xlsx"}
    )
])
```

!!!note
    Shell built-in commands like `start`, `copy`, `mkdir`, and `dir` are **not available** because commands run without a shell. Only direct executable binaries (`.exe`) can be invoked.

## Limitations

- **No output capture**: Command output (stdout/stderr) is not returned
- **No exit code**: Cannot determine if command succeeded
- **Async execution**: No way to know when command completes
- **No shell built-ins**: Commands like `start`, `dir`, `copy`, `cd` are not available (runs with `shell=False`)
- **No shell features**: Piping (`|`), redirection (`>`), chaining (`&&`) are not supported

**Tip:** For Linux systems with output capture and better control, use **BashExecutor** server instead.

## Related Documentation

- [BashExecutor](./bash_executor.md) - Linux command execution with output
- [Action Servers](../action.md) - Action server concepts
- [HostAgent](../../ufo2/host_agent/overview.md) - HostAgent architecture

