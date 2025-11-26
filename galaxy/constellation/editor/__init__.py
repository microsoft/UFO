# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
TaskConstellation Editor Module - Command Pattern Implementation

This module provides a command pattern-based editor for TaskConstellation manipulation.
Supports operations for adding/removing nodes/edges, building constellations, and
comprehensive CRUD operations with undo/redo capabilities.
"""

from .command_interface import ICommand, IUndoableCommand
from .constellation_editor import ConstellationEditor
from .commands import (
    AddTaskCommand,
    RemoveTaskCommand,
    UpdateTaskCommand,
    AddDependencyCommand,
    RemoveDependencyCommand,
    UpdateDependencyCommand,
    BuildConstellationCommand,
    ClearConstellationCommand,
    LoadConstellationCommand,
    SaveConstellationCommand,
)
from .command_invoker import CommandInvoker
from .command_history import CommandHistory

__all__ = [
    "ICommand",
    "IUndoableCommand",
    "ConstellationEditor",
    "AddTaskCommand",
    "RemoveTaskCommand",
    "UpdateTaskCommand",
    "AddDependencyCommand",
    "RemoveDependencyCommand",
    "UpdateDependencyCommand",
    "BuildConstellationCommand",
    "ClearConstellationCommand",
    "LoadConstellationCommand",
    "SaveConstellationCommand",
    "CommandInvoker",
    "CommandHistory",
]
