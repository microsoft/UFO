# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import logging
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Type

from ufo.automator.basic import CommandBasic, ReceiverBasic

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security: command allow-list for run_shell / execute_command
# Only these base commands may be executed.  Extend as needed.
# ---------------------------------------------------------------------------
ALLOWED_SHELL_COMMANDS: FrozenSet[str] = frozenset(
    {
        "Get-ChildItem",
        "Get-Content",
        "Get-Item",
        "Get-ItemProperty",
        "Get-Location",
        "Get-Process",
        "Get-Service",
        "Set-Location",
        "Select-Object",
        "Select-String",
        "Where-Object",
        "Sort-Object",
        "Format-Table",
        "Format-List",
        "Out-String",
        "Write-Output",
        "Test-Path",
        "Measure-Object",
        "ConvertTo-Json",
        "ConvertFrom-Json",
        # Common external utilities (read-only / benign)
        "dir",
        "type",
        "find",
        "findstr",
        "where",
        "echo",
        "hostname",
        "whoami",
        "ipconfig",
        "ping",
        "tracert",
        "nslookup",
        "systeminfo",
        "tasklist",
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
]

# Environment variables that must never be read or written by the LLM
_SENSITIVE_ENV_PATTERNS: List[re.Pattern] = [
    re.compile(r"(SECRET|TOKEN|PASSWORD|CREDENTIAL|KEY|PRIVATE)", re.IGNORECASE),
    re.compile(r"^(AWS_|AZURE_|GCP_|GOOGLE_)", re.IGNORECASE),
    re.compile(r"^(DATABASE_URL|DB_PASS|OPENAI_API_KEY)", re.IGNORECASE),
    re.compile(r"^(SSH_AUTH_SOCK|GPG_)", re.IGNORECASE),
]

# Maximum number of bytes that can be read from a single file
_MAX_READ_BYTES: int = 10 * 1024 * 1024  # 10 MB


def _extract_base_command(command_str: str) -> Optional[str]:
    """Extract the first token (base command) from a command string."""
    stripped = command_str.strip()
    if not stripped:
        return None
    # Strip leading & (PowerShell call operator)
    if stripped.startswith("&"):
        stripped = stripped[1:].strip()
    # Take the first whitespace-delimited token
    return stripped.split()[0] if stripped else None


def _is_command_allowed(command_str: str) -> bool:
    """
    Validate a command string against the allow-list and dangerous patterns.
    Returns True only if the base command is in the allow-list AND no
    dangerous patterns are detected.
    """
    if not command_str or not command_str.strip():
        return False

    base = _extract_base_command(command_str)
    if base is None:
        return False

    # Check base command against allow-list (case-insensitive)
    if not any(base.lower() == allowed.lower() for allowed in ALLOWED_SHELL_COMMANDS):
        logger.warning("Blocked shell command not in allow-list: %s", base)
        return False

    # Check for dangerous patterns
    for pattern in _DANGEROUS_PATTERNS:
        if pattern.search(command_str):
            logger.warning(
                "Blocked shell command matching dangerous pattern %s: %s",
                pattern.pattern,
                command_str[:200],
            )
            return False

    return True


def _is_env_var_sensitive(name: str) -> bool:
    """Return True if the environment variable name looks sensitive."""
    for pattern in _SENSITIVE_ENV_PATTERNS:
        if pattern.search(name):
            return True
    return False


def _validate_path(path_str: str, base_directory: str) -> str:
    """
    Resolve *path_str* and ensure it stays within *base_directory*.
    Raises ValueError on path-traversal attempts.
    Returns the resolved absolute path as a string.
    """
    base = Path(base_directory).resolve()
    resolved = (base / path_str).resolve() if not Path(path_str).is_absolute() else Path(path_str).resolve()

    if not (str(resolved).startswith(str(base) + os.sep) or resolved == base):
        raise ValueError(
            f"Path '{path_str}' resolves outside the allowed base directory '{base}'"
        )
    return str(resolved)


class ShellReceiver(ReceiverBasic):
    """
    The base class for shell command execution with security hardening.
    """

    _command_registry: Dict[str, Type[ShellCommand]] = {}

    def __init__(self, base_directory: Optional[str] = None) -> None:
        """
        Initialize the shell client.
        :param base_directory: The root directory that all filesystem
            operations are confined to.  Defaults to os.getcwd().
        """
        self.base_directory = os.path.abspath(base_directory or os.getcwd())
        self.current_directory = self.base_directory

    def run_shell(self, params: Dict[str, Any]) -> Any:
        """
        Run an allow-listed command.  The command string is validated against
        ``ALLOWED_SHELL_COMMANDS`` and scanned for dangerous patterns before
        execution.  ``shell=True`` is **not** used.
        :param params: The parameters of the command.
        :return: The result content.
        """
        command = params.get("command", "")
        timeout = params.get("timeout", 30)
        # Cap timeout to a sane maximum (120 s)
        timeout = min(max(int(timeout), 1), 120)

        if not _is_command_allowed(command):
            return {
                "error": "Command blocked by security policy. "
                "Only allow-listed commands may be executed.",
                "command": command,
            }

        powershell_path = (
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        )

        try:
            # Use shell=False with an explicit argument list.
            # PowerShell's -NoProfile -NonInteractive flags prevent profile
            # scripts from running and ensure no interactive prompts.
            process = subprocess.Popen(
                [
                    powershell_path,
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    command,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                text=True,
                cwd=self.current_directory,
            )

            stdout, stderr = process.communicate(timeout=timeout)
            return {
                "stdout": stdout,
                "stderr": stderr,
                "return_code": process.returncode,
                "command": command,
            }

        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "error": f"Command timed out after {timeout} seconds",
                "command": command,
            }
        except Exception as e:
            return {
                "error": f"Command execution failed: {str(e)}",
                "command": command,
            }

    def execute_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command with advanced options.
        The command is validated against the allow-list.
        LLM-supplied ``env_vars`` and ``shell`` parameters are **ignored**
        to prevent environment manipulation and shell injection.
        """
        command = params.get("command", "")
        args = params.get("args", [])
        # LLM-supplied env_vars are ignored for security
        # LLM-supplied shell flag is ignored — always False

        if not _is_command_allowed(command):
            return {
                "error": "Command blocked by security policy. "
                "Only allow-listed commands may be executed.",
                "command": command,
            }

        try:
            if args:
                # Ensure args are all strings
                cmd = [str(command)] + [str(a) for a in args]
            else:
                cmd = shlex.split(command)

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                text=True,
                cwd=self.current_directory,
            )

            stdout, stderr = process.communicate(timeout=120)
            return {
                "stdout": stdout,
                "stderr": stderr,
                "return_code": process.returncode,
                "command": str(cmd),
            }
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "error": "Command timed out after 120 seconds",
                "command": str(command),
            }
        except Exception as e:
            return {
                "error": f"Command execution failed: {str(e)}",
                "command": str(command),
            }

    def change_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Change the current working directory (confined to base_directory).
        """
        path = params.get("path", "")
        try:
            safe_path = _validate_path(path, self.base_directory)
            if not os.path.isdir(safe_path):
                return {"error": f"Directory does not exist: {path}"}
            self.current_directory = safe_path
            return {"success": True, "new_directory": self.current_directory}
        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
            return {"error": f"Failed to change directory: {str(e)}"}

    def get_current_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the current working directory.
        """
        try:
            current_dir = os.getcwd()
            self.current_directory = current_dir
            return {"current_directory": current_dir}
        except Exception as e:
            return {"error": f"Failed to get current directory: {str(e)}"}

    def list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List files and directories in a path (confined to base_directory).
        """
        path = params.get("path", self.current_directory)
        show_hidden = params.get("show_hidden", False)
        long_format = params.get("long_format", False)
        
        try:
            safe_path = _validate_path(path, self.base_directory)
            if not os.path.exists(safe_path):
                return {"error": f"Path does not exist: {path}"}
                
            items = []
            for item in os.listdir(safe_path):
                if not show_hidden and item.startswith('.'):
                    continue
                    
                item_path = os.path.join(safe_path, item)
                if long_format:
                    stat = os.stat(item_path)
                    items.append({
                        "name": item,
                        "type": "directory" if os.path.isdir(item_path) else "file",
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    })
                else:
                    items.append({
                        "name": item,
                        "type": "directory" if os.path.isdir(item_path) else "file"
                    })
            
            return {"path": safe_path, "items": items}
        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
            return {"error": f"Failed to list files: {str(e)}"}

    def create_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new directory (confined to base_directory).
        """
        path = params.get("path", "")
        parents = params.get("parents", False)
        
        try:
            safe_path = _validate_path(path, self.base_directory)
            if parents:
                os.makedirs(safe_path, exist_ok=True)
            else:
                os.mkdir(safe_path)
            return {"success": True, "directory_created": safe_path}
        except ValueError as ve:
            return {"error": str(ve)}
        except FileExistsError:
            return {"error": f"Directory already exists: {path}"}
        except Exception as e:
            return {"error": f"Failed to create directory: {str(e)}"}

    def remove_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove a file or directory (confined to base_directory).
        Recursive deletion is **disabled** to prevent mass data loss.
        """
        path = params.get("path", "")
        # 'recursive' and 'force' flags are intentionally ignored for safety.
        
        try:
            safe_path = _validate_path(path, self.base_directory)
            if not os.path.exists(safe_path):
                return {"error": f"Path does not exist: {path}"}

            # Prevent deleting the base directory itself
            if Path(safe_path).resolve() == Path(self.base_directory).resolve():
                return {"error": "Cannot remove the base working directory"}

            if os.path.isdir(safe_path):
                os.rmdir(safe_path)  # Only empty directories
            else:
                os.remove(safe_path)
                
            return {"success": True, "removed": safe_path}
        except ValueError as ve:
            return {"error": str(ve)}
        except OSError as e:
            return {"error": f"Failed to remove: {str(e)}"}

    def copy_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Copy a file (confined to base_directory). Directory copy is disabled.
        """
        source = params.get("source", "")
        destination = params.get("destination", "")
        
        try:
            import shutil
            safe_src = _validate_path(source, self.base_directory)
            safe_dst = _validate_path(destination, self.base_directory)
            if os.path.isdir(safe_src):
                return {"error": "Recursive directory copy is not permitted"}
            shutil.copy2(safe_src, safe_dst)
            return {"success": True, "copied_from": safe_src, "copied_to": safe_dst}
        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
            return {"error": f"Failed to copy: {str(e)}"}

    def move_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Move or rename a file or directory (confined to base_directory).
        """
        source = params.get("source", "")
        destination = params.get("destination", "")
        
        try:
            import shutil
            safe_src = _validate_path(source, self.base_directory)
            safe_dst = _validate_path(destination, self.base_directory)
            shutil.move(safe_src, safe_dst)
            return {"success": True, "moved_from": safe_src, "moved_to": safe_dst}
        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
            return {"error": f"Failed to move: {str(e)}"}

    def read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read the contents of a text file (confined to base_directory, size-limited).
        """
        file_path = params.get("file_path", "")
        encoding = params.get("encoding", "utf-8")
        
        try:
            safe_path = _validate_path(file_path, self.base_directory)
            file_size = os.path.getsize(safe_path)
            if file_size > _MAX_READ_BYTES:
                return {
                    "error": f"File too large ({file_size} bytes). "
                    f"Maximum allowed is {_MAX_READ_BYTES} bytes.",
                }
            with open(safe_path, 'r', encoding=encoding) as file:
                content = file.read()
            return {"file_path": safe_path, "content": content, "encoding": encoding}
        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    def write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write content to a text file (confined to base_directory).
        """
        file_path = params.get("file_path", "")
        content = params.get("content", "")
        append = params.get("append", False)
        encoding = params.get("encoding", "utf-8")
        
        try:
            safe_path = _validate_path(file_path, self.base_directory)
            mode = 'a' if append else 'w'
            with open(safe_path, mode, encoding=encoding) as file:
                file.write(content)
            return {"success": True, "file_path": safe_path, "mode": mode}
        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
            return {"error": f"Failed to write file: {str(e)}"}

    def check_file_exists(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a file or directory exists (confined to base_directory).
        """
        path = params.get("path", "")
        try:
            safe_path = _validate_path(path, self.base_directory)
            exists = os.path.exists(safe_path)
            return {
                "path": safe_path,
                "exists": exists,
                "is_file": os.path.isfile(safe_path) if exists else None,
                "is_directory": os.path.isdir(safe_path) if exists else None,
            }
        except ValueError as ve:
            return {"error": str(ve)}

    def get_file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get information about a file or directory (confined to base_directory).
        """
        path = params.get("path", "")
        
        try:
            safe_path = _validate_path(path, self.base_directory)
            if not os.path.exists(safe_path):
                return {"error": f"Path does not exist: {path}"}
                
            stat = os.stat(safe_path)
            return {
                "path": safe_path,
                "type": "directory" if os.path.isdir(safe_path) else "file",
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
            }
        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
            return {"error": f"Failed to get file info: {str(e)}"}

    def find_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find files matching a pattern (confined to base_directory).
        """
        pattern = params.get("pattern", "")
        directory = params.get("directory", self.current_directory)
        recursive = params.get("recursive", True)
        
        try:
            safe_dir = _validate_path(directory, self.base_directory)

            # Reject patterns that attempt path traversal
            if ".." in pattern or pattern.startswith("/") or pattern.startswith("\\"):
                return {"error": "Invalid search pattern"}

            import glob
            if recursive:
                search_pattern = os.path.join(safe_dir, "**", pattern)
                matches = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = os.path.join(safe_dir, pattern)
                matches = glob.glob(search_pattern)

            # Filter results to ensure all are within base_directory
            base = str(Path(self.base_directory).resolve())
            matches = [
                m for m in matches
                if str(Path(m).resolve()).startswith(base + os.sep)
                or str(Path(m).resolve()) == base
            ]
                
            return {
                "pattern": pattern,
                "directory": safe_dir,
                "matches": matches,
                "count": len(matches),
            }
        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
            return {"error": f"Failed to find files: {str(e)}"}

    def get_environment_variable(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the value of a non-sensitive environment variable.
        """
        name = params.get("name", "")
        if _is_env_var_sensitive(name):
            logger.warning("Blocked read of sensitive env var: %s", name)
            return {
                "error": f"Access to environment variable '{name}' is blocked "
                "by security policy (sensitive variable).",
            }
        value = os.environ.get(name)
        return {
            "variable_name": name,
            "value": value,
            "exists": value is not None,
        }

    def set_environment_variable(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set an environment variable.
        Sensitive variables (secrets, tokens, keys) are blocked.
        """
        name = params.get("name", "")
        value = params.get("value", "")
        
        if _is_env_var_sensitive(name):
            logger.warning("Blocked write to sensitive env var: %s", name)
            return {
                "error": f"Modification of environment variable '{name}' is "
                "blocked by security policy (sensitive variable).",
            }
        try:
            os.environ[name] = str(value)
            return {"success": True, "variable_name": name}
        except Exception as e:
            return {"error": f"Failed to set environment variable: {str(e)}"}

    def get_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get system information.
        """
        info_type = params.get("info_type", "all")
        
        try:
            import platform
            import psutil
            
            info = {}
            
            if info_type in ["os", "all"]:
                info["os"] = {
                    "system": platform.system(),
                    "release": platform.release(), 
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor()
                }
            
            if info_type in ["cpu", "all"]:
                info["cpu"] = {
                    "count": psutil.cpu_count(),
                    "usage_percent": psutil.cpu_percent(interval=1),
                    "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                }
            
            if info_type in ["memory", "all"]:
                memory = psutil.virtual_memory()
                info["memory"] = {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percentage": memory.percent
                }
            
            if info_type in ["disk", "all"]:
                disk = psutil.disk_usage('/')
                info["disk"] = {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percentage": (disk.used / disk.total) * 100
                }
            
            if info_type in ["network", "all"]:
                network = psutil.net_io_counters()
                info["network"] = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_received": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_received": network.packets_recv
                }
            
            return {"info_type": info_type, "system_info": info}
            
        except ImportError:
            return {"error": "psutil library not available for system info"}
        except Exception as e:
            return {"error": f"Failed to get system info: {str(e)}"}


class ShellCommand(CommandBasic):
    """
    The base class for Web commands.
    """

    def __init__(self, receiver: ShellReceiver, params: Dict[str, Any]) -> None:
        """
        Initialize the Web command.
        :param receiver: The receiver of the command.
        :param params: The parameters of the command.
        """
        super().__init__(receiver, params)
        self.receiver = receiver
        self.params = params

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "shell"


@ShellReceiver.register
class RunShellCommand(ShellCommand):
    """
    The command to run the crawler with various options.
    """

    def execute(self):
        """
        Execute the command to run the crawler.
        :return: The result content.
        """
        return self.receiver.run_shell(params=self.params)

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "run_shell"


@ShellReceiver.register
class ExecuteCommand(ShellCommand):
    """
    The command to execute a given command with arguments and options.
    """

    def execute(self):
        """
        Execute the command with advanced options.
        :return: The result of the command execution.
        """
        return self.receiver.execute_command(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "execute_command"


@ShellReceiver.register
class ChangeDirectoryCommand(ShellCommand):
    """
    The command to change the current working directory.
    """

    def execute(self):
        """
        Execute the command to change the directory.
        :return: The result of the directory change.
        """
        return self.receiver.change_directory(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "change_directory"


@ShellReceiver.register
class GetCurrentDirectoryCommand(ShellCommand):
    """
    The command to get the current working directory.
    """

    def execute(self):
        """
        Execute the command to get the current directory.
        :return: The current directory path.
        """
        return self.receiver.get_current_directory(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "get_current_directory"


@ShellReceiver.register
class ListFilesCommand(ShellCommand):
    """
    The command to list files and directories in a given path.
    """

    def execute(self):
        """
        Execute the command to list files.
        :return: The list of files and directories.
        """
        return self.receiver.list_files(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "list_files"


@ShellReceiver.register
class CreateDirectoryCommand(ShellCommand):
    """
    The command to create a new directory.
    """

    def execute(self):
        """
        Execute the command to create a directory.
        :return: The result of the directory creation.
        """
        return self.receiver.create_directory(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "create_directory"


@ShellReceiver.register
class RemoveFileCommand(ShellCommand):
    """
    The command to remove a file or directory.
    """

    def execute(self):
        """
        Execute the command to remove a file or directory.
        :return: The result of the removal operation.
        """
        return self.receiver.remove_file(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "remove_file"


@ShellReceiver.register
class CopyFileCommand(ShellCommand):
    """
    The command to copy a file or directory to another location.
    """

    def execute(self):
        """
        Execute the command to copy a file or directory.
        :return: The result of the copy operation.
        """
        return self.receiver.copy_file(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "copy_file"


@ShellReceiver.register
class MoveFileCommand(ShellCommand):
    """
    The command to move or rename a file or directory.
    """

    def execute(self):
        """
        Execute the command to move a file or directory.
        :return: The result of the move operation.
        """
        return self.receiver.move_file(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "move_file"


@ShellReceiver.register
class ReadFileCommand(ShellCommand):
    """
    The command to read the contents of a text file.
    """

    def execute(self):
        """
        Execute the command to read a file.
        :return: The content of the file.
        """
        return self.receiver.read_file(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "read_file"


@ShellReceiver.register
class WriteFileCommand(ShellCommand):
    """
    The command to write content to a text file.
    """

    def execute(self):
        """
        Execute the command to write to a file.
        :return: The result of the write operation.
        """
        return self.receiver.write_file(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "write_file"


@ShellReceiver.register
class CheckFileExistsCommand(ShellCommand):
    """
    The command to check if a file or directory exists.
    """

    def execute(self):
        """
        Execute the command to check file existence.
        :return: The existence status of the file or directory.
        """
        return self.receiver.check_file_exists(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "check_file_exists"


@ShellReceiver.register
class GetFileInfoCommand(ShellCommand):
    """
    The command to get information about a file or directory.
    """

    def execute(self):
        """
        Execute the command to get file or directory information.
        :return: The information about the file or directory.
        """
        return self.receiver.get_file_info(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "get_file_info"


@ShellReceiver.register
class FindFilesCommand(ShellCommand):
    """
    The command to find files matching a pattern.
    """

    def execute(self):
        """
        Execute the command to find files.
        :return: The list of found files matching the pattern.
        """
        return self.receiver.find_files(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "find_files"


@ShellReceiver.register
class GetEnvironmentVariableCommand(ShellCommand):
    """
    The command to get the value of an environment variable.
    """

    def execute(self):
        """
        Execute the command to get an environment variable.
        :return: The value of the environment variable.
        """
        return self.receiver.get_environment_variable(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "get_environment_variable"


@ShellReceiver.register
class SetEnvironmentVariableCommand(ShellCommand):
    """
    The command to set an environment variable.
    """

    def execute(self):
        """
        Execute the command to set an environment variable.
        :return: The result of the set operation.
        """
        return self.receiver.set_environment_variable(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "set_environment_variable"


@ShellReceiver.register
class GetSystemInfoCommand(ShellCommand):
    """
    The command to get system information.
    """

    def execute(self):
        """
        Execute the command to get system information.
        :return: The system information data.
        """
        return self.receiver.get_system_info(params=self.params)
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "get_system_info"
