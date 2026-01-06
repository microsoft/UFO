# Creating Custom MCP Servers - Complete Tutorial

This tutorial teaches you how to create, register, and deploy custom MCP servers for UFO² agents. You'll learn to build **local**, **HTTP**, and **stdio** MCP servers, and how to register them with different agents.

**Prerequisites**: Basic Python knowledge, familiarity with [MCP Overview](../mcp/overview.md) and [MCP Configuration](../mcp/configuration.md). Review [Built-in Local Servers](../mcp/local_servers.md) as examples.

---

## Table of Contents

1. [Overview](#overview)
2. [Local MCP Servers](#local-mcp-servers)
3. [HTTP MCP Servers](#http-mcp-servers)
4. [Stdio MCP Servers](#stdio-mcp-servers)
5. [Registering Servers with Agents](#registering-servers-with-agents)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### MCP Server Types

UFO² supports three deployment models:

| Type | Deployment | Use Case | Complexity |
|------|------------|----------|------------|
| **Local** | In-process with agent | Fast, built-in tools | ⭐ Simple |
| **HTTP** | Standalone HTTP server | Cross-platform, remote control | ⭐⭐ Moderate |
| **Stdio** | Child process (stdin/stdout) | Process isolation, third-party tools | ⭐⭐⭐ Advanced |

### Server Categories

All MCP servers fall into two categories:

| Category | Purpose | LLM Selectable? | Auto-Invoked? |
|----------|---------|-----------------|---------------|
| **Data Collection** | Read-only observation | ❌ No | ✅ Yes |
| **Action** | State-changing execution | ✅ Yes | ❌ No |

**Tool Selection:**
- **Data Collection tools**: Automatically invoked by the framework to build observation prompts
- **Action tools**: LLM agent actively selects which tool to execute at each step

**Important**: Write clear docstrings and type annotations - they become LLM instructions!

---

## Local MCP Servers

Local servers run **in-process** with the UFO² agent, providing the fastest tool access.

### Step 1: Create Your Server

Create a Python file in `ufo/client/mcp/local_servers/` (or your custom location):

```python
# File: ufo/client/mcp/local_servers/my_custom_server.py

from typing import Annotated
from fastmcp import FastMCP
from pydantic import Field
from ufo.client.mcp.mcp_registry import MCPRegistry


@MCPRegistry.register_factory_decorator("MyCustomExecutor")
def create_my_custom_server(*args, **kwargs) -> FastMCP:
    """
    Create a custom MCP server for specialized automation.
    Factory function registered with MCPRegistry for lazy initialization.
    
    :return: FastMCP instance with custom tools.
    """
    
    # Create FastMCP instance
    mcp = FastMCP("My Custom MCP Server")
    
    # Define tools using @mcp.tool() decorator
    @mcp.tool()
    def greet_user(
        name: Annotated[str, Field(description="The name of the user to greet.")],
        formal: Annotated[bool, Field(description="Use formal greeting?")] = False,
    ) -> Annotated[str, Field(description="The greeting message.")]:
        """
        Greet a user with a customized message.
        Use formal=True for business contexts, False for casual.
        """
        if formal:
            return f"Good day, {name}. How may I assist you?"
        else:
            return f"Hey {name}! What's up?"
    
    @mcp.tool()
    def calculate_sum(
        numbers: Annotated[
            list[int], 
            Field(description="List of integers to sum.")
        ],
    ) -> Annotated[int, Field(description="The sum of all numbers.")]:
        """
        Calculate the sum of a list of numbers.
        Useful for quick arithmetic operations.
        """
        return sum(numbers)
    
    return mcp
```

!!!warning "Critical Design Rules"
    1. **Use `@MCPRegistry.register_factory_decorator("Namespace")`** to register the factory
    2. **Factory function must return a `FastMCP` instance**
    3. **Use `@mcp.tool()` decorator** for each tool
    4. **Write detailed docstrings** - they become LLM instructions
    5. **Use `Annotated[Type, Field(description="...")]`** for all parameters and returns
    6. **Namespace must be unique** across all servers

### Step 2: Import the Server

Add your server to `ufo/client/mcp/local_servers/__init__.py`:

```python
# File: ufo/client/mcp/local_servers/__init__.py

from .my_custom_server import create_my_custom_server
# ... other imports

__all__ = [
    "create_my_custom_server",
    # ... other exports
]
```

### Step 3: Configure in mcp.yaml

Add your server to the appropriate agent in `config/ufo/mcp.yaml`:

```yaml
# For action server (LLM-selectable)
CustomAgent:
  default:
    action:
      - namespace: MyCustomExecutor
        type: local
        reset: false

# For data collection server (auto-invoked)
CustomAgent:
  default:
    data_collection:
      - namespace: MyCustomCollector
        type: local
        reset: false
```

### Step 4: Test Your Server

Test locally before integration:

```python
# File: test_my_server.py

import asyncio
from fastmcp.client import Client
from ufo.client.mcp.local_servers.my_custom_server import create_my_custom_server


async def test_server():
    """Test the custom MCP server."""
    server = create_my_custom_server()
    
    async with Client(server) as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")
        
        # Test greet_user tool
        result = await client.call_tool(
            "greet_user",
            arguments={"name": "Alice", "formal": True}
        )
        print(f"Greeting: {result.data}")
        
        # Test calculate_sum tool
        result = await client.call_tool(
            "calculate_sum",
            arguments={"numbers": [1, 2, 3, 4, 5]}
        )
        print(f"Sum: {result.data}")


if __name__ == "__main__":
    asyncio.run(test_server())
```

### Example: Application-Specific Server

Here's a real-world example - a server for Chrome browser automation. For more details on wrapping application native APIs, see [Wrapping App Native API](creating_app_agent/warpping_app_native_api.md).

```python
# File: ufo/client/mcp/local_servers/chrome_executor.py

from typing import Annotated, Optional
from fastmcp import FastMCP
from pydantic import Field
from ufo.client.mcp.mcp_registry import MCPRegistry
from ufo.automator.puppeteer import AppPuppeteer
from ufo.automator.action_execution import ActionExecutor
from ufo.agents.processors.schemas.actions import ActionCommandInfo


@MCPRegistry.register_factory_decorator("ChromeExecutor")
def create_chrome_executor(process_name: str, *args, **kwargs) -> FastMCP:
    """
    Create a Chrome-specific automation server.
    
    :param process_name: Chrome process name for UI automation.
    :return: FastMCP instance for Chrome automation.
    """
    
    # Initialize puppeteer for Chrome
    puppeteer = AppPuppeteer(
        process_name=process_name,
        app_root_name="chrome.exe",
    )
    executor = ActionExecutor()
    
    def _execute(action: ActionCommandInfo) -> dict:
        """Execute action via puppeteer."""
        return executor.execute(action, puppeteer, control_dict={})
    
    mcp = FastMCP("Chrome Automation MCP Server")
    
    @mcp.tool()
    def navigate_to_url(
        url: Annotated[str, Field(description="The URL to navigate to.")],
    ) -> Annotated[str, Field(description="Navigation result message.")]:
        """
        Navigate Chrome to a specific URL.
        Example: navigate_to_url(url="https://www.google.com")
        """
        action = ActionCommandInfo(
            function="navigate",
            arguments={"url": url},
        )
        return _execute(action)
    
    @mcp.tool()
    def search_in_page(
        query: Annotated[str, Field(description="Search query text.")],
        case_sensitive: Annotated[
            bool, Field(description="Case-sensitive search?")
        ] = False,
    ) -> Annotated[str, Field(description="Search results.")]:
        """
        Search for text in the current Chrome page.
        Returns the number of matches found.
        """
        action = ActionCommandInfo(
            function="find_in_page",
            arguments={"query": query, "case_sensitive": case_sensitive},
        )
        return _execute(action)
    
    @mcp.tool()
    def get_page_title() -> Annotated[str, Field(description="The page title.")]:
        """
        Get the title of the current Chrome page.
        Useful for verifying page navigation.
        """
        action = ActionCommandInfo(function="get_title", arguments={})
        return _execute(action)
    
    return mcp
```

**Configuration:**

```yaml
AppAgent:
  chrome.exe:
    data_collection:
      - namespace: UICollector
        type: local
    action:
      - namespace: AppUIExecutor  # Generic UI automation
        type: local
      - namespace: ChromeExecutor  # Chrome-specific tools
        type: local
        reset: true  # Reset when switching tabs/windows
```

---

## HTTP MCP Servers

HTTP servers run as **standalone services**, enabling cross-platform automation and distributed workflows.

### Step 1: Create HTTP Server

Create a standalone Python script:

```python
# File: ufo/client/mcp/http_servers/my_http_server.py

import argparse
from typing import Annotated, Any, Dict
from fastmcp import FastMCP
from pydantic import Field


def create_my_http_server(host: str = "localhost", port: int = 8020) -> None:
    """
    Create and run an HTTP MCP server.
    
    :param host: Host address to bind the server.
    :param port: Port number for the server.
    """
    
    # Create FastMCP with HTTP transport
    mcp = FastMCP(
        "My Custom HTTP MCP Server",
        instructions="Custom automation server via HTTP.",
        stateless_http=True,  # Stateless HTTP (one-shot JSON)
        json_response=True,   # Return pure JSON bodies
        host=host,
        port=port,
    )
    
    @mcp.tool()
    async def process_data(
        data: Annotated[str, Field(description="Data to process.")],
        transform: Annotated[
            str, Field(description="Transformation type: 'upper', 'lower', 'reverse'.")
        ] = "upper",
    ) -> Annotated[Dict[str, Any], Field(description="Processing result.")]:
        """
        Process text data with various transformations.
        Supports: 'upper' (uppercase), 'lower' (lowercase), 'reverse' (reverse string).
        """
        try:
            if transform == "upper":
                result = data.upper()
            elif transform == "lower":
                result = data.lower()
            elif transform == "reverse":
                result = data[::-1]
            else:
                return {"success": False, "error": f"Unknown transform: {transform}"}
            
            return {
                "success": True,
                "original": data,
                "transformed": result,
                "transform_type": transform,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool()
    async def get_server_info() -> Annotated[
        Dict[str, Any], Field(description="Server information.")
    ]:
        """
        Get information about the HTTP MCP server.
        Returns server name, version, and status.
        """
        import platform
        return {
            "server": "My Custom HTTP MCP Server",
            "version": "1.0.0",
            "platform": platform.system(),
            "status": "running",
        }
    
    # Start the HTTP server
    mcp.run(transport="streamable-http")


def main():
    """Main entry point for the HTTP server."""
    parser = argparse.ArgumentParser(description="My Custom HTTP MCP Server")
    parser.add_argument("--port", type=int, default=8020, help="Server port")
    parser.add_argument("--host", default="localhost", help="Server host")
    args = parser.parse_args()
    
    print("=" * 60)
    print("My Custom HTTP MCP Server")
    print(f"Running on {args.host}:{args.port}")
    print("=" * 60)
    
    create_my_http_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
```

### Step 2: Start the HTTP Server

Run the server as a standalone process:

```bash
# Start on localhost
python -m ufo.client.mcp.http_servers.my_http_server --host localhost --port 8020

# Start on all interfaces (for remote access)
python -m ufo.client.mcp.http_servers.my_http_server --host 0.0.0.0 --port 8020
```

**For production, run as a background service:**

**Linux/macOS:**
```bash
nohup python -m ufo.client.mcp.http_servers.my_http_server --host 0.0.0.0 --port 8020 &
```

**Windows:**
```powershell
Start-Process python -ArgumentList "-m", "ufo.client.mcp.http_servers.my_http_server", "--host", "0.0.0.0", "--port", "8020" -WindowStyle Hidden
```

### Step 3: Configure HTTP Server in mcp.yaml

```yaml
RemoteAgent:
  default:
    action:
      - namespace: MyHTTPExecutor
        type: http
        host: "localhost"  # Or remote IP: "192.168.1.100"
        port: 8020
        path: "/mcp"
        reset: false
```

### Step 4: Test HTTP Server

Test connectivity before integration:

```python
# File: test_http_server.py

import asyncio
from fastmcp.client import Client


async def test_http_server():
    """Test the HTTP MCP server."""
    server_url = "http://localhost:8020/mcp"
    
    async with Client(server_url) as client:
        # List tools
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")
        
        # Test process_data
        result = await client.call_tool(
            "process_data",
            arguments={"data": "Hello World", "transform": "reverse"}
        )
        print(f"Process result: {result.data}")
        
        # Test get_server_info
        result = await client.call_tool("get_server_info", arguments={})
        print(f"Server info: {result.data}")


if __name__ == "__main__":
    asyncio.run(test_http_server())
```

### Example: Cross-Platform Linux Executor

Real-world example - controlling Linux systems from Windows:

```python
# File: ufo/client/mcp/http_servers/linux_executor.py

import argparse
import asyncio
from typing import Annotated, Any, Dict, Optional
from fastmcp import FastMCP
from pydantic import Field


def create_linux_executor(host: str = "0.0.0.0", port: int = 8010) -> None:
    """Linux command execution MCP server."""
    
    mcp = FastMCP(
        "Linux Executor MCP Server",
        instructions="Execute shell commands on Linux.",
        stateless_http=True,
        json_response=True,
        host=host,
        port=port,
    )
    
    @mcp.tool()
    async def execute_command(
        command: Annotated[str, Field(description="Shell command to execute.")],
        timeout: Annotated[int, Field(description="Timeout in seconds.")] = 30,
        cwd: Annotated[
            Optional[str], Field(description="Working directory.")
        ] = None,
    ) -> Annotated[Dict[str, Any], Field(description="Execution result.")]:
        """
        Execute a shell command on Linux and return stdout/stderr.
        Dangerous commands (rm -rf /, shutdown, etc.) are blocked.
        """
        # Security check
        dangerous = ["rm -rf /", "shutdown", "reboot", "mkfs"]
        if any(d in command.lower() for d in dangerous):
            return {"success": False, "error": "Blocked dangerous command."}
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return {"success": False, "error": f"Timeout after {timeout}s."}
            
            return {
                "success": proc.returncode == 0,
                "exit_code": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool()
    async def get_system_info() -> Annotated[
        Dict[str, Any], Field(description="System information.")
    ]:
        """Get basic Linux system information."""
        info = {}
        cmds = {
            "uname": "uname -a",
            "uptime": "uptime",
            "memory": "free -h",
        }
        for key, cmd in cmds.items():
            try:
                proc = await asyncio.create_subprocess_shell(
                    cmd, stdout=asyncio.subprocess.PIPE
                )
                out, _ = await proc.communicate()
                info[key] = out.decode("utf-8", errors="replace").strip()
            except Exception as e:
                info[key] = f"Error: {e}"
        return info
    
    mcp.run(transport="streamable-http")


def main():
    parser = argparse.ArgumentParser(description="Linux Executor MCP Server")
    parser.add_argument("--port", type=int, default=8010)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    
    print(f"Linux Executor running on {args.host}:{args.port}")
    create_linux_executor(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
```

**Deploy on Linux:**

```bash
# Start server on Linux machine
python -m ufo.client.mcp.http_servers.linux_executor --host 0.0.0.0 --port 8010
```

**Configure on Windows UFO²:**

```yaml
LinuxAgent:
  default:
    action:
      - namespace: LinuxExecutor
        type: http
        host: "192.168.1.50"  # Linux machine IP
        port: 8010
        path: "/mcp"
```

**Cross-Platform Workflow**: Now your Windows UFO² agent can execute Linux commands remotely! The LLM will select `execute_command` or `get_system_info` as needed.

---

## Stdio MCP Servers

Stdio servers run as **child processes**, communicating via stdin/stdout. They provide process isolation and work with any language.

### Step 1: Create Stdio Server

Create a standalone script that reads JSON-RPC from stdin and writes to stdout:

```python
# File: custom_stdio_server.py

import sys
import json
from typing import Any, Dict


def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming MCP request.
    
    :param request: JSON-RPC request from stdin.
    :return: JSON-RPC response.
    """
    method = request.get("method", "")
    params = request.get("params", {})
    
    if method == "tools/list":
        # Return available tools
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "echo",
                        "description": "Echo back a message.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "Message to echo.",
                                }
                            },
                            "required": ["message"],
                        },
                    }
                ]
            },
        }
    
    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        if tool_name == "echo":
            message = arguments.get("message", "")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Echo: {message}",
                        }
                    ]
                },
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}",
                },
            }
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32601,
                "message": f"Unknown method: {method}",
            },
        }


def main():
    """Main stdio loop."""
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": str(e),
                },
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
```

### Step 2: Configure Stdio Server in mcp.yaml

```yaml
CustomAgent:
  default:
    action:
      - namespace: CustomStdioExecutor
        type: stdio
        command: "python"
        start_args: ["custom_stdio_server.py"]
        env:
          API_KEY: "secret_key"
          LOG_LEVEL: "INFO"
        cwd: "/path/to/server/directory"
        reset: false
```

!!!warning "Stdio Limitations"
    - **More complex** than local/HTTP servers
    - Requires implementing **JSON-RPC protocol** manually
    - Better suited for **third-party MCP servers** than custom tools
    - For custom Python tools, **prefer local or HTTP servers**

### Example: Third-Party Node.js Server

Stdio is ideal for integrating existing MCP servers written in other languages:

```yaml
CustomAgent:
  default:
    action:
      - namespace: NodeJSTools
        type: stdio
        command: "node"
        start_args: ["./node_mcp_server/index.js"]
        env:
          NODE_ENV: "production"
        cwd: "/path/to/node_mcp_server"
```

---

## Registering Servers with Agents

### Agent-Specific Registration

Different agents can use different MCP server configurations:

```yaml
# HostAgent: System-level automation
HostAgent:
  default:
    data_collection:
      - namespace: UICollector
        type: local
    action:
      - namespace: HostUIExecutor
        type: local
      - namespace: CommandLineExecutor
        type: local

# AppAgent: Application-specific automation
AppAgent:
  # Default configuration for all apps
  default:
    data_collection:
      - namespace: UICollector
        type: local
    action:
      - namespace: AppUIExecutor
        type: local
      - namespace: CommandLineExecutor
        type: local
  
  # Word-specific configuration
  WINWORD.EXE:
    data_collection:
      - namespace: UICollector
        type: local
    action:
      - namespace: AppUIExecutor
        type: local
      - namespace: WordCOMExecutor  # Word COM API
        type: local
        reset: true
      - namespace: CommandLineExecutor
        type: local
  
  # Excel-specific configuration
  EXCEL.EXE:
    data_collection:
      - namespace: UICollector
        type: local
    action:
      - namespace: AppUIExecutor
        type: local
      - namespace: ExcelCOMExecutor  # Excel COM API
        type: local
        reset: true
  
  # Chrome-specific configuration
  chrome.exe:
    data_collection:
      - namespace: UICollector
        type: local
    action:
      - namespace: AppUIExecutor
        type: local
      - namespace: ChromeExecutor  # Custom Chrome tools
        type: local
        reset: true

# Custom Agent: Specialized automation
CustomAutomationAgent:
  default:
    data_collection:
      - namespace: UICollector
        type: local
      - namespace: MyCustomCollector  # Custom data collection
        type: local
    action:
      - namespace: MyCustomExecutor  # Custom actions
        type: local
      - namespace: MyHTTPExecutor  # Remote HTTP actions
        type: http
        host: "192.168.1.100"
        port: 8020
        path: "/mcp"
```

### Multi-Server Agent Configuration

Agents can register **multiple servers** of the same category:

```yaml
HybridAgent:
  default:
    # Multiple data collection sources
    data_collection:
      - namespace: UICollector
        type: local
      - namespace: HardwareCollector  # Remote hardware monitoring
        type: http
        host: "192.168.1.50"
        port: 8006
        path: "/mcp"
      - namespace: SystemMetrics  # Custom metrics
        type: local
    
    # Multiple action executors (LLM chooses best tool)
    action:
      - namespace: AppUIExecutor  # GUI automation
        type: local
      - namespace: WordCOMExecutor  # API automation
        type: local
        reset: true
      - namespace: LinuxExecutor  # Remote Linux control
        type: http
        host: "192.168.1.100"
        port: 8010
        path: "/mcp"
      - namespace: CustomExecutor  # Custom actions
        type: local
```

**How it works:**

1. **Data collection tools**: All servers are invoked automatically to build observation
2. **Action tools**: LLM sees tools from ALL action servers and selects the best one

**Example LLM decision:**

```
Task: "Create a Word document with sales data from the Linux database"

Step 1: Get data from Linux
  → LLM selects: LinuxExecutor::execute_command(
      command="mysql -e 'SELECT * FROM sales'"
  )

Step 2: Create Word document
  → LLM selects: WordCOMExecutor::insert_table(rows=10, columns=3)

Step 3: Format the table
  → LLM selects: WordCOMExecutor::select_table(number=1)
  →            AppUIExecutor::click_input(name="Table Design")
```

### Configuration Hierarchy

Agent configurations follow this **inheritance hierarchy**:

```
AgentName
  ├─ default (fallback configuration)
  │   ├─ data_collection
  │   └─ action
  └─ SubType (e.g., "WINWORD.EXE")
      ├─ data_collection
      └─ action
```

**Lookup logic:**

1. Check for `AgentName.SubType`
2. If not found, use `AgentName.default`
3. If neither exists, raise error

**Example:**

```yaml
AppAgent:
  # Fallback for all apps
  default:
    action:
      - namespace: AppUIExecutor
        type: local
  
  # Overrides default for Word
  WINWORD.EXE:
    action:
      - namespace: AppUIExecutor
        type: local
      - namespace: WordCOMExecutor
        type: local
```

---

## Best Practices

### 1. Write Comprehensive Docstrings

Your docstrings are **directly converted to LLM prompts**. The LLM uses them to understand:
- **What** the tool does
- **When** to use it
- **How** to use it correctly

**Bad Example:**
```python
@mcp.tool()
def process(data: str) -> str:
    """Process data."""  # ❌ Too vague
    return data.upper()
```

**Good Example:**
```python
@mcp.tool()
def process_text_to_uppercase(
    text: Annotated[str, Field(description="The input text to convert.")],
) -> Annotated[str, Field(description="The text converted to uppercase.")]:
    """
    Convert text to uppercase letters.
    
    Use this tool when you need to standardize text formatting or make text
    more prominent. Works with all Unicode characters.
    
    Examples:
    - "hello world" → "HELLO WORLD"
    - "Café" → "CAFÉ"
    """  # ✅ Clear, detailed, with examples
    return text.upper()
```

### 2. Use Descriptive Parameter Names

```python
# ❌ Bad: Unclear parameter names
@mcp.tool()
def func(a: str, b: int, c: bool) -> str:
    ...

# ✅ Good: Self-documenting parameter names
@mcp.tool()
def send_email(
    recipient_address: str,
    message_body: str,
    use_html_format: bool = False,
) -> str:
    ...
```

### 3. Provide Default Values

```python
@mcp.tool()
def search_files(
    query: Annotated[str, Field(description="Search query.")],
    case_sensitive: Annotated[
        bool, Field(description="Case-sensitive search?")
    ] = False,  # ✅ Sensible default
    max_results: Annotated[
        int, Field(description="Maximum results to return.")
    ] = 10,  # ✅ Sensible default
) -> list[str]:
    """Search for files matching the query."""
    ...
```

### 4. Handle Errors Gracefully

```python
@mcp.tool()
def divide_numbers(
    dividend: Annotated[float, Field(description="Number to divide.")],
    divisor: Annotated[float, Field(description="Number to divide by.")],
) -> Annotated[dict, Field(description="Division result or error.")]:
    """
    Divide two numbers and return the result.
    Returns an error if divisor is zero.
    """
    try:
        if divisor == 0:
            return {
                "success": False,
                "error": "Cannot divide by zero.",
            }
        
        result = dividend / divisor
        return {
            "success": True,
            "result": result,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Division failed: {str(e)}",
        }
```

### 5. Use Reset for Stateful Servers

```yaml
# ✅ Good: Reset COM servers when switching contexts
AppAgent:
  WINWORD.EXE:
    action:
      - namespace: WordCOMExecutor
        type: local
        reset: true  # Prevents state leakage between documents

# ❌ Bad: Not resetting can cause issues
AppAgent:
  WINWORD.EXE:
    action:
      - namespace: WordCOMExecutor
        type: local
        reset: false  # May retain state from previous document
```

### 6. Validate Remote Server Connectivity

Before deploying, test connectivity:

```python
import asyncio
from fastmcp.client import Client


async def validate_server(url: str):
    """Validate HTTP server is accessible."""
    try:
        async with Client(url) as client:
            tools = await client.list_tools()
            print(f"✅ Server {url} is accessible")
            print(f"   Tools: {[t.name for t in tools]}")
            return True
    except Exception as e:
        print(f"❌ Server {url} is NOT accessible: {e}")
        return False


# Test before adding to mcp.yaml
asyncio.run(validate_server("http://192.168.1.100:8020/mcp"))
```

### 7. Use Environment Variables for Secrets

```yaml
# ❌ Bad: Hardcoded secrets
CustomAgent:
  default:
    action:
      - namespace: APIExecutor
        type: http
        host: "api.example.com"
        port: 443
        auth_token: "sk-1234567890"  # Don't commit this!

# ✅ Good: Use environment variables
CustomAgent:
  default:
    action:
      - namespace: APIExecutor
        type: http
        host: "${API_HOST}"
        port: "${API_PORT}"
        auth_token: "${API_TOKEN}"
```

Set environment variables before running UFO²:

```bash
export API_HOST="api.example.com"
export API_PORT="443"
export API_TOKEN="sk-1234567890"
```

---

## Troubleshooting

### Common Issues

#### 1. "No MCP server found for name 'MyServer'"

**Cause**: Server not registered in MCPRegistry.

**Solution**:
```python
# Ensure you're using the decorator
@MCPRegistry.register_factory_decorator("MyServer")
def create_my_server(*args, **kwargs) -> FastMCP:
    ...

# Or manually register
MCPRegistry.register_factory("MyServer", create_my_server)
```

#### 2. "Connection refused" for HTTP Server

**Cause**: HTTP server not running or wrong host/port.

**Solution**:
```bash
# Verify server is running
curl http://localhost:8020/mcp

# Check firewall rules
# Windows:
netsh advfirewall firewall add rule name="MCP Server" dir=in action=allow protocol=TCP localport=8020

# Linux:
sudo ufw allow 8020/tcp
```

#### 3. Tools Not Appearing in LLM Prompt

**Cause**: Server registered in wrong category (data_collection vs action).

**Solution**:
```yaml
# For LLM-selectable tools, use 'action'
CustomAgent:
  default:
    action:  # ✅ Correct for LLM-selectable tools
      - namespace: MyExecutor
        type: local

# For auto-invoked observation, use 'data_collection'
CustomAgent:
  default:
    data_collection:  # ✅ Correct for automatic observation
      - namespace: MyCollector
        type: local
```

#### 4. Server State Leaking Between Contexts

**Cause**: `reset: false` for stateful servers.

**Solution**:
```yaml
# Set reset: true for stateful servers
AppAgent:
  WINWORD.EXE:
    action:
      - namespace: WordCOMExecutor
        type: local
        reset: true  # ✅ Reset COM state when switching documents
```

#### 5. Timeout Errors for Long-Running Tools

**Cause**: Default timeout is 6000 seconds (100 minutes).

**Solution**:
```python
# In Computer class, adjust timeout
self._tool_timeout = 12000  # 200 minutes
```

### Debugging Tips

#### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ufo.client.mcp")
```

#### Check Registered Servers

```python
from ufo.client.mcp.mcp_server_manager import MCPServerManager

# List all registered servers
for namespace, server in MCPServerManager._servers_mapping.items():
    print(f"Server: {namespace}, Type: {type(server).__name__}")
```

#### Test Server in Isolation

```python
# Test local server
from ufo.client.mcp.local_servers.my_custom_server import create_my_custom_server
import asyncio
from fastmcp.client import Client


async def test():
    server = create_my_custom_server()
    async with Client(server) as client:
        tools = await client.list_tools()
        print(f"Tools: {[t.name for t in tools]}")


asyncio.run(test())
```

---

## Next Steps

Now that you've learned to create MCP servers, explore these related topics:

1. **Review Built-in Servers**: See [Local Servers](../mcp/local_servers.md) for production examples
2. **Explore HTTP Deployment**: Read [Remote Servers](../mcp/remote_servers.md) for cross-platform automation
3. **Understand Agent Configuration**: Study [MCP Configuration](../mcp/configuration.md) for advanced setups
4. **Learn about Computer Class**: Review [Computer](../client/computer.md) to understand the MCP client integration
5. **Create Your First Agent**: Follow [Creating App Agent](creating_app_agent/overview.md) to build custom agents

---

## Related Documentation

- [MCP Overview](../mcp/overview.md) - MCP architecture and concepts
- [MCP Configuration](../mcp/configuration.md) - Complete configuration reference
- [Local Servers](../mcp/local_servers.md) - Built-in local servers
- [Remote Servers](../mcp/remote_servers.md) - HTTP/Stdio deployment
- [Data Collection Servers](../mcp/data_collection.md) - Observation tools
- [Action Servers](../mcp/action.md) - Execution tools
- [MCP Reference](../configuration/system/mcp_reference.md) - Quick reference guide

---

## Best Practices Summary

- ✅ **Write clear docstrings** - they become LLM instructions
- ✅ **Use descriptive names** - for tools, parameters, and namespaces
- ✅ **Handle errors gracefully** - return structured error messages
- ✅ **Test in isolation** - before integrating with agents
- ✅ **Use `reset: true`** - for stateful servers (COM, API clients)
- ✅ **Validate connectivity** - for HTTP/Stdio servers before deployment
