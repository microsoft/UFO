# Galaxy Session Module

The Session module manages the complete lifecycle of Galaxy workflows, providing session orchestration, round-based execution, and event-driven monitoring for DAG-based task workflows.

## 🎯 Overview

Galaxy sessions represent complete workflow execution contexts, managing the interaction between ConstellationAgent, TaskConstellationOrchestrator, and event-driven observers. Sessions extend BaseSession to provide structured round-based execution with state persistence and comprehensive monitoring capabilities.

## 🏗️ Architecture

```
ufo/galaxy/session/
├── __init__.py                     # Module exports and observer imports
├── galaxy_session.py              # Main session and round implementation
└── observers/                     # Event-driven observer implementations
    ├── __init__.py                # Observer exports
    ├── base_observer.py           # ConstellationProgressObserver and SessionMetricsObserver
    ├── dag_visualization_observer.py  # Main DAGVisualizationObserver
    ├── task_visualization_handler.py  # Task-specific event handling (legacy)
    └── constellation_visualization_handler.py  # Constellation-specific event handling (legacy)
```

**Key Components:**
- **GalaxySession**: Extends BaseSession for constellation-based workflow execution
- **GalaxyRound**: Individual execution rounds within sessions extending BaseRound
- **ConstellationProgressObserver**: Handles task completion events and agent state coordination
- **SessionMetricsObserver**: Collects session performance metrics and statistics
- **DAGVisualizationObserver**: Provides real-time constellation visualization using modular visualization components

## 🎪 Core Components

### GalaxySession

The primary session orchestrator that extends BaseSession to manage constellation-based workflow lifecycles with event-driven monitoring.

#### Key Responsibilities
- **Session Lifecycle**: Initialize, execute, and finalize workflow sessions using BaseSession framework
- **Agent Coordination**: Manage ConstellationAgent state machine execution and request processing
- **Round Management**: Execute GalaxyRound instances with constellation support and state tracking
- **Observer Orchestration**: Coordinate event-driven observers through event bus integration
- **State Management**: Maintain session state and round history with persistence support
- **Error Handling**: Robust error recovery with constellation-aware error detection

#### Core Architecture
```python
class GalaxySession(BaseSession):
    def __init__(
        self,
        task: str,
        should_evaluate: bool,
        id: str,
        client: Optional[ConstellationClient] = None,
        initial_request: str = ""
    ):
        # Extends BaseSession with constellation support
        self._client = client
        self._orchestrator = TaskConstellationOrchestrator(
            device_manager=client.device_manager, enable_logging=True
        )
        self._agent = ConstellationAgent(orchestrator=self._orchestrator)
        
        # Event system setup
        self._event_bus = get_event_bus()
        self._observers = []
        self._setup_observers()
```

#### Usage Example
```python
from galaxy.session import GalaxySession
from galaxy.client.constellation_client import ConstellationClient

# Initialize session with client support
client = ConstellationClient()
session = GalaxySession(
    task="data_analysis_workflow",
    should_evaluate=True,
    id="session_001",
    client=client,
    initial_request="Create a comprehensive data analysis pipeline"
)

# Execute workflow using BaseSession framework
await session.run()

# Access session results
print(f"Session completed: {session.is_finished()}")
print(f"Current constellation: {session.current_constellation}")
print(f"Session results: {session.session_results}")
```

#### Key Properties and Methods
```python
class GalaxySession:
    # Properties
    @property
    def current_constellation(self) -> Optional[TaskConstellation]
    @property 
    def agent(self) -> ConstellationAgent
    @property
    def orchestrator(self) -> TaskConstellationOrchestrator
    @property
    def session_results(self) -> Dict[str, Any]
    
    # Core Methods (extends BaseSession)
    async def run(self) -> None                              # Main execution using BaseSession
    def create_new_round(self) -> Optional[GalaxyRound]     # Create constellation-aware rounds
    def next_request(self) -> str                           # Get next request for round execution
    def is_finished(self) -> bool                           # Check completion with constellation state
    def is_error(self) -> bool                              # Check error state with constellation awareness
    
    # Session Management
    def set_agent(self, agent: ConstellationAgent) -> None
    async def force_finish(self, reason: str = "Manual termination") -> None
    def request_to_evaluate(self) -> str                    # For evaluation framework integration
```

### GalaxyRound

Individual execution rounds within a session that extend BaseRound to support constellation agent state machine execution.

#### Round Structure and Implementation
```python
class GalaxyRound(BaseRound):
    def __init__(
        self,
        request: str,
        agent: ConstellationAgent,
        context: Context,
        should_evaluate: bool,
        id: int,
    ):
        super().__init__(request, agent, context, should_evaluate, id)
        self._task_results: Dict[str, Any] = {}
        self._execution_start_time: Optional[float] = None
        self._agent = agent
```

#### Round Execution Logic
```python
async def run(self) -> None:
    """
    Run the round using agent state machine.
    
    Executes the agent state machine until completion,
    managing state transitions and error handling.
    """
    try:
        # Set up agent with current request
        self._agent.current_request = self._request
        
        # Initialize agent in START state
        from ..agents.constellation_agent_states import StartConstellationAgentState
        self._agent.set_state(StartConstellationAgentState())
        
        # Run agent state machine until completion
        while not self.is_finished():
            # Execute current state
            await self._agent.handle(self._context)
            
            # Transition to next state
            next_state = self._agent.state.next_state(self._agent)
            self._agent.set_state(next_state)
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.01)
            
    except Exception as e:
        self.logger.error(f"Error in GalaxyRound execution: {e}")
```

#### Round State Management
```python
def is_finished(self) -> bool:
    """
    Verify if the round is finished by checking:
    - Round end state
    - Maximum step limit from configuration
    """
    if (
        self.state.is_round_end()
        or self.context.get(ContextNames.SESSION_STEP) >= configs["MAX_STEP"]
    ):
        return True
    return False
```

#### Round Properties
```python
@property
def constellation(self) -> Optional[TaskConstellation]:
    """Get the current constellation from the round."""
    return self._constellation

@property  
def task_results(self) -> Dict[str, Any]:
    """Get all task results collected during round execution."""
    return self._task_results
```

#### Usage Example
```python
from galaxy.session.galaxy_session import GalaxyRound
from galaxy.agents.constellation_agent import ConstellationAgent
from ufo.module.context import Context

# Create a new round (typically done by GalaxySession)
agent = ConstellationAgent(orchestrator=orchestrator)
context = Context()

round = GalaxyRound(
    request="Process customer data and generate insights",
    agent=agent,
    context=context,
    should_evaluate=True,
    id=1
)

# Execute the round (handles agent state machine)
await round.run()

# Check round completion
if round.is_finished():
    print(f"Round completed")
    print(f"Task results: {round.task_results}")
    if round.constellation:
        print(f"Generated constellation: {round.constellation.name}")
```

## 👁️ Observer System

The session module uses a modular event-driven observer system with specialized components for different aspects of monitoring and visualization.

### Modular Observer Architecture

The observer system is organized into specialized modules with clear separation of concerns:

- **`base_observer.py`**: Core observers for progress tracking and metrics collection
- **`dag_visualization_observer.py`**: Main visualization coordinator that delegates to Galaxy visualization module
- **Legacy handlers** (deprecated): Task and constellation handlers have been refactored into the dedicated visualization module

The visualization functionality has been moved to the dedicated [`ufo.galaxy.visualization`](../visualization/README.md) module for better modularity and separation of concerns.

### ConstellationProgressObserver

Handles constellation progress updates and coordinates task completion events with agent state machine. Located in `base_observer.py`.

#### Core Functionality
```python
class ConstellationProgressObserver(IEventObserver):
    def __init__(self, agent: ConstellationAgent, context: Context):
        """
        Initialize ConstellationProgressObserver.
        
        :param agent: ConstellationAgent instance for task coordination
        :param context: Context object for the session
        """
        self.agent = agent
        self.context = context
        self.task_results: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)

    async def on_event(self, event: Event) -> None:
        """
        Handle constellation-related events.
        
        :param event: Event instance to handle (TaskEvent or ConstellationEvent)
        """
        if isinstance(event, TaskEvent):
            await self._handle_task_event(event)
        elif isinstance(event, ConstellationEvent):
            await self._handle_constellation_event(event)
```

### SessionMetricsObserver

Collects session performance metrics and execution statistics from event streams. Located in `base_observer.py`.

#### Metrics Collection
```python
class SessionMetricsObserver(IEventObserver):
    def __init__(self, session_id: str, logger: Optional[logging.Logger] = None):
        self.metrics: Dict[str, Any] = {
            "session_id": session_id,
            "task_count": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_execution_time": 0.0,
            "task_timings": {},
        }
        self.logger = logger or logging.getLogger(__name__)

    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return self.metrics.copy()
```

### DAGVisualizationObserver

Provides real-time constellation visualization by integrating with the dedicated Galaxy visualization module. Located in `dag_visualization_observer.py`.

#### Integration with Visualization Module
```python
class DAGVisualizationObserver(IEventObserver):
    def __init__(self, enable_visualization: bool = True, console=None):
        self.enable_visualization = enable_visualization
        self._constellations: Dict[str, TaskConstellation] = {}
        
        # Initialize visualization components from dedicated module
        from galaxy.visualization import (
            TaskDisplay, ConstellationDisplay, VisualizationChangeDetector
        )
        
        self._task_display = TaskDisplay(console)
        self._constellation_display = ConstellationDisplay(console)
        self._change_detector = VisualizationChangeDetector()

    async def on_event(self, event: Event) -> None:
        """Handle visualization events using dedicated visualization components."""
        if not self.enable_visualization:
            return

        try:
            if isinstance(event, ConstellationEvent):
                await self._handle_constellation_event(event)
            elif isinstance(event, TaskEvent):
                await self._handle_task_event(event)
        except Exception as e:
            self.logger.debug(f"Visualization error: {e}")

    async def _handle_constellation_event(self, event: ConstellationEvent) -> None:
        """Handle constellation events using ConstellationDisplay from visualization module."""
        constellation = event.constellation
        
        if event.event_type == "constellation_started":
            self._constellation_display.display_constellation_started(constellation)
            self._change_detector.capture_constellation_state(constellation, "started")
            
        elif event.event_type == "constellation_completed":
            self._constellation_display.display_constellation_completed(
                constellation, 
                execution_time=event.execution_time
            )
            
        elif event.event_type == "constellation_modified":
            changes = self._change_detector.detect_changes(constellation, "started")
            if changes:
                self._constellation_display.display_constellation_modified(
                    constellation, changes
                )

    async def _handle_task_event(self, event: TaskEvent) -> None:
        """Handle task events using TaskDisplay from visualization module."""
        constellation = self._constellations.get(event.constellation_id)
        if not constellation:
            return
            
        if event.event_type == "task_completed":
            # Update execution flow display
            self._task_display.display_execution_flow(constellation)
            
        elif event.event_type == "task_failed":
            # Show updated task status
            self._task_display.display_task_details_table(constellation)
```

#### Key Features
- **Visualization Module Integration**: Delegates all visualization to the dedicated `ufo.galaxy.visualization` module
- **Event Coordination**: Routes constellation and task events to appropriate visualization components
- **Change Detection**: Uses `VisualizationChangeDetector` for intelligent change tracking
- **Modular Display**: Leverages `TaskDisplay` and `ConstellationDisplay` for specialized visualizations
- **Error Handling**: Graceful degradation when visualization components are unavailable

### Legacy Visualization Handlers (Deprecated)

The following handlers have been refactored and moved to the dedicated [`ufo.galaxy.visualization`](../visualization/README.md) module:

#### TaskVisualizationHandler (Moved to ufo.galaxy.visualization.TaskDisplay)
Previously located in `task_visualization_handler.py`, this functionality is now provided by the `TaskDisplay` class in the visualization module.

```python
# Old usage (deprecated)
from galaxy.session.observers.task_visualization_handler import TaskVisualizationHandler

# New usage (recommended)
from galaxy.visualization import TaskDisplay
task_display = TaskDisplay()
task_display.display_execution_flow(constellation)
```

#### ConstellationVisualizationHandler (Moved to ufo.galaxy.visualization.ConstellationDisplay)  
Previously located in `constellation_visualization_handler.py`, this functionality is now provided by the `ConstellationDisplay` class in the visualization module.

```python
# Old usage (deprecated)
from galaxy.session.observers.constellation_visualization_handler import ConstellationVisualizationHandler

# New usage (recommended)  
from galaxy.visualization import ConstellationDisplay
constellation_display = ConstellationDisplay()
constellation_display.display_constellation_started(constellation)
```

#### VisualizationChangeDetector (Moved to ufo.galaxy.visualization.VisualizationChangeDetector)
Previously located in `visualization_change_detector.py`, this functionality is now provided by the `VisualizationChangeDetector` class in the visualization module.

```python
# Old usage (deprecated)
from galaxy.session.observers.visualization_change_detector import VisualizationChangeDetector

# New usage (recommended)
from galaxy.visualization import VisualizationChangeDetector
change_detector = VisualizationChangeDetector()
changes = change_detector.detect_changes(constellation, "baseline")
```

### Migration Benefits

The refactoring provides several benefits:

- **Modular Architecture**: Visualization logic is centralized in a dedicated module
- **Reusability**: Visualization components can be used outside of session observers
- **Testability**: Each visualization component can be tested independently
- **Maintainability**: Clear separation of concerns between session management and visualization
- **Extensibility**: Easy to add new visualization components without modifying session code

### Observer Usage

#### Basic Observer Setup
```python
from galaxy.session import (
    ConstellationProgressObserver,
    SessionMetricsObserver,
    DAGVisualizationObserver
)

# Create observers
progress_observer = ConstellationProgressObserver(agent=agent, context=context)
metrics_observer = SessionMetricsObserver(session_id="session_001")
dag_observer = DAGVisualizationObserver(enable_visualization=True)

# Automatic setup in GalaxySession
session._observers = [progress_observer, metrics_observer, dag_observer]
for observer in session._observers:
    session._event_bus.subscribe(observer)
```

#### Advanced Observer Configuration
```python
from rich.console import Console

# Custom visualization observer with specific console
custom_console = Console(width=120, color_system="256")
dag_observer = DAGVisualizationObserver(
    enable_visualization=True,
    console=custom_console
)

# Access visualization components (from dedicated visualization module)
from galaxy.visualization import TaskDisplay, ConstellationDisplay, VisualizationChangeDetector

task_display = TaskDisplay(console=custom_console)
constellation_display = ConstellationDisplay(console=custom_console)
change_detector = VisualizationChangeDetector()

# Manual constellation visualization
constellation_display.display_constellation_started(constellation)
task_display.display_execution_flow(constellation)

# Manual change detection
changes = change_detector.detect_changes(constellation, "baseline")
if changes:
    constellation_display.display_constellation_modified(constellation, changes)
    print(f"Detected changes: {changes['modification_type']}")
```

## 🔄 Session Lifecycle

### Session Integration with BaseSession Framework

GalaxySession extends the UFO BaseSession framework, leveraging its round-based execution model while adding constellation-specific functionality.

#### BaseSession Integration
```python
class GalaxySession(BaseSession):
    # Inherits core session lifecycle from BaseSession:
    # - Round-based execution management
    # - Context initialization and management  
    # - Step counting and limits
    # - Evaluation framework integration
    # - Command dispatcher attachment

    async def run(self) -> None:
        """
        Run the Galaxy session using BaseSession framework.
        Adds constellation tracking and performance metrics.
        """
        try:
            self._session_start_time = time.time()
            
            # Run base session logic with constellation support
            await super().run()  # Uses BaseSession round management
            
            # Calculate session metrics
            if self._session_start_time:
                total_time = time.time() - self._session_start_time
                self._session_results["total_execution_time"] = total_time

            # Final constellation status
            if self._current_constellation:
                self._session_results["final_constellation_stats"] = (
                    self._current_constellation.get_statistics()
                )
                self._session_results["status"] = self._agent.status

        except Exception as e:
            self.logger.error(f"Error in GalaxySession: {e}")
```

#### State Management Integration
```python
def is_error(self) -> bool:
    """
    Check if the session is in error state.
    
    Override base implementation to handle Galaxy-specific logic
    by checking constellation state and agent status.
    """
    # Check if current constellation failed
    if self._current_constellation:
        return self._current_constellation.state == ConstellationState.FAILED

    # Fall back to checking rounds using BaseSession logic
    if self.current_round is not None and self.current_round.state is not None:
        try:
            from ufo.agents.states.basic import AgentStatus
            return self.current_round.state.name() == AgentStatus.ERROR.value
        except (AttributeError, ImportError):
            pass

    return False

def is_finished(self) -> bool:
    """
    Check if the session is finished.
    
    Uses BaseSession configuration for limits and adds constellation logic.
    """
    # Check standard BaseSession completion conditions
    if (
        self._finish
        or self.step >= self._config.get("MAX_STEP", 100)
        or self.total_rounds >= self._config.get("MAX_ROUND", 10)
    ):
        return True

    return False
```

#### Context and Command Dispatcher Setup
```python
def _init_context(self) -> None:
    """
    Initialize the context using BaseSession framework.
    Adds MCP server manager and command dispatcher integration.
    """
    super()._init_context()

    mcp_server_manager = MCPServerManager()
    command_dispatcher = LocalCommandDispatcher(self, mcp_server_manager)
    self.context.attach_command_dispatcher(command_dispatcher)
```

### Round Creation and Management
```python
def create_new_round(self) -> Optional[GalaxyRound]:
    """
    Create a new GalaxyRound.
    
    Called by BaseSession framework during session execution.
    """
    request = self.next_request()
    if not request:
        return None

    round_id = len(self._rounds)

    galaxy_round = GalaxyRound(
        request=request,
        agent=self._agent,
        context=self._context,
        should_evaluate=self._should_evaluate,
        id=round_id,
    )

    self.add_round(round_id, galaxy_round)  # BaseSession method
    return galaxy_round

def next_request(self) -> str:
    """
    Get the next request for the session.
    
    For Galaxy sessions, typically processes one request per session.
    """
    # For now, only process one request per session
    if len(self._rounds) == 0:
        return self._initial_request or self.task
    return ""  # No more requests
```

### Evaluation Framework Integration
```python
def request_to_evaluate(self) -> str:
    """
    Get the request for evaluation.
    
    Integrates with UFO evaluation framework for session assessment.
    """
    return self._initial_request or self.task
```

## 📊 Session Configuration and Management

### Session Configuration via Constructor

Galaxy sessions are configured through constructor parameters that align with the actual implementation:

```python
def __init__(
    self,
    task: str,                                    # Task name/description
    should_evaluate: bool,                        # Whether to evaluate the session
    id: str,                                     # Session ID
    client: Optional[ConstellationClient] = None, # ConstellationClient for device management
    initial_request: str = "",                   # Initial user request
):
```

### Automatic Setup and Integration

Sessions automatically handle setup and integration with the Galaxy framework:

```python
class GalaxySession(BaseSession):
    def __init__(self, ...):
        # BaseSession initialization
        super().__init__(...)
        
        # Galaxy-specific setup
        self._client = client
        self._orchestrator = TaskConstellationOrchestrator(
            device_manager=client.device_manager, enable_logging=True
        )
        self._agent = ConstellationAgent(orchestrator=self._orchestrator)
        
        # Event system and observers
        self._event_bus = get_event_bus()
        self._observers = []
        self._setup_observers()  # Automatically sets up all observers
```

### Session Properties and State Access

```python
# Core session properties
@property
def current_constellation(self) -> Optional[TaskConstellation]:
    """Get current constellation from agent."""
    return self._agent.current_constellation

@property
def agent(self) -> ConstellationAgent:
    """Get the constellation agent."""
    return self._agent

@property
def orchestrator(self) -> TaskConstellationOrchestrator:
    """Get the task orchestrator."""
    return self._orchestrator

@property
def session_results(self) -> Dict[str, Any]:
    """Get session execution results and metrics."""
    return self._session_results
```

### Session Control Methods

```python
# Session control
async def force_finish(self, reason: str = "Manual termination") -> None:
    """Force finish the session with specified reason."""
    self.logger.info(f"Force finishing session: {reason}")
    self._finish = True
    self._agent.status = "FINISH"
    self._session_results["finish_reason"] = reason

def set_agent(self, agent: ConstellationAgent) -> None:
    """Set the constellation agent."""
    self._agent = agent
```

## 🎮 Session Usage Patterns

### Basic Session Execution
```python
from galaxy.session import GalaxySession
from galaxy.client.constellation_client import ConstellationClient

# Create client and session
client = ConstellationClient()
session = GalaxySession(
    task="data_processing_pipeline",
    should_evaluate=False,
    id="session_001", 
    client=client,
    initial_request="Create a data processing pipeline with validation"
)

# Execute session (uses BaseSession framework)
await session.run()

# Check results
print(f"Session finished: {session.is_finished()}")
print(f"Session error: {session.is_error()}")
print(f"Current constellation: {session.current_constellation}")
print(f"Session results: {session.session_results}")
```

### Session with Custom Agent
```python
from galaxy.agents.constellation_agent import ConstellationAgent

# Create custom agent configuration
custom_agent = ConstellationAgent(
    orchestrator=custom_orchestrator,
    enable_mock_mode=False
)

# Set custom agent
session.set_agent(custom_agent)

# Execute with custom agent
await session.run()
```

### Session Results and Metrics
```python
# Access session results after execution
results = session.session_results

# Check execution metrics
if "total_execution_time" in results:
    print(f"Total execution time: {results['total_execution_time']:.2f}s")

if "final_constellation_stats" in results:
    stats = results["final_constellation_stats"]
    print(f"Final constellation statistics: {stats}")

# Agent status
print(f"Agent final status: {results.get('status', 'Unknown')}")

# Check for forced finish
if "finish_reason" in results:
    print(f"Session finished due to: {results['finish_reason']}")
```

### Error Handling and Recovery
```python
try:
    await session.run()
    
    if session.is_error():
        print("Session completed with errors")
        
        # Check constellation state for specific error info
        if session.current_constellation:
            constellation_state = session.current_constellation.state
            print(f"Constellation state: {constellation_state}")
            
    elif session.is_finished():
        print("Session completed successfully")
        
except Exception as e:
    print(f"Session execution failed: {e}")
    
    # Force finish with error reason
    await session.force_finish(f"Exception: {str(e)}")
```

## 🧪 Testing and Integration

### Session Testing with BaseSession Framework

Galaxy sessions integrate with the UFO testing framework through BaseSession inheritance:

```python
from galaxy.session import GalaxySession
from galaxy.client.constellation_client import ConstellationClient

# Create test session
def create_test_session():
    client = ConstellationClient()
    return GalaxySession(
        task="test_workflow",
        should_evaluate=True,  # Enable for testing
        id="test_session_001",
        client=client,
        initial_request="Test constellation creation and execution"
    )

# Test session execution
async def test_session_execution():
    session = create_test_session()
    
    await session.run()
    
    # Verify session completion
    assert session.is_finished()
    assert not session.is_error()
    
    # Check constellation creation
    assert session.current_constellation is not None
    assert session.current_constellation.name
    
    # Verify session results
    results = session.session_results
    assert "total_execution_time" in results
    assert results["status"]
```

### Observer Testing

```python
from galaxy.session.observers import ConstellationProgressObserver, SessionMetricsObserver

async def test_observer_functionality():
    # Test progress observer
    progress_observer = ConstellationProgressObserver(agent=mock_agent, context=mock_context)
    
    # Test event handling
    task_event = TaskEvent(task_id="test_task", status="completed")
    await progress_observer.on_event(task_event)
    
    # Verify task results storage
    assert "test_task" in progress_observer.task_results
    
    # Test metrics observer
    metrics_observer = SessionMetricsObserver(session_id="test_session")
    await metrics_observer.on_event(task_event)
    
    # Verify metrics collection
    metrics = metrics_observer.get_metrics()
    assert metrics["task_count"] > 0

async def test_visualization_observer():
    """Test DAGVisualizationObserver integration with visualization module."""
    from galaxy.session.observers import DAGVisualizationObserver
    from rich.console import Console
    from io import StringIO
    
    # Create observer with string buffer for testing
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    
    dag_observer = DAGVisualizationObserver(
        enable_visualization=True,
        console=console
    )
    
    # Test constellation event handling
    constellation_event = ConstellationEvent(
        event_type="constellation_started",
        constellation=mock_constellation
    )
    await dag_observer.on_event(constellation_event)
    
    # Verify visualization output was generated
    output_text = output.getvalue()
    assert "Constellation Started" in output_text or len(output_text) > 0
    
    # Test task event handling
    task_event = TaskEvent(
        event_type="task_completed",
        task_id="test_task",
        constellation_id=mock_constellation.constellation_id
    )
    await dag_observer.on_event(task_event)
```

### Mock Session Testing

```python
# Mock session for unit testing
class MockGalaxySession(GalaxySession):
    def __init__(self, *args, **kwargs):
        # Use mock components
        kwargs['client'] = MockConstellationClient()
        super().__init__(*args, **kwargs)
        
        # Replace with mock agent
        from tests.galaxy.mocks import MockConstellationAgent
        self._agent = MockConstellationAgent()

# Test with mock session
async def test_with_mock():
    mock_session = MockGalaxySession(
        task="mock_test",
        should_evaluate=False,
        id="mock_001"
    )
    
    await mock_session.run()
    
    # Predictable mock behavior
    assert mock_session.is_finished()
    assert mock_session.current_constellation
```

## 🚀 Getting Started

### Basic Session Setup
```python
from galaxy.session import GalaxySession
from galaxy.client.constellation_client import ConstellationClient

# 1. Create constellation client
client = ConstellationClient()

# 2. Initialize session
session = GalaxySession(
    task="my_first_workflow",
    should_evaluate=False,
    id="getting_started_001",
    client=client,
    initial_request="Create a simple data processing workflow"
)

# 3. Execute session
await session.run()

# 4. Check results
if session.is_finished() and not session.is_error():
    print("✅ Session completed successfully!")
    print(f"Constellation: {session.current_constellation.name}")
    print(f"Results: {session.session_results}")
else:
    print("❌ Session failed or incomplete")
```

### Advanced Session with Custom Configuration
```python
# Custom agent with specific configuration
from galaxy.agents.constellation_agent import ConstellationAgent
from galaxy.constellation import TaskConstellationOrchestrator

# Create custom orchestrator
orchestrator = TaskConstellationOrchestrator(
    device_manager=client.device_manager,
    enable_logging=True
)

# Create custom agent
agent = ConstellationAgent(
    orchestrator=orchestrator,
    enable_mock_mode=False  # Use real LLM
)

# Create session with custom agent
session = GalaxySession(
    task="advanced_workflow",
    should_evaluate=True,
    id="advanced_001",
    client=client,
    initial_request="Build a complex multi-device automation workflow"
)

# Set custom agent
session.set_agent(agent)

# Execute with monitoring
await session.run()

# Access detailed results
results = session.session_results
constellation = session.current_constellation

print(f"Execution time: {results.get('total_execution_time', 0):.2f}s")
print(f"Constellation stats: {results.get('final_constellation_stats', {})}")
print(f"Agent status: {results.get('status', 'Unknown')}")
```

## 🔗 Integration with Galaxy Framework

The session module serves as the orchestrator for all Galaxy components:

- **[Agents](../agents/README.md)**: ConstellationAgent state machine execution and coordination
- **[Constellation](../constellation/README.md)**: TaskConstellation lifecycle management and orchestration
- **[Core](../core/README.md)**: Event system integration and observer pattern implementation
- **[Client](../client/README.md)**: ConstellationClient device management and coordination  
- **[Visualization](../visualization/README.md)**: Real-time DAG visualization through DAGVisualizationObserver

### Session in Galaxy Ecosystem
```python
# Session coordinates all Galaxy components:

# 1. Agent Management
session._agent = ConstellationAgent(orchestrator=orchestrator)  # Agent coordination

# 2. Orchestration  
session._orchestrator = TaskConstellationOrchestrator(...)     # Task execution

# 3. Device Management
session._client = ConstellationClient()                        # Device coordination

# 4. Event System
session._event_bus = get_event_bus()                           # Event coordination

# 5. Observers
session._observers = [progress, metrics, visualization]        # Monitoring and visualization
```

---

*Orchestrating complete constellation workflows with BaseSession integration and event-driven monitoring* 🎯
