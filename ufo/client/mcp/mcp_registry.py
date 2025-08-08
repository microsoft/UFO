"""
MCP Registry System
Provides a centralized registry for MCP server instances and factories.
"""

from typing import Callable, Dict
from fastmcp import FastMCP


class MCPRegistry:
    """
    Registry for MCP server instances and factories.
    Supports both direct registration and factory-based lazy initialization.
    """

    _instances: Dict[str, FastMCP] = {}
    _factories: Dict[str, Callable[[], FastMCP] | Callable[[str], FastMCP]] = {}

    @classmethod
    def register_factory(cls, name: str, factory: Callable[[], FastMCP] | Callable[[str], FastMCP]) -> None:
        """
        Register a factory function for creating MCP server instances.
        :param name: Unique name for the MCP server.
        :param factory: Factory function that returns a FastMCP instance.
        :return: None
        """
        cls._factories[name] = factory

    @classmethod
    def register_instance(cls, name: str, instance: FastMCP) -> None:
        """
        Register a pre-created MCP server instance.
        :param name: Unique name for the MCP server.
        :param instance: FastMCP instance to register.
        :return: None
        """
        cls._instances[name] = instance

    @classmethod
    def get(cls, name: str, *args, **kwargs) -> FastMCP:
        """
        Get an MCP server instance by name.
        Creates the instance using the factory if not already created.
        :param name: Name of the MCP server.
        :return: FastMCP instance.
        :raises KeyError: If no server is registered under the given name.
        """
        if name in cls._instances:
            return cls._instances[name]
        if name in cls._factories:
            instance = cls._factories[name](*args, **kwargs)
            return instance
        raise KeyError(f"No MCP server registered under name '{name}'")

    @classmethod
    def list(cls) -> list:
        """
        List all registered MCP server names.
        :return: List of server names.
        """
        return list(set(cls._instances.keys()) | set(cls._factories.keys()))

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered instances and factories.
        Useful for testing or resetting the registry.
        """
        cls._instances.clear()
        cls._factories.clear()

    @classmethod
    def remove(cls, name: str) -> bool:
        """
        Remove a server from the registry.
        :param name: Name of the server to remove.
        :return: True if server was removed, False if not found.
        """
        removed = False
        if name in cls._instances:
            del cls._instances[name]
            removed = True
        if name in cls._factories:
            del cls._factories[name]
            removed = True
        return removed

    @classmethod
    def register_factory_decorator(cls, name: str):
        """
        Decorator version of register_factory.

        Usage:
            @MCPRegistry.register_factory_decorator("server_name")
            def create_server():
                return FastMCP("Server Name")

        :param name: Unique name for the MCP server.
        :return: Decorator function.
        """

        def decorator(factory_func: Callable[[], FastMCP] | Callable[[str], FastMCP]):
            cls.register_factory(name, factory_func)
            return factory_func

        return decorator

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if a server is registered.
        :param name: Name of the server to check.
        :return: True if server is registered, False otherwise.
        """
        return name in cls._instances or name in cls._factories

    @classmethod
    def get_info(cls) -> Dict[str, Dict[str, bool]]:
        """
        Get information about all registered servers.
        :return: Dictionary with server names and their status.
        """
        info = {}
        all_names = cls.list()
        for name in all_names:
            info[name] = {
                "has_instance": name in cls._instances,
                "has_factory": name in cls._factories,
                "is_instantiated": name in cls._instances,
            }
        return info
