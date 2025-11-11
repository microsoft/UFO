# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Data models for Galaxy Web UI.

This package contains Pydantic models and enums used throughout the Web UI.
"""

from galaxy.webui.models.enums import (
    WebSocketMessageType,
    RequestStatus,
)
from galaxy.webui.models.requests import (
    DeviceAddRequest,
    WebSocketMessage,
    RequestMessage,
    ResetMessage,
    NextSessionMessage,
    StopTaskMessage,
    PingMessage,
)
from galaxy.webui.models.responses import (
    StandardResponse,
    HealthResponse,
    DeviceAddResponse,
    WelcomeMessage,
    RequestReceivedMessage,
    RequestCompletedMessage,
    RequestFailedMessage,
    ResetAcknowledgedMessage,
    NextSessionAcknowledgedMessage,
    StopAcknowledgedMessage,
    PongMessage,
    ErrorMessage,
)

__all__ = [
    # Enums
    "WebSocketMessageType",
    "RequestStatus",
    # Requests
    "DeviceAddRequest",
    "WebSocketMessage",
    "RequestMessage",
    "ResetMessage",
    "NextSessionMessage",
    "StopTaskMessage",
    "PingMessage",
    # Responses
    "StandardResponse",
    "HealthResponse",
    "DeviceAddResponse",
    "WelcomeMessage",
    "RequestReceivedMessage",
    "RequestCompletedMessage",
    "RequestFailedMessage",
    "ResetAcknowledgedMessage",
    "NextSessionAcknowledgedMessage",
    "StopAcknowledgedMessage",
    "PongMessage",
    "ErrorMessage",
]
