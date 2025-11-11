# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Request models for Galaxy Web UI.

This module defines Pydantic models for all incoming requests,
both HTTP API requests and WebSocket messages.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from galaxy.webui.models.enums import WebSocketMessageType


class DeviceAddRequest(BaseModel):
    """
    Request model for adding a new device to the Galaxy configuration.

    This model is used for the POST /api/devices endpoint to validate
    and structure device registration data.
    """

    device_id: str = Field(..., description="Unique identifier for the device")
    server_url: str = Field(..., description="URL of the device's server endpoint")
    os: str = Field(
        ..., description="Operating system of the device (e.g., 'Windows', 'Linux')"
    )
    capabilities: List[str] = Field(
        ..., description="List of capabilities the device supports"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata about the device"
    )
    auto_connect: Optional[bool] = Field(
        True, description="Whether to automatically connect to the device"
    )
    max_retries: Optional[int] = Field(
        5, description="Maximum number of connection retry attempts"
    )


class WebSocketMessage(BaseModel):
    """
    Base model for WebSocket messages.

    All WebSocket messages must include a type field to identify
    the message purpose and optional data payload.
    """

    type: WebSocketMessageType = Field(..., description="Type of the WebSocket message")
    data: Optional[Dict[str, Any]] = Field(
        None, description="Optional data payload for the message"
    )


class PingMessage(BaseModel):
    """
    Ping message for health check.

    Client sends this to check if the server is responsive.
    """

    type: Literal[WebSocketMessageType.PING] = WebSocketMessageType.PING


class RequestMessage(BaseModel):
    """
    Request message to process a user request.

    Client sends this to initiate processing of a natural language request.
    """

    type: Literal[WebSocketMessageType.REQUEST] = WebSocketMessageType.REQUEST
    text: str = Field(..., description="The natural language request text to process")


class ResetMessage(BaseModel):
    """
    Reset message to reset the current session.

    Client sends this to reset the Galaxy session and clear state.
    """

    type: Literal[WebSocketMessageType.RESET] = WebSocketMessageType.RESET


class NextSessionMessage(BaseModel):
    """
    Next session message to create a new session.

    Client sends this to create a new Galaxy session while maintaining
    some context from the previous session.
    """

    type: Literal[WebSocketMessageType.NEXT_SESSION] = WebSocketMessageType.NEXT_SESSION


class StopTaskMessage(BaseModel):
    """
    Stop task message to cancel current task execution.

    Client sends this to stop the currently executing task and clean up resources.
    """

    type: Literal[WebSocketMessageType.STOP_TASK] = WebSocketMessageType.STOP_TASK
