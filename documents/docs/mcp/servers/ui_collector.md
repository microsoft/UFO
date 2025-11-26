# UICollector Server

## Overview

**UICollector** is a data collection MCP server that provides comprehensive UI observation and information retrieval capabilities for the UFO² framework. It automatically gathers screenshots, window lists, control information, and UI trees to build the observation context for LLM decision-making.

**Server Type:** Data Collection  
**Deployment:** Local (in-process)  
**Agent:** HostAgent, AppAgent  
**LLM-Selectable:** ❌ No (automatically invoked by framework)

## Server Information

| Property | Value |
|----------|-------|
| **Namespace** | `UICollector` |
| **Server Name** | `UFO UI Data MCP Server` |
| **Platform** | Windows |
| **Backend** | UIAutomation (UIA) or Win32 |
| **Tool Type** | `data_collection` |
| **Tool Key Format** | `data_collection::{tool_name}` |

## Tools

### 1. get_desktop_app_info

Get information about all application windows currently open on the desktop.

#### Description

Retrieves a list of all visible application windows on the Windows desktop, including window names, types, and identifiers. This is typically the first step in UI automation workflows to discover available applications.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `remove_empty` | `bool` | No | `True` | Whether to remove windows with no visible content |
| `refresh_app_windows` | `bool` | No | `True` | Whether to refresh the list of application windows |

#### Returns

**Type**: `List[Dict[str, Any]]`

List of window information dictionaries, each containing:

```python
{
    "id": str,           # Unique window identifier (e.g., "1", "2", "3")
    "name": str,         # Window title/text
    "type": str,         # Control type (e.g., "Window", "Pane")
    "kind": str          # Target kind: "window"
}
```

#### Example

```python
result = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::get_desktop_app_info",
        tool_name="get_desktop_app_info",
        parameters={
            "remove_empty": True,
            "refresh_app_windows": True
        }
    )
])

# Example output:
[
    {
        "id": "1",
        "name": "Visual Studio Code",
        "type": "Window",
        "kind": "window"
    },
    {
        "id": "2",
        "name": "Microsoft Edge",
        "type": "Window",
        "kind": "window"
    }
]
```

---

### 2. get_desktop_app_target_info

Get comprehensive target information for all desktop application windows.

#### Description

Similar to `get_desktop_app_info`, but returns `TargetInfo` objects instead of plain dictionaries. This provides a more structured representation of window information for internal framework use.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `remove_empty` | `bool` | No | `True` | Whether to remove windows with no visible content |
| `refresh_app_windows` | `bool` | No | `True` | Whether to refresh the list of application windows |

#### Returns

**Type**: `List[TargetInfo]`

List of `TargetInfo` objects with properties:
- `id`: Unique identifier
- `name`: Window title
- `type`: Control type
- `kind`: TargetKind.WINDOW

---

### 3. get_app_window_info

Get detailed information about the currently selected application window.

#### Description

Retrieves specific fields of information for the active/selected window. You must select a window using `select_application_window` (HostUIExecutor) before calling this tool.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `field_list` | `List[str]` | Yes | - | List of field names to retrieve |

#### Supported Fields

Common fields include:
- `"control_text"`: Window title/text
- `"control_type"`: Control type (e.g., "Window")
- `"control_rect"`: Bounding rectangle coordinates
- `"process_id"`: Process ID
- `"class_name"`: Window class name
- `"is_visible"`: Visibility status
- `"is_enabled"`: Enabled status

#### Returns

**Type**: `Dict[str, Any]`

Dictionary mapping field names to their values.

#### Example

```python
# First select a window
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_application_window",
        parameters={"id": "1", "name": "Calculator"}
    )
])

# Then get window info
result = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::get_app_window_info",
        tool_name="get_app_window_info",
        parameters={
            "field_list": ["control_text", "control_type", "control_rect"]
        }
    )
])

# Example output:
{
    "control_text": "Calculator",
    "control_type": "Window",
    "control_rect": {"x": 100, "y": 100, "width": 400, "height": 600}
}
```

---

### 4. get_app_window_controls_info

Get information about all UI controls in the selected application window.

#### Description

Scans the currently selected window and retrieves information about all interactive controls (buttons, text boxes, etc.). This is essential for understanding what actions can be performed on the window.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `field_list` | `List[str]` | Yes | - | List of field names to retrieve for each control |

#### Supported Fields

- `"label"`: Control identifier/label
- `"control_text"`: Text content of the control
- `"control_type"`: Type of control (Button, Edit, etc.)
- `"control_rect"`: Bounding rectangle
- `"is_enabled"`: Whether control is enabled
- `"is_visible"`: Whether control is visible

#### Returns

**Type**: `List[Dict[str, Any]]`

List of dictionaries, each representing one UI control.

#### Example

```python
result = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::get_app_window_controls_info",
        tool_name="get_app_window_controls_info",
        parameters={
            "field_list": ["label", "control_text", "control_type"]
        }
    )
])

# Example output:
[
    {
        "label": "1",
        "control_text": "Submit",
        "control_type": "Button"
    },
    {
        "label": "2",
        "control_text": "",
        "control_type": "Edit"
    }
]
```

---

### 5. get_app_window_controls_target_info

Get `TargetInfo` objects for all controls in the selected window.

#### Description

Similar to `get_app_window_controls_info`, but returns structured `TargetInfo` objects for internal framework use.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `field_list` | `List[str]` | Yes | - | List of field names to retrieve |

#### Returns

**Type**: `List[TargetInfo]`

List of `TargetInfo` objects, each with:
- `kind`: TargetKind.CONTROL
- `id`: Control identifier
- `name`: Control text
- `type`: Control type
- `rect`: Bounding rectangle
- `source`: "uia"

---

### 6. capture_window_screenshot

Capture a screenshot of the currently selected application window.

#### Description

Takes a screenshot of the active window and returns it as base64-encoded image data. This is crucial for visual observation and LLM vision capabilities.

#### Parameters

None

#### Returns

**Type**: `str`

Base64-encoded PNG image data.

#### Example

```python
result = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::capture_window_screenshot",
        tool_name="capture_window_screenshot",
        parameters={}
    )
])

# Result is base64 string: "iVBORw0KGgoAAAANSUhEUgAA..."
```

#### Error Handling

Returns error message string if screenshot capture fails:
```
"Error: No window selected"
"Error capturing screenshot: {error_details}"
```

---

### 7. capture_desktop_screenshot

Capture a screenshot of the entire desktop or primary screen.

#### Description

Takes a screenshot of the desktop environment, either all monitors or just the primary screen.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `all_screens` | `bool` | No | `True` | Capture all screens (True) or primary screen only (False) |

#### Returns

**Type**: `str`

Base64-encoded PNG image data of the desktop screenshot.

#### Example

```python
# Capture all screens
result = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::capture_desktop_screenshot",
        tool_name="capture_desktop_screenshot",
        parameters={"all_screens": True}
    )
])

# Capture primary screen only
result = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::capture_desktop_screenshot",
        tool_name="capture_desktop_screenshot",
        parameters={"all_screens": False}
    )
])
```

---

### 8. get_ui_tree

Get the complete UI tree structure for the selected window.

#### Description

Retrieves the hierarchical structure of all UI elements in the window as a tree. This provides deep insight into the window's layout and control relationships.

#### Parameters

None

#### Returns

**Type**: `Dict[str, Any]`

UI tree structure as a nested dictionary representing the control hierarchy.

#### Example

```python
result = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::get_ui_tree",
        tool_name="get_ui_tree",
        parameters={}
    )
])

# Example output (simplified):
{
    "control_type": "Window",
    "name": "Calculator",
    "children": [
        {
            "control_type": "Pane",
            "name": "Display",
            "children": [...]
        },
        {
            "control_type": "Button",
            "name": "1"
        }
    ]
}
```

#### Error Handling

Returns error dictionary if UI tree extraction fails:
```python
{"error": "No window selected"}
{"error": "Error getting UI tree: {details}"}
```

## Configuration

### Basic Configuration

```yaml
HostAgent:
  default:
    data_collection:
      - namespace: UICollector
        type: local
        reset: false

AppAgent:
  default:
    data_collection:
      - namespace: UICollector
        type: local
        reset: false
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `namespace` | `str` | Must be `"UICollector"` |
| `type` | `str` | Deployment type: `"local"` |
| `reset` | `bool` | Whether to reset server state between tasks |

## Internal State

The UICollector maintains shared state across operations:

- **photographer**: Screenshot capture facade
- **control_inspector**: UI control inspection facade
- **selected_app_window**: Currently selected window (set by HostUIExecutor)
- **last_app_windows**: Cached list of desktop windows
- **control_dict**: Dictionary mapping control IDs to control objects

## Usage Patterns

### Pattern 1: Complete Desktop Observation

```python
# 1. Get all windows
windows = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::get_desktop_app_info", ...)
])

# 2. Capture desktop screenshot
screenshot = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::capture_desktop_screenshot", ...)
])

# 3. Select target window
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_application_window",
        parameters={"id": "1", "name": "Calculator"}
    )
])

# 4. Get window controls
controls = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::get_app_window_controls_info",
        parameters={"field_list": ["label", "control_text", "control_type"]}
    )
])
```

### Pattern 2: Window-Specific Observation

```python
# After window is selected by HostUIExecutor...

# Get window info
window_info = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::get_app_window_info",
        parameters={"field_list": ["control_text", "control_rect"]}
    )
])

# Get window screenshot
screenshot = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::capture_window_screenshot", ...)
])

# Get UI controls
controls = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::get_app_window_controls_info",
        parameters={"field_list": ["label", "control_text"]}
    )
])
```

## Best Practices

### 1. Caching Window Lists

```python
# First call: refresh windows
windows = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::get_desktop_app_info",
        parameters={"refresh_app_windows": True}
    )
])

# Subsequent calls: use cached data
windows = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::get_desktop_app_info",
        parameters={"refresh_app_windows": False}  # Faster
    )
])
```

### 2. Selective Field Retrieval

```python
# ✅ Good: Only request needed fields
controls = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::get_app_window_controls_info",
        parameters={"field_list": ["label", "control_text"]}
    )
])

# ❌ Bad: Don't request unnecessary fields
controls = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::get_app_window_controls_info",
        parameters={"field_list": [
            "label", "control_text", "control_type", "control_rect",
            "is_visible", "is_enabled", "automation_id", "class_name"
        ]}  # Too many fields slow down processing
    )
])
```

### 3. Error Handling

```python
# Always check for window selection
window_info = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::get_app_window_info", ...)
])

if "error" in window_info[0].content[0].text:
    # No window selected
    # Select window first...
```

## Related Documentation

- [Data Collection Overview](../data_collection.md) - Data collection concepts
- [HostUIExecutor](./host_ui_executor.md) - Window selection server
- [AppUIExecutor](./app_ui_executor.md) - UI action execution
- [Local Servers](../local_servers.md) - Local server deployment
