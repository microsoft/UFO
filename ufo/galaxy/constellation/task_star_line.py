# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
TaskStarLine - Dependency relationship representation in Constellation V2.

This module defines the TaskStarLine class, representing directed dependency
relationships between tasks with conditional logic support.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from ..core.interfaces import IDependency
from .enums import DependencyType


class TaskStarLine(IDependency):
    """
    Represents a directed dependency relationship (TaskStarLine) between two tasks.

    Each TaskStarLine defines:
    - Source and target task relationship
    - Dependency type (conditional/unconditional)
    - Condition evaluation logic
    - Natural language condition description

    Implements IDependency interface for consistent dependency operations.
    """

    def __init__(
        self,
        from_task_id: str,
        to_task_id: str,
        dependency_type: DependencyType = DependencyType.UNCONDITIONAL,
        condition_description: Optional[str] = None,
        condition_evaluator: Optional[Callable[[Any], bool]] = None,
        line_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize a TaskStarLine.

        :param from_task_id: ID of the prerequisite task
        :param to_task_id: ID of the task that depends on from_task_id
        :param dependency_type: Type of dependency relationship
        :param condition_description: Natural language description of the condition
        :param condition_evaluator: Function to evaluate if condition is met
        :param line_id: Unique identifier for this dependency (auto-generated if None)
        :param metadata: Additional metadata for the dependency
        :return: None
        """
        self._line_id: str = line_id or str(uuid.uuid4())
        self._from_task_id: str = from_task_id
        self._to_task_id: str = to_task_id
        self._dependency_type: DependencyType = dependency_type
        self._condition_description: str = condition_description or ""
        self._condition_evaluator: Optional[Callable[[Any], bool]] = condition_evaluator
        self._metadata: Dict[str, Any] = metadata or {}

        # Tracking
        self._created_at: datetime = datetime.now(timezone.utc)
        self._updated_at: datetime = self._created_at
        self._is_satisfied: bool = False
        self._last_evaluation_result: Optional[bool] = None
        self._last_evaluation_time: Optional[datetime] = None

    @property
    def line_id(self) -> str:
        """Get the line ID."""
        return self._line_id

    @property
    def from_task_id(self) -> str:
        """Get the source task ID."""
        return self._from_task_id

    @property
    def to_task_id(self) -> str:
        """Get the target task ID."""
        return self._to_task_id

    @property
    def source_task_id(self) -> str:
        """Get the source task ID (implements IDependency interface)."""
        return self._from_task_id

    @property
    def target_task_id(self) -> str:
        """Get the target task ID (implements IDependency interface)."""
        return self._to_task_id

    @property
    def dependency_type(self) -> DependencyType:
        """Get the dependency type."""
        return self._dependency_type

    @dependency_type.setter
    def dependency_type(self, value: DependencyType) -> None:
        """Set the dependency type."""
        self._dependency_type = value
        self._updated_at = datetime.now(timezone.utc)
        # Reset satisfaction status when type changes
        self._is_satisfied = False
        self._last_evaluation_result = None

    @property
    def condition_description(self) -> str:
        """Get the condition description."""
        return self._condition_description

    @condition_description.setter
    def condition_description(self, value: str) -> None:
        """Set the condition description."""
        self._condition_description = value
        self._updated_at = datetime.now(timezone.utc)

    def is_satisfied(self, completed_tasks: Optional[List[str]] = None) -> bool:
        """
        Check if the dependency is satisfied.

        :param completed_tasks: List of completed task IDs (for interface compatibility)
        :return: True if dependency is satisfied
        """
        if completed_tasks is not None:
            # Interface-compliant check: dependency is satisfied if source task is completed
            return self._from_task_id in completed_tasks
        return self._is_satisfied

    @property
    def last_evaluation_result(self) -> Optional[bool]:
        """Get the last condition evaluation result."""
        return self._last_evaluation_result

    @property
    def last_evaluation_time(self) -> Optional[datetime]:
        """Get the time of last condition evaluation."""
        return self._last_evaluation_time

    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Get the last update timestamp."""
        return self._updated_at

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get a copy of the metadata."""
        return self._metadata.copy()

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update the metadata.

        :param metadata: Metadata to merge
        :return: None
        """
        self._metadata.update(metadata)
        self._updated_at = datetime.now(timezone.utc)

    def set_condition_evaluator(self, evaluator: Callable[[Any], bool]) -> None:
        """
        Set the condition evaluator function.

        :param evaluator: Function that takes task result and returns bool
        :return: None
        """
        self._condition_evaluator = evaluator
        self._updated_at = datetime.now(timezone.utc)
        # Reset satisfaction status when evaluator changes
        self._is_satisfied = False
        self._last_evaluation_result = None

    def evaluate_condition(self, prerequisite_result: Any) -> bool:
        """
        Evaluate if the dependency condition is satisfied.

        :param prerequisite_result: Result from the prerequisite task
        :return: True if condition is satisfied, False otherwise
        """
        self._last_evaluation_time = datetime.now(timezone.utc)

        try:
            if self._dependency_type == DependencyType.UNCONDITIONAL:
                result = True
            elif self._dependency_type == DependencyType.SUCCESS_ONLY:
                # Only satisfied if prerequisite completed successfully
                result = prerequisite_result is not None
            elif self._dependency_type == DependencyType.COMPLETION_ONLY:
                # Satisfied regardless of success/failure
                result = True
            elif self._dependency_type == DependencyType.CONDITIONAL:
                if self._condition_evaluator:
                    result = self._condition_evaluator(prerequisite_result)
                else:
                    # If no evaluator, default to success-only behavior
                    result = prerequisite_result is not None
            else:
                result = False

            self._last_evaluation_result = result
            self._is_satisfied = result

            return result

        except Exception as e:
            # Log the error but don't propagate it
            self._last_evaluation_result = False
            self._is_satisfied = False
            return False

    def mark_satisfied(self) -> None:
        """Mark the dependency as satisfied (for manual override)."""
        self._is_satisfied = True
        self._last_evaluation_result = True
        self._last_evaluation_time = datetime.now(timezone.utc)
        self._updated_at = self._last_evaluation_time

    def reset_satisfaction(self) -> None:
        """Reset the satisfaction status."""
        self._is_satisfied = False
        self._last_evaluation_result = None
        self._last_evaluation_time = None
        self._updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the TaskStarLine to a dictionary representation.

        :return: Dictionary representation of the TaskStarLine
        """
        return {
            "line_id": self._line_id,
            "from_task_id": self._from_task_id,
            "to_task_id": self._to_task_id,
            "dependency_type": self._dependency_type.value,
            "condition_description": self._condition_description,
            "metadata": self._metadata,
            "is_satisfied": self._is_satisfied,
            "last_evaluation_result": self._last_evaluation_result,
            "last_evaluation_time": (
                self._last_evaluation_time.isoformat()
                if self._last_evaluation_time
                else None
            ),
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskStarLine":
        """
        Create a TaskStarLine from a dictionary representation.

        :param data: Dictionary representation
        :return: TaskStarLine instance
        """
        line = cls(
            from_task_id=data["from_task_id"],
            to_task_id=data["to_task_id"],
            dependency_type=DependencyType(
                data.get("dependency_type", DependencyType.UNCONDITIONAL.value)
            ),
            condition_description=data.get("condition_description"),
            line_id=data.get("line_id"),
            metadata=data.get("metadata", {}),
        )

        # Restore state
        line._is_satisfied = data.get("is_satisfied", False)
        line._last_evaluation_result = data.get("last_evaluation_result")

        # Restore timestamps
        if data.get("created_at"):
            line._created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            line._updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("last_evaluation_time"):
            line._last_evaluation_time = datetime.fromisoformat(
                data["last_evaluation_time"]
            )

        return line

    @classmethod
    def create_unconditional(
        cls,
        from_task_id: str,
        to_task_id: str,
        description: str = "Unconditional dependency",
    ) -> "TaskStarLine":
        """
        Create an unconditional dependency.

        :param from_task_id: Prerequisite task ID
        :param to_task_id: Dependent task ID
        :param description: Description of the dependency
        :return: TaskStarLine instance
        """
        return cls(
            from_task_id=from_task_id,
            to_task_id=to_task_id,
            dependency_type=DependencyType.UNCONDITIONAL,
            condition_description=description,
        )

    @classmethod
    def create_success_only(
        cls,
        from_task_id: str,
        to_task_id: str,
        description: str = "Success-only dependency",
    ) -> "TaskStarLine":
        """
        Create a success-only dependency.

        :param from_task_id: Prerequisite task ID
        :param to_task_id: Dependent task ID
        :param description: Description of the dependency
        :return: TaskStarLine instance
        """
        return cls(
            from_task_id=from_task_id,
            to_task_id=to_task_id,
            dependency_type=DependencyType.SUCCESS_ONLY,
            condition_description=description,
        )

    @classmethod
    def create_conditional(
        cls,
        from_task_id: str,
        to_task_id: str,
        condition_description: str,
        condition_evaluator: Callable[[Any], bool],
    ) -> "TaskStarLine":
        """
        Create a conditional dependency.

        :param from_task_id: Prerequisite task ID
        :param to_task_id: Dependent task ID
        :param condition_description: Natural language description of condition
        :param condition_evaluator: Function to evaluate the condition
        :return: TaskStarLine instance
        """
        return cls(
            from_task_id=from_task_id,
            to_task_id=to_task_id,
            dependency_type=DependencyType.CONDITIONAL,
            condition_description=condition_description,
            condition_evaluator=condition_evaluator,
        )

    def __str__(self) -> str:
        """String representation of the TaskStarLine."""
        return f"TaskStarLine({self._from_task_id} -> {self._to_task_id}, {self._dependency_type.value})"

    def __repr__(self) -> str:
        """Detailed representation of the TaskStarLine."""
        return (
            f"TaskStarLine(line_id={self._line_id!r}, "
            f"from_task={self._from_task_id!r}, "
            f"to_task={self._to_task_id!r}, "
            f"type={self._dependency_type.value!r}, "
            f"satisfied={self._is_satisfied})"
        )
