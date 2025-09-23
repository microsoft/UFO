# Galaxy Core Module

The Core module provides the foundational components, interfaces, and type system that underpin the entire Galaxy Framework. It defines the essential abstractions, event system, and shared utilities used across all other modules.

## ⚡ Overview

The Core module establishes the fundamental architecture of Galaxy through well-defined interfaces, a robust event system, and comprehensive type definitions. It enables loose coupling, extensibility, and maintainability across the framework.

## 🏗️ Architecture

```
ufo/galaxy/core/
├── __init__.py                     # Module exports
├── events.py                      # Event system and observer pattern
├── interfaces.py                  # Core interfaces and abstractions
├── types.py                       # Type definitions and enums
├── exceptions.py                  # Custom exception hierarchy
├── utils.py                       # Shared utility functions
└── base/                          # Base classes and mixins
    ├── __init__.py
    ├── base_component.py          # Base component class
    ├── configurable.py            # Configuration mixin
    └── serializable.py            # Serialization mixin
```

## ⚡ Event System

### EventBus

The central event distribution system that enables loose coupling between components.

#### Key Features
- **Type-Safe Events**: Strongly typed event system with validation
- **Async/Await Support**: Full asynchronous event handling
- **Event Filtering**: Subscribe to specific event types or patterns
- **Event History**: Optional event history tracking and replay
- **Error Handling**: Robust error handling and recovery

#### Usage Example
```python
from ufo.galaxy.core.events import EventBus, Event, EventType

# Create event bus
event_bus = EventBus(
    enable_history=True,
    max_history_size=1000,
    enable_async_delivery=True
)

# Define custom event
class TaskCompletedEvent(Event):
    def __init__(self, task_id: str, result: Dict):
        super().__init__(EventType.TASK_COMPLETED)
        self.task_id = task_id
        self.result = result

# Subscribe to events
async def handle_task_completion(event: TaskCompletedEvent):
    print(f"Task {event.task_id} completed with result: {event.result}")

event_bus.subscribe(EventType.TASK_COMPLETED, handle_task_completion)

# Emit events
await event_bus.emit(TaskCompletedEvent("task_1", {"status": "success"}))
```

#### Key Methods
```python
class EventBus:
    def subscribe(self, event_type: EventType, handler: Callable) -> str
    def unsubscribe(self, subscription_id: str) -> bool
    async def emit(self, event: Event) -> None
    def subscribe_pattern(self, pattern: str, handler: Callable) -> str
    def get_event_history(self, event_type: EventType = None) -> List[Event]
    def replay_events(self, from_timestamp: datetime = None) -> None
    def clear_history(self) -> None
    def get_subscription_count(self) -> int
```

### Event Types

Comprehensive event type definitions for the Galaxy Framework.

```python
class EventType(Enum):
    # Session Events
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    SESSION_FAILED = "session_failed"
    ROUND_STARTED = "round_started"
    ROUND_COMPLETED = "round_completed"
    
    # Agent Events
    AGENT_STATE_CHANGED = "agent_state_changed"
    REQUEST_PROCESSING_STARTED = "request_processing_started"
    REQUEST_PROCESSING_COMPLETED = "request_processing_completed"
    
    # Constellation Events
    CONSTELLATION_CREATED = "constellation_created"
    CONSTELLATION_UPDATED = "constellation_updated"
    TASK_ADDED = "task_added"
    TASK_REMOVED = "task_removed"
    TASK_STATUS_CHANGED = "task_status_changed"
    DEPENDENCY_ADDED = "dependency_added"
    DEPENDENCY_REMOVED = "dependency_removed"
    
    # Execution Events
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # Device Events
    DEVICE_CONNECTED = "device_connected"
    DEVICE_DISCONNECTED = "device_disconnected"
    DEVICE_STATUS_CHANGED = "device_status_changed"
    
    # System Events
    ERROR_OCCURRED = "error_occurred"
    WARNING_ISSUED = "warning_issued"
    PERFORMANCE_METRIC_RECORDED = "performance_metric_recorded"
```

### Observer Pattern Implementation

Advanced observer pattern with type safety and error handling.

```python
from ufo.galaxy.core.events import Observer, Subject

# Create observable subject
class ConstellationSubject(Subject):
    def __init__(self):
        super().__init__()
        self._constellation_state = {}
    
    def update_constellation(self, changes: Dict):
        self._constellation_state.update(changes)
        # Notify all observers
        self.notify_observers(ConstellationUpdatedEvent(changes))

# Create observer
class ConstellationObserver(Observer):
    async def update(self, event: Event) -> None:
        if isinstance(event, ConstellationUpdatedEvent):
            print(f"Constellation updated: {event.changes}")

# Setup observer relationship
subject = ConstellationSubject()
observer = ConstellationObserver()
subject.attach_observer(observer)

# Update will automatically notify observer
subject.update_constellation({"task_count": 5})
```

## 🔌 Interfaces and Abstractions

### Core Interfaces

Define the essential contracts for Galaxy components.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class Agent(ABC):
    """Abstract base for all Galaxy agents"""
    
    @abstractmethod
    async def process_request(self, request: str, context: Dict[str, Any]) -> Any:
        """Process a user request and return result"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass
    
    @abstractmethod
    def get_status(self) -> AgentStatus:
        """Get current agent status"""
        pass

class Orchestrator(ABC):
    """Abstract base for workflow orchestrators"""
    
    @abstractmethod
    async def execute_constellation(self, constellation: 'TaskConstellation') -> ExecutionResult:
        """Execute a task constellation"""
        pass
    
    @abstractmethod
    def get_execution_status(self) -> ExecutionStatus:
        """Get current execution status"""
        pass
    
    @abstractmethod
    def cancel_execution(self) -> bool:
        """Cancel ongoing execution"""
        pass

class DeviceManager(ABC):
    """Abstract base for device management"""
    
    @abstractmethod
    def discover_devices(self) -> List[Device]:
        """Discover available devices"""
        pass
    
    @abstractmethod
    def assign_task(self, task: 'TaskStar', device: Device) -> bool:
        """Assign task to specific device"""
        pass
    
    @abstractmethod
    def get_device_capabilities(self, device: Device) -> List[str]:
        """Get device capabilities"""
        pass
```

### Component Interfaces

Specialized interfaces for specific Galaxy components.

```python
class ConstellationEditor(ABC):
    """Interface for constellation editing operations"""
    
    @abstractmethod
    def add_task(self, task: 'TaskStar') -> bool:
        """Add task to constellation"""
        pass
    
    @abstractmethod
    def remove_task(self, task_id: str) -> bool:
        """Remove task from constellation"""
        pass
    
    @abstractmethod
    def add_dependency(self, from_task: str, to_task: str) -> bool:
        """Add dependency between tasks"""
        pass

class SessionManager(ABC):
    """Interface for session management"""
    
    @abstractmethod
    async def create_session(self, config: Dict[str, Any]) -> 'Session':
        """Create new session"""
        pass
    
    @abstractmethod
    def get_active_sessions(self) -> List['Session']:
        """Get list of active sessions"""
        pass
    
    @abstractmethod
    async def cleanup_session(self, session_id: str) -> bool:
        """Cleanup and remove session"""
        pass
```

## 🎯 Type System

### Core Types

Fundamental type definitions used throughout Galaxy.

```python
from typing import Union, Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# Status Enums
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"

class ExecutionStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DeviceStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"

# Priority and Type Enums
class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TaskType(Enum):
    DATA_PROCESSING = "data_processing"
    MACHINE_LEARNING = "machine_learning"
    WEB_AUTOMATION = "web_automation"
    FILE_OPERATION = "file_operation"
    API_CALL = "api_call"
    CUSTOM = "custom"
```

### Data Structures

Core data structures for Galaxy operations.

```python
@dataclass
class ExecutionResult:
    """Result of constellation execution"""
    success: bool
    completed_tasks: List[str]
    failed_tasks: List[str]
    execution_time_seconds: float
    total_tasks: int
    error_messages: List[str]
    performance_metrics: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class ValidationResult:
    """Result of constellation validation"""
    is_valid: bool
    errors: List['ValidationError']
    warnings: List['ValidationWarning']
    validation_time_seconds: float
    checks_performed: List[str]

@dataclass
class DeviceInfo:
    """Device information and capabilities"""
    device_id: str
    device_type: str
    capabilities: List[str]
    status: DeviceStatus
    resource_usage: Dict[str, float]
    last_seen: datetime
    metadata: Dict[str, Any]

@dataclass
class SessionResult:
    """Result of session execution"""
    session_id: str
    success: bool
    rounds_completed: int
    total_duration_seconds: float
    final_constellation: Optional['TaskConstellation']
    error_info: Optional['ErrorInfo']
    performance_summary: Dict[str, Any]
```

### Type Aliases

Convenient type aliases for common patterns.

```python
from typing import TypeAlias

# Configuration types
ConfigDict: TypeAlias = Dict[str, Any]
TaskId: TypeAlias = str
DeviceId: TypeAlias = str
SessionId: TypeAlias = str

# Handler types
EventHandler: TypeAlias = Callable[[Event], Awaitable[None]]
ErrorHandler: TypeAlias = Callable[[Exception], Optional[bool]]
ProgressCallback: TypeAlias = Callable[[float], None]

# Result types
TaskResult: TypeAlias = Dict[str, Any]
ConstellationMetrics: TypeAlias = Dict[str, Union[int, float, str]]
PerformanceMetrics: TypeAlias = Dict[str, Union[int, float]]
```

## 🚨 Exception Hierarchy

### Custom Exception Classes

Comprehensive exception hierarchy for error handling.

```python
class GalaxyError(Exception):
    """Base exception for all Galaxy errors"""
    
    def __init__(self, message: str, error_code: str = None, context: Dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.utcnow()

class SessionError(GalaxyError):
    """Errors related to session management"""
    pass

class AgentError(GalaxyError):
    """Errors related to agent operations"""
    pass

class ConstellationError(GalaxyError):
    """Errors related to constellation operations"""
    pass

class ExecutionError(GalaxyError):
    """Errors during task execution"""
    pass

class ValidationError(GalaxyError):
    """Errors during validation"""
    pass

class DeviceError(GalaxyError):
    """Errors related to device operations"""
    pass

class ConfigurationError(GalaxyError):
    """Errors in configuration"""
    pass
```

### Error Handling Utilities

Utilities for robust error handling and recovery.

```python
from ufo.galaxy.core.exceptions import GalaxyErrorHandler

class GalaxyErrorHandler:
    def __init__(self):
        self._error_handlers = {}
        self._default_handler = self._default_error_handler
    
    def register_handler(self, error_type: type, handler: ErrorHandler):
        """Register custom error handler for specific error type"""
        self._error_handlers[error_type] = handler
    
    async def handle_error(self, error: Exception) -> bool:
        """Handle error with appropriate handler"""
        error_type = type(error)
        handler = self._error_handlers.get(error_type, self._default_handler)
        return await handler(error)
    
    def _default_error_handler(self, error: Exception) -> bool:
        """Default error handling logic"""
        logger.error(f"Unhandled error: {error}")
        return False

# Usage
error_handler = GalaxyErrorHandler()

# Register custom handlers
error_handler.register_handler(
    ConstellationError,
    lambda e: print(f"Constellation error: {e.message}")
)

# Handle errors
try:
    # Galaxy operations
    pass
except Exception as e:
    await error_handler.handle_error(e)
```

## 🛠️ Base Classes and Mixins

### BaseComponent

Base class for all Galaxy components with common functionality.

```python
from ufo.galaxy.core.base import BaseComponent

class BaseComponent:
    """Base class for all Galaxy components"""
    
    def __init__(self, component_name: str, config: ConfigDict = None):
        self.component_name = component_name
        self.config = config or {}
        self.logger = self._setup_logger()
        self.is_initialized = False
        self.creation_time = datetime.utcnow()
    
    def initialize(self) -> bool:
        """Initialize component"""
        try:
            self._validate_config()
            self._setup_resources()
            self.is_initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.component_name}: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup component resources"""
        self._cleanup_resources()
        self.is_initialized = False
    
    def _setup_logger(self) -> logging.Logger:
        """Setup component logger"""
        return logging.getLogger(f"galaxy.{self.component_name}")
    
    def _validate_config(self) -> None:
        """Validate component configuration"""
        pass
    
    def _setup_resources(self) -> None:
        """Setup component resources"""
        pass
    
    def _cleanup_resources(self) -> None:
        """Cleanup component resources"""
        pass
```

### Configurable Mixin

Mixin for components that need configuration management.

```python
from ufo.galaxy.core.base import Configurable

class Configurable:
    """Mixin for configurable components"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config_schema = {}
        self._config_defaults = {}
    
    def set_config(self, config: ConfigDict) -> bool:
        """Set component configuration with validation"""
        try:
            validated_config = self._validate_config_schema(config)
            merged_config = {**self._config_defaults, **validated_config}
            self.config = merged_config
            return True
        except Exception as e:
            self.logger.error(f"Invalid configuration: {e}")
            return False
    
    def get_config(self, key: str = None) -> Any:
        """Get configuration value or entire config"""
        if key is None:
            return self.config.copy()
        return self.config.get(key)
    
    def update_config(self, updates: ConfigDict) -> bool:
        """Update specific configuration values"""
        try:
            current_config = self.config.copy()
            current_config.update(updates)
            return self.set_config(current_config)
        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return False
```

### Serializable Mixin

Mixin for components that need serialization support.

```python
from ufo.galaxy.core.base import Serializable

class Serializable:
    """Mixin for serializable components"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary"""
        return {
            "component_name": self.component_name,
            "component_type": self.__class__.__name__,
            "config": self.config,
            "creation_time": self.creation_time.isoformat(),
            "is_initialized": self.is_initialized
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Serializable':
        """Create component from dictionary"""
        instance = cls(
            component_name=data["component_name"],
            config=data["config"]
        )
        instance.creation_time = datetime.fromisoformat(data["creation_time"])
        instance.is_initialized = data["is_initialized"]
        return instance
    
    def save_to_file(self, filepath: str) -> bool:
        """Save component to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2, default=str)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save to {filepath}: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str) -> Optional['Serializable']:
        """Load component from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            logging.error(f"Failed to load from {filepath}: {e}")
            return None
```

## 🔧 Utility Functions

### Core Utilities

Shared utility functions used across Galaxy.

```python
from ufo.galaxy.core.utils import (
    generate_unique_id, validate_graph_structure, 
    deep_merge_dicts, safe_json_serialize
)

# ID generation
task_id = generate_unique_id("task")  # "task_abc123def456"
session_id = generate_unique_id("session")  # "session_xyz789uvw012"

# Graph utilities
is_valid_dag = validate_graph_structure(tasks, dependencies)

# Dictionary utilities
merged_config = deep_merge_dicts(default_config, user_config)

# Serialization utilities
json_str = safe_json_serialize(complex_object, indent=2)
```

### Performance Utilities

Performance monitoring and optimization utilities.

```python
from ufo.galaxy.core.utils import PerformanceMonitor, timing_decorator

# Performance monitoring
monitor = PerformanceMonitor()

with monitor.measure("constellation_creation"):
    constellation = create_constellation()

metrics = monitor.get_metrics()
print(f"Constellation creation took {metrics['constellation_creation']}ms")

# Timing decorator
@timing_decorator("request_processing")
async def process_request(request: str):
    # Process request
    return result
```

## 🧪 Testing Support

### Core Testing Utilities

Testing utilities for Galaxy components.

```python
from ufo.galaxy.core.testing import ComponentTestHarness, MockEventBus

# Component testing
test_harness = ComponentTestHarness()

# Test component lifecycle
lifecycle_test = test_harness.test_component_lifecycle(MyComponent)
assert lifecycle_test.passed

# Mock event bus for testing
mock_event_bus = MockEventBus()
mock_event_bus.subscribe(EventType.TASK_COMPLETED, mock_handler)

# Events will be captured for testing
await mock_event_bus.emit(TaskCompletedEvent("test_task", {}))
captured_events = mock_event_bus.get_captured_events()
```

## 🚀 Getting Started

### Basic Core Usage

```python
from ufo.galaxy.core import EventBus, BaseComponent, Configurable

# Create event-driven component
class MyGalaxyComponent(BaseComponent, Configurable):
    def __init__(self, name: str):
        super().__init__(name)
        self.event_bus = EventBus()
    
    def setup_events(self):
        self.event_bus.subscribe(
            EventType.TASK_COMPLETED,
            self.handle_task_completion
        )
    
    async def handle_task_completion(self, event):
        self.logger.info(f"Task completed: {event.task_id}")

# Use the component
component = MyGalaxyComponent("my_component")
component.initialize()
component.setup_events()
```

### Advanced Core Usage

```python
from ufo.galaxy.core import (
    EventBus, Observer, Subject, 
    GalaxyErrorHandler, PerformanceMonitor
)

# Create advanced component with error handling and monitoring
class AdvancedGalaxyComponent(BaseComponent, Observer):
    def __init__(self, name: str):
        super().__init__(name)
        self.event_bus = EventBus(enable_history=True)
        self.error_handler = GalaxyErrorHandler()
        self.performance_monitor = PerformanceMonitor()
        
        # Setup error handlers
        self.error_handler.register_handler(
            ConstellationError,
            self.handle_constellation_error
        )
    
    async def handle_constellation_error(self, error):
        self.logger.error(f"Constellation error: {error.message}")
        # Implement recovery logic
        return True
    
    async def update(self, event):
        with self.performance_monitor.measure("event_processing"):
            try:
                await self.process_event(event)
            except Exception as e:
                await self.error_handler.handle_error(e)
```

## 🔗 Integration

The core module provides the foundation for all Galaxy components:

- **[Agents](../agents/README.md)**: Use interfaces and event system
- **[Constellation](../constellation/README.md)**: Leverage types and events
- **[Session](../session/README.md)**: Use observer pattern and events
- **[Client](../client/README.md)**: Implement core interfaces
- **[Visualization](../visualization/README.md)**: Subscribe to event streams

---

*The foundational bedrock that enables elegant, extensible, and robust Galaxy architecture* ⚡
