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
from ufo.server.services.client_connection_manager import (
    ClientConnectionManager,
    DuplicateClientError,
)
from ufo.utils import sanitize_task_name


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

        try:
            self.client_manager.add_client(
                client_id,
                platform,
                websocket,
                client_type,
                reg_info.metadata,
                transport=self.transport,
                task_protocol=self.task_protocol,
            )
        except DuplicateClientError as dup_err:
            # Refuse the new registration. The existing connection
            # remains untouched: its stored websocket, role and task
            # protocol are not overwritten. This blocks the duplicate
            # ``client_id`` registry-overwrite vector.
            self.logger.warning(
                f"[WS] 🚨 duplicate client_id rejected: {dup_err}"
            )
            await self._send_error_response(str(dup_err))
            try:
                await self.transport.close()
            except Exception:  # noqa: BLE001
                pass
            raise ValueError(str(dup_err)) from dup_err

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
            # Capture the role/identity that the server bound to this
            # connection during registration. Subsequent messages on this
            # connection are pinned to these values to prevent the client
            # from claiming a different ``client_id`` or ``client_type``
            # (role) at the message layer.
            registered_client_type = self.client_manager.get_client_type(client_id)
            while True:
                msg = await websocket.receive_text()
                asyncio.create_task(
                    self.handle_message(
                        msg,
                        registered_client_id=client_id,
                        registered_client_type=registered_client_type,
                    )
                )
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

    async def handle_message(
        self,
        msg: str,
        registered_client_id: Optional[str] = None,
        registered_client_type: Optional[ClientType] = None,
    ) -> None:
        """
        Dispatch incoming WS messages to specific handlers.

        Security: the per-connection identity established at registration
        (``registered_client_id`` and ``registered_client_type``) is the
        authoritative source of truth for the connection's role and
        principal. The values carried in ``ClientMessage`` are validated
        against the registered identity to defeat role/identity spoofing:
        a connection that registered as a ``DEVICE`` cannot later send
        messages claiming to be a ``CONSTELLATION`` (or impersonate a
        different ``client_id``).

        :param msg: The raw JSON message received from the client.
        :param registered_client_id: The ``client_id`` that the server
            bound to this connection at registration. ``None`` means
            the message did not originate from a registered connection
            (e.g. in unit tests) — in that case, privileged operations
            are refused.
        :param registered_client_type: The ``client_type`` (role) that
            the server bound to this connection at registration.
        """
        import traceback

        client_id = registered_client_id

        try:
            data = ClientMessage.model_validate_json(msg)

            # ---------- Authoritative identity/role binding ----------
            # Reject any message that does not match the identity that
            # was bound to this connection during registration. This is
            # the defense against the role/identity spoofing PoC where
            # a connection registered as ``DEVICE`` later sends a
            # ``TASK`` message claiming ``client_type=CONSTELLATION``
            # and ``target_id=<victim-device-id>``.
            if registered_client_id is not None:
                if data.client_id and data.client_id != registered_client_id:
                    self.logger.warning(
                        "[WS] 🚨 client_id spoof rejected: connection "
                        f"registered as {registered_client_id!r} but "
                        f"message claimed client_id={data.client_id!r}"
                    )
                    await self._safe_send_error(
                        "client_id does not match the registered connection"
                    )
                    return

                if (
                    registered_client_type is not None
                    and data.client_type != registered_client_type
                ):
                    self.logger.warning(
                        "[WS] 🚨 client_type/role spoof rejected: "
                        f"connection registered as {registered_client_type} "
                        f"but message claimed client_type={data.client_type}"
                    )
                    await self._safe_send_error(
                        "client_type does not match the registered connection"
                    )
                    return

                # Overwrite the wire-supplied fields with the server-bound
                # values so downstream handlers can never accidentally
                # consume the (potentially attacker-controlled) values
                # from the message body.
                data.client_id = registered_client_id
                if registered_client_type is not None:
                    data.client_type = registered_client_type
            else:
                # No registered connection identity is available. This
                # path is reachable only when ``handle_message`` is
                # invoked outside of the normal WebSocket loop (for
                # example in unit tests, or via a future code path).
                # We must refuse any operation that depends on the
                # caller's identity or role.
                if data.type in (
                    ClientMessageType.TASK,
                    ClientMessageType.COMMAND_RESULTS,
                    ClientMessageType.DEVICE_INFO_REQUEST,
                    ClientMessageType.REGISTER,
                ):
                    self.logger.warning(
                        "[WS] 🚨 refusing privileged message of type "
                        f"{data.type} on a connection with no bound "
                        "identity (possible identity spoof attempt)"
                    )
                    await self._safe_send_error(
                        "Connection is not registered; refusing privileged message"
                    )
                    return

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
            await self._safe_send_error(str(e))

    async def _safe_send_error(self, error: str) -> None:
        """
        Best-effort send of an error response to the current connection.

        Used by the message validator and the dispatch error handler.
        Swallows transport-level failures (closed connection) and the
        case where the per-connection task protocol has not been
        established yet (e.g. tests that exercise ``handle_message``
        without going through ``connect``).
        """
        try:
            if self.task_protocol is not None:
                await self.task_protocol.send_error(error)
        except (ConnectionError, IOError) as send_error:
            self.logger.debug(
                f"[WS] Could not send error response (connection closed): {send_error}"
            )
        except Exception as send_error:  # noqa: BLE001
            self.logger.debug(
                f"[WS] Suppressed error while sending error response: {send_error}"
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

        Security: ``data.client_id`` and ``data.client_type`` are expected
        to have been pinned to the registered connection identity by
        :meth:`handle_message`. As an additional defense-in-depth check,
        a ``DEVICE`` client is not permitted to set ``target_id`` to
        anything other than its own ``client_id``.

        :param data: The data from the client.
        """
        client_type = data.client_type
        client_id = data.client_id
        target_device_id = None  # Track for debugging

        if client_type == ClientType.CONSTELLATION:
            target_device_id = data.target_id
            if not target_device_id:
                self.logger.warning(
                    f"[WS] 🌟 Constellation {client_id} sent task without target_id"
                )
                await self._safe_send_error(
                    "Constellation task requests require target_id"
                )
                return

            target_info = self.client_manager.get_client_info(target_device_id)
            if target_info is None:
                self.logger.warning(
                    f"[WS] 🌟 Constellation {client_id} targeted unknown "
                    f"device {target_device_id!r}"
                )
                await self._safe_send_error(
                    f"Target device {target_device_id!r} is not connected"
                )
                return
            if target_info.client_type != ClientType.DEVICE:
                self.logger.warning(
                    f"[WS] 🌟 Constellation {client_id} targeted non-device "
                    f"client {target_device_id!r}"
                )
                await self._safe_send_error(
                    "Constellation tasks may only target device clients"
                )
                return

            self.logger.info(
                f"[WS] 🌟 Handling constellation task request: {data.request} from {data.target_id}"
            )
            platform = target_info.platform
        else:
            # Devices may only run tasks against themselves. Reject any
            # attempt to set ``target_id`` to a different ``client_id``;
            # combined with the connection-bound role enforced in
            # :meth:`handle_message`, this prevents a device-scoped
            # connection from steering tasks toward peer devices.
            if data.target_id and data.target_id != client_id:
                self.logger.warning(
                    f"[WS] 🚨 device {client_id} attempted to target peer "
                    f"device {data.target_id!r}; rejecting task request"
                )
                await self._safe_send_error(
                    "Device clients may not target other devices"
                )
                return

            device_info = self.client_manager.get_client_info(client_id)
            if device_info is None:
                self.logger.warning(
                    f"[WS] 📱 Task request from unknown device {client_id!r}"
                )
                await self._safe_send_error(
                    f"Device {client_id!r} is not connected"
                )
                return

            self.logger.info(
                f"[WS] 📱 Handling device task request: {data.request} from {data.client_id}"
            )
            platform = device_info.platform

        session_id = str(uuid.uuid4()) if not data.session_id else data.session_id
        # ``task_name`` is attacker-controllable and is later used as a
        # filesystem path component for the session log directory. Sanitize
        # it here so traversal sequences (e.g. ``../escape``) cannot leak
        # into downstream consumers or echo back unmodified.
        raw_task_name = data.task_name if data.task_name else str(uuid.uuid4())
        task_name = sanitize_task_name(raw_task_name)
        if raw_task_name != task_name:
            self.logger.warning(
                f"[WS] Sanitized unsafe task_name {raw_task_name!r} -> {task_name!r}"
            )

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
