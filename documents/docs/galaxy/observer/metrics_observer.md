# Session Metrics Observer

The **SessionMetricsObserver** collects comprehensive performance metrics and statistics during constellation execution. It tracks task execution times, constellation lifecycle, modifications, and computes detailed statistics for performance analysis.

**Location:** `galaxy/session/observers/base_observer.py`

The metrics observer is essential for evaluating Galaxy performance, identifying bottlenecks, and analyzing constellation modification patterns for research and optimization.

---

## 🎯 Purpose

The Metrics Observer provides:

1. **Performance Tracking** — Measure task and constellation execution times
2. **Success Rate Monitoring** — Track completion and failure rates
3. **Modification Analytics** — Monitor constellation structural changes
4. **Statistical Summaries** — Compute aggregated metrics for analysis

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Event Sources"
        O[Orchestrator]
        A[Agent]
    end
    
    subgraph "Event System"
        EB[EventBus]
    end
    
    subgraph "Metrics Observer"
        SMO[SessionMetricsObserver]
        TE[Task Events Handler]
        CE[Constellation Events Handler]
        MS[Metrics Storage]
        SC[Statistics Computer]
    end
    
    subgraph "Outputs"
        R[result.json]
        L[Logs]
    end
    
    O -->|task events| EB
    A -->|constellation events| EB
    EB -->|notify| SMO
    
    SMO --> TE
    SMO --> CE
    TE --> MS
    CE --> MS
    MS --> SC
    SC --> R
    SC --> L
    
    style SMO fill:#66bb6a,stroke:#333,stroke-width:3px
    style MS fill:#fff4e1,stroke:#333,stroke-width:2px
    style SC fill:#ffa726,stroke:#333,stroke-width:2px
    style EB fill:#4a90e2,stroke:#333,stroke-width:2px,color:#fff
```

---

## 📊 Metrics Collected

The observer collects metrics across three categories:

### Task Metrics

Track individual task execution:

| Metric | Description | Computed |
|--------|-------------|----------|
| **task_count** | Total number of tasks started | Real-time |
| **completed_tasks** | Number of successfully completed tasks | Real-time |
| **failed_tasks** | Number of failed tasks | Real-time |
| **total_execution_time** | Sum of all task execution times | Real-time |
| **task_timings** | Dict mapping task_id → {start, end, duration} | Real-time |
| **success_rate** | completed / total tasks | Computed |
| **failure_rate** | failed / total tasks | Computed |
| **average_task_duration** | Average execution time per task | Computed |
| **min_task_duration** | Fastest task execution time | Computed |
| **max_task_duration** | Slowest task execution time | Computed |

### Constellation Metrics

Monitor constellation lifecycle:

| Metric | Description | Computed |
|--------|-------------|----------|
| **constellation_count** | Total constellations processed | Real-time |
| **completed_constellations** | Successfully completed constellations | Real-time |
| **failed_constellations** | Failed constellations | Real-time |
| **total_constellation_time** | Total constellation execution time | Real-time |
| **constellation_timings** | Dict mapping constellation_id → timing data | Real-time |
| **constellation_success_rate** | completed / total constellations | Computed |
| **average_constellation_duration** | Average constellation execution time | Computed |
| **min_constellation_duration** | Fastest constellation | Computed |
| **max_constellation_duration** | Slowest constellation | Computed |
| **average_tasks_per_constellation** | Average number of tasks | Computed |

### Modification Metrics

Track constellation structural changes:

| Metric | Description | Computed |
|--------|-------------|----------|
| **constellation_modifications** | Dict mapping constellation_id → modification list | Real-time |
| **total_modifications** | Total number of modifications | Computed |
| **constellations_modified** | Number of constellations with modifications | Computed |
| **average_modifications_per_constellation** | Average modifications per constellation | Computed |
| **max_modifications_for_single_constellation** | Most-modified constellation | Computed |
| **most_modified_constellation** | ID of most-modified constellation | Computed |
| **modification_types_breakdown** | Count by modification type | Computed |

---

## 💻 Implementation

### Initialization

```python
from galaxy.session.observers import SessionMetricsObserver
import logging

# Create metrics observer
metrics_observer = SessionMetricsObserver(
    session_id="galaxy_session_20231113",
    logger=logging.getLogger(__name__)
)

# Subscribe to event bus
from galaxy.core.events import get_event_bus
event_bus = get_event_bus()
event_bus.subscribe(metrics_observer)
```

**Constructor Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | `str` | Yes | Unique identifier for the session |
| `logger` | `logging.Logger` | No | Logger instance (creates default if None) |

### Internal Metrics Structure

The observer maintains a comprehensive metrics dictionary:

```python
self.metrics: Dict[str, Any] = {
    "session_id": session_id,
    
    # Task metrics
    "task_count": 0,
    "completed_tasks": 0,
    "failed_tasks": 0,
    "total_execution_time": 0.0,
    "task_timings": {},  # task_id -> {start, end, duration}
    
    # Constellation metrics
    "constellation_count": 0,
    "completed_constellations": 0,
    "failed_constellations": 0,
    "total_constellation_time": 0.0,
    "constellation_timings": {},  # constellation_id -> timing data
    
    # Modification tracking
    "constellation_modifications": {}  # constellation_id -> [modifications]
}
```

---

## 🔄 Event Processing

### Task Event Handling

The observer tracks task lifecycle events:

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant EB as EventBus
    participant MO as MetricsObserver
    participant MS as Metrics Storage
    
    O->>EB: TASK_STARTED
    EB->>MO: on_event(event)
    MO->>MS: Increment task_count<br/>Record start_time
    
    Note over O: Task executes
    
    O->>EB: TASK_COMPLETED
    EB->>MO: on_event(event)
    MO->>MS: Increment completed_tasks<br/>Calculate duration<br/>Update total_execution_time
```

**Processing Logic:**

```python
def _handle_task_started(self, event: TaskEvent) -> None:
    """Handle TASK_STARTED event."""
    self.metrics["task_count"] += 1
    self.metrics["task_timings"][event.task_id] = {
        "start": event.timestamp
    }

def _handle_task_completed(self, event: TaskEvent) -> None:
    """Handle TASK_COMPLETED event."""
    self.metrics["completed_tasks"] += 1
    
    if event.task_id in self.metrics["task_timings"]:
        duration = (
            event.timestamp - 
            self.metrics["task_timings"][event.task_id]["start"]
        )
        self.metrics["task_timings"][event.task_id]["duration"] = duration
        self.metrics["task_timings"][event.task_id]["end"] = event.timestamp
        self.metrics["total_execution_time"] += duration

def _handle_task_failed(self, event: TaskEvent) -> None:
    """Handle TASK_FAILED event."""
    self.metrics["failed_tasks"] += 1
    # Also calculate duration for failed tasks
    if event.task_id in self.metrics["task_timings"]:
        duration = (
            event.timestamp - 
            self.metrics["task_timings"][event.task_id]["start"]
        )
        self.metrics["task_timings"][event.task_id]["duration"] = duration
        self.metrics["total_execution_time"] += duration
```

### Constellation Event Handling

Tracks constellation lifecycle and modifications:

```python
def _handle_constellation_started(self, event: ConstellationEvent) -> None:
    """Handle CONSTELLATION_STARTED event."""
    self.metrics["constellation_count"] += 1
    constellation_id = event.constellation_id
    constellation = event.data.get("constellation")
    
    # Store initial statistics
    self.metrics["constellation_timings"][constellation_id] = {
        "start_time": event.timestamp,
        "initial_statistics": (
            constellation.get_statistics() if constellation else {}
        ),
        "processing_start_time": event.data.get("processing_start_time"),
        "processing_end_time": event.data.get("processing_end_time"),
        "processing_duration": event.data.get("processing_duration"),
    }

def _handle_constellation_completed(self, event: ConstellationEvent) -> None:
    """Handle CONSTELLATION_COMPLETED event."""
    self.metrics["completed_constellations"] += 1
    constellation_id = event.constellation_id
    constellation = event.data.get("constellation")
    
    # Calculate duration and store final statistics
    duration = (
        event.timestamp - 
        self.metrics["constellation_timings"][constellation_id]["start_time"]
        if constellation_id in self.metrics["constellation_timings"]
        else None
    )
    
    if constellation_id in self.metrics["constellation_timings"]:
        self.metrics["constellation_timings"][constellation_id].update({
            "end_time": event.timestamp,
            "duration": duration,
            "final_statistics": (
                constellation.get_statistics() if constellation else {}
            ),
        })
```

### Modification Tracking

Tracks constellation structural changes with detailed change detection:

```python
def _handle_constellation_modified(self, event: ConstellationEvent) -> None:
    """Handle CONSTELLATION_MODIFIED event."""
    constellation_id = event.constellation_id
    
    # Initialize modifications list if needed
    if constellation_id not in self.metrics["constellation_modifications"]:
        self.metrics["constellation_modifications"][constellation_id] = []
    
    if hasattr(event, "data") and event.data:
        old_constellation = event.data.get("old_constellation")
        new_constellation = event.data.get("new_constellation")
        
        # Calculate changes using VisualizationChangeDetector
        changes = None
        if old_constellation and new_constellation:
            changes = VisualizationChangeDetector.calculate_constellation_changes(
                old_constellation, new_constellation
            )
        
        # Store modification record
        modification_record = {
            "timestamp": event.timestamp,
            "modification_type": event.data.get("modification_type", "unknown"),
            "on_task_id": event.data.get("on_task_id", []),
            "changes": changes,
            "new_statistics": (
                new_constellation.get_statistics() if new_constellation else {}
            ),
            "processing_start_time": event.data.get("processing_start_time"),
            "processing_end_time": event.data.get("processing_end_time"),
            "processing_duration": event.data.get("processing_duration"),
        }
        
        self.metrics["constellation_modifications"][constellation_id].append(
            modification_record
        )
```

---

## 📖 API Reference

### Constructor

```python
def __init__(self, session_id: str, logger: Optional[logging.Logger] = None)
```

Initialize the metrics observer.

**Parameters:**

- `session_id` — Unique identifier for the session
- `logger` — Optional logger instance (creates default if None)

### get_metrics()

```python
def get_metrics(self) -> Dict[str, Any]
```

Get collected metrics with computed statistics.

**Returns:**

Dictionary containing:
- All raw metrics (counts, timings, etc.)
- `task_statistics` — Computed task metrics
- `constellation_statistics` — Computed constellation metrics
- `modification_statistics` — Computed modification metrics

**Example:**

```python
# After constellation execution
metrics = metrics_observer.get_metrics()

# Access task statistics
print(f"Total tasks: {metrics['task_statistics']['total_tasks']}")
print(f"Success rate: {metrics['task_statistics']['success_rate']:.2%}")
print(f"Avg duration: {metrics['task_statistics']['average_task_duration']:.2f}s")

# Access constellation statistics
print(f"Total constellations: {metrics['constellation_statistics']['total_constellations']}")
print(f"Avg tasks per constellation: {metrics['constellation_statistics']['average_tasks_per_constellation']:.1f}")

# Access modification statistics
print(f"Total modifications: {metrics['modification_statistics']['total_modifications']}")
print(f"Modification types: {metrics['modification_statistics']['modification_types_breakdown']}")
```

---

## 📊 Computed Statistics

The observer computes three categories of statistics:

### Task Statistics

```python
{
    "total_tasks": 10,
    "completed_tasks": 8,
    "failed_tasks": 2,
    "success_rate": 0.8,
    "failure_rate": 0.2,
    "average_task_duration": 2.5,
    "min_task_duration": 0.5,
    "max_task_duration": 5.2,
    "total_task_execution_time": 25.0
}
```

### Constellation Statistics

```python
{
    "total_constellations": 1,
    "completed_constellations": 1,
    "failed_constellations": 0,
    "success_rate": 1.0,
    "average_constellation_duration": 30.5,
    "min_constellation_duration": 30.5,
    "max_constellation_duration": 30.5,
    "total_constellation_time": 30.5,
    "average_tasks_per_constellation": 10.0
}
```

### Modification Statistics

```python
{
    "total_modifications": 3,
    "constellations_modified": 1,
    "average_modifications_per_constellation": 3.0,
    "max_modifications_for_single_constellation": 3,
    "most_modified_constellation": "const_123",
    "modifications_per_constellation": {
        "const_123": 3
    },
    "modification_types_breakdown": {
        "add_tasks": 2,
        "modify_dependencies": 1
    }
}
```

---

## 🔍 Usage Examples

### Example 1: Basic Metrics Collection

```python
import asyncio
from galaxy.core.events import get_event_bus
from galaxy.session.observers import SessionMetricsObserver

async def collect_metrics():
    """Collect and display metrics for constellation execution."""
    
    # Create and subscribe metrics observer
    metrics_observer = SessionMetricsObserver(session_id="demo_session")
    event_bus = get_event_bus()
    event_bus.subscribe(metrics_observer)
    
    # Execute constellation (orchestrator will publish events)
    await orchestrator.execute_constellation(constellation)
    
    # Retrieve metrics
    metrics = metrics_observer.get_metrics()
    
    # Display summary
    print("\n=== Execution Summary ===")
    print(f"Session: {metrics['session_id']}")
    print(f"Tasks: {metrics['task_count']} total, "
          f"{metrics['completed_tasks']} completed, "
          f"{metrics['failed_tasks']} failed")
    print(f"Total execution time: {metrics['total_execution_time']:.2f}s")
    
    # Display task statistics
    task_stats = metrics['task_statistics']
    print(f"\nTask Success Rate: {task_stats['success_rate']:.1%}")
    print(f"Average Task Duration: {task_stats['average_task_duration']:.2f}s")
    print(f"Fastest Task: {task_stats['min_task_duration']:.2f}s")
    print(f"Slowest Task: {task_stats['max_task_duration']:.2f}s")
    
    # Clean up
    event_bus.unsubscribe(metrics_observer)

asyncio.run(collect_metrics())
```

### Example 2: Performance Analysis

```python
def analyze_performance(metrics_observer: SessionMetricsObserver):
    """Analyze performance metrics and identify bottlenecks."""
    
    metrics = metrics_observer.get_metrics()
    task_timings = metrics['task_timings']
    
    # Find slowest tasks
    sorted_tasks = sorted(
        task_timings.items(),
        key=lambda x: x[1].get('duration', 0),
        reverse=True
    )
    
    print("\n=== Top 5 Slowest Tasks ===")
    for task_id, timing in sorted_tasks[:5]:
        duration = timing.get('duration', 0)
        print(f"{task_id}: {duration:.2f}s")
    
    # Analyze modification patterns
    mod_stats = metrics['modification_statistics']
    if mod_stats['total_modifications'] > 0:
        print(f"\n=== Modification Analysis ===")
        print(f"Total Modifications: {mod_stats['total_modifications']}")
        print(f"Average per Constellation: "
              f"{mod_stats['average_modifications_per_constellation']:.1f}")
        print(f"Most Modified: {mod_stats['most_modified_constellation']}")
        print("\nModification Types:")
        for mod_type, count in mod_stats['modification_types_breakdown'].items():
            print(f"  {mod_type}: {count}")
```

### Example 3: Export Metrics to JSON

```python
import json
from pathlib import Path

def export_metrics(metrics_observer: SessionMetricsObserver, output_path: str):
    """Export metrics to JSON file for analysis."""
    
    metrics = metrics_observer.get_metrics()
    
    # Convert to JSON-serializable format
    output_data = {
        "session_id": metrics["session_id"],
        "task_statistics": metrics["task_statistics"],
        "constellation_statistics": metrics["constellation_statistics"],
        "modification_statistics": metrics["modification_statistics"],
        "raw_metrics": {
            "task_count": metrics["task_count"],
            "completed_tasks": metrics["completed_tasks"],
            "failed_tasks": metrics["failed_tasks"],
            "total_execution_time": metrics["total_execution_time"],
            "constellation_count": metrics["constellation_count"],
        }
    }
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Metrics exported to: {output_file}")
```

---

## 🎓 Best Practices

### 1. Session ID Naming

Use descriptive session IDs for easier analysis:

```python
# ✅ Good: Descriptive session ID
session_id = f"galaxy_session_{task_type}_{timestamp}"

# ❌ Bad: Generic session ID
session_id = "session_1"
```

### 2. Metrics Export

Export metrics immediately after execution:

```python
try:
    await orchestrator.execute_constellation(constellation)
finally:
    # Always export metrics, even if execution failed
    metrics = metrics_observer.get_metrics()
    export_metrics(metrics, "results/metrics.json")
```

### 3. Memory Management

Clear large timing dictionaries for long-running sessions:

```python
# After processing metrics
metrics_observer.metrics["task_timings"].clear()
metrics_observer.metrics["constellation_timings"].clear()
```

---

## 🔗 Related Documentation

- **[Observer System Overview](overview.md)** — Architecture and design
- **[Event System Core](event_system.md)** — Event types and EventBus

!!! note "Additional Resources"
    For information on constellation execution and orchestration, see the constellation orchestrator documentation in `galaxy/constellation/orchestrator/`.

---

## 📋 Summary

The Session Metrics Observer:

- **Collects** comprehensive performance metrics
- **Tracks** task and constellation execution times
- **Monitors** modification patterns
- **Computes** statistical summaries
- **Exports** data for analysis

This observer is essential for performance evaluation, bottleneck identification, and research analysis of Galaxy's constellation execution.
