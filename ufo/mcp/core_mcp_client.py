"""
Core MCP Client for communicating with the UFO Core MCP Server.

This client provides functionality to execute UFO actions through the MCP protocol
instead of directly using the Computer class.
"""

import json
import logging
import requests
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

from ufo.mcp.mcp_client import MCPClient

from ufo.cs.contracts import (
    UFOAction,
    CaptureDesktopScreenshotAction,
    CaptureAppWindowScreenshotAction,
    CaptureAppWindowScreenshotFromWebcamAction,
    GetDesktopAppInfoAction,
    GetAppWindowControlInfoAction,
    SelectApplicationWindowAction,
    LaunchApplicationAction,
    FindControlElementsAction,
    GetUITreeAction,
    OperationSequenceAction,
    OperationCommand,
    CallbackAction,
    MCPToolExecutionAction,
    MCPGetInstructionsAction,
    MCPGetAvailableToolsAction,
)

logger = logging.getLogger(__name__)


class CoreMCPClient(MCPClient):
    """
    Client for communicating with the UFO Core MCP Server.

    This client translates UFO actions into MCP tool calls and handles
    the HTTP communication with the MCP server.
    """

    def __init__(self, host: str = "localhost", port: int = 8000):
        """
        Initialize the Core MCP Client.

        Args:
            host: The hostname of the MCP server
            port: The port number of the MCP server
        """
        super().__init__(host=host, port=port, app_namespace="core")

    def run_action(self, action: UFOAction) -> Any:
        """
        Execute a UFO action by translating it to the appropriate MCP tool call.

        Args:
            action: The UFO action to execute

        Returns:
            The result from executing the action

        Raises:
            Exception: If the action type is not supported or execution fails
        """
        try:
            if isinstance(action, CaptureDesktopScreenshotAction):
                return self._capture_desktop_screenshot(action)
            elif isinstance(action, CaptureAppWindowScreenshotAction):
                return self._capture_app_window_screenshot(action)
            elif isinstance(action, CaptureAppWindowScreenshotFromWebcamAction):
                return self._capture_app_window_screenshot_from_webcam(action)
            elif isinstance(action, GetDesktopAppInfoAction):
                return self._get_desktop_app_info(action)
            elif isinstance(action, GetAppWindowControlInfoAction):
                return self._get_app_window_control_info(action)
            elif isinstance(action, SelectApplicationWindowAction):
                return self._select_application_window(action)
            elif isinstance(action, LaunchApplicationAction):
                return self._launch_application(action)
            elif isinstance(action, FindControlElementsAction):
                return self._find_control_elements(action)
            elif isinstance(action, GetUITreeAction):
                return self._get_ui_tree(action)
            elif isinstance(action, OperationSequenceAction):
                return self._execute_operation_sequence(action)
            elif isinstance(action, CallbackAction):
                return self._handle_callback(action)
            elif isinstance(action, MCPToolExecutionAction):
                return self._handle_mcp_tool_execution(action)
            elif isinstance(action, MCPGetInstructionsAction):
                return self._handle_mcp_get_instructions(action)
            elif isinstance(action, MCPGetAvailableToolsAction):
                return self._handle_mcp_get_available_tools(action)
            else:
                raise Exception(f"Unsupported action type: {type(action).__name__}")

        except Exception as e:
            logger.error(f"Failed to execute action {action.name}: {str(e)}")
            raise

    def _capture_desktop_screenshot(
        self, action: CaptureDesktopScreenshotAction
    ) -> str:
        """Execute capture_desktop_screenshot MCP tool."""
        params = action.params or {}
        arguments = {"all_screens": getattr(params, "all_screens", True)}
        return self._make_tool_call("capture_desktop_screenshot", arguments)

    def _capture_app_window_screenshot(
        self, action: CaptureAppWindowScreenshotAction
    ) -> str:
        """Execute capture_app_window_screenshot MCP tool."""
        params = action.params or {}
        arguments = {"annotation_id": getattr(params, "annotation_id", "")}
        return self._make_tool_call("capture_app_window_screenshot", arguments)

    def _capture_app_window_screenshot_from_webcam(
        self, action: CaptureAppWindowScreenshotFromWebcamAction
    ) -> str:
        """Execute capture_app_window_screenshot_from_webcam MCP tool."""
        params = action.params or {}
        webcam_index: int = 0  # Default to the first webcam

        width: int = 640  # Default width for the screenshot
        height: int = 480  # Default height for the screenshot
        arguments = {
            "annotation_id": getattr(
                params,
                "annotation_id",
                "",
            ),
            "webcam_index": getattr(params, "webcam_index", webcam_index),
            "width": getattr(params, "width", width),
            "height": getattr(params, "height", height),
        }
        return self._make_tool_call(
            "capture_app_window_screenshot_from_webcam", arguments
        )

    def _get_desktop_app_info(
        self, action: GetDesktopAppInfoAction
    ) -> List[Dict[str, Any]]:
        """Execute get_desktop_app_info MCP tool."""
        params = action.params or {}
        arguments = {
            "remove_empty": getattr(params, "remove_empty", True),
            "refresh_app_windows": getattr(params, "refresh_app_windows", False),
        }
        return self._make_tool_call("get_desktop_app_info", arguments)

    def _get_app_window_control_info(
        self, action: GetAppWindowControlInfoAction
    ) -> Dict[str, Any]:
        """Execute get_app_window_control_info MCP tool."""
        params = action.params or {}
        arguments = {"annotation_id": getattr(params, "annotation_id", "")}
        return self._make_tool_call("get_app_window_control_info", arguments)

    def _select_application_window(
        self, action: SelectApplicationWindowAction
    ) -> Dict[str, Any]:
        """Execute select_application_window MCP tool."""
        params = action.params or {}
        arguments = {"window_label": getattr(params, "window_label", "")}
        return self._make_tool_call("select_application_window", arguments)

    def _launch_application(self, action: LaunchApplicationAction) -> Dict[str, Any]:
        """Execute launch_application MCP tool."""
        params = action.params or {}
        arguments = {"bash_command": getattr(params, "bash_command", "")}
        return self._make_tool_call("launch_application", arguments)

    def _find_control_elements(
        self, action: FindControlElementsAction
    ) -> Dict[str, Any]:
        """Execute find_control_elements MCP tool."""
        params = action.params or {}
        arguments = {
            "annotation_id": getattr(params, "annotation_id", ""),
            "control_type_list": getattr(params, "control_type_list", []),
            "class_name_list": getattr(params, "class_name_list", []),
        }
        return self._make_tool_call("find_control_elements", arguments)

    def _get_ui_tree(self, action: GetUITreeAction) -> Dict[str, Any]:
        """Execute get_ui_tree MCP tool."""
        params = action.params or {}
        arguments = {
            "annotation_id": getattr(params, "annotation_id", ""),
            "remove_empty": getattr(params, "remove_empty", True),
        }
        return self._make_tool_call("get_ui_tree", arguments)

    def _execute_operation_sequence(
        self, action: OperationSequenceAction
    ) -> Dict[str, Any]:
        """Execute operation sequence through individual MCP tool calls."""
        if not action.params:
            return {"error": "No operations provided"}

        # For operation sequences, we need to handle individual operations
        # Check if this is a single operation that can be mapped to a specific tool
        operations = action.params
        if len(operations) == 1:
            operation = operations[0]
            return self._execute_single_operation(operation)
        else:
            # For multiple operations, use the execute_operation_sequence tool
            operation_dicts = []
            for op in operations:
                op_dict = {"command_id": op.command_id}

                # Convert operation to dictionary format expected by MCP server
                if op.click_input:
                    op_dict["params"] = op.click_input.model_dump()
                elif op.set_edit_text:
                    op_dict["params"] = op.set_edit_text.model_dump()
                elif op.keyboard_input:
                    op_dict["params"] = op.keyboard_input.model_dump()
                elif op.wheel_mouse_input:
                    op_dict["params"] = op.wheel_mouse_input.model_dump()
                elif op.click_on_coordinates:
                    op_dict["params"] = op.click_on_coordinates.model_dump()
                elif op.drag_on_coordinates:
                    op_dict["params"] = op.drag_on_coordinates.model_dump()

                operation_dicts.append(op_dict)

            arguments = {"operations": operation_dicts}
            return self._make_tool_call("execute_operation_sequence", arguments)

    def _execute_single_operation(self, operation: OperationCommand) -> Dict[str, Any]:
        """Execute a single operation through the appropriate MCP tool."""
        if operation.click_input:
            params = operation.click_input
            arguments = {
                "control_label": params.control_label or "",
                "control_text": params.control_text or "",
                "button": params.button,
                "double": params.double,
            }
            return self._make_tool_call("click_input", arguments)

        elif operation.set_edit_text:
            params = operation.set_edit_text
            arguments = {
                "control_label": params.control_label or "",
                "text": params.text,
                "control_text": params.control_text or "",
            }
            return self._make_tool_call("set_edit_text", arguments)

        elif operation.keyboard_input:
            params = operation.keyboard_input
            arguments = {
                "control_label": params.control_label or "",
                "keys": params.keys,
                "control_text": params.control_text or "",
                "control_focus": params.control_focus,
            }
            return self._make_tool_call("keyboard_input", arguments)

        elif operation.wheel_mouse_input:
            params = operation.wheel_mouse_input
            arguments = {
                "control_label": params.control_label or "",
                "x_dist": params.x_dist,
                "y_dist": params.y_dist,
                "control_text": params.control_text or "",
            }
            return self._make_tool_call("wheel_mouse_input", arguments)

        elif operation.click_on_coordinates:
            params = operation.click_on_coordinates
            arguments = {
                "x": params.x,
                "y": params.y,
                "button": params.button,
                "double": params.double,
                "control_label": params.control_label or "",
                "control_text": params.control_text or "",
            }
            return self._make_tool_call("click_on_coordinates", arguments)

        elif operation.drag_on_coordinates:
            params = operation.drag_on_coordinates
            arguments = {
                "start_x": params.start_x,
                "start_y": params.start_y,
                "end_x": params.end_x,
                "end_y": params.end_y,
                "duration": params.duration,
                "button": params.button,
                "key_hold": params.key_hold,
                "control_label": params.control_label or "",
                "control_text": params.control_text or "",
            }
            return self._make_tool_call("drag_on_coordinates", arguments)

        else:
            raise Exception(f"Unsupported operation type: {operation.command_id}")

    def _handle_callback(self, action: CallbackAction) -> Dict[str, Any]:
        """Handle callback actions - these are typically handled by the client itself."""
        logger.info(f"Handling callback action with call_id: {action.call_id}")
        return {
            "status": "callback_handled",
            "call_id": action.call_id,
            "params": action.params,
        }

    def _handle_mcp_tool_execution(
        self, action: MCPToolExecutionAction
    ) -> Dict[str, Any]:
        """Handle MCP tool execution - forward to the appropriate MCP server."""
        if not action.params:
            return {"error": "No MCP tool execution parameters provided"}

        params = action.params
        # For core MCP server, we can execute the tool directly if it's one of our supported tools
        # Otherwise, this would need to be forwarded to the appropriate MCP server
        tool_name = params.tool_name
        tool_args = params.tool_args

        logger.info(f"Executing MCP tool: {tool_name} with args: {tool_args}")

        # Check if this is a tool we can handle directly
        if hasattr(self, f"_{tool_name}"):
            # This is a direct tool call to our server
            return self._make_tool_call(tool_name, tool_args)
        else:
            # This might be for a different MCP server - return error for now
            return {
                "error": f"Tool {tool_name} not supported by core MCP server",
                "tool_name": tool_name,
                "app_namespace": params.app_namespace,
            }

    def _handle_mcp_get_instructions(
        self, action: MCPGetInstructionsAction
    ) -> Dict[str, Any]:
        """Handle requests for MCP instructions."""
        if not action.params:
            return {"error": "No MCP get instructions parameters provided"}

        params = action.params
        app_namespace = params.app_namespace

        # For the core MCP server, return basic instructions
        if app_namespace == "core" or app_namespace == "ufo":
            return {
                "instructions": "Core UFO MCP Server - provides basic UFO functionality including desktop screenshots, window management, and UI automation.",
                "app_namespace": app_namespace,
                "available_actions": [
                    "capture_desktop_screenshot",
                    "capture_app_window_screenshot",
                    "get_desktop_app_info",
                    "get_app_window_control_info",
                    "select_application_window",
                    "launch_application",
                    "find_control_elements",
                    "get_ui_tree",
                    "click_input",
                    "set_edit_text",
                    "keyboard_input",
                    "wheel_mouse_input",
                    "click_on_coordinates",
                    "drag_on_coordinates",
                ],
            }
        else:
            return {
                "error": f"Instructions not available for app namespace: {app_namespace}",
                "app_namespace": app_namespace,
            }

    def _handle_mcp_get_available_tools(
        self, action: MCPGetAvailableToolsAction
    ) -> Dict[str, Any]:
        """Handle requests for available MCP tools."""
        if not action.params:
            return {"error": "No MCP get available tools parameters provided"}

        params = action.params
        app_namespace = params.app_namespace

        # For the core MCP server, return the list of available tools
        if app_namespace == "core" or app_namespace == "ufo":
            return {
                "tools": [
                    {
                        "name": "capture_desktop_screenshot",
                        "description": "Capture a screenshot of the desktop",
                        "parameters": ["all_screens"],
                    },
                    {
                        "name": "capture_app_window_screenshot",
                        "description": "Capture a screenshot of a specific application window",
                        "parameters": ["annotation_id"],
                    },
                    {
                        "name": "get_desktop_app_info",
                        "description": "Get information about all desktop applications",
                        "parameters": ["remove_empty", "refresh_app_windows"],
                    },
                    {
                        "name": "get_app_window_control_info",
                        "description": "Get control information for a specific application window",
                        "parameters": ["annotation_id"],
                    },
                    {
                        "name": "select_application_window",
                        "description": "Select and focus on a specific application window",
                        "parameters": ["window_label"],
                    },
                    {
                        "name": "launch_application",
                        "description": "Launch an application using a bash command",
                        "parameters": ["bash_command"],
                    },
                    {
                        "name": "find_control_elements",
                        "description": "Find control elements in a specific application window",
                        "parameters": [
                            "annotation_id",
                            "control_type_list",
                            "class_name_list",
                        ],
                    },
                    {
                        "name": "get_ui_tree",
                        "description": "Get the UI tree for a specific application window",
                        "parameters": ["annotation_id", "remove_empty"],
                    },
                    {
                        "name": "click_input",
                        "description": "Click on a UI control element",
                        "parameters": [
                            "control_label",
                            "control_text",
                            "button",
                            "double",
                        ],
                    },
                    {
                        "name": "set_edit_text",
                        "description": "Set text in an edit control",
                        "parameters": ["control_label", "text", "control_text"],
                    },
                    {
                        "name": "keyboard_input",
                        "description": "Send keyboard input to a control",
                        "parameters": [
                            "control_label",
                            "keys",
                            "control_text",
                            "control_focus",
                        ],
                    },
                    {
                        "name": "wheel_mouse_input",
                        "description": "Send mouse wheel input to a control",
                        "parameters": [
                            "control_label",
                            "x_dist",
                            "y_dist",
                            "control_text",
                        ],
                    },
                    {
                        "name": "click_on_coordinates",
                        "description": "Click on specific coordinates within an application window",
                        "parameters": [
                            "x",
                            "y",
                            "button",
                            "double",
                            "control_label",
                            "control_text",
                        ],
                    },
                    {
                        "name": "drag_on_coordinates",
                        "description": "Drag from one coordinate to another within an application window",
                        "parameters": [
                            "start_x",
                            "start_y",
                            "end_x",
                            "end_y",
                            "duration",
                            "button",
                            "key_hold",
                            "control_label",
                            "control_text",
                        ],
                    },
                ],
                "app_namespace": app_namespace,
            }
        else:
            return {
                "error": f"Tools not available for app namespace: {app_namespace}",
                "app_namespace": app_namespace,
            }

    def test_connection(self) -> bool:
        """
        Test the connection to the MCP server.

        Returns:
            True if the connection is successful, False otherwise
        """
        try:
            # Try a simple tool call to test connectivity
            self._make_tool_call("get_desktop_app_info", {"remove_empty": True})
            return True
        except Exception as e:
            logger.error(f"MCP server connection test failed: {str(e)}")
            return False
