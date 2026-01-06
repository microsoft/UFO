# HardwareExecutor Server

## Overview

**HardwareExecutor** provides hardware control capabilities including Arduino HID, BB-8 test fixture, robot arm, mouse control, and screenshot capture.

**Server Type:** Action  
**Deployment:** HTTP (remote server)  
**Default Port:** 8006  
**LLM-Selectable:** ✅ Yes

## Server Information

| Property | Value |
|----------|-------|
| **Namespace** | `HardwareExecutor` |
| **Server Name** | `Echo Base MCP Server` |
| **Platform** | Cross-platform (requires hardware) |
| **Tool Type** | `action` |
| **Deployment** | HTTP server (stateless) |

## Tool Categories

### 1. Arduino HID Tools (Keyboard/Mouse Emulation)
### 2. Mouse Control Tools
### 3. BB-8 Test Fixture Tools
### 4. Robot Arm Tools
### 5. Screenshot Tool

## Arduino HID Tools

### arduino_hid_status

Get Arduino HID device status.

**Returns**: `Dict[str, Any]` with `connected`, `status`, `device`

---

### arduino_hid_connect

Connect to Arduino HID device.

**Returns**: `Dict[str, Any]` with success message

---

### arduino_hid_disconnect

Disconnect from Arduino HID device.

**Returns**: `Dict[str, Any]` with success message

---

### type_text

Type a string of text via Arduino HID.

**Parameters**:
- `text` (`str`): Text to type

**Returns**: Success message

**Example**:
```python
await computer.run_actions([
    MCPToolCall(
        tool_key="action::type_text",
        tool_name="type_text",
        parameters={"text": "Hello, World!"}
    )
])
```

---

### press_key_sequence

Press a sequence of keys.

**Parameters**:
- `keys` (`List[str]`): List of key names
- `interval` (`float`): Interval between key presses (default: 0.1)

**Example**:
```python
await computer.run_actions([
    MCPToolCall(
        tool_key="action::press_key_sequence",
        tool_name="press_key_sequence",
        parameters={
            "keys": ["a", "b", "c"],
            "interval": 0.2
        }
    )
])
```

---

### press_hotkey

Press multiple keys simultaneously (hotkey combination).

**Parameters**:
- `keys` (`List[str]`): List of keys to press together

**Example**:
```python
# Ctrl+C
await computer.run_actions([
    MCPToolCall(
        tool_key="action::press_hotkey",
        tool_name="press_hotkey",
        parameters={"keys": ["ctrl", "c"]}
    )
])
```

## Mouse Control Tools

### move_mouse

Move the mouse pointer.

**Parameters**:
- `x` (`int`): X coordinate
- `y` (`int`): Y coordinate
- `absolute` (`bool`): Absolute (True) or relative (False) positioning (default: False)

---

### click_mouse

Click mouse button.

**Parameters**:
- `button` (`str`): `"left"`, `"right"`, or `"middle"` (default: `"left"`)
- `count` (`int`): Number of clicks (default: 1)
- `interval` (`float`): Interval between clicks (default: 0.1)

---

### press_mouse_button

Press and hold mouse button.

**Parameters**:
- `button` (`str`): Mouse button (default: `"left"`)

---

### release_mouse_button

Release mouse button.

**Parameters**:
- `button` (`str`): Mouse button (default: `"left"`)

---

### scroll_mouse

Scroll mouse wheel.

**Parameters**:
- `vertical` (`int`): Vertical scroll amount (default: 0)
- `horizontal` (`int`): Horizontal scroll amount (default: 0)

**Example**:
```python
# Scroll down
await computer.run_actions([
    MCPToolCall(
        tool_key="action::scroll_mouse",
        tool_name="scroll_mouse",
        parameters={"vertical": -5, "horizontal": 0}
    )
])
```

---

### drag_mouse

Drag mouse from start to end position.

**Parameters**:
- `start` (`Tuple[int, int]`): Start (x, y) coordinates
- `end` (`Tuple[int, int]`): End (x, y) coordinates
- `button` (`str`): Mouse button (default: `"left"`)
- `duration` (`float`): Drag duration in seconds (default: 0.5)

**Example**:
```python
await computer.run_actions([
    MCPToolCall(
        tool_key="action::drag_mouse",
        tool_name="drag_mouse",
        parameters={
            "start": [100, 100],
            "end": [300, 300],
            "duration": 1.0
        }
    )
])
```

---

### double_click_mouse

Perform double-click.

**Parameters**:
- `button` (`str`): Mouse button (default: `"left"`)

---

### right_click_mouse

Shortcut for right-click.

---

### middle_click_mouse

Shortcut for middle-click.

## BB-8 Test Fixture Tools

Test fixture for Surface device testing.

### bb8_status

Get BB-8 test fixture status.

---

### bb8_connect / bb8_disconnect

Connect/disconnect to BB-8.

---

### bb8_usb_port_plug / bb8_usb_port_unplug

Plug/unplug USB device.

**Parameters**:
- `port_name` (`str`): USB port name

---

### bb8_psu_charger_plug / bb8_psu_charger_unplug

Plug/unplug PSU charger.

---

### bb8_blade_attach / bb8_blade_detach

Attach/detach blade.

---

### bb8_lid_open / bb8_lid_close

Open/close lid.

---

### bb8_button_press

Press a physical button.

**Parameters**:
- `button_name` (`str`): Button name

---

### bb8_button_long_press

Long press a button.

**Parameters**:
- `button_name` (`str`): Button name

## Robot Arm Tools

Physical robot arm for touchscreen interaction.

### robot_arm_status

Get robot arm status (position, connection).

---

### robot_arm_connect / robot_arm_disconnect

Connect/disconnect robot arm.

---

### touch_screen

Simulate touch at specific screen location.

**Parameters**:
- `location` (`Tuple[int, int]`): (x, y) coordinates

**Example**:
```python
await computer.run_actions([
    MCPToolCall(
        tool_key="action::touch_screen",
        tool_name="touch_screen",
        parameters={"location": [500, 300]}
    )
])
```

---

### draw_on_screen

Draw on screen by following coordinate path.

**Parameters**:
- `path` (`List[Tuple[int, int]]`): List of (x, y) coordinates

---

### tap_screen

Simulate tap(s) on screen.

**Parameters**:
- `location` (`Tuple[int, int]`): Tap location
- `count` (`int`): Number of taps (default: 1)
- `interval` (`float`): Interval between taps (default: 0.1)

---

### swipe_screen

Simulate swipe gesture.

**Parameters**:
- `start_location` (`Tuple[int, int]`): Start position
- `end_location` (`Tuple[int, int]`): End position
- `duration` (`float`): Swipe duration (default: 0.5)

---

### long_press_screen

Simulate long press.

**Parameters**:
- `location` (`Tuple[int, int]`): Press location
- `duration` (`float`): Press duration (default: 1.0)

---

### double_tap_screen

Simulate double tap.

**Parameters**:
- `location` (`Tuple[int, int]`): Tap location

---

### press_key

Simulate keyboard key press via robot arm.

**Parameters**:
- `key` (`str`): Key to press
- `modifiers` (`List[str]`): Modifier keys (e.g., `["ctrl", "shift"]`)
- `duration` (`float`): Press duration (default: 0.1)

---

### tap_trackpad / swipe_trackpad

Simulate trackpad interactions.

## Screenshot Tool

### take_screenshot

Capture a screenshot.

**Returns**: `str` - Base64-encoded image data

**Example**:
```python
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::take_screenshot",
        tool_name="take_screenshot",
        parameters={}
    )
])
# result[0].data = "iVBORw0KGgoAAAANSUhEUgAA..."
```

## Configuration

```yaml
# Client configuration (Windows agent)
HostAgent:
  default:
    action:
      - namespace: HardwareExecutor
        type: http
        host: "192.168.1.100"  # Hardware server IP
        port: 8006
        path: "/mcp"
```

## Deployment

### Starting the Server

```bash
# Start hardware MCP server
python -m ufo.client.mcp.http_servers.hardware_mcp_server --host 0.0.0.0 --port 8006

# Output:
# ==================================================
# UFO Hardware MCP Server
# Hardware automation via Model Context Protocol
# Running on 0.0.0.0:8006
# ==================================================
```

### Configuration

**Default Values**:
- Host: `localhost`
- Port: `8006`
- Path: `/mcp`

## Best Practices

### 1. Network Configuration

```yaml
# Use IP address for remote hardware
action:
  - namespace: HardwareExecutor
    type: http
    host: "192.168.1.100"  # Hardware server
    port: 8006
```

### 2. Error Handling

All tools return dict with `success` key:

```python
result = await computer.run_actions([
    MCPToolCall(tool_key="action::touch_screen", parameters={"location": [100, 100]})
])

if not result[0].data.get("success"):
    logger.error(f"Touch failed: {result[0].data.get('error')}")
```

### 3. Physical Hardware Requirements

- Arduino HID: Requires Arduino board with HID firmware
- BB-8: Microsoft Surface test fixture
- Robot Arm: Physical robot arm setup
- Network: Stable network connection for HTTP communication

## Use Cases

### Automated Testing

```python
# 1. Connect to hardware
await computer.run_actions([
    MCPToolCall(tool_key="action::robot_arm_connect", parameters={})
])

# 2. Touch screen at login button
await computer.run_actions([
    MCPToolCall(tool_key="action::touch_screen", parameters={"location": [500, 700]})
])

# 3. Take screenshot to verify
screenshot = await computer.run_actions([
    MCPToolCall(tool_key="action::take_screenshot", parameters={})
])
```

## Related Documentation

- [BashExecutor](./bash_executor.md) - Linux command execution
- [Remote Servers](../remote_servers.md) - HTTP deployment guide
- [Action Servers](../action.md) - Action server concepts
