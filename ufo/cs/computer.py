import os
import subprocess
import time
import yaml
from typing import Dict, List, Any, Optional

from pywinauto.controls.uiawrapper import UIAWrapper
from ufo.agents.processors.actions import ActionSequence, OneStepAction
from ufo.automator.puppeteer import AppPuppeteer, ReceiverManager
from ufo.automator.ui_control import ui_tree
from ufo.cs.contracts import (
    ActionBase,
    AppWindowControlInfo, 
    CallbackAction,
    CaptureDesktopScreenshotAction,
    CaptureAppWindowScreenshotAction,
    CaptureDesktopScreenshotParams,
    ControlInfo,
    GetAppWindowControlInfoParams,
    GetDesktopAppInfoAction,
    GetAppWindowControlInfoAction,
    FindControlElementsAction,
    GetDesktopAppInfoParams,
    GetUITreeAction,
    Rect,
    SelectApplicationWindowAction,
    LaunchApplicationAction,
    OperationCommand,
    WindowInfo,
    MCPToolExecutionAction,
    MCPGetInstructionsAction,
    MCPGetAvailableToolsAction
)

from ufo.automator.ui_control.inspector import ControlInspectorFacade
from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.automator.ui_control.grounding.basic import BasicGrounding
from ufo.config import Config
from ufo.automator.app_apis.factory import COMReceiverFactory, WebReceiverFactory, ShellReceiverFactory
from ufo.mcp.mcp_client import MCPClient

configs = Config.get_instance().config_data

if configs is not None:
    CONTROL_BACKEND = configs.get("CONTROL_BACKEND", ["uia"])
    BACKEND = "win32" if "win32" in CONTROL_BACKEND else "uia"


class Computer:
    last_app_windows: Optional[Dict[str, UIAWrapper]] = None
    last_app_windows_info: Optional[List[WindowInfo]] = None
    selected_app_window : Optional[UIAWrapper] = None
    selected_app_window_info: Optional[WindowInfo] = None
    selected_app_window_controls: Optional[Dict[str, UIAWrapper]] = None
    selected_app_window_control_info: Optional[AppWindowControlInfo] = None
    
    def __init__(self, name: str):
        self._name = name
        
        self.last_app_windows = {}
        self.last_app_windows_info = []
        
        self.photographer = PhotographerFacade()
        self.control_inspector = ControlInspectorFacade(BACKEND)
        self.grounding_service = None  # Initialize grounding service as None for now
        self.receiver_manager = ReceiverManager()
        
        self.mcp_servers = {}
        self.mcp_instructions = {}
        
        self._init_receivers()

        if configs and configs.get("USE_MCP", False):
            self._init_mcp_servers()

    
    @property
    def name(self) -> str:
        """Get the name of the computer"""
        return self._name
    
    def _init_receivers(self):
        """Initialize available receiver factories."""
        # Receivers are auto-registered via @ReceiverManager.register decorators
        pass
    
    def _init_mcp_servers(self):
        """Initialize MCP server connections for client applications."""
        # Get the base directory for UFO2
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Load MCP servers configuration from YAML file
        mcp_configs = {}
        try:
            servers_config_path = os.path.join(base_dir, "config", "mcp_servers.yaml")
            if os.path.exists(servers_config_path):
                with open(servers_config_path, 'r') as f:
                    servers_config = yaml.safe_load(f)
                
                # Extract server configurations
                mcp_servers_config = servers_config.get("mcp_servers", {})
                for namespace, server_config in mcp_servers_config.items():
                    if server_config.get("enabled", True):
                        mcp_configs[namespace] = {
                            "endpoint": server_config["endpoint"],
                            "instructions_path": os.path.join(base_dir, server_config["instructions_path"])
                        }
            else:
                # Fallback to hardcoded configuration if file doesn't exist
                mcp_configs = {
                    "powerpoint": {
                        "endpoint": "http://localhost:8001",
                        "instructions_path": os.path.join(base_dir, "config", "mcp_instructions", "powerpoint.yaml")
                    },
                    "word": {
                        "endpoint": "http://localhost:8002", 
                        "instructions_path": os.path.join(base_dir, "config", "mcp_instructions", "word.yaml")
                    },
                    "excel": {
                        "endpoint": "http://localhost:8003",
                        "instructions_path": os.path.join(base_dir, "config", "mcp_instructions", "excel.yaml")
                    },
                    "web": {
                        "endpoint": "http://localhost:8004",
                        "instructions_path": os.path.join(base_dir, "config", "mcp_instructions", "web.yaml")
                    },
                    "shell": {
                        "endpoint": "http://localhost:8005",
                        "instructions_path": os.path.join(base_dir, "config", "mcp_instructions", "shell.yaml")
                    }
                }
        except Exception as e:
            from ufo.utils import print_with_color
            print_with_color(f"Failed to load MCP servers configuration: {e}", "yellow")
        
        for namespace, config in mcp_configs.items():
            try:
                # Load instructions for this namespace
                if os.path.exists(config["instructions_path"]):
                    with open(config["instructions_path"], 'r') as f:
                        self.mcp_instructions[namespace] = yaml.safe_load(f)
                
                self.mcp_servers[namespace] = {
                    "endpoint": config["endpoint"],
                    "status": "initialized"
                }
            except Exception as e:
                from ufo.utils import print_with_color
                print_with_color(f"Failed to initialize MCP server {namespace}: {e}", "red")
                  # load tools from mcp servers and replace the tools in mcp_instructions if available
        for namespace, server_config in self.mcp_servers.items():
            try:
                endpoint = server_config["endpoint"]
                mcp_client = MCPClient.create_client(endpoint, namespace)
                
                # Create a temporary action to get available tools
                from ufo.cs.contracts import MCPGetAvailableToolsAction, MCPGetAvailableToolsParams
                temp_action = MCPGetAvailableToolsAction(
                    params=MCPGetAvailableToolsParams(app_namespace=namespace)
                )
                
                result = mcp_client._handle_mcp_get_available_tools(temp_action)
                if result.get("tools"):
                    # Normalize the MCP tools schema before updating instructions
                    normalized_tools = self._normalize_tool_schema(result["tools"], source="mcp")
                    
                    # Update the instructions with the normalized tools
                    if namespace in self.mcp_instructions:
                        self.mcp_instructions[namespace]["tools"] = normalized_tools
                    else:
                        # Create new entry if namespace doesn't exist
                        self.mcp_instructions[namespace] = {"tools": normalized_tools}
            except Exception as e:
                from ufo.utils import print_with_color
                print_with_color(f"Failed to fetch tools for {namespace}: {e}", "yellow")
    
    def run_action(self, action: ActionBase) -> Dict[str, Any]:
        """Run the specified action and return the result"""
        
        print(f"Running action: {action.name}\r\n")
        
        action_handlers = {
            "capture_desktop_screenshot": self._handle_capture_desktop_screenshot,
            "capture_app_window_screenshot": self._handle_capture_app_window_screenshot,
            "get_desktop_app_info": self._handle_get_desktop_app_info,
            "get_app_window_control_info": self._handle_get_app_window_control_info,
            "select_application_window": self._handle_select_application_window,
            "launch_application": self._handle_launch_application,
            "callback": self._handle_callback,
            "get_ui_tree": self._handle_get_ui_tree,
            "operation_sequence": self._handle_operation_sequence,
            "execute_mcp_tool": self._handle_execute_mcp_tool,
            "get_mcp_instructions": self._handle_get_mcp_instructions,
            "get_mcp_available_tools": self._handle_get_mcp_available_tools,
        }
        
        if action.name in action_handlers:
            return action_handlers[action.name](action)
        else:
            raise ValueError(f"Unknown action: {action.name}")

    def _handle_operation_sequence(self, action: ActionBase) -> Dict[str, Any]:
        action_commands: list[OperationCommand] = action.params
        actions = []
        application_window = self._get_window_by_annotation_id(self.selected_app_window_info.annotation_id)
        for command in action_commands:
            command_dict = command.model_dump()
            command_id = command.command_id
            control_label = command_dict[command_id].get("control_label", "")
            control_text = command_dict[command_id].get("control_text", "")
            after_status = command_dict[command_id].get("after_status", "CONTINUE")

            # copy all key values from command[command_instance] except control_label and control_text
            args = {key: value for key, value in command_dict[command_id].items() if key not in ["control_label", "control_text", "after_status"]}

            action = OneStepAction(
                function=command_id,
                args=args,
                control_label=control_label,
                control_text=control_text,
                after_status=after_status
            )
            actions.append(action)
        action_sequence = ActionSequence(actions)
        puppeteer = AppPuppeteer(self.selected_app_window_info.annotation_id, "")
        action_sequence.execute_all(puppeteer, self.selected_app_window_controls, application_window)

    def _handle_callback(self, action: CallbackAction) -> Dict[str, Any]:
        """Handle callback action"""
        # params = action.params
        # callback_function = params.callback_function
        # callback_args = params.callback_args
        
        # if not callback_function:
        #     raise ValueError("Callback function is required")
        
        # # Call the callback function with the provided arguments
        # result = callback_function(*callback_args)
        
        # return {"callback_result": result}
        return {"callback_result": "Callback action executed successfully"}

    def _handle_capture_desktop_screenshot(self, action: CaptureDesktopScreenshotAction) -> str:
        """Handle capture_desktop_screenshot action"""
        params = action.params
        all_screens = params.all_screens
        temp_path = "temp_desktop_screenshot.png"  # Temporary path for capturing
        
        # Capture screenshot to a temporary location
        self.photographer.capture_desktop_screen_screenshot(
            all_screens=all_screens, 
            save_path=temp_path
        )
        
        # Encode the image data
        desktop_screen_url = self.photographer.encode_image_from_path(temp_path)
       
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return desktop_screen_url

    def _handle_capture_app_window_screenshot(self, action: CaptureAppWindowScreenshotAction) -> str:
        """Handle capture_app_window_screenshot action"""
        params = action.params
        app_window = self._get_window_by_annotation_id(params.annotation_id)

        temp_path = "temp_app_screenshot.png"  # Temporary path for capturing
        
        if not app_window:
            raise ValueError("Window handle is required for capture_app_window_screenshot")
        
        # Capture screenshot to a temporary location
        self.photographer.capture_app_window_screenshot(
            app_window,
            save_path=temp_path
        )
           
        # Also encode as base64 for convenience
        app_screen_url = self.photographer.encode_image_from_path(temp_path)
        
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return app_screen_url

    def _handle_get_desktop_app_info(self, action: GetDesktopAppInfoAction) -> List[WindowInfo]:
        """Handle get_desktop_app_info action"""
        params = action.params
        remove_empty = params.remove_empty
        refresh_app_windows = params.refresh_app_windows
        
        if refresh_app_windows:
            self.last_app_windows = self.control_inspector.get_desktop_app_dict(
                remove_empty=remove_empty
            )
        
        window_dict = [
            dict(
                annotation_id=app_window[0],
                name=app_window[1].element_info.name,
                title=app_window[1].window_text(),
                handle=app_window[1].handle,
                class_name=app_window[1].class_name(),
                process_id=app_window[1].process_id(),
                is_visible=app_window[1].is_visible(),
                is_minimized=app_window[1].is_minimized(),
                is_maximized=app_window[1].is_maximized(),
                is_active=app_window[1].is_active(),
                rectangle=self._get_control_rectangle(app_window[1]),
                text_content=app_window[1].window_text(),
            )
            for app_window in self.last_app_windows.items()
        ]
        
        self.last_app_windows_info = [
            WindowInfo(
                annotation_id=app_window["annotation_id"],
                name=app_window["name"],
                title=app_window["title"],
                handle=app_window["handle"],
                class_name=app_window["class_name"],
                process_id=app_window["process_id"],
                is_visible=app_window["is_visible"],
                is_minimized=app_window["is_minimized"],
                is_maximized=app_window["is_maximized"],
                is_active=app_window["is_active"],
                rectangle=app_window["rectangle"],
                text_content=app_window["text_content"],
            )
            for app_window in window_dict
        ]

        return self.last_app_windows_info

    def _handle_get_app_window_control_info(self, action: GetAppWindowControlInfoAction) -> AppWindowControlInfo:
        """
        Get the control list from the annotation dictionary.
        :param screenshot_path: The path to the clean screenshot.
        :return: The list of control items.
        """
        params = action.params
        application_window = self._get_window_by_annotation_id(params.annotation_id)

        temp_path = "temp_app_screenshot.png"  # Temporary path for capturing
        
        if not application_window:
            raise ValueError("Window handle is required for capture_app_window_screenshot")
        
        # Capture screenshot to a temporary location
        self.photographer.capture_app_window_screenshot(
            application_window,
            save_path=temp_path
        )
        
        window_info = WindowInfo(
            title=application_window.window_text(),
            handle=application_window.handle,
            class_name=application_window.class_name(),
            process_id=application_window.process_id(),
            is_visible=application_window.is_visible(),
            is_minimized=application_window.is_minimized(),
            is_maximized=application_window.is_maximized(),
            is_active=application_window.is_active(),
            rectangle=self._get_control_rectangle(application_window),
        )

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
                self.control_inspector.find_control_elements_in_descendants(
                    application_window,
                    control_type_list=configs.get("CONTROL_LIST", []),
                    class_name_list=configs.get("CONTROL_LIST", []),
                )
            )
        else:
            api_control_list = []

        api_control_dict = {
            i + 1: control for i, control in enumerate(api_control_list)
        }

        # print(control_detection_backend, grounding_backend, screenshot_path)

        if grounding_backend == "omniparser" and self.grounding_service is not None:
            self.grounding_service: BasicGrounding

            onmiparser_configs = configs.get("OMNIPARSER", {})

            # print(onmiparser_configs)

            grounding_control_list = (
                self.grounding_service.convert_to_virtual_uia_elements(
                    image_path=temp_path,
                    application_window=application_window,
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

        merged_control_list = self.photographer.merge_control_list(
            api_control_list,
            grounding_control_list,
            iou_overlap_threshold=configs.get("IOU_THRESHOLD_FOR_MERGE", 0.1),
        )

        merged_control_dict = {
            i + 1: control for i, control in enumerate(merged_control_list)
        }
        
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Convert the control list to ControlElement objects
        control_elements = []
        for i, control in enumerate(merged_control_list):
            # Extract needed properties from control object
            # This will need to be adjusted based on the actual structure of your control objects
            control_element = ControlInfo(
                annotation_id=str(i + 1),
                control_type=getattr(control.element_info, 'control_type', None),
                name=getattr(control.element_info, 'name', None),
                automation_id=getattr(control.element_info, 'automation_id', None),
                class_name=getattr(control.element_info, 'class_name', None),
                rectangle=self._get_control_rectangle(control),
                is_enabled=getattr(control.element_info, 'is_enabled', True),
                is_visible=getattr(control.element_info, 'is_visible', True),
                source=getattr(control, 'source', 'merged')
            )
            control_elements.append(control_element)

        self.selected_app_window_controls = {f"{item[0]}": item[1] for item in merged_control_dict.items()}
        self.selected_app_window_control_info = AppWindowControlInfo(
            window_info=window_info,
            controls=control_elements
        )

        return AppWindowControlInfo(
            window_info=window_info,
            controls=control_elements)

    def _get_control_rectangle(self, control: UIAWrapper):
        """Helper method to extract rectangle coordinates from a control"""
        try:
            if hasattr(control, 'rectangle'):
                rect = control.rectangle()
                return Rect(
                    x=rect.left,
                    y=rect.top,
                    width=rect.width(),
                    height=rect.height()
                )
        except:
            pass
        return None

    def _handle_find_control_elements(self, action: FindControlElementsAction) -> Dict[str, Any]:
        """Handle find_control_elements action"""
        params = action.params
        window = self._get_window_by_annotation_id(params.annotation_id)
        control_type_list = params.control_type_list
        class_name_list = params.class_name_list

        if not window:
            raise ValueError("Window is required for find_control_elements")
        if not control_type_list and not class_name_list:
            raise ValueError("At least one of control_type_list or class_name_list is required for find_control_elements")
        control_elements = self.control_inspector.find_control_elements_in_descendants(
            window,
            control_type_list=control_type_list,
            class_name_list=class_name_list
        )
        
        return {"control_elements": control_elements}

    def _handle_select_application_window(self, action: SelectApplicationWindowAction) -> Dict[str, Any]:
        """Handle select_application_window action"""
        params = action.params
        window_label = params.window_label
        
        if not window_label:
            raise ValueError("Window label is required for select_application_window")
        
        app_window_dict = self.last_app_windows
        
        # Find the window with the matching label
        window = app_window_dict.get(window_label)
        
        if not window:
            raise ValueError(f"Window with label '{window_label}' not found")
        
        # Set focus on the window
        try:
            window.set_focus()
            if configs.get("MAXIMIZE_WINDOW", False):
                window.maximize()
                
            if configs.get("SHOW_VISUAL_OUTLINE_ON_SCREEN", True):
                window.draw_outline(colour="red", thickness=3)
        except Exception as e:
            raise ValueError(f"Failed to set focus on window: {str(e)}")
        
        # Return window information as a string, including process name and window text
        process_name = self.control_inspector.get_application_root_name(window)
        window_text = window.window_text() if hasattr(window, 'window_text') else "Unknown"
        
        self.selected_app_window = window
        self.selected_app_window_info = WindowInfo(
            annotation_id=window_label,
            title=window_text,
            handle=window.handle,
            class_name=window.class_name(),
            process_id=window.process_id(),
            is_visible=window.is_visible(),
            is_minimized=window.is_minimized(),
            is_maximized=window.is_maximized(),
            #is_active=window.is_active(),
            rectangle=self._get_control_rectangle(window),
        )
        
        return {
            "process_name": process_name,
            "window_text": window_text,
            "window_info": self.selected_app_window_info.model_dump()
        }    
    
    def _handle_launch_application(self, action: LaunchApplicationAction) -> Dict[str, Any]:
        """Handle launch_application action"""
        params = action.params
        bash_command = params.bash_command
        
        if not bash_command:
            raise ValueError("Bash command is required for launch_application")
            
       
        # Execute the bash command
        try:
            subprocess.Popen(bash_command, shell=True)
            # Wait for the application to start
            time.sleep(3)
        except Exception as e:
            raise ValueError(f"Failed to execute bash command: {str(e)}")
        
        # Get desktop windows after launching the app
        app_dict = self.control_inspector.get_desktop_app_dict(remove_empty=True)
        
        # As a simple approach, we'll use the desktop itself if we don't have a better way
        # to identify the specific window. In a real implementation, you might want to 
        # compare before/after snapshots of desktop windows to find the new one.
        window = self.control_inspector.desktop
        
        if app_dict and len(app_dict) > 0:
            # Use the first active window as a fallback
            # In a real implementation, you would use more sophisticated logic to identify
            # the correct window based on the launched application
            for key, win in app_dict.items():
                try:
                    if win.is_active():
                        window = win
                        break
                except:
                    pass
        
        self.last_app_windows = app_dict
        self.last_app_windows_info = [
            WindowInfo(
                annotation_id=app_window[0],
                name=app_window[1].element_info.name,
                title=app_window[1].window_text(),
                handle=app_window[1].handle,
                class_name=app_window[1].class_name(),
                process_id=app_window[1].process_id(),
                is_visible=app_window[1].is_visible(),
                is_minimized=app_window[1].is_minimized(),
                is_maximized=app_window[1].is_maximized(),
                is_active=app_window[1].is_active(),
                rectangle=self._get_control_rectangle(app_window[1]),
                text_content=app_window[1].window_text(),
            )
            for app_window in app_dict.items()
        ]
        self.selected_app_window = window
        # Set selected window info based on the recent application launch
        # Try to find the window that matches the process or handle from the launch
        window_found = False
        for win_info in self.last_app_windows_info:
            if hasattr(window, 'process_id') and window.process_id() == win_info.process_id:
                self.selected_app_window_info = win_info
                window_found = True
                break
            elif hasattr(window, 'handle') and window.handle == win_info.handle:
                self.selected_app_window_info = win_info
                window_found = True
                break
        
        # If no matching window was found, create basic window info
        if not window_found:
            self.selected_app_window_info = WindowInfo(
                annotation_id="unknown",
                name=getattr(window.element_info, 'name', None) if hasattr(window, 'element_info') else None,
                title=window.window_text() if hasattr(window, 'window_text') else "Unknown",
                handle=window.handle if hasattr(window, 'handle') else None,
                class_name=window.class_name() if hasattr(window, 'class_name') else None,
                process_id=window.process_id() if hasattr(window, 'process_id') else None,
                is_visible=window.is_visible() if hasattr(window, 'is_visible') else False,
                is_minimized=window.is_minimized() if hasattr(window, 'is_minimized') else False,
                is_maximized=window.is_maximized() if hasattr(window, 'is_maximized') else False,
                rectangle=self._get_control_rectangle(window),
                text_content=window.window_text() if hasattr(window, 'window_text') else None,
            )
          
        process_name = self.control_inspector.get_application_root_name(window)
        window_text = window.window_text() if hasattr(window, 'window_text') else "Unknown"
        
        return {
            "process_name": process_name,
            "window_text": window_text,
            "desk_top_windows_info": [w.model_dump() for w in self.last_app_windows_info],
            "window_info": self.selected_app_window_info.model_dump()
        }

    def _handle_get_ui_tree(self, action: GetUITreeAction) -> Dict[str, Any]:
        """Handle get_ui_tree action"""
        params = action.params
        annotation_id = params.annotation_id
        
        if not annotation_id:
            raise ValueError("Annotation ID is required for get_ui_tree")
        
        window = self._get_window_by_annotation_id(annotation_id)
        if not window:
            raise ValueError(f"Window with annotation ID '{annotation_id}' not found")
            
        ui_tree_obj = ui_tree.UITree(window)
        return {"ui_tree": str(ui_tree_obj)}

    def _get_receiver_for_app(self, app_root_name: str):
        """Get appropriate receiver for the application."""
        # Try COM receiver first
        com_factory = COMReceiverFactory()
        receiver = com_factory.create_receiver(app_root_name, "")
        if receiver:
            return receiver
        
        # Try Web receiver
        web_factory = WebReceiverFactory()
        if app_root_name in web_factory.supported_app_roots:
            return web_factory.create_receiver(app_root_name)
        
        # Try Shell receiver as fallback
        shell_factory = ShellReceiverFactory()
        return shell_factory.create_receiver()
    
    def _extract_app_from_action(self, action):
        """Extract application name from action if available."""
        # This would depend on your action structure
        # You might need to add app context to actions
        return None

    def _get_window_by_annotation_id(self, annotation_id: str) -> Optional[UIAWrapper]:
        """Get a window by its annotation ID"""
        if annotation_id and self.last_app_windows:
            return self.last_app_windows.get(annotation_id)
        return self.selected_app_window    
    
    def _handle_execute_mcp_tool(self, action: MCPToolExecutionAction) -> Dict[str, Any]:
        """Handle MCP tool execution by calling the appropriate MCP server."""
        # Check if MCP is enabled
        if not configs.get("USE_MCP", False):
            return {
                "success": False,
                "error": "MCP is disabled in configuration. Set USE_MCP: True to enable MCP functionality.",
                "tool_name": action.params.tool_name,
                "namespace": action.params.app_namespace
            }
                    
        params = action.params
        tool_name = params.tool_name
        tool_args = params.tool_args
        app_namespace = params.app_namespace
        if app_namespace not in self.mcp_servers:
            raise ValueError(f"MCP server not found for namespace: {app_namespace}")
        
        try:
            
            server_config = self.mcp_servers[app_namespace]
            endpoint = server_config["endpoint"]
            
            # Create general MCP client and execute tool
            mcp_client = MCPClient.create_client(endpoint, app_namespace)
            result = mcp_client._make_tool_call(tool_name, tool_args)
            
            return {
                "success": True,
                "result": result,
                "tool_name": tool_name,
                "namespace": app_namespace
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute MCP tool: {str(e)}",
                "tool_name": tool_name,
                "namespace": app_namespace
            }

    def _handle_get_mcp_instructions(self, action: MCPGetInstructionsAction) -> Dict[str, Any]:
        """Get MCP instructions for a specific application namespace."""
        params = action.params
        app_namespace = params.app_namespace
        
        instructions = self.mcp_instructions.get(app_namespace, {})
        
        return {
            "namespace": app_namespace,
            "instructions": instructions,
            "available": app_namespace in self.mcp_instructions
        }
        
    def _handle_get_mcp_available_tools(self, action: MCPGetAvailableToolsAction) -> Dict[str, Any]:
        """Get available MCP tools for a specific application namespace."""
        params = action.params
        app_namespace = params.app_namespace
        if app_namespace not in self.mcp_servers:
            return {
                "namespace": app_namespace,
                "tools": [],
                "available": False
            }
        
        try:
            server_config = self.mcp_servers[app_namespace]
            endpoint = server_config["endpoint"]
            mcp_client = MCPClient.create_client(endpoint, app_namespace)
            result = mcp_client._handle_mcp_get_available_tools(action)
            
            return {
                "namespace": app_namespace,
                "tools": result.get("tools", []),
                "available": True
            }
        except Exception as e:
            # Fallback to instructions if server communication fails
            instructions = self.mcp_instructions.get(app_namespace, {})
            tools = instructions.get("tools", [])
            
            return {
                "namespace": app_namespace,
                "tools": tools,
                "available": len(tools) > 0,
                "fallback": True,
                "error": str(e)
            }
    
    def _normalize_tool_schema(self, tools_data, source="yaml"):
        """
        Normalize tool schema from different sources to ensure compatibility.
        
        Args:
            tools_data: List of tools from either YAML or MCP server
            source: Source type - "yaml" or "mcp"
            
        Returns:
            List of tools in normalized internal format
        """
        if source == "mcp":
            # Transform MCP protocol format to internal YAML format
            normalized_tools = []
            for tool in tools_data:
                # MCP tools typically have this structure:
                # {
                #   "name": "tool_name",
                #   "description": "description",
                #   "inputSchema": {
                #     "type": "object",
                #     "properties": {...},
                #     "required": [...]
                #   }
                # }
                normalized_tool = {
                    "name": tool.get("name"),
                    "description": tool.get("description", ""),
                    # Convert parameters from MCP inputSchema to YAML parameters format
                    "parameters": self._convert_mcp_parameters_to_yaml(tool.get("inputSchema", {})),
                    "source": "mcp"
                }
                
                # Ensure the tool has all properties needed by action2action_sequence
                self._ensure_action_sequence_compatibility(normalized_tool)
                
                normalized_tools.append(normalized_tool)
            return normalized_tools
        elif source == "yaml":
            # YAML format is already in internal format, but ensure compatibility
            normalized_tools = []
            for tool in tools_data:
                normalized_tool = tool.copy()
                self._ensure_action_sequence_compatibility(normalized_tool)
                normalized_tools.append(normalized_tool)
            return normalized_tools
        else:
            return tools_data

    def _convert_mcp_parameters_to_yaml(self, input_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert MCP inputSchema to YAML parameters format.
        
        Args:
            input_schema: MCP inputSchema object
            
        Returns:
            List of parameters in YAML format
        """
        yaml_parameters = []
        
        properties = input_schema.get("properties", {})
        required_fields = input_schema.get("required", [])
        
        for param_name, param_info in properties.items():
            yaml_param = {
                "name": param_name,
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", ""),
                "required": param_name in required_fields
            }
            
            # Add default value if present
            if "default" in param_info:
                yaml_param["default"] = param_info["default"]
                
            yaml_parameters.append(yaml_param)
            
        return yaml_parameters

    def _ensure_action_sequence_compatibility(self, tool: Dict[str, Any]) -> None:
        """
        Ensure the tool has all properties needed by action2action_sequence method.
        
        The action2action_sequence method in agent_prompter.py expects these properties:
        - Function
        - Args
        - Status
        - ControlLabel
        - ControlText
        
        Args:
            tool: Tool definition to modify in place
        """
        # Ensure the tool has a mapping for action2action_sequence properties
        if "action_mapping" not in tool:
            tool["action_mapping"] = {
                "Function": tool.get("name", ""),
                "Args": {},  # Will be populated at runtime from parameters
                "Status": "CONTINUE",  # Default status
                "ControlLabel": "",  # Default empty, can be set during execution
                "ControlText": ""  # Default empty, can be set during execution
            }
        
        # Add schema metadata for validation
        if "schema_version" not in tool:
            tool["schema_version"] = "1.0"
            
        # Add execution hints for the tool
        if "execution_hints" not in tool:
            tool["execution_hints"] = {
                "can_be_used_in_sequence": True,
                "requires_ui_context": False,
                "modifies_application_state": True
            }

    # ...existing code...
    
if __name__ == "__main__":
    computer = Computer("TestComputer")
    action = CaptureDesktopScreenshotAction(
        params=CaptureDesktopScreenshotParams(all_screens=True)
    )
    result = computer.run_action(action)
    
    app_windows = computer.run_action(
        GetDesktopAppInfoAction(
            params=GetDesktopAppInfoParams(remove_empty=True)
        )
    )
    
    app_window_control_info = computer.run_action(
        GetAppWindowControlInfoAction(
            params=GetAppWindowControlInfoParams(
                annotation_id=app_windows[0].annotation_id if app_windows else None,
            )
        )
    )

    print("App Windows Information:", app_windows)
    print("App Window Control Information:", app_window_control_info)