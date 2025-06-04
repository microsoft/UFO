#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
UFO MCP Server Launcher
Launches all UFO MCP servers for different applications.
"""

import os
import sys
import time
import subprocess
import argparse
import psutil
import requests
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from colorama import Fore, Style, init

# Add UFO2 to the path
ufo_root = os.path.dirname(os.path.abspath(__file__))
if ufo_root not in sys.path:
    sys.path.insert(0, ufo_root)

# Initialize colorama for Windows color support
init(autoreset=True)

# Colors for output
COLORS = {
    "SUCCESS": Fore.GREEN,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "INFO": Fore.CYAN,
    "DEBUG": Fore.MAGENTA,
    "RESET": Style.RESET_ALL,
}


class MCPServerLauncher:
    """
    Launcher for UFO MCP servers.
    """    
    def __init__(self, config_path=None, development=False, verbose=False):
        self.config_path = config_path
        self.development = development
        self.verbose = verbose
        self.processes = {}

        # Load configuration from files
        self.servers = {}
        self.startup_order = []
        self.launcher_config = {}
        self._load_configuration()
        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging configuration."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_level = logging.DEBUG if self.verbose else logging.INFO

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        self.logger = logging.getLogger(__name__)
        if self.verbose:
            self._print_colored("Verbose logging enabled", "DEBUG")

    def _print_colored(
        self, message: str, color: str = "INFO", no_newline: bool = False
    ):
        """Print colored output to console."""
        color_code = COLORS.get(color.upper(), Fore.WHITE)
        if no_newline:
            print(f"{color_code}{message}", end="")
        else:
            print(f"{color_code}{message}{Style.RESET_ALL}")
    
    def test_server_health(self, endpoint: str, health_endpoint: str = "/health", timeout: int = 5) -> bool:
        """
        Test if a server is healthy by checking its health endpoint.
        :param endpoint: Server endpoint URL
        :param health_endpoint: Health check endpoint path (for FastMCP, use /sse)
        :param timeout: Request timeout in seconds
        :return: True if server is healthy
        """
        try:
            # For FastMCP servers running with SSE transport, check the /sse endpoint
            if health_endpoint == "/health":
                health_endpoint = "/sse"
            
            health_url = f"{endpoint}{health_endpoint}"
            
            if self.verbose:
                self._print_colored(f"  Checking: {health_url}", "DEBUG")
            
            # For SSE endpoints, we need to handle streaming responses differently
            if health_endpoint == "/sse":
                # Use a short timeout and stream=True to avoid waiting for the full response
                response = requests.get(health_url, timeout=2, stream=True)
                
                # If we get a 200 response for SSE, the server is healthy
                # We don't need to read the content, just check the status
                if response.status_code == 200:
                    response.close()  # Close the streaming connection
                    return True
                    
                # Some SSE implementations return 404 for GET on SSE endpoint but server is still running
                elif response.status_code == 404:
                    # Try the root endpoint to see if server is responding
                    root_response = requests.get(endpoint, timeout=timeout)
                    return root_response.status_code in [200, 404, 405]  # Any response means server is up
            else:
                # For regular health endpoints
                response = requests.get(health_url, timeout=timeout)
                if response.status_code == 200:
                    return True
            
            return False
        except requests.exceptions.ConnectionError:
            # Server is not running or not reachable
            return False
        except requests.exceptions.Timeout:
            # For SSE endpoints, a timeout on the initial connection might mean server is not ready
            # But a timeout after getting headers could mean it's working (streaming response)
            if health_endpoint == "/sse":
                # Try a HEAD request to see if server responds quickly
                try:
                    head_response = requests.head(health_url, timeout=1)
                    return head_response.status_code in [200, 405]  # 405 means HEAD not allowed but server is up
                except:
                    return False
            return False
        except Exception as e:
            if self.verbose:
                self._print_colored(f"  Health check error: {e}", "DEBUG")
            return False
        
    def test_all_servers_health(self) -> bool:
        """
        Test health of all running servers.
        :return: True if all servers are healthy
        """
        self._print_colored("\nChecking server health...", "INFO")
        self._print_colored("─" * 50, "INFO")

        all_healthy = True

        for server_name, config in self.servers.items():
            # Build endpoint URL from configuration
            port = config.get("port", 8000)
            endpoint = f"http://localhost:{port}"
            
            # Get health check endpoint from MCP config if available
            health_endpoint = "/health"
            if "mcp_config" in config:
                health_endpoint = config["mcp_config"].get("health_check_endpoint", "/health")
            
            self._print_colored(
                f"{server_name.title()} ({endpoint}): ", "INFO", no_newline=True
            )

            if self.test_server_health(endpoint, health_endpoint):
                self._print_colored("✓ Healthy", "SUCCESS")
            else:
                self._print_colored("✗ Unhealthy", "ERROR")
                all_healthy = False

        self._print_colored("─" * 50, "INFO")

        if all_healthy:
            self._print_colored("All servers are healthy!", "SUCCESS")
        else:
            self._print_colored("Some servers are not responding.", "WARNING")

        return all_healthy

    def stop_processes_by_port(self, ports: List[int]):
        """
        Stop processes running on specified ports.
        :param ports: List of port numbers
        """
        self._print_colored("Stopping processes by port...", "WARNING")

        for port in ports:
            try:
                # Find processes using the port
                for proc in psutil.process_iter(["pid", "name", "connections"]):
                    try:
                        connections = proc.info["connections"]
                        if connections:
                            for conn in connections:
                                if (
                                    hasattr(conn, "laddr")
                                    and conn.laddr
                                    and conn.laddr.port == port
                                ):
                                    pid = proc.info["pid"]
                                    self._print_colored(
                                        f"Stopping process on port {port} (PID: {pid})...",
                                        "WARNING",
                                    )
                                    psutil.Process(pid).terminate()
                                    break
                    except (
                        psutil.NoSuchProcess,
                        psutil.AccessDenied,
                        psutil.ZombieProcess,
                    ):
                        continue
            except Exception as e:
                self._print_colored(
                    f"Warning: Could not stop processes on port {port}: {e}", "WARNING"
                )

    def list_servers(self):
        """List available MCP servers."""
        self._print_colored("Available UFO MCP Servers:", "INFO")
        self._print_colored("=" * 40, "INFO")

        for name, config in self.servers.items():
            self._print_colored(
                f"{name:12} - Port {config['port']} - {config['description']}", "INFO"
            )

    def start_server(self, server_name: str) -> bool:
        """
        Start a specific MCP server.
        :param server_name: Name of the server to start
        :return: True if started successfully
        """
        if server_name not in self.servers:
            self._print_colored(f"Error: Unknown server '{server_name}'", "ERROR")
            return False

        config = self.servers[server_name]

        self._print_colored(
            f"Starting {server_name} MCP server on port {config['port']}...", "INFO"
        )

        if self.verbose:
            self._print_colored(
                f"Command: python -m {config['script']} {' '.join(config.get('args', []))}",
                "DEBUG",
            )
            self._print_colored(f"Working directory: {ufo_root}", "DEBUG")
            if config.get("environment"):
                self._print_colored(
                    f"Environment variables: {config['environment']}", "DEBUG"
                )

        try:
            # Set environment variables
            env = os.environ.copy()
            for key, value in config.get("environment", {}).items():
                env[key] = value

            # Ensure log directory exists
            log_file = config.get("log_file")
            if log_file:
                log_dir = Path(log_file).parent
                log_dir.mkdir(exist_ok=True)

                # Start process with log redirection
                with open(log_file, "w") as stdout_file, open(
                    f"{log_file}.err", "w"
                ) as stderr_file:
                    process = subprocess.Popen(
                        [sys.executable, "-m", config["script"]]
                        + config.get("args", []),
                        cwd=ufo_root,
                        stdout=stdout_file,
                        stderr=stderr_file,
                        env=env,
                        text=True,
                    )
            else:
                # Start process without log redirection
                process = subprocess.Popen(
                    [sys.executable, "-m", config["script"]] + config.get("args", []),
                    cwd=ufo_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True,
                )

            self.processes[server_name] = process

            # Give it a moment to start
            time.sleep(2)

            # Check if process is still running
            if process.poll() is None:
                self._print_colored(
                    f"✓ {server_name} started successfully (PID: {process.pid})",
                    "SUCCESS",
                )
                return True
            else:
                if not log_file:
                    stdout, stderr = process.communicate()
                    if stderr:
                        self._print_colored(f"Error: {stderr}", "ERROR")
                        if self.development:
                            self._print_colored(f"Additional debug info:", "DEBUG")
                            self._print_colored(
                                f"  Return code: {process.returncode}", "DEBUG"
                            )
                            if stdout:
                                self._print_colored(f"  Stdout: {stdout}", "DEBUG")
                self._print_colored(f"✗ {server_name} failed to start", "ERROR")
                return False

        except Exception as e:
            self._print_colored(
                f"✗ Error starting {server_name} MCP server: {e}", "ERROR"
            )
            return False

    def stop_server(self, server_name: str) -> bool:
        """
        Stop a specific MCP server.
        :param server_name: Name of the server to stop
        :return: True if stopped successfully
        """
        if server_name not in self.processes:
            self._print_colored(f"Server '{server_name}' is not running", "WARNING")
            return False

        process = self.processes[server_name]

        try:
            process.terminate()
            process.wait(timeout=5)
            self._print_colored(f"✓ {server_name} MCP server stopped", "SUCCESS")
            del self.processes[server_name]
            return True
        except subprocess.TimeoutExpired:
            process.kill()
            self._print_colored(f"✓ {server_name} MCP server force-killed", "SUCCESS")
            del self.processes[server_name]
            return True
        except Exception as e:
            self._print_colored(
                f"✗ Error stopping {server_name} MCP server: {e}", "ERROR"
            )
            return False

    def start_specific_servers(self, server_names: List[str]) -> bool:
        """Start specific MCP servers in startup order."""
        self._print_colored("═" * 60, "INFO")
        self._print_colored("UFO2 MCP Server Launcher", "INFO")
        self._print_colored("═" * 60, "INFO")

        self._print_colored(
            f"Starting specified MCP servers: {', '.join(server_names)}...", "INFO"
        )
        self._print_colored("=" * 40, "INFO")

        success_count = 0

        # Validate server names
        invalid_servers = [name for name in server_names if name not in self.servers]
        if invalid_servers:
            self._print_colored(
                f"Error: Unknown servers: {', '.join(invalid_servers)}", "ERROR"
            )
            self._print_colored("Available servers:", "INFO")
            for name in self.servers.keys():
                self._print_colored(f"  - {name}", "INFO")
            return False

        # Start servers in defined order (only those specified)
        for server_name in self.startup_order:
            if server_name in server_names:
                if self.start_server(server_name):
                    success_count += 1
                # Small delay between server starts
                time.sleep(2)

        self._print_colored(f"\n{'-' * 60}", "INFO")
        self._print_colored(f"Started {success_count} MCP server(s)", "SUCCESS")

        for server_name in self.processes:
            process = self.processes[server_name]
            config = self.servers[server_name]
            self._print_colored(
                f"• {config.get('script', server_name)} - Port {config['port']} - PID {process.pid}",
                "INFO",
            )

        # Wait a moment for all servers to fully initialize
        self._print_colored("\nWaiting for servers to initialize...", "INFO")
        time.sleep(5)

        if success_count == len(server_names):
            self._print_colored(
                f"\n🚀 All {success_count} specified MCP servers are running!",
                "SUCCESS",
            )
            self._print_colored("You can now use UFO2 with MCP integration.", "INFO")
            self.show_status()
            return True
        else:
            self._print_colored("⚠ Some MCP servers failed to start", "WARNING")
            return False

    def start_all(self) -> bool:
        """Start all MCP servers."""
        self._print_colored("═" * 60, "INFO")
        self._print_colored("UFO2 MCP Server Launcher", "INFO")
        self._print_colored("═" * 60, "INFO")

        self._print_colored("Starting all UFO MCP servers...", "INFO")
        self._print_colored("=" * 40, "INFO")

        success_count = 0
        total_count = len(self.servers)

        # Start servers in defined order
        for server_name in self.startup_order:
            if server_name in self.servers:
                if self.start_server(server_name):
                    success_count += 1
                # Small delay between server starts
                time.sleep(2)

        self._print_colored(f"\n{'-' * 60}", "INFO")
        self._print_colored(f"Started {success_count} MCP server(s)", "SUCCESS")

        for server_name in self.processes:
            process = self.processes[server_name]
            config = self.servers[server_name]
            self._print_colored(
                f"• {config.get('script', server_name)} - Port {config['port']} - PID {process.pid}",
                "INFO",
            )

        # Wait a moment for all servers to fully initialize
        self._print_colored("\nWaiting for servers to initialize...", "INFO")
        time.sleep(5)

        if success_count == total_count:
            # Health check
            if self.test_all_servers_health():
                self._print_colored(
                    "\n🚀 All MCP servers are running and healthy!", "SUCCESS"
                )
                self._print_colored(
                    "You can now use UFO2 with MCP integration.", "INFO"
                )
            else:
                self._print_colored(
                    "\n⚠️ Some servers may not be responding correctly.", "WARNING"
                )
                self._print_colored("Check the log files for more information.", "INFO")

            self.show_status()

            # Keep the servers running
            self._print_colored(
                "\nPress Ctrl+C to stop all servers and exit...", "INFO"
            )
            try:
                while True:
                    time.sleep(30)
                    # Check if any servers have died
                    dead_servers = []
                    for server_name, process in self.processes.items():
                        if process.poll() is not None:
                            dead_servers.append(server_name)

                    if dead_servers:
                        self._print_colored(f"\n⚠️ Detected dead processes:", "WARNING")
                        for server_name in dead_servers:
                            self._print_colored(f"• {server_name} has stopped", "ERROR")
                            del self.processes[server_name]
                        break

            except KeyboardInterrupt:
                self._print_colored("\nShutting down...", "WARNING")
                self.stop_all()

            return True
        else:
            self._print_colored("⚠ Some MCP servers failed to start", "WARNING")
            return False

    def stop_all(self):
        """Stop all running MCP servers."""
        self._print_colored("Stopping all MCP servers...", "WARNING")

        # Stop by port first (like PowerShell version)
        ports = [8001, 8002, 8003, 8004, 8005]
        self.stop_processes_by_port(ports)

        # Then stop tracked processes
        for server_name in list(self.processes.keys()):
            self.stop_server(server_name)

        self._print_colored("All MCP servers stopped", "SUCCESS")
    def show_status(self):
        """Show status of all MCP servers."""
        self._print_colored("\nMCP Server Status:", "INFO")
        self._print_colored("=" * 40, "INFO")

        for server_name, config in self.servers.items():
            port = config.get("port", 8000)
            endpoint = f"http://localhost:{port}"
            
            # Get health check endpoint from MCP config if available
            health_endpoint = "/health"
            if "mcp_config" in config:
                health_endpoint = config["mcp_config"].get("health_check_endpoint", "/health")
            
            # Check if server is actually running (regardless of how it was started)
            if self.test_server_health(endpoint, health_endpoint):
                # Server is running - check if we know the PID
                if server_name in self.processes:
                    process = self.processes[server_name]
                    if process.poll() is None:
                        status = f"Running (PID: {process.pid})"
                    else:
                        status = "Running (external process)"
                        # Clean up stale process reference
                        del self.processes[server_name]
                else:
                    status = "Running (external process)"
                color = "SUCCESS"
            else:
                # Server is not responding
                if server_name in self.processes:
                    process = self.processes[server_name]
                    if process.poll() is None:
                        status = "Not responding (process exists)"
                        color = "WARNING"
                    else:
                        status = "Stopped"
                        color = "ERROR"
                        # Clean up dead process reference
                        del self.processes[server_name]
                else:
                    status = "Not running"
                    color = "WARNING"

            self._print_colored(
                f"{server_name:12} - Port {config['port']} - {status}", color
            )

    def interactive_mode(self):
        """Run in interactive mode."""
        self._print_colored("UFO MCP Server Launcher - Interactive Mode", "INFO")
        self._print_colored("=" * 50, "INFO")

        while True:
            self._print_colored("\nCommands:", "INFO")
            self._print_colored("1. list      - List available servers", "INFO")
            self._print_colored("2. start     - Start specific server", "INFO")
            self._print_colored("3. stop      - Stop specific server", "INFO")
            self._print_colored("4. start-all - Start all servers", "INFO")
            self._print_colored("5. stop-all  - Stop all servers", "INFO")
            self._print_colored("6. status    - Show server status", "INFO")
            self._print_colored("7. health    - Check server health", "INFO")
            self._print_colored("8. quit      - Exit", "INFO")

            try:
                choice = (
                    input(f"\n{COLORS['INFO']}Enter command: {COLORS['RESET']}")
                    .strip()
                    .lower()
                )

                if choice in ["1", "list"]:
                    self.list_servers()

                elif choice in ["2", "start"]:
                    server_name = input(
                        f"{COLORS['INFO']}Enter server name: {COLORS['RESET']}"
                    ).strip()
                    self.start_server(server_name)

                elif choice in ["3", "stop"]:
                    server_name = input(
                        f"{COLORS['INFO']}Enter server name: {COLORS['RESET']}"
                    ).strip()
                    self.stop_server(server_name)

                elif choice in ["4", "start-all"]:
                    self.start_all()

                elif choice in ["5", "stop-all"]:
                    self.stop_all()

                elif choice in ["6", "status"]:
                    self.show_status()

                elif choice in ["7", "health"]:
                    self.test_all_servers_health()

                elif choice in ["8", "quit", "exit"]:
                    self.stop_all()
                    self._print_colored("Goodbye!", "SUCCESS")
                    break

                else:
                    self._print_colored("Invalid command", "ERROR")

            except KeyboardInterrupt:
                self._print_colored("\nShutting down...", "WARNING")
                self.stop_all()
                break
            except EOFError:
                self._print_colored("\nShutting down...", "WARNING")
                self.stop_all()
                break

    def start_all_daemon(self) -> bool:
        """Start all MCP servers and keep running in daemon mode."""
        success = self.start_all()

        if success:
            self._print_colored(
                "\nRunning in daemon mode. Press Ctrl+C to stop all servers...", "INFO"
            )
            try:
                while True:
                    time.sleep(5)  # Check every 5 seconds

                    # Monitor server health
                    for server_name in list(self.processes.keys()):
                        process = self.processes[server_name]
                        if process.poll() is not None:
                            self._print_colored(
                                f"Warning: {server_name} server stopped unexpectedly",
                                "WARNING",
                            )
                            # Optionally restart
                            self._print_colored(f"Restarting {server_name}...", "INFO")
                            self.start_server(server_name)

            except KeyboardInterrupt:
                self._print_colored("\nReceived shutdown signal...", "WARNING")
                self.stop_all()

        return success

    def _load_configuration(self):
        """Load MCP server configuration from YAML files."""
        # Default configuration in case files are missing
        default_servers = {
            "powerpoint": {
                "script": "ufo.mcp.app_servers.powerpoint_mcp_server",
                "port": 8001,
                "description": "Microsoft PowerPoint automation",
                "log_file": "logs/mcp_powerpoint.log",
                "args": ["--port", "8001", "--host", "localhost"],
                "environment": {},
            },
            "word": {
                "script": "ufo.mcp.app_servers.word_mcp_server",
                "port": 8002,
                "description": "Microsoft Word automation",
                "log_file": "logs/mcp_word.log",
                "args": ["--port", "8002", "--host", "localhost"],
                "environment": {},
            },
            "excel": {
                "script": "ufo.mcp.app_servers.excel_mcp_server",
                "port": 8003,
                "description": "Microsoft Excel automation",
                "log_file": "logs/mcp_excel.log",
                "args": ["--port", "8003", "--host", "localhost"],
                "environment": {},
            },
            "web": {
                "script": "ufo.mcp.app_servers.web_mcp_server",
                "port": 8004,
                "description": "Web browser automation",
                "log_file": "logs/mcp_web.log",
                "args": ["--port", "8004", "--host", "localhost"],
                "environment": {},
            },
            "shell": {
                "script": "ufo.mcp.app_servers.shell_mcp_server",
                "port": 8005,
                "description": "Shell command execution",
                "log_file": "logs/mcp_shell.log",
                "args": ["--port", "8005", "--host", "localhost"],
                "environment": {},
            },
        }
        
        default_startup_order = ["shell", "web", "excel", "word", "powerpoint"]
        
        # Try to load from launcher configuration file
        launcher_config_path = self.config_path or "ufo/config/mcp_launcher.yaml"
        
        try:
            if os.path.exists(launcher_config_path):
                self._print_colored(f"Loading launcher configuration from: {launcher_config_path}", "INFO")
                with open(launcher_config_path, 'r', encoding='utf-8') as f:
                    self.launcher_config = yaml.safe_load(f)
                
                # Load startup order
                startup_config = self.launcher_config.get("startup_config", {})
                self.startup_order = startup_config.get("startup_order", default_startup_order)
                
                # Load server configurations
                servers_config = self.launcher_config.get("servers", {})
                for server_name, server_config in servers_config.items():
                    self.servers[server_name] = {
                        "script": server_config.get("module_path", default_servers.get(server_name, {}).get("script", "")),
                        "port": server_config.get("port", 8000),
                        "description": server_config.get("name", f"{server_name.title()} MCP Server"),
                        "log_file": server_config.get("log_file", f"logs/mcp_{server_name}.log"),
                        "args": server_config.get("args", []),                        "environment": server_config.get("environment", {}),
                    }
                
                # Fill in any missing servers with defaults
                for server_name, server_config in default_servers.items():
                    if server_name not in self.servers:
                        self.servers[server_name] = server_config
                        
                self._print_colored(f"✓ Loaded configuration for {len(self.servers)} servers", "SUCCESS")
                if self.verbose:
                    self._print_colored(f"Startup order: {self.startup_order}", "DEBUG")
                    
            else:
                self._print_colored(f"Configuration file not found: {launcher_config_path}", "WARNING")
                self._print_colored("Using default configuration", "INFO")
                self.servers = default_servers
                self.startup_order = default_startup_order
                
        except Exception as e:
            self._print_colored(f"Error loading configuration: {e}", "ERROR")
            self._print_colored("Using default configuration", "WARNING")
            self.servers = default_servers
            self.startup_order = default_startup_order

        # Try to load MCP servers configuration for additional settings
        servers_config_path = "ufo/config/mcp_servers.yaml"
        try:
            if os.path.exists(servers_config_path):
                self._print_colored(f"Loading MCP servers configuration from: {servers_config_path}", "INFO")
                with open(servers_config_path, 'r', encoding='utf-8') as f:
                    mcp_servers_config = yaml.safe_load(f)
                
                # Update server configurations with MCP server settings
                mcp_servers = mcp_servers_config.get("mcp_servers", {})
                for server_name, mcp_config in mcp_servers.items():
                    if server_name in self.servers and mcp_config.get("enabled", True):
                        # Update description from MCP config
                        self.servers[server_name]["description"] = mcp_config.get("description", 
                                                                                  self.servers[server_name]["description"])
                        # Store additional MCP settings
                        self.servers[server_name]["mcp_config"] = {
                            "endpoint": mcp_config.get("endpoint"),
                            "timeout": mcp_config.get("timeout", 30),
                            "retry_count": mcp_config.get("retry_count", 3),
                            "health_check_endpoint": mcp_config.get("health_check_endpoint", "/health"),
                        }
                        
                if self.verbose:
                    self._print_colored(f"✓ Enhanced configuration with MCP server settings", "SUCCESS")
                    
        except Exception as e:
            if self.verbose:
                self._print_colored(f"Could not load MCP servers configuration: {e}", "WARNING")


def main():
    """Main entry point for the MCP server launcher."""
    parser = argparse.ArgumentParser(
        description="UFO MCP Server Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=""":
Examples:
  python launch_mcp_servers.py --list
  python launch_mcp_servers.py --start word
  python launch_mcp_servers.py --start-all
  python launch_mcp_servers.py --servers shell web
  python launch_mcp_servers.py --interactive
  python launch_mcp_servers.py --health
        """,
    )

    parser.add_argument(
        "--config-path",
        default="ufo/config/mcp_launcher.yaml",
        help="Path to configuration file (default: ufo/config/mcp_launcher.yaml)",
    )
    parser.add_argument(
        "--development", action="store_true", help="Run in development mode"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--servers",
        nargs="+",
        metavar="SERVER",
        help="Specific servers to start (space-separated list)",
    )
    parser.add_argument("--list", action="store_true", help="List available servers")
    parser.add_argument("--start", metavar="SERVER", help="Start specific server")
    parser.add_argument("--stop", metavar="SERVER", help="Stop specific server")
    parser.add_argument("--start-all", action="store_true", help="Start all servers")
    parser.add_argument("--stop-all", action="store_true", help="Stop all servers")
    parser.add_argument("--status", action="store_true", help="Show server status")
    parser.add_argument("--health", action="store_true", help="Check server health")
    parser.add_argument(
        "--interactive", action="store_true", help="Run in interactive mode"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in daemon mode (keep running after start-all)",
    )

    args = parser.parse_args()

    launcher = MCPServerLauncher(
        config_path=args.config_path, development=args.development, verbose=args.verbose
    )

    try:
        if args.list:
            launcher.list_servers()

        elif args.start:
            launcher.start_server(args.start)

        elif args.stop:
            launcher.stop_server(args.stop)

        elif args.servers:
            launcher.start_specific_servers(args.servers)

        elif args.start_all:
            if args.daemon:
                launcher.start_all_daemon()
            else:
                launcher.start_all()

        elif args.stop_all:
            launcher.stop_all()

        elif args.status:
            launcher.show_status()

        elif args.health:
            launcher.test_all_servers_health()

        elif args.interactive:
            launcher.interactive_mode()

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\nShutting down...")
        launcher.stop_all()


if __name__ == "__main__":
    main()
