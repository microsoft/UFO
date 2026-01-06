# ConstellationEditor Server

## Overview

**ConstellationEditor** provides multi-device task coordination and dependency management for distributed workflows in UFO².

**Server Type:** Action  
**Deployment:** Local (in-process)  
**Agent:** GalaxyAgent  
**LLM-Selectable:** ✅ Yes

## Server Information

| Property | Value |
|----------|-------|
| **Namespace** | `ConstellationEditor` |
| **Server Name** | `UFO Constellation Editor MCP Server` |
| **Platform** | Cross-platform |
| **Tool Type** | `action` |

## Tools Summary

| Category | Tool Name | Description |
|----------|-----------|-------------|
| **Task Management** | `add_task` | Create new task |
| | `remove_task` | Delete task |
| | `update_task` | Modify task properties |
| **Dependency Management** | `add_dependency` | Create task dependency |
| | `remove_dependency` | Delete dependency |
| | `update_dependency` | Modify dependency description |
| **Bulk Operations** | `build_constellation` | Build complete constellation from config |

## Task Management Tools

### add_task

Add a new task to the constellation.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_id` | `str` | ✅ Yes | - | Unique task identifier (e.g., `"open_browser"`, `"login_system"`) |
| `name` | `str` | ✅ Yes | - | Human-readable task name (e.g., `"Open Browser"`) |
| `description` | `str` | ✅ Yes | - | Detailed task description with steps and expected outcomes |
| `target_device_id` | `str` | No | `None` | Device ID where task should execute (from Device Info List) |
| `tips` | `List[str]` | No | `None` | List of tips and best practices for task execution |

#### Returns

`str` - JSON representation of complete TaskConstellation after adding task

#### Example

```python
await computer.run_actions([
    MCPToolCall(
        tool_key="action::add_task",
        tool_name="add_task",
        parameters={
            "task_id": "extract_data",
            "name": "Extract Data from Excel",
            "description": "Open Excel file, extract data from Sheet1, save to CSV format",
            "target_device_id": "device_windows_001",
            "tips": [
                "Ensure Excel is installed",
                "Close Excel before running task",
                "Verify file path exists"
            ]
        }
    )
])
```

---

### remove_task

Remove a task from the constellation (also removes all dependencies involving this task).

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | `str` | ✅ Yes | Unique task identifier to remove |

#### Returns

`str` - JSON representation of constellation after removal

#### Example

```python
await computer.run_actions([
    MCPToolCall(
        tool_key="action::remove_task",
        tool_name="remove_task",
        parameters={"task_id": "extract_data"}
    )
])
```

---

### update_task

Update specific fields of an existing task.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_id` | `str` | ✅ Yes | - | Task to update |
| `name` | `str` | No | `None` | New task name (leave empty to keep current) |
| `description` | `str` | No | `None` | New description |
| `target_device_id` | `str` | No | `None` | New target device |
| `tips` | `List[str]` | No | `None` | New tips list |

**Note:** Only provided fields are updated; others remain unchanged.

#### Returns

`str` - JSON representation of constellation after update

#### Example

```python
# Update only description and tips
await computer.run_actions([
    MCPToolCall(
        tool_key="action::update_task",
        tool_name="update_task",
        parameters={
            "task_id": "extract_data",
            "description": "Extract data from Excel Sheet1 and Sheet2, merge into single CSV",
            "tips": [
                "Ensure Excel is installed",
                "Handle merged cells properly",
                "Verify output CSV encoding"
            ]
        }
    )
])
```

## Dependency Management Tools

### add_dependency

Create a dependency relationship between two tasks (source task must complete before target task can start).

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dependency_id` | `str` | ✅ Yes | **MUST generate unique ID** (e.g., `"login->extract_data"`) |
| `from_task_id` | `str` | ✅ Yes | Source/prerequisite task ID |
| `to_task_id` | `str` | ✅ Yes | Target/dependent task ID |
| `condition_description` | `str` | No | `None` | Human-readable description of dependency condition |

!!!warning "dependency_id Required"
    You **MUST** generate and provide a unique `dependency_id`. Do not omit this parameter!

#### Returns

`str` - JSON representation of constellation after adding dependency

#### Example

```python
await computer.run_actions([
    MCPToolCall(
        tool_key="action::add_dependency",
        tool_name="add_dependency",
        parameters={
            "dependency_id": "login_system->extract_data",  # MUST provide
            "from_task_id": "login_system",
            "to_task_id": "extract_data",
            "condition_description": "Wait for successful user authentication before accessing user data"
        }
    )
])
```

---

### remove_dependency

Remove a dependency relationship without affecting the tasks themselves.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dependency_id` | `str` | ✅ Yes | Dependency ID (line_id) to remove |

#### Returns

`str` - JSON representation of constellation after removal

#### Example

```python
await computer.run_actions([
    MCPToolCall(
        tool_key="action::remove_dependency",
        tool_name="remove_dependency",
        parameters={"dependency_id": "login_system->extract_data"}
    )
])
```

---

### update_dependency

Update the condition description of an existing dependency.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dependency_id` | `str` | ✅ Yes | Dependency to update |
| `condition_description` | `str` | ✅ Yes | New condition description |

#### Returns

`str` - JSON representation of constellation after update

#### Example

```python
await computer.run_actions([
    MCPToolCall(
        tool_key="action::update_dependency",
        tool_name="update_dependency",
        parameters={
            "dependency_id": "login_system->extract_data",
            "condition_description": "Wait for successful authentication and database connection before data extraction"
        }
    )
])
```

## Bulk Operations

### build_constellation

Build a complete constellation from configuration data (batch creation).

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `config` | `TaskConstellationSchema` | ✅ Yes | - | Complete constellation configuration |
| `clear_existing` | `bool` | No | `True` | Clear existing tasks/dependencies before building |

#### Configuration Schema

```python
{
    "tasks": [
        {
            "task_id": "string (required)",
            "name": "string (optional)",
            "description": "string (required)",
            "target_device_id": "string (optional)",
            "priority": int (1-4, optional),
            "status": "string (optional)",
            "tips": ["string"] (optional)
        }
    ],
    "dependencies": [
        {
            "from_task_id": "string (required)",
            "to_task_id": "string (required)",
            "dependency_type": "string (optional)",
            "condition_description": "string (optional)"
        }
    ],
    "metadata": dict (optional)
}
```

#### Returns

`str` - JSON representation of built constellation

#### Example

```python
config = {
    "tasks": [
        {
            "task_id": "open_browser",
            "name": "Open Browser",
            "description": "Launch Chrome and navigate to login page",
            "target_device_id": "device_001"
        },
        {
            "task_id": "login",
            "name": "User Login",
            "description": "Enter credentials and submit login form",
            "target_device_id": "device_001"
        },
        {
            "task_id": "extract_data",
            "name": "Extract Data",
            "description": "Navigate to data page and extract table",
            "target_device_id": "device_002"
        }
    ],
    "dependencies": [
        {
            "from_task_id": "open_browser",
            "to_task_id": "login",
            "condition_description": "Browser must be open before login"
        },
        {
            "from_task_id": "login",
            "to_task_id": "extract_data",
            "condition_description": "User must be authenticated before data access"
        }
    ]
}

await computer.run_actions([
    MCPToolCall(
        tool_key="action::build_constellation",
        tool_name="build_constellation",
        parameters={
            "config": config,
            "clear_existing": True
        }
    )
])
```

## Configuration

```yaml
GalaxyAgent:
  default:
    action:
      - namespace: ConstellationEditor
        type: local
```

## Best Practices

### 1. Use Descriptive Task IDs

```python
# ✅ Good: Clear task IDs
"task_id": "extract_sales_data_from_excel"
"task_id": "send_email_notification"
"task_id": "process_user_input"

# ❌ Bad: Unclear IDs
"task_id": "task1"
"task_id": "do_stuff"
"task_id": "process"
```

### 2. Always Provide dependency_id

```python
# ✅ Good: Generate unique dependency_id
await computer.run_actions([
    MCPToolCall(
        tool_key="action::add_dependency",
        parameters={
            "dependency_id": f"{from_task}->{ to_task}",  # Generate ID
            "from_task_id": from_task,
            "to_task_id": to_task
        }
    )
])

# ❌ Bad: Omit dependency_id
await computer.run_actions([
    MCPToolCall(
        tool_key="action::add_dependency",
        parameters={
            # Missing dependency_id - will fail!
            "from_task_id": from_task,
            "to_task_id": to_task
        }
    )
])
```

### 3. Provide Detailed Descriptions

```python
# ✅ Good: Detailed description
{
    "description": "Open Chrome browser, navigate to https://example.com/login, wait for page to fully load, then take a screenshot and save it to C:\\screenshots\\login_page.png"
}

# ❌ Bad: Vague description
{
    "description": "Open browser"
}
```

## Use Cases

### Multi-Device Workflow

```python
# 1. Create tasks on different devices
await computer.run_actions([
    MCPToolCall(tool_key="action::add_task", parameters={
        "task_id": "windows_extract",
        "name": "Extract Data on Windows",
        "description": "Extract Excel data",
        "target_device_id": "device_windows_001"
    })
])

await computer.run_actions([
    MCPToolCall(tool_key="action::add_task", parameters={
        "task_id": "linux_process",
        "name": "Process Data on Linux",
        "description": "Run Python analysis script",
        "target_device_id": "device_linux_001"
    })
])

# 2. Create dependency
await computer.run_actions([
    MCPToolCall(tool_key="action::add_dependency", parameters={
        "dependency_id": "windows_extract->linux_process",
        "from_task_id": "windows_extract",
        "to_task_id": "linux_process",
        "condition_description": "Data must be extracted before processing"
    })
])
```

## Related Documentation

- [Action Servers](../action.md) - Action server concepts
- [MCP Overview](../overview.md) - MCP architecture
- [Configuration Guide](../configuration.md) - Constellation setup
- [Local Servers](../local_servers.md) - Local server deployment
