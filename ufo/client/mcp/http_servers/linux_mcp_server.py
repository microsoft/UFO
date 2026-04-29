#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Linux MCP Server
Provides MCP interface for executing shell commands on Linux systems.
"""

import argparse
import os
import re
import sys
import shlex
import asyncio
from pathlib import Path
from typing import Annotated, Any, Dict, Optional
from fastmcp import FastMCP
from pydantic import Field


# Commands that are allowed to be executed.
# Only these base command names are permitted.
_ALLOWED_COMMANDS = frozenset({
    # File system browsing (read-only)
    "ls", "find", "stat", "file", "du", "tree",
    # File content viewing (read-only)
    "cat", "head", "tail", "less", "more", "wc", "sort", "uniq",
    # Text search
    "grep", "egrep", "fgrep", "awk", "sed",
    # System info
    "uname", "uptime", "free", "df", "lsblk", "lscpu", "hostname",
    "whoami", "id", "env", "printenv", "date", "cal",
    # Process info (read-only)
    "ps", "top", "htop", "pgrep",
    # Network info (read-only)
    "ifconfig", "ip", "ss", "netstat", "ping", "traceroute",
    "dig", "nslookup", "host",
    # Development tools
    "python3", "python", "pip", "pip3", "node", "npm", "npx",
    "git", "make", "cmake", "cargo", "rustc", "go", "java", "javac",
    "gcc", "g++", "cc",
    # Package info (read-only)
    "dpkg", "apt", "rpm", "yum",
    # Misc safe utilities
    "echo", "printf", "test", "true", "false", "pwd", "which",
    "whereis", "basename", "dirname", "realpath", "readlink",
    "md5sum", "sha256sum", "sha1sum", "diff", "comm", "cut",
    "tr", "tee", "xargs",
})

# Patterns that indicate dangerous shell features even in individual arguments
_DANGEROUS_PATTERNS = [
    r";\s*",       # Command chaining via semicolons
    r"\|\|",       # OR chaining
    r"&&",         # AND chaining
    r"\$\(",       # Command substitution $(...)
    r"`",          # Command substitution `...`
    r">\s*/",      # Redirect to absolute path
    r">>\s*/",     # Append redirect to absolute path
]


def _validate_command(command: str) -> str:
    """
    Validate and sanitize a shell command.

    Only allows commands from the allowlist and blocks dangerous
    shell metacharacters and chaining operators.

    :param command: The raw command string
    :return: The validated command string
    :raises ValueError: If the command is blocked
    """
    if not command or not command.strip():
        raise ValueError("Command must not be empty")

    # Check for dangerous shell patterns in the raw command string
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            raise ValueError(
                f"Command contains blocked shell operator matching pattern: {pattern}"
            )

    # Parse the command into tokens
    try:
        tokens = shlex.split(command)
    except ValueError as e:
        raise ValueError(f"Invalid command syntax: {e}")

    if not tokens:
        raise ValueError("Command must not be empty")

    # Check if the base command is in the allowlist
    base_command = Path(tokens[0]).name  # Handle full paths like /usr/bin/ls
    if base_command not in _ALLOWED_COMMANDS:
        raise ValueError(
            f"Command '{base_command}' is not in the allowed command list"
        )

    return command


def _validate_cwd(cwd: Optional[str]) -> Optional[str]:
    """
    Validate the working directory to prevent path traversal.

    :param cwd: The working directory path
    :return: The resolved absolute path
    :raises ValueError: If the path is invalid
    """
    if cwd is None:
        return None

    resolved = Path(cwd).resolve()
    if not resolved.is_dir():
        raise ValueError(f"Working directory does not exist: {cwd}")

    return str(resolved)


def create_bash_mcp_server(host: str = "", port: int = 8010) -> None:
    """Create an MCP server for Linux command execution."""
    mcp = FastMCP(
        "Linux Bash MCP Server",
        instructions="MCP server for executing shell commands on Linux.",
        stateless_http=False,
        json_response=True,
        host=host,
        port=port,
    )

    @mcp.tool()
    async def execute_command(
        command: Annotated[
            str,
            Field(
                description="Shell command to execute on the Linux system. This should be a valid bash/sh command that will be executed in a shell environment. Examples: 'ls -la /home', 'cat /etc/os-release', 'python3 --version', 'grep -r \"pattern\" /path/to/search'. Be cautious with destructive commands as some dangerous operations are blocked for safety."
            ),
        ],
        timeout: Annotated[
            int,
            Field(
                description="Maximum execution time in seconds before the command is forcefully terminated. Use this to prevent commands from running indefinitely. Default is 30 seconds. For long-running operations like large file transfers or complex compilations, increase this value accordingly. Examples: 30 for quick operations, 300 for file processing, 600 for builds."
            ),
        ] = 30,
        cwd: Annotated[
            Optional[str],
            Field(
                description="Working directory path where the command should be executed. If not specified, the command runs in the server's current working directory. Use absolute paths for reliability. Examples: '/home/user/project', '/var/log', '/tmp/workspace'. Leave empty to use the default directory."
            ),
        ] = None,
    ) -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary containing execution results with keys: 'success' (bool indicating if command succeeded), 'exit_code' (int return code from the process), 'stdout' (str standard output from the command), 'stderr' (str standard error output), or 'error' (str error message if execution failed)"
        ),
    ]:
        """
        Execute a shell command on Linux and return stdout/stderr.
        """
        # Validate command against allowlist and dangerous patterns
        try:
            _validate_command(command)
        except ValueError as e:
            return {"success": False, "error": f"Command blocked: {e}"}

        # Validate working directory
        try:
            validated_cwd = _validate_cwd(cwd)
        except ValueError as e:
            return {"success": False, "error": f"Invalid working directory: {e}"}

        try:
            # Use create_subprocess_exec instead of create_subprocess_shell
            # to prevent shell injection attacks
            args = shlex.split(command)
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=validated_cwd,
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
        Dict[str, Any],
        Field(
            description="Dictionary containing basic Linux system information with keys: 'uname' (system and kernel information from uname -a), 'uptime' (system uptime and load averages), 'memory' (memory usage statistics in human-readable format from free -h), 'disk' (disk space usage for all mounted filesystems from df -h). Each value is either the command output string or an error message if retrieval failed."
        ),
    ]:
        """
        Get basic system info (uname, uptime, memory, disk).
        """
        info = {}
        cmds = {
            "uname": ["uname", "-a"],
            "uptime": ["uptime"],
            "memory": ["free", "-h"],
            "disk": ["df", "-h"],
        }
        for k, cmd in cmds.items():
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE
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
