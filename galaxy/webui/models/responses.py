# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Response models for Galaxy Web UI.

This module defines Pydantic models for all outgoing responses,
both HTTP API responses and WebSocket messages.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from galaxy.webui.models.enums import WebSocketMessageType, RequestStatus


class StandardResponse(BaseModel):
    """
    Standard response format for API endpoints.

    Provides a consistent structure for API responses with status,
    message, timestamp, and optional data payload.
    """

    status: str = Field(
        ..., description="Status of the response (e.g., 'success', 'error')"
    )
    message: str = Field(
        ..., description="Human-readable message describing the response"
    )
    timestamp: float = Field(
        ..., description="Unix timestamp when the response was generated"
    )
    data: Optional[Dict[str, Any]] = Field(None, description="Optional data payload")


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.

    Returns information about the server's current health status.
    """

    status: str = Field(..., description="Health status of the server")
    connections: int = Field(..., description="Number of active WebSocket connections")
    events_sent: int = Field(..., description="Total number of events sent to clients")


class DeviceAddResponse(BaseModel):
    """
    Response model for device addition endpoint.

    Returns confirmation of device addition with device details.
    """

    status: str = Field(..., description="Status of the device addition operation")
    message: str = Field(..., description="Human-readable message about the operation")
    device: Dict[str, Any] = Field(..., description="Details of the added device")


class WelcomeMessage(BaseModel):
    """
    Welcome message sent when WebSocket connection is established.

    Confirms successful connection and provides initial timestamp.
    """

    type: Literal[WebSocketMessageType.WELCOME] = WebSocketMessageType.WELCOME
    message: str = Field(..., description="Welcome message text")
    timestamp: float = Field(
        ..., description="Server timestamp when connection was established"
    )


class PongMessage(BaseModel):
    """
    Pong response to ping message.

    Confirms server is responsive to client health checks.
    """

    type: Literal[WebSocketMessageType.PONG] = WebSocketMessageType.PONG
    timestamp: float = Field(..., description="Server timestamp of the pong response")


class RequestReceivedMessage(BaseModel):
    """
    Acknowledgment that a request has been received and is being processed.

    Sent immediately after receiving a user request to provide feedback.
    """

    type: Literal[WebSocketMessageType.REQUEST_RECEIVED] = (
        WebSocketMessageType.REQUEST_RECEIVED
    )
    request: str = Field(..., description="The request text that was received")
    status: Literal[RequestStatus.PROCESSING] = RequestStatus.PROCESSING


class RequestCompletedMessage(BaseModel):
    """
    Message indicating request processing has completed successfully.

    Contains the result of the processed request.
    """

    type: Literal[WebSocketMessageType.REQUEST_COMPLETED] = (
        WebSocketMessageType.REQUEST_COMPLETED
    )
    request: str = Field(..., description="The request text that was processed")
    status: Literal[RequestStatus.COMPLETED] = RequestStatus.COMPLETED
    result: str = Field(..., description="The result of the request processing")


class RequestFailedMessage(BaseModel):
    """
    Message indicating request processing has failed.

    Contains error information about why the request failed.
    """

    type: Literal[WebSocketMessageType.REQUEST_FAILED] = (
        WebSocketMessageType.REQUEST_FAILED
    )
    request: str = Field(..., description="The request text that failed")
    status: Literal[RequestStatus.FAILED] = RequestStatus.FAILED
    error: str = Field(..., description="Error message explaining the failure")


class ResetAcknowledgedMessage(BaseModel):
    """
    Acknowledgment that session reset has been completed.

    Confirms the session state has been cleared.
    """

    type: Literal[WebSocketMessageType.RESET_ACKNOWLEDGED] = (
        WebSocketMessageType.RESET_ACKNOWLEDGED
    )
    status: str = Field(..., description="Status of the reset operation")
    message: str = Field(..., description="Message describing the reset result")
    timestamp: Optional[float] = Field(
        None, description="Timestamp of the reset operation"
    )


class NextSessionAcknowledgedMessage(BaseModel):
    """
    Acknowledgment that a new session has been created.

    Contains information about the newly created session.
    """

    type: Literal[WebSocketMessageType.NEXT_SESSION_ACKNOWLEDGED] = (
        WebSocketMessageType.NEXT_SESSION_ACKNOWLEDGED
    )
    status: str = Field(..., description="Status of the session creation")
    message: str = Field(..., description="Message describing the session creation")
    session_name: Optional[str] = Field(
        None, description="Name of the newly created session"
    )
    task_name: Optional[str] = Field(
        None, description="Name of the task for the new session"
    )
    timestamp: Optional[float] = Field(
        None, description="Timestamp of session creation"
    )


class StopAcknowledgedMessage(BaseModel):
    """
    Acknowledgment that task has been stopped.

    Confirms the task execution has been terminated and resources cleaned up.
    """

    type: Literal[WebSocketMessageType.STOP_ACKNOWLEDGED] = (
        WebSocketMessageType.STOP_ACKNOWLEDGED
    )
    status: str = Field(..., description="Status of the stop operation")
    message: str = Field(..., description="Message describing the stop result")
    session_name: Optional[str] = Field(
        None, description="Name of the session after restart"
    )
    timestamp: float = Field(..., description="Timestamp of the stop operation")


class ErrorMessage(BaseModel):
    """
    Error message for communicating failures to the client.

    Provides detailed error information for debugging and user feedback.
    """

    type: Literal[WebSocketMessageType.ERROR] = WebSocketMessageType.ERROR
    message: str = Field(..., description="Error message describing what went wrong")
