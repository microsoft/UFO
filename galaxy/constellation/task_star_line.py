# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
TaskStarLine - Dependency relationship representation in Constellation V2.

This module defines the TaskStarLine class, representing directed dependency
relationships between tasks with conditional logic support.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from ..core.interfaces import IDependency
from .enums import DependencyType

if TYPE_CHECKING:
    from galaxy.agents.schema import TaskStarLineSchema


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

    @staticmethod
    def _parse_dependency_type(dep_type_value: Any) -> DependencyType:
        """
        Parse dependency type value (string or DependencyType) into DependencyType enum.

        :param dep_type_value: Dependency type value to parse
        :return: DependencyType enum instance
        """
        if isinstance(dep_type_value, DependencyType):
            return dep_type_value
        elif isinstance(dep_type_value, str):
            # Map string names to DependencyType
            dep_type_map = {
                "UNCONDITIONAL": DependencyType.UNCONDITIONAL,
                "CONDITIONAL": DependencyType.CONDITIONAL,
                "SUCCESS_ONLY": DependencyType.SUCCESS_ONLY,
                "COMPLETION_ONLY": DependencyType.COMPLETION_ONLY,
            }
            return dep_type_map.get(
                dep_type_value.upper(), DependencyType.UNCONDITIONAL
            )
        else:
            return DependencyType.UNCONDITIONAL

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
            dependency_type=cls._parse_dependency_type(
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
    def from_basemodel(cls, schema: "TaskStarLineSchema") -> "TaskStarLine":
        """
        Create a TaskStarLine from a Pydantic BaseModel schema.

        :param schema: TaskStarLineSchema instance
        :return: TaskStarLine instance
        """
        from galaxy.agents.schema import TaskStarLineSchema

        if not isinstance(schema, TaskStarLineSchema):
            raise ValueError("Expected TaskStarLineSchema instance")

        # Convert schema to dict and use existing from_dict method
        data = schema.model_dump()
        return cls.from_dict(data)

    def to_basemodel(self) -> "TaskStarLineSchema":
        """
        Convert the TaskStarLine to a Pydantic BaseModel schema.

        :return: TaskStarLineSchema instance
        """
        from galaxy.agents.schema import TaskStarLineSchema

        # Get dictionary representation and create schema
        data = self.to_dict()
        return TaskStarLineSchema(**data)

    def to_json(self, save_path: Optional[str] = None) -> str:
        """
        Convert the TaskStarLine to a JSON string representation.

        :param save_path: Optional file path to save the JSON to disk
        :return: JSON string representation of the TaskStarLine
        :raises IOError: If file writing fails when save_path is provided
        """
        import json

        # Get dictionary representation
        line_dict = self.to_dict()

        # Handle potentially non-serializable attributes
        serializable_dict = self._ensure_json_serializable(line_dict)

        # Convert to JSON string with proper formatting
        json_str = json.dumps(serializable_dict, indent=2, ensure_ascii=False)

        # Save to file if path provided
        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(json_str)
            except Exception as e:
                raise IOError(f"Failed to save TaskStarLine to {save_path}: {e}")

        return json_str

    def _ensure_json_serializable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all values in the dictionary are JSON serializable.

        :param data: Dictionary to make serializable
        :return: JSON serializable dictionary
        """
        import json

        serializable_data = {}

        for key, value in data.items():
            try:
                # Test if the value is JSON serializable
                json.dumps(value)
                serializable_data[key] = value
            except (TypeError, ValueError):
                # Handle non-serializable values
                if hasattr(value, "__dict__"):
                    # For complex objects, try to convert to dict
                    try:
                        serializable_data[key] = vars(value)
                    except:
                        serializable_data[key] = str(value)
                elif isinstance(value, set):
                    # Convert sets to lists
                    serializable_data[key] = list(value)
                elif callable(value):
                    # Skip callable objects
                    serializable_data[key] = f"<callable: {value.__name__}>"
                else:
                    # Convert to string as fallback
                    serializable_data[key] = str(value)

        return serializable_data

    @classmethod
    def from_json(
        cls, json_data: Optional[str] = None, file_path: Optional[str] = None
    ) -> "TaskStarLine":
        """
        Create a TaskStarLine from a JSON string or JSON file.

        :param json_data: JSON string representation of the TaskStarLine
        :param file_path: Path to JSON file containing TaskStarLine data
        :return: TaskStarLine instance
        :raises ValueError: If neither json_data nor file_path is provided, or both are provided
        :raises FileNotFoundError: If file_path is provided but file doesn't exist
        :raises json.JSONDecodeError: If JSON parsing fails
        :raises IOError: If file reading fails
        """
        import json

        if json_data is None and file_path is None:
            raise ValueError("Either json_data or file_path must be provided")

        if json_data is not None and file_path is not None:
            raise ValueError("Only one of json_data or file_path should be provided")

        # Load JSON data
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f"JSON file not found: {file_path}")
            except Exception as e:
                raise IOError(f"Failed to read JSON file {file_path}: {e}")
        else:
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON format: {e}", json_data, e.pos
                )

        # Validate that data is a dictionary
        if not isinstance(data, dict):
            raise ValueError("JSON data must represent a dictionary/object")

        # Create TaskStarLine instance from dictionary
        return cls.from_dict(data)

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
