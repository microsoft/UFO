from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Union

from fastmcp import FastMCP
from fastmcp.client.transports import StdioTransport
from ufo.mcp.mcp_registry import MCPRegistry

# MCPServerType can be either a URL string for HTTP servers or a FastMCP instance for local in-memory servers, or a StdioTransport instance.
MCPServerType = Union[str, FastMCP, StdioTransport]


class BaseMCPServer(ABC):
    """
    Base class for MCP servers. This class should be extended by specific MCP server implementations.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the MCP server with the given configuration.
        :param config: Configuration dictionary for the MCP server.
        """
        self._config = config
        self._server: Optional[FastMCP] = None
        self._namespace = config.get("namespace", "default")

    @abstractmethod
    def start(self) -> None:
        """
        Start the MCP server. This method should be implemented by subclasses.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        Stop the MCP server. This method should be implemented by subclasses.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the MCP server. This method should be implemented by subclasses.
        """
        pass

    @property
    def config(self) -> Dict[str, Any]:
        """
        Get the configuration of the MCP server.
        :return: Configuration dictionary.
        """
        return self._config

    @property
    def namespace(self) -> str:
        """
        Get the namespace of the MCP server.
        :return: Namespace string.
        """
        return self._namespace

    @property
    def server(self) -> Optional[MCPServerType]:
        """
        Get the FastMCP server instance.
        :return: FastMCP instance or None if not started.
        """
        return self._server


class HTTPMCPServer(BaseMCPServer):
    """
    Implementation of an HTTP MCP server.
    """

    def start(self) -> None:
        """
        Start the HTTP MCP server and return its URL.
        :return: URL of the started HTTP server.
        """
        host = self._config.get("host", "localhost")
        port = self._config.get("port", 8000)
        path = self._config.get("path", "/mcp")
        self._server = f"http://{host}:{port}{path}"
        return self._server

    def stop(self) -> None:
        """
        Stop the HTTP MCP server. This is a placeholder as HTTP servers are typically managed externally.
        """
        pass

    def reset(self) -> None:
        """
        Reset the HTTP MCP server. This is a placeholder as HTTP servers are typically stateless.
        """
        print("HTTP MCP server reset is not supported.")


class LocalMCPServer(BaseMCPServer):
    """
    Implementation of a local in-memory MCP server.
    """

    _mcp_registry = MCPRegistry

    def start(self) -> None:
        """
        Start the local MCP server and return the FastMCP instance.
        :return: FastMCP instance for local in-memory server.
        """
        server_namespace = self._config.get("namespace", "default")

        try:
            # Try to get the server from the registry
            self._server = self._mcp_registry.get(server_namespace)
        except KeyError:
            raise ValueError(
                f"No MCP server found for name '{server_namespace}' in local server registry."
            )

    def stop(self) -> None:
        """
        Stop the local MCP server. This is a placeholder as local servers are typically managed by the application lifecycle.
        """
        pass

    def reset(self) -> None:
        """
        Reset the local MCP server. This is a placeholder as local servers are typically stateless.
        """
        pass


class StdioMCPServer(BaseMCPServer):
    """
    Implementation of a standard input/output MCP server.
    """

    def start(self) -> None:
        """
        Start the Stdio MCP server and return the StdioTransport instance.
        :return: StdioTransport instance for standard input/output server.
        """
        command = self._config.get("command", "python")
        args = self._config.get("args", [])
        env = self._config.get("env", {})
        cwd = self._config.get("cwd", ".")
        self._server = StdioTransport(command=command, args=args, env=env, cwd=cwd)

    def stop(self) -> None:
        """
        Stop the Stdio MCP server. This is a placeholder as stdio servers are typically managed by the application lifecycle.
        """
        pass

    def reset(self) -> None:
        """
        Reset the Stdio MCP server. This is a placeholder as stdio servers are typically stateless.
        """
        pass


class MCPServerManager:
    """
    This class manages the default MCP servers which are implemented and registered, which can be automatically started.
    """

    _server_type_mapping: Dict[str, Callable[[Dict[str, Any]], BaseMCPServer]] = {
        "http": HTTPMCPServer,
        "local": LocalMCPServer,
        "stdio": StdioMCPServer,
    }

    _servers_mapping: Dict[str, BaseMCPServer] = {}

    @classmethod
    def register_server(cls, namespace: str, server: MCPServerType) -> None:
        """
        Register a server with the given name.
        :param namespace: The namespace of the server.
        :param type: The type of the server (e.g., "http", "stdio", "local").
        """

        cls._servers_mapping[namespace] = server
        print(f"Registered MCP server '{namespace}'")

    @classmethod
    def create_mcp_server(self, mcp_config: Dict[str, Any]) -> MCPServerType:
        """
        Create an MCP server based on the type and parameters.
        :param mcp_config: Configuration dictionary for the MCP server.
        :return: A string URL for HTTP servers or a FastMCP instance for local in-memory servers, or a StdioTransport instance.
        """

        server_type = mcp_config.get("type")

        assert (
            server_type in self._server_type_mapping
        ), f"Unsupported server type: {server_type}"

        server_class = self._server_type_mapping[server_type]

        server_instance = server_class(mcp_config)
        server_instance.start()

        self.register_server(server_instance.namespace, server_instance)

        return server_instance.server

    @classmethod
    def get_server(cls, namespace: str) -> Optional[MCPServerType]:
        """
        Get the MCP server by its namespace.
        :param namespace: The namespace of the server.
        :return: The MCP server instance or None if not found.
        """
        return cls._servers_mapping.get(namespace, None)

    @classmethod
    def create_or_get_server(
        cls, mcp_config: Dict[str, Any], reset: bool = False
    ) -> MCPServerType:
        """
        Create a new MCP server or return an existing one based on the configuration.
        :param mcp_config: Configuration dictionary for the MCP server.
        :param reset: If True, reset the server if it already exists.
        :return: The MCP server instance.
        """
        namespace = mcp_config.get("namespace", "default")

        if reset and namespace in cls._servers_mapping:
            cls._servers_mapping[namespace].reset()

        if namespace not in cls._servers_mapping:
            return cls.create_mcp_server(mcp_config)

        return cls._servers_mapping[namespace]

    def clear_servers(self) -> None:
        """
        Clear all registered MCP servers.
        This is useful for resetting the server state during testing or reinitialization.
        """
        self._servers_mapping.clear()

        print("Cleared all registered MCP servers.")
