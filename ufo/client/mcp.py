from fastmcp import FastMCP
from typing import Any, Dict
import json


class DefaultMCPServerManager:
    """
    This class manages the default MCP servers which are implemented and registered, which can be automatically started.
    """

    _servers_mapping: Dict[str, FastMCP] = {}

    @classmethod
    def register_server(cls, server_name: str, server: FastMCP):
        """
        Register a server with the given name.

        Args:
            server_name: The name of the server to register.
            server: The FastMCP server instance to register.
        """
        if server_name in cls._servers_mapping:
            raise ValueError(f"Server {server_name} is already registered.")
        cls._servers_mapping[server_name] = server
        print(f"Registered MCP server '{server_name}'")

    def start_local_server(cls, namespace: str, host: str, port: int) -> str:
        """
        Start a server with the given namespace and parameters.

        Args:
            namespace: The namespace of the server to start.
            params: Parameters for starting the server.

        Returns:
            A message indicating the server has started.
        """
        if namespace not in cls._servers_mapping:
            raise ValueError(f"Server {namespace} is not registered.")
        cls._servers_mapping[namespace].run()
        return f"Server {namespace} started successfully."


class MCPServerController:
    """
    Controller for managing MCP servers.
    """

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.servers = {}
        self._meta_action_mappings = {
            "start_server": self.start_server,
            "stop_server": self.stop_server,
            "list_tools": self.list_tools,
        }

    async def start_local_server(self, name: str, host: str, port: int):
        if name in self.servers:
            raise ValueError(f"Server {name} is already running.")
        server = FastMCP(host=host, port=port)
        server.run()
        self.servers[name] = server
        print(f"Started MCP server '{name}' at {host}:{port}")

    async def stop_server(self, name: str):
        if name not in self.servers:
            raise ValueError(f"Server {name} is not running.")
        self.servers[name].shutdown()  # ← Replace with actual shutdown logic
        del self.servers[name]
        print(f"Stopped MCP server '{name}'")

    async def list_tools(self) -> Dict[str, Any]:
        tools = {}
        for name, server in self.servers.items():
            tools[name] = server.get_available_tools()
        return tools

    async def invoke(self, action_name: str, *args, **kwargs):
        if action_name not in self._meta_action_mappings:
            raise ValueError(f"Unknown action: {action_name}")
        return await self._meta_action_mappings[action_name](*args, **kwargs)
