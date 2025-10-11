# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Command History Management

Manages command execution history with undo/redo capabilities.
"""

from typing import List, Optional

from .command_interface import CommandUndoError, IUndoableCommand


class CommandHistory:
    """
    Manages command execution history for undo/redo operations.

    Provides a stack-based approach to command history management
    with support for undo/redo operations.
    """

    def __init__(self, max_history_size: int = 100):
        """
        Initialize command history.

        :param max_history_size: Maximum number of commands to keep in history
        """
        self._history: List[IUndoableCommand] = []
        self._current_index: int = -1
        self._max_history_size: int = max_history_size

    def add_command(self, command: IUndoableCommand) -> None:
        """
        Add a command to the history.

        :param command: Command to add to history
        """
        # Remove any commands after current index (redo stack)
        if self._current_index < len(self._history) - 1:
            self._history = self._history[: self._current_index + 1]

        # Add the new command
        self._history.append(command)
        self._current_index += 1

        # Maintain max history size
        if len(self._history) > self._max_history_size:
            self._history.pop(0)
            self._current_index -= 1

    def can_undo(self) -> bool:
        """
        Check if undo is possible.

        :return: True if undo is possible, False otherwise
        """
        return (
            self._current_index >= 0
            and self._current_index < len(self._history)
            and self._history[self._current_index].can_undo()
        )

    def can_redo(self) -> bool:
        """
        Check if redo is possible.

        :return: True if redo is possible, False otherwise
        """
        next_index = self._current_index + 1
        return (
            next_index < len(self._history) and self._history[next_index].can_execute()
        )

    def undo(self) -> Optional[IUndoableCommand]:
        """
        Undo the last command.

        :return: The undone command, or None if undo not possible
        :raises: CommandUndoError if undo fails
        """
        if not self.can_undo():
            return None

        command = self._history[self._current_index]
        try:
            command.undo()
            self._current_index -= 1
            return command
        except Exception as e:
            raise CommandUndoError(command, str(e), e)

    def redo(self) -> Optional[IUndoableCommand]:
        """
        Redo the next command.

        :return: The redone command, or None if redo not possible
        :raises: CommandExecutionError if redo fails
        """
        if not self.can_redo():
            return None

        self._current_index += 1
        command = self._history[self._current_index]
        try:
            command.execute()
            return command
        except Exception as e:
            self._current_index -= 1  # Revert index on failure
            from .command_interface import CommandExecutionError

            raise CommandExecutionError(command, str(e), e)

    def clear(self) -> None:
        """Clear the command history."""
        self._history.clear()
        self._current_index = -1

    def get_history(self) -> List[IUndoableCommand]:
        """
        Get a copy of the command history.

        :return: List of commands in history
        """
        return self._history.copy()

    def get_current_command(self) -> Optional[IUndoableCommand]:
        """
        Get the current command (last executed).

        :return: Current command or None if no commands executed
        """
        if self._current_index >= 0 and self._current_index < len(self._history):
            return self._history[self._current_index]
        return None

    def get_undo_description(self) -> Optional[str]:
        """
        Get description of the command that would be undone.

        :return: Description of undoable command, or None if no undo available
        """
        if self.can_undo():
            return f"Undo: {self._history[self._current_index].description}"
        return None

    def get_redo_description(self) -> Optional[str]:
        """
        Get description of the command that would be redone.

        :return: Description of redoable command, or None if no redo available
        """
        if self.can_redo():
            next_index = self._current_index + 1
            return f"Redo: {self._history[next_index].description}"
        return None

    @property
    def size(self) -> int:
        """Get the number of commands in history."""
        return len(self._history)

    @property
    def current_index(self) -> int:
        """Get the current command index."""
        return self._current_index

    def __len__(self) -> int:
        """Get the number of commands in history."""
        return len(self._history)

    def __str__(self) -> str:
        """String representation of command history."""
        return f"CommandHistory(size={len(self._history)}, current_index={self._current_index})"
