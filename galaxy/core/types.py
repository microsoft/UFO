# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Framework Core Types

This module defines the core type system for the Galaxy framework,
providing comprehensive type definitions for better type safety and IDE support.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    TypeVar,
    runtime_checkable,
)

# Import enums to resolve forward references
try:
    from ..constellation.enums import (
        ConstellationState,
        DependencyType,
        DeviceType,
        TaskPriority,
        TaskStatus,
    )
except ImportError:
    # Define placeholder enums if import fails
    class TaskStatus(Enum):
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"
        WAITING_DEPENDENCY = "waiting_dependency"

    class ConstellationState(Enum):
        CREATED = "created"
        READY = "ready"
        EXECUTING = "executing"
        COMPLETED = "completed"
        FAILED = "failed"
        PARTIALLY_FAILED = "partially_failed"

    class TaskPriority(Enum):
        LOW = 1
        MEDIUM = 2
        HIGH = 3
        CRITICAL = 4

    class DeviceType(Enum):
        WINDOWS = "windows"
        MACOS = "macos"
        LINUX = "linux"
        ANDROID = "android"
        IOS = "ios"
        WEB = "web"
        API = "api"

    class DependencyType(Enum):
        UNCONDITIONAL = "unconditional"
        CONDITIONAL = "conditional"
        SUCCESS_ONLY = "success_only"
        COMPLETION_ONLY = "completion_only"


# Type Variables
T = TypeVar("T")
TResult = TypeVar("TResult")
TContext = TypeVar("TContext")

# Core ID Types
TaskId = str
ConstellationId = str
DeviceId = str
SessionId = str
AgentId = str

# Callback Types
ProgressCallback = Callable[[TaskId, TaskStatus, Optional[Any]], None]
AsyncProgressCallback = Callable[[TaskId, TaskStatus, Optional[Any]], Awaitable[None]]
ErrorCallback = Callable[[Exception, Optional[Dict[str, Any]]], None]
AsyncErrorCallback = Callable[[Exception, Optional[Dict[str, Any]]], Awaitable[None]]


# Result Types
@dataclass
class ExecutionResult:
    """Result of a task execution."""

    task_id: TaskId
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[Exception | str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def execution_time(self) -> Optional[float]:
        """Calculate execution time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status in ["completed", "success"] and self.error is None


@dataclass
class ConstellationResult:
    """Result of a constellation execution."""

    constellation_id: ConstellationId
    status: ConstellationState
    task_results: Dict[TaskId, ExecutionResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def execution_time(self) -> Optional[float]:
        """Calculate total execution time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        """Calculate success rate of completed tasks."""
        if not self.task_results:
            return 0.0
        successful = sum(
            1 for result in self.task_results.values() if result.is_successful
        )
        return successful / len(self.task_results)


# Configuration Types
@dataclass
class TaskConfiguration:
    """Configuration for a task."""

    timeout: Optional[float] = None
    retry_count: int = 0
    retry_delay: float = 1.0
    priority: Optional[TaskPriority] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConstellationConfiguration:
    """Configuration for a constellation."""

    max_parallel_tasks: int = 10
    timeout: Optional[float] = None
    enable_retries: bool = True
    enable_progress_callbacks: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeviceConfiguration:
    """Configuration for a device."""

    device_id: DeviceId
    device_type: DeviceType
    capabilities: List[str] = field(default_factory=list)
    connection_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Protocols for core interfaces
@runtime_checkable
class IExecutable(Protocol):
    """Protocol for executable objects."""

    async def execute(self, context: Optional[TContext] = None) -> ExecutionResult:
        """Execute the object and return a result."""
        ...


@runtime_checkable
class IConfigurable(Protocol):
    """Protocol for configurable objects."""

    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the object with the given configuration."""
        ...


@runtime_checkable
class IObservable(Protocol):
    """Protocol for observable objects that can notify listeners."""

    def add_observer(self, observer: Callable[[Any], None]) -> None:
        """Add an observer to be notified of changes."""
        ...

    def remove_observer(self, observer: Callable[[Any], None]) -> None:
        """Remove an observer."""
        ...

    def notify_observers(self, event: Any) -> None:
        """Notify all observers of an event."""
        ...


@runtime_checkable
class IValidatable(Protocol):
    """Protocol for objects that can be validated."""

    def validate(self) -> bool:
        """Validate the object and return True if valid."""
        ...

    def get_validation_errors(self) -> List[str]:
        """Get a list of validation errors."""
        ...


# Abstract base classes for core components
class ITaskProcessor(ABC):
    """Interface for task processors."""

    @abstractmethod
    async def process_task(
        self, task: "ITask", context: Optional[TContext] = None
    ) -> ExecutionResult:
        """
        Process a single task.

        :param task: The task to process
        :param context: Optional processing context
        :return: The execution result
        """
        pass


class IConstellationManager(ABC):
    """Interface for constellation managers."""

    @abstractmethod
    async def create_constellation(
        self, tasks: List["ITask"], dependencies: Optional[List["IDependency"]] = None
    ) -> "IConstellation":
        """
        Create a new constellation from tasks and dependencies.

        :param tasks: List of tasks to include
        :param dependencies: Optional list of dependencies
        :return: The created constellation
        """
        pass

    @abstractmethod
    async def execute_constellation(
        self,
        constellation: "IConstellation",
        progress_callback: Optional[AsyncProgressCallback] = None,
    ) -> ConstellationResult:
        """
        Execute a constellation.

        :param constellation: The constellation to execute
        :param progress_callback: Optional progress callback
        :return: The execution result
        """
        pass


class IDeviceManager(ABC):
    """Interface for device managers."""

    @abstractmethod
    async def register_device(self, device_config: DeviceConfiguration) -> bool:
        """
        Register a new device.

        :param device_config: Device configuration
        :return: True if registration successful
        """
        pass

    @abstractmethod
    async def get_available_devices(
        self, capabilities: Optional[List[str]] = None
    ) -> List[DeviceId]:
        """
        Get list of available devices optionally filtered by capabilities.

        :param capabilities: Optional list of required capabilities
        :return: List of available device IDs
        """
        pass

    @abstractmethod
    async def assign_task_to_device(
        self, task: "ITask", device_id: Optional[DeviceId] = None
    ) -> bool:
        """
        Assign a task to a device.

        :param task: The task to assign
        :param device_id: Optional specific device ID, auto-select if None
        :return: True if assignment successful
        """
        pass


class IAgentProcessor(ABC):
    """Interface for agent processors."""

    @abstractmethod
    async def process_request(
        self, request: str, context: Optional[TContext] = None
    ) -> "IConstellation":
        """
        Process a user request and generate a constellation.

        :param request: User request string
        :param context: Optional processing context
        :return: Generated constellation
        """
        pass

    @abstractmethod
    async def process_result(
        self,
        result: ExecutionResult,
        constellation: "IConstellation",
        context: Optional[TContext] = None,
    ) -> "IConstellation":
        """
        Process a task result and potentially update the constellation.

        :param result: Task execution result
        :param constellation: Current constellation
        :param context: Optional processing context
        :return: Updated constellation
        """
        pass


# Forward declarations for complex types
class ITask(Protocol):
    """Protocol for task objects."""

    task_id: TaskId
    name: str
    description: str


class IDependency(Protocol):
    """Protocol for dependency objects."""

    source_task_id: TaskId
    target_task_id: TaskId
    dependency_type: DependencyType


class IConstellation(Protocol):
    """Protocol for constellation objects."""

    constellation_id: ConstellationId
    name: str
    tasks: Dict[TaskId, ITask]
    dependencies: List[IDependency]


# Exception hierarchy
class GalaxyFrameworkError(Exception):
    """Base exception for Galaxy framework."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.error_code = error_code or self.__class__.__name__
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()


class TaskExecutionError(GalaxyFrameworkError):
    """Exception raised during task execution."""

    def __init__(
        self, task_id: TaskId, message: str, original_error: Optional[Exception] = None
    ):
        super().__init__(f"Task {task_id}: {message}")
        self.task_id = task_id
        self.original_error = original_error


class ConstellationError(GalaxyFrameworkError):
    """Exception raised during constellation operations."""

    def __init__(self, constellation_id: ConstellationId, message: str):
        super().__init__(f"Constellation {constellation_id}: {message}")
        self.constellation_id = constellation_id


class DeviceError(GalaxyFrameworkError):
    """Exception raised during device operations."""

    def __init__(self, device_id: DeviceId, message: str):
        super().__init__(f"Device {device_id}: {message}")
        self.device_id = device_id


class ConfigurationError(GalaxyFrameworkError):
    """Exception raised for configuration errors."""

    pass


class ValidationError(GalaxyFrameworkError):
    """Exception raised for validation errors."""

    def __init__(self, message: str, validation_errors: List[str]):
        super().__init__(message)
        self.validation_errors = validation_errors


# Utility types
@dataclass
class Statistics:
    """Statistics for monitoring and debugging."""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_execution_time: float = 0.0
    success_rate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_from_result(self, result: ExecutionResult) -> None:
        """Update statistics from an execution result."""
        self.total_tasks += 1
        if result.is_successful:
            self.completed_tasks += 1
        else:
            self.failed_tasks += 1

        # Update success rate
        self.success_rate = (
            self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 0.0
        )

        # Update average execution time
        if result.execution_time is not None:
            current_total_time = self.average_execution_time * (self.total_tasks - 1)
            self.average_execution_time = (
                current_total_time + result.execution_time
            ) / self.total_tasks


# Context types
@dataclass
class ProcessingContext:
    """Context for processing operations."""

    session_id: Optional[SessionId] = None
    agent_id: Optional[AgentId] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    device_manager: Optional[Any] = (
        None  # ConstellationDeviceManager (avoiding circular import)
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
