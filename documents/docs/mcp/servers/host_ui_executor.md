# HostUIExecutor Server

## Overview

**HostUIExecutor** is an action server that provides system-level UI automation capabilities for the HostAgent. It enables window management, window switching, and cross-application interactions at the desktop level.

**Server Type:** Action  
**Deployment:** Local (in-process)  
**Agent:** HostAgent  
**LLM-Selectable:** ✅ Yes (LLM chooses when to execute)

## Server Information

| Property | Value |
|----------|-------|
| **Namespace** | `HostUIExecutor` |
| **Server Name** | `UFO UI HostAgent Action MCP Server` |
| **Platform** | Windows |
| **Backend** | UIAutomation (UIA) or Win32 |
| **Tool Type** | `action` |
| **Tool Key Format** | `action::{tool_name}` |

## Tools

### select_application_window

Select an application window for UI automation and set it as the active window.

#### Description

This is the primary tool for window selection in HostAgent workflows. It:
1. Finds the specified window by ID and name
2. Sets focus on the window
3. Optionally maximizes the window
4. Optionally draws a visual outline (for debugging)
5. Initializes UI state for subsequent AppAgent operations

!!!warning "Prerequisites"
    You must call `get_desktop_app_info` (UICollector) first to obtain valid window IDs and names.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | `str` | ✅ Yes | The precise annotated ID of the application window to select. Must match an ID from `get_desktop_app_info` |
| `name` | `str` | ✅ Yes | The precise name of the application window. Must match the name of the selected ID |

#### Returns

**Type**: `Dict[str, Any]`

```python
{
    "root_name": str,       # Application root name (e.g., "WINWORD.EXE")
    "window_info": dict     # WindowInfo object with window details
}
```

#### WindowInfo Structure

```python
{
    "annotation_id": str,           # Window identifier
    "name": str,                    # Window element name
    "title": str,                   # Window title text
    "handle": int,                  # Window handle (HWND)
    "class_name": str,              # Window class name
    "process_id": int,              # Process ID
    "is_visible": bool,             # Visibility status
    "is_minimized": bool,           # Minimized state
    "is_maximized": bool,           # Maximized state
    "is_active": bool,              # Active window status
    "rectangle": {                  # Window bounding rectangle
        "x": int,
        "y": int,
        "width": int,
        "height": int
    },
    "text_content": str,            # Window text
    "control_type": str             # Control type (usually "Window")
}
```

#### Example

```python
# Step 1: Get available windows
windows = await computer.run_actions([
    MCPToolCall(
        tool_key="data_collection::get_desktop_app_info",
        tool_name="get_desktop_app_info",
        parameters={"remove_empty": True}
    )
])

# windows[0].data = [
#     {"id": "1", "name": "Calculator", "type": "Window", "kind": "window"},
#     {"id": "2", "name": "Notepad", "type": "Window", "kind": "window"}
# ]

# Step 2: Select Calculator window
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_application_window",
        tool_name="select_application_window",
        parameters={
            "id": "1",
            "name": "Calculator"
        }
    )
])

# Result:
{
    "root_name": "ApplicationFrameHost.exe",
    "window_info": {
        "annotation_id": "1",
        "title": "Calculator",
        "handle": 12345678,
        "class_name": "ApplicationFrameWindow",
        "process_id": 9876,
        "is_visible": True,
        "is_minimized": False,
        "is_maximized": False,
        "is_active": True,
        "rectangle": {"x": 100, "y": 100, "width": 400, "height": 600}
    }
}
```

#### Error Handling

The tool raises `ToolError` in the following cases:

```python
# Error 1: Missing ID
ToolError("Window id is required for select_application_window")

# Error 2: No windows available
ToolError("No application windows available. Please call get_desktop_app_info first.")

# Error 3: Invalid ID
ToolError("Control with id '99' not found. Available control ids: ['1', '2', '3']")

# Error 4: Failed to set focus
ToolError("Failed to set focus on window: {error_details}")
```

#### Configuration Behavior

The tool respects these configuration settings:

**MAXIMIZE_WINDOW** (default: `False`)
```yaml
# config.yaml
MAXIMIZE_WINDOW: true  # Window is maximized after selection
```

**SHOW_VISUAL_OUTLINE_ON_SCREEN** (default: `True`)
```yaml
# config.yaml
SHOW_VISUAL_OUTLINE_ON_SCREEN: true  # Red outline drawn around window
```

#### Side Effects

!!!warning "Side Effects"
    - ✅ **Changes focus**: Brings target window to foreground
    - ✅ **May maximize**: If `MAXIMIZE_WINDOW` is enabled
    - ✅ **Visual feedback**: Red outline if `SHOW_VISUAL_OUTLINE_ON_SCREEN` is enabled
    - ✅ **State initialization**: Sets up AppPuppeteer for the window

#### Internal State Changes

After `select_application_window` executes:
1. `ui_state.selected_app_window` is set to the window object
2. `ui_state.puppeteer` is initialized with `AppPuppeteer`
3. Available commands are logged for debugging
4. Subsequent UICollector and AppUIExecutor tools can operate on this window

## Configuration

### Basic Configuration

```yaml
HostAgent:
  default:
    action:
      - namespace: HostUIExecutor
        type: local
        reset: false
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `namespace` | `str` | Must be `"HostUIExecutor"` |
| `type` | `str` | Deployment type: `"local"` |
| `reset` | `bool` | Whether to reset server state between tasks (usually `false` for HostUIExecutor) |

## Usage Patterns

### Pattern 1: Basic Window Selection

```python
# 1. Discover windows
windows = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::get_desktop_app_info", ...)
])

# 2. Select target window
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_application_window",
        parameters={"id": "1", "name": "Calculator"}
    )
])

# 3. Now AppAgent can interact with the window
controls = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::get_app_window_controls_info", ...)
])
```

### Pattern 2: Multi-Window Workflow

```python
# Work with first window
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_application_window",
        parameters={"id": "1", "name": "Word"}
    )
])
# ... perform actions on Word ...

# Switch to second window
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_application_window",
        parameters={"id": "2", "name": "Excel"}
    )
])
# ... perform actions on Excel ...
```

### Pattern 3: Verify Before Selection

```python
# Get windows
windows = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::get_desktop_app_info", ...)
])

# Verify target window exists
target_windows = [w for w in windows[0].data if "Calculator" in w["name"]]

if not target_windows:
    logger.error("Calculator not found")
else:
    # Select window
    await computer.run_actions([
        MCPToolCall(
            tool_key="action::select_application_window",
            parameters={
                "id": target_windows[0]["id"],
                "name": target_windows[0]["name"]
            }
        )
    ])
```

## Best Practices

### 1. Always Validate ID and Name

```python
# ✅ Good: Use exact ID and name from get_desktop_app_info
windows = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::get_desktop_app_info", ...)
])

window = windows[0].data[0]  # First window
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_application_window",
        parameters={
            "id": window["id"],      # Exact ID from response
            "name": window["name"]   # Exact name from response
        }
    )
])

# ❌ Bad: Hardcode or guess IDs
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_application_window",
        parameters={"id": "1", "name": "Some Window"}  # May not exist
    )
])
```

### 2. Handle Selection Failures

```python
try:
    result = await computer.run_actions([
        MCPToolCall(
            tool_key="action::select_application_window",
            parameters={"id": window_id, "name": window_name}
        )
    ])
    
    if result[0].is_error:
        logger.error(f"Failed to select window: {result[0].content}")
        # Retry or select alternative window
    else:
        logger.info(f"Selected window: {result[0].data['root_name']}")
        
except Exception as e:
    logger.error(f"Window selection exception: {e}")
```

### 3. Wait After Selection

```python
# Select window
await computer.run_actions([
    MCPToolCall(tool_key="action::select_application_window", ...)
])

# Wait for window to become active
await asyncio.sleep(0.5)

# Now interact with window
await computer.run_actions([
    MCPToolCall(tool_key="data_collection::capture_window_screenshot", ...)
])
```

### 4. Use Visual Outline for Debugging

```yaml
# config.yaml - Enable during development
SHOW_VISUAL_OUTLINE_ON_SCREEN: true  # See red outline on selected window

# config.yaml - Disable in production
SHOW_VISUAL_OUTLINE_ON_SCREEN: false
```

## Integration with AppAgent

After `select_application_window` succeeds, the window becomes the target for **AppAgent** operations:

```python
# HostAgent: Select window
host_result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_application_window",
        parameters={"id": "1", "name": "Calculator"}
    )
])

# AppAgent: Get controls in selected window
app_controls = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::get_app_window_controls_info", ...)
])

# AppAgent: Click a button in selected window
app_click = await computer.run_actions([
    MCPToolCall(
        tool_key="action::click_input",
        tool_name="click_input",
        parameters={"id": "5", "name": "Seven", "button": "left"}
    )
])
```

## Troubleshooting

### Window Not Found

**Problem**: `ToolError("Control with id 'X' not found")`

**Solutions**:
1. Call `get_desktop_app_info` with `refresh_app_windows=True`
2. Verify window is not minimized or hidden
3. Check window still exists (hasn't been closed)

### Focus Failed

**Problem**: `ToolError("Failed to set focus on window")`

**Solutions**:
1. Check window is not disabled or unresponsive
2. Verify window process is running
3. Ensure no modal dialogs are blocking focus
4. Try again after a short delay

### Wrong Window Selected

**Problem**: Selected wrong window with similar name

**Solutions**:
1. Use more specific name matching
2. Check `process_id` or `class_name` in window info
3. Filter windows by additional criteria before selection

## Related Documentation


- [UICollector](./ui_collector.md) - Window discovery server
- [AppUIExecutor](./app_ui_executor.md) - Window interaction server
- [Action Servers](../action.md) - Action server concepts
- [HostAgent](../../ufo2/host_agent/overview.md) - HostAgent architecture

