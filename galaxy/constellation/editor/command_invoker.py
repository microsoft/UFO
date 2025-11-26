# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Command Invoker

Handles command execution with history management and validation.
"""

from typing import Any, List, Optional

from .command_history import CommandHistory
from .command_interface import CommandExecutionError, ICommand, IUndoableCommand


class CommandInvoker:
    """
    Invoker for executing commands with history management.

    Provides centralized command execution with support for
    undo/redo operations and command validation.
    """

    def __init__(self, enable_history: bool = True, max_history_size: int = 100):
        """
        Initialize command invoker.

        :param enable_history: Whether to enable command history
        :param max_history_size: Maximum number of commands to keep in history
        """
        self._enable_history = enable_history
        self._history = CommandHistory(max_history_size) if enable_history else None
        self._execution_count = 0

    def execute(self, command: ICommand) -> Any:
        """
        Execute a command.

        :param command: Command to execute
        :return: Result of command execution
        :raises: CommandExecutionError if execution fails or command cannot be executed
        """
        if not command.can_execute():
            reason = command.get_cannot_execute_reason()
            raise CommandExecutionError(
                command,
                f"Command cannot be executed: {command.description}. Reason: {reason}",
            )

        try:
            result = command.execute()
            self._execution_count += 1

            # Add to history if it's an undoable command and history is enabled
            if (
                self._enable_history
                and self._history is not None
                and isinstance(command, IUndoableCommand)
            ):
                self._history.add_command(command)

            return result

        except Exception as e:
            raise CommandExecutionError(command, str(e), e)

    def undo(self) -> Optional[IUndoableCommand]:
        """
        Undo the last command.

        :return: The undone command, or None if undo not possible
        """
        if not self._enable_history or not self._history:
            return None

        return self._history.undo()

    def redo(self) -> Optional[IUndoableCommand]:
        """
        Redo the next command.

        :return: The redone command, or None if redo not possible
        """
        if not self._enable_history or not self._history:
            return None

        return self._history.redo()

    def can_undo(self) -> bool:
        """
        Check if undo is possible.

        :return: True if undo is possible, False otherwise
        """
        return (
            self._enable_history
            and self._history is not None
            and self._history.can_undo()
        )

    def can_redo(self) -> bool:
        """
        Check if redo is possible.

        :return: True if redo is possible, False otherwise
        """
        return (
            self._enable_history
            and self._history is not None
            and self._history.can_redo()
        )

    def clear_history(self) -> None:
        """Clear the command history."""
        if self._history:
            self._history.clear()

    def get_history(self) -> List[IUndoableCommand]:
        """
        Get the command history.

        :return: List of commands in history, empty list if history disabled
        """
        if self._history:
            return self._history.get_history()
        return []

    def get_undo_description(self) -> Optional[str]:
        """
        Get description of the command that would be undone.

        :return: Description of undoable command, or None if no undo available
        """
        if self._history:
            return self._history.get_undo_description()
        return None

    def get_redo_description(self) -> Optional[str]:
        """
        Get description of the command that would be redone.

        :return: Description of redoable command, or None if no redo available
        """
        if self._history:
            return self._history.get_redo_description()
        return None

    @property
    def execution_count(self) -> int:
        """Get the total number of commands executed."""
        return self._execution_count

    @property
    def history_enabled(self) -> bool:
        """Check if history is enabled."""
        return self._enable_history

    @property
    def history_size(self) -> int:
        """Get the number of commands in history."""
        return len(self._history) if self._history else 0

    def enable_history(self, enable: bool = True, max_history_size: int = 100) -> None:
        """
        Enable or disable command history.

        :param enable: Whether to enable history
        :param max_history_size: Maximum history size if enabling
        """
        if enable and not self._enable_history:
            self._history = CommandHistory(max_history_size)
            self._enable_history = True
        elif not enable and self._enable_history:
            self._history = None
            self._enable_history = False

    def __str__(self) -> str:
        """String representation of command invoker."""
        return (
            f"CommandInvoker(executions={self._execution_count}, "
            f"history_enabled={self._enable_history}, "
            f"history_size={self.history_size})"
        )
