# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Routers for Galaxy Web UI.

This package contains FastAPI routers that define API endpoints
and WebSocket endpoints for the Web UI.
"""

from galaxy.webui.routers.health import router as health_router
from galaxy.webui.routers.devices import router as devices_router
from galaxy.webui.routers.websocket import router as websocket_router

__all__ = [
    "health_router",
    "devices_router",
    "websocket_router",
]
