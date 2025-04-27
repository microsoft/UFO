# GUI Automator

The GUI Automator enables to mimic the operations of mouse and keyboard on the application's UI controls. UFO uses the **UIA** or **Win32** APIs to interact with the application's UI controls, such as buttons, edit boxes, and menus.


## Configuration

There are several configurations that need to be set up before using the UI Automator in the `config_dev.yaml` file. Below is the list of configurations related to the UI Automator:

| Configuration Option    | Description                                                                                             | Type     | Default Value |
|-------------------------|---------------------------------------------------------------------------------------------------------|----------|---------------|
| `CONTROL_BACKEND`       | The list of backend for control action, currently supporting `uia` and `win32` and `onmiparser`         | List     | ["uia"]       |
| `CONTROL_LIST`          | The list of widgets allowed to be selected.                                                             | List     | ["Button", "Edit", "TabItem", "Document", "ListItem", "MenuItem", "ScrollBar", "TreeItem", "Hyperlink", "ComboBox", "RadioButton", "DataItem"] |
| `ANNOTATION_COLORS`     | The colors assigned to different control types for annotation.                                          | Dictionary | {"Button": "#FFF68F", "Edit": "#A5F0B5", "TabItem": "#A5E7F0", "Document": "#FFD18A", "ListItem": "#D9C3FE", "MenuItem": "#E7FEC3", "ScrollBar": "#FEC3F8", "TreeItem": "#D6D6D6", "Hyperlink": "#91FFEB", "ComboBox": "#D8B6D4"} |
| `API_PROMPT`           | The prompt for the UI automation API. | String | "ufo/prompts/share/base/api.yaml"          |
| `CLICK_API`              | The API used for click action, can be `click_input` or `click`. | String  | "click_input" |
| `INPUT_TEXT_API`         | The API used for input text action, can be `type_keys` or `set_text`. | String  | "type_keys"   |
| `INPUT_TEXT_ENTER`       | Whether to press enter after typing the text.    | Boolean | False         |



## Receiver

The receiver of the UI Automator is the `ControlReceiver` class defined in the `ufo/automator/ui_control/controller/control_receiver` module. It is initialized with the application's window handle and control wrapper that executes the actions. The `ControlReceiver` provides functionalities to interact with the application's UI controls. Below is the reference for the `ControlReceiver` class:

::: automator.ui_control.controller.ControlReceiver

<br>

## Command

The command of the UI Automator is the `ControlCommand` class defined in the `ufo/automator/ui_control/controller/ControlCommand` module. It encapsulates the function and parameters required to execute the action. The `ControlCommand` class is a base class for all commands in the UI Automator application. Below is an example of a `ClickInputCommand` class that inherits from the `ControlCommand` class:

```python
@ControlReceiver.register
class ClickInputCommand(ControlCommand):
    """
    The click input command class.
    """

    def execute(self) -> str:
        """
        Execute the click input command.
        :return: The result of the click input command.
        """
        return self.receiver.click_input(self.params)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the atomic command.
        :return: The name of the atomic command.
        """
        return "click_input"
```

!!! note
    The concrete command classes must implement the `execute` method to execute the action and the `name` method to return the name of the atomic command.

!!! note
    Each command must register with a specific `ControlReceiver` to be executed using the `@ControlReceiver.register` decorator.

Below is the list of available commands in the UI Automator that are currently supported by UFO:

| Command Name | Function Name | Description |
|--------------|---------------|-------------|
| `ClickInputCommand` | `click_input` | Click the control item with the mouse. |
| `ClickOnCoordinatesCommand` | `click_on_coordinates` | Click on the specific fractional coordinates of the application window. |
| `DragOnCoordinatesCommand` | `drag_on_coordinates` | Drag the mouse on the specific fractional coordinates of the application window. |
| `SetEditTextCommand` | `set_edit_text` | Add new text to the control item. |
| `GetTextsCommand` | `texts` | Get the text of the control item. |
| `WheelMouseInputCommand` | `wheel_mouse_input` | Scroll the control item. |
| `KeyboardInputCommand` | `keyboard_input` | Simulate the keyboard input. |

!!! tip
    Please refer to the `ufo/prompts/share/base/api.yaml` file for the detailed API documentation of the UI Automator.

!!! tip
    You can customize the commands by adding new command classes to the `ufo/automator/ui_control/controller/ControlCommand` module.
