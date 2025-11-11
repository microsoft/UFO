# AppUIExecutor Server

## Overview

**AppUIExecutor** is an action server that provides application-level UI automation for the AppAgent. It enables precise interaction with UI controls within the currently selected application window.

**Server Type:** Action  
**Deployment:** Local (in-process)  
**Agent:** AppAgent  
**LLM-Selectable:** ✅ Yes

## Server Information

| Property | Value |
|----------|-------|
| **Namespace** | `AppUIExecutor` |
| **Server Name** | `UFO UI AppAgent Action MCP Server` |
| **Platform** | Windows |
| **Tool Type** | `action` |
| **Tool Key Format** | `action::{tool_name}` |

## Tools Summary

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `click_input` | Click on a UI control | `id`, `name`, `button`, `double` |
| `click_on_coordinates` | Click at fractional coordinates | `x`, `y`, `button`, `double` |
| `drag_on_coordinates` | Drag between two points | `start_x`, `start_y`, `end_x`, `end_y`, `button`, `duration`, `key_hold` |
| `set_edit_text` | Set text in edit control | `id`, `name`, `text`, `clear_current_text` |
| `keyboard_input` | Send keyboard keys | `id`, `name`, `keys`, `control_focus` |
| `wheel_mouse_input` | Scroll with mouse wheel | `id`, `name`, `wheel_dist` |
| `texts` | Get text from control | `id`, `name` |
| `wait` | Wait for specified time | `seconds` |
| `summary` | Provide observation summary | `text` |

## Tool Details

### click_input

Click on a UI control element using the mouse.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `id` | `str` | ✅ Yes | - | Control ID from `get_app_window_controls_info` |
| `name` | `str` | ✅ Yes | - | Control name matching the ID |
| `button` | `str` | No | `"left"` | Mouse button: `"left"`, `"right"`, `"middle"`, `"x"` |
| `double` | `bool` | No | `False` | Perform double-click |

#### Returns

`str` - Result message or warning if name doesn't match ID

#### Example

```python
await computer.run_actions([
    MCPToolCall(
        tool_key="action::click_input",
        tool_name="click_input",
        parameters={
            "id": "5",
            "name": "Submit Button",
            "button": "left",
            "double": False
        }
    )
])
```

---

### click_on_coordinates

Click at specific fractional coordinates within the window (0.0-1.0).

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `x` | `float` | ✅ Yes | - | Relative x-coordinate (0.0-1.0) |
| `y` | `float` | ✅ Yes | - | Relative y-coordinate (0.0-1.0) |
| `button` | `str` | No | `"left"` | Mouse button |
| `double` | `bool` | No | `False` | Double-click |

#### Example

```python
# Click at center of window
await computer.run_actions([
    MCPToolCall(
        tool_key="action::click_on_coordinates",
        tool_name="click_on_coordinates",
        parameters={"x": 0.5, "y": 0.5, "button": "left"}
    )
])
```

---

### drag_on_coordinates

Drag from one fractional coordinate to another.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_x` | `float` | ✅ Yes | - | Start x-coordinate (0.0-1.0) |
| `start_y` | `float` | ✅ Yes | - | Start y-coordinate (0.0-1.0) |
| `end_x` | `float` | ✅ Yes | - | End x-coordinate (0.0-1.0) |
| `end_y` | `float` | ✅ Yes | - | End y-coordinate (0.0-1.0) |
| `button` | `str` | No | `"left"` | Mouse button |
| `duration` | `float` | No | `1.0` | Drag duration in seconds |
| `key_hold` | `str` | No | `None` | Key to hold (`"ctrl"`, `"shift"`) |

#### Example

```python
# Drag from top-left to bottom-right
await computer.run_actions([
    MCPToolCall(
        tool_key="action::drag_on_coordinates",
        tool_name="drag_on_coordinates",
        parameters={
            "start_x": 0.2, "start_y": 0.2,
            "end_x": 0.8, "end_y": 0.8,
            "duration": 1.5
        }
    )
])
```

---

### set_edit_text

Set text in an edit control.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `id` | `str` | ✅ Yes | - | Control ID |
| `name` | `str` | ✅ Yes | - | Control name |
| `text` | `str` | ✅ Yes | - | Text to set |
| `clear_current_text` | `bool` | No | `False` | Clear existing text first |

#### Example

```python
await computer.run_actions([
    MCPToolCall(
        tool_key="action::set_edit_text",
        tool_name="set_edit_text",
        parameters={
            "id": "3",
            "name": "Search Box",
            "text": "Hello World",
            "clear_current_text": True
        }
    )
])
```

---

### keyboard_input

Send keyboard input to a control or application.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `id` | `str` | ✅ Yes | - | Control ID |
| `name` | `str` | ✅ Yes | - | Control name |
| `keys` | `str` | ✅ Yes | - | Key sequence (e.g., `"{VK_CONTROL}c"`, `"{TAB 2}"`) |
| `control_focus` | `bool` | No | `True` | Focus control before sending keys |

#### Example

```python
# Copy selected text (Ctrl+C)
await computer.run_actions([
    MCPToolCall(
        tool_key="action::keyboard_input",
        tool_name="keyboard_input",
        parameters={
            "id": "1",
            "name": "Editor",
            "keys": "{VK_CONTROL}c",
            "control_focus": True
        }
    )
])

# Press Tab twice
await computer.run_actions([
    MCPToolCall(
        tool_key="action::keyboard_input",
        tool_name="keyboard_input",
        parameters={
            "id": "1",
            "name": "Form",
            "keys": "{TAB 2}"
        }
    )
])
```

---

### wheel_mouse_input

Scroll using mouse wheel on a control.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `id` | `str` | ✅ Yes | - | Control ID |
| `name` | `str` | ✅ Yes | - | Control name |
| `wheel_dist` | `int` | No | `0` | Wheel notches (positive=up, negative=down) |

#### Example

```python
# Scroll down 5 notches
await computer.run_actions([
    MCPToolCall(
        tool_key="action::wheel_mouse_input",
        tool_name="wheel_mouse_input",
        parameters={
            "id": "10",
            "name": "Content Panel",
            "wheel_dist": -5
        }
    )
])
```

---

### texts

Retrieve all text content from a control.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `id` | `str` | ✅ Yes | - | Control ID |
| `name` | `str` | ✅ Yes | - | Control name |

#### Returns

`str` - Text content of the control

#### Example

```python
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::texts",
        tool_name="texts",
        parameters={"id": "7", "name": "Status Label"}
    )
])
# result[0].data = "Operation completed successfully"
```

---

### wait

Wait for a specified duration (non-blocking).

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `seconds` | `float` | ✅ Yes | - | Wait duration (max 300s) |

#### Example

```python
# Wait for 2 seconds
await computer.run_actions([
    MCPToolCall(
        tool_key="action::wait",
        tool_name="wait",
        parameters={"seconds": 2.0}
    )
])
```

---

### summary

Provide a visual summary of observations.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | `str` | ✅ Yes | - | Summary text based on visual observation |

#### Returns

`str` - The summary text (passed through)

#### Example

```python
await computer.run_actions([
    MCPToolCall(
        tool_key="action::summary",
        tool_name="summary",
        parameters={
            "text": "Window shows login form with username and password fields. Submit button is enabled."
        }
    )
])
```

## Configuration

```yaml
AppAgent:
  default:
    action:
      - namespace: AppUIExecutor
        type: local
        reset: false
  
  # App-specific configuration
  WINWORD.EXE:
    action:
      - namespace: AppUIExecutor
        type: local
      - namespace: WordCOMExecutor  # Additional server for Word
        type: local
```

## Best Practices

### 1. Always Verify Control ID and Name

```python
# ✅ Good
controls = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::get_app_window_controls_info", ...)
])

control = controls[0].data[0]  # Get first control
await computer.run_actions([
    MCPToolCall(
        tool_key="action::click_input",
        parameters={
            "id": control["label"],
            "name": control["control_text"]
        }
    )
])

# ❌ Bad: Hardcode IDs
await computer.run_actions([
    MCPToolCall(
        tool_key="action::click_input",
        parameters={"id": "1", "name": "Button"}  # May not exist
    )
])
```

### 2. Use Coordinates for Unlabeled Elements

```python
# When control not in control list
await computer.run_actions([
    MCPToolCall(
        tool_key="action::click_on_coordinates",
        parameters={"x": 0.75, "y": 0.25}  # Top-right area
    )
])
```

### 3. Wait After Actions

```python
# Click button
await computer.run_actions([
    MCPToolCall(tool_key="action::click_input", ...)
])

# Wait for UI update
await computer.run_actions([
    MCPToolCall(tool_key="action::wait", parameters={"seconds": 1.0})
])

# Verify result
screenshot = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::capture_window_screenshot", ...)
])
```

## Related Documentation

- [HostUIExecutor](./host_ui_executor.md) - Window selection
- [UICollector](./ui_collector.md) - Control discovery
- [Action Servers](../action.md) - Action concepts
- [AppAgent Overview](../../ufo2/app_agent/overview.md) - AppAgent architecture
