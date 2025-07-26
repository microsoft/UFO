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

import os
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pywinauto.controls.uiawrapper import UIAWrapper

from ufo.agents.processors.action_contracts import ActionSequence, OneStepAction
from ufo.automator.action_execution import ActionSequenceExecutor
from ufo.automator.puppeteer import AppPuppeteer
from ufo.automator.ui_control.grounding.basic import BasicGrounding
from ufo.automator.ui_control.inspector import ControlInspectorFacade
from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.config import get_config
from ufo.cs.contracts import AppWindowControlInfo, ControlInfo, Rect, WindowInfo

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
            UIServerState._initialized = True

    def initialize_for_window(self, window: UIAWrapper) -> None:
        """
        Initialize the puppeteer and controls for a specific window.
        :param window: The UIAWrapper window object to initialize for.
        :return: None
        """
        self.selected_app_window = window

        # Initialize AppPuppeteer with annotation_id like computer.py
        self.puppeteer = AppPuppeteer(
            self.control_inspector.get_application_root_name(window),
            window.window_text(),
        )


def create_action_mcp_server():
    """
    Create and return the Action MCP server instance.
    :return: FastMCP instance for action operations.
    """
    # Get singleton UI state instance
    ui_state = UIServerState()

    def _execute_action_sequence(actions: List[OneStepAction]) -> List:
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
            ui_state.selected_app_window_controls or {},
            application_window,
        )

        return action_sequence.get_results()

    action_mcp = FastMCP("UFO UI Action MCP Server")

    @action_mcp.tool()
    def select_application_window(
        window_label: str = "",
    ) -> Dict[str, Any]:
        """
        Select an application window for UI automation.
        :param window_label: The label or ID of the window to select.
        :return: Information about the selected window.
        """
        if not window_label:
            raise ToolError("Window label is required for select_application_window")

        # Use the last app windows retrieved from get_desktop_app_info
        app_window_dict = ui_state.last_app_windows

        if not app_window_dict:
            raise ToolError(
                "No application windows available. Please call get_desktop_app_info first."
            )

        # Find the window with the matching label
        window = app_window_dict.get(window_label)

        if not window:
            available_windows = list(app_window_dict.keys())
            raise ToolError(
                f"Window with label '{window_label}' not found. Available windows: {available_windows}"
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

    @action_mcp.tool()
    def click_input(
        control_label: str,
        control_text: str = "",
        button: str = "left",
        double: bool = False,
    ) -> List:
        """
        Click on a UI control element using the input method.
        :param control_label: The label/ID of the control to click.
        :param control_text: The text content of the control (optional).
        :param button: Mouse button to use ("left", "right", "middle").
        :param double: Whether to perform a double click.
        :return: List of execution results.
        """
        action = OneStepAction(
            function="click_input",
            args={"button": button, "double": double},
            control_label=control_label,
            control_text=control_text,
            after_status="CONTINUE",
        )

        return _execute_action_sequence([action])

    @action_mcp.tool()
    def click_on_coordinates(
        x: float,
        y: float,
        control_label: str = "",
        control_text: str = "",
        button: str = "left",
        double: bool = False,
    ) -> List:
        """
        Click on specific coordinates within the application window.
        :param x: X coordinate (relative to application window, 0.0 to 1.0).
        :param y: Y coordinate (relative to application window, 0.0 to 1.0).
        :param control_label: The label/ID of the target control (optional).
        :param control_text: The text content of the control (optional).
        :param button: Mouse button to use ("left", "right", "middle").
        :param double: Whether to perform a double click.
        :return: List of execution results.
        """
        action = OneStepAction(
            function="click_on_coordinates",
            args={"x": x, "y": y, "button": button, "double": double},
            control_label=control_label,
            control_text=control_text,
            after_status="CONTINUE",
        )

        return _execute_action_sequence([action])

    @action_mcp.tool()
    def drag_on_coordinates(
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        control_label: str = "",
        control_text: str = "",
        button: str = "left",
        duration: float = 1.0,
        key_hold: Optional[str] = None,
    ) -> List:
        """
        Drag from one coordinate to another within the application window.
        :param start_x: Starting X coordinate (relative to application window, 0.0 to 1.0).
        :param start_y: Starting Y coordinate (relative to application window, 0.0 to 1.0).
        :param end_x: Ending X coordinate (relative to application window, 0.0 to 1.0).
        :param end_y: Ending Y coordinate (relative to application window, 0.0 to 1.0).
        :param control_label: The label/ID of the target control (optional).
        :param control_text: The text content of the control (optional).
        :param button: Mouse button to use for dragging ("left", "right", "middle").
        :param duration: Duration of the drag operation in seconds.
        :param key_hold: Key to hold during drag operation (e.g., "ctrl", "shift").
        :return: List of execution results.
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
            control_label=control_label,
            control_text=control_text,
            after_status="CONTINUE",
        )

        return _execute_action_sequence([action])

    @action_mcp.tool()
    def set_edit_text(
        text: str,
        control_label: str,
        control_text: str = "",
        clear_current_text: bool = False,
        after_status: str = "CONTINUE",
    ) -> List:
        """
        Set text in an edit control (text box, input field, etc.).
        :param text: The text to set in the control.
        :param control_label: The label/ID of the edit control.
        :param control_text: The current text content of the control (optional).
        :param clear_current_text: Whether to clear existing text before setting new text.
        :param after_status: Status after execution ("CONTINUE", "FINISH", etc.).
        :return: List of execution results.
        """
        action = OneStepAction(
            function="set_edit_text",
            args={"text": text, "clear_current_text": clear_current_text},
            control_label=control_label,
            control_text=control_text,
            after_status=after_status,
        )

        return _execute_action_sequence([action])

    @action_mcp.tool()
    def keyboard_input(
        keys: str,
        control_label: str = "",
        control_text: str = "",
        control_focus: bool = True,
    ) -> List:
        """
        Send keyboard input to a control or the focused application.
        :param keys: Key sequence to send (e.g., "ctrl+c", "enter", "tab").
        :param control_label: The label/ID of the target control (optional).
        :param control_text: The text content of the control (optional).
        :param control_focus: Whether to focus the control before sending keys.
        :return: List of execution results.
        """
        action = OneStepAction(
            function="keyboard_input",
            args={"keys": keys, "control_focus": control_focus},
            control_label=control_label,
            control_text=control_text,
            after_status="CONTINUE",
        )

        return _execute_action_sequence([action])

    @action_mcp.tool()
    def wheel_mouse_input(
        direction: str = "up",
        clicks: int = 3,
        control_label: str = "",
        control_text: str = "",
    ) -> List:
        """
        Send mouse wheel input to scroll a control.
        :param direction: Scroll direction ("up" or "down").
        :param clicks: Number of wheel clicks.
        :param control_label: The label/ID of the target control (optional).
        :param control_text: The text content of the control (optional).
        :return: List of execution results.
        """
        action = OneStepAction(
            function="wheel_mouse_input",
            args={"direction": direction, "clicks": clicks},
            control_label=control_label,
            control_text=control_text,
            after_status="CONTINUE",
        )

        return _execute_action_sequence([action])

    @action_mcp.tool()
    def summary(
        text: str,
        control_label: str = "",
        control_text: str = "",
    ) -> List:
        """
        Provide a visual summary or description of a control element.
        :param text: The summary text to provide.
        :param control_label: The label/ID of the target control (optional).
        :param control_text: The text content of the control (optional).
        :return: List of execution results.
        """
        action = OneStepAction(
            function="summary",
            args={"text": text},
            control_label=control_label,
            control_text=control_text,
            after_status="CONTINUE",
        )

        return _execute_action_sequence([action])

    @action_mcp.tool()
    def annotation(
        control_labels: List[str],
        control_label: str = "",
        control_text: str = "",
    ) -> List:
        """
        Annotate or highlight specific controls on the screen.
        :param control_labels: List of control labels to annotate.
        :param control_label: The label/ID of the primary control (optional).
        :param control_text: The text content of the control (optional).
        :return: List of execution results.
        """
        action = OneStepAction(
            function="annotation",
            args={"control_labels": control_labels},
            control_label=control_label,
            control_text=control_text,
            after_status="CONTINUE",
        )

        return _execute_action_sequence([action])

    @action_mcp.tool()
    def no_action(
        control_label: str = "",
        control_text: str = "",
    ) -> List[Dict]:
        """
        Perform no action (useful for testing or as a placeholder).
        :param control_label: The label/ID of the target control (optional).
        :param control_text: The text content of the control (optional).
        :return: List of execution results.
        """
        action = OneStepAction(
            function="no_action",
            args={},
            control_label=control_label,
            control_text=control_text,
            after_status="CONTINUE",
        )

        return _execute_action_sequence([action])

    return action_mcp


def create_data_mcp_server():
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
        try:
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
            windows_info = []
            for annotation_id, window in app_windows.items():
                try:
                    window_info = _window2window_info(window, annotation_id)
                    windows_info.append(window_info.model_dump())
                except Exception as e:
                    # If there's an error with a specific window, add minimal info
                    windows_info.append(
                        {
                            "annotation_id": annotation_id,
                            "title": "Error retrieving window info",
                            "error": str(e),
                        }
                    )

            return windows_info

        except Exception as e:
            return []

    @data_mcp.tool()
    def get_app_window_controls() -> Dict[str, Any]:
        """
        Get information about controls in the currently selected window.
        Uses the same comprehensive control detection logic as computer.py.
        Returns data in the same format as _handle_get_app_window_control_info but using plain dictionaries.
        :return: Dictionary containing window info and control information in AppWindowControlInfo format.
        """
        if not ui_state.selected_app_window:
            return {"error": "No window selected"}

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
                ui_state.grounding_service: BasicGrounding

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

    return data_mcp


# Registry decorators for automatic registration
try:
    from ufo.mcp.mcp_registry import MCPRegistry

    @MCPRegistry.register_factory_decorator("UICollector")
    def create_ui_data_mcp_server_factory() -> FastMCP:
        """
        Factory function to create the UI Data MCP server.
        :return: FastMCP instance for UI data operations.
        """
        return create_data_mcp_server()

    @MCPRegistry.register_factory_decorator("UIExecutor")
    def create_ui_action_mcp_server_factory() -> FastMCP:
        """
        Factory function to create the UI Action MCP server.
        :return: FastMCP instance for UI action operations.
        """
        return create_action_mcp_server()

except ImportError:
    print("Warning: MCPRegistry not found. UI MCP servers will not be registered.")
