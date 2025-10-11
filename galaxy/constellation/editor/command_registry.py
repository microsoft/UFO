"""
Command registry for constellation editor commands.

This module provides a registry system for registering and managing
command classes using decorators.
"""

from typing import Any, Callable, Dict, Optional, Type

from .command_interface import ICommand, IUndoableCommand


class CommandRegistry:
    """Registry for managing command classes."""

    def __init__(self):
        """Initialize the command registry."""
        self._commands: Dict[str, Type[ICommand]] = {}
        self._command_metadata: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "general",
        **metadata,
    ) -> Callable:
        """
        Decorator to register a command class.

        :param name: Name for the command (defaults to class name)
        :param description: Description of the command
        :param category: Category for the command
        :param metadata: Additional metadata for the command
        :return: Decorator function
        """

        def decorator(command_class: Type[ICommand]) -> Type[ICommand]:
            command_name = name or command_class.__name__

            # Validate command class
            if not issubclass(command_class, ICommand):
                raise ValueError(
                    f"Command {command_name} must implement ICommand interface"
                )

            # Register the command
            self._commands[command_name] = command_class
            self._command_metadata[command_name] = {
                "description": description or command_class.__doc__ or "",
                "category": category,
                "is_undoable": issubclass(command_class, IUndoableCommand),
                "class_name": command_class.__name__,
                **metadata,
            }

            return command_class

        return decorator

    def get_command(self, name: str) -> Optional[Type[ICommand]]:
        """
        Get a command class by name.

        :param name: Name of the command
        :return: Command class or None if not found
        """
        return self._commands.get(name)

    def list_commands(
        self, category: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        List all registered commands.

        :param category: Optional category filter
        :return: Dictionary of command names and their metadata
        """
        if category is None:
            return self._command_metadata.copy()

        return {
            name: metadata
            for name, metadata in self._command_metadata.items()
            if metadata.get("category") == category
        }

    def get_command_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific command.

        :param name: Name of the command
        :return: Command metadata or None if not found
        """
        return self._command_metadata.get(name)

    def is_registered(self, name: str) -> bool:
        """
        Check if a command is registered.

        :param name: Name of the command
        :return: True if registered, False otherwise
        """
        return name in self._commands

    def unregister(self, name: str) -> bool:
        """
        Unregister a command.

        :param name: Name of the command to unregister
        :return: True if unregistered, False if not found
        """
        if name in self._commands:
            del self._commands[name]
            del self._command_metadata[name]
            return True
        return False

    def clear(self) -> None:
        """Clear all registered commands."""
        self._commands.clear()
        self._command_metadata.clear()

    def create_command(self, name: str, *args, **kwargs) -> Optional[ICommand]:
        """
        Create an instance of a registered command.

        :param name: Name of the command
        :param args: Positional arguments for command constructor
        :param kwargs: Keyword arguments for command constructor
        :return: Command instance or None if not found
        """
        command_class = self.get_command(name)
        if command_class is None:
            return None

        try:
            return command_class(*args, **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to create command {name}: {e}")

    def get_categories(self) -> list[str]:
        """
        Get all unique categories.

        :return: List of category names
        """
        categories = set()
        for metadata in self._command_metadata.values():
            categories.add(metadata.get("category", "general"))
        return sorted(list(categories))


# Global command registry instance
command_registry = CommandRegistry()


def register_command(
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: str = "general",
    **metadata,
) -> Callable:
    """
    Decorator to register a command with the global registry.

    :param name: Name for the command (defaults to class name)
    :param description: Description of the command
    :param category: Category for the command
    :param metadata: Additional metadata for the command
    :return: Decorator function
    """
    return command_registry.register(name, description, category, **metadata)
