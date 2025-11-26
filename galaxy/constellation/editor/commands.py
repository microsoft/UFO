# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Concrete Command Implementations

Implements specific commands for TaskConstellation manipulation.
"""

from typing import Any, Dict, Optional

from galaxy.agents.schema import TaskConstellationSchema

from ..task_constellation import TaskConstellation
from ..task_star import TaskStar
from ..task_star_line import TaskStarLine
from .command_interface import CommandExecutionError, CommandUndoError, IUndoableCommand
from .command_registry import register_command


class BaseConstellationCommand(IUndoableCommand):
    """
    Base class for constellation commands.

    Provides common functionality for commands that operate on TaskConstellation.
    """

    def __init__(self, constellation: TaskConstellation, description: str):
        """
        Initialize base constellation command.

        :param constellation: TaskConstellation to operate on
        :param description: Human-readable description of the command
        """
        self._constellation = constellation
        self._description = description
        self._executed = False
        self._backup_data: Optional[Dict[str, Any]] = None

    @property
    def constellation(self) -> TaskConstellation:
        """Get the constellation this command operates on."""
        return self._constellation

    @property
    def description(self) -> str:
        """Get the command description."""
        return self._description

    @property
    def is_executed(self) -> bool:
        """Check if the command has been executed."""
        return self._executed

    def _create_backup(self) -> None:
        """Create a backup of the constellation state."""
        try:
            self._backup_data = self._constellation.to_dict()
        except AttributeError as e:
            raise CommandExecutionError(
                self, f"Constellation missing required attribute: {e}"
            ) from e
        except TypeError as e:
            raise CommandExecutionError(self, f"Type error creating backup: {e}") from e
        except Exception as e:
            raise CommandExecutionError(
                self, f"Unexpected error creating backup: {e}"
            ) from e

    def _restore_backup(self) -> None:
        """Restore the constellation from backup."""
        if not self._backup_data:
            raise CommandUndoError(self, "No backup data available")

        try:
            # Clear current state and restore from backup
            restored = TaskConstellation.from_dict(self._backup_data)

            # Copy restored state to current constellation
            self._constellation._tasks = restored._tasks
            self._constellation._dependencies = restored._dependencies
            self._constellation._state = restored._state
            self._constellation._metadata = restored._metadata
            self._constellation._updated_at = restored._updated_at

        except KeyError as e:
            raise CommandUndoError(self, f"Missing required data in backup: {e}") from e
        except AttributeError as e:
            raise CommandUndoError(
                self, f"Attribute error restoring backup: {e}"
            ) from e
        except Exception as e:
            raise CommandUndoError(
                self, f"Unexpected error restoring backup: {e}"
            ) from e


@register_command(
    name="add_task",
    description="Add a task to the constellation",
    category="task_management",
)
class AddTaskCommand(BaseConstellationCommand):
    """Command to add a task to the constellation."""

    def __init__(self, constellation: TaskConstellation, task_data: dict):
        """
        Initialize add task command.

        :param constellation: TaskConstellation to add task to
        :param task_data: Dictionary containing task data for TaskStar.from_dict()
        """
        # Convert serializable data to TaskStar object
        self._task = TaskStar.from_dict(task_data)
        super().__init__(constellation, f"Add task: {self._task.task_id}")
        self._task_added = False

    def can_execute(self) -> bool:
        """Check if the task can be added."""
        return (
            self._task.task_id not in self._constellation.tasks and not self._executed
        )

    def get_cannot_execute_reason(self) -> str:
        """Get the reason why the command cannot be executed."""
        if self._task.task_id in self._constellation.tasks:
            return (
                f"Task with ID '{self._task.task_id}' already exists in constellation"
            )
        if self._executed:
            return "Command has already been executed"
        return "Unknown reason"

    def execute(self) -> TaskStar:
        """Execute the add task command with validation."""
        if not self.can_execute():
            raise CommandExecutionError(
                self, "Cannot add task - already exists or command already executed"
            )

        self._create_backup()

        try:
            self._constellation.add_task(self._task)

            # Validate constellation after adding
            is_valid, validation_errors = self._constellation.validate_dag()
            if not is_valid:
                # Rollback the operation
                self._restore_backup()
                raise CommandExecutionError(
                    self,
                    f"Task addition resulted in invalid constellation - operation rolled back. Errors: {validation_errors}",
                )

            self._executed = True
            self._task_added = True
            return self._task
        except Exception as e:
            # Ensure rollback on any error
            self._restore_backup()
            raise CommandExecutionError(self, f"Failed to add task: {e}")

    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        return self._executed and self._task_added

    def undo(self) -> None:
        """Undo the add task command."""
        if not self.can_undo():
            raise CommandUndoError(
                self, "Cannot undo - command not executed or task not added"
            )

        try:
            self._constellation.remove_task(self._task.task_id)
            self._executed = False
            self._task_added = False
        except Exception as e:
            # If removal fails, restore from backup
            self._restore_backup()
            self._executed = False
            self._task_added = False


@register_command(
    name="remove_task",
    description="Remove a task from the constellation",
    category="task_management",
)
class RemoveTaskCommand(BaseConstellationCommand):
    """Command to remove a task from the constellation."""

    def __init__(self, constellation: TaskConstellation, task_id: str):
        """
        Initialize remove task command.

        :param constellation: TaskConstellation to remove task from
        :param task_id: ID of task to remove
        """
        super().__init__(constellation, f"Remove task: {task_id}")
        self._task_id = task_id
        self._removed_task: Optional[TaskStar] = None
        self._removed_dependencies: list = []

    def can_execute(self) -> bool:
        """Check if the task can be removed."""
        task = self._constellation.get_task(self._task_id)
        return (
            task is not None
            and not self._executed
            and task.status.name != "RUNNING"  # Cannot remove running tasks
        )

    def get_cannot_execute_reason(self) -> str:
        """Get the reason why the command cannot be executed."""
        task = self._constellation.get_task(self._task_id)
        if task is None:
            existing_ids = list(self._constellation.tasks.keys())
            return f"Task with ID '{self._task_id}' not found in constellation. Existing task IDs: {existing_ids}"
        if task.status.name == "RUNNING":
            return (
                f"Cannot remove task '{self._task_id}' because it is currently running"
            )
        if self._executed:
            return "Command has already been executed"
        return "Unknown reason"

    def execute(self) -> str:
        """Execute the remove task command."""
        if not self.can_execute():
            raise CommandExecutionError(
                self,
                "Cannot remove task - not found, running, or command already executed",
            )

        self._create_backup()

        try:
            # Store the task being removed for undo
            self._removed_task = self._constellation.get_task(self._task_id)

            # Store dependencies that will be removed
            self._removed_dependencies = []
            for dep in self._constellation.get_all_dependencies():
                if dep.from_task_id == self._task_id or dep.to_task_id == self._task_id:
                    self._removed_dependencies.append(dep)

            self._constellation.remove_task(self._task_id)

            # Validate constellation after removal
            is_valid, validation_errors = self._constellation.validate_dag()
            if not is_valid:
                # Rollback the operation
                self._restore_backup()
                raise CommandExecutionError(
                    self,
                    f"Task removal resulted in invalid constellation - operation rolled back. Errors: {validation_errors}",
                )

            self._executed = True
            return self._task_id

        except Exception as e:
            # Ensure rollback on any error
            self._restore_backup()
            raise CommandExecutionError(self, f"Failed to remove task: {e}")

    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        return self._executed and self._removed_task is not None

    def undo(self) -> None:
        """Undo the remove task command."""
        if not self.can_undo():
            raise CommandUndoError(
                self, "Cannot undo - command not executed or no removed task"
            )

        try:
            # Restore from backup to ensure complete state restoration
            self._restore_backup()
            self._executed = False
            self._removed_task = None
            self._removed_dependencies = []

        except Exception as e:
            raise CommandUndoError(self, f"Failed to undo remove task: {e}")


@register_command(
    name="update_task",
    description="Update fields of a task in the constellation",
    category="task_management",
)
class UpdateTaskCommand(BaseConstellationCommand):
    """Command to update a task in the constellation."""

    def __init__(
        self, constellation: TaskConstellation, task_id: str, updates: Dict[str, Any]
    ):
        """
        Initialize update task command.

        :param constellation: TaskConstellation containing the task
        :param task_id: ID of task to update
        :param updates: Dictionary of field updates
        """
        super().__init__(constellation, f"Update task: {task_id}")
        self._task_id = task_id
        self._updates = updates.copy()
        self._original_values: Dict[str, Any] = {}

    def can_execute(self) -> bool:
        """Check if the task can be updated."""
        task = self._constellation.get_task(self._task_id)
        return task is not None and not self._executed

    def get_cannot_execute_reason(self) -> str:
        """Get the reason why the command cannot be executed."""
        task = self._constellation.get_task(self._task_id)
        if task is None:
            existing_ids = list(self._constellation.tasks.keys())
            return f"Task with ID '{self._task_id}' not found in constellation. Existing task IDs: {existing_ids}"
        if self._executed:
            return "Command has already been executed"
        return "Unknown reason"

    def execute(self) -> TaskStar:
        """Execute the update task command with validation."""
        if not self.can_execute():
            raise CommandExecutionError(
                self, "Cannot update task - not found or command already executed"
            )

        task = self._constellation.get_task(self._task_id)
        self._create_backup()

        try:
            # Store original values for undo
            self._original_values = {}
            for field, new_value in self._updates.items():
                if hasattr(task, field):
                    self._original_values[field] = getattr(task, field)
                    setattr(task, field, new_value)

            # Validate constellation after update
            is_valid, validation_errors = self._constellation.validate_dag()
            if not is_valid:
                # Rollback the operation
                self._restore_backup()
                raise CommandExecutionError(
                    self,
                    f"Task update resulted in invalid constellation - operation rolled back. Errors: {validation_errors}",
                )

            self._executed = True
            return task

        except Exception as e:
            # Ensure rollback on any error
            self._restore_backup()
            raise CommandExecutionError(self, f"Failed to update task: {e}")

    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        return self._executed and bool(self._original_values)

    def undo(self) -> None:
        """Undo the update task command."""
        if not self.can_undo():
            raise CommandUndoError(
                self, "Cannot undo - command not executed or no original values"
            )

        try:
            task = self._constellation.get_task(self._task_id)
            if task:
                for field, original_value in self._original_values.items():
                    setattr(task, field, original_value)

            self._executed = False
            self._original_values = {}

        except Exception as e:
            # If manual restoration fails, use backup
            self._restore_backup()
            self._executed = False
            self._original_values = {}


@register_command(
    name="add_dependency",
    description="Add a dependency to the constellation",
    category="dependency_management",
)
class AddDependencyCommand(BaseConstellationCommand):
    """Command to add a dependency to the constellation."""

    def __init__(self, constellation: TaskConstellation, dependency_data: dict):
        """
        Initialize add dependency command.

        :param constellation: TaskConstellation to add dependency to
        :param dependency_data: Dictionary containing dependency data for TaskStarLine.from_dict()
        """
        # Convert serializable data to TaskStarLine object
        self._dependency = TaskStarLine.from_dict(dependency_data)
        super().__init__(
            constellation,
            f"Add dependency: {self._dependency.from_task_id} -> {self._dependency.to_task_id}",
        )
        self._dependency_added = False

    def can_execute(self) -> bool:
        """Check if the dependency can be added."""
        return (
            self._dependency.line_id not in self._constellation.dependencies
            and not self._executed
            and self._dependency.from_task_id in self._constellation.tasks
            and self._dependency.to_task_id in self._constellation.tasks
        )

    def get_cannot_execute_reason(self) -> str:
        """Get the reason why the command cannot be executed."""
        if self._dependency.line_id in self._constellation.dependencies:
            return f"Dependency with ID '{self._dependency.line_id}' already exists in constellation"
        if self._dependency.from_task_id not in self._constellation.tasks:
            existing_task_ids = list(self._constellation.tasks.keys())
            return f"Source task '{self._dependency.from_task_id}' not found in constellation. Existing task IDs: {existing_task_ids}"
        if self._dependency.to_task_id not in self._constellation.tasks:
            existing_task_ids = list(self._constellation.tasks.keys())
            return f"Target task '{self._dependency.to_task_id}' not found in constellation. Existing task IDs: {existing_task_ids}"
        if self._executed:
            return "Command has already been executed"
        return "Unknown reason"

    def execute(self) -> TaskStarLine:
        """Execute the add dependency command with validation."""
        if not self.can_execute():
            raise CommandExecutionError(
                self,
                "Cannot add dependency - already exists, tasks missing, or command already executed",
            )

        self._create_backup()

        try:
            self._constellation.add_dependency(self._dependency)

            # Validate constellation after adding
            is_valid, validation_errors = self._constellation.validate_dag()
            if not is_valid:
                # Rollback the operation
                self._restore_backup()
                raise CommandExecutionError(
                    self,
                    f"Dependency addition resulted in invalid constellation - operation rolled back. Errors: {validation_errors}",
                )

            self._executed = True
            self._dependency_added = True
            return self._dependency
        except Exception as e:
            # Ensure rollback on any error
            self._restore_backup()
            raise CommandExecutionError(self, f"Failed to add dependency: {e}")

    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        return self._executed and self._dependency_added

    def undo(self) -> None:
        """Undo the add dependency command."""
        if not self.can_undo():
            raise CommandUndoError(
                self, "Cannot undo - command not executed or dependency not added"
            )

        try:
            self._constellation.remove_dependency(self._dependency.line_id)
            self._executed = False
            self._dependency_added = False
        except Exception as e:
            # If removal fails, restore from backup
            self._restore_backup()
            self._executed = False
            self._dependency_added = False


@register_command(
    name="remove_dependency",
    description="Remove a dependency from the constellation",
    category="dependency_management",
)
class RemoveDependencyCommand(BaseConstellationCommand):
    """Command to remove a dependency from the constellation."""

    def __init__(self, constellation: TaskConstellation, dependency_id: str):
        """
        Initialize remove dependency command.

        :param constellation: TaskConstellation to remove dependency from
        :param dependency_id: ID of dependency to remove
        """
        super().__init__(constellation, f"Remove dependency: {dependency_id}")
        self._dependency_id = dependency_id
        self._removed_dependency: Optional[TaskStarLine] = None

    def can_execute(self) -> bool:
        """Check if the dependency can be removed."""
        return (
            self._dependency_id in self._constellation.dependencies
            and not self._executed
        )

    def get_cannot_execute_reason(self) -> str:
        """Get the reason why the command cannot be executed."""
        if self._dependency_id not in self._constellation.dependencies:
            existing_dep_ids = list(self._constellation.dependencies.keys())
            return f"Dependency with ID '{self._dependency_id}' not found in constellation. Existing dependency IDs: {existing_dep_ids}"
        if self._executed:
            return "Command has already been executed"
        return "Unknown reason"

    def execute(self) -> str:
        """Execute the remove dependency command."""
        if not self.can_execute():
            raise CommandExecutionError(
                self, "Cannot remove dependency - not found or command already executed"
            )

        self._create_backup()

        try:
            # Store the dependency being removed for undo
            self._removed_dependency = self._constellation.get_dependency(
                self._dependency_id
            )

            self._constellation.remove_dependency(self._dependency_id)

            # Validate constellation after removal
            is_valid, validation_errors = self._constellation.validate_dag()
            if not is_valid:
                # Rollback the operation
                self._restore_backup()
                raise CommandExecutionError(
                    self,
                    f"Dependency removal resulted in invalid constellation - operation rolled back. Errors: {validation_errors}",
                )

            self._executed = True
            return self._dependency_id

        except Exception as e:
            # Ensure rollback on any error
            self._restore_backup()
            raise CommandExecutionError(self, f"Failed to remove dependency: {e}")

    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        return self._executed and self._removed_dependency is not None

    def undo(self) -> None:
        """Undo the remove dependency command."""
        if not self.can_undo():
            raise CommandUndoError(
                self, "Cannot undo - command not executed or no removed dependency"
            )

        try:
            # Restore from backup to ensure complete state restoration
            self._restore_backup()
            self._executed = False
            self._removed_dependency = None

        except Exception as e:
            raise CommandUndoError(self, f"Failed to undo remove dependency: {e}")


@register_command(
    name="update_dependency",
    description="Update fields of a dependency in the constellation",
    category="dependency_management",
)
class UpdateDependencyCommand(BaseConstellationCommand):
    """Command to update a dependency in the constellation."""

    def __init__(
        self,
        constellation: TaskConstellation,
        dependency_id: str,
        updates: Dict[str, Any],
    ):
        """
        Initialize update dependency command.

        :param constellation: TaskConstellation containing the dependency
        :param dependency_id: ID of dependency to update
        :param updates: Dictionary of field updates
        """
        super().__init__(constellation, f"Update dependency: {dependency_id}")
        self._dependency_id = dependency_id
        self._updates = updates.copy()
        self._original_values: Dict[str, Any] = {}

    def can_execute(self) -> bool:
        """Check if the dependency can be updated."""
        dependency = self._constellation.get_dependency(self._dependency_id)
        return dependency is not None and not self._executed

    def get_cannot_execute_reason(self) -> str:
        """Get the reason why the command cannot be executed."""
        dependency = self._constellation.get_dependency(self._dependency_id)
        if dependency is None:
            existing_dep_ids = list(self._constellation.dependencies.keys())
            return f"Dependency with ID '{self._dependency_id}' not found in constellation. Existing dependency IDs: {existing_dep_ids}"
        if self._executed:
            return "Command has already been executed"
        return "Unknown reason"

    def execute(self) -> TaskStarLine:
        """Execute the update dependency command with validation."""
        if not self.can_execute():
            raise CommandExecutionError(
                self, "Cannot update dependency - not found or command already executed"
            )

        dependency = self._constellation.get_dependency(self._dependency_id)
        self._create_backup()

        try:
            # Store original values for undo
            self._original_values = {}
            for field, new_value in self._updates.items():
                if hasattr(dependency, field):
                    self._original_values[field] = getattr(dependency, field)
                    setattr(dependency, field, new_value)

            # Validate constellation after update
            is_valid, validation_errors = self._constellation.validate_dag()
            if not is_valid:
                # Rollback the operation
                self._restore_backup()
                raise CommandExecutionError(
                    self,
                    f"Dependency update resulted in invalid constellation - operation rolled back. Errors: {validation_errors}",
                )

            self._executed = True
            return dependency

        except Exception as e:
            # Ensure rollback on any error
            self._restore_backup()
            raise CommandExecutionError(self, f"Failed to update dependency: {e}")

    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        return self._executed and bool(self._original_values)

    def undo(self) -> None:
        """Undo the update dependency command."""
        if not self.can_undo():
            raise CommandUndoError(
                self, "Cannot undo - command not executed or no original values"
            )

        try:
            dependency = self._constellation.get_dependency(self._dependency_id)
            if dependency:
                for field, original_value in self._original_values.items():
                    setattr(dependency, field, original_value)

            self._executed = False
            self._original_values = {}

        except Exception as e:
            # If manual restoration fails, use backup
            self._restore_backup()
            self._executed = False
            self._original_values = {}


@register_command(
    name="build_constellation",
    description="Build a constellation from configuration data",
    category="bulk_operations",
)
class BuildConstellationCommand(BaseConstellationCommand):
    """Command to build a constellation from a configuration."""

    def __init__(
        self,
        constellation: TaskConstellation,
        config: TaskConstellationSchema,
        clear_existing: bool = True,
    ):
        """
        Initialize build constellation command.

        :param constellation: TaskConstellation to build
        :param config: Configuration dictionary
        :param clear_existing: Whether to clear existing tasks/dependencies
        """
        super().__init__(constellation, f"Build constellation: {config.name}")
        self._config = config.model_copy()
        self._clear_existing = clear_existing
        self._original_state: Optional[Dict[str, Any]] = None

    def can_execute(self) -> bool:
        """Check if the constellation can be built."""
        return not self._executed and bool(self._config)

    def get_cannot_execute_reason(self) -> str:
        """Get the reason why the command cannot be executed."""
        if not bool(self._config):
            return "Configuration is empty or invalid"
        if self._executed:
            return "Command has already been executed"
        return "Unknown reason"

    def execute(self) -> TaskConstellation:
        """Execute the build constellation command."""
        if not self.can_execute():
            raise CommandExecutionError(
                self, "Cannot build constellation - already executed or invalid config"
            )

        self._create_backup()

        try:

            self._constellation = TaskConstellation.from_basemodel(self._config)

            # Validate constellation after building
            is_valid, validation_errors = self._constellation.validate_dag()
            if not is_valid:
                # Rollback the operation
                self._restore_backup()
                raise CommandExecutionError(
                    self,
                    f"Constellation build resulted in invalid constellation - operation rolled back. Errors: {validation_errors}",
                )

            self._executed = True
            return self._constellation

        except Exception as e:
            # Ensure rollback on any error
            self._restore_backup()
            raise CommandExecutionError(self, f"Failed to build constellation: {e}")

    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        return self._executed and self._backup_data is not None

    def undo(self) -> None:
        """Undo the build constellation command."""
        if not self.can_undo():
            raise CommandUndoError(
                self, "Cannot undo - command not executed or no backup available"
            )

        try:
            self._restore_backup()
            self._executed = False
        except Exception as e:
            raise CommandUndoError(self, f"Failed to undo build constellation: {e}")


@register_command(
    name="clear_constellation",
    description="Clear all tasks and dependencies from the constellation",
    category="bulk_operations",
)
class ClearConstellationCommand(BaseConstellationCommand):
    """Command to clear all tasks and dependencies from the constellation."""

    def __init__(self, constellation: TaskConstellation):
        """
        Initialize clear constellation command.

        :param constellation: TaskConstellation to clear
        """
        super().__init__(constellation, "Clear constellation")

    def can_execute(self) -> bool:
        """Check if the constellation can be cleared."""
        return not self._executed

    def get_cannot_execute_reason(self) -> str:
        """Get the reason why the command cannot be executed."""
        if self._executed:
            return "Command has already been executed"
        return "Unknown reason"

    def execute(self) -> TaskConstellation:
        """Execute the clear constellation command with validation."""
        if not self.can_execute():
            raise CommandExecutionError(
                self, "Cannot clear constellation - already executed"
            )

        self._create_backup()

        try:
            # Remove all tasks (this will also remove dependencies)
            for task_id in list(self._constellation.tasks.keys()):
                self._constellation.remove_task(task_id)

            # Validate constellation after clearing (should always be valid when empty)
            is_valid, validation_errors = self._constellation.validate_dag()
            if not is_valid:
                # Rollback the operation
                self._restore_backup()
                raise CommandExecutionError(
                    self,
                    f"Constellation clear resulted in invalid constellation - operation rolled back. Errors: {validation_errors}",
                )

            self._executed = True
            return self._constellation

        except Exception as e:
            # Ensure rollback on any error
            self._restore_backup()
            raise CommandExecutionError(self, f"Failed to clear constellation: {e}")

    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        return self._executed and self._backup_data is not None

    def undo(self) -> None:
        """Undo the clear constellation command."""
        if not self.can_undo():
            raise CommandUndoError(
                self, "Cannot undo - command not executed or no backup available"
            )

        try:
            self._restore_backup()
            self._executed = False
        except Exception as e:
            raise CommandUndoError(self, f"Failed to undo clear constellation: {e}")


@register_command(
    name="load_constellation",
    description="Load a constellation from JSON file",
    category="file_operations",
)
class LoadConstellationCommand(BaseConstellationCommand):
    """Command to load a constellation from JSON file."""

    def __init__(self, constellation: TaskConstellation, file_path: str):
        """
        Initialize load constellation command.

        :param constellation: TaskConstellation to load into
        :param file_path: Path to JSON file
        """
        super().__init__(constellation, f"Load constellation from: {file_path}")
        self._file_path = file_path

    def can_execute(self) -> bool:
        """Check if the constellation can be loaded."""
        import os

        return not self._executed and os.path.exists(self._file_path)

    def get_cannot_execute_reason(self) -> str:
        """Get the reason why the command cannot be executed."""
        import os

        if not os.path.exists(self._file_path):
            return f"File '{self._file_path}' not found"
        if self._executed:
            return "Command has already been executed"
        return "Unknown reason"

    def execute(self) -> TaskConstellation:
        """Execute the load constellation command with validation."""
        if not self.can_execute():
            raise CommandExecutionError(
                self, "Cannot load constellation - already executed or file not found"
            )

        self._create_backup()

        try:
            loaded_constellation = TaskConstellation.from_json(
                file_path=self._file_path
            )

            # Copy loaded state to current constellation
            self._constellation._tasks = loaded_constellation._tasks
            self._constellation._dependencies = loaded_constellation._dependencies
            self._constellation._state = loaded_constellation._state
            self._constellation._metadata = loaded_constellation._metadata
            self._constellation._name = loaded_constellation._name

            # Validate constellation after loading
            is_valid, validation_errors = self._constellation.validate_dag()
            if not is_valid:
                # Rollback the operation
                self._restore_backup()
                raise CommandExecutionError(
                    self,
                    f"Loaded constellation is invalid - operation rolled back. Errors: {validation_errors}",
                )

            self._executed = True
            return self._constellation

        except Exception as e:
            # Ensure rollback on any error
            self._restore_backup()
            raise CommandExecutionError(self, f"Failed to load constellation: {e}")

    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        return self._executed and self._backup_data is not None

    def undo(self) -> None:
        """Undo the load constellation command."""
        if not self.can_undo():
            raise CommandUndoError(
                self, "Cannot undo - command not executed or no backup available"
            )

        try:
            self._restore_backup()
            self._executed = False
        except Exception as e:
            raise CommandUndoError(self, f"Failed to undo load constellation: {e}")


@register_command(
    name="save_constellation",
    description="Save a constellation to JSON file",
    category="file_operations",
)
class SaveConstellationCommand(BaseConstellationCommand):
    """Command to save a constellation to JSON file."""

    def __init__(self, constellation: TaskConstellation, file_path: str):
        """
        Initialize save constellation command.

        :param constellation: TaskConstellation to save
        :param file_path: Path to save JSON file
        """
        super().__init__(constellation, f"Save constellation to: {file_path}")
        self._file_path = file_path
        self._file_existed = False
        self._backup_file_content: Optional[str] = None

    def can_execute(self) -> bool:
        """Check if the constellation can be saved."""
        return not self._executed

    def get_cannot_execute_reason(self) -> str:
        """Get the reason why the command cannot be executed."""
        if self._executed:
            return "Command has already been executed"
        return "Unknown reason"

    def execute(self) -> str:
        """Execute the save constellation command."""
        if not self.can_execute():
            raise CommandExecutionError(
                self, "Cannot save constellation - already executed"
            )

        import os

        try:
            # Backup existing file if it exists
            self._file_existed = os.path.exists(self._file_path)
            if self._file_existed:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    self._backup_file_content = f.read()

            # Save constellation
            self._constellation.to_json(save_path=self._file_path)

            self._executed = True
            return self._file_path

        except Exception as e:
            raise CommandExecutionError(self, f"Failed to save constellation: {e}")

    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        return self._executed

    def undo(self) -> None:
        """Undo the save constellation command."""
        if not self.can_undo():
            raise CommandUndoError(self, "Cannot undo - command not executed")

        import os

        try:
            if self._file_existed and self._backup_file_content is not None:
                # Restore original file content
                with open(self._file_path, "w", encoding="utf-8") as f:
                    f.write(self._backup_file_content)
            elif not self._file_existed and os.path.exists(self._file_path):
                # Remove the file we created
                os.remove(self._file_path)

            self._executed = False

        except Exception as e:
            raise CommandUndoError(self, f"Failed to undo save constellation: {e}")
