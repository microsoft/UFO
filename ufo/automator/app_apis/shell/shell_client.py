# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, Type

from ufo.automator.basic import CommandBasic, ReceiverBasic


class ShellReceiver(ReceiverBasic):
    """
    The base class for Web COM client using crawl4ai.
    """

    _command_registry: Dict[str, Type[ShellCommand]] = {}

    def __init__(self) -> None:
        """
        Initialize the shell client.
        """
        self.current_directory = os.getcwd()

    def run_shell(self, params: Dict[str, Any]) -> Any:
        """
        Run the command.
        :param params: The parameters of the command.
        :return: The result content.
        """
        command = params.get("command")
        working_directory = params.get("working_directory", self.current_directory)
        timeout = params.get("timeout", 30)
        capture_output = params.get("capture_output", True)
        
        try:
            if working_directory and os.path.exists(working_directory):
                original_dir = os.getcwd()
                os.chdir(working_directory)
            
            powershell_path = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe'
            process = subprocess.Popen(
                command,  
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                shell=True,
                text=True,
                executable=powershell_path,
            )
            
            if capture_output:
                stdout, stderr = process.communicate(timeout=timeout)
                if working_directory and os.path.exists(working_directory):
                    os.chdir(original_dir)
                return {
                    "stdout": stdout,
                    "stderr": stderr, 
                    "return_code": process.returncode,
                    "command": command
                }
            else:
                return {"message": "Command executed without output capture", "command": command}
                
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout} seconds", "command": command}
        except Exception as e:
            return {"error": f"Command execution failed: {str(e)}", "command": command}

    def execute_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command with advanced options.
        """
        command = params.get("command")
        args = params.get("args", [])
        shell = params.get("shell", True)
        env_vars = params.get("env_vars", {})
        
        try:
            env = os.environ.copy()
            env.update(env_vars)
            
            if args:
                cmd = [command] + args
            else:
                cmd = command
                
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=shell,
                text=True,
                env=env
            )
            
            stdout, stderr = process.communicate()
            return {
                "stdout": stdout,
                "stderr": stderr,
                "return_code": process.returncode,
                "command": str(cmd)
            }
        except Exception as e:
            return {"error": f"Command execution failed: {str(e)}", "command": str(command)}

    def change_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Change the current working directory.
        """
        path = params.get("path")
        try:
            if os.path.exists(path):
                os.chdir(path)
                self.current_directory = os.getcwd()
                return {"success": True, "new_directory": self.current_directory}
            else:
                return {"error": f"Directory does not exist: {path}"}
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
        List files and directories in a path.
        """
        path = params.get("path", self.current_directory)
        show_hidden = params.get("show_hidden", False)
        long_format = params.get("long_format", False)
        
        try:
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
                
            items = []
            for item in os.listdir(path):
                if not show_hidden and item.startswith('.'):
                    continue
                    
                item_path = os.path.join(path, item)
                if long_format:
                    stat = os.stat(item_path)
                    items.append({
                        "name": item,
                        "type": "directory" if os.path.isdir(item_path) else "file",
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "permissions": oct(stat.st_mode)[-3:]
                    })
                else:
                    items.append({
                        "name": item,
                        "type": "directory" if os.path.isdir(item_path) else "file"
                    })
            
            return {"path": path, "items": items}
        except Exception as e:
            return {"error": f"Failed to list files: {str(e)}"}

    def create_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new directory.
        """
        path = params.get("path")
        parents = params.get("parents", False)
        
        try:
            if parents:
                os.makedirs(path, exist_ok=True)
            else:
                os.mkdir(path)
            return {"success": True, "directory_created": path}
        except FileExistsError:
            return {"error": f"Directory already exists: {path}"}
        except Exception as e:
            return {"error": f"Failed to create directory: {str(e)}"}

    def remove_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove a file or directory.
        """
        path = params.get("path")
        recursive = params.get("recursive", False)
        force = params.get("force", False)
        
        try:
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
                
            if os.path.isdir(path):
                if recursive:
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.rmdir(path)
            else:
                os.remove(path)
                
            return {"success": True, "removed": path}
        except OSError as e:
            if force:
                return {"warning": f"Force removal failed: {str(e)}", "path": path}
            return {"error": f"Failed to remove: {str(e)}"}

    def copy_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Copy a file or directory.
        """
        source = params.get("source")
        destination = params.get("destination")
        recursive = params.get("recursive", False)
        
        try:
            import shutil
            if os.path.isdir(source):
                if recursive:
                    shutil.copytree(source, destination)
                else:
                    return {"error": "Source is directory but recursive=False"}
            else:
                shutil.copy2(source, destination)
                
            return {"success": True, "copied_from": source, "copied_to": destination}
        except Exception as e:
            return {"error": f"Failed to copy: {str(e)}"}

    def move_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Move or rename a file or directory.
        """
        source = params.get("source")
        destination = params.get("destination")
        
        try:
            import shutil
            shutil.move(source, destination)
            return {"success": True, "moved_from": source, "moved_to": destination}
        except Exception as e:
            return {"error": f"Failed to move: {str(e)}"}

    def read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read the contents of a text file.
        """
        file_path = params.get("file_path")
        encoding = params.get("encoding", "utf-8")
        
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            return {"file_path": file_path, "content": content, "encoding": encoding}
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    def write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write content to a text file.
        """
        file_path = params.get("file_path")
        content = params.get("content")
        append = params.get("append", False)
        encoding = params.get("encoding", "utf-8")
        
        try:
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding=encoding) as file:
                file.write(content)
            return {"success": True, "file_path": file_path, "mode": mode}
        except Exception as e:
            return {"error": f"Failed to write file: {str(e)}"}

    def check_file_exists(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a file or directory exists.
        """
        path = params.get("path")
        exists = os.path.exists(path)
        return {
            "path": path,
            "exists": exists,
            "is_file": os.path.isfile(path) if exists else None,
            "is_directory": os.path.isdir(path) if exists else None
        }

    def get_file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get information about a file or directory.
        """
        path = params.get("path")
        
        try:
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
                
            stat = os.stat(path)
            return {
                "path": path,
                "type": "directory" if os.path.isdir(path) else "file",
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "permissions": oct(stat.st_mode)[-3:],
                "owner": stat.st_uid,
                "group": stat.st_gid
            }
        except Exception as e:
            return {"error": f"Failed to get file info: {str(e)}"}

    def find_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find files matching a pattern.
        """
        pattern = params.get("pattern")
        directory = params.get("directory", self.current_directory)
        recursive = params.get("recursive", True)
        
        try:
            import glob
            if recursive:
                search_pattern = os.path.join(directory, "**", pattern)
                matches = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = os.path.join(directory, pattern)
                matches = glob.glob(search_pattern)
                
            return {
                "pattern": pattern,
                "directory": directory,
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            return {"error": f"Failed to find files: {str(e)}"}

    def get_environment_variable(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the value of an environment variable.
        """
        name = params.get("name")
        value = os.environ.get(name)
        return {
            "variable_name": name,
            "value": value,
            "exists": value is not None
        }

    def set_environment_variable(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set an environment variable.
        """
        name = params.get("name")
        value = params.get("value")
        
        try:
            os.environ[name] = value
            return {"success": True, "variable_name": name, "value": value}
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
