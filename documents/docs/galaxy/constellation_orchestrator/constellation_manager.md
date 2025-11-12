# Constellation Manager

## Overview

The `ConstellationManager` is a companion component to the `TaskConstellationOrchestrator` that handles device assignment, resource management, and constellation lifecycle tracking. While the orchestrator focuses on execution flow and coordination, the manager provides the infrastructure for device operations and state management.

This separation of concerns follows the Single Responsibility Principle: orchestration logic remains independent of device management details.

## Architecture

```mermaid
graph TB
    O[TaskConstellationOrchestrator] -->|uses| CM[ConstellationManager]
    CM -->|communicates| DM[ConstellationDeviceManager]
    DM -->|manages| D1[Device 1]
    DM -->|manages| D2[Device 2]
    DM -->|manages| D3[Device N]
    
    CM -->|tracks| MD[(Constellation Metadata)]
    CM -->|validates| AS[Device Assignments]
```

Learn more about the [orchestrator architecture](overview.md) and [asynchronous scheduling](asynchronous_scheduling.md).

## Core Responsibilities

The ConstellationManager handles four primary responsibilities:

### 1. Device Assignment

Assigns tasks to appropriate devices using configurable strategies:

| Strategy | Description | Use Case |
|----------|-------------|----------|
| Round Robin | Distributes tasks evenly across devices | Load balancing for homogeneous devices |
| Capability Match | Matches task requirements to device capabilities | Heterogeneous device types (Windows, Android, iOS) |
| Load Balance | Assigns to device with lowest current load | Dynamic workload distribution |

### 2. Resource Management

Tracks and manages constellation resources:

- Device availability and status
- Constellation registration and metadata
- Device utilization statistics
- Assignment validation

### 3. Lifecycle Management

Manages constellation lifecycle:

- Registration when orchestration begins
- Metadata tracking during execution
- Unregistration after completion
- Status querying

### 4. Validation

Validates device assignments against constraints:

- All tasks have assigned devices
- Assigned devices exist and are connected
- Device capabilities match task requirements

## Device Assignment Strategies

### Round Robin

Distributes tasks cyclically across available devices:

```python
async def _assign_round_robin(
    self,
    constellation: TaskConstellation,
    available_devices: List[Dict[str, Any]],
    preferences: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Round robin device assignment strategy."""
    
    assignments = {}
    device_index = 0
    
    for task_id, task in constellation.tasks.items():
        # Check preferences first
        if preferences and task_id in preferences:
            preferred_device = preferences[task_id]
            if any(d["device_id"] == preferred_device for d in available_devices):
                assignments[task_id] = preferred_device
                continue
        
        # Round robin assignment
        device = available_devices[device_index % len(available_devices)]
        assignments[task_id] = device["device_id"]
        device_index += 1
    
    return assignments
```

**Characteristics:**

- Fairness: Each device gets approximately equal number of tasks
- Simplicity: No complex decision-making
- Overhead: O(N) where N = number of tasks
- Best for: Homogeneous devices with similar capabilities

**Example**:
```python
# 3 devices, 7 tasks
Task 1 → Device A
Task 2 → Device B
Task 3 → Device C
Task 4 → Device A
Task 5 → Device B
Task 6 → Device C
Task 7 → Device A
```

### Capability Match

Matches tasks to devices based on device type and capabilities:

```python
async def _assign_capability_match(
    self,
    constellation: TaskConstellation,
    available_devices: List[Dict[str, Any]],
    preferences: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Capability-based device assignment strategy."""
    
    assignments = {}
    
    for task_id, task in constellation.tasks.items():
        # Check preferences first
        if preferences and task_id in preferences:
            preferred_device = preferences[task_id]
            if any(d["device_id"] == preferred_device for d in available_devices):
                assignments[task_id] = preferred_device
                continue
        
        # Find devices matching task requirements
        matching_devices = []
        
        if task.device_type:
            matching_devices = [
                d for d in available_devices
                if d.get("device_type") == task.device_type.value
            ]
        
        # Fall back to any available device if no matches
        if not matching_devices:
            matching_devices = available_devices
        
        # Choose first matching device
        if matching_devices:
            assignments[task_id] = matching_devices[0]["device_id"]
    
    return assignments
```

**Characteristics:**

- Type-aware: Respects task's `device_type` requirement
- Fallback: Uses any device if no type match found
- Overhead: O(N × D) where N = tasks, D = devices
- Best for: Heterogeneous device ecosystems

**Example**:
```python
# Mixed device types
Task A (requires Windows) → Windows Device 1
Task B (requires Android) → Android Device 1
Task C (requires Windows) → Windows Device 1
Task D (no requirement)   → Any available device
```

### Load Balance

Assigns tasks to minimize device load:

```python
async def _assign_load_balance(
    self,
    constellation: TaskConstellation,
    available_devices: List[Dict[str, Any]],
    preferences: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Load-balanced device assignment strategy."""
    
    assignments = {}
    device_load = {d["device_id"]: 0 for d in available_devices}
    
    for task_id, task in constellation.tasks.items():
        # Check preferences first
        if preferences and task_id in preferences:
            preferred_device = preferences[task_id]
            if any(d["device_id"] == preferred_device for d in available_devices):
                assignments[task_id] = preferred_device
                device_load[preferred_device] += 1
                continue
        
        # Find device with lowest load
        min_load_device = min(device_load.keys(), key=lambda d: device_load[d])
        assignments[task_id] = min_load_device
        device_load[min_load_device] += 1
    
    return assignments
```

**Characteristics:**

- Balanced: Minimizes maximum device load
- Dynamic: Adapts to varying task counts
- Overhead: O(N × log D) with priority queue optimization
- Best for: Constellations with varying task complexity

**Example**:
```python
# 2 devices, 5 tasks with varying complexity
Task 1 (simple)  → Device A [load: 1]
Task 2 (complex) → Device B [load: 1]
Task 3 (simple)  → Device A [load: 2]
Task 4 (simple)  → Device B [load: 2]
Task 5 (complex) → Device A [load: 3]
```

## Constellation Lifecycle Management

### Registration

Register a constellation for management:

```python
def register_constellation(
    self,
    constellation: TaskConstellation,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Register a constellation for management."""
    
    constellation_id = constellation.constellation_id
    self._managed_constellations[constellation_id] = constellation
    self._constellation_metadata[constellation_id] = metadata or {}
    
    if self._logger:
        self._logger.info(
            f"Registered constellation '{constellation.name}' ({constellation_id})"
        )
    
    return constellation_id
```

**Purpose**: Track active constellations and their metadata

**Metadata examples**:
```python
metadata = {
    "user_id": "user123",
    "session_id": "session_456",
    "priority": "high",
    "created_by": "automation_pipeline",
}
```

### Status Querying

Get detailed status of a managed constellation:

```python
async def get_constellation_status(
    self, constellation_id: str
) -> Optional[Dict[str, Any]]:
    """Get detailed status of a managed constellation."""
    
    constellation = self._managed_constellations.get(constellation_id)
    if not constellation:
        return None
    
    metadata = self._constellation_metadata.get(constellation_id, {})
    
    return {
        "constellation_id": constellation_id,
        "name": constellation.name,
        "state": constellation.state.value,
        "statistics": constellation.get_statistics(),
        "ready_tasks": [task.task_id for task in constellation.get_ready_tasks()],
        "running_tasks": [task.task_id for task in constellation.get_running_tasks()],
        "completed_tasks": [task.task_id for task in constellation.get_completed_tasks()],
        "failed_tasks": [task.task_id for task in constellation.get_failed_tasks()],
        "metadata": metadata,
    }
```

**Returns**:
```json
{
  "constellation_id": "constellation_20251106_143052_a1b2c3d4",
  "name": "Multi-Device Data Collection",
  "state": "executing",
  "statistics": {
    "total_tasks": 10,
    "task_status_counts": {
      "completed": 3,
      "running": 2,
      "pending": 5
    },
    "parallelism_ratio": 2.5
  },
  "ready_tasks": ["task_6", "task_7"],
  "running_tasks": ["task_4", "task_5"],
  "completed_tasks": ["task_1", "task_2", "task_3"],
  "failed_tasks": [],
  "metadata": {
    "user_id": "user123",
    "priority": "high"
  }
}
```

### Unregistration

Remove a constellation from management:

```python
def unregister_constellation(self, constellation_id: str) -> bool:
    """Unregister a constellation from management."""
    
    if constellation_id in self._managed_constellations:
        constellation = self._managed_constellations[constellation_id]
        del self._managed_constellations[constellation_id]
        del self._constellation_metadata[constellation_id]
        
        if self._logger:
            self._logger.info(
                f"Unregistered constellation '{constellation.name}' ({constellation_id})"
            )
        return True
    
    return False
```

**Purpose**: Clean up resources after orchestration completes

## Device Operations

### Getting Available Devices

Retrieve list of connected devices:

```python
async def get_available_devices(self) -> List[Dict[str, Any]]:
    """Get list of available devices from device manager."""
    
    if not self._device_manager:
        return []
    
    try:
        connected_device_ids = self._device_manager.get_connected_devices()
        devices = []
        
        for device_id in connected_device_ids:
            device_info = self._device_manager.device_registry.get_device_info(
                device_id
            )
            if device_info:
                devices.append({
                    "device_id": device_id,
                    "device_type": getattr(device_info, "device_type", "unknown"),
                    "capabilities": getattr(device_info, "capabilities", []),
                    "status": "connected",
                    "metadata": getattr(device_info, "metadata", {}),
                })
        
        return devices
    except Exception as e:
        if self._logger:
            self._logger.error(f"Failed to get available devices: {e}")
        return []
```

**Returns**:
```python
[
    {
        "device_id": "windows_main",
        "device_type": "windows",
        "capabilities": ["file_ops", "browser", "office"],
        "status": "connected",
        "metadata": {"os_version": "Windows 11"}
    },
    {
        "device_id": "android_pixel",
        "device_type": "android",
        "capabilities": ["touch", "camera", "gps"],
        "status": "connected",
        "metadata": {"android_version": "14"}
    }
]
```

### Device Assignment

Automatically assign devices to all tasks:

```python
async def assign_devices_automatically(
    self,
    constellation: TaskConstellation,
    strategy: str = "round_robin",
    device_preferences: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Automatically assign devices to tasks in a constellation."""
    
    if not self._device_manager:
        raise ValueError("Device manager not available for device assignment")
    
    available_devices = await self._get_available_devices()
    if not available_devices:
        raise ValueError("No available devices for assignment")
    
    if self._logger:
        self._logger.info(
            f"Assigning devices to constellation '{constellation.name}' "
            f"using strategy '{strategy}'"
        )
    
    # Select strategy
    if strategy == "round_robin":
        assignments = await self._assign_round_robin(
            constellation, available_devices, device_preferences
        )
    elif strategy == "capability_match":
        assignments = await self._assign_capability_match(
            constellation, available_devices, device_preferences
        )
    elif strategy == "load_balance":
        assignments = await self._assign_load_balance(
            constellation, available_devices, device_preferences
        )
    else:
        raise ValueError(f"Unknown assignment strategy: {strategy}")
    
    # Apply assignments to tasks
    for task_id, device_id in assignments.items():
        task = constellation.get_task(task_id)
        if task:
            task.target_device_id = device_id
    
    if self._logger:
        self._logger.info(f"Assigned {len(assignments)} tasks to devices")
    
    return assignments
```

### Manual Reassignment

Reassign a single task to a different device:

```python
def reassign_task_device(
    self,
    constellation: TaskConstellation,
    task_id: str,
    new_device_id: str,
) -> bool:
    """Reassign a task to a different device."""
    
    task = constellation.get_task(task_id)
    if not task:
        return False
    
    old_device_id = task.target_device_id
    task.target_device_id = new_device_id
    
    if self._logger:
        self._logger.info(
            f"Reassigned task '{task_id}' from device '{old_device_id}' "
            f"to '{new_device_id}'"
        )
    
    return True
```

## Validation

### Assignment Validation

Validate that all tasks have valid device assignments:

```python
def validate_constellation_assignments(
    self, constellation: TaskConstellation
) -> tuple[bool, List[str]]:
    """Validate that all tasks have valid device assignments."""
    
    errors = []
    
    for task_id, task in constellation.tasks.items():
        if not task.target_device_id:
            errors.append(f"Task '{task_id}' has no device assignment")
    
    is_valid = len(errors) == 0
    
    if self._logger:
        if is_valid:
            self._logger.info(
                f"All tasks in constellation '{constellation.name}' have "
                f"valid assignments"
            )
        else:
            self._logger.warning(
                f"Constellation '{constellation.name}' has {len(errors)} "
                f"assignment errors"
            )
    
    return is_valid, errors
```

### Device Information

Get device information for a specific task:

```python
def get_task_device_info(
    self, constellation: TaskConstellation, task_id: str
) -> Optional[Dict[str, Any]]:
    """Get device information for a specific task."""
    
    task = constellation.get_task(task_id)
    if not task or not task.target_device_id:
        return None
    
    # Get device info from device manager
    if self._device_manager:
        try:
            device_info = self._device_manager.device_registry.get_device_info(
                task.target_device_id
            )
            if device_info:
                return {
                    "device_id": task.target_device_id,
                    "device_type": getattr(device_info, "device_type", "unknown"),
                    "capabilities": getattr(device_info, "capabilities", []),
                    "metadata": getattr(device_info, "metadata", {}),
                }
        except Exception as e:
            if self._logger:
                self._logger.error(
                    f"Failed to get device info for task '{task_id}': {e}"
                )
    
    return None
```

## Utilization Tracking

### Device Utilization Statistics

Get device utilization across constellation:

```python
def get_device_utilization(
    self, constellation: TaskConstellation
) -> Dict[str, int]:
    """Get device utilization statistics for a constellation."""
    
    utilization = {}
    
    for task in constellation.tasks.values():
        if task.target_device_id:
            utilization[task.target_device_id] = (
                utilization.get(task.target_device_id, 0) + 1
            )
    
    return utilization
```

**Example output**:
```python
{
    "windows_main": 5,
    "android_pixel": 3,
    "ios_iphone": 2
}
```

### Listing All Constellations

List all managed constellations:

```python
def list_constellations(self) -> List[Dict[str, Any]]:
    """List all managed constellations with basic information."""
    
    result = []
    for constellation_id, constellation in self._managed_constellations.items():
        metadata = self._constellation_metadata.get(constellation_id, {})
        result.append({
            "constellation_id": constellation_id,
            "name": constellation.name,
            "state": constellation.state.value,
            "task_count": constellation.task_count,
            "dependency_count": constellation.dependency_count,
            "metadata": metadata,
        })
    
    return result
```

## Usage Patterns

### Basic Setup

```python
from galaxy.constellation.orchestrator import ConstellationManager
from galaxy.client.device_manager import ConstellationDeviceManager

# Create device manager
device_manager = ConstellationDeviceManager()

# Create constellation manager
manager = ConstellationManager(device_manager, enable_logging=True)

# Register constellation
constellation_id = manager.register_constellation(
    constellation,
    metadata={"priority": "high"}
)
```

### Automatic Assignment

```python
# Assign devices using capability matching
assignments = await manager.assign_devices_automatically(
    constellation,
    strategy="capability_match"
)

print(f"Assigned {len(assignments)} tasks")
```

### With Preferences

```python
# Specify preferred devices for specific tasks
preferences = {
    "critical_task_1": "windows_main",
    "gpu_task_2": "windows_gpu",
}

assignments = await manager.assign_devices_automatically(
    constellation,
    strategy="load_balance",
    device_preferences=preferences
)
```

### Manual Override

```python
# Reassign specific task
manager.reassign_task_device(
    constellation,
    task_id="task_5",
    new_device_id="android_backup"
)
```

### Validation

```python
# Validate assignments before orchestration
is_valid, errors = manager.validate_constellation_assignments(constellation)

if not is_valid:
    print(f"Validation errors: {errors}")
    # Fix assignments...
```

### Monitoring

```python
# Check constellation status during execution
status = await manager.get_constellation_status(constellation_id)

print(f"State: {status['state']}")
print(f"Running tasks: {len(status['running_tasks'])}")
print(f"Completed tasks: {len(status['completed_tasks'])}")

# Get device utilization
utilization = manager.get_device_utilization(constellation)
for device_id, task_count in utilization.items():
    print(f"{device_id}: {task_count} tasks")
```

## Integration with Orchestrator

The orchestrator uses the manager internally:

```python
class TaskConstellationOrchestrator:
    def __init__(self, device_manager, enable_logging=True):
        self._device_manager = device_manager
        self._constellation_manager = ConstellationManager(
            device_manager, enable_logging
        )
    
    async def orchestrate_constellation(self, constellation, ...):
        # Use manager for assignment
        await self._constellation_manager.assign_devices_automatically(
            constellation, assignment_strategy
        )
        
        # Use manager for validation
        is_valid, errors = self._constellation_manager \
            .validate_constellation_assignments(constellation)
        
        if not is_valid:
            raise ValueError(f"Device assignment validation failed: {errors}")
        
        # Continue orchestration...
```

## Related Documentation

- [Overview](overview.md) - Orchestrator architecture and design
- [Asynchronous Scheduling](asynchronous_scheduling.md) - Task execution model
- [Consistency Guarantees](consistency_guarantees.md) - Device assignment validation
- [API Reference](api_reference.md) - Complete API documentation
