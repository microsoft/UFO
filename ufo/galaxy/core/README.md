# Galaxy Core Module

The Core module provides the foundational type system and interface definitions that underpin the entire Galaxy Framework. It defines the essential types, protocols, data classes, and abstract interfaces used across all other modules to ensure type safety, modularity, and clear contracts between components.

## ⚡ Overview

The Core module establishes the fundamental architecture of Galaxy through:
- **Comprehensive Type System**: Type aliases, protocols, dataclasses, and exception hierarchy
- **Interface Segregation**: Well-defined, focused abstract interfaces following SOLID principles  
- **Cross-Module Integration**: Types that integrate with constellation, session, and agent modules
- **Type Safety**: Runtime-checkable protocols and comprehensive type annotations
- **Exception Handling**: Hierarchical exception system with detailed error context

## 🏗️ Architecture

```
ufo/galaxy/core/
├── __init__.py                     # Module exports (types and interfaces only)
├── types.py                       # Complete type system with protocols and dataclasses
├── interfaces.py                  # Abstract interface definitions (ISP compliance)
├── di_container.py               # Dependency injection (standalone, not exported)
├── events.py                     # Event system (standalone, not exported)  
└── README.md                     # This documentation
```

**Note**: The `di_container.py` and `events.py` files exist but are not currently exported by the module's `__init__.py`, meaning they are standalone utilities rather than core framework components.

## 🎯 Core Type System (`types.py`)

The type system defines all fundamental types, protocols, and data structures used throughout Galaxy. It integrates with constellation module enums and provides comprehensive type safety.

### Core Type Aliases

```python
# Identifier Types  
TaskId = str
ConstellationId = str
DeviceId = str
SessionId = str
AgentId = str

# Callback Types (with rich signatures)
ProgressCallback = Callable[[TaskId, TaskStatus, Optional[Any]], None]
AsyncProgressCallback = Callable[[TaskId, TaskStatus, Optional[Any]], Awaitable[None]]
ErrorCallback = Callable[[Exception, Optional[Dict[str, Any]]], None]
AsyncErrorCallback = Callable[[Exception, Optional[Dict[str, Any]]], Awaitable[None]]
```

### Imported Enumerations

The core module imports enums from the constellation module (with fallback definitions):

```python
# From constellation.enums (or fallback definitions)
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
```

### Core Data Classes

Rich dataclasses with computed properties and business logic:

```python
@dataclass
class ExecutionResult:
    """Result of a task execution with computed properties."""
    
    task_id: TaskId
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[Exception] = None
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
    """Result of a constellation execution with aggregated metrics."""
    
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
        successful = sum(1 for result in self.task_results.values() if result.is_successful)
        return successful / len(self.task_results)
```

### Configuration Classes

```python
@dataclass
class TaskConfiguration:
    """Configuration for individual task execution."""
    
    timeout: Optional[float] = None
    retry_count: int = 0
    retry_delay: float = 1.0
    priority: Optional[TaskPriority] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass  
class ConstellationConfiguration:
    """Configuration for constellation execution."""
    
    max_parallel_tasks: int = 10
    timeout: Optional[float] = None
    enable_retries: bool = True
    enable_progress_callbacks: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeviceConfiguration:
    """Configuration for device management."""
    
    device_id: DeviceId
    device_type: DeviceType
    capabilities: List[str] = field(default_factory=list)
    connection_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Runtime-Checkable Protocols

```python
@runtime_checkable
class IExecutable(Protocol):
    """Protocol for executable objects."""
    async def execute(self, context: Optional[TContext] = None) -> ExecutionResult: ...

@runtime_checkable  
class IConfigurable(Protocol):
    """Protocol for configurable objects."""
    def configure(self, config: Dict[str, Any]) -> None: ...

@runtime_checkable
class IObservable(Protocol):
    """Protocol for observable objects that can notify listeners."""
    def add_observer(self, observer: Callable[[Any], None]) -> None: ...
    def remove_observer(self, observer: Callable[[Any], None]) -> None: ...
    def notify_observers(self, event: Any) -> None: ...

@runtime_checkable
class IValidatable(Protocol):
    """Protocol for objects that can be validated."""
    def validate(self) -> bool: ...
    def get_validation_errors(self) -> List[str]: ...
```

### Abstract Base Classes

```python
class ITaskProcessor(ABC):
    """Interface for task processors."""
    @abstractmethod
    async def process_task(self, task: "ITask", context: Optional[TContext] = None) -> ExecutionResult: ...

class IConstellationManager(ABC):
    """Interface for constellation managers."""
    @abstractmethod
    async def create_constellation(self, tasks: List["ITask"], dependencies: Optional[List["IDependency"]] = None) -> "IConstellation": ...
    @abstractmethod
    async def execute_constellation(self, constellation: "IConstellation", progress_callback: Optional[AsyncProgressCallback] = None) -> ConstellationResult: ...

class IDeviceManager(ABC):
    """Interface for device managers."""
    @abstractmethod
    async def register_device(self, device_config: DeviceConfiguration) -> bool: ...
    @abstractmethod  
    async def get_available_devices(self, capabilities: Optional[List[str]] = None) -> List[DeviceId]: ...
    @abstractmethod
    async def assign_task_to_device(self, task: "ITask", device_id: Optional[DeviceId] = None) -> bool: ...

class IAgentProcessor(ABC):
    """Interface for agent processors."""
    @abstractmethod
    async def process_request(self, request: str, context: Optional[TContext] = None) -> "IConstellation": ...
    @abstractmethod
    async def process_result(self, result: ExecutionResult, constellation: "IConstellation", context: Optional[TContext] = None) -> "IConstellation": ...
```

### Exception Hierarchy

Comprehensive exception hierarchy with rich error context:

```python
class GalaxyFrameworkError(Exception):
    """Base exception for Galaxy framework with metadata support."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code or self.__class__.__name__
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

class TaskExecutionError(GalaxyFrameworkError):
    """Exception raised during task execution."""
    def __init__(self, task_id: TaskId, message: str, original_error: Optional[Exception] = None):
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

class ValidationError(GalaxyFrameworkError):
    """Exception raised for validation errors."""
    def __init__(self, message: str, validation_errors: List[str]):
        super().__init__(message)
        self.validation_errors = validation_errors
```

### Utility Classes

```python
@dataclass
class Statistics:
    """Statistics for monitoring and debugging with auto-update methods."""
    
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
        self.success_rate = self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 0.0
        
        # Update average execution time
        if result.execution_time is not None:
            current_total_time = self.average_execution_time * (self.total_tasks - 1)
            self.average_execution_time = (current_total_time + result.execution_time) / self.total_tasks

@dataclass
class ProcessingContext:
    """Context for processing operations with serialization support."""
    
    session_id: Optional[SessionId] = None
    agent_id: Optional[AgentId] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    device_manager: Optional[Any] = None  # ConstellationDeviceManager (avoiding circular import)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
```

## 🔌 Interface System (`interfaces.py`)

The interface system follows the Interface Segregation Principle, providing focused contracts for different aspects of the Galaxy framework. All interfaces are abstract base classes.

### Task Management Interfaces

```python
class ITask(ABC):
    """Interface for task objects."""
    
    @property
    @abstractmethod
    def task_id(self) -> TaskId: ...
    
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def description(self) -> str: ...
    
    @abstractmethod
    async def execute(self, context: Optional[ProcessingContext] = None) -> ExecutionResult: ...
    
    @abstractmethod
    def validate(self) -> bool: ...

class ITaskFactory(ABC):
    """Interface for creating tasks."""
    
    @abstractmethod
    def create_task(self, name: str, description: str, config: Optional[TaskConfiguration] = None, **kwargs) -> ITask: ...
    
    @abstractmethod
    def supports_task_type(self, task_type: str) -> bool: ...

class ITaskExecutor(ABC):
    """Interface for executing individual tasks."""
    
    @abstractmethod
    async def execute_task(self, task: ITask, context: Optional[ProcessingContext] = None) -> ExecutionResult: ...
    
    @abstractmethod
    def can_execute(self, task: ITask) -> bool: ...
```

### Dependency Management Interfaces

```python
class IDependency(ABC):
    """Interface for task dependencies."""
    
    @property
    @abstractmethod
    def source_task_id(self) -> TaskId: ...
    
    @property
    @abstractmethod
    def target_task_id(self) -> TaskId: ...
    
    @property
    @abstractmethod
    def dependency_type(self) -> str: ...
    
    @abstractmethod
    def is_satisfied(self, completed_tasks: List[TaskId]) -> bool: ...

class IDependencyResolver(ABC):
    """Interface for resolving task dependencies."""
    
    @abstractmethod
    def get_ready_tasks(self, all_tasks: List[ITask], dependencies: List[IDependency], completed_tasks: List[TaskId]) -> List[ITask]: ...
    
    @abstractmethod
    def validate_dependencies(self, tasks: List[ITask], dependencies: List[IDependency]) -> bool: ...
```

### Constellation Management Interfaces

```python
class IConstellation(ABC):
    """Interface for constellation objects."""
    
    @property
    @abstractmethod
    def constellation_id(self) -> ConstellationId: ...
    
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def tasks(self) -> Dict[TaskId, ITask]: ...
    
    @property
    @abstractmethod
    def dependencies(self) -> List[IDependency]: ...
    
    @abstractmethod
    def add_task(self, task: ITask) -> None: ...
    
    @abstractmethod
    def add_dependency(self, dependency: IDependency) -> None: ...
    
    @abstractmethod
    def get_ready_tasks(self, completed_tasks: Optional[List[TaskId]] = None) -> List[ITask]: ...

class IConstellationBuilder(ABC):
    """Interface for building constellations."""
    
    @abstractmethod
    def create_constellation(self, name: str) -> IConstellation: ...
    
    @abstractmethod
    def add_task(self, constellation: IConstellation, task: ITask) -> IConstellation: ...
    
    @abstractmethod
    def add_dependency(self, constellation: IConstellation, source_task_id: TaskId, target_task_id: TaskId, dependency_type: str = "finish_to_start") -> IConstellation: ...

class IConstellationExecutor(ABC):
    """Interface for executing constellations."""
    
    @abstractmethod
    async def execute_constellation(self, constellation: IConstellation, config: Optional[ConstellationConfiguration] = None, progress_callback: Optional[AsyncProgressCallback] = None, error_callback: Optional[AsyncErrorCallback] = None) -> ConstellationResult: ...
    
    @abstractmethod
    async def pause_execution(self, constellation_id: ConstellationId) -> bool: ...
    
    @abstractmethod
    async def resume_execution(self, constellation_id: ConstellationId) -> bool: ...
    
    @abstractmethod
    async def cancel_execution(self, constellation_id: ConstellationId) -> bool: ...
```

### Device Management Interfaces

```python
class IDevice(ABC):
    """Interface for device objects."""
    
    @property
    @abstractmethod
    def device_id(self) -> DeviceId: ...
    
    @property
    @abstractmethod
    def device_type(self) -> str: ...
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]: ...
    
    @property
    @abstractmethod
    def is_connected(self) -> bool: ...
    
    @abstractmethod
    async def connect(self) -> bool: ...
    
    @abstractmethod
    async def disconnect(self) -> bool: ...
    
    @abstractmethod
    async def execute_task(self, task: ITask) -> ExecutionResult: ...

class IDeviceRegistry(ABC):
    """Interface for device registry."""
    
    @abstractmethod
    async def register_device(self, device: IDevice) -> bool: ...
    
    @abstractmethod
    async def unregister_device(self, device_id: DeviceId) -> bool: ...
    
    @abstractmethod
    async def get_device(self, device_id: DeviceId) -> Optional[IDevice]: ...
    
    @abstractmethod
    async def get_available_devices(self, capabilities: Optional[List[str]] = None) -> List[IDevice]: ...

class IDeviceSelector(ABC):
    """Interface for device selection strategies."""
    
    @abstractmethod
    async def select_device(self, task: ITask, available_devices: List[IDevice], context: Optional[ProcessingContext] = None) -> Optional[IDevice]: ...
```

### Agent and Session Interfaces

```python
class IRequestProcessor(ABC):
    """Interface for processing user requests."""
    
    @abstractmethod
    async def process_creation(self, context: Optional[ProcessingContext] = None) -> IConstellation: ...

class IResultProcessor(ABC):
    """Interface for processing task results."""
    
    @abstractmethod
    async def process_editing(self, context: Optional[ProcessingContext] = None) -> IConstellation: ...

class IConstellationUpdater(ABC):
    """Interface for updating constellations based on results."""
    
    @abstractmethod
    async def should_update(self, result: ExecutionResult, constellation: IConstellation) -> bool: ...
    
    @abstractmethod
    async def update_constellation(self, result: ExecutionResult, constellation: IConstellation, context: Optional[ProcessingContext] = None) -> IConstellation: ...

class ISession(ABC):
    """Interface for session objects."""
    
    @property
    @abstractmethod
    def session_id(self) -> SessionId: ...
    
    @property
    @abstractmethod
    def is_active(self) -> bool: ...
    
    @abstractmethod
    async def process_request(self, request: str) -> ConstellationResult: ...
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]: ...

class ISessionManager(ABC):
    """Interface for session management."""
    
    @abstractmethod
    async def create_session(self, session_id: SessionId, initial_request: str, context: Optional[ProcessingContext] = None) -> ISession: ...
    
    @abstractmethod
    async def get_session(self, session_id: SessionId) -> Optional[ISession]: ...
    
    @abstractmethod
    async def end_session(self, session_id: SessionId) -> bool: ...
```

### Monitoring and Observability Interfaces

```python
class IMetricsCollector(ABC):
    """Interface for collecting metrics."""
    
    @abstractmethod
    def record_task_execution(self, result: ExecutionResult) -> None: ...
    
    @abstractmethod
    def record_constellation_execution(self, result: ConstellationResult) -> None: ...
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]: ...

class IEventLogger(ABC):
    """Interface for event logging."""
    
    @abstractmethod
    def log_event(self, event_type: str, event_data: Dict[str, Any], context: Optional[ProcessingContext] = None) -> None: ...
    
    @abstractmethod
    def get_events(self, event_type: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]: ...
```

## 📦 Module Exports (`__init__.py`)

The core module exports only types and interfaces through its `__init__.py`. The dependency injection and event system files exist but are not exported.

### Exported Types (from `types.py`)
- **Type Aliases**: `TaskId`, `ConstellationId`, `DeviceId`, `SessionId`, `AgentId`
- **Callbacks**: `ProgressCallback`, `AsyncProgressCallback`, `ErrorCallback`, `AsyncErrorCallback`
- **Data Classes**: `ExecutionResult`, `ConstellationResult`, `TaskConfiguration`, `ConstellationConfiguration`, `DeviceConfiguration`, `ProcessingContext`, `Statistics`
- **Exceptions**: `GalaxyFrameworkError`, `TaskExecutionError`, `ConstellationError`, `DeviceError`, `ConfigurationError`, `ValidationError`

### Exported Interfaces (from `interfaces.py`)
- **Task Interfaces**: `ITask`, `ITaskFactory`, `ITaskExecutor`
- **Dependency Interfaces**: `IDependency`, `IDependencyResolver`  
- **Constellation Interfaces**: `IConstellation`, `IConstellationBuilder`, `IConstellationExecutor`
- **Device Interfaces**: `IDevice`, `IDeviceRegistry`, `IDeviceSelector`
- **Agent Interfaces**: `IRequestProcessor`, `IResultProcessor`, `IConstellationUpdater`
- **Session Interfaces**: `ISession`, `ISessionManager`
- **Monitoring Interfaces**: `IMetricsCollector`, `IEventLogger`

### Not Exported (Standalone Files)
- **Dependency Injection**: `di_container.py` (exists but not in `__init__.py`)
- **Event System**: `events.py` (exists but not in `__init__.py`)

## 🚀 Usage Patterns

### Basic Type Usage

```python
from ufo.galaxy.core import (
    TaskId, ConstellationId, ExecutionResult,
    TaskConfiguration, ProcessingContext,
    GalaxyFrameworkError
)

# Create execution result
result = ExecutionResult(
    task_id="task_1",
    status=TaskStatus.COMPLETED,
    result={"output": "success"},
    metadata={"duration": 1.5}
)

# Check success
if result.is_successful:
    print(f"Task completed in {result.execution_time}s")
```

### Interface Implementation

```python
from ufo.galaxy.core import ITask, ITaskExecutor

class MyTask(ITask):
    def __init__(self, task_id: TaskId, name: str, description: str):
        self._task_id = task_id
        self._name = name
        self._description = description
    
    @property
    def task_id(self) -> TaskId:
        return self._task_id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    async def execute(self, context: Optional[ProcessingContext] = None) -> ExecutionResult:
        # Implementation here
        return ExecutionResult(
            task_id=self.task_id,
            status=TaskStatus.COMPLETED,
            result={"success": True}
        )
    
    def validate(self) -> bool:
        return bool(self.task_id and self.name)
```

### Exception Handling

```python
from ufo.galaxy.core import TaskExecutionError, ValidationError

try:
    # Galaxy operations
    pass
except TaskExecutionError as e:
    print(f"Task {e.task_id} failed: {e}")
    if e.original_error:
        print(f"Original error: {e.original_error}")
except ValidationError as e:
    print(f"Validation failed: {e}")
    for error in e.validation_errors:
        print(f"  - {error}")
```

## 🔗 Integration with Other Modules

The core module provides the foundation that other Galaxy modules build upon:

- **[Constellation](../constellation/README.md)**: Provides enums imported by core types, implements constellation interfaces
- **[Session](../session/README.md)**: Implements session interfaces, uses core types for results
- **[Agents](../agents/README.md)**: Implements agent interfaces, uses processing context and callbacks
- **[Client](../client/README.md)**: Uses device interfaces and core types for coordination

The core module's cross-module integration approach (importing enums from constellation) ensures type consistency while maintaining clear architectural boundaries.

---

*The type-safe foundation enabling consistent, well-defined contracts across the entire Galaxy framework* 🎯
