from typing import Any, List, Literal, Optional, Union, Dict, Annotated
from pydantic import BaseModel, Field


class Rect(BaseModel):
    x: int
    y: int
    width: int
    height: int


class ControlInfo(BaseModel):
    annotation_id: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    handle: Optional[int] = None
    class_name: Optional[str] = None
    rectangle: Optional[Rect] = None
    control_type: Optional[str] = None

    automation_id: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_visible: Optional[bool] = None
    source: Optional[str] = None
    text_content: Optional[str] = None


class WindowInfo(ControlInfo):
    process_id: Optional[int] = None
    process_name: Optional[str] = None
    is_visible: Optional[bool] = None
    is_minimized: Optional[bool] = None
    is_maximized: Optional[bool] = None
    is_active: Optional[bool] = None


class AppWindowControlInfo(BaseModel):
    window_info: WindowInfo
    controls: Optional[List[ControlInfo]] = None


class ActionBase(BaseModel):
    name: str
    params: Optional[BaseModel] = None
    call_id: Optional[str] = None


class CallbackAction(ActionBase):
    name: Literal["callback"] = "callback"
    params: Optional[Dict[str, Any]] = None


class CaptureDesktopScreenshotParams(BaseModel):
    all_screens: bool = True
    remove_empty: bool = True
    refresh_app_windows: bool = False


class CaptureDesktopScreenshotAction(ActionBase):
    name: Literal["capture_desktop_screenshot"] = "capture_desktop_screenshot"
    params: Optional[CaptureDesktopScreenshotParams] = None


class GetDesktopAppInfoParams(BaseModel):
    remove_empty: bool = True
    refresh_app_windows: bool = False


class GetDesktopAppInfoAction(ActionBase):
    name: Literal["get_desktop_app_info"] = "get_desktop_app_info"
    params: Optional[GetDesktopAppInfoParams] = None


class SelectApplicationWindowParams(BaseModel):
    window_label: Optional[str] = None


class SelectApplicationWindowAction(ActionBase):
    name: Literal["select_application_window"] = "select_application_window"
    params: Optional[SelectApplicationWindowParams] = None


class LaunchApplicationParams(BaseModel):
    bash_command: Optional[str] = None


class LaunchApplicationAction(ActionBase):
    name: Literal["launch_application"] = "launch_application"
    params: Optional[LaunchApplicationParams] = None


class CaptureAppWindowScreenshotParams(BaseModel):
    annotation_id: Optional[str] = None


class CaptureAppWindowScreenshotAction(ActionBase):
    name: Literal["capture_app_window_screenshot"] = "capture_app_window_screenshot"
    params: Optional[CaptureAppWindowScreenshotParams] = None


class CaptureAppWindowScreenshotFromWebcamParams(BaseModel):
    annotation_id: Optional[str] = None
    webcam_index: int = 0  # Default to the first webcam
    width: int = 640
    height: int = 480


class CaptureAppWindowScreenshotFromWebcamAction(ActionBase):
    name: Literal["capture_app_window_screenshot_from_webcam"] = (
        "capture_app_window_screenshot_from_webcam"
    )
    params: Optional[CaptureAppWindowScreenshotFromWebcamParams] = None


class GetAppWindowControlInfoParams(BaseModel):
    annotation_id: Optional[str] = None
    field_list: Optional[Any] = None


class GetAppWindowControlInfoAction(ActionBase):
    name: Literal["get_app_window_control_info"] = "get_app_window_control_info"
    params: Optional[GetAppWindowControlInfoParams] = None


class FindControlElementsParams(BaseModel):
    annotation_id: Optional[str] = None
    control_type_list: List[Any] = []
    class_name_list: List[Any] = []


class FindControlElementsAction(ActionBase):
    name: Literal["find_control_elements"] = "find_control_elements"
    params: Optional[FindControlElementsParams] = None


class GetUITreeParams(BaseModel):
    annotation_id: Optional[str] = None
    remove_empty: bool = True


class GetUITreeAction(ActionBase):
    name: Literal["get_ui_tree"] = "get_ui_tree"
    params: Optional[GetUITreeParams] = None


# Interaction actions
class MouseClickParams(BaseModel):
    button: Literal["left", "right", "middle"] = "left"
    click_type: Literal["single", "double"] = "single"


class MouseMoveToParams(BaseModel):
    x: float
    y: float


class MouseDragParams(BaseModel):
    path: list[dict[str, int]]


class MouseWheelParams(BaseModel):
    x: int = 0
    y: int = 0
    scroll_x: int = 0
    scroll_y: int = 0


class KeyboardTypeParams(BaseModel):
    text: str


class KeyboardKeyParams(BaseModel):
    keys: List[str]


class UIACommandParams(BaseModel):
    control_label: Optional[str] = None
    control_text: Optional[str] = None
    after_status: Optional[str] = None


class ClickInputParams(UIACommandParams):
    button: str = "left"
    double: bool = False


class ClickOnCoordinatesParams(UIACommandParams):
    x: float
    y: float
    button: str = "left"
    double: bool = False


class DragOnCoordinatesParams(UIACommandParams):
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    duration: float = 1.0
    button: str = "left"
    key_hold: Optional[str] = None


class SummaryParams(UIACommandParams):
    text: str


class SetEditTextParams(UIACommandParams):
    text: str


class KeyboardInputParams(UIACommandParams):
    control_focus: bool = True
    keys: str


class WheelMouseInputParams(UIACommandParams):
    x_dist: int = 0
    y_dist: int = 0


class AnnotationParams(UIACommandParams):
    control_labels: List[str]


class NoActionParams(BaseModel):
    pass


# MCP Action Contracts
class MCPToolExecutionParams(BaseModel):
    tool_name: str
    tool_args: Dict[str, Any]
    app_namespace: str


class MCPToolExecutionAction(ActionBase):
    name: Literal["execute_mcp_tool"] = "execute_mcp_tool"
    params: Optional[MCPToolExecutionParams] = None


class MCPGetInstructionsParams(BaseModel):
    app_namespace: str


class MCPGetInstructionsAction(ActionBase):
    name: Literal["get_mcp_instructions"] = "get_mcp_instructions"
    params: Optional[MCPGetInstructionsParams] = None


class MCPGetAvailableToolsParams(BaseModel):
    app_namespace: str


class MCPGetAvailableToolsAction(ActionBase):
    name: Literal["get_mcp_available_tools"] = "get_mcp_available_tools"
    params: Optional[MCPGetAvailableToolsParams] = None


class OperationCommand(BaseModel):
    command_id: str
    click_input: Optional[ClickInputParams] = None
    click_on_coordinates: Optional[ClickOnCoordinatesParams] = None
    drag_on_coordinates: Optional[DragOnCoordinatesParams] = None
    summary: Optional[SummaryParams] = None
    set_edit_text: Optional[SetEditTextParams] = None
    keyboard_input: Optional[KeyboardInputParams] = None
    wheel_mouse_input: Optional[WheelMouseInputParams] = None
    annotation: Optional[AnnotationParams] = None
    no_action: Optional[NoActionParams] = None

    def get_command_type(self) -> Optional[str]:
        for field, value in self.model_dump(exclude_unset=True).items():
            if value is not None:
                return field
        return None


class OperationSequenceAction(ActionBase):
    name: Literal["operation_sequence"] = "operation_sequence"
    params: Optional[list[OperationCommand]] = None


class GetDesktopControlInfoParams(BaseModel):
    all_screens: bool = True
    remove_empty: bool = True
    refresh_app_windows: bool = False


class GetDesktopControlInfoAction(ActionBase):
    name: Literal["get_desktop_control_info"] = "get_desktop_control_info"
    params: Optional[GetDesktopControlInfoParams] = None


UFOAction = Annotated[
    Union[
        CaptureDesktopScreenshotAction,
        GetDesktopAppInfoAction,
        GetDesktopControlInfoAction,
        SelectApplicationWindowAction,
        LaunchApplicationAction,
        CaptureAppWindowScreenshotAction,
        CaptureAppWindowScreenshotFromWebcamAction,
        GetAppWindowControlInfoAction,
        FindControlElementsAction,
        GetUITreeAction,
        OperationSequenceAction,
        CallbackAction,
        MCPToolExecutionAction,
        MCPGetInstructionsAction,
        MCPGetAvailableToolsAction,
    ],
    Field(discriminator="name"),
]


class Command(BaseModel):
    tool_name: str
    parameters: Optional[Dict[str, Any]] = None
    tool_type: Literal["data_collection", "action"]
    call_id: Optional[str] = None


class ServerResponse(BaseModel):
    status: Literal["continue", "completed", "failure"]
    agent_name: Optional[str] = None
    process_name: Optional[str] = None
    root_name: Optional[str] = None
    actions: Optional[List[Command]] = None
    messages: Optional[List[str]] = None
    error: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[str] = None


class ClientRequest(BaseModel):
    session_id: Optional[str] = None
    request: Optional[str] = None
    action_results: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


class UFORequest(BaseModel):
    session_id: Optional[str] = None
    request: Optional[str] = None
    action_results: Optional[Dict[str, Any]] = None


class UFOResponse(BaseModel):
    session_id: Optional[str] = None
    status: Literal["continue", "completed", "failure"]
    actions: Optional[List[UFOAction]] = None
    error: Optional[str] = None
    messages: Optional[List[str]] = None
