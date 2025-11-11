# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
WebSocket message handlers for Galaxy Web UI.

This module contains handlers for processing different types of WebSocket
messages from clients, implementing the business logic for each message type.
"""

import asyncio
import logging
import time
from typing import Any, Dict

from fastapi import WebSocket

from galaxy.webui.dependencies import AppState
from galaxy.webui.models.enums import WebSocketMessageType, RequestStatus
from galaxy.webui.services import DeviceService, GalaxyService


class WebSocketMessageHandler:
    """
    Handler for processing WebSocket messages.

    This class encapsulates the logic for handling different types of
    WebSocket messages, separating concerns and improving testability.
    """

    def __init__(self, app_state: AppState) -> None:
        """
        Initialize the WebSocket message handler.

        :param app_state: Application state containing Galaxy client references
        """
        self.app_state = app_state
        self.galaxy_service = GalaxyService(app_state)
        self.device_service = DeviceService(app_state)
        self.logger: logging.Logger = logging.getLogger(__name__)

    async def handle_message(self, websocket: WebSocket, data: dict) -> None:
        """
        Route incoming WebSocket messages to appropriate handlers.

        :param websocket: The WebSocket connection
        :param data: The message data from client
        """
        message_type: str = data.get("type", "")
        self.logger.info(f"Received message - Type: {message_type}, Full data: {data}")

        # Route to specific handler based on message type
        if message_type == WebSocketMessageType.PING:
            await self._handle_ping(websocket, data)
        elif message_type == WebSocketMessageType.REQUEST:
            await self._handle_request(websocket, data)
        elif message_type == WebSocketMessageType.RESET:
            await self._handle_reset(websocket, data)
        elif message_type == WebSocketMessageType.NEXT_SESSION:
            await self._handle_next_session(websocket, data)
        elif message_type == WebSocketMessageType.STOP_TASK:
            await self._handle_stop_task(websocket, data)
        else:
            await self._handle_unknown(websocket, message_type)

    async def _handle_ping(self, websocket: WebSocket, data: dict) -> None:
        """
        Handle ping message by responding with pong.

        Provides health check functionality for clients to verify
        the server is responsive.

        :param websocket: The WebSocket connection
        :param data: The ping message data
        """
        await websocket.send_json(
            {
                "type": WebSocketMessageType.PONG,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )
        self.logger.debug("Responded to ping with pong")

    async def _handle_request(self, websocket: WebSocket, data: dict) -> None:
        """
        Handle user request to process a natural language command.

        Sends immediate acknowledgment and processes the request in the background,
        sending completion or failure messages when done.

        :param websocket: The WebSocket connection
        :param data: The request message data containing 'text' field
        """
        request_text: str = data.get("text", "")
        self.logger.info(f"Received request: {request_text}")

        if not self.galaxy_service.is_client_available():
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.ERROR,
                    "message": "Galaxy client not initialized",
                }
            )
            return

        # Send immediate acknowledgment to client
        await websocket.send_json(
            {
                "type": WebSocketMessageType.REQUEST_RECEIVED,
                "request": request_text,
                "status": RequestStatus.PROCESSING,
            }
        )

        # Process request in background task
        async def process_in_background() -> None:
            try:
                result = await self.galaxy_service.process_request(request_text)
                await websocket.send_json(
                    {
                        "type": WebSocketMessageType.REQUEST_COMPLETED,
                        "request": request_text,
                        "status": RequestStatus.COMPLETED,
                        "result": str(result),
                    }
                )
            except Exception as e:
                self.logger.error(f"❌ Error processing request: {e}", exc_info=True)
                await websocket.send_json(
                    {
                        "type": WebSocketMessageType.REQUEST_FAILED,
                        "request": request_text,
                        "status": RequestStatus.FAILED,
                        "error": str(e),
                    }
                )

        # Start background task
        asyncio.create_task(process_in_background())

    async def _handle_reset(self, websocket: WebSocket, data: dict) -> None:
        """
        Handle session reset request.

        Resets the current Galaxy session and clears state.

        :param websocket: The WebSocket connection
        :param data: The reset message data
        """
        self.logger.info("Received reset request")

        if not self.galaxy_service.is_client_available():
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.RESET_ACKNOWLEDGED,
                    "status": RequestStatus.WARNING,
                    "message": "No active client to reset",
                }
            )
            return

        try:
            result = await self.galaxy_service.reset_session()
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.RESET_ACKNOWLEDGED,
                    "status": result.get("status", RequestStatus.SUCCESS),
                    "message": result.get("message", "Session reset"),
                    "timestamp": result.get("timestamp"),
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to reset session: {e}", exc_info=True)
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.ERROR,
                    "message": f"Failed to reset session: {str(e)}",
                }
            )

    async def _handle_next_session(self, websocket: WebSocket, data: dict) -> None:
        """
        Handle next session creation request.

        Creates a new Galaxy session while potentially maintaining some context.

        :param websocket: The WebSocket connection
        :param data: The next session message data
        """
        self.logger.info("Received next_session request")

        if not self.galaxy_service.is_client_available():
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.ERROR,
                    "message": "Galaxy client not initialized",
                }
            )
            return

        try:
            result = await self.galaxy_service.create_next_session()
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.NEXT_SESSION_ACKNOWLEDGED,
                    "status": result.get("status", RequestStatus.SUCCESS),
                    "message": result.get("message", "Next session created"),
                    "session_name": result.get("session_name"),
                    "task_name": result.get("task_name"),
                    "timestamp": result.get("timestamp"),
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to create next session: {e}", exc_info=True)
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.ERROR,
                    "message": f"Failed to create next session: {str(e)}",
                }
            )

    async def _handle_stop_task(self, websocket: WebSocket, data: dict) -> None:
        """
        Handle task stop/cancel request.

        Shuts down the Galaxy client to clean up device tasks, then reinitializes
        the client and creates a new session.

        :param websocket: The WebSocket connection
        :param data: The stop task message data
        """
        self.logger.info("Received stop_task request")

        if not self.galaxy_service.is_client_available():
            self.logger.warning("No active galaxy client to stop")
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.STOP_ACKNOWLEDGED,
                    "status": RequestStatus.WARNING,
                    "message": "No active task to stop",
                    "timestamp": time.time(),
                }
            )
            return

        try:
            new_session_result = await self.galaxy_service.stop_task_and_restart()
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.STOP_ACKNOWLEDGED,
                    "status": RequestStatus.SUCCESS,
                    "message": "Task stopped and client restarted",
                    "session_name": new_session_result.get("session_name"),
                    "timestamp": time.time(),
                }
            )
        except Exception as e:
            self.logger.error(
                f"Failed to stop task and restart client: {e}", exc_info=True
            )
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.ERROR,
                    "message": f"Failed to stop task: {str(e)}",
                }
            )

    async def _handle_unknown(self, websocket: WebSocket, message_type: str) -> None:
        """
        Handle unknown message types.

        Logs a warning and sends an error response to the client.

        :param websocket: The WebSocket connection
        :param message_type: The unknown message type
        """
        self.logger.warning(f"Unknown message type: {message_type}")
        await websocket.send_json(
            {
                "type": WebSocketMessageType.ERROR,
                "message": f"Unknown message type: {message_type}",
            }
        )

    async def send_welcome_message(self, websocket: WebSocket) -> None:
        """
        Send welcome message to newly connected client.

        Sends a welcome message and initial device snapshot to help
        the UI render current state immediately.

        :param websocket: The WebSocket connection
        """
        # Send welcome message
        await websocket.send_json(
            {
                "type": WebSocketMessageType.WELCOME,
                "message": "Connected to Galaxy Web UI",
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

        # Send initial device snapshot
        device_snapshot = self.device_service.build_device_snapshot()
        if device_snapshot:
            await websocket.send_json(
                {
                    "event_type": "device_snapshot",
                    "source_id": "webui.server",
                    "timestamp": time.time(),
                    "data": {
                        "event_name": "device_snapshot",
                        "device_count": len(device_snapshot),
                    },
                    "all_devices": device_snapshot,
                }
            )
