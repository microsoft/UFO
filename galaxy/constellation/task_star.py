# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
TaskStar - Individual task representation in Constellation V2.

This module defines the TaskStar class, representing individual tasks
with comprehensive metadata, execution tracking, and device targeting.
Optimized for type safety, maintainability, and follows SOLID principles.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from galaxy.client.device_manager import ConstellationDeviceManager

from ..core.interfaces import ITask
from ..core.types import ExecutionResult, TaskConfiguration, TaskId
from .enums import DeviceType, TaskPriority, TaskStatus

if TYPE_CHECKING:
    from galaxy.agents.schema import TaskStarSchema


class TaskStar(ITask):
    """
    Represents an individual task (TaskStar) in the task constellation.

    Each TaskStar contains:
    - Task description and metadata
    - Target device information
    - Execution result and timestamps
    - Dependency tracking capabilities

    This class implements the ITask interface and provides comprehensive
    task management with type safety and validation.
    """

    def __init__(
        self,
        task_id: Optional[TaskId] = None,
        name: str = "",
        description: str = "",
        tips: List[str] = None,
        target_device_id: Optional[str] = None,
        device_type: Optional[DeviceType] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout: Optional[float] = None,
        retry_count: int = 0,
        task_data: Optional[Dict[str, Any]] = None,
        expected_output_type: Optional[str] = None,
        config: Optional[TaskConfiguration] = None,
    ):
        """
        Initialize a TaskStar.

        :param task_id: Unique identifier for the task (auto-generated if None)
        :param name: Short name for the task
        :param description: Natural language description of the task
        :param tips: List of tips or hints for the completing the task
        :param target_device_id: ID of the device to execute this task
        :param device_type: Type of the target device
        :param priority: Priority level for execution scheduling
        :param timeout: Maximum execution time in seconds
        :param retry_count: Number of retries allowed for this task
        :param task_data: Additional data needed for task execution
        :param expected_output_type: Expected type/format of the output
        :param config: Optional task configuration object
        """
        self._task_id: TaskId = task_id or str(uuid.uuid4())
        self._name: str = name or f"task_{self._task_id[:8]}"
        self._description: str = description
        self._tips: Optional[List[str]] = tips
        self._target_device_id: Optional[str] = target_device_id
        self._device_type: Optional[DeviceType] = device_type
        self._priority: TaskPriority = priority
        self._timeout: Optional[float] = timeout
        self._retry_count: int = retry_count
        self._current_retry: int = 0
        self._task_data: Dict[str, Any] = task_data or {}
        self._expected_output_type: Optional[str] = expected_output_type

        # Apply configuration if provided
        if config:
            self._timeout = config.timeout or self._timeout
            self._retry_count = config.retry_count or self._retry_count
            self._priority = config.priority or self._priority
            self._task_data.update(config.metadata)

        # Execution tracking
        self._status: TaskStatus = TaskStatus.PENDING
        self._result: Optional[Any] = None
        self._error: Optional[Exception] = None
        self._execution_start_time: Optional[datetime] = None
        self._execution_end_time: Optional[datetime] = None

        # Metadata
        self._created_at: datetime = datetime.now(timezone.utc)
        self._updated_at: datetime = self._created_at

        # Dependencies managed by TaskConstellation
        self._dependencies: set[TaskId] = set()
        self._dependents: set[TaskId] = set()

        # Validation errors cache
        self._validation_errors: List[str] = []

        self.logger = logging.getLogger(__name__)

    # ITask interface implementation
    @property
    def task_id(self) -> TaskId:
        """Get the task ID."""
        return self._task_id

    @property
    def name(self) -> str:
        """Get the task name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """
        Set the task name.

        :param value: New task name
        :raises ValueError: If task is currently running
        """
        if self._status == TaskStatus.RUNNING:
            raise ValueError(f"Cannot modify name of running task {self._task_id}")
        self._name = value
        self._updated_at = datetime.now(timezone.utc)

    @property
    def description(self) -> str:
        """Get the task description."""
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        """
        Set the task description.

        :param value: New task description
        :raises ValueError: If task is currently running
        """
        if self._status == TaskStatus.RUNNING:
            raise ValueError(
                f"Cannot modify description of running task {self._task_id}"
            )
        self._description = value
        self._updated_at = datetime.now(timezone.utc)

    @property
    def tips(self) -> List[str]:
        """Get the task tips."""
        return self._tips

    @tips.setter
    def tips(self, value: List[str]) -> None:
        """
        Set the task tips.

        :param value: New task tips
        :raises ValueError: If task is currently running
        """
        if self._status == TaskStatus.RUNNING:
            raise ValueError(f"Cannot modify tips of running task {self._task_id}")
        self._tips = value
        self._updated_at = datetime.now(timezone.utc)

    @description.setter
    def description(self, value: str) -> None:
        """
        Set the task description.

        :param value: New task description
        :raises ValueError: If task is currently running
        """
        if self._status == TaskStatus.RUNNING:
            raise ValueError(
                f"Cannot modify description of running task {self._task_id}"
            )
        self._description = value
        self._updated_at = datetime.now(timezone.utc)

    async def execute(
        self, device_manager: ConstellationDeviceManager
    ) -> ExecutionResult:
        """
        Execute the task using the provided device manager.

        :param device_manager: Device manager instance for task execution
        :return: Execution result
        :raises ValueError: If device manager not provided or no device assigned
        """
        if not device_manager:
            raise ValueError("Device manager is required for task execution")

        if not self.target_device_id:
            raise ValueError(f"No device assigned to task {self.task_id}")

        start_time = datetime.now(timezone.utc)

        request_string = self.to_request_string()

        try:
            # Execute task directly using ConstellationDeviceManager
            result = await device_manager.assign_task_to_device(
                task_id=self.task_id,
                device_id=self.target_device_id,
                task_description=request_string,
                task_data=self.task_data or {},
                timeout=self._timeout or 1000.0,
            )

            end_time = datetime.now(timezone.utc)

            result.start_time = start_time
            result.end_time = end_time

            return result

        except asyncio.TimeoutError as e:
            end_time = datetime.now(timezone.utc)
            return ExecutionResult(
                task_id=self.task_id,
                status=TaskStatus.FAILED,
                error=TimeoutError(f"Task execution timeout: {e}"),
                start_time=start_time,
                end_time=end_time,
                metadata={"device_id": self.target_device_id},
            )
        except AttributeError as e:
            end_time = datetime.now(timezone.utc)
            return ExecutionResult(
                task_id=self.task_id,
                status=TaskStatus.FAILED,
                error=AttributeError(f"Configuration error: {e}"),
                start_time=start_time,
                end_time=end_time,
                metadata={"device_id": self.target_device_id},
            )
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            return ExecutionResult(
                task_id=self.task_id,
                status=TaskStatus.FAILED,
                error=e,
                start_time=start_time,
                end_time=end_time,
                metadata={"device_id": self.target_device_id},
            )

    def validate(self) -> bool:
        """
        Validate the task configuration.

        :return: True if valid, False otherwise
        """
        self._validation_errors.clear()

        # Validate task ID
        if not self._task_id or not isinstance(self._task_id, str):
            self._validation_errors.append("Task ID must be a non-empty string")

        # Validate name
        if not self._name or not isinstance(self._name, str):
            self._validation_errors.append("Task name must be a non-empty string")

        # Validate description
        if not self._description or not isinstance(self._description, str):
            self._validation_errors.append(
                "Task description must be a non-empty string"
            )

        # Validate timeout
        if self._timeout is not None and (
            not isinstance(self._timeout, (int, float)) or self._timeout <= 0
        ):
            self._validation_errors.append("Timeout must be a positive number")

        # Validate retry count
        if not isinstance(self._retry_count, int) or self._retry_count < 0:
            self._validation_errors.append("Retry count must be a non-negative integer")

        # Validate priority
        if not isinstance(self._priority, TaskPriority):
            self._validation_errors.append("Priority must be a TaskPriority enum value")

        return len(self._validation_errors) == 0

    def get_validation_errors(self) -> List[str]:
        """
        Get a list of validation errors.

        :return: List of validation error messages
        """
        return self._validation_errors.copy()

    # Additional properties with improved type annotations
    @property
    def task_description(self) -> str:
        """Get the task description (backwards compatibility)."""
        return self._description

    @task_description.setter
    def task_description(self, value: str) -> None:
        """Set the task description (backwards compatibility)."""
        self.description = value

    @property
    def target_device_id(self) -> Optional[str]:
        """Get the target device ID."""
        return self._target_device_id

    @target_device_id.setter
    def target_device_id(self, value: Optional[str]) -> None:
        """Set the target device ID."""
        if self._status == TaskStatus.RUNNING:
            raise ValueError(
                f"Cannot modify device assignment of running task {self._task_id}"
            )
        self._target_device_id = value
        self._updated_at = datetime.now(timezone.utc)

    @property
    def device_type(self) -> Optional[DeviceType]:
        """Get the device type."""
        return self._device_type

    @device_type.setter
    def device_type(self, value: Optional[DeviceType]) -> None:
        """Set the device type."""
        if self._status == TaskStatus.RUNNING:
            raise ValueError(
                f"Cannot modify device type of running task {self._task_id}"
            )
        self._device_type = value
        self._updated_at = datetime.now(timezone.utc)

    @property
    def priority(self) -> TaskPriority:
        """Get the task priority."""
        return self._priority

    @priority.setter
    def priority(self, value: TaskPriority) -> None:
        """Set the task priority."""
        if self._status == TaskStatus.RUNNING:
            raise ValueError(f"Cannot modify priority of running task {self._task_id}")
        self._priority = value
        self._updated_at = datetime.now(timezone.utc)

    @property
    def status(self) -> TaskStatus:
        """Get the current status."""
        return self._status

    @property
    def result(self) -> Optional[Any]:
        """Get the task execution result."""
        return self._result

    @property
    def error(self) -> Optional[Exception]:
        """Get the task execution error, if any."""
        return self._error

    @property
    def execution_start_time(self) -> Optional[datetime]:
        """Get the execution start timestamp."""
        return self._execution_start_time

    @property
    def execution_end_time(self) -> Optional[datetime]:
        """Get the execution end timestamp."""
        return self._execution_end_time

    @property
    def execution_duration(self) -> Optional[float]:
        """Get the execution duration in seconds."""
        if self._execution_start_time and self._execution_end_time:
            return (
                self._execution_end_time - self._execution_start_time
            ).total_seconds()
        return None

    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Get the last update timestamp."""
        return self._updated_at

    @property
    def is_terminal(self) -> bool:
        """Check if the task is in a terminal state."""
        return self._status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )

    @property
    def is_ready_to_execute(self) -> bool:
        """Check if the task is ready to execute (has no pending dependencies)."""
        return self._status == TaskStatus.PENDING and len(self._dependencies) == 0

    @property
    def task_data(self) -> Dict[str, Any]:
        """Get a copy of the task data."""
        return self._task_data.copy()

    def update_task_data(self, data: Dict[str, Any]) -> None:
        """
        Update the task data.

        :param data: Data to merge into task data
        :raises ValueError: If task is currently running
        """
        if self._status == TaskStatus.RUNNING:
            raise ValueError(f"Cannot modify task data of running task {self._task_id}")

        self._task_data.update(data)
        self._updated_at = datetime.now(timezone.utc)

    def start_execution(self) -> None:
        """
        Mark the task as started.

        :raises ValueError: If task is not ready to execute
        """
        if self._status != TaskStatus.PENDING:
            raise ValueError(
                f"Cannot start task {self._task_id} in status {self._status.value}"
            )

        if len(self._dependencies) > 0:
            raise ValueError(
                f"Cannot start task {self._task_id} with pending dependencies"
            )

        self._status = TaskStatus.RUNNING
        self._execution_start_time = datetime.now(timezone.utc)
        self._updated_at = self._execution_start_time

    def complete_with_success(self, result: Any) -> None:
        """
        Mark the task as successfully completed.

        :param result: The execution result
        :raises ValueError: If task is not running
        """
        if self._status != TaskStatus.RUNNING:
            raise ValueError(
                f"Cannot complete task {self._task_id} in status {self._status.value}"
            )

        self._status = TaskStatus.COMPLETED
        self._result = result
        self._execution_end_time = datetime.now(timezone.utc)
        self._updated_at = self._execution_end_time

    def complete_with_failure(self, error: Exception) -> None:
        """
        Mark the task as failed.

        :param error: The error that caused the failure
        :raises ValueError: If task is not running
        """
        if self._status != TaskStatus.RUNNING:
            raise ValueError(
                f"Cannot fail task {self._task_id} in status {self._status.value}"
            )

        self._status = TaskStatus.FAILED
        self._error = error
        self._execution_end_time = datetime.now(timezone.utc)
        self._updated_at = self._execution_end_time

    def cancel(self) -> None:
        """Cancel the task."""
        if self._status == TaskStatus.RUNNING:
            self._execution_end_time = datetime.now(timezone.utc)

        self._status = TaskStatus.CANCELLED
        self._updated_at = datetime.now(timezone.utc)

    def should_retry(self) -> bool:
        """Check if the task should be retried."""
        return (
            self._status == TaskStatus.FAILED
            and self._current_retry < self._retry_count
        )

    def retry(self) -> None:
        """
        Reset the task for retry.

        :raises ValueError: If task cannot be retried
        """
        if not self.should_retry():
            raise ValueError(f"Task {self._task_id} cannot be retried")

        self._current_retry += 1
        self._status = TaskStatus.PENDING
        self._error = None
        self._execution_start_time = None
        self._execution_end_time = None
        self._updated_at = datetime.now(timezone.utc)

    def add_dependency(self, dependency_task_id: TaskId) -> None:
        """
        Add a dependency (internal use by TaskConstellation).

        :param dependency_task_id: ID of the dependency task
        """
        self._dependencies.add(dependency_task_id)

    def remove_dependency(self, dependency_task_id: TaskId) -> None:
        """
        Remove a dependency (internal use by TaskConstellation).

        :param dependency_task_id: ID of the dependency task
        """
        self._dependencies.discard(dependency_task_id)

    def add_dependent(self, dependent_task_id: TaskId) -> None:
        """
        Add a dependent (internal use by TaskConstellation).

        :param dependent_task_id: ID of the dependent task
        """
        self._dependents.add(dependent_task_id)

    def remove_dependent(self, dependent_task_id: TaskId) -> None:
        """
        Remove a dependent (internal use by TaskConstellation).

        :param dependent_task_id: ID of the dependent task
        """
        self._dependents.discard(dependent_task_id)

    def to_request_string(self):
        """
        Convert the TaskStar to a formated string representation (description + tips) for requests.
        """
        tips = (
            "\n".join(f" - {tip}" for tip in self._tips)
            if self._tips
            else "No tips available."
        )
        return f"Task Description: {self._description}\nTips for Completion:\n{tips}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the TaskStar to a dictionary representation.

        :return: Dictionary representation of the TaskStar
        """
        return {
            "task_id": self._task_id,
            "name": self._name,
            "description": self._description,
            "tips": self._tips,
            "task_description": self._description,  # Backwards compatibility
            "target_device_id": self._target_device_id,
            "device_type": self._device_type.value if self._device_type else None,
            "priority": self._priority.value,
            "status": self._status.value,
            "result": self._serialize_result(self._result),
            "error": str(self._error) if self._error else None,
            "timeout": self._timeout,
            "retry_count": self._retry_count,
            "current_retry": self._current_retry,
            "task_data": self._serialize_task_data(self._task_data),
            "expected_output_type": self._expected_output_type,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "execution_start_time": (
                self._execution_start_time.isoformat()
                if self._execution_start_time
                else None
            ),
            "execution_end_time": (
                self._execution_end_time.isoformat()
                if self._execution_end_time
                else None
            ),
            "execution_duration": self.execution_duration,
            "dependencies": list(self._dependencies),
            "dependents": list(self._dependents),
        }

    def _serialize_result(self, result: Any) -> Any:
        """
        Recursively serialize the task result for JSON compatibility.

        :param result: The result to serialize
        :return: JSON-compatible result
        """
        import json
        from enum import Enum
        from datetime import datetime

        if result is None:
            return None

        # Handle primitives
        if isinstance(result, (str, int, float, bool)):
            return result

        # Handle datetime
        if isinstance(result, datetime):
            return result.isoformat()

        # Handle Enum
        if isinstance(result, Enum):
            return result.value

        # Handle dictionaries recursively
        if isinstance(result, dict):
            serialized_dict = {}
            for key, value in result.items():
                serialized_dict[key] = self._serialize_result(value)
            return serialized_dict

        # Handle lists/tuples recursively
        if isinstance(result, (list, tuple)):
            return [self._serialize_result(item) for item in result]

        # Handle sets
        if isinstance(result, set):
            return [self._serialize_result(item) for item in result]

        # Handle objects with __dict__
        if hasattr(result, "__dict__"):
            try:
                obj_dict = vars(result)
                return self._serialize_result(obj_dict)
            except:
                return str(result)

        # Fallback to string
        return str(result)

    def _serialize_task_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively serialize task data for JSON compatibility.

        :param task_data: The task data to serialize
        :return: JSON-compatible task data
        """
        if not task_data:
            return {}

        serialized = {}
        for key, value in task_data.items():
            # Reuse _serialize_result for consistent recursive serialization
            serialized[key] = self._serialize_result(value)

        return serialized

    @staticmethod
    def _parse_priority(priority_value: Any) -> TaskPriority:
        """
        Parse priority value (int, string, or TaskPriority) into TaskPriority enum.

        :param priority_value: Priority value to parse
        :return: TaskPriority enum instance
        """
        if isinstance(priority_value, TaskPriority):
            return priority_value
        elif isinstance(priority_value, str):
            # Map string names to TaskPriority
            priority_map = {
                "LOW": TaskPriority.LOW,
                "MEDIUM": TaskPriority.MEDIUM,
                "HIGH": TaskPriority.HIGH,
                "CRITICAL": TaskPriority.CRITICAL,
            }
            return priority_map.get(priority_value.upper(), TaskPriority.MEDIUM)
        elif isinstance(priority_value, int):
            # Direct enum creation from int value
            try:
                return TaskPriority(priority_value)
            except ValueError:
                return TaskPriority.MEDIUM
        else:
            return TaskPriority.MEDIUM

    @staticmethod
    def _parse_device_type(device_type_value: Any) -> Optional[DeviceType]:
        """
        Parse device type value (string or DeviceType) into DeviceType enum.

        :param device_type_value: Device type value to parse
        :return: DeviceType enum instance or None
        """
        if device_type_value is None:
            return None
        elif isinstance(device_type_value, DeviceType):
            return device_type_value
        elif isinstance(device_type_value, str):
            # Map string names to DeviceType
            device_type_map = {
                "WINDOWS": DeviceType.WINDOWS,
                "MACOS": DeviceType.MACOS,
                "LINUX": DeviceType.LINUX,
                "ANDROID": DeviceType.ANDROID,
                "IOS": DeviceType.IOS,
                "WEB": DeviceType.WEB,
                "API": DeviceType.API,
            }
            return device_type_map.get(device_type_value.upper())
        else:
            return None

    @staticmethod
    def _parse_status(status_value: Any) -> TaskStatus:
        """
        Parse status value (string or TaskStatus) into TaskStatus enum.

        :param status_value: Status value to parse
        :return: TaskStatus enum instance
        """
        if isinstance(status_value, TaskStatus):
            return status_value
        elif isinstance(status_value, str):
            # Map string names to TaskStatus
            status_map = {
                "PENDING": TaskStatus.PENDING,
                "RUNNING": TaskStatus.RUNNING,
                "COMPLETED": TaskStatus.COMPLETED,
                "FAILED": TaskStatus.FAILED,
                "CANCELLED": TaskStatus.CANCELLED,
                "WAITING_DEPENDENCY": TaskStatus.WAITING_DEPENDENCY,
            }
            return status_map.get(status_value.upper(), TaskStatus.PENDING)
        else:
            return TaskStatus.PENDING

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskStar":
        """
        Create a TaskStar from a dictionary representation.

        :param data: Dictionary representation
        :return: TaskStar instance
        """
        task = cls(
            task_id=data.get("task_id"),
            name=data.get("name", ""),
            description=data.get("description", ""),  # Backwards compatibility
            tips=data.get("tips", []),
            target_device_id=data.get("target_device_id"),
            device_type=cls._parse_device_type(data.get("device_type")),
            priority=cls._parse_priority(
                data.get("priority", TaskPriority.MEDIUM.value)
            ),
            timeout=data.get("timeout"),
            retry_count=data.get("retry_count", 0),
            task_data=data.get("task_data", {}),
            expected_output_type=data.get("expected_output_type"),
        )

        # Restore state
        task._status = cls._parse_status(data.get("status", TaskStatus.PENDING.value))
        task._result = data.get("result")
        task._current_retry = data.get("current_retry", 0)

        if data.get("error"):
            task._error = Exception(data["error"])

        # Restore timestamps
        if data.get("created_at"):
            task._created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            task._updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("execution_start_time"):
            task._execution_start_time = datetime.fromisoformat(
                data["execution_start_time"]
            )
        if data.get("execution_end_time"):
            task._execution_end_time = datetime.fromisoformat(
                data["execution_end_time"]
            )

        return task

    @classmethod
    def from_basemodel(cls, schema: "TaskStarSchema") -> "TaskStar":
        """
        Create a TaskStar from a Pydantic BaseModel schema.

        :param schema: TaskStarSchema instance
        :return: TaskStar instance
        """
        from galaxy.agents.schema import TaskStarSchema

        if not isinstance(schema, TaskStarSchema):
            raise ValueError("Expected TaskStarSchema instance")

        # Convert schema to dict and use existing from_dict method
        data = schema.model_dump()
        return cls.from_dict(data)

    def to_basemodel(self) -> "TaskStarSchema":
        """
        Convert the TaskStar to a Pydantic BaseModel schema.

        :return: TaskStarSchema instance
        """
        from galaxy.agents.schema import TaskStarSchema

        # Get dictionary representation and create schema
        data = self.to_dict()
        return TaskStarSchema(**data)

    @classmethod
    def from_json(
        cls, json_data: Optional[str] = None, file_path: Optional[str] = None
    ) -> "TaskStar":
        """
        Create a TaskStar from a JSON string or JSON file.

        :param json_data: JSON string representation of the TaskStar
        :param file_path: Path to JSON file containing TaskStar data
        :return: TaskStar instance
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

        # Create TaskStar instance from dictionary
        return cls.from_dict(data)

    def to_json(self, save_path: Optional[str] = None) -> str:
        """
        Convert the TaskStar to a JSON string representation.

        :param save_path: Optional file path to save the JSON to disk
        :return: JSON string representation of the TaskStar
        :raises IOError: If file writing fails when save_path is provided
        """
        import json

        # Get dictionary representation
        task_dict = self.to_dict()

        # Handle potentially non-serializable attributes
        serializable_dict = self._ensure_json_serializable(task_dict)

        # Convert to JSON string with proper formatting
        json_str = json.dumps(serializable_dict, indent=2, ensure_ascii=False)

        # Save to file if path provided
        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(json_str)
                self.logger.info(f"TaskStar {self.task_id} saved to {save_path}")
            except Exception as e:
                self.logger.error(f"Failed to save TaskStar to {save_path}: {e}")
                raise IOError(f"Failed to save TaskStar to {save_path}: {e}")

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

    def __str__(self) -> str:
        """String representation of the TaskStar."""
        return f"TaskStar(id={self._task_id}, status={self._status.value}, device={self._target_device_id})"

    def __repr__(self) -> str:
        """Detailed representation of the TaskStar."""
        return (
            f"TaskStar(task_id={self._task_id!r}, "
            f"description={self._task_description!r}, "
            f"status={self._status.value!r}, "
            f"target_device={self._target_device_id!r})"
        )
