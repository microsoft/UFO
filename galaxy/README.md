# UFO Galaxy Framework

The UFO Galaxy Framework is a comprehensive system for DAG-based task orchestration and intelligent device management. It provides a sophisticated platform for automating complex workflows through constellation-based task organization and AI-powered agents.

## 🌟 Overview

Galaxy transforms complex user requests into executable DAGs (Directed Acyclic Graphs) where each node represents a task and edges represent dependencies. The framework leverages AI agents to dynamically create, modify, and orchestrate these task constellations across multiple devices.

### Key Features

- **🔗 DAG-based Task Orchestration**: Convert natural language requests into structured task workflows
- **🤖 AI-Powered Agents**: Intelligent agents that understand context and dynamically modify task graphs
- **📱 Multi-Device Coordination**: Seamlessly distribute tasks across different devices and platforms
- **⚡ Real-time Event System**: Observer pattern implementation for live monitoring and visualization
- **🎯 Context-Aware Execution**: Maintain execution context across complex multi-step workflows
- **📊 Modular Rich Visualization**: Beautiful DAG visualization with specialized display components using Rich
- **🔄 Dynamic Adaptation**: Runtime modification of task graphs based on execution results

## 🏗️ Architecture

```
Galaxy Framework
├── 🎭 Agents/                    # AI agents for constellation orchestration
│   ├── ConstellationAgent       # Main DAG orchestration agent (extends BasicAgent)
│   ├── Agent States             # State machine for agent workflow (START/CONTINUE/FINISH/FAIL)
│   └── Processors/              # Request and result processing with MCP tools
├── 🌟 Constellation/            # Core DAG management system
│   ├── TaskConstellation        # DAG container with state machine and validation
│   ├── TaskStar                 # Task nodes with device assignment and lifecycle
│   ├── TaskStarLine            # Dependency edges with conditional logic
│   ├── Editor/                  # Command pattern DAG editing with undo/redo
│   └── Orchestrator/           # Event-driven execution coordination and device management
├── 🎯 Session/                  # Session lifecycle and event-driven monitoring
│   ├── GalaxySession           # BaseSession extension with constellation support
│   └── Observers/              # Event-driven observers with visualization integration
├── 📡 Client/                   # Device management support component
│   ├── ConstellationClient     # Device registration and connection interface
│   ├── ConstellationDeviceManager # Core device management coordinator
│   ├── ConstellationConfig     # Configuration loading (JSON/YAML/CLI/env)
│   ├── Components/             # Modular components (registry, connections, heartbeat)
│   └── Orchestration/          # Client orchestration and event handling
├── ⚡ Core/                     # Foundational components
│   ├── Types                   # Type system: protocols, dataclasses, enums
│   ├── Interfaces              # Interface definitions following ISP
│   ├── DI Container            # Dependency injection with lifecycle management
│   └── Events                  # Observer pattern and event system
└── 🎨 Visualization/           # Modular Rich console DAG visualization
    ├── DAGVisualizer           # DAG topology and structure visualization
    ├── TaskDisplay             # Task-specific displays and formatting
    ├── ConstellationDisplay    # Constellation lifecycle event displays
    └── VisualizationChangeDetector # Change detection and comparison
```

## 🚀 Quick Start

### Basic Usage

```python
from galaxy import GalaxyClient, GalaxySession

# Initialize Galaxy client
client = GalaxyClient(
    session_name="my_workflow",
    use_mock_agent=False,  # Use real AI agent
    max_rounds=10
)

# Start interactive session
await client.start_interactive_session()

# Or execute a single request
result = await client.execute_request(
    "Create a data analysis pipeline with visualization"
)
```

### Command Line Interface

```bash
# Execute a single request
python -m ufo.galaxy --request "Create a data processing pipeline" --mock-agent

# Start interactive mode
python -m ufo.galaxy --interactive --mock-agent

# Custom session configuration
python -m ufo.galaxy --request "Task" --session-name "my_session" --max-rounds 5
```

### Programmatic DAG Creation

```python
from galaxy import TaskConstellation, TaskStar, TaskStarLine, TaskPriority, DeviceType

# Create a constellation with advanced features
constellation = TaskConstellation(
    name="Data Processing Pipeline",
    description="Comprehensive data processing with validation",
    enable_visualization=True
)

# Add tasks with device requirements and priorities
data_task = TaskStar(
    task_id="data_collection",
    name="Data Collection",
    description="Collect data from multiple sources",
    priority=TaskPriority.HIGH,
    device_type=DeviceType.WINDOWS,
    max_retries=3,
    timeout_seconds=300
)
constellation.add_task(data_task)

process_task = TaskStar(
    task_id="data_processing", 
    name="Data Processing",
    description="Process and transform collected data",
    priority=TaskPriority.MEDIUM,
    device_type=DeviceType.LINUX,
    estimated_duration=600
)
constellation.add_task(process_task)

# Add conditional dependency with metadata
dependency = TaskStarLine(
    from_task_id="data_collection",
    to_task_id="data_processing",
    dependency_type=DependencyType.SUCCESS_ONLY,
    metadata={"validation_required": True}
)
constellation.add_dependency(dependency)

# Validate and get metrics
is_valid, errors = constellation.validate()
metrics = constellation.get_metrics()
print(f"Tasks: {metrics['total_tasks']}, Dependencies: {metrics['total_dependencies']}")
```

## 📋 Workflow Process

The Galaxy Framework follows a sophisticated multi-stage workflow:

### 1. Request Processing
```
User Request → ConstellationAgent → Task DAG Generation
```
- Natural language request parsing
- Context analysis and requirement extraction
- Initial DAG structure creation

### 2. Constellation Creation
```
DAG Generation → TaskConstellation → Validation & Optimization
```
- Task breakdown and dependency analysis
- DAG validation (cycle detection, feasibility)
- Resource requirement analysis

### 3. Device Assignment
```
Constellation → DeviceManager → Task Distribution
```
- Device capability matching
- Load balancing and optimization
- Task assignment to appropriate devices

### 4. Execution Orchestration
```
Task Distribution → TaskOrchestrator → Parallel Execution
```
- Dependency-aware task scheduling
- Real-time progress monitoring
- Dynamic adaptation based on results

### 5. Result Integration
```
Task Results → ConstellationAgent → DAG Updates
```
- Result analysis and validation
- Dynamic DAG modification if needed
- Success/failure propagation

## 🎯 Core Components

### ConstellationAgent
The brain of the Galaxy Framework that:
- Processes user requests using BasicAgent framework and LLM integration
- Generates task DAGs through constellation creation via `process_creation()`
- Updates constellations based on task results via `process_editing()`
- Maintains state through ConstellationAgentStatus state machine
- Publishes constellation modification events to the event bus
- Implements IRequestProcessor and IResultProcessor interfaces

### TaskConstellation
The core DAG container implementing IConstellation interface that:
- Manages task nodes (TaskStar) and dependency edges (TaskStarLine) with comprehensive validation
- Provides DAG operations with cycle detection, topological sorting, and structural validation
- Tracks constellation state through state machine (CREATED/READY/EXECUTING/COMPLETED/FAILED)
- Supports complex dependency types (UNCONDITIONAL, CONDITIONAL, SUCCESS_ONLY) with metadata
- Enables JSON serialization/deserialization for persistence and data interchange
- Integrates with event system for real-time monitoring and change propagation
- Works with ConstellationEditor for interactive modification using command pattern with undo/redo
- Provides comprehensive statistics, metrics, and progress tracking for monitoring

### GalaxySession
The session orchestrator that extends BaseSession framework to:
- Manages constellation-based workflow execution through round-based processing
- Coordinates ConstellationAgent state machine and TaskConstellationOrchestrator
- Provides event-driven monitoring through specialized observers that integrate with visualization components
- Handles session lifecycle, state persistence, and error recovery with constellation awareness
- Integrates with UFO BaseSession for round management, context handling, and evaluation framework

### Visualization System
Modular visualization components that provide beautiful terminal displays:
- **DAGVisualizer**: Specialized for DAG topology and structure visualization with Rich console output
- **TaskDisplay**: Task-specific displays including status grids, detail tables, and execution flow
- **ConstellationDisplay**: Constellation lifecycle event displays with professional notifications
- **VisualizationChangeDetector**: Intelligent change detection and visual comparison of constellation modifications
- **Session Integration**: Observers use visualization components for real-time monitoring and event displays

### Event System
Real-time communication system that:
- Propagates task and constellation events via EventBus
- Enables live monitoring and visualization through observers
- Supports observer pattern for extensibility and decoupling
- Facilitates debugging, logging, and audit trails
- Provides typed event system for type safety

## 📚 Module Documentation

Each module contains detailed documentation and implementation guides:

- **[Agents](./agents/README.md)** - AI agents, state machines, and processing logic
- **[Constellation](./constellation/README.md)** - DAG management, task orchestration, and editing
- **[Session](./session/README.md)** - BaseSession extension, event-driven observers, and constellation lifecycle management
- **[Client](./client/README.md)** - Device management support component for WebSocket connections and basic task execution
- **[Core](./core/README.md)** - Type system, interfaces, dependency injection, and event system
- **[Visualization](./visualization/README.md)** - Modular Rich console DAG visualization with specialized display components

## 🔧 Configuration

Galaxy supports extensive configuration through multiple mechanisms:

### CLI Configuration
```bash
# Session settings
--session-name "custom_session"    # Custom session name
--max-rounds 15                    # Maximum execution rounds
--task-name "my_task"             # Task identifier

# Agent settings
--mock-agent                      # Use mock agent for testing
--log-level DEBUG                 # Enable verbose logging

# Output settings
--output-dir "./custom_logs"      # Custom output directory
```

### Programmatic Configuration
```python
# Session configuration
session_config = {
    "max_rounds": 10,
    "timeout_seconds": 300,
    "enable_visualization": True,
    "observer_config": {
        "enable_rich_output": True,
        "enable_change_detection": True,
        "visualization_components": ["DAGVisualizer", "TaskDisplay", "ConstellationDisplay"]
    }
}

# Agent configuration
agent_config = {
    "llm_model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000
}
```

## 📊 Monitoring and Visualization

The framework provides comprehensive monitoring capabilities through modular visualization components:

### Modular Console Visualization  
- **DAG Topology Display**: Hierarchical tree visualization of task dependencies using DAGVisualizer
- **Task Status Tracking**: Color-coded status indicators and grids using TaskDisplay
- **Constellation Events**: Professional lifecycle notifications using ConstellationDisplay  
- **Change Detection**: Intelligent tracking and visual comparison using VisualizationChangeDetector
- **Rich Console Output**: Beautiful terminal formatting with specialized components

### Session Observer Integration
- **Real-time Monitoring**: Observers integrate with visualization components for live updates
- **Event-driven Displays**: Professional notifications for constellation lifecycle events
- **Progress Tracking**: Visual representation of task execution and constellation changes
- **Modular Architecture**: Mix and match visualization components based on specific needs

### Event Streaming
- **Task Events**: Creation, update, completion, and failure events
- **Constellation Events**: DAG structure changes and modifications
- **Session Events**: Round progression and lifecycle management
- **Observer Events**: Custom event handling and processing

### Metrics and Analytics
- **Execution Statistics**: Task completion times and success rates
- **Resource Utilization**: Device and resource usage tracking
- **Performance Metrics**: Throughput and latency measurements
- **Error Analysis**: Failure patterns and debugging information

## 🧪 Testing and Development

Galaxy includes comprehensive testing infrastructure:

### Mock Components
```python
from tests.galaxy.mocks import MockConstellationAgent, MockTaskConstellationOrchestrator

# Use mock agent for testing
client = GalaxyClient(use_mock_agent=True)

# Mock orchestrator for unit tests
orchestrator = MockTaskConstellationOrchestrator()
```

### Test Scenarios
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow validation
- **Performance Tests**: Load and stress testing
- **Regression Tests**: Automated testing for stability

### Development Tools
```bash
# Run all tests
python -m pytest tests/galaxy/

# Run specific test modules
python -m pytest tests/galaxy/session/

# Run with coverage
python -m pytest --cov=ufo.galaxy tests/galaxy/
```

## 🏛️ Design Principles

Galaxy follows established software engineering principles:

### SOLID Principles
- **Single Responsibility**: Each class has a focused, well-defined purpose
- **Open/Closed**: Extensible through interfaces without modifying existing code
- **Liskov Substitution**: Interchangeable implementations through abstract interfaces
- **Interface Segregation**: Focused, minimal interfaces for specific concerns
- **Dependency Inversion**: Depend on abstractions, not concrete implementations

### Architectural Patterns
- **Observer Pattern**: Event-driven architecture for loose coupling
- **State Machine**: Well-defined agent states and transitions
- **Command Pattern**: Encapsulated request processing
- **Factory Pattern**: Flexible component creation and configuration
- **Adapter Pattern**: Device and client abstraction

### Best Practices
- **Type Safety**: Comprehensive type hints and validation
- **Error Handling**: Robust error recovery and reporting
- **Logging**: Structured logging for debugging and monitoring
- **Documentation**: Comprehensive docstrings and examples
- **Testing**: High test coverage and quality assurance

## 🚀 Getting Started

### Installation
```bash
# Clone the UFO repository
git clone <repository-url>
cd UFO2

# Install dependencies
pip install -r requirements.txt
```

### First Steps
1. **Start with Mock Agent**: Use `--mock-agent` for initial exploration
2. **Try Interactive Mode**: Use `--interactive` for hands-on experience
3. **Review Examples**: Check the examples in each module's README
4. **Read Documentation**: Explore module-specific documentation
5. **Run Tests**: Validate your setup with the test suite

### Example Workflows
```bash
# Data processing pipeline
python -m ufo.galaxy --request "Create a data processing pipeline with validation and transformation" --mock-agent

# Machine learning workflow
python -m ufo.galaxy --request "Build a machine learning workflow with training and evaluation" --mock-agent

# Web scraping system
python -m ufo.galaxy --request "Design a web scraping system with data validation" --mock-agent
```

## 📄 License

Copyright (c) Microsoft Corporation. Licensed under the MIT License.

---

*Galaxy Framework - Transforming natural language into intelligent task orchestration* 🌟
