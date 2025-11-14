import asyncio
import datetime
import logging
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

import websockets
from websockets import WebSocketClientProtocol

from aip.protocol.registration import RegistrationProtocol
from aip.protocol.heartbeat import HeartbeatProtocol
from aip.protocol.task_execution import TaskExecutionProtocol
from aip.transport.websocket import WebSocketTransport
from aip.messages import (
    ClientMessage,
    ClientMessageType,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)

if TYPE_CHECKING:
    from ufo.client.ufo_client import UFOClient


class UFOWebSocketClient:
    """
    WebSocket client compatible with FastAPI UFO server.
    Uses AIP (Agent Interaction Protocol) for structured message handling.
    Handles task_request, heartbeat, result_ack, notify_ack.
    """

    def __init__(
        self,
        ws_url: str,
        ufo_client: "UFOClient",
        max_retries: int = 3,
        timeout: float = 120,
    ):
        """
        Initialize the WebSocket client.
        :param ws_url: WebSocket server URL
        :param ufo_client: Instance of UFOClient
        :param max_retries: Maximum number of connection retries
        :param timeout: Connection timeout in seconds
        """
        self.ws_url = ws_url
        self.ufo_client = ufo_client
        self.max_retries = max_retries
        self.retry_count = 0
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_task: Optional[asyncio.Task] = None
        self.session_id: Optional[str] = None
        self._ws: Optional[WebSocketClientProtocol] = None

        self.connected_event = asyncio.Event()

        # AIP protocol instances (will be initialized on connection)
        self.transport: Optional[WebSocketTransport] = None
        self.registration_protocol: Optional[RegistrationProtocol] = None
        self.heartbeat_protocol: Optional[HeartbeatProtocol] = None
        self.task_protocol: Optional[TaskExecutionProtocol] = None

    async def connect_and_listen(self):
        """
        Connect to the FastAPI WebSocket server and listen for incoming messages.
        Automatically retries on failure.
        """
        while True:  # Infinite loop - retry logic is in _maybe_retry
            try:
                # Check retry limit before attempting connection
                if self.retry_count >= self.max_retries:
                    self.logger.error(
                        f"[WS] ❌ Max retries ({self.max_retries}) reached. Exiting."
                    )
                    break

                # Only log on first attempt or after failures
                if self.retry_count == 0:
                    self.logger.info(f"[WS] Connecting to {self.ws_url}...")
                else:
                    self.logger.info(
                        f"[WS] Reconnecting... (attempt {self.retry_count + 1}/{self.max_retries})"
                    )

                # Reset connection state before attempting to connect
                self.connected_event.clear()
                self._ws = None

                async with websockets.connect(
                    self.ws_url,
                    ping_interval=20,  # Reduced to 20s for more frequent keepalive
                    ping_timeout=180,  # Increased to 180s (3 minutes) to handle long-running operations
                    close_timeout=10,
                    max_size=100 * 1024 * 1024,
                ) as ws:
                    self._ws = ws

                    # Initialize AIP protocols for this connection
                    self.transport = WebSocketTransport(ws)
                    self.registration_protocol = RegistrationProtocol(self.transport)
                    self.heartbeat_protocol = HeartbeatProtocol(self.transport)
                    self.task_protocol = TaskExecutionProtocol(self.transport)

                    await self.register_client()
                    self.retry_count = 0  # Reset retry count on successful connection
                    await self.handle_messages()

            except (
                websockets.ConnectionClosed,  # Base class for all connection closed exceptions
                websockets.ConnectionClosedError,
                websockets.ConnectionClosedOK,
            ) as e:
                self.logger.warning(f"[WS] Connection closed: {e}. Will retry.")
                self.connected_event.clear()
                self.retry_count += 1
                await self._maybe_retry()
                # Loop continues automatically

            except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                self.logger.warning(
                    f"[WS] Connection timeout/cancelled: {e}. Will retry."
                )
                self.connected_event.clear()
                self.retry_count += 1
                await self._maybe_retry()
                # Loop continues automatically

            except ConnectionRefusedError as e:
                # Common error - don't show full traceback
                self.logger.warning(
                    f"[WS] Connection refused: Server not available at {self.ws_url}"
                )
                self.connected_event.clear()
                self.retry_count += 1
                await self._maybe_retry()
                # Loop continues automatically

            except Exception as e:
                # Show error type and message without full traceback for connection errors
                error_type = type(e).__name__
                self.logger.warning(f"[WS] Connection error ({error_type}): {e}")
                self.connected_event.clear()
                self.retry_count += 1
                await self._maybe_retry()
                # Loop continues automatically

    async def register_client(self):
        """
        Send client_id and device system information to server upon connection.
        Uses AIP RegistrationProtocol for structured registration.
        This implements the Push model where device info is sent during registration.
        """
        from ufo.client.device_info_provider import DeviceInfoProvider

        # Collect device system information (no custom metadata from device side)
        try:
            system_info = DeviceInfoProvider.collect_system_info(
                self.ufo_client.client_id,
                custom_metadata=None,  # Server will add custom metadata if configured
            )

            # Prepare metadata with system info
            metadata = {
                "system_info": system_info.to_dict(),
                "registration_time": datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat(),
            }

            self.logger.info(
                f"[WS] [AIP] Collected device info: platform={system_info.platform}, "
                f"cpu={system_info.cpu_count}, memory={system_info.memory_total_gb}GB"
            )

        except Exception as e:
            self.logger.error(
                f"[WS] [AIP] Error collecting device info: {e}", exc_info=True
            )
            # Continue with registration even if info collection fails
            metadata = {
                "registration_time": datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat(),
            }

        # Use AIP RegistrationProtocol to register
        self.logger.info(
            f"[WS] [AIP] Attempting to register as {self.ufo_client.client_id}"
        )
        success = await self.registration_protocol.register_as_device(
            device_id=self.ufo_client.client_id,
            metadata=metadata,
            platform=self.ufo_client.platform,
        )

        if success:
            self.connected_event.set()
            self.logger.warning(
                f"[WS] [AIP] ✅ Successfully registered as {self.ufo_client.client_id}"
            )
        else:
            self.logger.error(
                f"[WS] [AIP] ❌ Failed to register as {self.ufo_client.client_id}"
            )
            raise RuntimeError(f"Registration failed for {self.ufo_client.client_id}")

    async def handle_messages(self):
        """
        Listen for messages from server and dispatch them.
        When either recv_loop or heartbeat_loop fails, both will be cancelled.
        """
        recv_task = asyncio.create_task(self.recv_loop(), name="recv_loop")
        heartbeat_task = asyncio.create_task(
            self.heartbeat_loop(self.timeout), name="heartbeat_loop"
        )

        try:
            # Wait for the first task to complete (which means it failed)
            done, pending = await asyncio.wait(
                [recv_task, heartbeat_task], return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Check if any completed task raised an exception
            for task in done:
                if task.exception() is not None:
                    exc = task.exception()
                    self.logger.warning(f"[WS] {task.get_name()} failed with: {exc}")
                    raise exc

        except Exception as e:
            self.logger.warning(f"[WS] Message handling stopped: {e}")
            # Clean up connection state
            self.connected_event.clear()
            # Re-raise to trigger reconnection in connect_and_listen
            raise

    async def recv_loop(self):
        """
        Listen for incoming messages from the WebSocket.
        """
        try:
            while True:
                msg = await self._ws.recv()
                await self.handle_message(msg)
        except websockets.ConnectionClosed as e:
            self.logger.warning(f"[WS] recv_loop: Connection closed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"[WS] recv_loop error: {e}", exc_info=True)
            raise

    async def heartbeat_loop(self, interval: float = 30) -> None:
        """
        Send periodic heartbeat messages to the server using AIP HeartbeatProtocol.
        :param interval: The interval between heartbeat messages in seconds.
        """
        while True:
            await asyncio.sleep(interval)
            try:
                # Use AIP HeartbeatProtocol to send heartbeat
                await self.heartbeat_protocol.send_heartbeat(self.ufo_client.client_id)
                self.logger.debug("[WS] [AIP] Heartbeat sent")
            except (ConnectionError, IOError) as e:
                self.logger.debug(
                    f"[WS] [AIP] Heartbeat failed (connection closed): {e}"
                )
                break  # Exit loop if connection is closed

    async def handle_message(self, msg: str):
        """
        Dispatch messages based on their type.
        """
        try:
            data = ServerMessage.model_validate_json(msg)
            msg_type = data.type

            self.logger.info(f"[WS] Received message: {data}")

            if msg_type == ServerMessageType.TASK:
                await self.start_task(data.user_request, data.task_name)
            elif msg_type == ServerMessageType.HEARTBEAT:
                self.logger.info("[WS] Heartbeat received")
            elif msg_type == ServerMessageType.TASK_END:
                await self.handle_task_end(data)
            elif msg_type == ServerMessageType.ERROR:
                self.logger.error(f"[WS] Server error: {data.error}")
            elif msg_type == ServerMessageType.COMMAND:
                await self.handle_commands(data)
            else:
                self.logger.warning(f"[WS] Unknown message type: {msg_type}")

        except Exception as e:
            self.logger.error(f"[WS] Error handling message: {e}", exc_info=True)

    async def start_task(self, request_text: str, task_name: str | None):
        """
        Start a new task based on the received data.
        :param data: The data received from the server.
        :param ws: The WebSocket connection.
        """
        if self.current_task is not None and not self.current_task.done():
            self.logger.warning(
                f"[WS] Task {self.session_id} is still running, ignoring new task"
            )
            return

        self.logger.info(f"[WS] Starting task: {request_text}")

        async def task_loop():

            try:
                async with self.ufo_client.task_lock:
                    self.ufo_client.reset()

                    # Build metadata with platform information
                    metadata = {}
                    if self.ufo_client.platform:
                        metadata["platform"] = self.ufo_client.platform

                    # Use AIP TaskExecutionProtocol to send task request
                    await self.task_protocol.send_task_request(
                        request=request_text,
                        task_name=task_name if task_name else str(uuid4()),
                        session_id=self.ufo_client.session_id,
                        client_id=self.ufo_client.client_id,
                        metadata=metadata if metadata else None,
                    )

                    self.logger.info(
                        f"[WS] [AIP] Sent task request with platform: {self.ufo_client.platform}"
                    )
            except Exception as e:
                self.logger.error(
                    f"[WS] [AIP] Error sending task request: {e}", exc_info=True
                )
                # Send error message via AIP
                error_msg = ClientMessage(
                    type=ClientMessageType.ERROR,
                    error=str(e),
                    client_id=self.ufo_client.client_id,
                    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                )
                # Use transport directly for error messages
                await self.transport.send(error_msg.model_dump_json().encode())

        self.current_task = asyncio.create_task(task_loop())

    async def handle_commands(self, server_response: ServerMessage):
        """
        Handle commands received from the server.
        Uses AIP TaskExecutionProtocol to send results back.
        """

        response_id = server_response.response_id
        task_status = server_response.status
        self.session_id = server_response.session_id

        action_results = await self.ufo_client.execute_step(server_response)

        # Use AIP TaskExecutionProtocol to send results
        await self.task_protocol.send_task_result(
            session_id=self.session_id,
            prev_response_id=response_id,
            action_results=action_results,
            status=task_status,
            client_id=self.ufo_client.client_id,
        )

        self.logger.info(
            f"[WS] [AIP] Sent client result for prev_response_id: {response_id}"
        )

        if task_status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            await self.handle_task_end(server_response)

    async def handle_task_end(self, server_response: ServerMessage):
        """
        Handle task end messages from the server.
        :param server_response: The server response message.
        """

        if server_response.status == TaskStatus.COMPLETED:
            self.logger.info(
                f"[WS] Task {self.session_id} completed, result: {server_response.result}"
            )
        elif server_response.status == TaskStatus.FAILED:
            self.logger.info(
                f"[WS] Task {self.session_id} failed, with error: {server_response.error}"
            )
        else:
            self.logger.warning(
                f"[WS] Unknown task status for {self.session_id}: {server_response.status}"
            )

    async def _maybe_retry(self):
        """
        Exponential backoff before retrying connection.
        Only waits if we haven't exceeded max retries.
        """
        if self.retry_count < self.max_retries:
            wait_time = 2**self.retry_count
            self.logger.info(
                f"[WS] Retrying in {wait_time}s... ({self.retry_count}/{self.max_retries})"
            )
            await asyncio.sleep(wait_time)
        else:
            self.logger.error(
                f"[WS] ❌ Max retries reached ({self.max_retries}). Please check if server is running at {self.ws_url}"
            )

    def is_connected(self) -> bool:
        """
        Check if the WebSocket connection is active.
        """
        return (
            self.connected_event.is_set()
            and self._ws is not None
            and not self._ws.closed
        )

    @property
    def ws(self) -> Optional[WebSocketClientProtocol]:
        """
        Get the current WebSocket connection.
        """
        return self._ws

    @ws.setter
    def ws(self, value: Optional[WebSocketClientProtocol]):
        """
        Set the current WebSocket connection.
        """
        self._ws = value
