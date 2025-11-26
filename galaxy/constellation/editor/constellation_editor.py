# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
TaskConstellation Editor

Main editor class providing high-level interface for constellation manipulation
using the command pattern.
"""

from typing import Any, Dict, List, Optional, Union

from galaxy.agents.schema import TaskConstellationSchema

from ..task_constellation import TaskConstellation
from ..task_star import TaskStar
from ..task_star_line import TaskStarLine
from .command_invoker import CommandInvoker
from .command_registry import command_registry
from .commands import (
    AddDependencyCommand,
    AddTaskCommand,
    BuildConstellationCommand,
    ClearConstellationCommand,
    LoadConstellationCommand,
    RemoveDependencyCommand,
    RemoveTaskCommand,
    SaveConstellationCommand,
    UpdateDependencyCommand,
    UpdateTaskCommand,
)


class ConstellationEditor:
    """
    High-level editor for TaskConstellation manipulation.

    Provides a command pattern-based interface for comprehensive
    constellation editing operations with undo/redo support.
    """

    def __init__(
        self,
        constellation: Optional[TaskConstellation] = None,
        enable_history: bool = True,
        max_history_size: int = 100,
    ):
        """
        Initialize constellation editor.

        :param constellation: TaskConstellation to edit (creates new if None)
        :param enable_history: Whether to enable command history
        :param max_history_size: Maximum number of commands in history
        """
        self._constellation = constellation or TaskConstellation()
        self._invoker = CommandInvoker(enable_history, max_history_size)
        self._observers: List[callable] = []

    @property
    def constellation(self) -> TaskConstellation:
        """Get the constellation being edited."""
        return self._constellation

    @property
    def invoker(self) -> CommandInvoker:
        """Get the command invoker."""
        return self._invoker

    def add_observer(self, observer: callable) -> None:
        """
        Add an observer for constellation changes.

        :param observer: Callable that receives (editor, command, result) on each operation
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: callable) -> None:
        """
        Remove an observer.

        :param observer: Observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self, command: str, result: Any) -> None:
        """Notify all observers of a command execution."""
        for observer in self._observers:
            try:
                observer(self, command, result)
            except Exception:
                pass  # Silently ignore observer errors

    # Task Management Operations

    def add_task(self, task: Union[TaskStar, Dict[str, Any]]) -> TaskStar:
        """
        Add a task to the constellation.

        :param task: TaskStar object or dict with task data
        :return: The added task
        :raises: CommandExecutionError if operation fails
        """
        if isinstance(task, TaskStar):
            task_data = task.to_dict()
        else:
            task_data = task

        command = AddTaskCommand(self._constellation, task_data)
        result = self._invoker.execute(command)
        self._notify_observers("add_task", result)
        return result

    def create_and_add_task(
        self, task_id: str, description: str, name: str = "", **kwargs
    ) -> TaskStar:
        """
        Create and add a new task to the constellation.

        :param task_id: Unique identifier for the task
        :param description: Description of the task
        :param name: Name of the task
        :param kwargs: Additional task parameters
        :return: The created and added task
        """
        task = TaskStar(task_id=task_id, description=description, name=name, **kwargs)
        return self.add_task(task)

    def remove_task(self, task_id: str) -> str:
        """
        Remove a task from the constellation.

        :param task_id: ID of task to remove
        :return: The removed task ID
        :raises: CommandExecutionError if operation fails
        """
        command = RemoveTaskCommand(self._constellation, task_id)
        result = self._invoker.execute(command)
        self._notify_observers("remove_task", result)
        return result

    def update_task(self, task_id: str, **updates) -> TaskStar:
        """
        Update a task in the constellation.

        :param task_id: ID of task to update
        :param updates: Field updates as keyword arguments
        :return: The updated task
        :raises: CommandExecutionError if operation fails
        """
        command = UpdateTaskCommand(self._constellation, task_id, updates)
        result = self._invoker.execute(command)
        self._notify_observers("update_task", result)
        return result

    def get_task(self, task_id: str) -> Optional[TaskStar]:
        """
        Get a task by ID.

        :param task_id: ID of the task
        :return: TaskStar instance or None if not found
        """
        return self._constellation.get_task(task_id)

    def list_tasks(self) -> List[TaskStar]:
        """
        Get all tasks in the constellation.

        :return: List of all tasks
        """
        return self._constellation.get_all_tasks()

    # Dependency Management Operations

    def add_dependency(
        self, dependency: Union[TaskStarLine, Dict[str, Any]]
    ) -> TaskStarLine:
        """
        Add a dependency to the constellation.

        :param dependency: TaskStarLine object or dict with dependency data
        :return: The added dependency
        :raises: CommandExecutionError if operation fails
        """
        if isinstance(dependency, TaskStarLine):
            dependency_data = dependency.to_dict()
        else:
            dependency_data = dependency

        command = AddDependencyCommand(self._constellation, dependency_data)
        result = self._invoker.execute(command)
        self._notify_observers("add_dependency", result)
        return result

    def create_and_add_dependency(
        self,
        from_task_id: str,
        to_task_id: str,
        dependency_type: str = "UNCONDITIONAL",
        **kwargs,
    ) -> TaskStarLine:
        """
        Create and add a new dependency to the constellation.

        :param from_task_id: Source task ID
        :param to_task_id: Target task ID
        :param dependency_type: Type of dependency
        :param kwargs: Additional dependency parameters
        :return: The created and added dependency
        """
        from ..enums import DependencyType

        # Convert string to enum if needed
        if isinstance(dependency_type, str):
            dependency_type = DependencyType[dependency_type.upper()]

        dependency = TaskStarLine(
            from_task_id=from_task_id,
            to_task_id=to_task_id,
            dependency_type=dependency_type,
            **kwargs,
        )
        return self.add_dependency(dependency)

    def remove_dependency(self, dependency_id: str) -> str:
        """
        Remove a dependency from the constellation.

        :param dependency_id: ID of dependency to remove
        :return: The removed dependency ID
        :raises: CommandExecutionError if operation fails
        """
        command = RemoveDependencyCommand(self._constellation, dependency_id)
        result = self._invoker.execute(command)
        self._notify_observers("remove_dependency", result)
        return result

    def update_dependency(self, dependency_id: str, **updates) -> TaskStarLine:
        """
        Update a dependency in the constellation.

        :param dependency_id: ID of dependency to update
        :param updates: Field updates as keyword arguments
        :return: The updated dependency
        :raises: CommandExecutionError if operation fails
        """
        command = UpdateDependencyCommand(self._constellation, dependency_id, updates)
        result = self._invoker.execute(command)
        self._notify_observers("update_dependency", result)
        return result

    def get_dependency(self, dependency_id: str) -> Optional[TaskStarLine]:
        """
        Get a dependency by ID.

        :param dependency_id: ID of the dependency
        :return: TaskStarLine instance or None if not found
        """
        return self._constellation.get_dependency(dependency_id)

    def list_dependencies(self) -> List[TaskStarLine]:
        """
        Get all dependencies in the constellation.

        :return: List of all dependencies
        """
        return self._constellation.get_all_dependencies()

    def get_task_dependencies(self, task_id: str) -> List[TaskStarLine]:
        """
        Get dependencies for a specific task.

        :param task_id: ID of the task
        :return: List of dependencies for the task
        """
        return self._constellation.get_task_dependencies(task_id)

    # Bulk Operations

    def build_constellation(
        self, config: TaskConstellationSchema, clear_existing: bool = True
    ) -> TaskConstellation:
        """
        Build constellation from configuration.

        :param config: Configuration dictionary
        :param clear_existing: Whether to clear existing tasks/dependencies
        :return: The built constellation
        :raises: CommandExecutionError if operation fails
        """
        command = BuildConstellationCommand(self._constellation, config, clear_existing)
        result = self._invoker.execute(command)
        self._notify_observers("build_constellation", result)
        self._constellation = result  # Update reference in case of new instance
        return result

    def build_from_tasks_and_dependencies(
        self,
        tasks: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]],
        clear_existing: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskConstellation:
        """
        Build constellation from task and dependency lists.

        :param tasks: List of task configurations
        :param dependencies: List of dependency configurations
        :param clear_existing: Whether to clear existing content
        :param metadata: Optional metadata to set
        :return: The built constellation
        """
        config = {"tasks": tasks, "dependencies": dependencies}
        if metadata:
            config["metadata"] = metadata

        return self.build_constellation(config, clear_existing)

    def clear_constellation(self) -> TaskConstellation:
        """
        Clear all tasks and dependencies from the constellation.

        :return: The cleared constellation
        :raises: CommandExecutionError if operation fails
        """
        command = ClearConstellationCommand(self._constellation)
        result = self._invoker.execute(command)
        self._notify_observers("clear_constellation", result)
        return result

    # File Operations

    def load_constellation(self, file_path: str) -> TaskConstellation:
        """
        Load constellation from JSON file.

        :param file_path: Path to JSON file
        :return: The loaded constellation
        :raises: CommandExecutionError if operation fails
        """
        command = LoadConstellationCommand(self._constellation, file_path)
        result = self._invoker.execute(command)
        self._notify_observers("load_constellation", result)
        return result

    def save_constellation(self, file_path: str) -> str:
        """
        Save constellation to JSON file.

        :param file_path: Path to save JSON file
        :return: The file path
        :raises: CommandExecutionError if operation fails
        """
        command = SaveConstellationCommand(self._constellation, file_path)
        result = self._invoker.execute(command)
        self._notify_observers("save_constellation", result)
        return result

    def load_from_dict(self, data: Dict[str, Any]) -> TaskConstellation:
        """
        Load constellation from dictionary data.

        :param data: Dictionary representation of constellation
        :return: The loaded constellation
        """
        # Create temporary constellation and copy state
        temp_constellation = TaskConstellation.from_dict(data)

        # Use build command to apply the state
        config = temp_constellation.to_dict()
        return self.build_constellation(config, clear_existing=True)

    def load_from_json_string(self, json_string: str) -> TaskConstellation:
        """
        Load constellation from JSON string.

        :param json_string: JSON string representation
        :return: The loaded constellation
        """
        temp_constellation = TaskConstellation.from_json(json_data=json_string)
        config = temp_constellation.to_dict()
        return self.build_constellation(config, clear_existing=True)

    # History Operations

    def undo(self) -> bool:
        """
        Undo the last command.

        :return: True if undo was successful, False if no undo available
        """
        if self._invoker.can_undo():
            command = self._invoker.undo()
            self._notify_observers("undo", command)
            return True
        return False

    def redo(self) -> bool:
        """
        Redo the next command.

        :return: True if redo was successful, False if no redo available
        """
        if self._invoker.can_redo():
            command = self._invoker.redo()
            self._notify_observers("redo", command)
            return True
        return False

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self._invoker.can_undo()

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self._invoker.can_redo()

    def get_undo_description(self) -> Optional[str]:
        """Get description of the command that would be undone."""
        return self._invoker.get_undo_description()

    def get_redo_description(self) -> Optional[str]:
        """Get description of the command that would be redone."""
        return self._invoker.get_redo_description()

    def clear_history(self) -> None:
        """Clear the command history."""
        self._invoker.clear_history()
        self._notify_observers("clear_history", None)

    def get_history(self) -> List[str]:
        """
        Get command history descriptions.

        :return: List of command descriptions
        """
        return [cmd.description for cmd in self._invoker.get_history()]

    # Validation and Analysis

    def validate_constellation(self) -> tuple[bool, List[str]]:
        """
        Validate the constellation structure.

        :return: Tuple of (is_valid, list_of_errors)
        """
        return self._constellation.validate_dag()

    def get_topological_order(self) -> List[str]:
        """
        Get topological ordering of tasks.

        :return: List of task IDs in topological order
        :raises: ValueError if constellation has cycles
        """
        return self._constellation.get_topological_order()

    def has_cycles(self) -> bool:
        """Check if the constellation has any cycles."""
        return self._constellation.has_cycle()

    def get_ready_tasks(self) -> List[TaskStar]:
        """Get tasks that are ready to execute."""
        return self._constellation.get_ready_tasks()

    def get_statistics(self) -> Dict[str, Any]:
        """Get constellation statistics."""
        stats = self._constellation.get_statistics()
        stats.update(
            {
                "editor_execution_count": self._invoker.execution_count,
                "editor_history_size": self._invoker.history_size,
                "editor_can_undo": self.can_undo(),
                "editor_can_redo": self.can_redo(),
            }
        )
        return stats

    # Advanced Operations

    def batch_operations(self, operations: List[callable]) -> List[Any]:
        """
        Execute multiple operations in sequence.

        :param operations: List of callables that take the editor as parameter
        :return: List of operation results
        """
        results = []
        for operation in operations:
            try:
                result = operation(self)
                results.append(result)
            except Exception as e:
                results.append(e)
        return results

    def create_subgraph(self, task_ids: List[str]) -> "ConstellationEditor":
        """
        Create a new editor with a subgraph containing specified tasks.

        :param task_ids: List of task IDs to include in subgraph
        :return: New ConstellationEditor with subgraph
        """
        subgraph_constellation = TaskConstellation(
            name=f"{self._constellation.name}_subgraph"
        )
        subgraph_editor = ConstellationEditor(subgraph_constellation)

        # Add specified tasks
        for task_id in task_ids:
            task = self.get_task(task_id)
            if task:
                # Create a copy of the task for the subgraph
                task_dict = task.to_dict()
                new_task = TaskStar.from_dict(task_dict)
                subgraph_editor.add_task(new_task)

        # Add dependencies between included tasks
        for dependency in self.list_dependencies():
            if (
                dependency.from_task_id in task_ids
                and dependency.to_task_id in task_ids
            ):
                # Create a copy of the dependency for the subgraph
                dep_dict = dependency.to_dict()
                new_dependency = TaskStarLine.from_dict(dep_dict)
                subgraph_editor.add_dependency(new_dependency)

        return subgraph_editor

    def merge_constellation(
        self, other_editor: "ConstellationEditor", prefix: str = ""
    ) -> None:
        """
        Merge another constellation into this one.

        :param other_editor: ConstellationEditor to merge from
        :param prefix: Prefix to add to task IDs to avoid conflicts
        """
        # Create mapping for task ID changes
        id_mapping = {}

        # Add tasks with prefix
        for task in other_editor.list_tasks():
            original_id = task.task_id
            new_id = f"{prefix}{original_id}" if prefix else original_id
            id_mapping[original_id] = new_id

            # Create new task with updated ID
            task_dict = task.to_dict()
            task_dict["task_id"] = new_id
            new_task = TaskStar.from_dict(task_dict)
            self.add_task(new_task)

        # Add dependencies with updated IDs
        for dependency in other_editor.list_dependencies():
            dep_dict = dependency.to_dict()
            dep_dict["from_task_id"] = id_mapping[dependency.from_task_id]
            dep_dict["to_task_id"] = id_mapping[dependency.to_task_id]
            dep_dict["line_id"] = (
                f"{prefix}{dependency.line_id}" if prefix else dependency.line_id
            )

            new_dependency = TaskStarLine.from_dict(dep_dict)
            self.add_dependency(new_dependency)

    # Display and Debug

    def display_constellation(self, mode: str = "overview") -> None:
        """
        Display the constellation using visualization.

        :param mode: Display mode ('overview', 'topology', 'details', 'execution')
        """
        self._constellation.display_dag(mode)

    # Command Registry Methods
    def list_available_commands(
        self, category: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        List all available commands from the registry.

        :param category: Optional category filter
        :return: Dictionary of command names and their metadata
        """
        return command_registry.list_commands(category)

    def get_command_metadata(self, command_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific command.

        :param command_name: Name of the command
        :return: Command metadata or None if not found
        """
        return command_registry.get_command_metadata(command_name)

    def execute_command_by_name(self, command_name: str, *args, **kwargs) -> Any:
        """
        Execute a command by its registered name.

        :param command_name: Name of the registered command
        :param args: Positional arguments for the command
        :param kwargs: Keyword arguments for the command
        :return: Result of command execution
        """
        command = command_registry.create_command(
            command_name, self._constellation, *args, **kwargs
        )
        if command is None:
            raise ValueError(f"Command '{command_name}' not found in registry")

        return self._invoker.execute(command)

    def get_command_categories(self) -> List[str]:
        """
        Get all available command categories.

        :return: List of category names
        """
        return command_registry.get_categories()

    def __str__(self) -> str:
        """String representation of the editor."""
        return (
            f"ConstellationEditor("
            f"constellation={self._constellation.constellation_id}, "
            f"tasks={len(self._constellation.tasks)}, "
            f"dependencies={len(self._constellation.dependencies)}, "
            f"history={self._invoker.history_size})"
        )

    def __repr__(self) -> str:
        """Detailed representation of the editor."""
        return (
            f"ConstellationEditor("
            f"constellation_id={self._constellation.constellation_id!r}, "
            f"tasks={len(self._constellation.tasks)}, "
            f"dependencies={len(self._constellation.dependencies)}, "
            f"execution_count={self._invoker.execution_count}, "
            f"can_undo={self.can_undo()}, "
            f"can_redo={self.can_redo()})"
        )
