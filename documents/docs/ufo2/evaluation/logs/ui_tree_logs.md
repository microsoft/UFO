# UI Tree Logs

UFO can save the entire UI tree of the application window at every step for data collection purposes. The UI tree can represent the application's UI structure, including the window, controls, and their properties. The UI tree logs are saved in the `logs/{task_name}/ui_tree` folder. You have to set the `SAVE_UI_TREE` flag to `True` in the `config_dev.yaml` file to enable the UI tree logs. Below is an example of the UI tree logs for application:
    
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


## Fields in the UI tree logs
Below is a table of the fields in the UI tree logs:

| Field | Description | Type |
| --- | --- | --- |
| id | The unique identifier of the UI tree node. | String |
| name | The name of the UI tree node. | String |
| control_type | The type of the UI tree node. | String |
| rectangle | The absolute position of the UI tree node. | Dictionary |
| adjusted_rectangle | The adjusted position of the UI tree node. | Dictionary |
| relative_rectangle | The relative position of the UI tree node. | Dictionary |
| level | The level of the UI tree node. | Integer |
| children | The children of the UI tree node. | List of UI tree nodes |

# Reference

:::automator.ui_control.ui_tree.UITree

<br>

!!!note
    Save the UI tree logs may increase the latency of the system. It is recommended to set the `SAVE_UI_TREE` flag to `False` when you do not need the UI tree logs.