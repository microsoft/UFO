# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Web UI Module.

Provides a modern web interface for the Galaxy Framework with real-time
event streaming via WebSocket.
"""

from .server import app, start_server, set_galaxy_session
from .websocket_observer import WebSocketObserver

__all__ = [
    "app",
    "start_server",
    "set_galaxy_session",
    "WebSocketObserver",
]
