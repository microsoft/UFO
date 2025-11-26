# Constellation Progress Observer

The **ConstellationProgressObserver** is responsible for tracking task execution progress and coordinating between the orchestrator and the agent. It acts as the bridge that enables the agent to react to task completion events and make necessary constellation modifications.

**Location:** `galaxy/session/observers/base_observer.py`

## Purpose

The Progress Observer serves two critical functions:

- **Task Completion Coordination** — Queues task completion events for the agent to process
- **Constellation Event Handling** — Notifies the agent when constellation execution completes

## Architecture

```mermaid
graph TB
    subgraph "Orchestrator Layer"
        O[TaskConstellationOrchestrator]
    end
    
    subgraph "Event System"
        EB[EventBus]
    end
    
    subgraph "Observer Layer"
        CPO[ConstellationProgressObserver]
    end
    
    subgraph "Agent Layer"
        A[ConstellationAgent]
        Q[Task Completion Queue]
    end
    
    O -->|publish events| EB
    EB -->|notify| CPO
    CPO -->|queue events| Q
    A -->|process from| Q
    
    style CPO fill:#66bb6a,stroke:#333,stroke-width:3px
    style Q fill:#fff4e1,stroke:#333,stroke-width:2px
    style EB fill:#4a90e2,stroke:#333,stroke-width:2px,color:#fff
```

**Component Interaction:**

| Component | Role | Communication |
|-----------|------|---------------|
| **Orchestrator** | Executes tasks, publishes events | → EventBus |
| **EventBus** | Distributes events | → Progress Observer |
| **Progress Observer** | Filters & queues relevant events | → Agent Queue |
| **Agent** | Processes completions, modifies constellation | ← Agent Queue |

## Event Handling

The Progress Observer handles two types of events:

### Task Events

Monitors task execution lifecycle and queues completion events:

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant EB as EventBus
    participant PO as ProgressObserver
    participant Q as Agent Queue
    participant A as Agent
    
    O->>EB: TASK_STARTED
    EB->>PO: on_event(event)
    Note over PO: Store task result<br/>Log progress
    
    O->>EB: TASK_COMPLETED
    EB->>PO: on_event(event)
    Note over PO: Store result<br/>Queue for agent
    PO->>Q: add_task_completion_event()
    
    Note over A: Agent in Continue state<br/>waiting for events
    A->>Q: get event
    Note over A: Process result<br/>Modify constellation
```

**Handled Event Types:**

| Event Type | Action | Data Stored |
|------------|--------|-------------|
| `TASK_STARTED` | Store task result placeholder | task_id, status, timestamp |
| `TASK_COMPLETED` | Store result, queue for agent | task_id, status, result, timestamp |
| `TASK_FAILED` | Store error, queue for agent | task_id, status, error, timestamp |

### Constellation Events

Handles constellation lifecycle events:

| Event Type | Action | Effect |
|------------|--------|--------|
| `CONSTELLATION_COMPLETED` | Queue completion event for agent | Wakes up agent's Continue state to process final results |

## Implementation

### Initialization

```python
from galaxy.session.observers import ConstellationProgressObserver
from galaxy.agents import ConstellationAgent

# Create progress observer with agent reference
agent = ConstellationAgent(orchestrator=orchestrator)
progress_observer = ConstellationProgressObserver(agent=agent)

# Subscribe to event bus
from galaxy.core.events import get_event_bus
event_bus = get_event_bus()
event_bus.subscribe(progress_observer)
```

**Constructor Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent` | `ConstellationAgent` | The agent that will process queued events |

### Internal Data Structures

The observer maintains:

```python
class ConstellationProgressObserver(IEventObserver):
    def __init__(self, agent: ConstellationAgent):
        self.agent = agent
        
        # Task results storage: task_id -> result dict
        self.task_results: Dict[str, Dict[str, Any]] = {}
        
        self.logger = logging.getLogger(__name__)
```

**Task Result Structure:**

```python
{
    "task_id": "task_123",
    "status": "COMPLETED",  # or "FAILED"
    "result": {...},         # Task execution result
    "error": None,           # Exception if failed
    "timestamp": 1234567890.123
}
```

## Event Processing Flow

### Task Event Processing

```python
async def _handle_task_event(self, event: TaskEvent) -> None:
    """Handle task progress events and queue them for agent processing."""
    
    try:
        self.logger.info(
            f"Task progress: {event.task_id} -> {event.status}. "
            f"Event Type: {event.event_type}"
        )
        
        # 1. Store task result for tracking
        self.task_results[event.task_id] = {
            "task_id": event.task_id,
            "status": event.status,
            "result": event.result,
            "error": event.error,
            "timestamp": event.timestamp,
        }
        
        # 2. Queue completion/failure events for agent
        if event.event_type in [EventType.TASK_COMPLETED, EventType.TASK_FAILED]:
            await self.agent.add_task_completion_event(event)
    
    except Exception as e:
        self.logger.error(f"Error handling task event: {e}", exc_info=True)
```

**Processing Steps:**

1. **Log Progress**: Record task status change
2. **Store Result**: Update internal task_results dictionary
3. **Queue for Agent**: If completion/failure, add to agent's queue
4. **Error Handling**: Catch and log any exceptions

### Constellation Event Processing

```python
async def _handle_constellation_event(self, event: ConstellationEvent) -> None:
    """Handle constellation update events."""
    
    try:
        if event.event_type == EventType.CONSTELLATION_COMPLETED:
            # Queue completion event for agent
            await self.agent.add_constellation_completion_event(event)
    
    except Exception as e:
        self.logger.error(
            f"Error handling constellation event: {e}", 
            exc_info=True
        )
```

## API Reference

### Constructor

```python
def __init__(self, agent: ConstellationAgent)
```

Initialize the progress observer with a reference to the agent.

**Parameters:**

- `agent` — `ConstellationAgent` instance that will process queued events

**Example:**

```python
from galaxy.agents import ConstellationAgent
from galaxy.session.observers import ConstellationProgressObserver

agent = ConstellationAgent(orchestrator=orchestrator)
progress_observer = ConstellationProgressObserver(agent=agent)
```

### Event Handler

```python
async def on_event(self, event: Event) -> None
```

Handle constellation-related events (TaskEvent or ConstellationEvent).

**Parameters:**

- `event` — Event instance (TaskEvent or ConstellationEvent)

**Behavior:**

- Filters events by type (TaskEvent vs ConstellationEvent)
- Delegates to appropriate handler method
- Logs progress and stores results
- Queues completion events for agent

## Usage Examples

### Example 1: Basic Setup

```python
import asyncio
from galaxy.core.events import get_event_bus
from galaxy.agents import ConstellationAgent
from galaxy.constellation import TaskConstellationOrchestrator
from galaxy.session.observers import ConstellationProgressObserver

async def setup_progress_tracking():
    """Set up progress tracking for constellation execution."""
    
    # Create orchestrator and agent
    orchestrator = TaskConstellationOrchestrator()
    agent = ConstellationAgent(orchestrator=orchestrator)
    
    # Create and subscribe progress observer
    progress_observer = ConstellationProgressObserver(agent=agent)
    event_bus = get_event_bus()
    event_bus.subscribe(progress_observer)
    
    # Now orchestrator events will be tracked and queued for agent
    return agent, orchestrator, progress_observer
```

### Example 2: Monitoring Task Results

```python
async def monitor_task_progress(observer: ConstellationProgressObserver):
    """Monitor task execution progress."""
    
    # Wait for some tasks to complete
    await asyncio.sleep(5)
    
    # Access stored results
    for task_id, result in observer.task_results.items():
        status = result["status"]
        timestamp = result["timestamp"]
        
        if status == "COMPLETED":
            print(f"✅ Task {task_id} completed at {timestamp}")
            print(f"   Result: {result['result']}")
        elif status == "FAILED":
            print(f"❌ Task {task_id} failed at {timestamp}")
            print(f"   Error: {result['error']}")
```

### Example 3: Custom Progress Observer

```python
from galaxy.core.events import IEventObserver, TaskEvent, EventType

class CustomProgressObserver(IEventObserver):
    """Custom observer with additional progress tracking."""
    
    def __init__(self, agent, on_progress_callback=None):
        self.agent = agent
        self.on_progress_callback = on_progress_callback
        
        # Track progress statistics
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
    
    async def on_event(self, event: Event) -> None:
        if isinstance(event, TaskEvent):
            # Update statistics
            if event.event_type == EventType.TASK_STARTED:
                self.total_tasks += 1
            elif event.event_type == EventType.TASK_COMPLETED:
                self.completed_tasks += 1
            elif event.event_type == EventType.TASK_FAILED:
                self.failed_tasks += 1
            
            # Call custom callback
            if self.on_progress_callback:
                progress = self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 0
                self.on_progress_callback(progress, event)
            
            # Queue for agent
            if event.event_type in [EventType.TASK_COMPLETED, EventType.TASK_FAILED]:
                await self.agent.add_task_completion_event(event)

# Usage
def progress_callback(progress, event):
    print(f"Progress: {progress*100:.1f}% - {event.task_id} {event.status}")

custom_observer = CustomProgressObserver(
    agent=agent,
    on_progress_callback=progress_callback
)
event_bus.subscribe(custom_observer)
```

## Integration with Agent

The Progress Observer integrates tightly with the ConstellationAgent's state machine:

### Agent Queue Interface

The observer calls these agent methods:

```python
# Queue task completion event
await self.agent.add_task_completion_event(task_event)

# Queue constellation completion event
await self.agent.add_constellation_completion_event(constellation_event)
```

### Agent Processing

The agent processes queued events in its `Continue` state:

```mermaid
stateDiagram-v2
    [*] --> Continue: Task completes
    Continue --> ProcessEvent: Get event from queue
    ProcessEvent --> UpdateConstellation: Event is TASK_COMPLETED
    ProcessEvent --> HandleFailure: Event is TASK_FAILED
    UpdateConstellation --> Continue: More tasks pending
    UpdateConstellation --> Finish: All tasks done
    HandleFailure --> Continue: Retry task
    HandleFailure --> Finish: Max retries exceeded
    Finish --> [*]
```

**Agent State Machine States:**

| State | Description | Trigger |
|-------|-------------|---------|
| **Continue** | Wait for task completion events | Events queued by Progress Observer |
| **ProcessEvent** | Extract event from queue | Event available |
| **UpdateConstellation** | Modify constellation based on result | Task completed successfully |
| **HandleFailure** | Handle task failure, retry if needed | Task failed |
| **Finish** | Complete constellation execution | All tasks done or unrecoverable error |

## Performance Considerations

### Memory Management

The observer stores all task results in memory:

```python
self.task_results: Dict[str, Dict[str, Any]] = {}
```

**Best Practices:**

- **Clear results** after constellation completion to free memory
- **Limit result size** by storing only essential data
- **Use weak references** for large result objects if needed

### Queue Management

Events are queued to the agent's asyncio queue:

```python
await self.agent.add_task_completion_event(event)
```

**Considerations:**

- **Queue size** is unbounded by default
- **Back pressure** may occur if agent processes slowly
- **Memory growth** possible with many rapid completions

!!! warning "Memory Usage"
    For long-running sessions with many tasks, consider periodically clearing the `task_results` dictionary to prevent memory growth.

## Best Practices

### 1. Clean Up After Completion

Clear task results after constellation execution:

```python
async def execute_with_cleanup(orchestrator, constellation, progress_observer):
    """Execute constellation and clean up observer."""
    
    try:
        await orchestrator.execute_constellation(constellation)
    finally:
        # Clear stored results
        progress_observer.task_results.clear()
```

### 2. Handle Errors Gracefully

The observer includes comprehensive error handling:

```python
try:
    # Process event
    await self._handle_task_event(event)
except AttributeError as e:
    self.logger.error(f"Attribute error: {e}", exc_info=True)
except KeyError as e:
    self.logger.error(f"Missing key: {e}", exc_info=True)
except Exception as e:
    self.logger.error(f"Unexpected error: {e}", exc_info=True)
```

### 3. Monitor Queue Size

Check agent queue size periodically:

```python
# Access agent's internal queue
queue_size = self.agent.task_completion_queue.qsize()
if queue_size > 100:
    logger.warning(f"Task completion queue growing large: {queue_size}")
```

## Related Documentation

- **[Observer System Overview](overview.md)** — Architecture and design principles
- **[Agent Output Observer](agent_output_observer.md)** — Agent response and action display
- **[Constellation Agent](../constellation_agent/overview.md)** — Agent state machine and event processing
- **[Constellation Modification Synchronizer](synchronizer.md)** — Coordination between agent and orchestrator

## Summary

The Constellation Progress Observer:

- **Tracks** task execution progress
- **Stores** task results for historical reference
- **Queues** completion events for agent processing
- **Coordinates** between orchestrator and agent
- **Enables** event-driven constellation modification

This observer is essential for the agent-orchestrator coordination pattern in Galaxy, replacing complex callback mechanisms with a clean event-driven interface.
