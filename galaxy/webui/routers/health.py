# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Health check router for Galaxy Web UI.

This module defines the health check endpoint that returns server status.
"""

from typing import Dict, Any

from fastapi import APIRouter

from galaxy.webui.dependencies import get_app_state
from galaxy.webui.models.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns the current status of the server including:
    - Overall health status
    - Number of active WebSocket connections
    - Total number of events sent to clients

    This endpoint can be used for monitoring and load balancer health checks.

    :return: Dictionary containing health status information
    """
    app_state = get_app_state()
    websocket_observer = app_state.websocket_observer

    return {
        "status": "healthy",
        "connections": (
            websocket_observer.connection_count if websocket_observer else 0
        ),
        "events_sent": (
            websocket_observer.total_events_sent if websocket_observer else 0
        ),
    }
