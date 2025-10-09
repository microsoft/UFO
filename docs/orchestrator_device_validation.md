# Orchestrator Device Assignment Validation

## 📋 Overview

Added validation logic to `TaskConstellationOrchestrator` to ensure all tasks have device assignments when no assignment strategy is provided.

## 🎯 Feature Description

### New Method: `_validate_existing_device_assignments()`

This method validates that all tasks in a constellation have a `target_device_id` assigned when neither `device_assignments` nor `assignment_strategy` parameters are provided to `orchestrate_constellation()`.

## 🔧 Implementation Details

### Method Signature

```python
def _validate_existing_device_assignments(
    self, constellation: TaskConstellation
) -> None:
    """
    Validate that all tasks in constellation have target_device_id assigned.
    
    :param constellation: TaskConstellation to validate
    :raises ValueError: If any task is missing target_device_id
    """
```

### Validation Logic

The method performs the following checks for each task:

1. **Attribute Existence**: Checks if the task has a `target_device_id` attribute
2. **Value Check**: Verifies that `target_device_id` is not `None` or empty string
3. **Error Collection**: Collects all task IDs that fail validation
4. **Error Reporting**: Raises `ValueError` with detailed error message if validation fails

## 📝 Usage Scenarios

### Scenario 1: Manual Device Assignments (Existing Behavior)

```python
# Manually assign devices to specific tasks
device_assignments = {
    "task_1": "device_001",
    "task_2": "device_002",
    "task_3": "device_001"
}

result = await orchestrator.orchestrate_constellation(
    constellation=my_constellation,
    device_assignments=device_assignments
)
# ✅ Works: Manual assignments are applied
```

### Scenario 2: Auto-Assignment with Strategy (Existing Behavior)

```python
# Automatically assign devices using round-robin strategy
result = await orchestrator.orchestrate_constellation(
    constellation=my_constellation,
    assignment_strategy="round_robin"
)
# ✅ Works: Devices auto-assigned using strategy
```

### Scenario 3: Pre-Assigned Devices (NEW - Validation Added)

```python
# Tasks already have target_device_id set
task_1.target_device_id = "device_001"
task_2.target_device_id = "device_002"
task_3.target_device_id = "device_001"

# No device_assignments or assignment_strategy needed
result = await orchestrator.orchestrate_constellation(
    constellation=my_constellation
)
# ✅ Works: Validates existing assignments and proceeds
```

### Scenario 4: Missing Device Assignments (NEW - Validation Catches Error)

```python
# Some tasks don't have target_device_id set
task_1.target_device_id = "device_001"
task_2.target_device_id = None  # ❌ Missing!
task_3.target_device_id = ""     # ❌ Empty!

result = await orchestrator.orchestrate_constellation(
    constellation=my_constellation
)
# ❌ Raises ValueError:
# "Device assignment validation failed: The following tasks do not have 
#  target_device_id assigned: ['task_2', 'task_3']. Please provide either 
#  'device_assignments' or 'assignment_strategy' parameter."
```

## 🔄 Updated Assignment Flow

```python
async def _assign_devices_to_tasks(
    self,
    constellation: TaskConstellation,
    device_assignments: Optional[Dict[str, str]],
    assignment_strategy: Optional[str] = None,
) -> None:
    if device_assignments:
        # Path 1: Apply manual device assignments
        for task_id, device_id in device_assignments.items():
            self._constellation_manager.reassign_task_device(
                constellation, task_id, device_id
            )
    elif assignment_strategy:
        # Path 2: Auto-assign using strategy
        await self._constellation_manager.assign_devices_automatically(
            constellation, assignment_strategy
        )
    else:
        # Path 3: Validate existing assignments (NEW!)
        self._validate_existing_device_assignments(constellation)
```

## ✅ Validation Details

### What Gets Checked

For each task in the constellation:

```python
# Check 1: Attribute exists
if not hasattr(task, 'target_device_id'):
    # ❌ Task doesn't have target_device_id attribute
    
# Check 2: Value is not None
if task.target_device_id is None:
    # ❌ target_device_id is None
    
# Check 3: Value is not empty
if task.target_device_id == "":
    # ❌ target_device_id is empty string
```

### Error Message Format

When validation fails, the error message includes:

1. **Clear description** of the problem
2. **List of task IDs** without device assignments
3. **Helpful suggestion** to provide `device_assignments` or `assignment_strategy`

Example:
```
ValueError: Device assignment validation failed: 
The following tasks do not have target_device_id assigned: ['task_2', 'task_3', 'task_5']. 
Please provide either 'device_assignments' or 'assignment_strategy' parameter.
```

## 📊 Logging

### Success Case

When all tasks have valid assignments:

```
INFO: All tasks have existing device assignments. Total tasks validated: 5
```

### Failure Case

When validation fails:

```
ERROR: Device assignment validation failed: 
The following tasks do not have target_device_id assigned: ['task_2', 'task_3'].
```

## 🎯 Benefits

### 1. Early Error Detection
- Catches missing device assignments **before** execution starts
- Prevents runtime failures during task execution
- Provides clear error messages for troubleshooting

### 2. Flexible Assignment Options
Now supports three ways to assign devices:
1. **Manual**: Explicit `device_assignments` dictionary
2. **Automatic**: Using `assignment_strategy`
3. **Pre-assigned**: Tasks already have `target_device_id` set

### 3. Better Developer Experience
- Clear error messages guide developers to fix issues
- Validation happens early in the orchestration process
- No ambiguity about device assignment requirements

## 🧪 Testing Recommendations

### Unit Test: Validation Success

```python
async def test_validate_existing_device_assignments_success():
    """Test validation passes when all tasks have device IDs."""
    # Setup
    orchestrator = TaskConstellationOrchestrator(...)
    constellation = create_test_constellation()
    
    # Assign devices to all tasks
    for task in constellation.tasks.values():
        task.target_device_id = "device_001"
    
    # Should not raise
    orchestrator._validate_existing_device_assignments(constellation)
```

### Unit Test: Validation Failure

```python
async def test_validate_existing_device_assignments_failure():
    """Test validation fails when tasks missing device IDs."""
    # Setup
    orchestrator = TaskConstellationOrchestrator(...)
    constellation = create_test_constellation()
    
    # Leave some tasks without device IDs
    constellation.tasks["task_1"].target_device_id = None
    constellation.tasks["task_2"].target_device_id = ""
    
    # Should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        orchestrator._validate_existing_device_assignments(constellation)
    
    assert "task_1" in str(exc_info.value)
    assert "task_2" in str(exc_info.value)
```

### Integration Test: Orchestration with Pre-Assigned Devices

```python
async def test_orchestrate_with_preassigned_devices():
    """Test orchestration works with pre-assigned device IDs."""
    # Setup
    orchestrator = TaskConstellationOrchestrator(...)
    constellation = create_test_constellation()
    
    # Pre-assign devices
    for task in constellation.tasks.values():
        task.target_device_id = "device_001"
    
    # Orchestrate without device_assignments or assignment_strategy
    result = await orchestrator.orchestrate_constellation(
        constellation=constellation
    )
    
    assert result["status"] == "completed"
```

## 🔍 Edge Cases Handled

### 1. Task Without `target_device_id` Attribute
```python
# If task doesn't have the attribute at all
if not hasattr(task, 'target_device_id'):
    # ❌ Caught by validation
```

### 2. Task with `None` Value
```python
task.target_device_id = None
# ❌ Caught by validation
```

### 3. Task with Empty String
```python
task.target_device_id = ""
# ❌ Caught by validation
```

### 4. Task with Whitespace Only
```python
task.target_device_id = "   "
# ⚠️ Currently passes validation
# Consider adding: if not task.target_device_id.strip():
```

## 📚 Related Code

### Files Modified
- `galaxy/constellation/orchestrator/orchestrator.py`

### Related Methods
- `orchestrate_constellation()` - Main orchestration entry point
- `_validate_and_prepare_constellation()` - Calls device assignment logic
- `_assign_devices_to_tasks()` - Updated to call new validation method
- `_validate_existing_device_assignments()` - NEW validation method

## 🚀 Migration Guide

### For Existing Code

If you have code that relies on pre-assigned `target_device_id` values:

**Before:**
```python
# Tasks have target_device_id already set
result = await orchestrator.orchestrate_constellation(
    constellation=my_constellation,
    assignment_strategy="round_robin"  # Unnecessary but harmless
)
```

**After:**
```python
# Can now omit assignment_strategy if tasks already have device IDs
result = await orchestrator.orchestrate_constellation(
    constellation=my_constellation
    # No device_assignments or assignment_strategy needed!
)
```

### For New Code

Choose the appropriate approach based on your use case:

```python
# Option 1: Let tasks come with pre-assigned devices
for task in constellation.tasks.values():
    task.target_device_id = get_device_for_task(task)

result = await orchestrator.orchestrate_constellation(
    constellation=my_constellation
)

# Option 2: Manual assignment
device_map = {"task_1": "dev_1", "task_2": "dev_2"}
result = await orchestrator.orchestrate_constellation(
    constellation=my_constellation,
    device_assignments=device_map
)

# Option 3: Auto-assignment
result = await orchestrator.orchestrate_constellation(
    constellation=my_constellation,
    assignment_strategy="round_robin"
)
```

---

**Created**: October 9, 2025  
**Author**: AI Assistant  
**Status**: Implemented ✅
