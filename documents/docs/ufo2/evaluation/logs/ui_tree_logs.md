# UI Tree Logs

UFO can capture the complete UI control tree of application windows at every step. This structured data represents the hierarchical UI layout and is useful for analysis and debugging.

## Configuration

Enable UI tree logging by setting `SAVE_UI_TREE: true` in `config_dev.yaml`.

**Location:** `logs/{task_name}/ui_tree/`

**File naming:** `step_{step_number}.json`

## Example
    
```json
{
    "id": "node_0",
    "name": "Mail - Chaoyun Zhang - Outlook",
    "control_type": "Window",
    "rectangle": {
        "left": 628,
        "top": 258,
        "right": 3508,
        "bottom": 1795
    },
    "adjusted_rectangle": {
        "left": 0,
        "top": 0,
        "right": 2880,
        "bottom": 1537
    },
    "relative_rectangle": {
        "left": 0.0,
        "top": 0.0,
        "right": 1.0,
        "bottom": 1.0
    },
    "level": 0,
    "children": [
        {
            "id": "node_1",
            "name": "",
            "control_type": "Pane",
            "rectangle": {
                "left": 3282,
                "top": 258,
                "right": 3498,
                "bottom": 330
            },
            "adjusted_rectangle": {
                "left": 2654,
                "top": 0,
                "right": 2870,
                "bottom": 72
            },
            "relative_rectangle": {
                "left": 0.9215277777777777,
                "top": 0.0,
                "right": 0.9965277777777778,
                "bottom": 0.0468445022771633
            },
            "level": 1,
            "children": []
        }
    ]
}
```


## Field Reference

| Field | Description | Type |
| --- | --- | --- |
| `id` | Unique node identifier in the tree | String |
| `name` | Control element name/text | String |
| `control_type` | UI element type (Window, Button, Edit, etc.) | String |
| `rectangle` | Absolute screen coordinates | Dictionary |
| `adjusted_rectangle` | Coordinates relative to window | Dictionary |
| `relative_rectangle` | Normalized coordinates (0.0-1.0) | Dictionary |
| `level` | Depth in the UI tree hierarchy | Integer |
| `children` | Child UI elements | List |

### Rectangle Structure

All rectangle fields contain:

```json
{
    "left": 0,
    "top": 0,
    "right": 100,
    "bottom": 100
}
```

## Usage

UI tree logs enable:

- Understanding application structure
- Analyzing control element hierarchy
- Debugging control selection issues
- Training ML models on UI data

!!! note "Performance Impact"
    Saving UI trees increases execution latency. Disable when not needed for data collection.

## Reference

:::automator.ui_control.ui_tree.UITree