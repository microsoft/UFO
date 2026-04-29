#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Linux MCP Server
Provides MCP interface for executing shell commands on Linux systems.

Security model (mirrors the Windows ``shell_client.py`` approach):
- **Allowlist**: only explicitly permitted base commands may run.
- **Dangerous-pattern scan**: blocks shell metacharacters, command
  substitution, reverse-shell indicators, etc.
- **shell=False**: commands are executed via ``create_subprocess_exec``
  so shell metacharacters are *never* interpreted.
- **API-key authentication**: every tool call must supply a key that
  matches the ``UFO_MCP_API_KEY`` environment variable.
"""

import argparse
import hmac
import logging
import os
import re
import shlex
import asyncio
from pathlib import Path
from typing import Annotated, Any, Dict, FrozenSet, List, Optional
from fastmcp import FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security: command allow-list for execute_command
# Only these base commands may be executed.  Extend as needed.
# ---------------------------------------------------------------------------
ALLOWED_SHELL_COMMANDS: FrozenSet[str] = frozenset(
    {
        # File listing / navigation
        "ls",
        "pwd",
        # File reading (read-only)
        "cat",
        "head",
        "tail",
        # Search / lookup
        "grep",
        "find",
        "which",
        "whereis",
        # Text processing (read-only, no write side-effects)
        "wc",
        "sort",
        "uniq",
        "cut",
        "tr",
        # System info (read-only)
        "uname",
        "hostname",
        "whoami",
        "id",
        "uptime",
        "free",
        "df",
        "du",
        "ps",
        # Network diagnostics (read-only)
        "ping",
        "traceroute",
        "nslookup",
        "dig",
        "host",
        # File metadata (read-only)
        "file",
        "stat",
        "md5sum",
        "sha256sum",
        # Version checks
        "python3",
        "python",
        # Other benign read-only utilities
        "echo",
        "date",
        "cal",
        "basename",
        "dirname",
        "realpath",
        "diff",
        "test",
    }
)

# Patterns that indicate dangerous intent regardless of the base command.
_DANGEROUS_PATTERNS: List[re.Pattern] = [
    # Shell metacharacters for chaining / piping (defense-in-depth)
    re.compile(r"[;|&`]"),
    # Command substitution
    re.compile(r"\$\("),
    re.compile(r"\$\{"),
    # find -exec / -execdir can run arbitrary commands
    re.compile(r"-exec\b"),
    re.compile(r"-execdir\b"),
    # Reverse-shell indicators
    re.compile(r"/dev/tcp/"),
    re.compile(r"/dev/udp/"),
    # I/O redirection (defense-in-depth, shell=False already neutralises)
    re.compile(r"[><]"),
    # Newline / null-byte injection
    re.compile(r"[\n\r\x00]"),
]


def _extract_base_command(command_str: str) -> Optional[str]:
    """Return the first token (base command) from *command_str*."""
    stripped = command_str.strip()
    if not stripped:
        return None
    try:
        tokens = shlex.split(stripped)
        return tokens[0] if tokens else None
    except ValueError:
        # Malformed shell quoting
        return None


def _is_command_allowed(command_str: str) -> bool:
    """
    Validate *command_str* against the allow-list **and** dangerous patterns.

    Returns ``True`` only when the base command is in
    ``ALLOWED_SHELL_COMMANDS`` **and** no dangerous pattern is found.
    """
    if not command_str or not command_str.strip():
        return False

    # Scan for dangerous patterns in the raw input first
    for pattern in _DANGEROUS_PATTERNS:
        if pattern.search(command_str):
            logger.warning(
                "Blocked command matching dangerous pattern %s: %s",
                pattern.pattern,
                command_str[:200],
            )
            return False

    base = _extract_base_command(command_str)
    if base is None:
        return False

    # Use basename to prevent path-based bypass (e.g. /usr/bin/bash)
    base_name = os.path.basename(base)

    if base_name not in ALLOWED_SHELL_COMMANDS:
        logger.warning("Blocked command not in allow-list: %s", base_name)
        return False

    return True


def _validate_api_key(provided_key: Optional[str]) -> bool:
    """
    Constant-time comparison of *provided_key* against the
    ``UFO_MCP_API_KEY`` environment variable.
    Rejects the request when no server-side key is configured.
    """
    expected_key = os.environ.get("UFO_MCP_API_KEY")
    if not expected_key:
        # No key configured → deny all requests (fail-closed)
        return False
    if not provided_key:
        return False
    return hmac.compare_digest(provided_key, expected_key)


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


def create_bash_mcp_server(host: str = "localhost", port: int = 8010) -> None:
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
                description="Shell command to execute on the Linux system. Only allow-listed base commands are permitted (e.g. ls, cat, grep, find, df, ps). Shell metacharacters, pipes, and chaining operators are blocked. Examples: 'ls -la /home', 'cat /etc/os-release', 'grep -r \"pattern\" /path'."
            ),
        ],
        api_key: Annotated[
            str,
            Field(
                description="API key for authentication. Must match the UFO_MCP_API_KEY environment variable configured on the server."
            ),
        ],
        timeout: Annotated[
            int,
            Field(
                description="Maximum execution time in seconds (1-120). Default is 30."
            ),
        ] = 30,
        cwd: Annotated[
            Optional[str],
            Field(
                description="Working directory for command execution. Must be an absolute path. Defaults to the server's current directory."
            ),
        ] = None,
    ) -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary containing execution results with keys: 'success', 'exit_code', 'stdout', 'stderr', or 'error'."
        ),
    ]:
        """
        Execute an allow-listed command on Linux and return stdout/stderr.

        Security controls:
        - API-key authentication required.
        - Command must be in the server allow-list.
        - Dangerous patterns (shell metacharacters, -exec, etc.) are rejected.
        - Executed with shell=False (no shell interpretation).
        """
        # --- authentication ---
        if not _validate_api_key(api_key):
            return {
                "success": False,
                "error": "Authentication failed. Invalid or missing API key.",
            }

        # --- command validation ---
        if not _is_command_allowed(command):
            return {
                "success": False,
                "error": "Command blocked by security policy. "
                "Only allow-listed commands may be executed.",
            }

        # Cap timeout to a sane range
        timeout = min(max(int(timeout), 1), 120)

        # Validate working directory
        try:
            validated_cwd = _validate_cwd(cwd)
        except ValueError as e:
            return {"success": False, "error": f"Invalid working directory: {e}"}

        try:
            cmd_tokens = shlex.split(command)

            proc = await asyncio.create_subprocess_exec(
                *cmd_tokens,
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
    async def get_system_info(
        api_key: Annotated[
            str,
            Field(
                description="API key for authentication. Must match the UFO_MCP_API_KEY environment variable configured on the server."
            ),
        ],
    ) -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary containing basic Linux system information with keys: 'uname', 'uptime', 'memory', 'disk'."
        ),
    ]:
        """
        Get basic system info (uname, uptime, memory, disk).
        Requires API key authentication.
        """
        if not _validate_api_key(api_key):
            return {
                "error": "Authentication failed. Invalid or missing API key.",
            }

        info: Dict[str, str] = {}
        # Fixed argument lists — no user input, no shell
        cmds: Dict[str, List[str]] = {
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

    # Fail-fast when no API key is configured
    if not os.environ.get("UFO_MCP_API_KEY"):
        print(
            "ERROR: UFO_MCP_API_KEY environment variable is not set.\n"
            "Set it before starting the server:\n"
            "  export UFO_MCP_API_KEY='<your-secret-key>'"
        )
        raise SystemExit(1)

    if args.host == "0.0.0.0":
        print(
            "WARNING: Binding to 0.0.0.0 exposes the server to all network "
            "interfaces. Use 'localhost' or '127.0.0.1' unless remote access "
            "is explicitly required."
        )

    print("=" * 50)
    print("UFO Linux Bash MCP Server")
    print("Linux command execution via Model Context Protocol")
    print(f"Running on {args.host}:{args.port}")
    print("=" * 50)

    create_bash_mcp_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
