# Galaxy Visualization Module

The Visualization module provides real-time DAG visualization, change detection, and interactive monitoring capabilities for the Galaxy Framework. It transforms complex workflow data into beautiful, informative visual representations.

## 🎨 Overview

Galaxy visualization brings workflows to life through dynamic, interactive displays that show task relationships, execution progress, and system state changes in real-time. The module supports multiple visualization backends and provides rich terminal output for comprehensive workflow monitoring.

## 🏗️ Architecture

```
ufo/galaxy/visualization/
├── __init__.py                     # Module exports
├── constellation_visualizer.py     # Main DAG visualization engine
├── change_detector.py             # DAG change detection and highlighting
├── rich_renderer.py               # Rich terminal rendering
├── observers/                     # Visualization observers
│   ├── __init__.py
│   ├── base_viz_observer.py       # Base visualization observer
│   ├── dag_observer.py            # DAG structure observer
│   └── progress_observer.py       # Execution progress observer
├── renderers/                     # Visualization renderers
│   ├── __init__.py
│   ├── console_renderer.py        # Console-based rendering
│   ├── web_renderer.py            # Web-based rendering
│   └── export_renderer.py         # Static export rendering
└── layouts/                       # Graph layout algorithms
    ├── __init__.py
    ├── hierarchical_layout.py     # Hierarchical layout
    ├── force_directed_layout.py   # Force-directed layout
    └── circular_layout.py         # Circular layout
```

## 🌟 Core Components

### ConstellationVisualizer

The main visualization engine that renders DAG structures and execution states.

#### Key Features
- **Real-time Updates**: Live visualization updates as constellations change
- **Multiple Layouts**: Support for various graph layout algorithms
- **Interactive Elements**: Clickable nodes and edges for detailed information
- **Customizable Styling**: Flexible styling and theming options
- **Export Capabilities**: Save visualizations as images or interactive HTML

#### Usage Example
```python
from ufo.galaxy.visualization import ConstellationVisualizer
from ufo.galaxy.constellation import TaskConstellation

# Initialize visualizer
visualizer = ConstellationVisualizer(
    layout="hierarchical",
    enable_real_time_updates=True,
    theme="galaxy_dark",
    show_task_details=True
)

# Create constellation
constellation = TaskConstellation(name="Data Pipeline")
# Add tasks and dependencies...

# Start visualization
await visualizer.visualize_constellation(constellation)

# Visualization will automatically update as constellation changes
constellation.add_task(new_task)  # Updates visualization
constellation.add_dependency("task1", "task2")  # Shows new edge
```

#### Key Methods
```python
class ConstellationVisualizer:
    async def visualize_constellation(self, constellation: TaskConstellation) -> None
    def update_visualization(self, changes: ConstellationChanges) -> None
    def set_layout_algorithm(self, layout: LayoutAlgorithm) -> None
    def apply_theme(self, theme: VisualizationTheme) -> None
    def highlight_tasks(self, task_ids: List[str], style: HighlightStyle) -> None
    def export_visualization(self, format: ExportFormat, filepath: str) -> bool
    def get_visualization_metrics(self) -> VisualizationMetrics
    def capture_snapshot(self) -> VisualizationSnapshot
```

### ChangeDetector

Intelligent change detection system that identifies and highlights DAG modifications.

#### Change Detection Features
- **Structural Changes**: Detect added/removed tasks and dependencies
- **Property Changes**: Track changes in task properties and metadata
- **Visual Highlighting**: Highlight changes with different colors and animations
- **Change History**: Maintain history of changes for replay and analysis
- **Diff Generation**: Generate detailed change reports and summaries

#### Usage Example
```python
from ufo.galaxy.visualization import ChangeDetector, ChangeHighlighter

# Initialize change detector
change_detector = ChangeDetector(
    enable_property_tracking=True,
    enable_visual_highlighting=True,
    change_retention_hours=24
)

# Setup change highlighting
highlighter = ChangeHighlighter(
    new_task_color="green",
    removed_task_color="red",
    modified_task_color="yellow",
    animation_duration=2.0
)

# Detect changes between constellation versions
old_constellation = constellation.copy()
constellation.add_task(new_task)

changes = change_detector.detect_changes(old_constellation, constellation)
print(f"Detected {len(changes)} changes:")

for change in changes:
    print(f"  {change.change_type}: {change.description}")
    if change.change_type == ChangeType.TASK_ADDED:
        highlighter.highlight_new_task(change.task_id)
```

#### Change Types
```python
class ChangeType(Enum):
    TASK_ADDED = "task_added"
    TASK_REMOVED = "task_removed"
    TASK_MODIFIED = "task_modified"
    DEPENDENCY_ADDED = "dependency_added"
    DEPENDENCY_REMOVED = "dependency_removed"
    PROPERTY_CHANGED = "property_changed"
    STATUS_CHANGED = "status_changed"
    METADATA_UPDATED = "metadata_updated"
```

### RichRenderer

Advanced terminal rendering using the Rich library for beautiful console output.

#### Rich Features
- **Colorful Tables**: Beautiful task status tables with colors and formatting
- **Progress Bars**: Real-time progress indicators with smooth animations
- **Status Panels**: Interactive status panels showing system state
- **Live Updates**: Live updating displays without screen flicker
- **Custom Themes**: Configurable color schemes and styling

#### Usage Example
```python
from ufo.galaxy.visualization import RichRenderer
from rich.console import Console

# Initialize rich renderer
console = Console()
renderer = RichRenderer(
    console=console,
    enable_animations=True,
    color_scheme="galaxy",
    update_interval=0.5
)

# Render constellation as table
constellation_table = renderer.render_constellation_table(constellation)
console.print(constellation_table)

# Show execution progress
with renderer.create_progress_display() as progress:
    for task in constellation.tasks:
        task_progress = progress.add_task(f"[cyan]{task.description}", total=100)
        # Update progress as task executes
        progress.update(task_progress, advance=20)

# Display live status panel
with renderer.create_live_status_panel() as live:
    while execution_active:
        status_panel = renderer.create_status_panel(constellation)
        live.update(status_panel)
        await asyncio.sleep(1)
```

## 📊 Visualization Observers

### BaseVizObserver

Abstract base class for all visualization observers.

```python
from abc import ABC, abstractmethod
from ufo.galaxy.core.events import Event

class BaseVizObserver(ABC):
    def __init__(self, observer_name: str):
        self.observer_name = observer_name
        self.is_active = True
        self.visualization_config = {}
    
    @abstractmethod
    async def handle_visualization_event(self, event: Event) -> None:
        """Handle visualization-related events"""
        pass
    
    @abstractmethod
    def update_visualization(self, data: Any) -> None:
        """Update visualization display"""
        pass
    
    @abstractmethod
    def cleanup_visualization(self) -> None:
        """Cleanup visualization resources"""
        pass
```

### DAGObserver

Specialized observer for DAG structure and changes.

```python
from ufo.galaxy.visualization.observers import DAGObserver

class DAGObserver(BaseVizObserver):
    def __init__(self):
        super().__init__("dag_observer")
        self.visualizer = ConstellationVisualizer()
        self.change_detector = ChangeDetector()
        self.current_constellation = None
    
    async def handle_visualization_event(self, event: Event) -> None:
        """Handle DAG-related events"""
        if event.event_type == EventType.CONSTELLATION_UPDATED:
            await self._handle_constellation_update(event)
        elif event.event_type == EventType.TASK_ADDED:
            await self._handle_task_added(event)
        elif event.event_type == EventType.DEPENDENCY_ADDED:
            await self._handle_dependency_added(event)
    
    async def _handle_constellation_update(self, event):
        """Handle constellation update event"""
        old_constellation = self.current_constellation
        new_constellation = event.constellation
        
        if old_constellation:
            changes = self.change_detector.detect_changes(
                old_constellation, new_constellation
            )
            self.visualizer.highlight_changes(changes)
        
        self.current_constellation = new_constellation
        self.visualizer.update_visualization(new_constellation)
```

### ProgressObserver

Observer for execution progress and performance metrics.

```python
from ufo.galaxy.visualization.observers import ProgressObserver

class ProgressObserver(BaseVizObserver):
    def __init__(self):
        super().__init__("progress_observer")
        self.progress_renderer = RichRenderer()
        self.progress_displays = {}
        self.performance_metrics = {}
    
    async def handle_visualization_event(self, event: Event) -> None:
        """Handle progress-related events"""
        if event.event_type == EventType.TASK_STARTED:
            self._start_task_progress(event.task_id)
        elif event.event_type == EventType.TASK_COMPLETED:
            self._complete_task_progress(event.task_id)
        elif event.event_type == EventType.EXECUTION_PROGRESS:
            self._update_execution_progress(event.progress_data)
    
    def _start_task_progress(self, task_id: str):
        """Start progress tracking for task"""
        progress_display = self.progress_renderer.create_task_progress(task_id)
        self.progress_displays[task_id] = progress_display
    
    def _update_execution_progress(self, progress_data):
        """Update overall execution progress"""
        overall_progress = self.progress_renderer.create_overall_progress(
            progress_data.completed_tasks,
            progress_data.total_tasks
        )
        self.progress_renderer.update_display(overall_progress)
```

## 🎨 Visualization Renderers

### ConsoleRenderer

Console-based rendering for terminal environments.

```python
from ufo.galaxy.visualization.renderers import ConsoleRenderer

class ConsoleRenderer:
    def __init__(self, width: int = 120, height: int = 40):
        self.width = width
        self.height = height
        self.color_enabled = True
    
    def render_dag_ascii(self, constellation: TaskConstellation) -> str:
        """Render DAG as ASCII art"""
        graph_builder = ASCIIGraphBuilder(self.width, self.height)
        
        # Add nodes
        for task in constellation.tasks:
            graph_builder.add_node(
                task.task_id,
                task.description[:20],
                self._get_task_color(task)
            )
        
        # Add edges
        for dependency in constellation.dependencies:
            graph_builder.add_edge(
                dependency.from_task_id,
                dependency.to_task_id
            )
        
        return graph_builder.render()
    
    def render_task_table(self, constellation: TaskConstellation) -> str:
        """Render tasks as formatted table"""
        table_builder = ASCIITableBuilder()
        table_builder.add_column("Task ID", width=15)
        table_builder.add_column("Description", width=40)
        table_builder.add_column("Status", width=12)
        table_builder.add_column("Priority", width=10)
        
        for task in constellation.tasks:
            table_builder.add_row([
                task.task_id,
                task.description,
                task.status.value,
                task.priority.name
            ])
        
        return table_builder.render()
```

### WebRenderer

Web-based rendering for browser visualization.

```python
from ufo.galaxy.visualization.renderers import WebRenderer

class WebRenderer:
    def __init__(self, port: int = 8080):
        self.port = port
        self.web_server = None
        self.visualization_data = {}
    
    async def start_web_server(self):
        """Start web server for visualization"""
        app = self._create_web_app()
        self.web_server = await aiohttp.web.start_server(
            app, '0.0.0.0', self.port
        )
        print(f"Visualization server started at http://localhost:{self.port}")
    
    def render_interactive_dag(self, constellation: TaskConstellation) -> str:
        """Render interactive DAG using D3.js"""
        dag_data = self._convert_to_d3_format(constellation)
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                .node { fill: #69b3a2; stroke: #333; stroke-width: 2px; }
                .link { stroke: #999; stroke-width: 2px; }
                .node-text { font-family: Arial; font-size: 12px; }
            </style>
        </head>
        <body>
            <div id="visualization"></div>
            <script>
                const data = {dag_data};
                // D3.js visualization code here
            </script>
        </body>
        </html>
        """
        
        return html_template.format(dag_data=json.dumps(dag_data))
```

## 🎭 Layout Algorithms

### Hierarchical Layout

Hierarchical layout algorithm for DAG visualization.

```python
from ufo.galaxy.visualization.layouts import HierarchicalLayout

class HierarchicalLayout:
    def __init__(self, node_spacing: int = 100, level_spacing: int = 150):
        self.node_spacing = node_spacing
        self.level_spacing = level_spacing
    
    def calculate_layout(self, constellation: TaskConstellation) -> LayoutResult:
        """Calculate hierarchical layout positions"""
        
        # Perform topological sort to determine levels
        levels = self._calculate_task_levels(constellation)
        
        # Position nodes within each level
        positions = {}
        for level, tasks in levels.items():
            y_position = level * self.level_spacing
            total_width = len(tasks) * self.node_spacing
            start_x = -total_width / 2
            
            for i, task_id in enumerate(tasks):
                x_position = start_x + (i * self.node_spacing)
                positions[task_id] = Position(x_position, y_position)
        
        return LayoutResult(positions, self._calculate_edge_paths(positions))
    
    def _calculate_task_levels(self, constellation: TaskConstellation) -> Dict[int, List[str]]:
        """Calculate hierarchical levels for tasks"""
        levels = {}
        task_levels = {}
        
        # Find root tasks (no dependencies)
        root_tasks = [
            task.task_id for task in constellation.tasks
            if not constellation.get_dependencies(task.task_id)
        ]
        
        # Assign level 0 to root tasks
        for task_id in root_tasks:
            task_levels[task_id] = 0
            levels.setdefault(0, []).append(task_id)
        
        # Calculate levels for dependent tasks
        self._propagate_levels(constellation, task_levels, levels)
        
        return levels
```

### Force-Directed Layout

Physics-based force-directed layout algorithm.

```python
from ufo.galaxy.visualization.layouts import ForceDirectedLayout

class ForceDirectedLayout:
    def __init__(self, iterations: int = 1000, cooling_factor: float = 0.95):
        self.iterations = iterations
        self.cooling_factor = cooling_factor
        self.spring_length = 100
        self.spring_strength = 0.1
        self.repulsion_strength = 1000
    
    def calculate_layout(self, constellation: TaskConstellation) -> LayoutResult:
        """Calculate force-directed layout using physics simulation"""
        
        # Initialize random positions
        positions = self._initialize_random_positions(constellation.tasks)
        velocities = {task.task_id: Vector(0, 0) for task in constellation.tasks}
        
        temperature = 100.0
        
        for iteration in range(self.iterations):
            forces = self._calculate_forces(constellation, positions)
            
            # Update positions and velocities
            for task_id in positions:
                velocities[task_id] += forces[task_id] * temperature
                velocities[task_id] *= 0.9  # Damping
                positions[task_id] += velocities[task_id]
            
            # Cool down the system
            temperature *= self.cooling_factor
        
        return LayoutResult(positions, self._calculate_edge_paths(positions))
    
    def _calculate_forces(self, constellation, positions):
        """Calculate attractive and repulsive forces"""
        forces = {task_id: Vector(0, 0) for task_id in positions}
        
        # Repulsive forces between all nodes
        for task1_id in positions:
            for task2_id in positions:
                if task1_id != task2_id:
                    repulsive_force = self._calculate_repulsive_force(
                        positions[task1_id], positions[task2_id]
                    )
                    forces[task1_id] += repulsive_force
        
        # Attractive forces for connected nodes
        for dependency in constellation.dependencies:
            attractive_force = self._calculate_attractive_force(
                positions[dependency.from_task_id],
                positions[dependency.to_task_id]
            )
            forces[dependency.from_task_id] += attractive_force
            forces[dependency.to_task_id] -= attractive_force
        
        return forces
```

## 🎯 Real-time Updates and Animations

### Animation System

Smooth animations for visualization updates.

```python
from ufo.galaxy.visualization import AnimationSystem

class AnimationSystem:
    def __init__(self, fps: int = 60):
        self.fps = fps
        self.active_animations = {}
        self.animation_queue = []
    
    def animate_task_addition(self, task_id: str, position: Position):
        """Animate new task appearance"""
        animation = TaskAdditionAnimation(
            task_id=task_id,
            start_position=Position(position.x, position.y - 50),
            end_position=position,
            duration=1.0,
            easing=EasingFunction.EASE_OUT
        )
        self.add_animation(animation)
    
    def animate_dependency_addition(self, from_task: str, to_task: str):
        """Animate new dependency edge"""
        animation = EdgeAdditionAnimation(
            from_task=from_task,
            to_task=to_task,
            duration=0.8,
            easing=EasingFunction.EASE_IN_OUT
        )
        self.add_animation(animation)
    
    def animate_status_change(self, task_id: str, new_status: TaskStatus):
        """Animate task status change"""
        animation = StatusChangeAnimation(
            task_id=task_id,
            new_status=new_status,
            duration=0.5,
            effect=AnimationEffect.PULSE
        )
        self.add_animation(animation)
```

### Live Update Manager

Manages real-time updates to visualizations.

```python
from ufo.galaxy.visualization import LiveUpdateManager

class LiveUpdateManager:
    def __init__(self, update_interval: float = 0.1):
        self.update_interval = update_interval
        self.update_queue = asyncio.Queue()
        self.subscribers = []
        self.is_running = False
    
    async def start_live_updates(self):
        """Start live update processing"""
        self.is_running = True
        while self.is_running:
            try:
                update = await asyncio.wait_for(
                    self.update_queue.get(),
                    timeout=self.update_interval
                )
                await self._process_update(update)
            except asyncio.TimeoutError:
                # Process periodic updates
                await self._process_periodic_updates()
    
    def queue_update(self, update: VisualizationUpdate):
        """Queue update for processing"""
        self.update_queue.put_nowait(update)
    
    async def _process_update(self, update: VisualizationUpdate):
        """Process queued update"""
        for subscriber in self.subscribers:
            await subscriber.handle_update(update)
```

## 🔧 Configuration

### Visualization Configuration

```python
visualization_config = {
    "layout": {
        "algorithm": "hierarchical",  # "hierarchical", "force_directed", "circular"
        "node_spacing": 100,
        "level_spacing": 150,
        "auto_layout": True
    },
    "appearance": {
        "theme": "galaxy_dark",
        "node_size": 20,
        "edge_width": 2,
        "font_size": 12,
        "show_task_details": True,
        "show_dependencies": True
    },
    "animation": {
        "enable_animations": True,
        "animation_duration": 1.0,
        "fps": 60,
        "easing_function": "ease_out"
    },
    "updates": {
        "enable_real_time_updates": True,
        "update_interval": 0.1,
        "batch_updates": True,
        "max_update_queue_size": 1000
    },
    "export": {
        "default_format": "png",
        "image_resolution": "1920x1080",
        "include_metadata": True
    }
}
```

### Rich Console Configuration

```python
rich_config = {
    "console": {
        "width": 120,
        "height": 40,
        "color_system": "auto",
        "legacy_windows": False
    },
    "tables": {
        "show_header": True,
        "show_lines": True,
        "expand": True,
        "padding": 1
    },
    "progress": {
        "show_progress": True,
        "show_percentage": True,
        "show_time": True,
        "show_speed": True
    },
    "themes": {
        "galaxy": {
            "primary": "#4A90E2",
            "secondary": "#7ED321",
            "accent": "#F5A623",
            "error": "#D0021B",
            "warning": "#F8E71C"
        }
    }
}
```

## 🧪 Testing

### Visualization Testing

```python
from tests.galaxy.visualization import VisualizationTestHarness

# Test visualization components
test_harness = VisualizationTestHarness()

# Test layout algorithms
layout_tests = test_harness.test_layout_algorithms([
    "hierarchical_layout",
    "force_directed_layout",
    "circular_layout"
])

# Test rendering systems
rendering_tests = test_harness.test_renderers([
    "console_renderer",
    "web_renderer",
    "export_renderer"
])

# Test animation system
animation_tests = test_harness.test_animations([
    "task_addition_animation",
    "dependency_animation",
    "status_change_animation"
])
```

### Mock Visualization Components

```python
from tests.galaxy.mocks import MockVisualizer, MockRenderer

# Mock visualizer for testing
mock_visualizer = MockVisualizer()
mock_visualizer.enable_capture_mode()

# Render constellation
await mock_visualizer.visualize_constellation(constellation)

# Verify visualization calls
captured_calls = mock_visualizer.get_captured_calls()
assert len(captured_calls) > 0
assert captured_calls[0].method == "render_constellation"
```

## 🚀 Getting Started

### Basic Visualization

```python
from ufo.galaxy.visualization import ConstellationVisualizer
from ufo.galaxy.constellation import TaskConstellation

# Create constellation
constellation = TaskConstellation(name="Sample Workflow")
# Add tasks and dependencies...

# Create visualizer
visualizer = ConstellationVisualizer(
    layout="hierarchical",
    enable_real_time_updates=True
)

# Start visualization
await visualizer.visualize_constellation(constellation)
```

### Advanced Visualization

```python
from ufo.galaxy.visualization import (
    ConstellationVisualizer, ChangeDetector, 
    RichRenderer, AnimationSystem
)

# Setup advanced visualization system
visualizer = ConstellationVisualizer(layout="force_directed")
change_detector = ChangeDetector(enable_visual_highlighting=True)
rich_renderer = RichRenderer(enable_animations=True)
animation_system = AnimationSystem(fps=60)

# Combine components
visualizer.set_change_detector(change_detector)
visualizer.set_renderer(rich_renderer)
visualizer.set_animation_system(animation_system)

# Start comprehensive visualization
await visualizer.start_comprehensive_visualization(constellation)
```

## 🔗 Integration

The visualization module enhances all Galaxy components:

- **[Agents](../agents/README.md)**: Visualize agent state and processing
- **[Constellation](../constellation/README.md)**: Render DAG structures and changes
- **[Session](../session/README.md)**: Monitor session progress and lifecycle
- **[Client](../client/README.md)**: Display device assignments and execution
- **[Core](../core/README.md)**: Subscribe to events for real-time updates

---

*Bringing Galaxy workflows to life through beautiful, interactive visualizations* 🎨
