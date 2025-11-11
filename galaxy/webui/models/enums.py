# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Enumerations for Galaxy Web UI.

This module defines all enum types used in the Web UI for type safety
and standardization of string constants.
"""

from enum import Enum


class WebSocketMessageType(str, Enum):
    """
    Types of WebSocket messages exchanged between client and server.

    These message types define the protocol for communication over WebSocket.
    """

    # Client -> Server messages
    PING = "ping"
    REQUEST = "request"
    RESET = "reset"
    NEXT_SESSION = "next_session"
    STOP_TASK = "stop_task"

    # Server -> Client messages
    PONG = "pong"
    WELCOME = "welcome"
    REQUEST_RECEIVED = "request_received"
    REQUEST_COMPLETED = "request_completed"
    REQUEST_FAILED = "request_failed"
    RESET_ACKNOWLEDGED = "reset_acknowledged"
    NEXT_SESSION_ACKNOWLEDGED = "next_session_acknowledged"
    STOP_ACKNOWLEDGED = "stop_acknowledged"
    ERROR = "error"


class RequestStatus(str, Enum):
    """
    Status of a user request being processed.

    These statuses track the lifecycle of a request from submission to completion.
    """

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SUCCESS = "success"
    WARNING = "warning"
