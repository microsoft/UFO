# Galaxy Constellation Module

The Constellation module is the core DAG management system of the Galaxy Framework, responsible for creating, managing, and orchestrating task workflows represented as directed acyclic graphs.

## 🌟 Overview

A constellation in Galaxy represents a structured workflow where tasks (TaskStar) are connected by dependencies (TaskStarLine). This module provides comprehensive DAG operations including creation, validation, editing, execution orchestration, and device assignment.

## 🏗️ Architecture

```
ufo/galaxy/constellation/
├── __init__.py                     # Module exports and main interfaces
├── enums.py                       # Core enumerations (TaskStatus, DependencyType, etc.)
├── task_constellation.py          # Main DAG container implementing IConstellation
├── task_star.py                   # Individual task nodes implementing ITask
├── task_star_line.py              # Dependency edges implementing IDependency
├── editor/                        # Interactive DAG editing with command pattern
│   ├── constellation_editor.py    # Main editor controller
│   ├── commands.py                # Command implementations
│   ├── command_history.py         # Undo/redo functionality
│   ├── command_interface.py       # Command pattern interfaces
│   ├── command_invoker.py         # Command execution manager
│   └── command_registry.py        # Command registration system
└── orchestrator/                  # Execution coordination
    ├── orchestrator.py            # Task execution orchestrator
    └── constellation_manager.py   # Device and state management
```

# Galaxy Constellation Module

The Constellation module is the core DAG (Directed Acyclic Graph) management system of the Galaxy Framework, responsible for creating, managing, and orchestrating task workflows represented as constellations of interconnected tasks.

## 🌟 Overview

A constellation in Galaxy represents a structured workflow where individual tasks (TaskStar) are connected by dependency relationships (TaskStarLine). This module provides comprehensive DAG operations including creation, validation, editing, execution orchestration, and device assignment across multiple platforms.

## 🏗️ Architecture

```
ufo/galaxy/constellation/
├── __init__.py                     # Module exports and core interfaces
├── enums.py                       # Core enumerations and type definitions
├── task_constellation.py          # Main DAG container (implements IConstellation)
├── task_star.py                   # Individual task nodes (implements ITask)
├── task_star_line.py              # Dependency edges (implements IDependency)
├── editor/                        # Interactive constellation editing system
│   ├── __init__.py
│   ├── constellation_editor.py    # Main editor with command pattern interface
│   ├── commands.py                # Concrete command implementations
│   ├── command_history.py         # Command history management
│   ├── command_interface.py       # Command pattern base interfaces
│   ├── command_invoker.py         # Command execution and undo/redo
│   └── command_registry.py        # Command registration and discovery
└── orchestrator/                  # Execution coordination and device management
    ├── orchestrator.py            # Task execution orchestrator
    └── constellation_manager.py   # Device assignment and constellation lifecycle
```

## 🎯 Core Components

### TaskConstellation

The primary DAG container implementing the `IConstellation` interface, providing comprehensive workflow management capabilities.

#### Core Features
- **DAG Management**: Complete task graph operations with cycle detection and validation
- **State Tracking**: Constellation state machine (CREATED/READY/EXECUTING/COMPLETED/FAILED/PARTIALLY_FAILED)
- **Task Lifecycle**: Full task status management from creation through completion
- **Dependency Resolution**: Complex dependency evaluation with conditional logic
- **Device Integration**: Task-to-device assignment coordination
- **Persistence**: Complete JSON serialization/deserialization support
- **Event Integration**: Real-time event publishing for monitoring and visualization
- **LLM Integration**: String representations optimized for LLM consumption

#### Core Properties and State
```python
class TaskConstellation(IConstellation):
    # Core Identification
    constellation_id: str                    # Auto-generated unique identifier
    name: str                               # Human-readable name
    state: ConstellationState               # Current execution state
    
    # Content Management
    tasks: Dict[str, TaskStar]              # Task collection by ID
    dependencies: Dict[str, TaskStarLine]   # Dependency collection by ID
    
    # Metadata and Tracking
    metadata: Dict[str, Any]                # User-defined metadata
    llm_source: Optional[str]               # LLM generation source info
    created_at: datetime                    # Creation timestamp
    updated_at: datetime                    # Last modification timestamp
    execution_start_time: Optional[datetime]
    execution_end_time: Optional[datetime]
    
    # Configuration
    enable_visualization: bool              # Visualization integration flag
```

#### State Management
```python
class ConstellationState(Enum):
    CREATED = "created"                     # Initial state, not validated
    READY = "ready"                         # Validated, ready for execution  
    EXECUTING = "executing"                 # Currently executing tasks
    COMPLETED = "completed"                 # All tasks completed successfully
    FAILED = "failed"                       # Execution failed completely
    PARTIALLY_FAILED = "partially_failed"  # Some tasks failed, some succeeded
```

#### Usage Example
```python
from ufo.galaxy.constellation import TaskConstellation, TaskStar, TaskStarLine
from ufo.galaxy.constellation.enums import TaskPriority, DeviceType

# Create constellation
constellation = TaskConstellation(
    name="Data Processing Pipeline",
    enable_visualization=True
)

# Create and add tasks
collect_task = TaskStar(
    name="collect_data",
    description="Collect data from various sources",
    priority=TaskPriority.HIGH,
    device_type=DeviceType.WINDOWS,
    timeout=300.0
)
constellation.add_task(collect_task)

process_task = TaskStar(
    name="process_data",
    description="Process collected data",
    priority=TaskPriority.MEDIUM,
    device_type=DeviceType.LINUX
)
constellation.add_task(process_task)

# Create dependency
dependency = TaskStarLine.create_success_only(
    from_task_id="collect_data",
    to_task_id="process_data",
    description="Process only after successful collection"
)
constellation.add_dependency(dependency)

# Validate and get execution plan
is_valid, errors = constellation.validate_dag()
if is_valid:
    ready_tasks = constellation.get_ready_tasks()
    print(f"Ready to execute: {[t.name for t in ready_tasks]}")
```

#### Key Methods
```python
class TaskConstellation:
    # Task Management
    def add_task(self, task: TaskStar) -> None
    def remove_task(self, task_id: str) -> None
    def get_task(self, task_id: str) -> Optional[TaskStar]
    def get_all_tasks(self) -> List[TaskStar]
    
    # Dependency Management  
    def add_dependency(self, dependency: TaskStarLine) -> None
    def remove_dependency(self, dependency_id: str) -> None
    def get_dependency(self, dependency_id: str) -> Optional[TaskStarLine]
    def get_task_dependencies(self, task_id: str) -> List[TaskStarLine]
    
    # Execution Management
    def get_ready_tasks(self) -> List[TaskStar]
    def get_running_tasks(self) -> List[TaskStar]
    def get_completed_tasks(self) -> List[TaskStar]
    def get_failed_tasks(self) -> List[TaskStar]
    def start_execution(self) -> None
    def complete_execution(self) -> None
    def mark_task_completed(self, task_id: str, success: bool, result: Any, error: Exception) -> List[TaskStar]
    
    # Validation and Analysis
    def validate_dag(self) -> Tuple[bool, List[str]]
    def has_cycle(self) -> bool
    def get_topological_order(self) -> List[str]
    def is_complete(self) -> bool
    def update_state(self) -> None
    
    # Persistence
    def to_dict(self) -> Dict[str, Any]
    def to_json(self, save_path: Optional[str] = None) -> str
    def to_llm_string(self) -> str
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskConstellation'
    @classmethod  
    def from_json(cls, json_data: str = None, file_path: str = None) -> 'TaskConstellation'
    
    # Statistics and Monitoring
    def get_statistics(self) -> Dict[str, Any]
    def display_dag(self, mode: str = "overview") -> None
```

### TaskStar

Individual task nodes representing atomic work units within the constellation, implementing the `ITask` interface with comprehensive execution and lifecycle management.

#### Core Features
- **Unique Identification**: Auto-generated UUID-based task IDs with human-readable names
- **Rich Metadata**: Comprehensive task description, execution tips, and custom data
- **Device Targeting**: Device type specification and assignment coordination
- **Priority Management**: Four-level priority system for execution scheduling
- **Lifecycle Tracking**: Complete status management from creation through completion
- **Retry Logic**: Built-in retry mechanism with configurable attempt limits
- **Timeout Management**: Per-task execution timeout with failure handling
- **Result Tracking**: Execution results, errors, and performance metrics
- **Validation System**: Built-in validation with detailed error reporting
- **Persistence**: Full JSON serialization with type safety

#### Task Properties and State
```python
class TaskStar(ITask):
    # Core Identification
    task_id: TaskId                        # Auto-generated UUID
    name: str                              # Short, human-readable name
    description: str                       # Detailed task description
    tips: Optional[List[str]]              # Execution hints and guidance
    
    # Device and Execution Configuration
    target_device_id: Optional[str]        # Assigned device identifier
    device_type: Optional[DeviceType]      # Target device type constraint
    priority: TaskPriority                 # Execution priority level
    timeout: Optional[float]               # Maximum execution time (seconds)
    
    # Retry and Error Handling
    retry_count: int                       # Maximum retry attempts allowed
    current_retry: int                     # Current retry attempt number
    
    # Task Data and Configuration
    task_data: Dict[str, Any]              # Custom execution parameters
    expected_output_type: Optional[str]    # Expected result format/type
    
    # Execution State and Results
    status: TaskStatus                     # Current execution status
    result: Optional[Any]                  # Execution result (if successful)
    error: Optional[Exception]             # Error information (if failed)
    execution_start_time: Optional[datetime]
    execution_end_time: Optional[datetime]
    
    # Timestamps and Tracking
    created_at: datetime                   # Task creation time
    updated_at: datetime                   # Last modification time
    
    # Dependency Management (managed by TaskConstellation)
    _dependencies: set[TaskId]             # Prerequisite task IDs
    _dependents: set[TaskId]              # Dependent task IDs
```

#### Task Status Lifecycle
```python
class TaskStatus(Enum):
    PENDING = "pending"                    # Waiting for dependencies or execution
    RUNNING = "running"                    # Currently executing
    COMPLETED = "completed"                # Successfully completed
    FAILED = "failed"                      # Execution failed
    CANCELLED = "cancelled"                # Task was cancelled
    WAITING_DEPENDENCY = "waiting_dependency"  # Blocked by unmet dependencies
```

#### Priority and Device Types
```python
class TaskPriority(Enum):
    LOW = 1                                # Background/non-critical tasks
    MEDIUM = 2                             # Standard priority (default)
    HIGH = 3                               # Important/time-sensitive tasks
    CRITICAL = 4                           # Urgent/blocking tasks

class DeviceType(Enum):
    WINDOWS = "windows"                    # Windows desktop/server
    MACOS = "macos"                        # macOS desktop/server  
    LINUX = "linux"                       # Linux desktop/server
    ANDROID = "android"                    # Android mobile device
    IOS = "ios"                            # iOS mobile device
    WEB = "web"                            # Web browser environment
    API = "api"                            # API/service endpoint
```

#### Usage Example
```python
from ufo.galaxy.constellation import TaskStar, TaskPriority, DeviceType

# Create a comprehensive task
task = TaskStar(
    name="analyze_sales_data",
    description="Analyze Q4 sales data and generate insights",
    tips=[
        "Check for data quality issues before analysis",
        "Use the standard analytics template",
        "Include year-over-year comparisons"
    ],
    device_type=DeviceType.LINUX,
    priority=TaskPriority.HIGH,
    timeout=1800.0,  # 30 minutes
    retry_count=2,
    task_data={
        "input_file": "/data/sales_q4.csv",
        "analysis_type": "comprehensive",
        "output_format": "pdf",
        "include_charts": True
    },
    expected_output_type="analytics_report"
)

# Check task state and readiness
print(f"Task ready to execute: {task.is_ready_to_execute}")
print(f"Task is terminal: {task.is_terminal}")
print(f"Execution duration: {task.execution_duration} seconds")

# Task lifecycle management (typically handled by orchestrator)
task.start_execution()
# ... execution occurs ...
task.complete_with_success({"report_path": "/output/q4_report.pdf"})

# Handle retry logic
if task.should_retry():
    task.retry()
```

#### Key Methods  
```python
class TaskStar:
    # ITask Interface Implementation
    @property
    def task_id(self) -> TaskId
    @property  
    def name(self) -> str
    @property
    def description(self) -> str
    async def execute(self, device_manager: ConstellationDeviceManager) -> ExecutionResult
    def validate(self) -> bool
    
    # Lifecycle Management
    def start_execution(self) -> None
    def complete_with_success(self, result: Any) -> None
    def complete_with_failure(self, error: Exception) -> None
    def cancel(self) -> None
    def should_retry(self) -> bool
    def retry(self) -> None
    
    # Data and Configuration
    def update_task_data(self, data: Dict[str, Any]) -> None
    def get_validation_errors(self) -> List[str]
    def to_request_string(self) -> str
    
    # Dependency Management (used by TaskConstellation)
    def add_dependency(self, dependency_task_id: TaskId) -> None
    def remove_dependency(self, dependency_task_id: TaskId) -> None
    def add_dependent(self, dependent_task_id: TaskId) -> None
    def remove_dependent(self, dependent_task_id: TaskId) -> None
    
    # State Properties
    @property
    def is_terminal(self) -> bool           # Check if in final state
    @property  
    def is_ready_to_execute(self) -> bool   # Check if ready for execution
    @property
    def execution_duration(self) -> Optional[float]  # Get execution time
    
    # Persistence and Serialization
    def to_dict(self) -> Dict[str, Any]
    def to_json(self, save_path: Optional[str] = None) -> str
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskStar'
    @classmethod
    def from_json(cls, json_data: str = None, file_path: str = None) -> 'TaskStar'
```

### TaskStarLine

Dependency edges that define execution relationships between tasks, implementing the `IDependency` interface with sophisticated conditional logic and evaluation capabilities.

#### Core Features
- **Unique Identification**: Auto-generated UUID-based dependency identifiers
- **Rich Dependency Types**: Multiple dependency types with conditional evaluation
- **Condition Evaluation**: Custom condition functions with natural language descriptions
- **Satisfaction Tracking**: Real-time dependency satisfaction monitoring
- **Metadata Support**: Extensible metadata for custom dependency logic
- **Evaluation History**: Tracking of condition evaluation results and timing
- **Persistence**: Complete JSON serialization with condition preservation

#### Dependency Properties
```python
class TaskStarLine(IDependency):
    # Core Identification
    line_id: str                           # Auto-generated UUID
    from_task_id: str                      # Source/prerequisite task ID
    to_task_id: str                        # Target/dependent task ID
    
    # Dependency Configuration
    dependency_type: DependencyType        # Type of dependency relationship
    condition_description: str             # Human-readable condition description
    condition_evaluator: Optional[Callable[[Any], bool]]  # Condition evaluation function
    metadata: Dict[str, Any]               # Custom dependency metadata
    
    # State Tracking
    is_satisfied: bool                     # Current satisfaction status
    last_evaluation_result: Optional[bool] # Last condition evaluation result
    last_evaluation_time: Optional[datetime]  # Time of last evaluation
    
    # Timestamps
    created_at: datetime                   # Dependency creation time
    updated_at: datetime                   # Last modification time
```

#### Dependency Types
```python
class DependencyType(Enum):
    UNCONDITIONAL = "unconditional"       # Execute after prerequisite completes (any result)
    CONDITIONAL = "conditional"            # Execute only if custom condition is met
    SUCCESS_ONLY = "success_only"          # Execute only if prerequisite succeeds
    COMPLETION_ONLY = "completion_only"    # Execute after completion (ignore success/failure)
```

#### Usage Examples

**Basic Dependencies**
```python
from ufo.galaxy.constellation import TaskStarLine, DependencyType

# Unconditional dependency - execute after prerequisite completes
basic_dep = TaskStarLine.create_unconditional(
    from_task_id="collect_data",
    to_task_id="backup_data", 
    description="Always backup data after collection"
)

# Success-only dependency - execute only if prerequisite succeeds
success_dep = TaskStarLine.create_success_only(
    from_task_id="validate_data",
    to_task_id="process_data",
    description="Process only if validation succeeds"
)
```

**Conditional Dependencies with Custom Logic**
```python
# Custom condition function
def check_data_quality(result):
    """Check if data quality meets minimum threshold"""
    if not result or not isinstance(result, dict):
        return False
    return result.get("quality_score", 0) >= 0.85

# Conditional dependency with custom evaluator
conditional_dep = TaskStarLine.create_conditional(
    from_task_id="analyze_data",
    to_task_id="generate_report", 
    condition_description="Generate report only if data quality score >= 85%",
    condition_evaluator=check_data_quality
)

# Complex business logic condition  
def check_business_rules(result):
    """Verify business rules are met"""
    if not result:
        return False
    
    # Check multiple criteria
    revenue_ok = result.get("revenue", 0) > 10000
    compliance_ok = result.get("compliance_passed", False)
    data_complete = result.get("data_completeness", 0) > 0.95
    
    return revenue_ok and compliance_ok and data_complete

business_dep = TaskStarLine.create_conditional(
    from_task_id="business_analysis",
    to_task_id="executive_report",
    condition_description="Generate executive report only if business rules are satisfied",
    condition_evaluator=check_business_rules
)
```

**Dependency Evaluation and Management**
```python
# Evaluate dependency condition
prerequisite_result = {"quality_score": 0.92, "record_count": 5000}

if conditional_dep.evaluate_condition(prerequisite_result):
    print("Dependency satisfied - dependent task can execute")
else:
    print("Dependency not satisfied - dependent task blocked")

# Check evaluation history
print(f"Last evaluation: {conditional_dep.last_evaluation_result}")
print(f"Evaluation time: {conditional_dep.last_evaluation_time}")

# Manual dependency control
conditional_dep.mark_satisfied()  # Override condition
conditional_dep.reset_satisfaction()  # Reset satisfaction status

# Update dependency metadata
conditional_dep.update_metadata({
    "business_priority": "high",
    "escalation_contact": "data-team@company.com",
    "retry_policy": "exponential_backoff"
})
```

#### Factory Methods for Common Patterns
```python
class TaskStarLine:
    @classmethod
    def create_unconditional(cls, from_task_id: str, to_task_id: str, description: str) -> 'TaskStarLine'
    
    @classmethod  
    def create_success_only(cls, from_task_id: str, to_task_id: str, description: str) -> 'TaskStarLine'
    
    @classmethod
    def create_conditional(cls, from_task_id: str, to_task_id: str, 
                          condition_description: str, condition_evaluator: Callable) -> 'TaskStarLine'
```

#### Key Methods
```python
class TaskStarLine:
    # IDependency Interface Implementation
    @property
    def source_task_id(self) -> str        # Get source task ID
    @property  
    def target_task_id(self) -> str        # Get target task ID
    def is_satisfied(self, completed_tasks: Optional[List[str]] = None) -> bool
    
    # Condition Management
    def evaluate_condition(self, prerequisite_result: Any) -> bool
    def set_condition_evaluator(self, evaluator: Callable[[Any], bool]) -> None
    def mark_satisfied(self) -> None
    def reset_satisfaction(self) -> None
    
    # Metadata and Configuration
    def update_metadata(self, metadata: Dict[str, Any]) -> None
    @property
    def dependency_type(self) -> DependencyType
    @dependency_type.setter
    def dependency_type(self, value: DependencyType) -> None
    
    # State and History
    @property
    def last_evaluation_result(self) -> Optional[bool]
    @property
    def last_evaluation_time(self) -> Optional[datetime]
    @property  
    def condition_description(self) -> str
    
    # Persistence
    def to_dict(self) -> Dict[str, Any]
    def to_json(self, save_path: Optional[str] = None) -> str
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskStarLine'
    @classmethod
    def from_json(cls, json_data: str = None, file_path: str = None) -> 'TaskStarLine'
```

### ConstellationEditor

High-level constellation editing interface implementing the Command Pattern for comprehensive DAG manipulation with full undo/redo support and command history tracking.

#### Core Features
- **Command Pattern Architecture**: All operations implemented as reversible commands
- **Undo/Redo System**: Complete command history with configurable history size
- **Observer Pattern**: Event notifications for all editing operations
- **Batch Operations**: Execute multiple operations in sequence with rollback support
- **Command Registry**: Discoverable command system with metadata and categories
- **Validation Integration**: Real-time validation with detailed error reporting
- **File Operations**: Load/save constellations with comprehensive error handling
- **Merge and Subgraph**: Advanced operations for constellation composition

#### Architecture Overview
```python
class ConstellationEditor:
    # Core Components
    _constellation: TaskConstellation      # Target constellation being edited
    _invoker: CommandInvoker              # Command execution and history management
    _observers: List[callable]            # Change notification observers
    
    # Configuration
    enable_history: bool                  # Command history enabled/disabled
    max_history_size: int                 # Maximum commands in history
```

#### Command Pattern Implementation
The editor uses a sophisticated command pattern where all operations are implemented as reversible commands:

```python
# Available Command Types
class CommandType:
    # Task Operations
    ADD_TASK = "add_task"
    REMOVE_TASK = "remove_task"  
    UPDATE_TASK = "update_task"
    
    # Dependency Operations
    ADD_DEPENDENCY = "add_dependency"
    REMOVE_DEPENDENCY = "remove_dependency"
    UPDATE_DEPENDENCY = "update_dependency"
    
    # Bulk Operations
    BUILD_CONSTELLATION = "build_constellation"
    CLEAR_CONSTELLATION = "clear_constellation"
    
    # File Operations
    LOAD_CONSTELLATION = "load_constellation"
    SAVE_CONSTELLATION = "save_constellation"
```

#### Usage Examples

**Basic Editing Operations**
```python
from ufo.galaxy.constellation.editor import ConstellationEditor
from ufo.galaxy.constellation import TaskConstellation, TaskStar, TaskPriority

# Initialize editor with new constellation
editor = ConstellationEditor(
    constellation=TaskConstellation(name="My Workflow"),
    enable_history=True,
    max_history_size=50
)

# Create and add tasks
task1 = editor.create_and_add_task(
    task_id="data_extraction",
    name="Extract Data",
    description="Extract data from multiple sources",
    priority=TaskPriority.HIGH,
    timeout=600.0
)

task2 = editor.create_and_add_task(
    task_id="data_validation", 
    name="Validate Data",
    description="Validate extracted data quality",
    priority=TaskPriority.MEDIUM
)

# Create dependencies
editor.create_and_add_dependency(
    from_task_id="data_extraction",
    to_task_id="data_validation",
    dependency_type="SUCCESS_ONLY"
)

# Update task properties
editor.update_task("data_extraction", timeout=900.0, retry_count=3)

print(f"Constellation has {len(editor.list_tasks())} tasks")
print(f"Can undo: {editor.can_undo()}")
```

**Command History and Undo/Redo**
```python
# View command history
history = editor.get_history()
for i, command_desc in enumerate(history):
    print(f"{i+1}. {command_desc}")

# Undo last operation
if editor.can_undo():
    print(f"Undoing: {editor.get_undo_description()}")
    editor.undo()

# Redo operation
if editor.can_redo():
    print(f"Redoing: {editor.get_redo_description()}")
    editor.redo()

# Clear history
editor.clear_history()
```

**Bulk Operations and File Handling**
```python
# Build constellation from configuration
config = {
    "tasks": [
        {
            "task_id": "task1",
            "name": "First Task", 
            "description": "Initial task",
            "priority": TaskPriority.HIGH.value
        },
        {
            "task_id": "task2",
            "name": "Second Task",
            "description": "Follow-up task", 
            "priority": TaskPriority.MEDIUM.value
        }
    ],
    "dependencies": [
        {
            "from_task_id": "task1",
            "to_task_id": "task2",
            "dependency_type": "SUCCESS_ONLY"
        }
    ],
    "metadata": {
        "author": "data_team",
        "version": "1.0"
    }
}

# Build constellation (clears existing content)
editor.build_constellation(config, clear_existing=True)

# Save and load operations
editor.save_constellation("my_workflow.json")
editor.load_constellation("my_workflow.json")

# Load from dictionary or JSON string
editor.load_from_dict(config)
editor.load_from_json_string('{"tasks": [], "dependencies": []}')
```

**Advanced Operations**
```python
# Create subgraph with specific tasks
subgraph_editor = editor.create_subgraph(["task1", "task2", "task3"])

# Merge another constellation
other_editor = ConstellationEditor(other_constellation)
editor.merge_constellation(other_editor, prefix="imported_")

# Batch operations with error handling
operations = [
    lambda ed: ed.create_and_add_task("batch_task1", "Batch Task 1"),
    lambda ed: ed.create_and_add_task("batch_task2", "Batch Task 2"),
    lambda ed: ed.create_and_add_dependency("batch_task1", "batch_task2", "UNCONDITIONAL")
]

results = editor.batch_operations(operations)
for i, result in enumerate(results):
    if isinstance(result, Exception):
        print(f"Operation {i+1} failed: {result}")
    else:
        print(f"Operation {i+1} succeeded: {result}")
```

**Observer Pattern for Change Notifications**
```python
def constellation_observer(editor, command, result):
    """Observer function for constellation changes"""
    print(f"Command executed: {command}")
    print(f"Result: {result}")
    print(f"Constellation now has {len(editor.constellation.tasks)} tasks")

# Add observer
editor.add_observer(constellation_observer)

# Operations will now trigger notifications
editor.add_task(new_task)  # Observer will be called

# Remove observer
editor.remove_observer(constellation_observer)
```

#### Key Methods
```python
class ConstellationEditor:
    # Task Management
    def add_task(self, task: Union[TaskStar, Dict[str, Any]]) -> TaskStar
    def create_and_add_task(self, task_id: str, description: str, name: str = "", **kwargs) -> TaskStar
    def remove_task(self, task_id: str) -> str
    def update_task(self, task_id: str, **updates) -> TaskStar
    def get_task(self, task_id: str) -> Optional[TaskStar]
    def list_tasks(self) -> List[TaskStar]
    
    # Dependency Management
    def add_dependency(self, dependency: Union[TaskStarLine, Dict[str, Any]]) -> TaskStarLine
    def create_and_add_dependency(self, from_task_id: str, to_task_id: str, dependency_type: str = "UNCONDITIONAL", **kwargs) -> TaskStarLine
    def remove_dependency(self, dependency_id: str) -> str
    def update_dependency(self, dependency_id: str, **updates) -> TaskStarLine
    def get_dependency(self, dependency_id: str) -> Optional[TaskStarLine]
    def list_dependencies(self) -> List[TaskStarLine]
    def get_task_dependencies(self, task_id: str) -> List[TaskStarLine]
    
    # Bulk Operations
    def build_constellation(self, config: Dict[str, Any], clear_existing: bool = True) -> TaskConstellation
    def build_from_tasks_and_dependencies(self, tasks: List[Dict], dependencies: List[Dict], clear_existing: bool = True, metadata: Optional[Dict] = None) -> TaskConstellation
    def clear_constellation(self) -> TaskConstellation
    
    # File Operations
    def load_constellation(self, file_path: str) -> TaskConstellation
    def save_constellation(self, file_path: str) -> str
    def load_from_dict(self, data: Dict[str, Any]) -> TaskConstellation
    def load_from_json_string(self, json_string: str) -> TaskConstellation
    
    # History Operations
    def undo(self) -> bool
    def redo(self) -> bool
    def can_undo(self) -> bool
    def can_redo(self) -> bool
    def get_undo_description(self) -> Optional[str]
    def get_redo_description(self) -> Optional[str]
    def clear_history(self) -> None
    def get_history(self) -> List[str]
    
    # Observer Management
    def add_observer(self, observer: callable) -> None
    def remove_observer(self, observer: callable) -> None
    
    # Validation and Analysis
    def validate_constellation(self) -> tuple[bool, List[str]]
    def get_topological_order(self) -> List[str]
    def has_cycles(self) -> bool
    def get_ready_tasks(self) -> List[TaskStar]
    def get_statistics(self) -> Dict[str, Any]
    
    # Advanced Operations  
    def batch_operations(self, operations: List[callable]) -> List[Any]
    def create_subgraph(self, task_ids: List[str]) -> 'ConstellationEditor'
    def merge_constellation(self, other_editor: 'ConstellationEditor', prefix: str = "") -> None
    def display_constellation(self, mode: str = "overview") -> None
    
    # Command Registry Integration
    def list_available_commands(self, category: Optional[str] = None) -> Dict[str, Dict[str, Any]]
    def get_command_metadata(self, command_name: str) -> Optional[Dict[str, Any]]
    def execute_command_by_name(self, command_name: str, *args, **kwargs) -> Any
    def get_command_categories(self) -> List[str]
```

### TaskConstellationOrchestrator

High-level execution coordinator that manages constellation execution across multiple devices using event-driven patterns and delegation to specialized managers.

#### Core Features
- **Event-Driven Architecture**: Complete integration with Galaxy event system for real-time coordination
- **Device Management Integration**: Works with ConstellationDeviceManager for multi-device coordination  
- **Delegation Pattern**: Delegates device assignment and state management to ConstellationManager
- **Async Execution**: Full async/await support for concurrent task execution
- **Assignment Strategies**: Multiple device assignment strategies with customization
- **Progress Monitoring**: Real-time execution tracking with event publishing
- **Error Recovery**: Comprehensive error handling with graceful failure management
- **Execution Control**: Support for pause/resume/cancel operations

#### Architecture Integration
```python
class TaskConstellationOrchestrator:
    # Core Components
    _device_manager: ConstellationDeviceManager    # Device communication
    _constellation_manager: ConstellationManager  # Device assignment and state management
    _event_bus: EventBus                          # Event publishing and coordination
    _execution_tasks: Dict[str, asyncio.Task]     # Active task execution tracking
    _logger: Optional[logging.Logger]             # Execution logging
```

#### Device Assignment Strategies
The orchestrator supports multiple strategies for assigning tasks to devices:

```python
# Assignment Strategy Types
ASSIGNMENT_STRATEGIES = {
    "round_robin": "Distribute tasks evenly across available devices",
    "capability_based": "Assign based on device capabilities and task requirements", 
    "load_balanced": "Consider current device load for optimal distribution"
}
```

#### Usage Examples

**Basic Constellation Execution**
```python
from ufo.galaxy.constellation import TaskConstellationOrchestrator
from ufo.galaxy.client.device_manager import ConstellationDeviceManager

# Initialize components
device_manager = ConstellationDeviceManager()
orchestrator = TaskConstellationOrchestrator(
    device_manager=device_manager,
    enable_logging=True
)

# Create constellation (from previous examples)
constellation = create_sample_constellation()

# Execute with automatic device assignment
result = await orchestrator.orchestrate_constellation(
    constellation,
    assignment_strategy="capability_based"
)

# Check execution results
if result["status"] == "completed":
    print(f"✅ Execution completed successfully!")
    print(f"Total tasks: {result['total_tasks']}")
    print(f"Statistics: {result['statistics']}")
else:
    print(f"❌ Execution failed")
    print(f"Error details: {result.get('error_details')}")
```

**Manual Device Assignment**
```python
# Define specific device assignments
manual_assignments = {
    "data_extraction": "windows_workstation_1",
    "data_validation": "linux_server_1",
    "data_processing": "gpu_cluster_1",
    "report_generation": "windows_workstation_2"
}

# Execute with manual assignments
result = await orchestrator.orchestrate_constellation(
    constellation,
    device_assignments=manual_assignments
)

# Verify assignments were applied
for task_id, device_id in manual_assignments.items():
    task = constellation.get_task(task_id)
    assert task.target_device_id == device_id
```

**Single Task Execution**
```python
# Execute individual task on specific device
task = TaskStar(
    name="data_analysis",
    description="Analyze dataset for patterns",
    device_type=DeviceType.LINUX
)

result = await orchestrator.execute_single_task(
    task,
    target_device_id="analytics_server_1"
)

print(f"Task result: {result}")
```

**Execution Monitoring and Control**
```python
# Start execution in background
execution_task = asyncio.create_task(
    orchestrator.orchestrate_constellation(constellation)
)

# Monitor execution progress
while not execution_task.done():
    status = await orchestrator.get_constellation_status(constellation)
    
    print(f"Running tasks: {len(status['running_tasks'])}")
    print(f"Completed tasks: {len(status['completed_tasks'])}")
    print(f"Failed tasks: {len(status['failed_tasks'])}")
    
    await asyncio.sleep(5)  # Check every 5 seconds

# Get final result
final_result = await execution_task
```

**Device Management Integration**
```python
# Get available devices
available_devices = await orchestrator.get_available_devices()
print("Available devices:")
for device in available_devices:
    print(f"  - {device['device_id']}: {device['device_type']} ({device['status']})")

# Auto-assign devices with preferences
device_preferences = {
    "cpu_intensive_task": "high_performance_server",
    "gpu_task": "gpu_cluster_node"
}

assignments = await orchestrator.assign_devices_automatically(
    constellation,
    strategy="capability_based",
    device_preferences=device_preferences
)

print("Device assignments:")
for task_id, device_id in assignments.items():
    print(f"  {task_id} -> {device_id}")
```

#### Event-Driven Coordination
The orchestrator publishes comprehensive events throughout execution:

```python
# Event Types Published by Orchestrator
EVENT_TYPES = {
    EventType.CONSTELLATION_STARTED: "Constellation execution began",
    EventType.CONSTELLATION_COMPLETED: "Constellation execution finished successfully", 
    EventType.CONSTELLATION_FAILED: "Constellation execution failed",
    EventType.TASK_STARTED: "Individual task execution started",
    EventType.TASK_COMPLETED: "Individual task completed successfully",
    EventType.TASK_FAILED: "Individual task execution failed"
}

# Subscribe to orchestration events
def handle_constellation_event(event):
    if event.event_type == EventType.CONSTELLATION_STARTED:
        print(f"🚀 Started executing constellation {event.constellation_id}")
    elif event.event_type == EventType.TASK_COMPLETED:
        print(f"✅ Task {event.task_id} completed")

event_bus.subscribe(EventType.CONSTELLATION_STARTED, handle_constellation_event)
event_bus.subscribe(EventType.TASK_COMPLETED, handle_constellation_event)
```

#### Integration with ConstellationManager
The orchestrator delegates device and state management to ConstellationManager:

```python
# ConstellationManager responsibilities:
# 1. Device assignment strategies and validation
# 2. Constellation registration and lifecycle tracking  
# 3. Device utilization monitoring
# 4. Task-device assignment validation
# 5. Available device discovery and management

# Access constellation manager
constellation_manager = orchestrator._constellation_manager

# Register constellation for management
constellation_id = constellation_manager.register_constellation(
    constellation,
    metadata={"priority": "high", "department": "analytics"}
)

# Get detailed status
status = await constellation_manager.get_constellation_status(constellation_id)

# Validate device assignments
is_valid, errors = constellation_manager.validate_constellation_assignments(constellation)
```

#### Key Methods
```python
class TaskConstellationOrchestrator:
    # Core Execution
    async def orchestrate_constellation(
        self, 
        constellation: TaskConstellation,
        device_assignments: Optional[Dict[str, str]] = None,
        assignment_strategy: str = "round_robin"
    ) -> Dict[str, Any]
    
    async def execute_single_task(
        self,
        task: TaskStar, 
        target_device_id: Optional[str] = None
    ) -> Any
    
    # Device Management
    def set_device_manager(self, device_manager: ConstellationDeviceManager) -> None
    async def get_available_devices(self) -> List[Dict[str, Any]]
    async def assign_devices_automatically(
        self,
        constellation: TaskConstellation,
        strategy: str = "round_robin", 
        device_preferences: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]
    
    # Monitoring and Status
    async def get_constellation_status(self, constellation: TaskConstellation) -> Dict[str, Any]
    
    # Internal Event Management
    async def _execute_task_with_events(self, task: TaskStar, constellation: TaskConstellation) -> None
```

## 🔍 DAG Validation and Management

### Constellation State Management
```python
class ConstellationState(Enum):
    CREATED = "created"                    # Initial state after creation
    READY = "ready"                        # Validated and ready for execution
    EXECUTING = "executing"                # Currently executing tasks
    COMPLETED = "completed"                # All tasks completed successfully
    FAILED = "failed"                      # Execution failed
    PARTIALLY_FAILED = "partially_failed" # Some tasks failed, some succeeded
```

### Built-in Validation
The TaskConstellation class provides built-in validation methods:

```python
# Check for cycles in the DAG
has_cycles = constellation.has_cycles()

# Get topological ordering of tasks
execution_order = constellation.get_topological_order()

# Get tasks ready for immediate execution
ready_tasks = constellation.get_ready_tasks()

# Validate entire constellation
validation_result = constellation.validate()
if not validation_result.is_valid:
    print("Validation errors found:")
    for error in validation_result.errors:
        print(f"  - {error}")
```

### Dependency Resolution
The system automatically resolves dependencies and determines execution readiness:

```python
# Check if task dependencies are satisfied
def _are_dependencies_satisfied(self, task_id: str) -> bool:
    task = self._tasks[task_id]
    for dep_task_id in task._dependencies:
        dep_task = self._tasks.get(dep_task_id)
        if not dep_task or dep_task.status != TaskStatus.COMPLETED:
            return False
    return True

# Get tasks that can execute immediately
ready_tasks = constellation.get_ready_tasks()
```

## ⚡ Event-Driven Architecture

The constellation module is deeply integrated with the Galaxy event system for real-time coordination and monitoring.

### Event Integration
```python
from ufo.galaxy.core.events import get_event_bus, ConstellationEvent, TaskEvent

# Orchestrator publishes events during execution
event_bus = get_event_bus()

# Task execution events
task_event = TaskEvent(
    event_type=EventType.TASK_STARTED,
    task_id="collect_data",
    constellation_id=constellation.constellation_id,
    timestamp=datetime.now(timezone.utc)
)
event_bus.publish(task_event)

# Constellation state change events
constellation_event = ConstellationEvent(
    event_type=EventType.CONSTELLATION_EXECUTION_STARTED,
    constellation_id=constellation.constellation_id,
    timestamp=datetime.now(timezone.utc)
)
event_bus.publish(constellation_event)
```

### Event Types
Events are published for all major constellation operations:
- **Task Events**: Task started, completed, failed, cancelled
- **Constellation Events**: Execution started, completed, failed
- **Dependency Events**: Dependency satisfied, failed
- **Device Events**: Device assigned, task dispatched

### Event Subscribers
Other components can subscribe to constellation events:
```python
def handle_task_completion(event):
    print(f"Task {event.task_id} completed successfully")

def handle_constellation_failure(event):
    print(f"Constellation {event.constellation_id} execution failed")

event_bus.subscribe(EventType.TASK_COMPLETED, handle_task_completion)
event_bus.subscribe(EventType.CONSTELLATION_EXECUTION_FAILED, handle_constellation_failure)
```

## 📊 Serialization and Persistence

### JSON Serialization
Both TaskStar and TaskStarLine support comprehensive JSON serialization:

```python
# Serialize constellation to JSON
constellation_json = constellation.to_json(save_path="workflow.json")

# Load constellation from JSON
loaded_constellation = TaskConstellation.from_json(file_path="workflow.json")

# Serialize individual tasks
task_json = task.to_json(save_path="task.json")
loaded_task = TaskStar.from_json(file_path="task.json")

# Serialize dependencies
dependency_json = dependency.to_json(save_path="dependency.json") 
loaded_dependency = TaskStarLine.from_json(file_path="dependency.json")
```

### Dictionary Conversion
Full support for dictionary-based serialization:

```python
# Convert to dictionary
constellation_dict = constellation.to_dict()
task_dict = task.to_dict()
dependency_dict = dependency.to_dict()

# Create from dictionary
new_constellation = TaskConstellation.from_dict(constellation_dict)
new_task = TaskStar.from_dict(task_dict)
new_dependency = TaskStarLine.from_dict(dependency_dict)
```

### Metadata Management
All components support flexible metadata:

```python
# Update task metadata
task.update_task_data({
    "processing_config": {"batch_size": 100},
    "quality_threshold": 0.95
})

# Update dependency metadata
dependency.update_metadata({
    "condition_params": {"min_confidence": 0.8},
    "retry_policy": "exponential_backoff"
})

# Update constellation metadata
constellation.update_metadata({
    "author": "data_team",
    "version": "2.1",
    "environment": "production"
})
```

## 🧪 Testing and Development

### Mock Objects
The module provides mock implementations for testing:

```python
# Mock constellation for testing
from tests.galaxy.mocks import MockTaskConstellation

mock_constellation = MockTaskConstellation()
mock_constellation.add_mock_tasks(["task1", "task2", "task3"])
mock_constellation.add_mock_dependencies([("task1", "task2"), ("task2", "task3")])

# Predictable execution results
result = await mock_orchestrator.orchestrate_constellation(mock_constellation)
assert result["success"]
assert result["completed_tasks"] == 3
```

### Test Utilities
```python
# Create test constellations programmatically
def create_linear_workflow(task_count: int) -> TaskConstellation:
    constellation = TaskConstellation(name=f"Linear-{task_count}")
    
    tasks = []
    for i in range(task_count):
        task = TaskStar(
            name=f"task_{i}",
            description=f"Task {i} in linear workflow",
            priority=TaskPriority.MEDIUM
        )
        tasks.append(task)
        constellation.add_task(task)
    
    # Add sequential dependencies
    for i in range(len(tasks) - 1):
        dep = TaskStarLine.create_unconditional(
            from_task_id=tasks[i].task_id,
            to_task_id=tasks[i + 1].task_id
        )
        constellation.add_dependency(dep)
    
    return constellation

# Create complex test scenarios
def create_diamond_workflow() -> TaskConstellation:
    """Create a diamond-shaped DAG for testing parallel execution."""
    constellation = TaskConstellation(name="Diamond-DAG")
    
    # Create tasks
    start_task = TaskStar(name="start", description="Start task")
    left_task = TaskStar(name="left", description="Left branch")
    right_task = TaskStar(name="right", description="Right branch")
    end_task = TaskStar(name="end", description="End task")
    
    for task in [start_task, left_task, right_task, end_task]:
        constellation.add_task(task)
    
    # Add dependencies to form diamond shape
    deps = [
        TaskStarLine.create_unconditional("start", "left"),
        TaskStarLine.create_unconditional("start", "right"), 
        TaskStarLine.create_unconditional("left", "end"),
        TaskStarLine.create_unconditional("right", "end")
    ]
    
    for dep in deps:
        constellation.add_dependency(dep)
    
    return constellation
```

## � Getting Started

### Basic Constellation Creation
```python
from ufo.galaxy.constellation import (
    TaskConstellation, TaskStar, TaskStarLine, 
    TaskPriority, DeviceType, DependencyType
)

# Create a simple data processing constellation
constellation = TaskConstellation(name="Data Processing Pipeline")

# Create tasks
collect_task = TaskStar(
    name="collect_data",
    description="Collect data from various sources",
    priority=TaskPriority.HIGH,
    device_type=DeviceType.WINDOWS,
    timeout=300.0
)

validate_task = TaskStar(
    name="validate_data", 
    description="Validate collected data quality",
    priority=TaskPriority.MEDIUM,
    device_type=DeviceType.LINUX
)

process_task = TaskStar(
    name="process_data",
    description="Process and transform data", 
    priority=TaskPriority.HIGH,
    device_type=DeviceType.WINDOWS
)

# Add tasks to constellation
for task in [collect_task, validate_task, process_task]:
    constellation.add_task(task)

# Create dependencies
collect_to_validate = TaskStarLine.create_success_only(
    from_task_id="collect_data",
    to_task_id="validate_data",
    description="Validate only if collection succeeds"
)

validate_to_process = TaskStarLine.create_conditional(
    from_task_id="validate_data",
    to_task_id="process_data", 
    condition_description="Process only if validation score > 0.8",
    condition_evaluator=lambda result: result.get("score", 0) > 0.8
)

# Add dependencies to constellation
constellation.add_dependency(collect_to_validate)
constellation.add_dependency(validate_to_process)

# Validate and check readiness
if constellation.validate().is_valid:
    ready_tasks = constellation.get_ready_tasks()
    print(f"Constellation ready with {len(ready_tasks)} tasks ready to execute")
```

### Execution with Orchestrator
```python
from ufo.galaxy.constellation import TaskConstellationOrchestrator
from ufo.galaxy.client.device_manager import ConstellationDeviceManager

# Initialize components
device_manager = ConstellationDeviceManager()
orchestrator = TaskConstellationOrchestrator(device_manager=device_manager)

# Execute the constellation
result = await orchestrator.orchestrate_constellation(
    constellation,
    assignment_strategy="capability_based"
)

# Check results
if result["success"]:
    print(f"Execution completed successfully!")
    print(f"Duration: {result['total_duration']} seconds")
    print(f"Completed tasks: {result['completed_tasks']}")
else:
    print(f"Execution failed:")
    print(f"Failed tasks: {result['failed_tasks']}")
```

## 🔗 Integration

The constellation module integrates seamlessly with all other Galaxy components:

- **[Agents](../agents/README.md)**: ConstellationAgent generates and modifies constellations from natural language requests
- **[Session](../session/README.md)**: Constellations are managed within GalaxySession lifecycle 
- **[Core](../core/README.md)**: Uses event system, interfaces (IConstellation, ITask, IDependency), and type definitions
- **[Client](../client/README.md)**: Orchestrator coordinates execution across devices via ConstellationDeviceManager
- **[Visualization](../visualization/README.md)**: Real-time DAG rendering and monitoring integration

## 📋 Key Interfaces

The module implements several core interfaces from the Galaxy framework:

### IConstellation
```python
class IConstellation:
    """Interface for DAG management operations."""
    def add_task(self, task: ITask) -> None
    def remove_task(self, task_id: str) -> None
    def get_task(self, task_id: str) -> Optional[ITask]
    def validate(self) -> ValidationResult
```

### ITask  
```python
class ITask:
    """Interface for individual task operations."""
    @property
    def task_id(self) -> TaskId
    @property
    def name(self) -> str
    @property
    def description(self) -> str
    async def execute(self, context: ProcessingContext) -> ExecutionResult
    def validate(self) -> bool
```

### IDependency
```python
class IDependency:
    """Interface for dependency management."""
    @property
    def source_task_id(self) -> str
    @property
    def target_task_id(self) -> str
    def is_satisfied(self, completed_tasks: List[str]) -> bool
```

---

*Structured workflows that orchestrate complex tasks across devices* 🌟
