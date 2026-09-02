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
import signal
import shlex
import asyncio
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)
from fastmcp import FastMCP
from pydantic import Field
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security: transport-level DNS-rebinding defense (CWE-346)
#
# The server binds to localhost, but localhost binding alone does NOT protect
# against DNS-rebinding: a browser page on an attacker-controlled domain can
# rebind its DNS record to 127.0.0.1 and issue same-origin ``fetch()`` calls
# to this server. Such requests carry a non-local ``Host`` header (and usually
# an ``Origin``/``Sec-Fetch-Site`` header). We reject anything whose Host or
# Origin is not local, before the request ever reaches a tool.
# ---------------------------------------------------------------------------
ALLOWED_LOCAL_HOSTS: FrozenSet[str] = frozenset({"localhost", "127.0.0.1", "::1"})


def _extract_hostname(host_header: str) -> str:
    """Return the bare hostname from a Host/Origin value, stripping any port.

    Handles IPv6 literals such as ``[::1]:8010`` and ``[::1]`` as well as the
    usual ``host`` / ``host:port`` forms.
    """
    host = host_header.strip()
    if not host:
        return ""
    if host.startswith("["):
        # IPv6 literal: [::1]:8010 or [::1]
        end = host.find("]")
        if end != -1:
            return host[1:end]
        return host
    # IPv4 / hostname: strip :port if present
    return host.rsplit(":", 1)[0] if ":" in host else host


class LocalhostGuardMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Host/Origin is not local (DNS-rebinding defense).

    A non-browser client such as the UFO CLI sends a local ``Host`` header and
    no ``Origin``/``Sec-Fetch-*`` headers, so it passes unaffected. A browser
    page abusing DNS rebinding sends the attacker's domain in ``Host`` and an
    explicit cross-site ``Origin``/``Sec-Fetch-Site``, all of which are
    rejected here with HTTP 403.
    """

    async def dispatch(self, request: Request, call_next):
        # --- Host header must resolve to a local name ---
        raw_host = request.headers.get("host", "")
        if _extract_hostname(raw_host) not in ALLOWED_LOCAL_HOSTS:
            logger.warning("Rejected request with non-local Host header: %r", raw_host)
            return JSONResponse(
                {"error": "Forbidden: invalid Host header."}, status_code=403
            )

        # --- Origin, when present, must be local (rejects cross-origin fetch) ---
        origin = request.headers.get("origin")
        if origin:
            origin_host = _extract_hostname(origin.split("://", 1)[-1])
            if origin_host not in ALLOWED_LOCAL_HOSTS:
                logger.warning("Rejected cross-origin request: Origin=%r", origin)
                return JSONResponse(
                    {"error": "Forbidden: cross-origin request rejected."},
                    status_code=403,
                )

        # --- Reject browser requests explicitly flagged as cross-site ---
        sec_fetch_site = request.headers.get("sec-fetch-site")
        if sec_fetch_site and sec_fetch_site not in ("same-origin", "none"):
            logger.warning(
                "Rejected request with Sec-Fetch-Site=%r", sec_fetch_site
            )
            return JSONResponse(
                {"error": "Forbidden: cross-site request rejected."},
                status_code=403,
            )

        return await call_next(request)

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

TRUSTED_EXECUTABLE_DIRS: Tuple[Path, ...] = (
    Path("/usr/bin"),
    Path("/bin"),
)
MAX_COMMAND_OUTPUT_BYTES = 1_000_000
_USE_PROCESS_GROUPS = os.name == "posix"

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


def _check_python_args(args: List[str]) -> bool:
    """
    Argument policy for the ``python`` / ``python3`` interpreters.

    Allow only fixed version-reporting forms (``--version`` / ``-V``).
    Reject any flag that causes the interpreter to execute
    caller-controlled code (``-c``, ``-m``, reading a script from a path
    or from stdin via ``-``), which would bypass the read-only allow-list.
    """
    # Bare ``python3`` (REPL) is interactive and serves no read-only purpose.
    if not args:
        return False
    # Only the version-reporting forms are permitted.
    return all(arg in ("--version", "-V") for arg in args)


def _check_find_args(args: List[str]) -> bool:
    """
    Argument policy for ``find``.

    Block actions that execute commands or write to the filesystem.
    ``-exec`` / ``-execdir`` are already blocked by the dangerous-pattern
    scan; this also rejects other side-effecting actions such as
    ``-delete`` and the ``-f*`` file-writing primaries.
    """
    blocked_actions = {
        "-exec",
        "-execdir",
        "-delete",
        "-ok",
        "-okdir",
        "-fprint",
        "-fprint0",
        "-fprintf",
        "-fls",
    }
    return not any(arg in blocked_actions for arg in args)


def _allow_unrestricted_args(args: List[str]) -> bool:
    """Allow arguments for commands with no known mutating options."""
    return True


def _is_long_option_prefix(arg: str, option: str) -> bool:
    """Return whether *arg* is a GNU-style abbreviation of *option*."""
    option_name = arg.split("=", 1)[0]
    return (
        option_name.startswith("--")
        and len(option_name) > 2
        and option.startswith(option_name)
    )


def _check_date_args(args: List[str]) -> bool:
    """Allow only GNU date forms that report information."""
    reporting_options = {
        "-u",
        "--utc",
        "--universal",
        "-R",
        "--rfc-email",
        "--resolution",
        "--debug",
        "--help",
        "--version",
        "-I",
        "--iso-8601",
    }
    reporting_value_options = (
        "--date=",
        "--file=",
        "--reference=",
        "--iso-8601=",
        "--rfc-3339=",
    )
    return all(
        arg in reporting_options
        or arg.startswith("+")
        or (arg.startswith("-I") and not arg.startswith("--"))
        or arg.startswith(reporting_value_options)
        for arg in args
    )


def _check_hostname_args(args: List[str]) -> bool:
    """Allow only hostname's information-reporting options."""
    reporting_options = {
        "-a",
        "--alias",
        "-A",
        "--all-fqdns",
        "-d",
        "--domain",
        "-f",
        "--fqdn",
        "--long",
        "-i",
        "--ip-address",
        "-I",
        "--all-ip-addresses",
        "-s",
        "--short",
        "-y",
        "--yp",
        "--nis",
        "--help",
        "--version",
    }
    return all(arg in reporting_options for arg in args)


def _check_file_args(args: List[str]) -> bool:
    """Reject file options that write files or launch decompressors."""
    dangerous_long_options = (
        "--compile",
        "--no-sandbox",
        "--uncompress",
        "--uncompress-noreport",
    )
    for arg in args:
        if any(
            _is_long_option_prefix(arg, option)
            for option in dangerous_long_options
        ):
            return False
        if (
            arg.startswith("-")
            and not arg.startswith("--")
            and any(option in arg[1:] for option in "CSzZ")
        ):
            return False
    return True


def _check_diff_args(args: List[str]) -> bool:
    """Reject diff options that write output to a file."""
    return not any(
        (arg.startswith("-o") and not arg.startswith("--"))
        or _is_long_option_prefix(arg, "--output")
        for arg in args
    )


def _check_uniq_args(args: List[str]) -> bool:
    """Allow at most one input operand so uniq cannot write an output file."""
    value_options = {
        "--check-chars",
        "--skip-chars",
        "--skip-fields",
    }
    operand_count = 0
    consume_option_value = False
    parse_options = True

    for arg in args:
        if consume_option_value:
            consume_option_value = False
            continue
        if parse_options and arg == "--":
            parse_options = False
            continue
        if parse_options and arg.startswith("--"):
            option_name, has_separator, _ = arg.partition("=")
            if _is_long_option_prefix(arg, "--output"):
                return False
            if option_name in value_options and not has_separator:
                consume_option_value = True
            continue
        if parse_options and arg.startswith("-") and arg != "-":
            short_options = arg[1:]
            for index, option in enumerate(short_options):
                if option in "fsw":
                    consume_option_value = index == len(short_options) - 1
                    break
            continue

        operand_count += 1
        if operand_count > 1:
            return False

    return True


_ARGUMENT_POLICIES: Dict[str, Callable[[List[str]], bool]] = {
    "ls": _allow_unrestricted_args,
    "pwd": _allow_unrestricted_args,
    "cat": _allow_unrestricted_args,
    "head": _allow_unrestricted_args,
    "tail": _allow_unrestricted_args,
    "grep": _allow_unrestricted_args,
    "find": _check_find_args,
    "which": _allow_unrestricted_args,
    "whereis": _allow_unrestricted_args,
    "wc": _allow_unrestricted_args,
    "uniq": _check_uniq_args,
    "cut": _allow_unrestricted_args,
    "tr": _allow_unrestricted_args,
    "uname": _allow_unrestricted_args,
    "hostname": _check_hostname_args,
    "whoami": _allow_unrestricted_args,
    "id": _allow_unrestricted_args,
    "uptime": _allow_unrestricted_args,
    "free": _allow_unrestricted_args,
    "df": _allow_unrestricted_args,
    "du": _allow_unrestricted_args,
    "ps": _allow_unrestricted_args,
    "ping": _allow_unrestricted_args,
    "traceroute": _allow_unrestricted_args,
    "nslookup": _allow_unrestricted_args,
    "dig": _allow_unrestricted_args,
    "host": _allow_unrestricted_args,
    "file": _check_file_args,
    "stat": _allow_unrestricted_args,
    "md5sum": _allow_unrestricted_args,
    "sha256sum": _allow_unrestricted_args,
    "python": _check_python_args,
    "python3": _check_python_args,
    "echo": _allow_unrestricted_args,
    "date": _check_date_args,
    "cal": _allow_unrestricted_args,
    "basename": _allow_unrestricted_args,
    "dirname": _allow_unrestricted_args,
    "realpath": _allow_unrestricted_args,
    "diff": _check_diff_args,
    "test": _allow_unrestricted_args,
}


def _tokenize(command_str: str) -> Optional[List[str]]:
    """Return the full token list for *command_str* or ``None`` if malformed."""
    stripped = command_str.strip()
    if not stripped:
        return None
    try:
        tokens = shlex.split(stripped)
        return tokens or None
    except ValueError:
        # Malformed shell quoting
        return None


def _extract_base_command(command_str: str) -> Optional[str]:
    """Return the first token (base command) from *command_str*."""
    tokens = _tokenize(command_str)
    return tokens[0] if tokens else None


def _is_command_allowed(command_str: str) -> bool:
    """
    Validate *command_str* against the allow-list **and** dangerous patterns.

    Returns ``True`` only when the base command is in
    ``ALLOWED_SHELL_COMMANDS``, no dangerous pattern is found, **and** any
    per-command argument policy (e.g. for interpreters) is satisfied.
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

    tokens = _tokenize(command_str)
    if not tokens:
        return False

    base_name = tokens[0]

    if "/" in base_name:
        logger.warning("Blocked path-qualified command: %s", base_name)
        return False

    if base_name not in ALLOWED_SHELL_COMMANDS:
        logger.warning("Blocked command not in allow-list: %s", base_name)
        return False

    # Enforce per-command argument policy (defends interpreters such as
    # ``python3 -c`` from turning read-only access into code execution).
    policy = _ARGUMENT_POLICIES.get(base_name)
    if policy is None:
        logger.error("Blocked command with no argument policy: %s", base_name)
        return False
    if not policy(tokens[1:]):
        logger.warning(
            "Blocked command failing argument policy for %s: %s",
            base_name,
            command_str[:200],
        )
        return False

    return True


def _resolve_allowed_executables(
    command_names: FrozenSet[str] = ALLOWED_SHELL_COMMANDS,
    trusted_directories: Sequence[Path] = TRUSTED_EXECUTABLE_DIRS,
) -> Dict[str, Path]:
    """Resolve available commands only from trusted system directories."""
    trusted_roots: List[Path] = []
    for directory in trusted_directories:
        try:
            resolved_directory = directory.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if resolved_directory.is_dir() and resolved_directory not in trusted_roots:
            trusted_roots.append(resolved_directory)

    executable_paths: Dict[str, Path] = {}
    for command_name in command_names:
        for trusted_root in trusted_roots:
            try:
                candidate = (trusted_root / command_name).resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            if trusted_root not in candidate.parents:
                logger.warning(
                    "Ignored executable outside trusted directories: %s",
                    candidate,
                )
                continue
            if candidate.is_file() and os.access(candidate, os.X_OK):
                executable_paths[command_name] = candidate
                break

    return executable_paths


class _OutputLimitExceeded(Exception):
    pass


class _OutputBudget:
    def __init__(self, limit: int) -> None:
        self.remaining = max(limit, 0)

    def consume(self, size: int) -> None:
        if size > self.remaining:
            raise _OutputLimitExceeded
        self.remaining -= size


async def _read_stream_limited(
    stream: asyncio.StreamReader, budget: _OutputBudget
) -> bytes:
    chunks: List[bytes] = []
    while True:
        chunk = await stream.read(min(65_536, budget.remaining + 1))
        if not chunk:
            return b"".join(chunks)
        budget.consume(len(chunk))
        chunks.append(chunk)


async def _terminate_process(proc) -> None:
    if proc.returncode is not None:
        return
    process_id = getattr(proc, "pid", None)
    if _USE_PROCESS_GROUPS and process_id is not None:
        try:
            os.killpg(process_id, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError:
            if proc.returncode is None:
                proc.kill()
    elif proc.returncode is None:
        proc.kill()
    if proc.returncode is None:
        await proc.wait()


async def _cleanup_execution(proc, execution_tasks: Sequence[asyncio.Task]) -> None:
    for task in execution_tasks:
        task.cancel()
    await _terminate_process(proc)
    await asyncio.gather(*execution_tasks, return_exceptions=True)


async def _shielded_cleanup(
    proc, execution_tasks: Sequence[asyncio.Task]
) -> None:
    cleanup_task = asyncio.create_task(
        _cleanup_execution(proc, execution_tasks)
    )
    try:
        await asyncio.shield(cleanup_task)
    except asyncio.CancelledError:
        try:
            await cleanup_task
        finally:
            raise


async def _execute_allowed_command(
    command: str,
    timeout: int,
    cwd: Optional[str],
    executable_paths: Mapping[str, Path],
    output_limit: int = MAX_COMMAND_OUTPUT_BYTES,
) -> Dict[str, Any]:
    """Execute a validated command using its pinned trusted executable."""
    tokens = _tokenize(command)
    if not tokens:
        return {"success": False, "error": "Malformed command."}

    executable = executable_paths.get(tokens[0])
    if executable is None:
        return {
            "success": False,
            "error": "Command executable is unavailable in trusted directories.",
        }

    try:
        proc = await asyncio.create_subprocess_exec(
            str(executable),
            *tokens[1:],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            start_new_session=_USE_PROCESS_GROUPS,
        )
        output_budget = _OutputBudget(output_limit)
        stdout_task = asyncio.create_task(
            _read_stream_limited(proc.stdout, output_budget)
        )
        stderr_task = asyncio.create_task(
            _read_stream_limited(proc.stderr, output_budget)
        )
        wait_task = asyncio.create_task(proc.wait())
        execution_tasks = (stdout_task, stderr_task, wait_task)
        try:
            stdout, stderr, _ = await asyncio.wait_for(
                asyncio.gather(*execution_tasks), timeout=timeout
            )
        except asyncio.TimeoutError:
            await _shielded_cleanup(proc, execution_tasks)
            return {"success": False, "error": f"Timeout after {timeout}s."}
        except _OutputLimitExceeded:
            await _shielded_cleanup(proc, execution_tasks)
            return {
                "success": False,
                "error": (
                    f"Command output exceeded the {output_limit}-byte limit."
                ),
            }
        except asyncio.CancelledError:
            await _shielded_cleanup(proc, execution_tasks)
            raise
        except Exception as e:
            await _shielded_cleanup(proc, execution_tasks)
            return {"success": False, "error": str(e)}
        return {
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _collect_system_info(
    executable_paths: Mapping[str, Path], timeout: int
) -> Dict[str, str]:
    """Collect fixed system details through pinned trusted executables."""
    commands = {
        "uname": "uname -a",
        "uptime": "uptime",
        "memory": "free -h",
        "disk": "df -h",
    }
    info: Dict[str, str] = {}
    for key, command in commands.items():
        result = await _execute_allowed_command(
            command,
            timeout=timeout,
            cwd=None,
            executable_paths=executable_paths,
        )
        if "stdout" in result:
            info[key] = result["stdout"].strip()
        else:
            info[key] = f"Error: {result.get('error', 'Command failed.')}"
    return info


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
    executable_paths = _resolve_allowed_executables()
    unavailable_commands = sorted(
        ALLOWED_SHELL_COMMANDS.difference(executable_paths)
    )
    if unavailable_commands:
        logger.warning(
            "Allow-listed commands unavailable in trusted directories: %s",
            ", ".join(unavailable_commands),
        )
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

        return await _execute_allowed_command(
            command,
            timeout=timeout,
            cwd=validated_cwd,
            executable_paths=executable_paths,
        )

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

        return await _collect_system_info(executable_paths, timeout=30)

    # Enforce transport-level Host/Origin validation to defeat DNS rebinding.
    mcp.run(
        transport="streamable-http",
        middleware=[Middleware(LocalhostGuardMiddleware)],
    )


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
