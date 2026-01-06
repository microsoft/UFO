# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Command Interface Definitions

Defines the core interfaces for the command pattern implementation.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ICommand(ABC):
    """
    Base interface for all commands in the constellation editor.

    Implements the Command pattern for encapsulating operations
    on TaskConstellation objects.
    """

    @abstractmethod
    def execute(self) -> Any:
        """
        Execute the command.

        :return: Result of the command execution
        :raises: CommandExecutionError if execution fails
        """
        pass

    @abstractmethod
    def can_execute(self) -> bool:
        """
        Check if the command can be executed.

        :return: True if command can be executed, False otherwise
        """
        pass
    
    def get_cannot_execute_reason(self) -> str:
        """
        Get a detailed reason why the command cannot be executed.
        
        This method should be called when can_execute() returns False
        to provide specific debugging information.
        
        :return: Detailed reason why command cannot execute
        """
        return "Command cannot be executed"

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get a human-readable description of the command.

        :return: Command description
        """
        pass


class IUndoableCommand(ICommand):
    """
    Interface for commands that can be undone.

    Extends ICommand with undo/redo capabilities.
    """

    @abstractmethod
    def undo(self) -> Any:
        """
        Undo the command execution.

        :return: Result of the undo operation
        :raises: CommandUndoError if undo fails
        """
        pass

    @abstractmethod
    def can_undo(self) -> bool:
        """
        Check if the command can be undone.

        :return: True if command can be undone, False otherwise
        """
        pass

    @property
    @abstractmethod
    def is_executed(self) -> bool:
        """
        Check if the command has been executed.

        :return: True if executed, False otherwise
        """
        pass


class CommandExecutionError(Exception):
    """Exception raised when command execution fails."""

    def __init__(
        self,
        command: ICommand,
        message: str,
        original_error: Optional[Exception] = None,
    ):
        self.command = command
        self.original_error = original_error
        super().__init__(f"Command execution failed: {message}")


class CommandUndoError(Exception):
    """Exception raised when command undo fails."""

    def __init__(
        self,
        command: IUndoableCommand,
        message: str,
        original_error: Optional[Exception] = None,
    ):
        self.command = command
        self.original_error = original_error
        super().__init__(f"Command undo failed: {message}")
