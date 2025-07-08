from fastmcp import FastMCP
from typing import Any, Dict


class MCPServerManager:
    """
    Manager for MCP servers, providing methods to start and stop servers.
    """

    def __init__(self):
        self.servers = {}

    def _load_server_config(self, config_file: str) -> Dict[str, Any]:
        """
        Load server configuration from a JSON file.

        Args:
            config_file: Path to the configuration file

        Returns:
            A dictionary containing server configurations
        """
        import json

        with open(config_file, "r") as f:
            return json.load(f)

    def start_server(self, name: str, host: str, port: int):
        """
        Start an MCP server.

        Args:
            name: The name of the server
            host: The host address for the server
            port: The port number for the server
        """
        if name in self.servers:
            raise ValueError(f"Server {name} is already running.")

        server = FastMCP(host=host, port=port)
        server.run()

        self.servers[name] = server

        server
        print(f"Started MCP server '{name}' at {host}:{port}")

    def stop_server(self, name: str):
        """
        Stop an MCP server.

        Args:
            name: The name of the server to stop
        """
        if name not in self.servers:
            raise ValueError(f"Server {name} is not running.")

        self.servers[name].run()  # Assuming run() stops the server
        del self.servers[name]
        print(f"Stopped MCP server '{name}'")
