#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
CLI MCP Server
Provides MCP server for command line operations:
- Application launching via command execution
"""

import logging
import re
import shlex
import subprocess
import time
from typing import FrozenSet, List

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from ufo.client.mcp.mcp_registry import MCPRegistry
from ufo.config import get_config

logger = logging.getLogger(__name__)

# Get config
configs = get_config()

# ---------------------------------------------------------------------------
# Security: only these base commands / executables may be launched.
# Extend as needed for legitimate application-launching use cases.
# ---------------------------------------------------------------------------
ALLOWED_CLI_COMMANDS: FrozenSet[str] = frozenset(
    {
        # Windows applications
        "notepad",
        "notepad.exe",
        "calc",
        "calc.exe",
        "mspaint",
        "mspaint.exe",
        "wordpad",
        "wordpad.exe",
        "explorer",
        "explorer.exe",
        "msedge",
        "msedge.exe",
        "chrome",
        "chrome.exe",
        "firefox",
        "firefox.exe",
        # Microsoft Office
        "winword",
        "winword.exe",
        "excel",
        "excel.exe",
        "powerpnt",
        "powerpnt.exe",
        "outlook",
        "outlook.exe",
        "onenote",
        "onenote.exe",
        # Common utilities
        "code",
        "code.exe",
    }
)

# Patterns that indicate malicious or dangerous intent regardless of command
_DANGEROUS_PATTERNS: List[re.Pattern] = [
    re.compile(r"Invoke-Expression|IEX\b", re.IGNORECASE),
    re.compile(r"Invoke-WebRequest|IWR\b|Invoke-RestMethod|IRM\b", re.IGNORECASE),
    re.compile(r"Start-Process\b", re.IGNORECASE),
    re.compile(r"New-Object\s+.*Net\.WebClient", re.IGNORECASE),
    re.compile(r"DownloadString|DownloadFile", re.IGNORECASE),
    re.compile(r"\bAdd-Type\b", re.IGNORECASE),
    re.compile(r"\b(cmd|powershell|pwsh)(\.exe)?\s+[/-]", re.IGNORECASE),
    re.compile(r"[|;&`]\s*(bash|sh|cmd|powershell|pwsh)", re.IGNORECASE),
    re.compile(r"\bNew-Service\b|\bsc\.exe\b", re.IGNORECASE),
    re.compile(r"\breg(\.exe)?\s+(add|delete|import)", re.IGNORECASE),
    re.compile(r"\bschtasks(\.exe)?\b", re.IGNORECASE),
    re.compile(r"\bnet\s+(user|localgroup)\b", re.IGNORECASE),
    re.compile(r"\bSet-ExecutionPolicy\b", re.IGNORECASE),
    re.compile(r"\bRemove-Item\b.*-Recurse", re.IGNORECASE),
    re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
    re.compile(r"[`$]\(", re.IGNORECASE),  # sub-expression / command substitution
    re.compile(r"\bcurl\b|\bwget\b", re.IGNORECASE),
    re.compile(r"\brdp\b|\bmstsc\b", re.IGNORECASE),
    re.compile(r">{1,2}\s*[/\\]", re.IGNORECASE),  # output redirection to paths
]

# start.exe flags that consume no additional argument
_START_FLAGS_NO_ARG: FrozenSet[str] = frozenset(
    {
        "/b", "/wait", "/min", "/max",
        "/abovenormal", "/normal", "/belownormal",
        "/low", "/idle", "/high", "/realtime",
        "/affinity", "/node",
    }
)

# start.exe flags that consume one additional argument
_START_FLAGS_ONE_ARG: FrozenSet[str] = frozenset({"/d"})


def _strip_start_prefix(tokens: List[str]) -> List[str]:
    """
    If the token list begins with the Windows ``start`` shell command, strip
    it along with any ``start`` flags so the returned list begins with the
    actual executable.  Returns the original list unchanged for all other
    commands.
    """
    if not tokens or tokens[0].lower() not in ("start", "start.exe"):
        return tokens

    idx = 1

    # Skip optional window title: a non-flag token that looks like a plain
    # label (no dot, no path separators) rather than an executable name.
    if idx < len(tokens) and not tokens[idx].startswith("/"):
        candidate = tokens[idx]
        if "." not in candidate and "\\" not in candidate and "/" not in candidate:
            idx += 1

    # Skip /flag and /flag <value> pairs
    while idx < len(tokens) and tokens[idx].startswith("/"):
        flag = tokens[idx].lower()
        idx += 1
        if flag in _START_FLAGS_ONE_ARG and idx < len(tokens):
            idx += 1  # consume the flag's argument

    return tokens[idx:]


def _is_cli_command_allowed(command_str: str) -> bool:
    """
    Validate a command string against the allow-list and dangerous patterns.
    Returns True only if the base command is in the allow-list AND no
    dangerous patterns are detected.
    """
    if not command_str or not command_str.strip():
        return False

    try:
        tokens = shlex.split(command_str)
    except ValueError:
        return False

    if not tokens:
        return False

    # Unwrap Windows ``start`` launcher so we validate the real executable.
    tokens = _strip_start_prefix(tokens)

    if not tokens:
        return False

    base = tokens[0].strip().lower()

    # Check base command against allow-list (case-insensitive)
    if not any(base == allowed.lower() for allowed in ALLOWED_CLI_COMMANDS):
        logger.warning("Blocked CLI command not in allow-list: %s", base)
        return False

    # Check for dangerous patterns in the full command string
    for pattern in _DANGEROUS_PATTERNS:
        if pattern.search(command_str):
            logger.warning(
                "Blocked CLI command matching dangerous pattern %s: %s",
                pattern.pattern,
                command_str[:200],
            )
            return False

    return True


def _resolve_launch_args(command_str: str) -> List[str]:
    """
    Return the argument list to pass to ``subprocess.Popen``.
    When the command begins with ``start``, the launcher prefix is stripped
    so the application is launched directly without requiring ``shell=True``.
    """
    tokens = shlex.split(command_str)
    return _strip_start_prefix(tokens)


@MCPRegistry.register_factory_decorator("CommandLineExecutor")
def create_cli_mcp_server(*args, **kwargs) -> FastMCP:
    """
    Create and return the CLI MCP server instance.
    :return: FastMCP instance for CLI operations.
    """

    cli_mcp = FastMCP("UFO CLI MCP Server")

    @cli_mcp.tool()
    def run_shell(
        bash_command: str,
    ) -> None:
        """
        Launch an application using the provided command.
        Only allow-listed applications may be launched.
        :param bash_command: The command to execute to launch the application.
        :return: None
        """

        if not bash_command:
            raise ToolError("Bash command cannot be empty.")

        if not _is_cli_command_allowed(bash_command):
            raise ToolError(
                "Command blocked by security policy. "
                "Only allow-listed applications may be launched."
            )

        try:
            # Resolve to a direct executable invocation (strips ``start`` if
            # present) and launch without shell=True to prevent shell injection.
            args = _resolve_launch_args(bash_command)
            subprocess.Popen(args, shell=False)
            time.sleep(5)  # Wait for the application to launch
        except Exception as e:
            raise ToolError(f"Failed to launch application: {str(e)}")

    return cli_mcp
