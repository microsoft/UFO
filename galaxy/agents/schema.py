from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid
import threading

from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum

from ufo.agents.processors.schemas.actions import ActionCommandInfo


class IDManager:
    """
    Manages ID allocation for constellations, tasks, and dependencies.
    Ensures uniqueness within the same constellation context.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._constellation_counters = (
                        {}
                    )  # constellation_id -> {'task': counter, 'line': counter}
                    cls._instance._used_ids = (
                        {}
                    )  # constellation_id -> {'task_ids': set, 'line_ids': set}
        return cls._instance

    def generate_constellation_id(self) -> str:
        """Generate a unique constellation ID."""
        return f"constellation_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def generate_task_id(
        self, constellation_id: str = None, prefix: str = "task"
    ) -> str:
        """Generate a unique task ID within a constellation context."""
        if constellation_id is None:
            # Global unique task ID
            return f"{prefix}_{uuid.uuid4().hex[:8]}"

        with self._lock:
            if constellation_id not in self._constellation_counters:
                self._constellation_counters[constellation_id] = {"task": 0, "line": 0}
                self._used_ids[constellation_id] = {
                    "task_ids": set(),
                    "line_ids": set(),
                }

            counter = self._constellation_counters[constellation_id]["task"]
            while True:
                counter += 1
                task_id = f"{prefix}_{counter:03d}"
                if task_id not in self._used_ids[constellation_id]["task_ids"]:
                    self._constellation_counters[constellation_id]["task"] = counter
                    self._used_ids[constellation_id]["task_ids"].add(task_id)
                    return task_id

    def generate_line_id(
        self, constellation_id: str = None, prefix: str = "line"
    ) -> str:
        """Generate a unique line ID within a constellation context."""
        if constellation_id is None:
            # Global unique line ID
            return f"{prefix}_{uuid.uuid4().hex[:8]}"

        with self._lock:
            if constellation_id not in self._constellation_counters:
                self._constellation_counters[constellation_id] = {"task": 0, "line": 0}
                self._used_ids[constellation_id] = {
                    "task_ids": set(),
                    "line_ids": set(),
                }

            counter = self._constellation_counters[constellation_id]["line"]
            while True:
                counter += 1
                line_id = f"{prefix}_{counter:03d}"
                if line_id not in self._used_ids[constellation_id]["line_ids"]:
                    self._constellation_counters[constellation_id]["line"] = counter
                    self._used_ids[constellation_id]["line_ids"].add(line_id)
                    return line_id

    def register_existing_id(self, constellation_id: str, id_type: str, id_value: str):
        """Register an existing ID to avoid conflicts."""
        with self._lock:
            if constellation_id not in self._used_ids:
                self._constellation_counters[constellation_id] = {"task": 0, "line": 0}
                self._used_ids[constellation_id] = {
                    "task_ids": set(),
                    "line_ids": set(),
                }

            if id_type == "task":
                self._used_ids[constellation_id]["task_ids"].add(id_value)
            elif id_type == "line":
                self._used_ids[constellation_id]["line_ids"].add(id_value)

    def is_task_id_available(self, constellation_id: str, task_id: str) -> bool:
        """Check if a task ID is available in the constellation."""
        if constellation_id not in self._used_ids:
            return True
        return task_id not in self._used_ids[constellation_id]["task_ids"]

    def is_line_id_available(self, constellation_id: str, line_id: str) -> bool:
        """Check if a line ID is available in the constellation."""
        if constellation_id not in self._used_ids:
            return True
        return line_id not in self._used_ids[constellation_id]["line_ids"]


class WeavingMode(str, Enum):
    """
    Represents the weaving mode for the Constellation Agent.
    """

    CREATION = "creation"
    EDITING = "editing"


class TaskStarSchema(BaseModel):
    """
    Pydantic BaseModel for TaskStar serialization/deserialization.
    """

    task_id: Optional[str] = Field(default=None)
    name: str
    description: str
    tips: Optional[List[str]] = None
    target_device_id: Optional[str] = None
    device_type: Optional[str] = None
    priority: Any = "MEDIUM"  # Can accept int or str
    status: Any = "PENDING"  # Can accept int or str
    result: Optional[Any] = None
    error: Optional[str] = None
    timeout: Optional[float] = None
    retry_count: int = 0
    current_retry: int = 0
    task_data: Dict[str, Any] = Field(default_factory=dict)
    expected_output_type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    execution_start_time: Optional[str] = None
    execution_end_time: Optional[str] = None
    execution_duration: Optional[float] = None
    dependencies: List[str] = Field(default_factory=list)
    dependents: List[str] = Field(default_factory=list)

    @field_validator("priority", mode="before")
    @classmethod
    def convert_priority(cls, v):
        """Convert priority to string if it's an int."""
        if isinstance(v, int):
            # Map int values to string names
            priority_map = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}
            return priority_map.get(v, "MEDIUM")
        return v

    @field_validator("status", mode="before")
    @classmethod
    def convert_status(cls, v):
        """Convert status enum value to string if needed."""
        if hasattr(v, "value"):
            return v.value.upper()
        return str(v).upper() if v else v

    @field_validator("device_type", mode="before")
    @classmethod
    def convert_device_type(cls, v):
        """Convert device type enum to string if needed."""
        if v is None:
            return None
        if hasattr(v, "value"):
            return v.value.upper()
        return str(v).upper() if v else v

    @model_validator(mode="before")
    @classmethod
    def generate_task_id(cls, data):
        """Generate task_id if not provided."""
        if isinstance(data, dict):
            if data.get("task_id") is None or data.get("task_id") == "":
                id_manager = IDManager()
                data["task_id"] = id_manager.generate_task_id()
        return data


class TaskStarLineSchema(BaseModel):
    """
    Pydantic BaseModel for TaskStarLine serialization/deserialization.
    """

    line_id: Optional[str] = Field(default=None)
    from_task_id: str
    to_task_id: str
    dependency_type: Any = "UNCONDITIONAL"  # Can accept enum value
    condition_description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_satisfied: bool = False
    last_evaluation_result: Optional[bool] = None
    last_evaluation_time: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("dependency_type", mode="before")
    @classmethod
    def convert_dependency_type(cls, v):
        """Convert dependency type enum to string if needed."""
        if hasattr(v, "value"):
            return v.value.upper()
        return str(v).upper() if v else v

    @model_validator(mode="before")
    @classmethod
    def generate_line_id(cls, data):
        """Generate line_id if not provided."""
        if isinstance(data, dict):
            if data.get("line_id") is None or data.get("line_id") == "":
                id_manager = IDManager()
                data["line_id"] = id_manager.generate_line_id()
        return data


class TaskConstellationSchema(BaseModel):
    """
    Pydantic BaseModel for TaskConstellation serialization/deserialization.
    """

    constellation_id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    state: Any = "CREATED"  # Can accept enum value
    tasks: Union[Dict[str, TaskStarSchema], List[TaskStarSchema]] = Field(
        default_factory=dict
    )
    dependencies: Union[Dict[str, TaskStarLineSchema], List[TaskStarLineSchema]] = (
        Field(default_factory=dict)
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    execution_start_time: Optional[str] = None
    execution_end_time: Optional[str] = None
    execution_duration: Optional[float] = None

    @field_validator("state", mode="before")
    @classmethod
    def convert_state(cls, v):
        """Convert constellation state enum to string if needed."""
        if hasattr(v, "value"):
            return v.value.upper()
        return str(v).upper() if v else v

    @model_validator(mode="before")
    @classmethod
    def generate_constellation_id(cls, data):
        """Generate constellation_id if not provided."""
        if isinstance(data, dict):
            if (
                data.get("constellation_id") is None
                or data.get("constellation_id") == ""
            ):
                id_manager = IDManager()
                data["constellation_id"] = id_manager.generate_constellation_id()
        return data

    @model_validator(mode="before")
    @classmethod
    def convert_lists_to_dicts(cls, data):
        """Convert tasks and dependencies from List to Dict format if needed."""
        if isinstance(data, dict):
            # Convert tasks from List to Dict
            if "tasks" in data and isinstance(data["tasks"], list):
                tasks_dict = {}
                for task_data in data["tasks"]:
                    if isinstance(task_data, dict):
                        # Ensure task has a task_id for use as key
                        task_id = task_data.get("task_id")
                        if not task_id:
                            # Generate task_id if not present
                            id_manager = IDManager()
                            task_id = id_manager.generate_task_id()
                            task_data["task_id"] = task_id
                        tasks_dict[task_id] = task_data
                    elif hasattr(task_data, "task_id"):
                        # Handle TaskStarSchema objects
                        tasks_dict[task_data.task_id] = task_data
                data["tasks"] = tasks_dict

            # Convert dependencies from List to Dict
            if "dependencies" in data and isinstance(data["dependencies"], list):
                deps_dict = {}
                for dep_data in data["dependencies"]:
                    if isinstance(dep_data, dict):
                        # Ensure dependency has a line_id for use as key
                        line_id = dep_data.get("line_id")
                        if not line_id:
                            # Generate line_id if not present
                            id_manager = IDManager()
                            line_id = id_manager.generate_line_id()
                            dep_data["line_id"] = line_id
                        deps_dict[line_id] = dep_data
                    elif hasattr(dep_data, "line_id"):
                        # Handle TaskStarLineSchema objects
                        deps_dict[dep_data.line_id] = dep_data
                data["dependencies"] = deps_dict

        return data

    @model_validator(mode="after")
    def validate_unique_ids(self):
        """Validate that all task_ids and line_ids are unique within the constellation."""
        id_manager = IDManager()

        # Check for duplicate task IDs
        task_ids = set()
        for task_id, task in self.tasks.items():
            if task.task_id in task_ids:
                raise ValueError(f"Duplicate task_id found: {task.task_id}")
            task_ids.add(task.task_id)

            # Register the task ID with the manager
            id_manager.register_existing_id(self.constellation_id, "task", task.task_id)

        # Check for duplicate line IDs
        line_ids = set()
        for line_id, line in self.dependencies.items():
            if line.line_id in line_ids:
                raise ValueError(f"Duplicate line_id found: {line.line_id}")
            line_ids.add(line.line_id)

            # Register the line ID with the manager
            id_manager.register_existing_id(self.constellation_id, "line", line.line_id)

        return self

    def get_tasks_as_list(self) -> List[TaskStarSchema]:
        """Convert tasks dict to list format."""
        return list(self.tasks.values())

    def get_dependencies_as_list(self) -> List[TaskStarLineSchema]:
        """Convert dependencies dict to list format."""
        return list(self.dependencies.values())

    def to_dict_with_lists(self) -> Dict[str, Any]:
        """Export constellation data with tasks and dependencies as lists."""
        data = self.model_dump()
        # Convert tasks to list of dictionaries
        data["tasks"] = [task.model_dump() for task in self.get_tasks_as_list()]
        # Convert dependencies to list of dictionaries
        data["dependencies"] = [
            dep.model_dump() for dep in self.get_dependencies_as_list()
        ]
        return data


class ConstellationAgentResponse(BaseModel):
    """
    The multi-action response data for the Constellation Creation.
    """

    thought: str
    status: str
    constellation: Optional[TaskConstellationSchema] = None
    action: Optional[List[ActionCommandInfo]] = None
    results: Any = None


@dataclass
class ConstellationRequestLog:
    """
    The request log data for the ConstellationAgent.
    """

    step: int
    weaving_mode: WeavingMode
    device_info: str
    constellation: str
    request: str
    prompt: Dict[str, Any]
