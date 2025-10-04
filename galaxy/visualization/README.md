# Galaxy Visualization Module

The Visualization module provides modular and comprehensive visualization capabilities for the Galaxy Framework using rich console output. It specializes in displaying TaskConstellation structures, execution progress, task relationships, and event notifications in beautiful terminal-based interfaces.

## 🎨 Overview

Galaxy visualization transforms complex DAG workflows into readable, informative console displays using the Rich library. The module follows a modular architecture with specialized display components for different aspects of constellation visualization.

### Key Features
- **Modular Architecture**: Specialized components for different visualization needs
- **DAG Topology Visualization**: Tree-based display of task hierarchies and dependencies
- **Rich Console Output**: Beautiful terminal rendering with colors, tables, and panels
- **Task Status Tracking**: Real-time status indicators with icons and color coding
- **Event Notifications**: Specialized displays for constellation lifecycle events
- **Change Detection**: Intelligent tracking and visualization of constellation modifications
- **Dependency Analysis**: Visual representation of task relationships and satisfaction status
- **Execution Flow Monitoring**: Display of ready, running, completed, and failed tasks

## 🏗️ Architecture

```
ufo/galaxy/visualization/
├── __init__.py                     # Module exports and convenience functions
├── dag_visualizer.py              # Main DAG topology visualization
├── task_display.py                # Task-specific display components
├── constellation_display.py       # Constellation lifecycle displays
└── change_detector.py             # Change detection and comparison
```

### Modular Design Philosophy
The visualization module follows a modular, single-responsibility design with specialized components:

- **DAGVisualizer**: Focuses on DAG structure and topology
- **TaskDisplay**: Handles task-specific formatting and displays  
- **ConstellationDisplay**: Manages constellation lifecycle events
- **VisualizationChangeDetector**: Detects and visualizes changes

## 🌟 Core Components

### DAGVisualizer

The main visualization coordinator that provides comprehensive DAG visualization capabilities using Rich console output, focusing specifically on DAG topology and structure.

#### Key Features
- **Constellation Overview**: Complete constellation information with statistics
- **DAG Topology Display**: Hierarchical tree visualization of task dependencies
- **Execution Flow**: Real-time display of task execution states
- **Rich Formatting**: Beautiful colors, icons, and styling throughout

#### Usage Examples

**Basic Constellation Overview**
```python
from galaxy.visualization import DAGVisualizer

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

# Show execution flow and ready tasks
visualizer.display_execution_flow(constellation)
```

### TaskDisplay

Specialized display component for task-related visualizations with reusable formatting components.

#### Key Features
- **Task Detail Tables**: Comprehensive task information in formatted tables
- **Task Status Formatting**: Consistent status icons and colors
- **Progress Indicators**: Visual representation of task execution progress
- **Flexible Layouts**: Reusable components for different contexts

#### Usage Examples

```python
from galaxy.visualization import TaskDisplay

# Create task display component
task_display = TaskDisplay()

# Display task details table
task_display.display_task_details_table(constellation)

# Display task status grid
task_display.display_task_status_grid(constellation)

# Display execution flow with task focus
task_display.display_execution_flow(constellation)
```

### ConstellationDisplay

Specialized display component for constellation lifecycle events and state changes.

#### Key Features
- **Lifecycle Events**: Start, completion, and failure notifications
- **State Transitions**: Visual representation of constellation state changes
- **Modification Tracking**: Detailed display of constellation changes
- **Statistics Panels**: Comprehensive constellation metrics

#### Usage Examples

```python
from galaxy.visualization import ConstellationDisplay

# Create constellation display component  
constellation_display = ConstellationDisplay()

# Display constellation started event
constellation_display.display_constellation_started(constellation)

# Display constellation completion
constellation_display.display_constellation_completed(
    constellation, 
    execution_time=45.2
)

# Display constellation modifications with changes
constellation_display.display_constellation_modified(
    constellation,
    changes={
        "modification_type": "tasks_added",
        "added_tasks": ["task1", "task2"],
        "added_dependencies": [("task1", "task2")]
    }
)
```

### VisualizationChangeDetector

Intelligent change detection and comparison for constellation modifications.

#### Key Features
- **Change Detection**: Automatic detection of constellation modifications
- **Detailed Comparisons**: Task-level and dependency-level change tracking
- **Visual Differences**: Clear display of what changed between states
- **Modification Types**: Categorization of different change patterns

#### Usage Examples

```python
from galaxy.visualization import VisualizationChangeDetector

# Create change detector
change_detector = VisualizationChangeDetector()

# Take constellation snapshot
change_detector.capture_constellation_state(constellation, "initial")

# ... make changes to constellation ...

# Detect and display changes
changes = change_detector.detect_changes(constellation, "initial") 
if changes:
    change_detector.display_changes(constellation, changes)
```

**Convenience Functions**
```python
from galaxy.visualization import (
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
visualize_dag(constellation, mode="execution")   # Just execution flow
```

#### Core Methods

**DAGVisualizer Methods**
```python
class DAGVisualizer:
    def __init__(self, console: Optional[Console] = None)
    
    # Main visualization methods
    def display_constellation_overview(self, constellation: TaskConstellation, title: str) -> None
    def display_dag_topology(self, constellation: TaskConstellation) -> None
    def display_execution_flow(self, constellation: TaskConstellation) -> None
```

**TaskDisplay Methods** 
```python
class TaskDisplay:
    def __init__(self, console: Optional[Console] = None)
    
    # Task-specific display methods
    def display_task_details_table(self, constellation: TaskConstellation) -> None
    def display_task_status_grid(self, constellation: TaskConstellation) -> None
    def display_execution_flow(self, constellation: TaskConstellation) -> None
    
    # Formatting helpers
    def format_task_for_tree(self, task: TaskStar, compact: bool = False) -> str
    def get_status_text(self, status: TaskStatus) -> str
    def get_priority_color(self, priority: TaskPriority) -> str
```

**ConstellationDisplay Methods**
```python
class ConstellationDisplay:
    def __init__(self, console: Optional[Console] = None)
    
    # Lifecycle event displays
    def display_constellation_started(self, constellation: TaskConstellation, additional_info: Dict) -> None
    def display_constellation_completed(self, constellation: TaskConstellation, execution_time: float) -> None
    def display_constellation_failed(self, constellation: TaskConstellation, error: Exception) -> None
    def display_constellation_modified(self, constellation: TaskConstellation, changes: Dict) -> None
```

**VisualizationChangeDetector Methods**
```python
class VisualizationChangeDetector:
    def __init__(self)
    
    # Change detection methods
    def capture_constellation_state(self, constellation: TaskConstellation, label: str) -> None
    def detect_changes(self, constellation: TaskConstellation, baseline_label: str) -> Dict[str, Any]
    def display_changes(self, constellation: TaskConstellation, changes: Dict[str, Any]) -> None
    def get_modification_type(self, changes: Dict[str, Any]) -> str
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
- **Change Highlights**: Color-coded change indicators (🟢 added, 🔴 removed, 🟡 modified)

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

### Modular Display Architecture

Each display component provides specialized functionality:

#### DAGVisualizer - Topology Focus
- **Layer-based Topology**: Intelligent grouping of tasks by dependency layers
- **Tree Visualization**: Rich Tree widget for clear hierarchical display
- **Cycle Detection**: Identifies and reports potential cycles in the DAG
- **Dependency Flow**: Visual representation of task execution order

#### TaskDisplay - Task Focus  
- **Status Grids**: Organized layout of tasks by status
- **Detail Tables**: Comprehensive task information with filtering
- **Progress Tracking**: Real-time execution progress visualization
- **Priority Highlighting**: Color-coded priority levels

#### ConstellationDisplay - Event Focus
- **Lifecycle Events**: Professional notifications for state changes
- **Statistics Panels**: Real-time metrics and counters
- **Change Summaries**: Detailed breakdown of modifications
- **Error Handling**: Clear error and failure notifications

#### VisualizationChangeDetector - Change Focus
- **Intelligent Comparison**: Automatic detection of meaningful changes
- **Change Categories**: Classification of modification types
- **Visual Diffs**: Side-by-side comparison of states
- **History Tracking**: Maintains constellation state snapshots

### Change Detection and Visualization

The change detection system provides intelligent tracking:

#### Change Types Detected
```python
# Types of changes automatically detected
change_types = {
    "tasks_added": "New tasks added to constellation",
    "tasks_removed": "Tasks removed from constellation", 
    "dependencies_added": "New dependencies created",
    "dependencies_removed": "Dependencies removed",
    "tasks_modified": "Existing tasks updated",
    "structure_reorganized": "DAG structure changed",
    "metadata_updated": "Constellation metadata changed"
}
```

#### Change Display Features
- **Color-coded Changes**: Green for additions, red for removals, yellow for modifications
- **Summary Statistics**: Quick overview of change magnitude
- **Detailed Breakdown**: Task-by-task and dependency-by-dependency changes
- **Impact Analysis**: Shows which tasks are affected by changes

## 📊 Example Outputs

### Constellation Overview Display (DAGVisualizer)

When you call `display_constellation_overview()`, you get a comprehensive view:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Task Constellation Overview ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────── 📊 Constellation Info ────────┐ ┌────────── 📈 Statistics ─────────────┐
│ ID: data_pipeline_001                 │ │ Total Tasks: 5                        │
│ Name: Data Processing Pipeline        │ │ Dependencies: 6                       │
│ State: EXECUTING                      │ │ ✅ Completed: 2                       │
│ Created: 2025-09-23 14:30:15         │ │ 🔵 Running: 1                         │
│                                       │ │ 🟡 Ready: 2                          │
│                                       │ │ ❌ Failed: 0                         │
└───────────────────────────────────────┘ └───────────────────────────────────────┘

📊 DAG Topology
🌌 Task Constellation
├── Layer 1
│   ├── ✅ Data Collection (data_001...)
│   │   └── Dependencies: none
│   └── ✅ Config Setup (conf_001...)
│       └── Dependencies: none
├── Layer 2
│   ├── 🔵 Data Validation (valid_001...)
│   │   └── Dependencies:
│   │       └── ⬅️ ✅ Data Collection
│   └── 🟡 Processing Prep (prep_001...)
│       └── Dependencies:
│           ├── ⬅️ ✅ Data Collection
│           └── ⬅️ ✅ Config Setup
└── Layer 3
    └── 🟡 Final Report (report_001...)
        └── Dependencies:
            └── ⬅️ 🔵 Data Validation
```

### Task Details Display (TaskDisplay)

When using `display_task_details_table()`:

```
📋 Task Details
┌──────────────┬───────────────────────────┬──────────────┬──────────┬───────────────┬──────────┐
│ ID           │ Name                      │    Status    │ Priority │ Dependencies  │ Progress │
├──────────────┼───────────────────────────┼──────────────┼──────────┼───────────────┼──────────┤
│ data_001...  │ Data Collection Task      │ ✅ completed │    5     │ none          │   100%   │
│ conf_001...  │ Configuration Setup       │ ✅ completed │    8     │ none          │   100%   │
│ valid_001... │ Data Validation Process   │ 🔵 running   │    6     │ 1 deps        │   45%    │
│ prep_001...  │ Processing Preparation    │ 🟡 ready     │    5     │ 2 deps        │   N/A    │
│ report_001...│ Final Report Generation   │ ⏳ waiting   │    3     │ 1 deps        │   N/A    │
└──────────────┴───────────────────────────┴──────────────┴──────────┴───────────────┴──────────┘
```

### Constellation Events Display (ConstellationDisplay)

#### Constellation Started Event
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━ � Constellation Started ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────── 📊 🚀 Constellation Started ───────┐ ┌────────── 📈 Statistics ─────────────┐
│ ID: pipeline_789...                       │ │ Total Tasks: 8                        │
│ Name: ML Training Pipeline                │ │ Dependencies: 12                      │
│ State: EXECUTING                          │ │ ✅ Completed: 0                       │
│ Created: 14:30:15                         │ │ 🔵 Running: 0                         │
│ Started: 14:30:16                         │ │ 🟡 Ready: 3                          │
│                                           │ │ ❌ Failed: 0                         │
└───────────────────────────────────────────┘ └───────────────────────────────────────┘
```

#### Constellation Modified Event  
```
╭───────────────────── ⚙️ Constellation Structure Updated ──────────────────────╮
│ 🔄 Constellation Modified: ML Training Pipeline (pipeline_789...)            │
│                                                                              │
│ 🔧 Change Type:     │Tasks Added                                             │
│ ➕ Tasks Added:     │3 new tasks                                             │
│                     │(data_prep, feature_eng, model_val)                    │
│ 🔗 Deps Added:      │4 links                                                 │
│ 📊 Total Tasks:     │11                                                      │
│ 🔗 Total Deps:      │16                                                      │
│ 📈 Task Status:     │✅ 2 | 🔵 1 | 🟡 8 | ❌ 0                               │
│ ℹ️ Timestamp:        │2025-09-23 14:35:22                                     │
│ ℹ️ Modified By:      │MLAgent                                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### Change Detection Display (VisualizationChangeDetector)

When significant changes are detected:

```
🔄 Constellation Changes Detected

┌─────────────── Added Components ───────────────┐
│ ➕ Tasks Added (3):                            │
│   • data_preprocessing_v2 (High Priority)      │
│   • model_validation (Medium Priority)         │
│   • output_formatting (Low Priority)           │
│                                                │
│ � Dependencies Added (4):                     │
│   • data_collection → data_preprocessing_v2    │
│   • data_preprocessing_v2 → model_training     │
│   • model_training → model_validation          │
│   • model_validation → output_formatting       │
└────────────────────────────────────────────────┘

┌─────────────── Removed Components ─────────────┐
│ ➖ Tasks Removed (1):                          │
│   • old_data_processor (was Medium Priority)   │
│                                                │
│ 🔗 Dependencies Removed (2):                   │
│   • data_collection → old_data_processor       │
│   • old_data_processor → model_training        │
└────────────────────────────────────────────────┘

📊 Change Summary: +3 tasks, -1 task, +4 deps, -2 deps
```

## 🔧 Customization and Configuration

### Console Customization

You can customize the visualization output by providing your own Rich Console:

```python
from rich.console import Console
from galaxy.visualization import DAGVisualizer, TaskDisplay, ConstellationDisplay

# Custom console with specific settings
custom_console = Console(
    width=100,           # Narrower output
    color_system="256",  # 256 color support
    force_terminal=True, # Force terminal mode
    legacy_windows=False # Modern Windows terminal support
)

# Use custom console with visualizers
dag_visualizer = DAGVisualizer(console=custom_console)
task_display = TaskDisplay(console=custom_console)
constellation_display = ConstellationDisplay(console=custom_console)
```

### Modular Usage Patterns

The modular design allows for flexible usage:

#### Full Integration Pattern
```python
from galaxy.visualization import (
    DAGVisualizer, TaskDisplay, ConstellationDisplay, VisualizationChangeDetector
)

class ConstellationMonitor:
    def __init__(self):
        self.dag_viz = DAGVisualizer()
        self.task_display = TaskDisplay()
        self.constellation_display = ConstellationDisplay()
        self.change_detector = VisualizationChangeDetector()
    
    def handle_constellation_created(self, constellation):
        self.constellation_display.display_constellation_started(constellation)
        self.dag_viz.display_constellation_overview(constellation)
    
    def handle_constellation_modified(self, constellation):
        changes = self.change_detector.detect_changes(constellation, "baseline")
        if changes:
            self.constellation_display.display_constellation_modified(
                constellation, changes
            )
```

#### Selective Usage Pattern
```python
# Use only specific components as needed
from galaxy.visualization import TaskDisplay

# Just for task monitoring
task_display = TaskDisplay()

def monitor_task_progress(constellation):
    task_display.display_execution_flow(constellation)
    if constellation.task_count <= 20:
        task_display.display_task_details_table(constellation)
```

#### Convenience Functions Pattern
```python
# Quick visualization without object management
from galaxy.visualization import visualize_dag, display_execution_progress

def quick_debug(constellation):
    visualize_dag(constellation, mode="topology")
    display_execution_progress(constellation)
```

### Display Customization

Each component provides customization options:

#### DAGVisualizer Customization
```python
class CustomDAGVisualizer(DAGVisualizer):
    def __init__(self, console=None):
        super().__init__(console)
        # Override status colors
        self.status_colors = {
            TaskStatus.PENDING: "bright_yellow",
            TaskStatus.RUNNING: "bright_blue", 
            TaskStatus.COMPLETED: "bright_green",
            TaskStatus.FAILED: "bright_red",
        }
        
        # Override dependency symbols
        self.dependency_symbols = {
            DependencyType.UNCONDITIONAL: "➤",
            DependencyType.SUCCESS_ONLY: "⟹",
            DependencyType.CONDITIONAL: "⇥",
        }
```

#### TaskDisplay Customization
```python
# Customize task table columns
task_display = TaskDisplay()

# Override table formatting
def custom_task_table(constellation):
    table = Table(title="Custom Task View", box=box.DOUBLE)
    table.add_column("Task", style="cyan", width=30)
    table.add_column("Status", justify="center", width=15) 
    table.add_column("ETA", justify="right", width=10)
    
    for task in constellation.get_all_tasks():
        table.add_row(
            task.name,
            task_display.get_status_text(task.status),
            calculate_eta(task)
        )
    
    task_display.console.print(table)
```

## 🧪 Testing and Development

### Unit Testing

The visualization module includes comprehensive testing capabilities:

```python
import pytest
from rich.console import Console
from io import StringIO
from galaxy.visualization import (
    DAGVisualizer, TaskDisplay, ConstellationDisplay, 
    VisualizationChangeDetector, visualize_dag
)

def test_modular_visualization():
    """Test modular visualization components"""
    # Create test constellation
    constellation = create_test_constellation()
    
    # Test each component independently
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    
    # Test DAGVisualizer
    dag_viz = DAGVisualizer(console=console)
    dag_viz.display_constellation_overview(constellation)
    
    # Test TaskDisplay
    task_display = TaskDisplay(console=console)
    task_display.display_task_details_table(constellation)
    
    # Test ConstellationDisplay
    constellation_display = ConstellationDisplay(console=console)
    constellation_display.display_constellation_started(constellation)
    
    # Verify output was generated
    output_text = output.getvalue()
    assert "Task Constellation" in output_text
    assert "📋 Task Details" in output_text

def test_change_detection():
    """Test change detection functionality"""
    constellation = create_test_constellation()
    change_detector = VisualizationChangeDetector()
    
    # Capture initial state
    change_detector.capture_constellation_state(constellation, "initial")
    
    # Modify constellation
    constellation.create_task("new_task", "New Task")
    
    # Detect changes
    changes = change_detector.detect_changes(constellation, "initial")
    assert changes["added_tasks"]
    assert "new_task" in changes["added_tasks"]

def test_convenience_functions():
    """Test convenience visualization functions"""
    constellation = create_test_constellation()
    
    # Test all convenience functions don't crash
    visualize_dag(constellation, mode="overview")
    visualize_dag(constellation, mode="topology")
    visualize_dag(constellation, mode="execution")

def test_component_integration():
    """Test that components work together"""
    constellation = create_test_constellation()
    
    # All components should accept the same console
    console = Console()
    dag_viz = DAGVisualizer(console=console)
    task_display = TaskDisplay(console=console)
    constellation_display = ConstellationDisplay(console=console)
    
    # Should all work without errors
    dag_viz.display_constellation_overview(constellation)
    task_display.display_execution_flow(constellation)
    constellation_display.display_constellation_started(constellation)
```

### Manual Testing

You can manually test the visualization with sample data:

```python
from galaxy.visualization import *
from galaxy.constellation import TaskConstellation, TaskPriority
from galaxy.constellation.enums import TaskStatus

def create_sample_constellation():
    """Create a comprehensive sample constellation for testing"""
    constellation = TaskConstellation(name="ML Training Pipeline")
    
    # Data tasks
    data_task = constellation.create_task(
        "data_collection", "Data Collection", priority=TaskPriority.HIGH
    )
    data_task.status = TaskStatus.COMPLETED
    
    prep_task = constellation.create_task(
        "data_preprocessing", "Data Preprocessing", priority=TaskPriority.HIGH
    )
    prep_task.status = TaskStatus.RUNNING
    
    # Model tasks
    train_task = constellation.create_task(
        "model_training", "Model Training", priority=TaskPriority.MEDIUM  
    )
    train_task.status = TaskStatus.WAITING_DEPENDENCY
    
    val_task = constellation.create_task(
        "model_validation", "Model Validation", priority=TaskPriority.MEDIUM
    )
    val_task.status = TaskStatus.PENDING
    
    # Output tasks
    deploy_task = constellation.create_task(
        "model_deployment", "Model Deployment", priority=TaskPriority.LOW
    )
    deploy_task.status = TaskStatus.PENDING
    
    # Add dependencies
    constellation.add_dependency("data_collection", "data_preprocessing")
    constellation.add_dependency("data_preprocessing", "model_training")
    constellation.add_dependency("model_training", "model_validation")
    constellation.add_dependency("model_validation", "model_deployment")
    
    return constellation

def test_all_components():
    """Comprehensive test of all visualization components"""
    constellation = create_sample_constellation()
    
    print("=== Testing DAGVisualizer ===")
    dag_viz = DAGVisualizer()
    dag_viz.display_constellation_overview(constellation)
    
    print("\n=== Testing TaskDisplay ===")
    task_display = TaskDisplay()
    task_display.display_task_details_table(constellation)
    task_display.display_execution_flow(constellation)
    
    print("\n=== Testing ConstellationDisplay ===")
    constellation_display = ConstellationDisplay()
    constellation_display.display_constellation_started(constellation)
    
    print("\n=== Testing Change Detection ===")
    change_detector = VisualizationChangeDetector()
    change_detector.capture_constellation_state(constellation, "baseline")
    
    # Make changes
    new_task = constellation.create_task("monitoring", "Model Monitoring")
    constellation.add_dependency("model_deployment", "monitoring")
    
    changes = change_detector.detect_changes(constellation, "baseline")
    constellation_display.display_constellation_modified(constellation, changes)
    
    print("\n=== Testing Convenience Functions ===")
    visualize_dag(constellation, mode="topology")

if __name__ == "__main__":
    test_all_components()
```

### Integration Testing

Test integration with Galaxy Framework components:

```python
def test_galaxy_integration():
    """Test integration with Galaxy session observers"""
    from galaxy.session.observers import DAGVisualizationObserver
    from galaxy.visualization import ConstellationDisplay, VisualizationChangeDetector
    
    # Test that observers can use visualization components
    observer = DAGVisualizationObserver()
    constellation = create_sample_constellation()
    
    # Should work with all event types
    observer.on_constellation_started(constellation)
    observer.on_constellation_task_completed(constellation, "data_collection")
    observer.on_constellation_completed(constellation)
```

## 🚀 Getting Started

### Quick Start

The simplest way to visualize a constellation using convenience functions:

```python
from galaxy.visualization import visualize_dag

# Create your constellation
constellation = TaskConstellation(name="My Workflow")
# ... add tasks and dependencies ...

# Quick visualization
visualize_dag(constellation)  # Shows full overview by default
```

### Component-Based Usage

For more control, use individual components:

```python
from galaxy.visualization import DAGVisualizer, TaskDisplay, ConstellationDisplay

# Choose components based on your needs
dag_viz = DAGVisualizer()          # For topology and structure
task_display = TaskDisplay()       # For task-focused views  
constellation_display = ConstellationDisplay()  # For lifecycle events

# Use specific visualizations
dag_viz.display_constellation_overview(constellation)
task_display.display_execution_flow(constellation)
constellation_display.display_constellation_started(constellation)
```

### Step-by-Step Usage

```python
from galaxy.visualization import DAGVisualizer, TaskDisplay

# 1. Create visualizers
dag_visualizer = DAGVisualizer()
task_display = TaskDisplay()

# 2. Choose what to display based on your needs:

# Full overview (recommended for first look)
dag_visualizer.display_constellation_overview(constellation)

# Focus on task execution
task_display.display_execution_flow(constellation)

# Detailed task information  
task_display.display_task_details_table(constellation)

# Just the DAG structure
dag_visualizer.display_dag_topology(constellation)
```

### Change Monitoring Pattern

Track constellation changes over time:

```python
from galaxy.visualization import (
    VisualizationChangeDetector, ConstellationDisplay
)

# Set up change monitoring
change_detector = VisualizationChangeDetector()
constellation_display = ConstellationDisplay()

# Capture initial state
change_detector.capture_constellation_state(constellation, "initial")

# ... constellation gets modified ...

# Detect and display changes
changes = change_detector.detect_changes(constellation, "initial")
if changes:
    constellation_display.display_constellation_modified(constellation, changes)
```

### Integration with Galaxy Framework

The visualization module integrates seamlessly with the Galaxy Framework:

#### Session Observer Integration
```python
from galaxy.visualization import ConstellationDisplay, VisualizationChangeDetector

class VisualizationSessionObserver:
    def __init__(self):
        self.constellation_display = ConstellationDisplay()
        self.change_detector = VisualizationChangeDetector()
    
    async def on_constellation_started(self, constellation):
        self.constellation_display.display_constellation_started(constellation)
        self.change_detector.capture_constellation_state(constellation, "started")
    
    async def on_constellation_modified(self, constellation):
        changes = self.change_detector.detect_changes(constellation, "started")
        if changes:
            self.constellation_display.display_constellation_modified(
                constellation, changes
            )
    
    async def on_constellation_completed(self, constellation):
        self.constellation_display.display_constellation_completed(constellation)
```

#### Agent Integration
```python
from galaxy.visualization import visualize_dag, TaskDisplay

class ConstellationAgent:
    def __init__(self):
        self.task_display = TaskDisplay()
        self.debug_mode = True
    
    def process_constellation(self, constellation):
        # Debug visualization during development
        if self.debug_mode:
            visualize_dag(constellation, mode="topology")
        
        # Monitor execution progress
        self.task_display.display_execution_flow(constellation)
        
        # Process tasks...
```

## 🌟 Key Benefits

### Why Use Galaxy Visualization?

1. **Modular Design**: Use only the components you need for specific visualization tasks
2. **Instant Understanding**: Quickly grasp complex DAG structures at a glance
3. **Debug Friendly**: Identify circular dependencies, bottlenecks, and issues
4. **Progress Tracking**: Monitor execution progress in real-time with specialized displays
5. **Change Awareness**: Intelligent detection and visualization of constellation modifications
6. **Beautiful Output**: Professional-quality terminal visualization with Rich
7. **Event Integration**: Seamless integration with Galaxy's event-driven architecture
8. **Zero Configuration**: Works out of the box with sensible defaults

### Use Cases

#### Development and Debugging
- **Constellation Creation**: Visualize DAG structure as it's being built
- **Dependency Analysis**: Identify circular dependencies and structural issues  
- **Task Debugging**: Monitor individual task status and execution progress
- **Change Impact**: See how modifications affect the overall constellation structure

#### Monitoring and Operations
- **Real-time Progress**: Track execution progress during workflow runs
- **Event Notifications**: Professional displays for constellation lifecycle events
- **Status Dashboards**: Comprehensive view of task and constellation status
- **Change Tracking**: Historical view of constellation modifications

#### Documentation and Presentation
- **Visual Documentation**: Generate visual representations for documentation
- **Workflow Demos**: Show workflow structures in presentations and demos
- **Training Materials**: Educational displays for understanding DAG concepts
- **Architecture Review**: Clear visualization for architecture discussions

### Component Benefits

#### DAGVisualizer Benefits
- **Structure Focus**: Clear visualization of DAG topology and hierarchy
- **Layer Analysis**: Intelligent grouping by dependency layers
- **Cycle Detection**: Early identification of structural problems
- **Execution Flow**: Real-time view of task execution order

#### TaskDisplay Benefits
- **Task Focus**: Detailed view of individual task information
- **Status Grids**: Organized layout of tasks by execution status
- **Progress Tracking**: Visual representation of task completion
- **Flexible Tables**: Customizable task information displays

#### ConstellationDisplay Benefits
- **Event Clarity**: Professional notifications for lifecycle events
- **Change Visualization**: Clear display of constellation modifications
- **Statistics Integration**: Real-time metrics and performance data
- **Error Handling**: Clear error and failure notifications

#### VisualizationChangeDetector Benefits
- **Intelligent Detection**: Automatic identification of meaningful changes
- **Change Classification**: Categorization of different modification types
- **Impact Analysis**: Understanding of change scope and effects
- **History Tracking**: Ability to compare against previous states

## 🔗 Integration with Galaxy Framework

The visualization module serves Galaxy Framework components with modular, specialized displays:

- **[Constellation](../constellation/README.md)**: Visualizes TaskConstellation DAG structures and execution states
- **[Session](../session/README.md)**: Used by session observers to display progress and changes  
- **[Agents](../agents/README.md)**: Provides debugging visualization for constellation creation and modification
- **[Core](../core/README.md)**: Uses core types and enums for consistent representation

### Framework Integration Points

The module integrates through:

#### Observer Pattern Integration
- **Event Displays**: ConstellationDisplay handles lifecycle events from session observers
- **Change Detection**: VisualizationChangeDetector works with constellation modification events
- **Progress Monitoring**: TaskDisplay provides real-time task execution updates
- **Modular Events**: Each component can handle specific event types independently

#### Agent Integration
- **Development Support**: DAGVisualizer provides topology debugging for agents
- **Execution Monitoring**: TaskDisplay tracks agent-initiated task execution
- **Change Visualization**: Shows how agents modify constellation structure
- **Error Debugging**: Clear visualization of constellation issues for agent development

#### Session Management
- **Lifecycle Tracking**: ConstellationDisplay handles session start/complete/fail events
- **Progress Updates**: TaskDisplay provides execution flow monitoring
- **Change Notifications**: VisualizationChangeDetector tracks session modifications
- **State Visualization**: DAGVisualizer shows current constellation state

#### Type System Integration
- **Rich Console**: Professional terminal output that fits Galaxy's user experience
- **Type Compatibility**: Full support for Galaxy's type system (TaskStatus, TaskPriority, etc.)
- **Enum Support**: Consistent display of Galaxy enums and constants
- **Error Handling**: Graceful handling of Galaxy exceptions and error states

### Integration Patterns

#### Session Observer Pattern
```python
from galaxy.session.observers import DAGVisualizationObserver
from galaxy.visualization import ConstellationDisplay, TaskDisplay

class EnhancedVisualizationObserver(DAGVisualizationObserver):
    def __init__(self):
        super().__init__()
        self.constellation_display = ConstellationDisplay()
        self.task_display = TaskDisplay()
    
    async def on_constellation_started(self, constellation):
        self.constellation_display.display_constellation_started(constellation)
    
    async def on_task_completed(self, constellation, task_id):
        self.task_display.display_execution_flow(constellation)
```

#### Agent Development Pattern  
```python
from galaxy.agents import ConstellationAgent
from galaxy.visualization import DAGVisualizer, VisualizationChangeDetector

class DebuggingAgent(ConstellationAgent):
    def __init__(self):
        super().__init__()
        self.dag_viz = DAGVisualizer()
        self.change_detector = VisualizationChangeDetector()
        
    def modify_constellation(self, constellation):
        # Capture state before changes
        self.change_detector.capture_constellation_state(constellation, "before")
        
        # Make modifications
        self.add_tasks(constellation)
        
        # Visualize changes
        changes = self.change_detector.detect_changes(constellation, "before")
        if changes and self.debug_mode:
            self.dag_viz.display_constellation_overview(constellation)
```

## 📋 Requirements

- **Python 3.8+**
- **Rich library**: For beautiful console output and formatting
- **Galaxy Core Types**: Uses TaskConstellation, TaskStar, and related enums
- **Galaxy Framework**: Integrates with Galaxy session management and event system

## 🎯 Migration from Previous Architecture

### Refactoring Benefits

The modular architecture provides several improvements over the previous single-class design:

#### Before (Single DAGVisualizer)
- ❌ Single large class with multiple responsibilities
- ❌ Mixed visualization logic with event handling
- ❌ Difficult to customize specific display aspects
- ❌ Code duplication across similar display functions

#### After (Modular Components)  
- ✅ Specialized components with single responsibilities
- ✅ Clean separation of visualization and event handling
- ✅ Easy customization and extension of specific components
- ✅ Reusable display components across different contexts
- ✅ Better testability and maintainability

### Migration Guide

If you were using the old DAGVisualizer directly:

```python
# Old way
from galaxy.visualization import DAGVisualizer
visualizer = DAGVisualizer()
visualizer.display_constellation_overview(constellation)

# New way (still works!)
from galaxy.visualization import DAGVisualizer  
visualizer = DAGVisualizer()
visualizer.display_constellation_overview(constellation)

# New way (modular)
from galaxy.visualization import ConstellationDisplay, TaskDisplay
constellation_display = ConstellationDisplay()
task_display = TaskDisplay()
constellation_display.display_constellation_started(constellation)
task_display.display_execution_flow(constellation)
```

The convenience functions provide backward compatibility while the new modular components offer enhanced flexibility.

---

*Modular, beautiful console visualization for Galaxy's intelligent task orchestration* 🎨✨
