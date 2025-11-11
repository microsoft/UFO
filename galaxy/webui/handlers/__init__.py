# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Handlers for Galaxy Web UI.

This package contains handlers for processing various types of messages
and requests, particularly WebSocket message handlers.
"""

from galaxy.webui.handlers.websocket_handlers import WebSocketMessageHandler

__all__ = [
    "WebSocketMessageHandler",
]
