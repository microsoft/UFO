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
import websockets

from aip.messages import ServerMessage, ServerMessageType, TaskStatus
from .device_registry import DeviceRegistry
from .heartbeat_manager import HeartbeatManager

# Avoid circular import
if TYPE_CHECKING:
    from .connection_manager import WebSocketConnectionManager
    from aip.transport.websocket import WebSocketTransport


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
        connection_manager: Optional["WebSocketConnectionManager"] = None,
    ):
        """
        Initialize the MessageProcessor.

        :param device_registry: Registry for tracking connected devices
        :param heartbeat_manager: Manager for device heartbeat monitoring
        :param connection_manager: Optional ConnectionManager for completing task responses
                                  (set later via set_connection_manager to avoid circular dependency)
        """
        self.device_registry = device_registry
        self.heartbeat_manager = heartbeat_manager
        self.connection_manager = connection_manager
        self._message_handlers: Dict[str, asyncio.Task] = {}
        # Callback for handling disconnections (set by DeviceManager)

        self._disconnection_handler: Optional[callable] = None
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

    def set_disconnection_handler(self, handler: callable) -> None:
        """
        Set the disconnection handler callback.

        This method allows DeviceManager to register a callback that will be
        invoked when a device disconnects, enabling proper cleanup and reconnection.

        :param handler: Async function to call on disconnection (device_id: str) -> None
        """
        self._disconnection_handler = handler
        self.logger.debug("🔗 Disconnection handler set")

    def start_message_handler(
        self, device_id: str, transport: "WebSocketTransport"
    ) -> None:
        """
        Start message handling for a device.

        Creates an asyncio task to listen for incoming messages from the device's
        AIP Transport connection. This task will run until the connection is closed
        or the handler is explicitly stopped.

        :param device_id: Unique device identifier
        :param transport: AIP Transport for the device connection
        """
        if device_id not in self._message_handlers:
            self._message_handlers[device_id] = asyncio.create_task(
                self._handle_device_messages(device_id, transport)
            )
            self.logger.debug(f"📨 Started message handler for device {device_id}")

    def stop_message_handler(self, device_id: str) -> None:
        """
        Stop message handling for a device.

        Cancels the asyncio task that is listening for messages from the device.
        This is called when manually disconnecting from a device or during cleanup.

        :param device_id: Unique device identifier
        """
        if device_id in self._message_handlers:
            task = self._message_handlers[device_id]
            if not task.done():
                task.cancel()
            del self._message_handlers[device_id]
            self.logger.debug(f"📨 Stopped message handler for device {device_id}")

    async def _handle_device_messages(
        self, device_id: str, transport: "WebSocketTransport"
    ) -> None:
        """
        Handle incoming messages from a device.

        This is the main message processing loop that listens for messages
        from a device via AIP Transport. It validates and routes each message to
        the appropriate handler based on message type. The loop continues until
        the connection is closed or an error occurs.

        Handles the following scenarios:
        - Normal message processing: Routes to _process_server_message()
        - ConnectionClosed: Triggers disconnection cleanup and reconnection
        - CancelledError: Gracefully stops when handler is explicitly stopped
        - Other exceptions: Logs error and triggers disconnection cleanup

        :param device_id: Unique device identifier
        :param transport: AIP Transport to listen on
        """
        message_count = 0
        try:
            # Use Transport.receive() instead of async for websocket
            while transport.is_connected:
                try:
                    message_bytes = await transport.receive()
                    message = message_bytes.decode("utf-8")
                    message_count += 1

                    self.logger.debug(
                        f"DeviceID: {device_id}, message count: {message_count}, message: {message}"
                    )

                    server_msg = ServerMessage.model_validate_json(message)
                    asyncio.create_task(
                        self._process_server_message(device_id, server_msg)
                    )
                except (
                    ConnectionError,
                    websockets.ConnectionClosed,
                    websockets.WebSocketException,
                    OSError,
                ):
                    # Re-raise connection-related exceptions to outer handler
                    raise
                except json.JSONDecodeError as e:
                    self.logger.error(
                        f"❌ Invalid JSON from device {device_id}: {e}", exc_info=True
                    )
                except ValueError as e:
                    self.logger.error(
                        f"❌ Invalid message format from device {device_id}: {e}",
                        exc_info=True,
                    )
                except TypeError as e:
                    self.logger.error(
                        f"❌ Type error processing message from device {device_id}: {e}",
                        exc_info=True,
                    )
                except Exception as e:
                    self.logger.error(
                        f"❌ Unexpected error processing message from device {device_id}: {e}",
                        exc_info=True,
                    )

        except ConnectionError as e:
            # Handle ConnectionError raised by transport layer
            self.logger.warning(
                f"🔌 Connection to device {device_id} closed: {e} (messages received: {message_count})"
            )
            # Trigger disconnection handler for cleanup and reconnection
            await self._handle_disconnection(device_id)
        except websockets.ConnectionClosed as e:
            self.logger.warning(
                f"🔌 Connection to device {device_id} closed "
                f"(code: {e.code}, reason: {e.reason}, messages received: {message_count})"
            )
            # Trigger disconnection handler for cleanup and reconnection
            await self._handle_disconnection(device_id)
        except asyncio.CancelledError:
            self.logger.info(f"📨 Message handler for device {device_id} was cancelled")
            raise
        except websockets.WebSocketException as e:
            self.logger.warning(f"⚠️ WebSocket error for device {device_id}: {e}")
            await self._handle_disconnection(device_id)
        except OSError as e:
            self.logger.warning(f"⚠️ Network error for device {device_id}: {e}")
            await self._handle_disconnection(device_id)
        except Exception as e:
            self.logger.error(
                f"❌ Unexpected message handler error for device {device_id}: {e}"
            )
            # Trigger disconnection handler for unexpected errors
            await self._handle_disconnection(device_id)

    async def _process_server_message(
        self, device_id: str, server_msg: ServerMessage
    ) -> None:
        """
        Process a message received from the UFO server.

        Routes incoming ServerMessage to the appropriate handler based on message type:
        - TASK_END: Task completion (delegates to _handle_task_completion)
        - ERROR: Error messages (delegates to _handle_error_message)
        - HEARTBEAT: Heartbeat responses (updates heartbeat manager)
        - COMMAND: Command messages (delegates to _handle_command_message)
        - DEVICE_INFO_RESPONSE: Device info responses (delegates to _handle_device_info_response)

        Also tracks message processing time and logs warnings for slow processing.

        :param device_id: Device that sent the message
        :param server_msg: Parsed ServerMessage object
        """
        try:
            self.logger.debug(
                f"📨 Processing message type {server_msg.type} from device {device_id}"
            )
            start_time = asyncio.get_event_loop().time()

            if server_msg.type == ServerMessageType.TASK_END:
                await self._handle_task_completion(device_id, server_msg)
            elif server_msg.type == ServerMessageType.ERROR:
                # Check if this is a registration error response
                self.connection_manager.complete_registration_response(
                    device_id, success=False, error_message=server_msg.error
                )
                await self._handle_error_message(device_id, server_msg)
            elif server_msg.type == ServerMessageType.HEARTBEAT:
                # Check if this is a registration success response
                # (server sends HEARTBEAT with status=OK to confirm registration)
                if server_msg.status == TaskStatus.OK:
                    self.connection_manager.complete_registration_response(
                        device_id, success=True
                    )
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
            if elapsed > 0.5:  # Warn if processing takes more than 500ms
                self.logger.warning(
                    f"⏱️ Slow message processing: {server_msg.type} took {elapsed:.2f}s"
                )

        except KeyError as e:
            self.logger.error(
                f"❌ Missing required field in message from device {device_id}: {e}",
                exc_info=True,
            )
        except AttributeError as e:
            self.logger.error(
                f"❌ Invalid message structure from device {device_id}: {e}",
                exc_info=True,
            )
        except Exception as e:
            self.logger.error(
                f"❌ Unexpected error processing server message from device {device_id}: {e}",
                exc_info=True,
            )

    async def _handle_task_completion(
        self, device_id: str, server_msg: ServerMessage
    ) -> None:
        """
        Handle task completion messages from UFO servers.

        This method completes the pending task response Future in ConnectionManager
        to unblock send_task_to_device() calls waiting for task results.

        Workflow:
        - Extract task_id from server_msg (uses request_id or falls back to session_id)
        - Call ConnectionManager.complete_task_response() to unblock send_task_to_device()
        - Prepare result dictionary with task execution details

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
        """
        Handle error messages from the server.

        Processes ERROR type messages from the UFO server. Logs the error and
        notifies event handlers about task failures if a session_id is present.

        :param device_id: Device that sent the error
        :param server_msg: ServerMessage containing error details
        """
        error_text = getattr(server_msg, "error", "Unknown error")
        self.logger.error(f"❌ Error from device {device_id}: {error_text}")

    async def _handle_command_message(
        self, device_id: str, server_msg: ServerMessage
    ) -> None:
        """
        Handle command messages from the server.

        Processes COMMAND type messages from the UFO server. In constellation mode,
        commands are typically handled by local clients rather than the constellation
        itself, so this method primarily logs and acknowledges the command.

        :param device_id: Device that sent the command
        :param server_msg: ServerMessage containing command details
        """
        # For constellation clients, acknowledge and continue processing
        try:
            # Commands are typically handled by local clients, not constellation
            self.logger.debug(
                f"🔄 Received command from device {device_id}, delegating to local clients"
            )
        except KeyError as e:
            self.logger.error(
                f"❌ Missing command field from device {device_id}: {e}", exc_info=True
            )
        except Exception as e:
            self.logger.error(
                f"❌ Unexpected error handling command from device {device_id}: {e}",
                exc_info=True,
            )

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
        """
        Process device information response.

        Updates the device registry with capabilities and system information
        received from the device. This is a legacy method that updates the
        registry directly, while _handle_device_info_response completes the
        async Future for request-response pattern.

        :param device_id: Device that provided the information
        :param results: Device information dictionary
        """
        try:
            if isinstance(results, dict):
                self.device_registry.set_device_capabilities(device_id, results)
                self.logger.info(f"📊 Updated device info for {device_id}")
        except KeyError as e:
            self.logger.error(
                f"❌ Missing required device info field for {device_id}: {e}",
                exc_info=True,
            )
        except TypeError as e:
            self.logger.error(
                f"❌ Invalid device info data type for {device_id}: {e}", exc_info=True
            )
        except Exception as e:
            self.logger.error(
                f"❌ Unexpected error processing device info for {device_id}: {e}",
                exc_info=True,
            )

    async def _handle_disconnection(self, device_id: str) -> None:
        """
        Handle device disconnection cleanup and trigger reconnection.

        This method is called when a device disconnects (either due to connection
        closed or unexpected error). It performs cleanup and delegates to the
        DeviceManager's disconnection handler for reconnection logic.

        :param device_id: Device that disconnected
        """
        try:
            self.logger.info(f"🔌 Handling disconnection for device {device_id}")

            # Stop heartbeat monitoring
            self.heartbeat_manager.stop_heartbeat(device_id)

            # Trigger the DeviceManager's disconnection handler if set
            if self._disconnection_handler:
                await self._disconnection_handler(device_id)
            else:
                self.logger.warning(
                    f"⚠️ No disconnection handler set for device {device_id}"
                )

        except Exception as e:
            self.logger.error(
                f"❌ Error handling disconnection for device {device_id}: {e}",
                exc_info=True,
            )

    def stop_all_handlers(self) -> None:
        """
        Stop all message handlers.

        Cancels all active message processing tasks. This is typically called
        during shutdown to ensure all background tasks are properly cleaned up.
        """
        for device_id in list(self._message_handlers.keys()):
            self.stop_message_handler(device_id)
