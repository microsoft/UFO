# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
WebSocket router for Galaxy Web UI.

This module defines the WebSocket endpoint for real-time event streaming
and bidirectional communication with clients.
"""

import logging
import secrets

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from galaxy.webui.dependencies import get_app_state
from galaxy.webui.handlers import WebSocketMessageHandler

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)

WS_1008_POLICY_VIOLATION = 1008


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default=None),
) -> None:
    """
    WebSocket endpoint for real-time event streaming.

    Requires a valid ``token`` query parameter that matches the server API key.

    This endpoint establishes a persistent connection with clients to:
    - Send welcome messages and initial state (device snapshots)
    - Receive and process client messages (requests, commands)
    - Broadcast Galaxy events to all connected clients in real-time

    The connection lifecycle:
    1. Validate the token query parameter
    2. Accept the WebSocket connection
    3. Register with the WebSocket observer for event broadcasting
    4. Send welcome message and initial device snapshot
    5. Process incoming messages until disconnection
    6. Cleanup and remove from observer on disconnect

    :param websocket: The WebSocket connection from the client
    :param token: API key passed as a query parameter
    """
    # Validate token before accepting the connection
    app_state = get_app_state()
    expected_key = app_state.api_key
    if (
        not expected_key
        or not token
        or not secrets.compare_digest(token, expected_key)
    ):
        await websocket.close(
            code=WS_1008_POLICY_VIOLATION,
            reason="Invalid or missing token",
        )
        logger.warning(
            "WebSocket connection rejected (invalid token) from %s",
            websocket.client,
        )
        return

    await websocket.accept()
    logger.info(f"WebSocket connection established from {websocket.client}")

    # Get application state and message handler
    app_state = get_app_state()
    message_handler = WebSocketMessageHandler(app_state)

    # Add connection to observer for event broadcasting
    websocket_observer = app_state.websocket_observer
    if websocket_observer:
        websocket_observer.add_connection(websocket)

    try:
        # Send welcome message and initial device snapshot
        await message_handler.send_welcome_message(websocket)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for and receive message from client
                data: dict = await websocket.receive_json()

                # Process the message through handler
                await message_handler.handle_message(websocket, data)

            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error receiving/processing WebSocket message: {e}")
                # Continue listening for messages unless it's a connection error
                # The outer try-finally will handle cleanup
                break

    finally:
        # Remove connection from observer on disconnect
        if websocket_observer:
            websocket_observer.remove_connection(websocket)
        logger.info("WebSocket connection closed")
