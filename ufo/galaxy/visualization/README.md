# Galaxy Visualization Module

The Visualization module provides comprehensive DAG visualization capabilities for the Galaxy Framework using rich console output. It specializes in displaying TaskConstellation structures, execution progress, and task relationships in beautiful terminal-based interfaces.

## 🎨 Overview

Galaxy visualization transforms complex DAG workflows into readable, informative console displays using the Rich library. It provides detailed topology visualization, task status monitoring, dependency tracking, and execution flow analysis through beautifully formatted terminal output.

### Key Features
- **DAG Topology Visualization**: Tree-based display of task hierarchies and dependencies
- **Rich Console Output**: Beautiful terminal rendering with colors, tables, and panels
- **Task Status Tracking**: Real-time status indicators with icons and color coding
- **Dependency Analysis**: Visual representation of task relationships and satisfaction status
- **Execution Flow Monitoring**: Display of ready, running, completed, and failed tasks
- **Statistics Panels**: Comprehensive task and constellation metrics

## 🏗️ Architecture

```
ufo/galaxy/visualization/
├── __init__.py                     # Module exports
└── dag_visualizer.py              # Complete DAG visualization implementation
```

### Simple and Focused Design
The visualization module follows a single-responsibility principle with one comprehensive class that handles all DAG visualization needs through the Rich library.

## 🌟 Core Component

### DAGVisualizer

The main visualization class that provides comprehensive DAG visualization capabilities using Rich console output.

#### Key Features
- **Constellation Overview**: Complete constellation information with statistics
- **DAG Topology Display**: Hierarchical tree visualization of task dependencies
- **Task Details Table**: Comprehensive task information in formatted tables
- **Dependency Summary**: Visual representation of all dependency relationships
- **Execution Flow**: Real-time display of task execution states
- **Rich Formatting**: Beautiful colors, icons, and styling throughout

#### Usage Examples

**Basic Constellation Overview**
```python
from ufo.galaxy.visualization import DAGVisualizer
from ufo.galaxy.constellation import TaskConstellation

# Create visualizer
visualizer = DAGVisualizer()

# Display complete constellation overview
visualizer.display_constellation_overview(
    constellation, 
    title="My Data Pipeline"
)
```

**Specific Visualization Modes**
```python
# Display just the DAG topology
visualizer.display_dag_topology(constellation)

# Show detailed task information
visualizer.display_task_details(constellation)

# Display dependency relationships
visualizer.display_dependency_summary(constellation)

# Show execution flow and ready tasks
visualizer.display_execution_flow(constellation)
```

**Convenience Functions**
```python
from ufo.galaxy.visualization import (
    display_constellation_creation,
    display_constellation_update,
    display_execution_progress,
    visualize_dag
)

# Display when constellation is first created
display_constellation_creation(constellation)

# Display after constellation updates
display_constellation_update(constellation, "Added new data validation task")

# Display execution progress
display_execution_progress(constellation)

# Quick visualization with different modes
visualize_dag(constellation, mode="overview")    # Full overview
visualize_dag(constellation, mode="topology")    # Just topology
visualize_dag(constellation, mode="details")     # Just task details
visualize_dag(constellation, mode="execution")   # Just execution flow
```

#### Core Methods
```python
class DAGVisualizer:
    def __init__(self, console: Optional[Console] = None)
    
    # Main visualization methods
    def display_constellation_overview(self, constellation: TaskConstellation, title: str = "Task Constellation Overview") -> None
    def display_dag_topology(self, constellation: TaskConstellation) -> None
    def display_task_details(self, constellation: TaskConstellation) -> None
    def display_dependency_summary(self, constellation: TaskConstellation) -> None
    def display_execution_flow(self, constellation: TaskConstellation) -> None
    
    # Private helper methods for formatting and layout
    def _create_info_panel(self, constellation: TaskConstellation) -> Panel
    def _create_stats_panel(self, constellation: TaskConstellation) -> Panel
    def _build_topology_layers(self, constellation: TaskConstellation) -> List[List[TaskStar]]
    def _format_task_for_tree(self, task: TaskStar, compact: bool = False) -> str
    def _get_status_text(self, status: TaskStatus) -> str
    def _get_status_icon(self, status: TaskStatus) -> str
```

## 🎯 Visualization Features

### Rich Console Integration

The visualization module leverages the Rich library to provide beautiful terminal output with:

#### Visual Elements
- **Status Icons**: Intuitive icons for task states (⭕ pending, 🔵 running, ✅ completed, ❌ failed)
- **Color Coding**: Consistent color scheme for status, priority, and state indicators
- **Formatted Tables**: Well-structured tables with proper alignment and borders
- **Tree Structures**: Hierarchical tree displays for DAG topology
- **Information Panels**: Organized panels for constellation info and statistics
- **Progress Indicators**: Visual representation of execution progress

#### Status Mapping
```python
# Status colors and icons used throughout the visualization
status_colors = {
    TaskStatus.PENDING: "yellow",
    TaskStatus.WAITING_DEPENDENCY: "orange1", 
    TaskStatus.RUNNING: "blue",
    TaskStatus.COMPLETED: "green",
    TaskStatus.FAILED: "red",
    TaskStatus.CANCELLED: "dim"
}

status_icons = {
    TaskStatus.PENDING: "⭕",
    TaskStatus.WAITING_DEPENDENCY: "⏳",
    TaskStatus.RUNNING: "🔵", 
    TaskStatus.COMPLETED: "✅",
    TaskStatus.FAILED: "❌",
    TaskStatus.CANCELLED: "⭕"
}
```

#### Dependency Symbols
```python
# Visual symbols for different dependency types
dependency_symbols = {
    DependencyType.UNCONDITIONAL: "→",
    DependencyType.SUCCESS_ONLY: "⇒", 
    DependencyType.CONDITIONAL: "⇝",
    DependencyType.COMPLETION_ONLY: "⟶"
}
```

### Topology Visualization

The DAG topology visualization uses intelligent layering to display task hierarchies:

#### Topology Algorithm
- **Topological Sorting**: Arranges tasks in dependency-respecting layers
- **Layer-based Display**: Groups tasks by their position in the dependency graph
- **Cycle Detection**: Identifies and reports potential cycles in the DAG
- **Tree Structure**: Uses Rich Tree widget for clear hierarchical display

#### Topology Features
```python
# Example topology display structure
🌌 Task Constellation
├── Layer 1
│   ├── 🟡 Data Collection Task (dc_001...)
│   │   └── Dependencies: none
│   └── 🟡 Configuration Setup (cfg_001...)
│       └── Dependencies: none
├── Layer 2  
│   ├── 🔵 Data Validation (dv_001...)
│   │   └── Dependencies:
│   │       └── ⬅️ 🟡 Data Collection Task
│   └── 🟡 Processing Prep (pp_001...)
│       └── Dependencies:
│           ├── ⬅️ 🟡 Data Collection Task
│           └── ⬅️ 🟡 Configuration Setup
└── Layer 3
    └── ✅ Final Report (fr_001...)
        └── Dependencies:
            └── ⬅️ 🔵 Data Validation
```

## 📊 Example Outputs

### Constellation Overview Display

When you call `display_constellation_overview()`, you get a comprehensive view:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 🆕 New Task Constellation Created ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────── 📊 Constellation Info ────────┐ ┌────────── 📈 Statistics ─────────────┐
│ ID: data_pipeline_001                 │ │ Total Tasks: 5                        │
│ Name: Data Processing Pipeline        │ │ Dependencies: 6                       │
│ State: READY                          │ │ ✅ Completed: 0                       │
│ Created: 2025-09-23 14:30:15         │ │ 🔵 Running: 0                         │
│                                       │ │ 🟡 Ready: 2                          │
│                                       │ │ ❌ Failed: 0                         │
└───────────────────────────────────────┘ └───────────────────────────────────────┘

📊 DAG Topology
🌌 Task Constellation
├── Layer 1
│   ├── ⭕ Data Collection (data_001...)
│   │   └── Dependencies: none
│   └── ⭕ Config Setup (conf_001...)
│       └── Dependencies: none
├── Layer 2
│   ├── ⏳ Data Validation (valid_001...)
│   │   └── Dependencies:
│   │       └── ⬅️ ⭕ Data Collection
│   └── ⏳ Processing Prep (prep_001...)
│       └── Dependencies:
│           ├── ⬅️ ⭕ Data Collection
│           └── ⬅️ ⭕ Config Setup
└── Layer 3
    └── ⏳ Final Report (report_001...)
        └── Dependencies:
            └── ⬅️ ⏳ Data Validation
```

### Task Details Table

```
📋 Task Details
┌──────────────┬───────────────────────────┬──────────────┬──────────┬───────────────┬──────────┐
│ ID           │ Name                      │    Status    │ Priority │ Dependencies  │ Progress │
├──────────────┼───────────────────────────┼──────────────┼──────────┼───────────────┼──────────┤
│ data_001...  │ Data Collection Task      │ ⭕ pending   │    5     │ none          │   N/A    │
│ conf_001...  │ Configuration Setup       │ ⭕ pending   │    8     │ none          │   N/A    │
│ valid_001... │ Data Validation Process   │ ⏳ waiting   │    6     │ 1 deps        │   N/A    │
│ prep_001...  │ Processing Preparation    │ ⏳ waiting   │    5     │ 2 deps        │   N/A    │
│ report_001...│ Final Report Generation   │ ⏳ waiting   │    3     │ 1 deps        │   N/A    │
└──────────────┴───────────────────────────┴──────────────┴──────────┴───────────────┴──────────┘
```

### Dependency Summary

```
🔗 Dependency Relationships

┌─────────── → Unconditional (4) ───────────┐
│ ⭕ Data Collection → ⏳ Data Validation ✅   │
│ ⭕ Data Collection → ⏳ Processing Prep ✅  │
│ ⭕ Config Setup → ⏳ Processing Prep ✅     │
│ ⏳ Data Validation → ⏳ Final Report ❌     │
└──────────────────────────────────────────────┘

┌─────────── ⇒ Success Only (2) ────────────┐
│ ⏳ Processing Prep → ⏳ Final Report ❌     │
│ ⏳ Data Validation → ⏳ Report Upload ❌   │
└──────────────────────────────────────────────┘
```

### Execution Flow Display

```
⚡ Execution Flow

┌─── Ready (2) ────┐ ┌─── Running (1) ───┐ ┌── Completed ──┐ ┌─── Failed (0) ────┐
│ 🟡 Data Collection │ │ 🔵 Config Setup   │ │ ✅ 3 tasks     │ │                   │
│ 🟡 Input Validation│ │                   │ │ completed      │ │                   │
└───────────────────┘ └───────────────────┘ └───────────────┘ └───────────────────┘
```

## 🔧 Customization and Configuration

### Console Customization

You can customize the visualization output by providing your own Rich Console:

```python
from rich.console import Console
from ufo.galaxy.visualization import DAGVisualizer

# Custom console with specific settings
custom_console = Console(
    width=100,           # Narrower output
    color_system="256",  # 256 color support
    force_terminal=True, # Force terminal mode
    legacy_windows=False # Modern Windows terminal support
)

# Use custom console with visualizer
visualizer = DAGVisualizer(console=custom_console)
visualizer.display_constellation_overview(constellation)
```

### Display Customization

The visualizer provides several helper methods for customizing appearance:

```python
class DAGVisualizer:
    # Status color mapping (can be customized)
    status_colors = {
        TaskStatus.PENDING: "yellow",
        TaskStatus.WAITING_DEPENDENCY: "orange1",
        TaskStatus.RUNNING: "blue", 
        TaskStatus.COMPLETED: "green",
        TaskStatus.FAILED: "red",
        TaskStatus.CANCELLED: "dim"
    }
    
    # Dependency symbols (can be customized)
    dependency_symbols = {
        DependencyType.UNCONDITIONAL: "→",
        DependencyType.SUCCESS_ONLY: "⇒",
        DependencyType.CONDITIONAL: "⇝", 
        DependencyType.COMPLETION_ONLY: "⟶"
    }
```

### Truncation and Formatting

The visualizer automatically handles text truncation and formatting:

- **Task Names**: Truncated to fit display width
- **Task IDs**: Shortened to first 6-8 characters with ellipsis
- **Long Lists**: Limited display with "... and N more" indicators
- **Priority Colors**: Color-coded based on priority values

## 🧪 Testing and Development

### Unit Testing

The visualization module includes comprehensive testing capabilities:

```python
import pytest
from rich.console import Console
from io import StringIO
from ufo.galaxy.visualization import DAGVisualizer, visualize_dag
from ufo.galaxy.constellation import TaskConstellation

def test_dag_visualizer_basic():
    """Test basic DAG visualizer functionality"""
    # Create test constellation
    constellation = TaskConstellation(name="Test Pipeline")
    
    # Add some test tasks
    task1 = constellation.create_task("task1", "First Task")
    task2 = constellation.create_task("task2", "Second Task")
    constellation.add_dependency("task1", "task2")
    
    # Create visualizer with string buffer
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    visualizer = DAGVisualizer(console=console)
    
    # Test visualization methods
    visualizer.display_constellation_overview(constellation)
    visualizer.display_dag_topology(constellation)
    visualizer.display_task_details(constellation)
    
    # Verify output was generated
    output_text = output.getvalue()
    assert "Task Constellation" in output_text
    assert "task1" in output_text
    assert "task2" in output_text

def test_convenience_functions():
    """Test convenience visualization functions"""
    constellation = TaskConstellation(name="Test")
    
    # Test all convenience functions don't crash
    display_constellation_creation(constellation)
    display_constellation_update(constellation, "Test update")
    display_execution_progress(constellation)
    
    # Test visualize_dag with different modes
    visualize_dag(constellation, mode="overview")
    visualize_dag(constellation, mode="topology")
    visualize_dag(constellation, mode="details")
    visualize_dag(constellation, mode="execution")
```

### Manual Testing

You can manually test the visualization with sample data:

```python
from ufo.galaxy.visualization import DAGVisualizer
from ufo.galaxy.constellation import TaskConstellation, TaskPriority
from ufo.galaxy.constellation.enums import TaskStatus

# Create a sample constellation for testing
constellation = TaskConstellation(name="Sample Data Pipeline")

# Add various tasks with different statuses
data_task = constellation.create_task(
    "data_collection", 
    "Data Collection Task",
    priority=TaskPriority.HIGH
)
data_task.status = TaskStatus.COMPLETED

validation_task = constellation.create_task(
    "data_validation",
    "Data Validation Process", 
    priority=TaskPriority.MEDIUM
)
validation_task.status = TaskStatus.RUNNING

process_task = constellation.create_task(
    "data_processing",
    "Data Processing and Transformation",
    priority=TaskPriority.LOW
)
process_task.status = TaskStatus.WAITING_DEPENDENCY

# Add dependencies
constellation.add_dependency("data_collection", "data_validation")
constellation.add_dependency("data_validation", "data_processing")

# Test visualization
visualizer = DAGVisualizer()
visualizer.display_constellation_overview(constellation, "Sample Pipeline Test")
```

## 🚀 Getting Started

### Quick Start

The simplest way to visualize a constellation:

```python
from ufo.galaxy.visualization import visualize_dag
from ufo.galaxy.constellation import TaskConstellation

# Create your constellation
constellation = TaskConstellation(name="My Workflow")
# ... add tasks and dependencies ...

# Quick visualization
visualize_dag(constellation)  # Shows full overview by default
```

### Step-by-Step Usage

```python
from ufo.galaxy.visualization import DAGVisualizer

# 1. Create visualizer
visualizer = DAGVisualizer()

# 2. Choose what to display based on your needs:

# Full overview (recommended for first look)
visualizer.display_constellation_overview(constellation)

# Just the DAG structure
visualizer.display_dag_topology(constellation)  

# Detailed task information
visualizer.display_task_details(constellation)

# Dependency relationships
visualizer.display_dependency_summary(constellation)

# Current execution state
visualizer.display_execution_flow(constellation)
```

### Integration with Galaxy Framework

The visualization module integrates seamlessly with the Galaxy Framework:

```python
# In Galaxy Session observers
from ufo.galaxy.visualization import display_constellation_update

class MySessionObserver:
    async def handle_constellation_update(self, constellation):
        # Automatically visualize constellation changes
        display_constellation_update(
            constellation, 
            "Constellation updated by agent"
        )

# In Galaxy agents for debugging
from ufo.galaxy.visualization import visualize_dag

class MyConstellationAgent:
    def process_constellation(self, constellation):
        # Debug visualization during development
        if self.debug_mode:
            visualize_dag(constellation, mode="topology")
```

## 🌟 Key Benefits

### Why Use Galaxy Visualization?

1. **Instant Understanding**: Quickly grasp complex DAG structures at a glance
2. **Debug Friendly**: Identify circular dependencies, bottlenecks, and issues
3. **Progress Tracking**: Monitor execution progress in real-time
4. **Beautiful Output**: Professional-quality terminal visualization with Rich
5. **Zero Configuration**: Works out of the box with sensible defaults
6. **Lightweight**: Single-file implementation with minimal dependencies

### Use Cases

- **Development**: Debug constellation creation and modification
- **Monitoring**: Track execution progress during workflow runs
- **Documentation**: Generate visual representations for documentation
- **Troubleshooting**: Identify dependency issues and execution problems
- **Demo and Presentation**: Show workflow structures in presentations

## 🔗 Integration with Galaxy Framework

The visualization module serves Galaxy Framework components:

- **[Constellation](../constellation/README.md)**: Visualizes TaskConstellation DAG structures and execution states
- **[Session](../session/README.md)**: Used by session observers to display progress and changes
- **[Agents](../agents/README.md)**: Provides debugging visualization for constellation creation and modification
- **[Core](../core/README.md)**: Uses core types and enums for consistent representation

### Framework Integration Points

The module integrates through:
- **Convenience Functions**: Easy-to-use functions for different lifecycle events
- **Rich Console**: Professional terminal output that fits Galaxy's user experience
- **Type Compatibility**: Full support for Galaxy's type system (TaskStatus, TaskPriority, etc.)
- **Observer Pattern**: Can be used in Galaxy's observer-based session monitoring

## 📋 Requirements

- **Python 3.8+**
- **Rich library**: For beautiful console output and formatting
- **Galaxy Core Types**: Uses TaskConstellation, TaskStar, TaskStarLine, and related enums

---

*Beautiful console visualization for Galaxy's intelligent task orchestration* 🎨
