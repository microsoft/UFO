from typing import Dict, List, Any
from fastmcp import FastMCP
from ufo.cs.computer import Computer
from ufo.cs.contracts import (
    CaptureDesktopScreenshotAction,
    CaptureDesktopScreenshotParams,
    CaptureAppWindowScreenshotAction,
    CaptureAppWindowScreenshotParams,
    GetDesktopAppInfoAction,
    GetDesktopAppInfoParams,
    GetAppWindowControlInfoAction,
    GetAppWindowControlInfoParams,
    SelectApplicationWindowAction,
    SelectApplicationWindowParams,
    LaunchApplicationAction,
    LaunchApplicationParams,
    FindControlElementsAction,
    FindControlElementsParams,
    GetUITreeAction,
    GetUITreeParams,
    OperationSequenceAction,
    OperationCommand,
    ClickInputParams,
    SetEditTextParams,
    KeyboardInputParams,
    WheelMouseInputParams,
    ClickOnCoordinatesParams,
    DragOnCoordinatesParams,
)

mcp = FastMCP("UFO MCP Server")

# Initialize the Computer instance
computer = Computer("UFO_MCP_Computer")


@mcp.tool()
def capture_desktop_screenshot(all_screens: bool = True) -> str:
    """
    Capture a screenshot of the desktop.

    Args:
        all_screens: Whether to capture all screens or just the primary screen

    Returns:
        Base64 encoded image data URL
    """
    action = CaptureDesktopScreenshotAction(
        params=CaptureDesktopScreenshotParams(all_screens=all_screens)
    )
    return computer.run_action(action)


@mcp.tool()
def capture_app_window_screenshot(annotation_id: str) -> str:
    """
    Capture a screenshot of a specific application window.

    Args:
        annotation_id: The annotation ID of the application window

    Returns:
        Base64 encoded image data URL
    """
    action = CaptureAppWindowScreenshotAction(
        params=CaptureAppWindowScreenshotParams(annotation_id=annotation_id)
    )
    return computer.run_action(action)


@mcp.tool()
def get_desktop_app_info(
    remove_empty: bool = True, refresh_app_windows: bool = False
) -> List[Dict[str, Any]]:
    """
    Get information about all desktop applications.

    Args:
        remove_empty: Whether to remove empty windows from the result
        refresh_app_windows: Whether to refresh the application windows list

    Returns:
        List of window information dictionaries
    """
    action = GetDesktopAppInfoAction(
        params=GetDesktopAppInfoParams(
            remove_empty=remove_empty, refresh_app_windows=refresh_app_windows
        )
    )
    windows = computer.run_action(action)
    # Convert WindowInfo objects to dictionaries for JSON serialization
    return [
        window.model_dump() if hasattr(window, "model_dump") else window.__dict__
        for window in windows
    ]


@mcp.tool()
def get_app_window_control_info(annotation_id: str) -> Dict[str, Any]:
    """
    Get control information for a specific application window.

    Args:
        annotation_id: The annotation ID of the application window

    Returns:
        Dictionary containing window info and controls
    """
    action = GetAppWindowControlInfoAction(
        params=GetAppWindowControlInfoParams(annotation_id=annotation_id)
    )
    result = computer.run_action(action)
    # Convert to dictionary for JSON serialization
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result.__dict__


@mcp.tool()
def select_application_window(window_label: str) -> Dict[str, Any]:
    """
    Select and focus on a specific application window.

    Args:
        window_label: The label/ID of the window to select

    Returns:
        Dictionary with process name and window text
    """
    action = SelectApplicationWindowAction(
        params=SelectApplicationWindowParams(window_label=window_label)
    )
    return computer.run_action(action)


@mcp.tool()
def launch_application(bash_command: str) -> Dict[str, Any]:
    """
    Launch an application using a bash command.

    Args:
        bash_command: The command to execute to launch the application

    Returns:
        Dictionary with process name and window text of the launched application
    """
    action = LaunchApplicationAction(
        params=LaunchApplicationParams(bash_command=bash_command)
    )
    return computer.run_action(action)


@mcp.tool()
def find_control_elements(
    annotation_id: str,
    control_type_list: List[str] = None,
    class_name_list: List[str] = None,
) -> Dict[str, Any]:
    """
    Find control elements in a specific application window.

    Args:
        annotation_id: The annotation ID of the application window
        control_type_list: List of control types to search for
        class_name_list: List of class names to search for

    Returns:
        Dictionary with found control elements
    """
    if control_type_list is None:
        control_type_list = []
    if class_name_list is None:
        class_name_list = []

    action = FindControlElementsAction(
        params=FindControlElementsParams(
            annotation_id=annotation_id,
            control_type_list=control_type_list,
            class_name_list=class_name_list,
        )
    )
    return computer.run_action(action)


@mcp.tool()
def get_ui_tree(annotation_id: str, remove_empty: bool = True) -> Dict[str, Any]:
    """
    Get the UI tree for a specific application window.

    Args:
        annotation_id: The annotation ID of the application window
        remove_empty: Whether to remove empty elements from the tree

    Returns:
        Dictionary representing the UI tree
    """
    action = GetUITreeAction(
        params=GetUITreeParams(annotation_id=annotation_id, remove_empty=remove_empty)
    )
    return computer.run_action(action)


@mcp.tool()
def click_input(
    control_label: str,
    control_text: str = "",
    button: str = "left",
    double: bool = False,
) -> Dict[str, Any]:
    """
    Click on a UI control element.

    Args:
        control_label: The label of the control to click
        control_text: The text of the control (optional)
        button: Mouse button to use ("left", "right", "middle")
        double: Whether to perform a double click

    Returns:
        Dictionary with execution result
    """
    command = OperationCommand(
        command_id="click_input",
        click_input=ClickInputParams(
            control_label=control_label,
            control_text=control_text,
            button=button,
            double=double,
        ),
    )

    action = OperationSequenceAction(params=[command])
    return computer.run_action(action)


@mcp.tool()
def set_edit_text(
    control_label: str, text: str, control_text: str = ""
) -> Dict[str, Any]:
    """
    Set text in an edit control.

    Args:
        control_label: The label of the edit control
        text: The text to set
        control_text: The current text of the control (optional)

    Returns:
        Dictionary with execution result
    """
    command = OperationCommand(
        command_id="set_edit_text",
        set_edit_text=SetEditTextParams(
            control_label=control_label, control_text=control_text, text=text
        ),
    )

    action = OperationSequenceAction(params=[command])
    return computer.run_action(action)


@mcp.tool()
def keyboard_input(
    control_label: str, keys: str, control_text: str = "", control_focus: bool = True
) -> Dict[str, Any]:
    """
    Send keyboard input to a control.

    Args:
        control_label: The label of the control
        keys: The keys to send
        control_text: The text of the control (optional)
        control_focus: Whether to focus the control first

    Returns:
        Dictionary with execution result
    """
    command = OperationCommand(
        command_id="keyboard_input",
        keyboard_input=KeyboardInputParams(
            control_label=control_label,
            control_text=control_text,
            keys=keys,
            control_focus=control_focus,
        ),
    )

    action = OperationSequenceAction(params=[command])
    return computer.run_action(action)


@mcp.tool()
def wheel_mouse_input(
    control_label: str, x_dist: int = 0, y_dist: int = 0, control_text: str = ""
) -> Dict[str, Any]:
    """
    Send mouse wheel input to a control.

    Args:
        control_label: The label of the control
        x_dist: Horizontal scroll distance
        y_dist: Vertical scroll distance
        control_text: The text of the control (optional)

    Returns:
        Dictionary with execution result
    """
    command = OperationCommand(
        command_id="wheel_mouse_input",
        wheel_mouse_input=WheelMouseInputParams(
            control_label=control_label,
            control_text=control_text,
            x_dist=x_dist,
            y_dist=y_dist,
        ),
    )

    action = OperationSequenceAction(params=[command])
    return computer.run_action(action)


@mcp.tool()
def click_on_coordinates(
    x: float,
    y: float,
    button: str = "left",
    double: bool = False,
    control_label: str = "",
    control_text: str = "",
) -> Dict[str, Any]:
    """
    Click on specific coordinates within an application window.

    Args:
        x: X coordinate (fractional, 0.0 to 1.0)
        y: Y coordinate (fractional, 0.0 to 1.0)
        button: Mouse button to use ("left", "right", "middle")
        double: Whether to perform a double click
        control_label: The label of the control (optional)
        control_text: The text of the control (optional)

    Returns:
        Dictionary with execution result
    """
    command = OperationCommand(
        command_id="click_on_coordinates",
        click_on_coordinates=ClickOnCoordinatesParams(
            control_label=control_label,
            control_text=control_text,
            x=x,
            y=y,
            button=button,
            double=double,
        ),
    )

    action = OperationSequenceAction(params=[command])
    return computer.run_action(action)


@mcp.tool()
def drag_on_coordinates(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    duration: float = 1.0,
    button: str = "left",
    key_hold: str = None,
    control_label: str = "",
    control_text: str = "",
) -> Dict[str, Any]:
    """
    Drag from one coordinate to another within an application window.

    Args:
        start_x: Starting X coordinate (fractional, 0.0 to 1.0)
        start_y: Starting Y coordinate (fractional, 0.0 to 1.0)
        end_x: Ending X coordinate (fractional, 0.0 to 1.0)
        end_y: Ending Y coordinate (fractional, 0.0 to 1.0)
        duration: Duration of the drag operation in seconds
        button: Mouse button to use ("left", "right", "middle")
        key_hold: Key to hold during drag (optional)
        control_label: The label of the control (optional)
        control_text: The text of the control (optional)

    Returns:
        Dictionary with execution result
    """
    command = OperationCommand(
        command_id="drag_on_coordinates",
        drag_on_coordinates=DragOnCoordinatesParams(
            control_label=control_label,
            control_text=control_text,
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            duration=duration,
            button=button,
            key_hold=key_hold,
        ),
    )

    action = OperationSequenceAction(params=[command])
    return computer.run_action(action)


@mcp.tool()
def execute_operation_sequence(operations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Execute a sequence of operations on UI controls.

    Args:
        operations: List of operation dictionaries, each containing:
            - command_id: The type of operation (e.g., "click_input", "set_edit_text")
            - Parameters specific to the operation type

    Returns:
        Dictionary with execution result
    """
    commands = []
    for op in operations:
        command_id = op.get("command_id")
        if not command_id:
            continue

        # Create OperationCommand based on command_id
        if command_id == "click_input":
            command = OperationCommand(
                command_id=command_id,
                click_input=ClickInputParams(**op.get("params", {})),
            )
        elif command_id == "set_edit_text":
            command = OperationCommand(
                command_id=command_id,
                set_edit_text=SetEditTextParams(**op.get("params", {})),
            )
        elif command_id == "keyboard_input":
            command = OperationCommand(
                command_id=command_id,
                keyboard_input=KeyboardInputParams(**op.get("params", {})),
            )
        elif command_id == "wheel_mouse_input":
            command = OperationCommand(
                command_id=command_id,
                wheel_mouse_input=WheelMouseInputParams(**op.get("params", {})),
            )
        elif command_id == "click_on_coordinates":
            command = OperationCommand(
                command_id=command_id,
                click_on_coordinates=ClickOnCoordinatesParams(**op.get("params", {})),
            )
        elif command_id == "drag_on_coordinates":
            command = OperationCommand(
                command_id=command_id,
                drag_on_coordinates=DragOnCoordinatesParams(**op.get("params", {})),
            )
        else:
            continue

        commands.append(command)

    if not commands:
        return {"error": "No valid commands provided"}

    action = OperationSequenceAction(params=commands)
    return computer.run_action(action)


# Entry point for running the MCP server
if __name__ == "__main__":
    mcp.run(transport="sse")
