# Task Constellation — Overview

<div align="center">
  <img src="../../img/task_constellation.png" alt="Task Constellation DAG Structure" style="max-width: 90%; height: auto; margin: 20px 0;">
  <p><em>Example of a Task Constellation illustrating both sequential and parallel dependencies</em></p>
</div>

---

## 🌌 Introduction

The **Task Constellation** is the central abstraction in UFO³ Galaxy that captures the concurrent and asynchronous structure of distributed task execution. It provides a formal, directed acyclic graph (DAG) representation of complex workflows, enabling consistent scheduling, fault-tolerant orchestration, and runtime dynamism across heterogeneous devices.

At its core, a Task Constellation decomposes complex user requests into interdependent subtasks connected through explicit dependency edges. This formalism not only enables correct distributed execution but also supports runtime adaptation—allowing new tasks or dependencies to be introduced as the workflow evolves.

---

## 🎯 Core Components

The Task Constellation framework consists of four primary components:

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **[TaskStar](task_star.md)** | Atomic execution unit | Self-contained task with description, device assignment, execution state, dependencies |
| **[TaskStarLine](task_star_line.md)** | Dependency relationship | Directed edge with conditional logic, success-only, or unconditional execution |
| **[TaskConstellation](task_constellation.md)** | DAG orchestrator | Complete workflow graph with validation, scheduling, and dynamic modification |
| **[ConstellationEditor](constellation_editor.md)** | Interactive editor | Command pattern-based interface with undo/redo for safe constellation manipulation |

---

## 📐 Formal Model

### Mathematical Foundation

A Task Constellation $\mathcal{C}$ is formally defined as a directed acyclic graph (DAG):

$$
\mathcal{C} = (\mathcal{T}, \mathcal{E})
$$

where:
- $\mathcal{T}$ is the set of all **TaskStars** (task nodes)
- $\mathcal{E}$ is the set of **TaskStarLines** (dependency edges)

### TaskStar Representation

Each TaskStar $t_i \in \mathcal{T}$ is defined as:

$$
t_i = (\text{name}_i, \text{description}_i, \text{device}_i, \text{tips}_i, \text{status}_i, \text{dependencies}_i)
$$

**Components:**
- **name**: Unique identifier for the task
- **description**: Natural-language specification sent to the device agent
- **device**: Identifier of the device agent responsible for execution
- **tips**: Guidance list to help the device agent complete the task
- **status**: Current execution state (pending, running, completed, failed, cancelled)
- **dependencies**: References to prerequisite tasks that must complete first

### TaskStarLine Representation

Each TaskStarLine $e_{i \rightarrow j} \in \mathcal{E}$ represents a dependency from task $t_i$ to task $t_j$:

$$
e_{i \rightarrow j} = (\text{from\_task}_i, \text{to\_task}_j, \text{type}, \text{description})
$$

**Dependency Types:**

| Type | Behavior |
|------|----------|
| **Unconditional** | $t_j$ always waits for $t_i$ to complete |
| **Success-only** | $t_j$ proceeds only if $t_i$ succeeds |
| **Completion-only** | $t_j$ proceeds when $t_i$ completes (regardless of success/failure) |
| **Conditional** | $t_j$ proceeds based on a user-defined or runtime condition |

---

## ✨ Key Advantages

### 1. Explicit Task Ordering
Task dependencies are explicitly captured in the DAG structure, ensuring correctness across distributed execution without ambiguity.

### 2. Natural Parallelism
The DAG topology naturally exposes parallelizable tasks, enabling efficient concurrent execution across heterogeneous devices.

### 3. Runtime Dynamism
Unlike static DAG schedulers, Task Constellations are **mutable objects**. Tasks and dependency edges can be:
- **Added**: Introduce new subtasks or diagnostic tasks
- **Removed**: Prune completed or redundant nodes
- **Modified**: Rewire dependencies, update conditions, change device assignments

This enables adaptive execution without restarting the entire workflow.

### 4. Formal Guarantees
The DAG representation provides formal properties:
- **Acyclicity**: No circular dependencies
- **Causal consistency**: Execution respects logical ordering
- **Safe concurrency**: Parallel execution without race conditions

---

## 🔄 Lifecycle States

The Task Constellation progresses through several states during its lifecycle:

```mermaid
stateDiagram-v2
    [*] --> CREATED: Initialize
    CREATED --> READY: Add tasks & dependencies
    READY --> EXECUTING: Start execution
    EXECUTING --> EXECUTING: Tasks running
    EXECUTING --> COMPLETED: All tasks succeed
    EXECUTING --> FAILED: All tasks fail
    EXECUTING --> PARTIALLY_FAILED: Some succeed, some fail
    COMPLETED --> [*]
    FAILED --> [*]
    PARTIALLY_FAILED --> [*]
```

| State | Description |
|-------|-------------|
| **CREATED** | Constellation initialized, no tasks added |
| **READY** | Tasks and dependencies configured, ready to execute |
| **EXECUTING** | At least one task is running or completed |
| **COMPLETED** | All tasks completed successfully |
| **FAILED** | All tasks failed |
| **PARTIALLY_FAILED** | Some tasks succeeded, some failed |

---

## 📊 DAG Metrics

### Parallelism Analysis

The Task Constellation provides several metrics to analyze workflow parallelism:

#### Critical Path Length ($L$)
The longest serial dependency chain in the constellation:

$$
L = \max_{p \in \text{paths}} |p|
$$

where $|p|$ is the length of path $p$ from any root to any leaf node.

#### Total Work ($W$)
Sum of all task execution durations:

$$
W = \sum_{t_i \in \mathcal{T}} \text{duration}(t_i)
$$

#### Parallelism Ratio ($P$)
Measure of achievable parallelism:

$$
P = \frac{W}{L}
$$

- $P = 1$: Completely serial execution
- $P > 1$: Parallel execution possible
- Higher $P$ indicates more parallelism

#### Maximum Width
Maximum number of tasks that can execute concurrently:

$$
\text{MaxWidth} = \max_{\text{level}} |\text{tasks at level}|
$$

!!!info "Calculation Modes"
    The constellation supports two calculation modes:
    
    - **Node Count Mode**: Uses task counts when execution is incomplete
    - **Actual Time Mode**: Uses real execution durations when all tasks are terminal

---

## 🛠️ Core Operations

### DAG Construction

```python
from galaxy.constellation import TaskConstellation, TaskStar, TaskStarLine

# Create constellation
constellation = TaskConstellation(name="my_workflow")

# Add tasks
task_a = TaskStar(name="task_a", description="Checkout code on laptop")
task_b = TaskStar(name="task_b", description="Build on GPU server")
task_c = TaskStar(name="task_c", description="Deploy to staging")

constellation.add_task(task_a)
constellation.add_task(task_b)
constellation.add_task(task_c)

# Add dependencies
dep_ab = TaskStarLine.create_success_only(
    from_task_id=task_a.task_id,
    to_task_id=task_b.task_id,
    description="Build depends on successful checkout"
)

dep_bc = TaskStarLine.create_unconditional(
    from_task_id=task_b.task_id,
    to_task_id=task_c.task_id,
    description="Deploy after build"
)

constellation.add_dependency(dep_ab)
constellation.add_dependency(dep_bc)
```

### DAG Validation

```python
# Validate structure
is_valid, errors = constellation.validate_dag()
if not is_valid:
    print(f"Validation errors: {errors}")

# Check for cycles
has_cycles = constellation.has_cycle()

# Get topological order
order = constellation.get_topological_order()
print(f"Execution order: {order}")
```

### Parallelism Analysis

```python
# Get parallelism metrics
metrics = constellation.get_parallelism_metrics()

print(f"Critical Path Length: {metrics['critical_path_length']}")
print(f"Total Work: {metrics['total_work']}")
print(f"Parallelism Ratio: {metrics['parallelism_ratio']}")
print(f"Critical Path: {metrics['critical_path_tasks']}")

# Get maximum width
max_width = constellation.get_max_width()
print(f"Maximum concurrent tasks: {max_width}")
```

---

## 🔧 Dynamic Modification

### Safe Editing with ConstellationEditor

```python
from galaxy.constellation.editor import ConstellationEditor

# Create editor with undo/redo support
editor = ConstellationEditor(constellation)

# Add a new diagnostic task
diagnostic_task = editor.create_and_add_task(
    task_id="diag_1",
    description="Check server health",
    device_type="LINUX"
)

# Add conditional dependency
editor.create_and_add_dependency(
    from_task_id=task_b.task_id,
    to_task_id=diagnostic_task.task_id,
    dependency_type="CONDITIONAL",
    condition_description="Run diagnostic if build fails"
)

# Undo if needed
if something_wrong:
    editor.undo()

# Get modifiable components
modifiable_tasks = constellation.get_modifiable_tasks()
modifiable_deps = constellation.get_modifiable_dependencies()
```

!!!warning "Modification Safety"
    Tasks and dependencies can only be modified if they are in `PENDING` or `WAITING_DEPENDENCY` status. Running or completed tasks cannot be modified to ensure execution consistency.

---

## 📈 Example Workflows

### Sequential Workflow

```
A → B → C
```

- **Parallelism Ratio**: 1.0 (completely serial)
- **Maximum Width**: 1

### Parallel Workflow

```
    ┌─ B ─┐
A ──┤     ├─ D
    └─ C ─┘
```

- **Parallelism Ratio**: 2.0 (B and C can run in parallel)
- **Maximum Width**: 2

### Complex Workflow

```
A ──┬─ B ─┬─ D ─┐
    │     │     ├─ F
    └─ C ─┴─ E ─┘
```

- **Parallelism Ratio**: ~1.67
- **Maximum Width**: 3 (B, C, E can run concurrently after A completes)

---

## 🎨 Visualization

The Task Constellation provides multiple visualization modes:

### Overview Mode
High-level constellation structure with task counts and state

### Topology Mode
DAG graph showing task relationships and dependencies

### Details Mode
Detailed task information including execution times and status

### Execution Mode
Real-time execution flow with progress tracking

```python
# Display constellation
constellation.display_dag(mode="overview")  # or "topology", "details", "execution"
```

---

## 📚 Component Documentation

Explore detailed documentation for each component:

<div class="grid cards" markdown>

-   :material-star: **[TaskStar](task_star.md)**

    ---
    
    Atomic execution units representing individual tasks in the constellation

-   :material-connection: **[TaskStarLine](task_star_line.md)**

    ---
    
    Dependency relationships connecting tasks with conditional logic

-   :material-graph: **[TaskConstellation](task_constellation.md)**

    ---
    
    Complete DAG orchestrator managing workflow execution and coordination

-   :material-pencil: **[ConstellationEditor](constellation_editor.md)**

    ---
    
    Interactive editor with command pattern and undo/redo capabilities

</div>

---

## 🔬 Research Background

The Task Constellation model is grounded in formal DAG theory and distributed systems research. Key properties include:

- **Acyclicity guarantees** through Kahn's algorithm
- **Topological ordering** for consistent execution
- **Critical path analysis** for performance optimization
- **Dynamic graph evolution** without compromising consistency

For detailed research context, see the [UFO³ Research Paper](https://arxiv.org/) *(Coming Soon)*.

---

## 💡 Best Practices

!!!tip "Designing Effective Constellations"
    1. **Keep tasks atomic**: Each TaskStar should represent a single, well-defined operation
    2. **Minimize dependencies**: Reduce unnecessary dependencies to maximize parallelism
    3. **Use appropriate dependency types**: Choose conditional dependencies for error handling
    4. **Validate early**: Run `validate_dag()` before execution
    5. **Monitor metrics**: Track parallelism ratio to optimize workflow design

!!!example "Common Patterns"
    - **Fan-out**: One task spawns multiple independent parallel tasks
    - **Fan-in**: Multiple parallel tasks converge to a single task
    - **Pipeline**: Sequential stages with parallel tasks within each stage
    - **Conditional branching**: Use conditional dependencies for error handling paths

---

## 🚀 Next Steps

- Learn about **[TaskStar](task_star.md)** — Atomic task execution units
- Explore **[TaskStarLine](task_star_line.md)** — Dependency relationships
- Master **[TaskConstellation](task_constellation.md)** — DAG orchestration
- Try **[ConstellationEditor](constellation_editor.md)** — Interactive editing

---

<div align="center">
  <p><em>Task Constellation — The formal foundation of distributed workflow orchestration</em></p>
</div>
