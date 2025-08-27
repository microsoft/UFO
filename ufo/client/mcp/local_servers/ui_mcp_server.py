#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
UI MCP Servers
Provides two MCP servers:
1. UI Data MCP Server - for data retrieval operations
2. UI Action MCP Server - for UI automation actions
Both servers share the same UI state for coordinated operations.
"""

import logging
import os
from typing import Annotated, Any, Dict, List, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field
from pywinauto.controls.uiawrapper import UIAWrapper

from ufo.agents.processors.actions import ActionSequence, OneStepAction
from ufo.automator.action_execution import ActionSequenceExecutor
from ufo.automator.puppeteer import AppPuppeteer
from ufo.automator.ui_control import ui_tree
from ufo.automator.ui_control.inspector import ControlInspectorFacade
from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.client.mcp.mcp_registry import MCPRegistry
from ufo.config import get_config
from ufo.contracts.contracts import AppWindowControlInfo, ControlInfo, Rect, WindowInfo

# Get config
configs = get_config()
CONTROL_BACKEND = configs.get("CONTROL_BACKEND", ["uia"]) if configs else ["uia"]
BACKEND = "win32" if "win32" in CONTROL_BACKEND else "uia"


def _get_control_rectangle(control: UIAWrapper) -> Optional[Rect]:
    """
    Helper method to extract rectangle coordinates from a control.
    :param control: The UIAWrapper control to extract rectangle from.
    :return: Rect object with coordinates, or None if extraction fails.
    """
    try:
        if hasattr(control, "rectangle"):
            rect = control.rectangle()
            return Rect(
                x=rect.left, y=rect.top, width=rect.width(), height=rect.height()
            )
    except Exception:
        pass
    return None


def _window2window_info(
    window: UIAWrapper, annotation_id: Optional[str] = None
) -> WindowInfo:
    """
    Convert a UIAWrapper window to a WindowInfo object.
    :param window: The UIAWrapper window to convert.
    :return: WindowInfo object with relevant properties.
    """
    return WindowInfo(
        annotation_id=annotation_id,
        name=window.element_info.name if hasattr(window, "element_info") else None,
        title=window.window_text(),
        handle=window.handle,
        class_name=window.class_name(),
        process_id=window.process_id(),
        is_visible=window.is_visible(),
        is_minimized=window.is_minimized(),
        is_maximized=window.is_maximized(),
        is_active=window.is_active(),
        rectangle=_get_control_rectangle(window),
        text_content=window.window_text(),
        control_type=(
            window.element_info.control_type
            if hasattr(window, "element_info")
            else None
        ),
    )


def _control2control_info(
    control: UIAWrapper, annotation_id: Optional[str] = None
) -> ControlInfo:
    """
    Convert a UIAWrapper control to a ControlInfo object.
    :param control: The UIAWrapper control to convert.
    :return: ControlInfo object with relevant properties.
    """
    return ControlInfo(
        annotation_id=annotation_id,
        name=control.element_info.name if hasattr(control, "element_info") else None,
        automation_id=(
            control.element_info.automation_id
            if hasattr(control, "element_info")
            else None
        ),
        class_name=control.class_name(),
        rectangle=_get_control_rectangle(control),
        is_enabled=control.is_enabled(),
        is_visible=control.is_visible(),
        control_type=(
            control.element_info.control_type
            if hasattr(control, "element_info")
            else None
        ),
    )


# Singleton UI server state
class UIServerState:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UIServerState, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.photographer = PhotographerFacade()
            self.control_inspector = ControlInspectorFacade(BACKEND)
            self.selected_app_window: Optional[UIAWrapper] = None
            self.selected_app_window_controls: Optional[Dict[str, UIAWrapper]] = None
            self.puppeteer: Optional[AppPuppeteer] = None
            self.last_app_windows: Optional[Dict[str, UIAWrapper]] = None
            self.grounding_service = (
                None  # Initialize grounding service as None for now
            )
            self.control_dict: Optional[Dict[str, UIAWrapper]] = None
            UIServerState._initialized = True
            self.logger = logging.getLogger(__name__)

    def initialize_for_window(self, window: UIAWrapper) -> None:
        """
        Initialize the puppeteer and controls for a specific window.
        :param window: The UIAWrapper window object to initialize for.
        :return: None
        """
        self.selected_app_window = window

        # Initialize AppPuppeteer with annotation_id like computer.py
        self.puppeteer = AppPuppeteer(
            window.window_text(),
            self.control_inspector.get_application_root_name(window),
        )
        self.logger.info(f"Initialized AppPuppeteer for window: {window.window_text()}")
        self.logger.info(f"Available commands: {self.puppeteer.list_commands()}")


@MCPRegistry.register_factory_decorator("HostUIExecutor")
def create_host_action_mcp_server(*args, **kwargs) -> FastMCP:
    """
    Create and return the HostAgent Action MCP server instance.
    :return: FastMCP instance for HostAgent action operations.
    """
    ui_state = UIServerState()
    action_mcp = FastMCP("UFO UI HostAgent Action MCP Server")

    @action_mcp.tool(tags={"HostAgent"})
    def select_application_window(
        id: Annotated[
            str,
            "Specify the precise label of the application or third-party agents to be selected for the current sub-task, adhering strictly to the provided options in the field of id in the application information.",
        ],
        name: Annotated[
            str,
            "Specify the precise name of the application or third-party agents to be selected for the current sub-task, adhering strictly to the provided options and matching the selected id.",
        ],
    ) -> Dict[str, Any]:
        """
        Select an application window for UI automation.
        :return: Information about the selected window.
        """
        if not id:
            raise ToolError("Window label is required for select_application_window")

        # Use the last app windows retrieved from get_desktop_app_info
        app_window_dict = ui_state.last_app_windows

        if not app_window_dict:
            raise ToolError(
                "No application windows available. Please call get_desktop_app_info first."
            )

        # Find the window with the matching label
        window = app_window_dict.get(id)

        if not window:
            available_windows = list(app_window_dict.keys())
            raise ToolError(
                f"Window with label '{id}' not found. Available windows: {available_windows}"
            )

        # Set focus on the window
        try:
            window.set_focus()

            # Get configurations for window behavior
            if configs and configs.get("MAXIMIZE_WINDOW", False):
                window.maximize()

            if configs and configs.get("SHOW_VISUAL_OUTLINE_ON_SCREEN", True):
                window.draw_outline(colour="red", thickness=3)
        except Exception as e:
            raise ToolError(f"Failed to set focus on window: {str(e)}")

        # Initialize UI state for this window
        ui_state.initialize_for_window(window)

        return {
            "root_name": ui_state.control_inspector.get_application_root_name(window),
            "window_info": _window2window_info(window).model_dump(),
        }

    return action_mcp


@MCPRegistry.register_factory_decorator("AppUIExecutor")
def create_app_action_mcp_server(*args, **kwargs) -> FastMCP:
    """
    Create and return the AppAgent Action MCP server instance.
    :return: FastMCP instance for AppAgent action operations.
    """
    # Get singleton UI state instance
    ui_state = UIServerState()

    def _execute_action_sequence(actions: List[OneStepAction]) -> List[Dict[str, Any]]:
        """
        Execute a sequence of UI actions using direct AppPuppeteer interaction.
        :param actions: List of OneStepAction objects to execute.
        :return: List of execution results.
        """
        if not ui_state.puppeteer or not ui_state.selected_app_window:
            raise ValueError(
                "UI state not initialized. Please select an application window first."
            )

        action_sequence = ActionSequence(actions)

        application_window = ui_state.selected_app_window

        # Execute the sequence like computer.py does
        ActionSequenceExecutor.execute_all(
            action_sequence,
            ui_state.puppeteer,
            ui_state.control_dict or {},
            application_window,
        )

        return action_sequence.get_results()

    def _execute_action(action: OneStepAction) -> Dict[str, Any]:
        """
        Execute a single UI action.
        :param action: OneStepAction object to execute.
        :return: Execution result as a dictionary.
        """
        return _execute_action_sequence([action])[0]

    action_mcp = FastMCP("UFO UI AppAgent Action MCP Server")

    @action_mcp.tool(tags={"AppAgent"}, exclude_args=[])
    def click_input(
        id: Annotated[
            str,
            Field(
                description="The precise annotated ID of the selected control item to be clicked, adhering strictly to the provided options in the field of 'id' in the control information."
            ),
        ],
        name: Annotated[
            str,
            Field(
                description="The precise name of the selected control item to be clicked, adhering strictly to the provided options in the field of 'name' in the control information, and must match the name of its selected id."
            ),
        ],
        button: Annotated[
            str,
            Field(
                description="The mouse button to click. One of ''left'', ''right'', ''middle'' or ''x'"
            ),
        ] = "left",
        double: Annotated[
            bool, Field(description="Whether to perform a double click")
        ] = False,
    ) -> Annotated[Dict, Field(description="None")]:
        """
        Click on a UI control element using the mouse. All type of controls elements are supported.
        """
        action = OneStepAction(
            function="click_input",
            args={"button": button, "double": double},
            control_label=id,
            control_text=name,
            after_status="CONTINUE",
        )

        return _execute_action(action)

    @action_mcp.tool(tags={"AppAgent"}, exclude_args=[])
    def click_on_coordinates(
        x: Annotated[
            float,
            Field(
                description="The relative fractional x-coordinate of the point to click on, ranging from 0.0 to 1.0. The origin is the top-left corner of the application window."
            ),
        ],
        y: Annotated[
            float,
            Field(
                description="The relative fractional y-coordinate of the point to click on, ranging from 0.0 to 1.0. The origin is the top-left corner of the application window."
            ),
        ],
        button: Annotated[
            str,
            Field(description="Mouse button to use ('left', 'right', 'middle')"),
        ] = "left",
        double: Annotated[
            bool, Field(description="Whether to perform a double click")
        ] = False,
    ) -> Annotated[Dict, Field(description="None")]:
        """
        Click on specific coordinates within the application window, instead of clicking on a specific control item.
        This API is useful when the control item is not available in the control item list and screenshot, but you want to click on a specific point in the application window.
        When you use this API, you must estimate the relative fractional x and y coordinates of the point to click on, ranging from 0.0 to 1.0.
        """
        action = OneStepAction(
            function="click_on_coordinates",
            args={"x": x, "y": y, "button": button, "double": double},
            control_label="",
            control_text="",
            after_status="CONTINUE",
        )

        return _execute_action(action)

    @action_mcp.tool(tags={"AppAgent"}, exclude_args=[])
    def drag_on_coordinates(
        start_x: Annotated[
            float,
            Field(
                description="The relative fractional x-coordinate of the starting point to drag from, ranging from 0.0 to 1.0. The origin is the top-left corner of the application window."
            ),
        ],
        start_y: Annotated[
            float,
            Field(
                description="The relative fractional y-coordinate of the starting point to drag from, ranging from 0.0 to 1.0. The origin is the top-left corner of the application window."
            ),
        ],
        end_x: Annotated[
            float,
            Field(
                description="The relative fractional x-coordinate of the ending point to drag to, ranging from 0.0 to 1.0. The origin is the top-left corner of the application window."
            ),
        ],
        end_y: Annotated[
            float,
            Field(
                description="The relative fractional y-coordinate of the ending point to drag to, ranging from 0.0 to 1.0. The origin is the top-left corner of the application window."
            ),
        ],
        button: Annotated[
            str, Field(description="Mouse button to use ('left', 'right', 'middle')")
        ] = "left",
        duration: Annotated[
            float, Field(description="Duration of the drag operation in seconds")
        ] = 1.0,
        key_hold: Annotated[
            Optional[str],
            Field(
                description="Key to hold during drag operation (e.g., 'ctrl', 'shift')"
            ),
        ] = None,
    ) -> Annotated[Dict, Field(description="None")]:
        """
        Drag from one point to another point in the application window, instead of dragging a specific control item.
        This API is useful when the control item is not available in the control item list and screenshot, but you want to drag from one point to another point in the application window.
        When you use this API, you must estimate the relative fractional x and y coordinates of the starting point and ending point to drag from and to, ranging from 0.0 to 1.0.
        The origin is the top-left corner of the application window.
        """
        action = OneStepAction(
            function="drag_on_coordinates",
            args={
                "start_x": start_x,
                "start_y": start_y,
                "end_x": end_x,
                "end_y": end_y,
                "button": button,
                "duration": duration,
                "key_hold": key_hold,
            },
            control_label="",
            control_text="",
            after_status="CONTINUE",
        )

        return _execute_action(action)

    @action_mcp.tool(tags={"AppAgent"}, exclude_args=[])
    def set_edit_text(
        id: Annotated[
            str,
            Field(
                description="The precise annotated ID of the selected control item to be set text, adhering strictly to the provided options in the field of 'id' in the control information."
            ),
        ],
        name: Annotated[
            str,
            Field(
                description="The precise name of the selected control item to be set text, adhering strictly to the provided options in the field of 'name' in the control information, and must match the name of its selected id."
            ),
        ],
        text: Annotated[
            str,
            Field(
                description="The text input to the Edit control item. You must also use Double Backslash escape character to escape the single quote in the string argument."
            ),
        ],
        clear_current_text: Annotated[
            bool,
            Field(
                description="Whether to clear the current text in the Edit before setting the new text. If True, the current text will be completely replaced by the new text."
            ),
        ] = False,
    ) -> Annotated[Dict, Field(description="None")]:
        """
        Set text in a control element. Only works with Edit control items.
        """
        action = OneStepAction(
            function="set_edit_text",
            args={"text": text, "clear_current_text": clear_current_text},
            control_label=id,
            control_text=name,
            after_status="CONTINUE",
        )

        return _execute_action(action)

    @action_mcp.tool(tags={"AppAgent"}, exclude_args=[])
    def keyboard_input(
        id: Annotated[
            str,
            Field(
                description="The precise annotated ID of the selected control item to send keyboard input to, adhering strictly to the provided options in the field of 'id' in the control information."
            ),
        ],
        name: Annotated[
            str,
            Field(
                description="The precise name of the selected control item to send keyboard input to, adhering strictly to the provided options in the field of 'name' in the control information."
            ),
        ],
        keys: Annotated[
            str,
            Field(
                description="Key sequence to send. It can be any key on the keyboard, with special keys represented by their virtual key codes, for example, '{VK_CONTROL}c' for Ctrl+C."
            ),
        ],
        control_focus: Annotated[
            bool,
            Field(
                description="Whether to focus the selected control before sending keys. If False, the hotkeys will operate on the application window."
            ),
        ] = True,
    ) -> Annotated[Dict, Field(description="None")]:
        """
        Simulate keyboard input to a control or the focused application, such as sending key presses or shortcuts.
        For example,
        - keyboard_input(keys="{VK_CONTROL}c") --> Copy the selected text
        - keyboard_input(keys="{TAB 2}") --> Press the Tab key twice.
        """
        action = OneStepAction(
            function="keyboard_input",
            args={"keys": keys, "control_focus": control_focus},
            control_label=id,
            control_text=name,
            after_status="CONTINUE",
        )

        return _execute_action(action)

    @action_mcp.tool(tags={"AppAgent"}, exclude_args=[])
    def wheel_mouse_input(
        id: Annotated[
            str,
            Field(
                description="The precise annotated ID of the selected control item to send mouse wheel input to, adhering strictly to the provided options in the field of 'id' in the control information."
            ),
        ],
        name: Annotated[
            str,
            Field(
                description="The precise name of the selected control item to send mouse wheel input to, adhering strictly to the provided options in the field of 'name' in the control information."
            ),
        ],
        wheel_dist: Annotated[
            int,
            Field(
                description="The number of wheel notches to scroll. Positive values indicate upward scrolling, negative values indicate downward scrolling."
            ),
        ] = 0,
    ) -> Annotated[Dict, Field(description="None")]:
        """
        Send mouse wheel input to scroll a control.
        """
        action = OneStepAction(
            function="wheel_mouse_input",
            args={"wheel_dist": wheel_dist},
            control_label=id,
            control_text=name,
            after_status="CONTINUE",
        )

        return _execute_action(action)

    @action_mcp.tool(tags={"AppAgent"}, exclude_args=[])
    def texts(
        id: Annotated[
            str,
            Field(
                description="The precise annotated ID of the selected control item to retrieve text from, adhering strictly to the provided options in the field of 'id' in the control information."
            ),
        ],
        name: Annotated[
            str,
            Field(
                description="The precise name of the selected control item to retrieve text from, adhering strictly to the provided options in the field of 'name' in the control information."
            ),
        ],
    ) -> Annotated[Dict, Field(description="the text content of the control item")]:
        """
        Retrieve all text content from a control element.
        """
        action = OneStepAction(
            function="texts",
            args={},
            control_label=id,
            control_text=name,
            after_status="CONTINUE",
        )

        return _execute_action(action)

    @action_mcp.tool()
    def summary(
        text: Annotated[str, Field(description="The summary text to provide.")],
    ) -> Annotated[
        str,
        Field(
            description="A visual summary of the current application window based on the task to complete."
        ),
    ]:
        """
        Summarize your observation of the current application window base on the subtask to complete.
        You must use your vision to summarize the image with required information and put it into the `text` argument.
        This summary will be passed to future steps for information.
        """
        return text

    return action_mcp


@MCPRegistry.register_factory_decorator("UICollector")
def create_data_mcp_server(*args, **kwargs) -> FastMCP:
    """
    Create and return the Data MCP server instance.
    :return: FastMCP instance for data retrieval operations.
    """
    # Get singleton UI state instance
    ui_state = UIServerState()

    data_mcp = FastMCP("UFO UI Data MCP Server")

    @data_mcp.tool()
    def get_desktop_app_info(
        remove_empty: bool = True, refresh_app_windows: bool = True
    ) -> List:
        """
        Get information about all application windows currently open on the desktop.
        :param remove_empty: Whether to remove windows with no visible content.
        :param refresh_app_windows: Whether to refresh the list of application windows.
        :return: Dictionary containing list of window information and metadata.
        """
        if refresh_app_windows:
            app_windows = ui_state.control_inspector.get_desktop_app_dict(
                remove_empty=remove_empty
            )
        else:
            # Use existing windows if available
            app_windows = getattr(ui_state, "last_app_windows", {})
            if not app_windows:
                app_windows = ui_state.control_inspector.get_desktop_app_dict(
                    remove_empty=remove_empty
                )

        # Store for future use
        ui_state.last_app_windows = app_windows

        # Convert to WindowInfo objects
        desktop_windows_info = ui_state.control_inspector.get_control_info_list_of_dict(
            app_windows, ["control_text", "control_type"]
        )
        from ufo.agents.processors.target import TargetKind

        revised_desktop_windows_info = [
            {
                "id": window_info["label"],
                "name": window_info["control_text"],
                "type": window_info["control_type"],
                "kind": TargetKind.WINDOW.value,
            }
            for window_info in desktop_windows_info
        ]

        return revised_desktop_windows_info

    @data_mcp.tool()
    def get_app_window_info(field_list: List[str]) -> Dict[str, Any]:
        """
        Get information about the currently selected application window.
        :param field_list: List of fields to retrieve from the window info.
        :return: Dictionary containing the requested window information.
        """
        if not ui_state.selected_app_window:
            raise ToolError("No window is selected， please select a window first.")

        window_info = ui_state.control_inspector.get_control_info(
            ui_state.selected_app_window, field_list=field_list
        )

        return window_info

    @data_mcp.tool()
    def get_app_window_controls_info(field_list: List[str]) -> List:
        """
        Get information about controls in the currently selected application window.
        :param field_list: List of fields to retrieve from the control info.
        :return: Dictionary containing the requested control information.
        """
        if not ui_state.selected_app_window:
            raise ToolError("No window is selected， please select a window first.")

        controls_list = ui_state.control_inspector.find_control_elements_in_descendants(
            ui_state.selected_app_window,
            control_type_list=configs.get("CONTROL_LIST", []),
            class_name_list=configs.get("CONTROL_LIST", []),
        )

        control_dict = {str(i + 1): control for i, control in enumerate(controls_list)}

        result = ui_state.control_inspector.get_control_info_list_of_dict(
            control_dict, field_list=field_list
        )

        ui_state.control_dict = control_dict

        return result

    @data_mcp.tool()
    def get_app_window_controls() -> Dict[str, Any]:
        """
        Get information about controls in the currently selected window.
        :return: Dictionary containing window info and control information in AppWindowControlInfo format.
        """
        if not ui_state.selected_app_window:
            raise ToolError("No window is selected， please select a window first.")

        temp_path = "temp_app_screenshot.png"  # Temporary path for capturing

        try:
            selected_window = ui_state.selected_app_window

            # Capture screenshot to a temporary location
            ui_state.photographer.capture_app_window_screenshot(
                selected_window, save_path=temp_path
            )

            window_info = _window2window_info(selected_window)

            api_backend = None
            grounding_backend = None

            control_detection_backend = configs.get("CONTROL_BACKEND", ["uia"])

            if "uia" in control_detection_backend:
                api_backend = "uia"
            elif "win32" in control_detection_backend:
                api_backend = "win32"

            if "omniparser" in control_detection_backend:
                grounding_backend = "omniparser"

            if api_backend is not None:
                api_control_list = (
                    ui_state.control_inspector.find_control_elements_in_descendants(
                        ui_state.selected_app_window,
                        control_type_list=configs.get("CONTROL_LIST", []),
                        class_name_list=configs.get("CONTROL_LIST", []),
                    )
                )
            else:
                api_control_list = []

            api_control_dict = {
                i + 1: control for i, control in enumerate(api_control_list)
            }

            if (
                grounding_backend == "omniparser"
                and ui_state.grounding_service is not None
            ):

                onmiparser_configs = configs.get("OMNIPARSER", {}) if configs else {}

                grounding_control_list = (
                    ui_state.grounding_service.convert_to_virtual_uia_elements(
                        image_path=temp_path,
                        application_window=ui_state.selected_app_window,
                        box_threshold=onmiparser_configs.get("BOX_THRESHOLD", 0.05),
                        iou_threshold=onmiparser_configs.get("IOU_THRESHOLD", 0.1),
                        use_paddleocr=onmiparser_configs.get("USE_PADDLEOCR", True),
                        imgsz=onmiparser_configs.get("IMGSZ", 640),
                    )
                )
            else:
                grounding_control_list = []

            grounding_control_dict = {
                i + 1: control for i, control in enumerate(grounding_control_list)
            }

            merged_control_list = ui_state.photographer.merge_control_list(
                api_control_list,
                grounding_control_list,
                iou_overlap_threshold=(
                    configs.get("IOU_THRESHOLD_FOR_MERGE", 0.1) if configs else 0.1
                ),
            )

            merged_control_dict = {
                i + 1: control for i, control in enumerate(merged_control_list)
            }

            ui_state.selected_app_window_controls = {
                f"{item[0]}": item[1] for item in merged_control_dict.items()
            }

            # Convert control elements to ControlInfo objects
            control_elements = []
            for i, control in enumerate(merged_control_list):
                try:
                    control_element = _control2control_info(control, str(i + 1))
                    control_elements.append(control_element)
                except Exception as e:
                    control_elements.append(
                        ControlInfo(annotation_id=str(i + 1), name=f"Error: {str(e)}")
                    )

            app_window_control_info = AppWindowControlInfo(
                window_info=window_info, controls=control_elements
            )

            return app_window_control_info.model_dump()

        except Exception as e:
            return {"error": f"Error getting window controls: {str(e)}"}
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @data_mcp.tool()
    def capture_window_screenshot() -> str:
        """
        Capture a screenshot of the currently selected application window.
        :return: Base64 encoded image data of the screenshot.
        """
        if not ui_state.selected_app_window:
            return "Error: No window selected"

        try:
            temp_path = "temp_direct_mcp_screenshot.png"
            ui_state.photographer.capture_app_window_screenshot(
                ui_state.selected_app_window, save_path=temp_path
            )

            # Encode as base64
            screenshot_data = ui_state.photographer.encode_image_from_path(temp_path)

            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)

            return screenshot_data

        except Exception as e:
            return f"Error capturing screenshot: {str(e)}"

    @data_mcp.tool()
    def capture_desktop_screenshot(all_screens: bool = True) -> str:
        """
        Capture a screenshot of the desktop (all screens or primary screen).
        :param all_screens: Whether to capture all screens or just the primary screen.
        :return: Base64 encoded image data of the desktop screenshot.
        """
        try:
            temp_path = "temp_desktop_mcp_screenshot.png"

            # Capture desktop screenshot
            ui_state.photographer.capture_desktop_screen_screenshot(
                all_screens=all_screens, save_path=temp_path
            )

            # Encode as base64
            desktop_screen_data = ui_state.photographer.encode_image_from_path(
                temp_path
            )

            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)

            return desktop_screen_data

        except Exception as e:
            raise ToolError(f"Failed to capture screenshot: {str(e)}")

    @data_mcp.tool()
    def get_ui_tree() -> Dict[str, Any]:
        """
        Get the UI tree for currently selected application window.
        """
        if not ui_state.selected_app_window:
            return {"error": "No window selected"}

        try:
            window = ui_state.selected_app_window
            return ui_tree.UITree(window).ui_tree
        except Exception as e:
            return {"error": f"Error getting UI tree: {str(e)}"}

    return data_mcp
