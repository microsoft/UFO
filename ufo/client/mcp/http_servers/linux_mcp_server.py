#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Linux MCP Server
Provides MCP interface for executing shell commands on Linux systems.
"""

import argparse
import os
import sys
import shlex
import asyncio
from typing import Any, Dict, Optional
from fastmcp import FastMCP


def create_bash_mcp_server(host: str = "", port: int = 8010) -> None:
    """Create an MCP server for Linux command execution."""
    mcp = FastMCP(
        "Linux Bash MCP Server",
        instructions="MCP server for executing shell commands on Linux.",
        stateless_http=True,
        json_response=True,
        host=host,
        port=port,
    )

    @mcp.tool()
    async def execute_command(
        command: str, timeout: int = 30, cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a shell command on Linux and return stdout/stderr.
        """
        # Basic security: block dangerous commands
        dangerous = [
            "rm -rf /",
            ":(){ :|:& };:",
            "mkfs",
            "dd if=/dev/zero",
            "shutdown",
            "reboot",
        ]
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
    async def get_system_info() -> Dict[str, Any]:
        """
        Get basic system info (uname, uptime, memory, disk).
        """
        info = {}
        cmds = {
            "uname": "uname -a",
            "uptime": "uptime",
            "memory": "free -h",
            "disk": "df -h",
        }
        for k, cmd in cmds.items():
            try:
                proc = await asyncio.create_subprocess_shell(
                    cmd, stdout=asyncio.subprocess.PIPE
                )
                out, _ = await proc.communicate()
                info[k] = out.decode("utf-8", errors="replace").strip()
            except Exception as e:
                info[k] = f"Error: {e}"
        return info

    mcp.run(transport="streamable-http")


def main():
    parser = argparse.ArgumentParser(description="Linux Bash MCP Server")
    parser.add_argument(
        "--port", type=int, default=8010, help="Port to run the server on"
    )
    parser.add_argument(
        "--host", default="localhost", help="Host to bind the server to"
    )
    args = parser.parse_args()

    print("=" * 50)
    print("UFO Linux Bash MCP Server")
    print("Linux command execution via Model Context Protocol")
    print(f"Running on {args.host}:{args.port}")
    print("=" * 50)

    create_bash_mcp_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
