import asyncio
import logging
import uuid
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from aip.protocol.registration import RegistrationProtocol
from aip.protocol.heartbeat import HeartbeatProtocol
from aip.protocol.device_info import DeviceInfoProtocol
from aip.protocol.task_execution import TaskExecutionProtocol
from aip.transport.websocket import WebSocketTransport
from aip.messages import ClientMessage, ClientMessageType, ClientType, ServerMessage
from ufo.module.dispatcher import WebSocketCommandDispatcher
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.client_connection_manager import ClientConnectionManager


class UFOWebSocketHandler:
    """
    Handles WebSocket connections for the UFO server.
    Uses AIP (Agent Interaction Protocol) for structured message handling.
    """

    def __init__(
        self,
        client_manager: ClientConnectionManager,
        session_manager: SessionManager,
        local: bool = False,
    ):
        """
        Initializes the WebSocket handler.
        :param client_manager: The client connection manager.
        :param session_manager: The session manager.
        :param local: Whether running in local mode with client auto-connect.
        """
        self.client_manager = client_manager
        self.session_manager = session_manager
        self.local = local
        self.logger = logging.getLogger(self.__class__.__name__)

        # AIP protocol instances (will be initialized per connection)
        self.transport: Optional[WebSocketTransport] = None
        self.registration_protocol: Optional[RegistrationProtocol] = None
        self.heartbeat_protocol: Optional[HeartbeatProtocol] = None
        self.device_info_protocol: Optional[DeviceInfoProtocol] = None
        self.task_protocol: Optional[TaskExecutionProtocol] = None

    async def connect(self, websocket: WebSocket) -> str:
        """
        Connects a client and registers it in the client manager.
        Uses AIP RegistrationProtocol for structured registration.
        Expects the first message to contain {"client_id": ...}.
        :param websocket: The WebSocket connection.
        :return: The client_id.
        """
        await websocket.accept()

        # Initialize AIP protocols for this connection
        self.transport = WebSocketTransport(websocket)
        self.registration_protocol = RegistrationProtocol(self.transport)
        self.heartbeat_protocol = HeartbeatProtocol(self.transport)
        self.device_info_protocol = DeviceInfoProtocol(self.transport)
        self.task_protocol = TaskExecutionProtocol(self.transport)

        # Parse registration message using AIP protocol
        reg_info = await self._parse_registration_message()

        # Determine and validate client type
        client_type = reg_info.client_type

        platform = (
            reg_info.metadata.get("platform", "windows")
            if reg_info.metadata
            else "windows"
        )

        # Register client
        client_id = reg_info.client_id
        if client_type == ClientType.CONSTELLATION:
            await self._validate_constellation_client(reg_info)

        self.client_manager.add_client(
            client_id,
            platform,
            websocket,
            client_type,
            reg_info.metadata,
            transport=self.transport,
            task_protocol=self.task_protocol,
        )

        # Send registration confirmation using AIP protocol
        await self._send_registration_confirmation()

        # Log successful connection
        self._log_client_connection(client_id, client_type)

        return client_id

    async def _parse_registration_message(self) -> ClientMessage:
        """
        Parse and validate the registration message from client using AIP Transport.
        :return: Parsed registration message.
        :raises: ValueError if message is invalid.
        """
        self.logger.info("[WS] [AIP] Waiting for registration message...")
        # Receive registration message through AIP Transport
        reg_data = await self.transport.receive()
        if isinstance(reg_data, bytes):
            reg_data = reg_data.decode("utf-8")

        reg_info = ClientMessage.model_validate_json(reg_data)
        self.logger.info(
            f"[WS] [AIP] Received registration from {reg_info.client_id}, type={reg_info.client_type}"
        )

        if not reg_info.client_id:
            raise ValueError("Client ID is required for WebSocket registration")
        if reg_info.type != ClientMessageType.REGISTER:
            raise ValueError("First message must be a registration message")

        return reg_info

    async def _validate_constellation_client(self, reg_info: ClientMessage) -> None:
        """
        Validate constellation client's claimed device_id.
        Uses AIP to send error response and close transport if validation fails.

        :param reg_info: Registration message information.
        :raises: ValueError if validation fails.
        """
        claimed_device_id = reg_info.target_id

        if not claimed_device_id:
            return  # No device_id to validate

        if not self.client_manager.is_device_connected(claimed_device_id):
            error_msg = f"Target device '{claimed_device_id}' is not connected"
            self.logger.warning(f"[WS] Constellation registration failed: {error_msg}")

            # Send error via AIP and close connection
            await self._send_error_response(error_msg)
            await self.transport.close()
            raise ValueError(error_msg)

    async def _send_registration_confirmation(self) -> None:
        """
        Send successful registration confirmation to client using AIP RegistrationProtocol.
        """
        self.logger.info("[WS] [AIP] Sending registration confirmation...")
        await self.registration_protocol.send_registration_confirmation()
        self.logger.info("[WS] [AIP] Registration confirmation sent")

    async def _send_error_response(self, error_msg: str) -> None:
        """
        Send error response to client using AIP RegistrationProtocol.
        :param error_msg: Error message to send.
        """
        await self.registration_protocol.send_registration_error(error_msg)

    def _log_client_connection(self, client_id: str, client_type: ClientType) -> None:
        """
        Log successful client connection with appropriate emoji.
        :param client_id: The client ID.
        :param client_type: The client type.
        """
        if client_type == ClientType.CONSTELLATION:
            self.logger.info(f"[WS] 🌟 Constellation client {client_id} connected")
        else:
            # Log device connection with system info if available
            system_info = self.client_manager.get_device_system_info(client_id)
            if system_info:
                self.logger.info(
                    f"[WS] 📱 Device client {client_id} connected - "
                    f"Platform: {system_info.get('platform', 'unknown')}, "
                    f"CPU: {system_info.get('cpu_count', 'N/A')}, "
                    f"Memory: {system_info.get('memory_total_gb', 'N/A')}GB"
                )
            else:
                self.logger.info(f"[WS] 📱 Device client {client_id} connected")

    async def disconnect(self, client_id: str) -> None:
        """
        Disconnects a client and removes it from the WS manager.
        :param client_id: The ID of the client.
        """
        # Check if this is a constellation client with active sessions
        client_info = self.client_manager.get_client_info(client_id)

        if client_info and client_info.client_type == ClientType.CONSTELLATION:
            # Get all sessions associated with this constellation client
            session_ids = self.client_manager.get_constellation_sessions(client_id)

            if session_ids:
                self.logger.info(
                    f"[WS] 🌟 Constellation {client_id} disconnected, "
                    f"cancelling {len(session_ids)} active session(s)"
                )

            # Cancel all associated sessions
            for session_id in session_ids:
                try:
                    await self.session_manager.cancel_task(
                        session_id, reason="constellation_disconnected"
                    )
                except Exception as e:
                    self.logger.error(
                        f"[WS] Error cancelling session {session_id}: {e}"
                    )  # Clean up the mapping
                self.client_manager.remove_constellation_sessions(client_id)

        elif client_info and client_info.client_type == ClientType.DEVICE:
            # Get all sessions running on this device
            session_ids = self.client_manager.get_device_sessions(client_id)

            if session_ids:
                self.logger.info(
                    f"[WS] 📱 Device {client_id} disconnected, "
                    f"cancelling {len(session_ids)} active session(s)"
                )

            # Cancel all sessions running on this device
            for session_id in session_ids:
                try:
                    await self.session_manager.cancel_task(
                        session_id, reason="device_disconnected"
                    )
                except Exception as e:
                    self.logger.error(
                        f"[WS] Error cancelling session {session_id}: {e}"
                    )  # Clean up the mapping
                self.client_manager.remove_device_sessions(client_id)

        self.client_manager.remove_client(client_id)
        self.logger.info(f"[WS] {client_id} disconnected")

    async def handler(self, websocket: WebSocket) -> None:
        """
        FastAPI WebSocket entry point.
        :param websocket: The WebSocket connection.
        """
        client_id = None

        try:
            client_id = await self.connect(websocket)
            while True:
                msg = await websocket.receive_text()
                asyncio.create_task(self.handle_message(msg))
        except WebSocketDisconnect as e:
            self.logger.warning(
                f"[WS] {client_id} disconnected - code={e.code}, reason={e.reason}"
            )
            if client_id:
                await self.disconnect(client_id)
        except Exception as e:
            self.logger.error(f"[WS] Error with client {client_id}: {e}")
            if client_id:
                await self.disconnect(client_id)

    async def handle_message(self, msg: str) -> None:
        """
        Dispatch incoming WS messages to specific handlers.
        :param msg: The message received from the client.
        :param client_type: The type of client ("device" or "constellation").
        """
        import traceback

        try:
            data = ClientMessage.model_validate_json(msg)

            client_id = data.client_id
            client_type = data.client_type

            # Log message with client type context
            if client_type == ClientType.CONSTELLATION:
                self.logger.debug(
                    f"[WS] 🌟 Handling constellation message from {client_id}, type: {data.type}"
                )
            else:
                self.logger.debug(
                    f"[WS] 📱 Received device message from {client_id}, type: {data.type}"
                )

            msg_type = data.type

            if msg_type == ClientMessageType.TASK:
                await self.handle_task_request(data)
            elif msg_type == ClientMessageType.COMMAND_RESULTS:
                await self.handle_command_result(data)
            elif msg_type == ClientMessageType.HEARTBEAT:
                await self.handle_heartbeat(data)
            elif msg_type == ClientMessageType.ERROR:
                await self.handle_error(data)
            elif msg_type == ClientMessageType.DEVICE_INFO_REQUEST:
                # Constellation requesting device info
                await self.handle_device_info_request(data)
            elif msg_type == ClientMessageType.DEVICE_INFO_RESPONSE:
                # Reserved for future Pull model where device pushes info on request
                await self.handle_device_info_response(data)
            else:
                await self.handle_unknown(data)
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"[WS] Error handling message from {client_id}: {e}")

            # Try to send error, but don't fail if connection is closed
            try:
                await self.task_protocol.send_error(str(e))
            except (ConnectionError, IOError) as send_error:
                self.logger.debug(
                    f"[WS] Could not send error response (connection closed): {send_error}"
                )

    async def handle_heartbeat(self, data: ClientMessage) -> None:
        """
        Handle heartbeat messages from the client using AIP HeartbeatProtocol.
        :param data: The data from the client.
        """
        self.logger.debug(f"[WS] [AIP] Heartbeat from {data.client_id}")
        # Use AIP heartbeat protocol to send acknowledgment (server-side)
        try:
            await self.heartbeat_protocol.send_heartbeat_ack()
            self.logger.debug(f"[WS] [AIP] Heartbeat response sent to {data.client_id}")
        except (ConnectionError, IOError) as e:
            self.logger.debug(
                f"[WS] [AIP] Could not send heartbeat ack (connection closed): {e}"
            )

    async def handle_error(self, data: ClientMessage) -> None:
        """
        Handle error messages from the client.
        :param data: The data from the client.
        """
        self.logger.error(f"[WS] [AIP] Error from {data.client_id}: {data.error}")
        # Send error acknowledgment
        await self.task_protocol.send_error(data.error or "Unknown error")

    async def handle_unknown(self, data: ClientMessage) -> None:
        """
        Handle unknown message types.
        :param data: The data from the client.
        """
        self.logger.warning(f"[WS] [AIP] Unknown message type: {data.type}")
        await self.task_protocol.send_error(f"Unknown message type: {data.type}")

    async def handle_task_request(self, data: ClientMessage) -> None:
        """
        Handle a task request message from the client.

        This method now delegates session execution to SessionManager,
        which runs tasks in background without blocking the event loop.
        This allows WebSocket ping/pong and heartbeat messages to continue.

        Uses AIP protocols for all communication, no direct WebSocket access needed.

        :param data: The data from the client.
        """
        client_type = data.client_type
        client_id = data.client_id
        target_device_id = None  # Track for debugging

        if client_type == ClientType.CONSTELLATION:
            target_device_id = data.target_id
            self.logger.info(
                f"[WS] 🌟 Handling constellation task request: {data.request} from {data.target_id}"
            )
            platform = self.client_manager.get_client_info(data.target_id).platform
        else:
            self.logger.info(
                f"[WS] 📱 Handling device task request: {data.request} from {data.client_id}"
            )
            platform = self.client_manager.get_client_info(data.client_id).platform

        session_id = str(uuid.uuid4()) if not data.session_id else data.session_id
        task_name = data.task_name if data.task_name else str(uuid.uuid4())

        self.logger.info(
            f"[WS] 🎯 Prepared task: session_id={session_id}, task_name={task_name}, "
            f"client_type={client_type}, target_device={target_device_id}"
        )

        # Track constellation session mapping
        if client_type == ClientType.CONSTELLATION:
            self.client_manager.add_constellation_session(data.client_id, session_id)
            # Also track on target device
            if target_device_id:
                self.client_manager.add_device_session(target_device_id, session_id)

        # Define callback to send results when task completes
        async def send_result(sid: str, result_msg: ServerMessage):
            """Send task result to client when session completes using AIP."""
            self.logger.info(
                f"[WS] 📬 CALLBACK INVOKED! session={sid}, status={result_msg.status}, "
                f"client_type={client_type}, target_device={target_device_id}"
            )

            # Get task protocol for the requesting client
            requester_protocol = self.client_manager.get_task_protocol(client_id)

            if not requester_protocol:
                self.logger.warning(
                    f"[WS] ⚠️ Client {client_id} disconnected, "
                    f"skipping result callback for session {sid}"
                )
                return

            try:
                # Send to requesting client (constellation or device) using AIP
                self.logger.info(
                    f"[WS] 📤 Sending result to client {client_id} via AIP..."
                )

                # Use AIP TaskExecutionProtocol.send_task_end()
                await requester_protocol.send_task_end(
                    session_id=sid,
                    status=result_msg.status,
                    result=result_msg.result,
                    error=result_msg.error,
                    response_id=result_msg.response_id,
                )
                self.logger.info(f"[WS] ✅ Sent to client {client_id} successfully")

                # If constellation client, also notify the target device
                if client_type == ClientType.CONSTELLATION and target_device_id:
                    target_protocol = self.client_manager.get_task_protocol(
                        target_device_id
                    )

                    if target_protocol:
                        self.logger.info(
                            f"[WS] 📤 Sending result to target device {target_device_id} via AIP..."
                        )
                        try:
                            await target_protocol.send_task_end(
                                session_id=sid,
                                status=result_msg.status,
                                result=result_msg.result,
                                error=result_msg.error,
                                response_id=result_msg.response_id,
                            )
                            self.logger.info(
                                f"[WS] ✅ Sent to target device {target_device_id} successfully"
                            )
                        except (ConnectionError, IOError) as target_error:
                            self.logger.warning(
                                f"[WS] ⚠️ Target device {target_device_id} disconnected: {target_error}"
                            )
                    else:
                        self.logger.warning(
                            f"[WS] ⚠️ Target device {target_device_id} disconnected, skipping send"
                        )

                self.logger.info(f"[WS] ✅ All results sent for session {sid}")
            except (ConnectionError, IOError) as e:
                self.logger.warning(
                    f"[WS] ⚠️ Connection error sending result for {sid}: {e}"
                )
            except Exception as e:
                import traceback

                self.logger.error(
                    f"[WS] ❌ Failed to send result for {sid}: {e}\n{traceback.format_exc()}"
                )

        self.logger.info(
            f"[WS] 🎯 About to call execute_task_async for session {session_id}"
        )

        # Get task protocol for target device
        target_protocol = self.client_manager.get_task_protocol(
            target_device_id if client_type == ClientType.CONSTELLATION else client_id
        )

        # Start task in background (non-blocking)
        await self.session_manager.execute_task_async(
            session_id=session_id,
            task_name=task_name,
            request=data.request,
            task_protocol=target_protocol,
            platform_override=platform,
            callback=send_result,
        )

        self.logger.info(
            f"[WS] 🎯 execute_task_async returned for session {session_id}"
        )

        # Send immediate acknowledgment that task was accepted
        await self.task_protocol.send_ack(session_id=session_id)

        self.logger.info(
            f"[WS] 📝 Task {session_id} accepted and running in background"
        )

    async def handle_command_result(self, data: ClientMessage) -> None:
        """
        Handle the result of commands. Run in background.
        :param data: The data from the client.
        """

        self.logger.debug(f"[WS] Handling command result: {data.action_results}")

        response_id = data.prev_response_id
        session_id = data.session_id
        session = self.session_manager.get_or_create_session(
            session_id, local=self.local
        )

        command_dispatcher: WebSocketCommandDispatcher = (
            session.context.command_dispatcher
        )

        await command_dispatcher.set_result(response_id, data)

    async def handle_device_info_response(self, data: ClientMessage) -> None:
        """
        Handle device info response (reserved for future Pull model).
        :param data: The data from the client.
        """
        self.logger.info(
            f"[WS] Received device info response from {data.client_id} (not implemented)"
        )

    async def handle_device_info_request(self, data: ClientMessage) -> None:
        """
        Handle device info request from constellation client using AIP DeviceInfoProtocol.

        :param data: The request data from constellation.
        """
        device_id = data.target_id
        request_id = data.request_id

        self.logger.info(
            f"[WS] [AIP] 🌟 Constellation requesting device info for {device_id}"
        )

        # Get device info from WSManager
        device_info = await self.get_device_info(device_id)

        # Use AIP DeviceInfoProtocol to send response
        await self.device_info_protocol.send_device_info_response(
            device_info=device_info, request_id=request_id
        )

        self.logger.info(
            f"[WS] [AIP] 📤 Sent device info response for {device_id} to constellation"
        )

    async def get_device_info(self, device_id: str) -> dict:
        """
        Get device system information for a specific device.
        This is called by constellation clients via WebSocket.

        :param device_id: The device ID to get information for.
        :return: Device system information dictionary.
        """
        device_info = self.client_manager.get_device_system_info(device_id)
        if device_info:
            return device_info
        else:
            return {
                "error": f"Device {device_id} not found or no system info available"
            }
