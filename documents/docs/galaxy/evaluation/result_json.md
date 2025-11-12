# Result JSON Format Reference

Galaxy automatically saves comprehensive execution results to `result.json` after each session completes. This file contains the complete execution history, performance metrics, constellation statistics, and final outcomes of multi-device workflows.

## Overview

The `result.json` file provides a **complete audit trail** and **performance analysis** of Galaxy session execution. It combines session metadata, execution metrics, constellation statistics, and final results into a single structured document.

### File Location

```
logs/galaxy/<task_name>/result.json
```

**Example:**

```
logs/galaxy/request_20251111_140216_1/result.json
```

## File Structure

### Top-Level Schema

```json
{
    "session_name": "string",           // Unique session identifier
    "request": "string",                // Original user request
    "task_name": "string",              // Task identifier
    "status": "string",                 // Session outcome
    "execution_time": "float",          // Total duration (seconds)
    "rounds": "integer",                // Number of orchestration rounds
    "start_time": "string",             // ISO 8601 start timestamp
    "end_time": "string",               // ISO 8601 end timestamp
    "trajectory_path": "string",        // Path to session logs
    "session_results": { /* ... */ },   // Detailed execution results
    "constellation": { /* ... */ }      // Final constellation summary
}
```

---

## Field Reference

### Session Metadata

#### `session_name` (string)

Unique identifier for the Galaxy session, generated automatically.

**Format:** `galaxy_session_YYYYMMDD_HHMMSS`

**Example:**

```json
{
    "session_name": "galaxy_session_20251025_183449"
}
```

#### `request` (string)

The original natural language request provided by the user.

**Example:**

```json
{
    "request": "For all linux, get their disk usage statistics. Then, from Windows browser, search for the top 3 recommended ways to reduce high disk usage for Linux systems and document these in a report on notepad."
}
```

#### `task_name` (string)

Internal task identifier assigned to the session.

**Format:** `task_<number>` or custom name

**Example:**

```json
{
    "task_name": "task_32"
}
```

#### `status` (string)

Final session outcome status.

**Possible Values:**

| Status | Description | Meaning |
|--------|-------------|---------|
| `"completed"` | Session finished successfully | All tasks completed |
| `"failed"` | Session encountered unrecoverable error | Task failure or system error |
| `"timeout"` | Session exceeded time limit | Max execution time reached |
| `"cancelled"` | Session manually stopped by user | User interruption |

**Example:**

```json
{
    "status": "completed"
}
```

#### `execution_time` (float)

Total session duration in seconds, from start to completion.

**Example:**

```json
{
    "execution_time": 684.864645
}
```

#### `rounds` (integer)

Number of orchestration rounds executed during the session. Each round represents a full constellation creation or modification cycle.

**Example:**

```json
{
    "rounds": 1
}
```

!!! tip "Understanding Rounds"
    Multiple rounds indicate a complex request requiring iterative refinement. Most sessions complete in 1-2 rounds.

#### `start_time` (string)

ISO 8601 formatted timestamp when the session started.

**Format:** `YYYY-MM-DDTHH:MM:SS.ssssss`

**Example:**

```json
{
    "start_time": "2025-10-25T18:34:52.641877"
}
```

#### `end_time` (string)

ISO 8601 formatted timestamp when the session completed.

**Example:**

```json
{
    "end_time": "2025-10-25T18:46:17.506522"
}
```

#### `trajectory_path` (string)

File system path to the directory containing all session logs and artifacts.

**Example:**

```json
{
    "trajectory_path": "logs/galaxy/request_20251111_140216_1/"
}
```

**Directory Contents:**

```
logs/galaxy/request_20251111_140216_1/
├── result.json                # This file
├── output.md                  # Trajectory report
├── response.log               # JSONL execution log
├── request.log                # Request details
├── evaluation.log             # Optional evaluation
└── topology_images/           # DAG visualizations
    └── *.png
```

### Session Results

The `session_results` object contains detailed execution information and metrics.

```json
{
    "session_results": {
        "total_execution_time": "float",
        "final_constellation_stats": { /* ... */ },
        "status": "string",
        "final_results": [ /* ... */ ],
        "metrics": { /* ... */ }
    }
}
```

#### `total_execution_time` (float)

Total time spent executing tasks (excludes planning/overhead).

**Example:**

```json
{
    "total_execution_time": 684.8532314300537
}
```

#### `final_constellation_stats` (object)

Statistics for the final constellation after all tasks completed.

**Schema:**

```json
{
    "constellation_id": "string",               // Unique constellation ID
    "name": "string",                           // Constellation name
    "state": "string",                          // "completed", "failed", "executing"
    "total_tasks": "integer",                   // Total task count
    "total_dependencies": "integer",            // Dependency count
    "task_status_counts": {                     // Task states
        "completed": "integer",
        "failed": "integer",
        "pending": "integer",
        "running": "integer"
    },
    "longest_path_length": "integer",           // Max depth (levels)
    "longest_path_tasks": ["string"],           // Task IDs in longest path
    "max_width": "integer",                     // Max concurrent tasks
    "critical_path_length": "float",            // Critical path duration (seconds)
    "total_work": "float",                      // Sum of all task durations
    "parallelism_ratio": "float",               // total_work / critical_path_length
    "parallelism_calculation_mode": "string",   // "actual_time" or "node_count"
    "critical_path_tasks": ["string"],          // Task IDs in critical path
    "execution_duration": "float",              // Constellation total duration
    "created_at": "string",                     // ISO 8601 creation timestamp
    "updated_at": "string"                      // ISO 8601 last update timestamp
}
```

**Example:**

```json
{
    "final_constellation_stats": {
        "constellation_id": "constellation_b0864385_20251025_183508",
        "name": "constellation_b0864385_20251025_183508",
        "state": "completed",
        "total_tasks": 5,
        "total_dependencies": 4,
        "task_status_counts": {
            "completed": 5
        },
        "longest_path_length": 2,
        "longest_path_tasks": ["t1", "t5"],
        "max_width": 4,
        "critical_path_length": 638.134632,
        "total_work": 674.4709760000001,
        "parallelism_ratio": 1.0569415013350976,
        "parallelism_calculation_mode": "actual_time",
        "critical_path_tasks": ["t4", "t5"],
        "execution_duration": null,
        "created_at": "2025-10-25T10:35:08.777663+00:00",
        "updated_at": "2025-10-25T10:46:08.625716+00:00"
    }
}
```

**Key Metrics:**

| Field | Description | Use Case |
|-------|-------------|----------|
| `critical_path_length` | Minimum possible execution time | Theoretical performance limit |
| `total_work` | Total computational effort | Resource utilization |
| `parallelism_ratio` | Efficiency of parallel execution | Optimization target |
| `max_width` | Peak concurrent tasks | Capacity planning |

!!! note "Parallelism Ratio Interpretation"
    - **1.0**: Sequential execution (no parallelism)
    - **1.5**: 50% time reduction through parallelism
    - **2.0**: 2x speedup from parallel execution
    - **>2.0**: High parallelism efficiency

#### `status` (string)

Final status from ConstellationAgent.

**Possible Values:**

- `"FINISH"`: Successful completion
- `"FAIL"`: Execution failure
- `"PENDING"`: Incomplete (should not appear in final result)

**Example:**

```json
{
    "status": "FINISH"
}
```

#### `final_results` (array)

Array of result objects containing request-result pairs.

**Schema:**

```json
{
    "final_results": [
        {
            "request": "string",    // User request (may be same as top-level)
            "result": "string"      // Final outcome description
        }
    ]
}
```

**Example:**

```json
{
    "final_results": [
        {
            "request": "For all linux, get their disk usage statistics. Then, from Windows browser, search for the top 3 recommended ways to reduce high disk usage for Linux systems and document these in a report on notepad.",
            "result": "User request fully completed. Final artifact: 'Documents\\\\Linux_Disk_Usage_Report.txt' on windows_agent, containing full disk usage summaries for linux_agent_1, linux_agent_2, and linux_agent_3, and top 3 recommendations for reducing high disk usage (from Tecmint). All tasks completed successfully; no further constellation updates required."
        }
    ]
}
```

#### `metrics` (object)

Comprehensive performance metrics collected during execution. See **[Performance Metrics](./performance_metrics.md)** for detailed documentation.

**Schema:**

```json
{
    "metrics": {
        "session_id": "string",
        "task_count": "integer",
        "completed_tasks": "integer",
        "failed_tasks": "integer",
        "total_execution_time": "float",
        "task_timings": { /* ... */ },
        "constellation_count": "integer",
        "completed_constellations": "integer",
        "failed_constellations": "integer",
        "total_constellation_time": "float",
        "constellation_timings": { /* ... */ },
        "constellation_modifications": { /* ... */ },
        "task_statistics": { /* ... */ },
        "constellation_statistics": { /* ... */ },
        "modification_statistics": { /* ... */ }
    }
}
```

**See:** [Performance Metrics Documentation](./performance_metrics.md)

### Constellation Summary

The `constellation` object provides a high-level summary of the final constellation.

**Schema:**

```json
{
    "constellation": {
        "id": "string",                // Constellation ID
        "name": "string",              // Constellation name
        "task_count": "integer",       // Total tasks
        "dependency_count": "integer", // Total dependencies
        "state": "string"              // Final state
    }
}
```

**Example:**

```json
{
    "constellation": {
        "id": "constellation_b0864385_20251025_183508",
        "name": "constellation_b0864385_20251025_183508",
        "task_count": 5,
        "dependency_count": 4,
        "state": "completed"
    }
}
```

---

## Complete Example

Here's a complete `result.json` file from an actual Galaxy session:

```json
{
  "session_name": "galaxy_session_20251025_183449",
  "request": "For all linux, get their disk usage statistics. Then, from Windows browser, search for the top 3 recommended ways to reduce high disk usage for Linux systems and document these in a report on notepad.",
  "task_name": "task_32",
  "status": "completed",
  "execution_time": 684.864645,
  "rounds": 1,
  "start_time": "2025-10-25T18:34:52.641877",
  "end_time": "2025-10-25T18:46:17.506522",
  "trajectory_path": "logs/galaxy/task_32/",
  
  "session_results": {
    "total_execution_time": 684.8532314300537,
    
    "final_constellation_stats": {
      "constellation_id": "constellation_b0864385_20251025_183508",
      "name": "constellation_b0864385_20251025_183508",
      "state": "completed",
      "total_tasks": 5,
      "total_dependencies": 4,
      "task_status_counts": {
        "completed": 5
      },
      "longest_path_length": 2,
      "longest_path_tasks": ["t1", "t5"],
      "max_width": 4,
      "critical_path_length": 638.134632,
      "total_work": 674.4709760000001,
      "parallelism_ratio": 1.0569415013350976,
      "parallelism_calculation_mode": "actual_time",
      "critical_path_tasks": ["t4", "t5"],
      "execution_duration": null,
      "created_at": "2025-10-25T10:35:08.777663+00:00",
      "updated_at": "2025-10-25T10:46:08.625716+00:00"
    },
    
    "status": "FINISH",
    
    "final_results": [
      {
        "request": "For all linux, get their disk usage statistics. Then, from Windows browser, search for the top 3 recommended ways to reduce high disk usage for Linux systems and document these in a report on notepad.",
        "result": "User request fully completed. Final artifact: 'Documents\\\\Linux_Disk_Usage_Report.txt' on windows_agent, containing full disk usage summaries for linux_agent_1, linux_agent_2, and linux_agent_3, and top 3 recommendations for reducing high disk usage (from Tecmint). All tasks completed successfully; no further constellation updates required."
      }
    ],
    
    "metrics": {
      "session_id": "galaxy_session_galaxy_session_20251025_183449_task_32",
      "task_count": 5,
      "completed_tasks": 5,
      "failed_tasks": 0,
      "total_execution_time": 674.547759771347,
      
      "task_timings": {
        "t1": {
          "start": 1761388508.9484463,
          "duration": 11.852121591567993,
          "end": 1761388520.8005679
        },
        "t2": {
          "start": 1761388508.9494512,
          "duration": 12.128723621368408,
          "end": 1761388521.0781748
        },
        "t3": {
          "start": 1761388508.9494512,
          "duration": 12.409801721572876,
          "end": 1761388521.359253
        },
        "t4": {
          "start": 1761388508.9494512,
          "duration": 269.1103162765503,
          "end": 1761388778.0597675
        },
        "t5": {
          "start": 1761388799.57892,
          "duration": 369.0467965602875,
          "end": 1761389168.6257164
        }
      },
      
      "constellation_count": 1,
      "completed_constellations": 1,
      "failed_constellations": 0,
      "total_constellation_time": 0.0,
      
      "task_statistics": {
        "total_tasks": 5,
        "completed_tasks": 5,
        "failed_tasks": 0,
        "success_rate": 1.0,
        "failure_rate": 0.0,
        "average_task_duration": 134.9095519542694,
        "min_task_duration": 11.852121591567993,
        "max_task_duration": 369.0467965602875,
        "total_task_execution_time": 674.547759771347
      },
      
      "constellation_statistics": {
        "total_constellations": 1,
        "completed_constellations": 1,
        "failed_constellations": 0,
        "success_rate": 1.0,
        "average_constellation_duration": 659.9815917015076,
        "min_constellation_duration": 659.9815917015076,
        "max_constellation_duration": 659.9815917015076,
        "total_constellation_time": 0.0,
        "average_tasks_per_constellation": 5.0
      },
      
      "modification_statistics": {
        "total_modifications": 4,
        "constellations_modified": 1,
        "average_modifications_per_constellation": 4.0,
        "max_modifications_for_single_constellation": 4,
        "most_modified_constellation": "constellation_b0864385_20251025_183508",
        "modifications_per_constellation": {
          "constellation_b0864385_20251025_183508": 4
        },
        "modification_types_breakdown": {
          "Edited by constellation_agent": 4
        }
      }
    }
  },
  
  "constellation": {
    "id": "constellation_b0864385_20251025_183508",
    "name": "constellation_b0864385_20251025_183508",
    "task_count": 5,
    "dependency_count": 4,
    "state": "completed"
  }
}
```

---

## Programmatic Access

### Reading Result JSON

```python
import json
from pathlib import Path

def load_session_result(task_name: str) -> dict:
    """
    Load Galaxy session result.
    
    :param task_name: Task identifier (e.g., "task_32")
    :return: Result dictionary
    """
    result_path = Path("logs/galaxy") / task_name / "result.json"
    
    with open(result_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Example usage
result = load_session_result("task_32")
print(f"Session: {result['session_name']}")
print(f"Status: {result['status']}")
print(f"Duration: {result['execution_time']:.2f}s")
```

### Extracting Key Information

```python
def extract_summary(result: dict) -> dict:
    """
    Extract key summary information from result.json.
    
    :param result: Result dictionary from load_session_result()
    :return: Summary dictionary
    """
    metrics = result["session_results"]["metrics"]
    task_stats = metrics["task_statistics"]
    const_stats = result["session_results"]["final_constellation_stats"]
    
    return {
        "session_name": result["session_name"],
        "request": result["request"],
        "status": result["status"],
        "total_duration": result["execution_time"],
        "task_count": task_stats["total_tasks"],
        "success_rate": task_stats["success_rate"],
        "parallelism_ratio": const_stats.get("parallelism_ratio", 1.0),
        "final_result": result["session_results"]["final_results"][0]["result"] 
                        if result["session_results"]["final_results"] else None
    }

# Example usage
result = load_session_result("task_32")
summary = extract_summary(result)

print(f"✅ Success Rate: {summary['success_rate'] * 100:.1f}%")
print(f"⏱️  Duration: {summary['total_duration']:.2f}s")
print(f"🔀 Parallelism: {summary['parallelism_ratio']:.2f}")
```

**Expected Output:**

```
✅ Success Rate: 100.0%
⏱️  Duration: 684.86s
🔀 Parallelism: 1.06
```

### Batch Analysis

```python
def analyze_multiple_sessions(log_dir: str = "logs/galaxy"):
    """
    Analyze multiple Galaxy sessions from log directory.
    
    :param log_dir: Path to Galaxy log directory
    :return: DataFrame with session analysis
    """
    import pandas as pd
    
    sessions = []
    
    for task_dir in Path(log_dir).iterdir():
        result_file = task_dir / "result.json"
        
        if result_file.exists():
            with open(result_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
                summary = extract_summary(result)
                sessions.append(summary)
    
    df = pd.DataFrame(sessions)
    
    print("📊 Session Analysis Summary:")
    print(f"   Total sessions: {len(df)}")
    print(f"   Average duration: {df['total_duration'].mean():.2f}s")
    print(f"   Average success rate: {df['success_rate'].mean() * 100:.1f}%")
    print(f"   Average parallelism: {df['parallelism_ratio'].mean():.2f}")
    
    return df

# Example usage
df = analyze_multiple_sessions()
```

### Generating Reports

```python
def generate_performance_report(task_name: str, output_file: str = "report.md"):
    """
    Generate Markdown performance report from result.json.
    
    :param task_name: Task identifier
    :param output_file: Output Markdown file path
    """
    result = load_session_result(task_name)
    metrics = result["session_results"]["metrics"]
    
    # Generate Markdown report
    report = f"""# Galaxy Session Performance Report
```

## Session Information

- **Session Name:** {result['session_name']}
- **Task Name:** {result['task_name']}
- **Status:** {result['status']}
- **Start Time:** {result['start_time']}
- **End Time:** {result['end_time']}
- **Total Duration:** {result['execution_time']:.2f}s


## Task Performance

| Metric | Value |
|--------|-------|
| Total Tasks | `{metrics['task_count']}` |
| Completed Tasks | `{metrics['completed_tasks']}` |
| Failed Tasks | `{metrics['failed_tasks']}` |
| Success Rate | `{metrics['task_statistics']['success_rate'] * 100:.1f}%` |
| Average Task Duration | `{metrics['task_statistics']['average_task_duration']:.2f}s` |
| Min Task Duration | `{metrics['task_statistics']['min_task_duration']:.2f}s` |
| Max Task Duration | `{metrics['task_statistics']['max_task_duration']:.2f}s` |

## Constellation Performance

| Metric | Value |
|--------|-------|
| Parallelism Ratio | `{result['session_results']['final_constellation_stats']['parallelism_ratio']:.2f}` |
| Critical Path Length | `{result['session_results']['final_constellation_stats']['critical_path_length']:.2f}s` |
| Total Work | `{result['session_results']['final_constellation_stats']['total_work']:.2f}s` |
| Max Width | `{result['session_results']['final_constellation_stats']['max_width']}` |


# Example usage

```python
    generate_performance_report("task_32", "task_32_report.md")
```

## Use Cases

### 1. Debugging Failed Sessions

```python
def debug_failed_session(task_name: str):
    """
    Analyze failed session for debugging.
    
    :param task_name: Task identifier
    """
    result = load_session_result(task_name)
    
    if result["status"] != "completed":
        print(f"⚠️  Session Failed: {result['status']}")
        
        metrics = result["session_results"]["metrics"]
        failed_tasks = []
        
        for task_id, timing in metrics["task_timings"].items():
            # Check if task is in failed list
            if task_id in [f"t{i}" for i in range(metrics["failed_tasks"])]:
                failed_tasks.append(task_id)
        
        if failed_tasks:
            print(f"\n❌ Failed Tasks:")
            for task_id in failed_tasks:
                print(f"   • {task_id}")
        
        # Check logs for more details
        log_dir = Path(result["trajectory_path"])
        print(f"\n📁 Check logs in: {log_dir}")
```

### 2. Comparing Session Performance

```python
def compare_sessions(task_name_1: str, task_name_2: str):
    """
    Compare performance of two Galaxy sessions.
    
    :param task_name_1: First task identifier
    :param task_name_2: Second task identifier
    """
    result1 = load_session_result(task_name_1)
    result2 = load_session_result(task_name_2)
    
    summary1 = extract_summary(result1)
    summary2 = extract_summary(result2)
    
    print(f"📊 Session Comparison:")
    print(f"\n{'Metric':<30} {task_name_1:<20} {task_name_2:<20}")
    print("-" * 70)
    print(f"{'Duration (s)':<30} {summary1['total_duration']:<20.2f} {summary2['total_duration']:<20.2f}")
    print(f"{'Task Count':<30} {summary1['task_count']:<20} {summary2['task_count']:<20}")
    print(f"{'Success Rate':<30} {summary1['success_rate']*100:<20.1f}% {summary2['success_rate']*100:<20.1f}%")
    print(f"{'Parallelism Ratio':<30} {summary1['parallelism_ratio']:<20.2f} {summary2['parallelism_ratio']:<20.2f}")
```

```python
import matplotlib.pyplot as plt
from datetime import datetime

def plot_performance_trend(log_dir: str = "logs/galaxy"):
    """
    Plot performance trends across sessions.
    
    :param log_dir: Path to Galaxy log directory
    """
    sessions = []
    
    for task_dir in sorted(Path(log_dir).iterdir()):
        result_file = task_dir / "result.json"
        
        if result_file.exists():
            with open(result_file, 'r') as f:
                result = json.load(f)
                sessions.append({
                    "timestamp": datetime.fromisoformat(result["start_time"]),
                    "duration": result["execution_time"],
                    "task_count": result["session_results"]["metrics"]["task_count"],
                    "parallelism": result["session_results"]["final_constellation_stats"].get("parallelism_ratio", 1.0)
                })
    
    if not sessions:
        print("No sessions found")
        return
    
    # Plot duration trend
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    timestamps = [s["timestamp"] for s in sessions]
    durations = [s["duration"] for s in sessions]
    parallelism = [s["parallelism"] for s in sessions]
    
    ax1.plot(timestamps, durations, marker='o')
    ax1.set_xlabel("Session Timestamp")
    ax1.set_ylabel("Duration (seconds)")
    ax1.set_title("Session Duration Trend")
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(timestamps, parallelism, marker='o', color='green')
    ax2.set_xlabel("Session Timestamp")
    ax2.set_ylabel("Parallelism Ratio")
    ax2.set_title("Parallelism Efficiency Trend")
    ax2.axhline(y=1.0, color='red', linestyle='--', label='Sequential (no parallelism)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig("performance_trend.png")
    print("📈 Trend plot saved to performance_trend.png")

# Example usage
plot_performance_trend()
```

## Related Documentation

- **[Performance Metrics](./performance_metrics.md)** - Detailed metrics documentation and analysis
- **[Trajectory Report](./trajectory_report.md)** - Human-readable execution log with DAG visualizations
- **[Galaxy Overview](../overview.md)** - Main Galaxy framework documentation
- **[Task Constellation](../constellation/task_constellation.md)** - DAG structure and parallelism metrics
- **[Constellation Orchestrator](../constellation_orchestrator/overview.md)** - Execution coordination

## Summary

The `result.json` file provides comprehensive session analysis:

- **Complete execution history** - All session details in structured format
- **Performance metrics** - Comprehensive timing and statistics via `SessionMetricsObserver`
- **Constellation analysis** - DAG structure and parallelism data
- **Programmatic access** - JSON format for automated analysis and reporting
- **Debugging support** - Failed task identification and detailed execution logs
- **Trend analysis** - Compare sessions over time for performance monitoring

Use `result.json` for debugging, performance optimization, reporting, and automated analysis of Galaxy workflows.
