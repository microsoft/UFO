# Galaxy Trajectory Report

## Overview

The **Galaxy Trajectory Report** (`output.md`) is an automatically generated comprehensive execution log that documents the complete lifecycle of a multi-device task execution session in Galaxy. This human-readable Markdown report provides step-by-step visualization of constellation evolution, task execution, and device coordination.

### Report Location

After each Galaxy session completes, the trajectory report is automatically generated:

```
logs/galaxy/<session_name>/output.md
logs/galaxy/<session_name>/topology_images/  # DAG visualizations
```

**Example:**
```
logs/galaxy/request_20251111_140216_1/
├── output.md                    # Main trajectory report
├── response.log                 # Raw JSONL execution log
├── request.log                  # Request details  
├── evaluation.log               # Optional evaluation
├── result.json                  # Performance metrics
└── topology_images/             # Generated DAG topology graphs
    ├── step1_after_constellation_xxx.png
    ├── step2_after_constellation_xxx.png
    └── step999_final_constellation_xxx.png
```

## Report Structure

### 1. Executive Summary

High-level session overview:

```markdown
## Executive Summary

- **User Request**: type hi on all linux and write results to windows notepad
- **Total Steps**: 4
- **Total Time**: 31.54s
```

**Components:**
- **User Request**: Original natural language task description
- **Total Steps**: Number of orchestration steps (DAG creation + execution rounds)
- **Total Time**: End-to-end session duration in seconds

### 2. Step-by-Step Execution

Detailed breakdown of each orchestration step with:

#### Step Metadata

```markdown
### Step 2

- **Agent**: constellation_agent (ConstellationAgent)
- **Status**: CONTINUE
- **Round**: 0 | **Round Step**: 0
- **Execution Time**: 9.27s
- **Time Breakdown**:
  - LLM_INTERACTION: 8.96s
  - ACTION_EXECUTION: 0.29s
  - MEMORY_UPDATE: 0.00s
```

**Fields:**
- **Agent**: Agent name and type (ConstellationAgent for orchestration)
- **Status**: Step outcome (`CONTINUE`, `FINISH`, `ERROR`)
- **Round/Round Step**: ReAct iteration counters
- **Execution Time**: Total step duration
- **Time Breakdown**: Profiling data for LLM calls, action execution, memory updates

#### Actions Performed

Documents agent actions with collapsible argument details:

```markdown
#### Actions Performed

**Function**: `build_constellation`

<details>
<summary>Arguments (click to expand)</summary>

```json
{
  "config": {
    "constellation_id": "constellation_xxx",
    "tasks": { ... },
    "dependencies": { ... }
  }
}
```

</details>
```

**Common Functions:**
- `build_constellation`: Initial DAG creation
- `edit_constellation`: Dynamic DAG modification
- `execute_constellation`: Trigger task execution

#### Constellation Evolution

Visualizes DAG state changes with interactive topology graphs:

```markdown
#### Constellation Evolution

<details>
<summary>Constellation AFTER (click to expand)</summary>

**Constellation ID**: constellation_bcd1726e_20251105_134526
**State**: created

##### Dependency Graph (Topology)

<img src="topology_images/step2_after_constellation_xxx.png" width="600">

##### Task Summary Table

| Task ID | Name | Status | Device | Duration |
|---------|------|--------|--------|----------|
| task-1 | Type hi on linux_agent_1 | pending | linux_agent_1 | N/A |
| task-2 | Type hi on linux_agent_2 | pending | linux_agent_2 | N/A |
| task-3 | Type hi on linux_agent_3 | pending | linux_agent_3 | N/A |
```

**Topology Visualization Features:**
- **Color-coded nodes** by task status:
  - 🟢 Green: Completed
  - 🔵 Cyan: Running
  - ⚫ Gray: Pending
  - 🔴 Red: Failed/Error
- **Edge styles** for dependencies:
  - Solid green: Satisfied dependencies
  - Dashed orange: Pending dependencies
- **Automatic layout** with hierarchical spring algorithm
- **Legend** showing node/edge meanings

##### Detailed Task Information

Comprehensive task metadata with execution details:

```markdown
#### Task task-1: Type hi on linux_agent_1

- **Status**: completed
- **Target Device**: linux_agent_1
- **Priority**: 2
- **Description**: On device linux_agent_1 (Linux), open a terminal and execute the command: echo 'hi'. Return the output text.
- **Tips**:
  - Ensure CLI access is available.
  - Expected textual result: Return the exact output of the command, which should be 'hi'.
- **Result**: 
  ```
  hi
  ```
- **Started**: 2025-11-05T05:45:26.395208+00:00
- **Ended**: 2025-11-05T05:45:42.981859+00:00
- **Duration**: 16.59s
```

**Task Fields:**
- **Status**: Current execution state (`pending`, `running`, `completed`, `failed`, `cancelled`)
- **Target Device**: Assigned device agent ID
- **Priority**: Task scheduling priority (1=HIGH, 2=MEDIUM, 3=LOW)
- **Description**: Natural language task specification for device agent
- **Tips**: Execution hints and expected output guidance
- **Result**: Task execution output (truncated if large)
- **Error**: Error message if task failed
- **Timing**: Start/end timestamps and duration

##### Dependency Details

Shows task relationships and satisfaction status:

```markdown
| Line ID | From Task | To Task | Type | Satisfied | Condition |
|---------|-----------|---------|------|-----------|----------|
| l1 | t1 | t4 | unconditional | [PENDING] | Output from linux_agent_1 collected successfully. |
| l2 | t2 | t4 | unconditional | [OK] | Output from linux_agent_2 collected successfully. |
```

**Dependency Types:**
- `unconditional`: Always active when source task completes
- `conditional`: Activated based on result evaluation

#### Connected Devices

Device registry snapshot at step completion:

```markdown
<details>
<summary>Connected Devices</summary>

| Device ID | OS | Status | Last Heartbeat |
|-----------|----|---------|--------------|
| windowsagent | windows | idle | 2025-11-05T05:45:43 |
| linux_agent_1 | linux | idle | 2025-11-05T05:45:43 |
| linux_agent_2 | linux | idle | 2025-11-05T05:45:43 |
| linux_agent_3 | linux | idle | 2025-11-05T05:45:43 |
```

**Device Statuses:**
- `idle`: Connected and available
- `busy`: Executing task
- `disconnected`: WebSocket connection lost

### 3. Final Constellation State

Complete final DAG with all task results:

```markdown
## Final Constellation State

**ID**: constellation_bcd1726e_20251105_134526
**State**: completed
**Created**: 2025-11-05T05:45:26.230930+00:00
**Updated**: 2025-11-05T05:45:42.981859+00:00

### Task Details
[Full task information with results]

### Task Summary Table
[Aggregated task status table]

### Final Dependency Graph
[Final topology visualization]
```

## Generation Process

### Automatic Generation

The trajectory report is generated automatically by `GalaxySession` upon completion:

```python
# galaxy/session/galaxy_session.py
async def close_session(self):
    """Generate trajectory report on session close"""
    trajectory = GalaxyTrajectory(self.log_path)
    trajectory.to_markdown(self.log_path + "output.md")
```

**Trigger Points:**
1. Normal session completion (`GalaxyClient.shutdown()`)
2. User termination (Ctrl+C in interactive mode)
3. Error-induced session end

### Manual Generation

You can regenerate reports manually using the CLI tool:

```bash
# Generate report for specific session
python -m galaxy.trajectory.generate_report logs/galaxy/test1

# Custom output path
python -m galaxy.trajectory.generate_report logs/galaxy/test1 -o custom_report.md

# Minimal report (exclude details)
python -m galaxy.trajectory.generate_report logs/galaxy/test1 \
  --no-constellation --no-tasks --no-devices
```

**CLI Options:**
- `--no-constellation`: Exclude constellation evolution details
- `--no-tasks`: Exclude detailed task information
- `--no-devices`: Exclude device connection information
- `-o, --output`: Custom output file path

### Batch Generation

Process multiple sessions at once:

```python
# galaxy/trajectory/galaxy_parser.py
if __name__ == "__main__":
    """Process all Galaxy task logs and generate markdown reports."""
    
    galaxy_logs_dir = Path("logs/galaxy")
    task_dirs = sorted([d for d in galaxy_logs_dir.iterdir() if d.is_dir()])
    
    for task_dir in task_dirs:
        trajectory = GalaxyTrajectory(str(task_dir))
        output_path = task_dir / "trajectory_report.md"
        trajectory.to_markdown(str(output_path))
```

Run batch processing:

```bash
cd c:\Users\chaoyunzhang\OneDrive - Microsoft\Desktop\research\GPTV\UFO-windows\github\saber\UFO2
python -m galaxy.trajectory.galaxy_parser
```

**Output:**
```
[BOLD BLUE] Galaxy Trajectory Parser - Batch Mode
Found 42 task directories

Processing task_1... [OK]
Processing task_2... [OK]
Processing test1... [OK]
...

=====================================================
Summary:
  Total: 42
  Success: 40
  Skipped: 2
  Failed: 0
=====================================================
```

## Programmatic Access

### Loading Trajectory Data

```python
from galaxy.trajectory import GalaxyTrajectory

# Load trajectory from log directory
trajectory = GalaxyTrajectory("logs/galaxy/test1")

# Access metadata
print(f"Request: {trajectory.request}")
print(f"Steps: {trajectory.total_steps}")
print(f"Cost: ${trajectory.total_cost:.4f}")
print(f"Time: {trajectory.total_time:.2f}s")

# Iterate through steps
for idx, step in enumerate(trajectory.step_log, 1):
    agent = step.get("agent_name")
    status = step.get("status")
    time = step.get("total_time", 0)
    print(f"Step {idx}: {agent} - {status} ({time:.2f}s)")
```

### Extracting Constellation Data

```python
# Get final constellation state
last_step = trajectory.step_log[-1]
final_constellation = trajectory._parse_constellation(
    last_step.get("constellation_after")
)

if final_constellation:
    constellation_id = final_constellation.get("constellation_id")
    state = final_constellation.get("state")
    tasks = final_constellation.get("tasks", {})
    
    print(f"Constellation {constellation_id}: {state}")
    print(f"Tasks: {len(tasks)}")
    
    # Analyze task outcomes
    completed = sum(1 for t in tasks.values() if t.get("status") == "completed")
    failed = sum(1 for t in tasks.values() if t.get("status") == "failed")
    
    print(f"Completed: {completed}/{len(tasks)}")
    print(f"Failed: {failed}/{len(tasks)}")
```

### Custom Report Generation

```python
# Generate custom report with specific options
trajectory.to_markdown(
    output_path="custom_report.md",
    include_constellation_details=True,  # Show DAG evolution
    include_task_details=True,          # Show task results
    include_device_info=False           # Hide device info
)
```

## Visualization Features

### Topology Graph Generation

The trajectory report includes dynamically generated DAG topology images:

**Implementation:**
```python
def _generate_topology_image(
    self,
    dependencies: Dict[str, Any],
    tasks: Dict[str, Any],
    constellation_id: str,
    step_number: int,
    state: str = "before"
) -> Optional[str]:
    """Generate beautiful topology graph using networkx and matplotlib"""
    
    # Create directed graph
    G = nx.DiGraph()
    
    # Add all tasks as nodes
    for task_id in tasks.keys():
        G.add_node(task_id)
    
    # Add dependency edges
    for dep in dependencies.values():
        from_task = dep["from_task_id"]
        to_task = dep["to_task_id"]
        G.add_edge(from_task, to_task)
    
    # Color nodes by status
    status_colors = {
        "completed": "#28A745",  # Green
        "running": "#17A2B8",    # Cyan
        "pending": "#6C757D",    # Gray
        "failed": "#DC3545",     # Red
    }
    
    # Generate layout and save image
    pos = nx.spring_layout(G, k=1.5, iterations=100)
    # ... [matplotlib rendering code]
```

**Graph Features:**
- **Hierarchical Layout**: Spring algorithm with optimized spacing (`k=1.5`)
- **Adaptive Node Size**: Ellipses scale with task ID length
- **Color-Coded Status**: Bootstrap-inspired color scheme
- **Edge Differentiation**: Solid (satisfied) vs dashed (pending)
- **Legend**: Automatic status and dependency type legend
- **High Quality**: 120 DPI PNG with antialiasing

### Image Organization

```
topology_images/
├── step1_after_constellation_7b3c0f47_20251104_182305.png
├── step2_before_constellation_bcd1726e_20251105_134526.png
├── step2_after_constellation_bcd1726e_20251105_134526.png
├── step3_before_constellation_bcd1726e_20251105_134526.png
├── step3_after_constellation_bcd1726e_20251105_134526.png
└── step999_final_constellation_bcd1726e_20251105_134526.png
```

**Naming Convention:**
- `step{N}_{state}_{constellation_id}.png`
- `state`: `before`, `after`, or `final`
- `step999`: Reserved for final summary graph

## Use Cases

### 1. Debugging Failed Sessions

Identify which task failed and why:

```python
trajectory = GalaxyTrajectory("logs/galaxy/failed_session")

for step in trajectory.step_log:
    constellation = trajectory._parse_constellation(step.get("constellation_after"))
    if not constellation:
        continue
    
    tasks = constellation.get("tasks", {})
    for task_id, task in tasks.items():
        if task.get("status") == "failed":
            print(f"❌ Task {task_id}: {task.get('name')}")
            print(f"   Device: {task.get('target_device_id')}")
            print(f"   Error: {task.get('error')}")
```

### 2. Performance Analysis

Correlate with `result.json` for bottleneck identification:

```python
import json

# Load trajectory for execution timeline
trajectory = GalaxyTrajectory("logs/galaxy/task_32")

# Load metrics for performance data
with open("logs/galaxy/task_32/result.json") as f:
    result = json.load(f)

metrics = result["session_results"]["metrics"]
task_stats = metrics["task_statistics"]

# Find slowest tasks
slow_tasks = [
    (tid, task.get("execution_duration", 0))
    for step in trajectory.step_log
    for tid, task in trajectory._parse_constellation(
        step.get("constellation_after")
    ).get("tasks", {}).items()
]

slow_tasks.sort(key=lambda x: x[1], reverse=True)
print(f"Top 5 slowest tasks:")
for tid, duration in slow_tasks[:5]:
    print(f"  {tid}: {duration:.2f}s")
```

### 3. Constellation Evolution Analysis

Track DAG modifications across steps:

```python
trajectory = GalaxyTrajectory("logs/galaxy/adaptive_session")

for idx, step in enumerate(trajectory.step_log, 1):
    before = trajectory._parse_constellation(step.get("constellation_before"))
    after = trajectory._parse_constellation(step.get("constellation_after"))
    
    if before and after:
        tasks_before = len(before.get("tasks", {}))
        tasks_after = len(after.get("tasks", {}))
        
        if tasks_after > tasks_before:
            print(f"Step {idx}: Added {tasks_after - tasks_before} tasks")
        elif tasks_after < tasks_before:
            print(f"Step {idx}: Removed {tasks_before - tasks_after} tasks")
```

### 4. Device Utilization Tracking

Analyze device workload distribution:

```python
trajectory = GalaxyTrajectory("logs/galaxy/multi_device")

# Count tasks per device
device_tasks = {}
for step in trajectory.step_log:
    constellation = trajectory._parse_constellation(step.get("constellation_after"))
    if not constellation:
        continue
    
    for task in constellation.get("tasks", {}).values():
        device = task.get("target_device_id")
        device_tasks[device] = device_tasks.get(device, 0) + 1

print("Task distribution:")
for device, count in sorted(device_tasks.items(), key=lambda x: x[1], reverse=True):
    print(f"  {device}: {count} tasks")
```

### 5. Session Comparison

Compare multiple sessions for regression testing:

```python
def compare_sessions(session1_path, session2_path):
    t1 = GalaxyTrajectory(session1_path)
    t2 = GalaxyTrajectory(session2_path)
    
    print(f"Session 1 vs Session 2:")
    print(f"  Steps: {t1.total_steps} vs {t2.total_steps}")
    print(f"  Time: {t1.total_time:.2f}s vs {t2.total_time:.2f}s")
    print(f"  Cost: ${t1.total_cost:.4f} vs ${t2.total_cost:.4f}")
    
    speedup = (t1.total_time - t2.total_time) / t1.total_time * 100
    print(f"  Performance: {speedup:+.1f}%")

compare_sessions("logs/galaxy/test_v1", "logs/galaxy/test_v2")
```

## Data Sources

The trajectory report aggregates data from multiple log sources:

### 1. response.log (Primary Source)

JSONL file with per-step execution records:

```json
{
  "request": "type hi on all linux devices",
  "agent_name": "constellation_agent",
  "agent_type": "ConstellationAgent",
  "status": "CONTINUE",
  "round_num": 0,
  "round_step": 0,
  "total_time": 9.27,
  "cost": 0.0042,
  "execution_times": {
    "LLM_INTERACTION": 8.96,
    "ACTION_EXECUTION": 0.29,
    "MEMORY_UPDATE": 0.00
  },
  "action": [
    {
      "function": "build_constellation",
      "arguments": { ... }
    }
  ],
  "constellation_before": "{...}",
  "constellation_after": "{...}",
  "device_info": { ... }
}
```

### 2. result.json (Performance Metrics)

Aggregated session-level metrics:

```json
{
  "session_results": {
    "request": "type hi on all linux devices",
    "status": "completed",
    "total_cost": 0.0156,
    "total_rounds": 1,
    "total_steps": 4,
    "total_time": 31.54,
    "metrics": {
      "task_statistics": { ... },
      "constellation_statistics": { ... }
    }
  }
}
```

### 3. evaluation.log (Optional)

User-provided evaluation results:

```json
{
  "task_success": true,
  "evaluation_score": 5,
  "comments": "All tasks completed successfully"
}
```

## Configuration

### Customizing Report Content

Control report verbosity via generation parameters:

```python
trajectory.to_markdown(
    output_path="output.md",
    include_constellation_details=True,  # DAG evolution (default: True)
    include_task_details=True,          # Task execution logs (default: True)
    include_device_info=True            # Device status (default: True)
)
```

**Report Size Impact:**
- Full report (all options enabled): ~200KB for 10-task session
- Minimal report (all options disabled): ~20KB
- Topology images: ~50KB each

### Topology Graph Styling

Customize graph appearance by modifying `_generate_topology_image()`:

```python
# Adjust node colors
status_colors = {
    "completed": "#28A745",  # Change to custom color
    "running": "#17A2B8",
    # ...
}

# Adjust layout parameters
pos = nx.spring_layout(
    G,
    k=1.5,        # Node spacing (higher = more spread)
    iterations=100,  # Layout quality (higher = better but slower)
    seed=42       # Deterministic layout
)

# Adjust image quality
plt.savefig(
    image_path,
    dpi=120,           # Resolution (higher = larger files)
    bbox_inches="tight",
    facecolor="white"
)
```

## Best Practices

### 1. Regular Report Review

Monitor trajectory reports to catch issues early:

```bash
# Generate reports for recent sessions
for dir in logs/galaxy/*/; do
    python -m galaxy.trajectory.generate_report "$dir"
done

# Open reports in browser for visual inspection
start logs/galaxy/test1/output.md
```

### 2. Archive Trajectory Reports

Store reports with version control for reproducibility:

```bash
# Create timestamped archive
mkdir -p trajectory_archives/$(date +%Y-%m-%d)
cp logs/galaxy/*/output.md trajectory_archives/$(date +%Y-%m-%d)/
cp logs/galaxy/*/result.json trajectory_archives/$(date +%Y-%m-%d)/
```

### 3. Automated Analysis

Integrate trajectory parsing into CI/CD pipelines:

```python
# test/analyze_trajectory.py
def validate_trajectory(log_dir):
    trajectory = GalaxyTrajectory(log_dir)
    
    # Check for failures
    for step in trajectory.step_log:
        if step.get("status") == "ERROR":
            raise AssertionError(f"Session failed at step {step.get('_line_number')}")
    
    # Check performance thresholds
    if trajectory.total_time > 60.0:
        print(f"WARNING: Session took {trajectory.total_time:.2f}s (>60s threshold)")
    
    return True
```

### 4. Compare Before/After States

Use constellation evolution to verify correctness:

```python
# Verify DAG grows monotonically (no premature task deletion)
trajectory = GalaxyTrajectory("logs/galaxy/session")

prev_task_count = 0
for step in trajectory.step_log:
    constellation = trajectory._parse_constellation(step.get("constellation_after"))
    if constellation:
        task_count = len(constellation.get("tasks", {}))
        if task_count < prev_task_count:
            print(f"WARNING: Task count decreased from {prev_task_count} to {task_count}")
        prev_task_count = task_count
```

## Related Documentation

- **[Performance Metrics](./performance_metrics.md)** - Quantitative session analysis with `result.json`
- **[Result JSON Reference](./result_json.md)** - Complete `result.json` schema documentation
- **[Galaxy Overview](../overview.md)** - Main Galaxy framework documentation
- **[Constellation Orchestrator](../constellation_orchestrator/overview.md)** - DAG execution engine
- **[Task Constellation](../constellation/overview.md)** - DAG data structure and validation

## Troubleshooting

### Empty or Missing Report

**Problem:** `output.md` not generated after session

**Solutions:**

1. Check for `response.log` existence:
   ```bash
   ls logs/galaxy/<session_name>/response.log
   ```

2. Manually trigger generation:
   ```bash
   python -m galaxy.trajectory.generate_report logs/galaxy/<session_name>
   ```

3. Verify session closed properly (check for exception in terminal)

### Parse Errors in Report

**Problem:** `⚠️ Parse Error` warnings in report

**Cause:** Legacy log format with serialization bugs (tasks as Python strings instead of JSON)

**Solution:** This is a known issue fixed in current versions. Reports will display:
```markdown
##### ⚠️ Parse Error

**Error Type**: `legacy_serialization_bug`
**Message**: Tasks field contains Python object representations (not pure JSON). 
This is due to a serialization bug in older versions.
```

**Workaround:** Re-run session with updated codebase to generate proper logs.

### Missing Topology Images

**Problem:** Broken image links in report

**Solutions:**

1. Check `topology_images/` directory exists:
   ```bash
   ls logs/galaxy/<session_name>/topology_images/
   ```

2. Verify matplotlib backend:
   ```python
   import matplotlib
   matplotlib.use("Agg")  # Non-interactive backend required
   ```

3. Regenerate report to recreate images:
   ```bash
   python -m galaxy.trajectory.generate_report logs/galaxy/<session_name>
   ```

### Large Report Files

**Problem:** `output.md` exceeds 10MB

**Solutions:**

1. Generate minimal report:
   ```bash
   python -m galaxy.trajectory.generate_report logs/galaxy/<session_name> \
     --no-constellation --no-tasks
   ```

2. Reduce topology image quality (edit `galaxy_parser.py`):
   ```python
   plt.savefig(image_path, dpi=80)  # Lower DPI
   ```

3. Archive and compress:
   ```bash
   gzip logs/galaxy/<session_name>/output.md
   ```

## API Reference

### GalaxyTrajectory Class

```python
class GalaxyTrajectory:
    """Parser for Galaxy agent logs with constellation visualization"""
    
    def __init__(self, folder_path: str) -> None:
        """
        Initialize trajectory parser.
        
        Args:
            folder_path: Path to Galaxy log directory (e.g., logs/galaxy/task_1)
        
        Raises:
            ValueError: If response.log file not found
        """
    
    @property
    def step_log(self) -> List[Dict[str, Any]]:
        """Get all step logs from response.log"""
    
    @property
    def evaluation_log(self) -> Dict[str, Any]:
        """Get evaluation results from evaluation.log"""
    
    @property
    def request(self) -> Optional[str]:
        """Get original user request"""
    
    @property
    def total_steps(self) -> int:
        """Get total number of steps"""
    
    @property
    def total_cost(self) -> float:
        """Calculate total LLM cost"""
    
    @property
    def total_time(self) -> float:
        """Calculate total execution time"""
    
    def to_markdown(
        self,
        output_path: str,
        include_constellation_details: bool = True,
        include_task_details: bool = True,
        include_device_info: bool = True
    ) -> None:
        """
        Export trajectory to Markdown file.
        
        Args:
            output_path: Path to save markdown file
            include_constellation_details: Include DAG evolution details
            include_task_details: Include task execution logs
            include_device_info: Include device status information
        """
```

---

**Next Steps:**
- Combine trajectory reports with `result.json` metrics for comprehensive analysis
- Automate report generation in CI/CD pipelines
- Visualize execution timelines with custom scripts
- Compare session trajectories for performance regression testing
