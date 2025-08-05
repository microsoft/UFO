from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict
from ufo.client.mcp.mcp_server_manager import BaseMCPServer


class Rect(BaseModel):
    """
    Rectangle coordinates for UI elements.
    Represents a rectangle with x, y coordinates and width and height.
    """

    x: int
    y: int
    width: int
    height: int


class ControlInfo(BaseModel):
    """
    Information about a UI control.
    """

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
    """
    Information about a window in the UI.
    """

    process_id: Optional[int] = None
    process_name: Optional[str] = None
    is_visible: Optional[bool] = None
    is_minimized: Optional[bool] = None
    is_maximized: Optional[bool] = None
    is_active: Optional[bool] = None


class AppWindowControlInfo(BaseModel):
    """
    Information about a window and its controls.
    """

    window_info: WindowInfo
    controls: Optional[List[ControlInfo]] = None


class MCPToolInfo(BaseModel):
    """
    Information about a tool registered with the computer.
    """

    tool_key: str
    tool_name: str
    title: Optional[str] = None
    namespace: str
    tool_type: str
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None


class MCPToolCall(BaseModel):
    """
    Information about a tool registered with the computer and its associated MCP server.
    """

    tool_key: str  # Unique key for the tool, e.g., "namespace.tool_name"
    tool_name: str  # Name of the tool
    title: Optional[str] = None  # Title of the tool, if any
    namespace: str  # Namespace of the tool, same as the MCP server namespace
    tool_type: str  # Type of the tool (e.g., "action", "data_collection")
    description: str  # Description of the tool
    input_schema: Optional[Dict[str, Any]] = None  # Input schema for the tool, if any
    output_schema: Optional[Dict[str, Any]] = None  # Output schema for the tool, if any
    parameters: Optional[Dict[str, Any]] = None  # Parameters for the tool, if any
    mcp_server: BaseMCPServer  # The BaseMCPServer instance where the tool is registered
    meta: Optional[Dict[str, Any]] = None  # Metadata about the tool, if any
    annotations: Optional[Dict[str, Any]] = None  # Annotations for the tool, if any

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def tool_info(self) -> MCPToolInfo:
        """
        Get a dictionary representation of the tool call.
        :return: Dictionary with tool information.
        """
        return MCPToolInfo(
            tool_key=self.tool_key,
            tool_name=self.tool_name,
            title=self.title,
            namespace=self.namespace,
            tool_type=self.tool_type,
            description=self.description,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            meta=self.meta,
            annotations=self.annotations,
        )


class Command(BaseModel):
    """
    Represents a command to be executed by the computer.
    """

    tool_name: str
    parameters: Optional[Dict[str, Any]] = None
    tool_type: Literal["data_collection", "action"]
    call_id: Optional[str] = None


class Result(BaseModel):
    """
    Represents the result of a command execution.
    """

    status: Literal["success", "failure", "skipped"]
    error: Optional[str] = None
    result: Any = None


class ServerResponse(BaseModel):
    """
    Represents a response from the server to the client.
    """

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
    """
    Represents a request from the client to the server.
    """

    session_id: Optional[str] = None
    request: Optional[str] = None
    action_results: Optional[Dict[str, Result]] = None
    timestamp: Optional[str] = None
