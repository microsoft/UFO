from typing import Any, List, Literal, Optional, Dict
from pydantic import BaseModel


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


class MCPToolInfo(BaseModel):
    tool_key: str
    tool_name: str
    title: Optional[str] = None
    namespace: str
    tool_type: str
    description: Optional[str] = None
    tool_schema: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None


class Command(BaseModel):
    tool_name: str
    parameters: Optional[Dict[str, Any]] = None
    tool_type: Literal["data_collection", "action"]
    call_id: Optional[str] = None


class Result(BaseModel):
    status: Literal["success", "failure", "skipped"]
    error: Optional[str] = None
    result: Any = None


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
    action_results: Optional[Dict[str, Result]] = None
    timestamp: Optional[str] = None
