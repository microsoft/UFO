# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
UFO Contracts - Backward Compatibility Layer

This module maintains backward compatibility by re-exporting message types from AIP.
All new code should import directly from aip.messages instead.

Deprecated: This module will be removed in a future version.
Use: from aip.messages import ClientMessage, ServerMessage, ...
"""

# Import from AIP for backward compatibility
from aip.messages import (
    AppWindowControlInfo,
    ClientMessage,
    ClientMessageType,
    ClientType,
    Command,
    ControlInfo,
    MCPToolCall,
    MCPToolInfo,
    Rect,
    Result,
    ResultStatus,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
    WindowInfo,
)

# Re-export all symbols for backward compatibility
__all__ = [
    "Rect",
    "ControlInfo",
    "WindowInfo",
    "AppWindowControlInfo",
    "MCPToolInfo",
    "MCPToolCall",
    "Command",
    "ResultStatus",
    "Result",
    "TaskStatus",
    "ClientMessageType",
    "ServerMessageType",
    "ClientType",
    "ServerMessage",
    "ClientMessage",
]
