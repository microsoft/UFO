# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Message Processor

Processes incoming messages from UFO servers.
Single responsibility: Message handling and routing.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from websockets import WebSocketClientProtocol
import websockets

from ufo.contracts.contracts import ServerMessage, ServerMessageType, TaskStatus
from .device_registry import DeviceRegistry
from .heartbeat_manager import HeartbeatManager
from .event_manager import EventManager

# Avoid circular import
if TYPE_CHECKING:
    from .connection_manager import WebSocketConnectionManager


class MessageProcessor:
    """
    Processes incoming messages from UFO servers.
    Single responsibility: Message handling and routing.

    The MessageProcessor listens for incoming WebSocket messages from UFO servers
    and routes them to appropriate handlers based on message type. It also coordinates
    with the ConnectionManager to complete pending task responses.
    """

    def __init__(
        self,
        device_registry: DeviceRegistry,
        heartbeat_manager: HeartbeatManager,
        event_manager: EventManager,
        connection_manager: Optional["WebSocketConnectionManager"] = None,
    ):
        """
        Initialize the MessageProcessor.

        :param device_registry: Registry for tracking connected devices
        :param heartbeat_manager: Manager for device heartbeat monitoring
        :param event_manager: Manager for event callbacks
        :param connection_manager: Optional ConnectionManager for completing task responses
                                  (set later via set_connection_manager to avoid circular dependency)
        """
        self.device_registry = device_registry
        self.heartbeat_manager = heartbeat_manager
        self.event_manager = event_manager
        self.connection_manager = connection_manager
        self._message_handlers: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger(f"{__name__}.MessageProcessor")

    def set_connection_manager(
        self, connection_manager: "WebSocketConnectionManager"
    ) -> None:
        """
        Set the connection manager reference.

        This method is used to set the ConnectionManager after initialization
        to avoid circular dependency issues during object construction.

        :param connection_manager: The WebSocketConnectionManager instance
        """
        self.connection_manager = connection_manager
        self.logger.debug("🔗 ConnectionManager reference set")

    def start_message_handler(
        self, device_id: str, websocket: WebSocketClientProtocol
    ) -> None:
        """Start message handling for a device"""
        if device_id not in self._message_handlers:
            self._message_handlers[device_id] = asyncio.create_task(
                self._handle_device_messages(device_id, websocket)
            )
            self.logger.debug(f"📨 Started message handler for device {device_id}")

    def stop_message_handler(self, device_id: str) -> None:
        """Stop message handling for a device"""
        if device_id in self._message_handlers:
            task = self._message_handlers[device_id]
            if not task.done():
                task.cancel()
            del self._message_handlers[device_id]
            self.logger.debug(f"📨 Stopped message handler for device {device_id}")

    async def _handle_device_messages(
        self, device_id: str, websocket: WebSocketClientProtocol
    ) -> None:
        """Handle incoming messages from a device"""
        message_count = 0
        try:
            async for message in websocket:
                message_count += 1

                self.logger.debug(
                    f"DeviceID: {device_id}, message count: {message_count}, message: {message}"
                )
                try:
                    server_msg = ServerMessage.model_validate_json(message)
                    asyncio.create_task(
                        self._process_server_message(device_id, server_msg)
                    )
                except json.JSONDecodeError as e:
                    self.logger.error(f"❌ Invalid JSON from device {device_id}: {e}")
                except Exception as e:
                    self.logger.error(
                        f"❌ Error processing message from device {device_id}: {e}"
                    )

        except websockets.ConnectionClosed as e:
            self.logger.warning(
                f"🔌 Connection to device {device_id} closed "
                f"(code: {e.code}, reason: {e.reason}, messages received: {message_count})"
            )
        except asyncio.CancelledError:
            self.logger.info(f"📨 Message handler for device {device_id} was cancelled")
            raise
        except Exception as e:
            self.logger.error(f"❌ Message handler error for device {device_id}: {e}")

    async def _process_server_message(
        self, device_id: str, server_msg: ServerMessage
    ) -> None:
        """Process a message received from the UFO server"""
        try:
            self.logger.debug(
                f"📨 Processing message type {server_msg.type} from device {device_id}"
            )
            start_time = asyncio.get_event_loop().time()

            if server_msg.type == ServerMessageType.TASK_END:
                await self._handle_task_completion(device_id, server_msg)
            elif server_msg.type == ServerMessageType.ERROR:
                await self._handle_error_message(device_id, server_msg)
            elif server_msg.type == ServerMessageType.HEARTBEAT:
                self.heartbeat_manager.handle_heartbeat_response(device_id)
            elif server_msg.type == ServerMessageType.COMMAND:
                await self._handle_command_message(device_id, server_msg)
            elif server_msg.type == ServerMessageType.DEVICE_INFO_RESPONSE:
                await self._handle_device_info_response(device_id, server_msg)
            else:
                self.logger.debug(
                    f"📋 Unhandled message type {server_msg.type} from device {device_id}"
                )

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > 0.5:  # 超过500ms就警告
                self.logger.warning(
                    f"⏱️ Slow message processing: {server_msg.type} took {elapsed:.2f}s"
                )

        except Exception as e:
            self.logger.error(
                f"❌ Error processing server message from device {device_id}: {e}"
            )

    async def _handle_task_completion(
        self, device_id: str, server_msg: ServerMessage
    ) -> None:
        """
        Handle task completion messages from UFO servers.

        This method performs two critical operations when a TASK_END message is received:
        1. Completes the pending task response Future in ConnectionManager (for synchronous waiting)
        2. Notifies event handlers via EventManager (for asynchronous callbacks)

        Workflow:
        - Extract task_id from server_msg (uses request_id or falls back to session_id)
        - Call ConnectionManager.complete_task_response() to unblock send_task_to_device()
        - Prepare result dictionary with task execution details
        - Notify EventManager to trigger registered callbacks

        :param device_id: Device that completed the task
        :param server_msg: ServerMessage containing task completion details

        Example ServerMessage:
            ServerMessage(
                type=ServerMessageType.TASK_END,
                request_id="task_12345",
                status=TaskStatus.COMPLETED,
                result={"output": "success"},
                ...
            )
        """
        try:
            # Prefer response_id over session_id for task identification
            # response_id corresponds to the request_id sent in ClientMessage
            # Fallback to session_id if response_id is not available
            session_id = server_msg.session_id
            task_id = session_id.split("@")[-1] if session_id else "unknown_task"

            # Step 1: Complete the pending task response Future
            # This unblocks the corresponding send_task_to_device() call
            if self.connection_manager:
                self.connection_manager.complete_task_response(session_id, server_msg)
                self.logger.debug(
                    f"🔄 Completed task response Future for task {task_id}"
                )
            else:
                self.logger.warning(
                    f"⚠️ ConnectionManager not set, cannot complete task response for {task_id}"
                )

            # Step 2: Prepare result data for event handlers
            result = {
                "success": server_msg.status == TaskStatus.COMPLETED,
                "device_id": device_id,
                "session_id": session_id,
                "task_id": task_id,
                "status": server_msg.status,
                "error": server_msg.error,
                "result": server_msg.result,
                "timestamp": server_msg.timestamp,
            }

            # Step 3: Notify event handlers (asynchronous callbacks)
            await self.event_manager.notify_task_completed(device_id, task_id, result)

            self.logger.info(
                f"✅ Task {task_id} completed on device {device_id} "
                f"(status: {server_msg.status})"
            )

        except Exception as e:
            self.logger.error(
                f"❌ Error handling task completion from device {device_id}: {e}",
                exc_info=True,
            )

    async def _handle_error_message(
        self, device_id: str, server_msg: ServerMessage
    ) -> None:
        """Handle error messages from the server"""
        error_text = getattr(server_msg, "error", "Unknown error")
        self.logger.error(f"❌ Error from device {device_id}: {error_text}")

        session_id = getattr(server_msg, "session_id", None)
        if session_id:
            # Notify event handlers about task failure
            await self.event_manager.notify_task_failed(
                device_id, session_id, error_text
            )

    async def _handle_command_message(
        self, device_id: str, server_msg: ServerMessage
    ) -> None:
        """Handle command messages from the server"""
        # For constellation clients, acknowledge and continue processing
        try:
            # Commands are typically handled by local clients, not constellation
            self.logger.debug(
                f"🔄 Received command from device {device_id}, delegating to local clients"
            )
        except Exception as e:
            self.logger.error(f"❌ Error handling command from device {device_id}: {e}")

    async def _handle_device_info_response(
        self, device_id: str, server_msg: ServerMessage
    ) -> None:
        """
        Handle device info response messages from the server.

        This method completes the pending device info request Future in ConnectionManager.

        :param device_id: Device that sent the response
        :param server_msg: ServerMessage containing device info
        """
        try:
            # Extract response_id (ServerMessage uses response_id, not request_id)
            request_id = server_msg.response_id

            if not request_id:
                self.logger.warning(
                    f"⚠️ Device info response from {device_id} missing response_id"
                )
                return

            # Extract device info from response
            device_info = None
            if server_msg.result and isinstance(server_msg.result, dict):
                if "error" not in server_msg.result:
                    device_info = server_msg.result
                else:
                    self.logger.warning(
                        f"⚠️ Device info request failed: {server_msg.result.get('error')}"
                    )

            # Complete the pending request Future
            if self.connection_manager:
                self.connection_manager.complete_device_info_response(
                    request_id, device_info
                )
                self.logger.debug(
                    f"🔄 Completed device info response Future for request {request_id}"
                )
            else:
                self.logger.warning(
                    f"⚠️ ConnectionManager not set, cannot complete device info response"
                )

        except Exception as e:
            self.logger.error(
                f"❌ Error handling device info response from {device_id}: {e}",
                exc_info=True,
            )

    async def _process_device_info_response(self, device_id: str, results: Any) -> None:
        """Process device information response"""
        try:
            if isinstance(results, dict):
                self.device_registry.set_device_capabilities(device_id, results)
                self.logger.info(f"📊 Updated device info for {device_id}")
        except Exception as e:
            self.logger.error(f"❌ Error processing device info for {device_id}: {e}")

    def stop_all_handlers(self) -> None:
        """Stop all message handlers"""
        for device_id in list(self._message_handlers.keys()):
            self.stop_message_handler(device_id)
