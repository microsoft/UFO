import asyncio
import datetime
import logging
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

import websockets
from websockets import WebSocketClientProtocol

from ufo.contracts.contracts import ClientMessage, ServerMessage

if TYPE_CHECKING:
    from ufo.client.ufo_client import UFOClient


class UFOWebSocketClient:
    """
    WebSocket client compatible with FastAPI UFO server.
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

    async def connect_and_listen(self):
        """
        Connect to the FastAPI WebSocket server and listen for incoming messages.
        Automatically retries on failure.
        """
        while self.retry_count < self.max_retries:
            try:
                self.logger.info(
                    f"[WS] Connecting to {self.ws_url} (attempt {self.retry_count + 1}/{self.max_retries})"
                )
                async with websockets.connect(self.ws_url) as ws:
                    self._ws = ws
                    await self.register_client()
                    self.retry_count = 0
                    await self.handle_messages()
            except (
                websockets.ConnectionClosedError,
                websockets.ConnectionClosedOK,
            ) as e:
                self.logger.error(f"[WS] Connection closed: {e}")
                self.retry_count += 1
                await self._maybe_retry()
            except Exception as e:
                self.logger.error(f"[WS] Unexpected error: {e}", exc_info=True)
                self.retry_count += 1
                await self._maybe_retry()
        self.logger.error("[WS] Max retries reached. Exiting.")

    async def register_client(self):
        """
        Send client_id to server upon connection.
        """

        client_message = ClientMessage(
            type="register",
            client_id=self.ufo_client.client_id,
            status="ok",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        await self._ws.send(client_message.model_dump_json())

        self.connected_event.set()

        self.logger.info(f"[WS] Registered as {self.ufo_client.client_id}")

    async def handle_messages(self):
        """
        Listen for messages from server and dispatch them.
        """
        await asyncio.gather(self.recv_loop(), self.heartbeat_loop(self.timeout))

    async def recv_loop(self):
        """
        Listen for incoming messages from the WebSocket.
        """
        while True:
            msg = await self._ws.recv()
            await self.handle_message(msg)

    async def heartbeat_loop(self, interval: float = 30) -> None:
        """
        Send periodic heartbeat messages to the server.
        :param interval: The interval between heartbeat messages in seconds.
        """
        while True:
            await asyncio.sleep(interval)
            client_message = ClientMessage(
                type="heartbeat",
                client_id=self.ufo_client.client_id,
                status="ok",
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )
            await self._ws.send(client_message.model_dump_json())
            self.logger.debug("[WS] Heartbeat sent")

    async def handle_message(self, msg: str):
        """
        Dispatch messages based on their type.
        """
        try:
            data = ServerMessage.model_validate_json(msg)
            msg_type = data.type

            self.logger.info(f"[WS] Received message: {data}")

            if msg_type == "task":
                await self.start_task(data.user_request, data.task_name)
            elif msg_type == "heartbeat":
                self.logger.info("[WS] Heartbeat received")
            elif msg_type == "task_end":
                await self.handle_task_end(data)
            elif msg_type == "error":
                self.logger.error(f"[WS] Server error: {data.error}")
            elif msg_type == "commands":
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

                    client_message = ClientMessage(
                        type="task",
                        request=request_text,
                        task_name=task_name if task_name else str(uuid4()),
                        session_id=self.ufo_client.session_id,
                        client_id=self.ufo_client.client_id,
                        request_id=str(uuid4()),
                        timestamp=datetime.datetime.now(
                            datetime.timezone.utc
                        ).isoformat(),
                        status="continue",
                    )

                    await self._ws.send(client_message.model_dump_json())
            except Exception as e:
                self.logger.error(
                    f"[WS] Error sending task request: {e}", exc_info=True
                )
                client_message = ClientMessage(
                    type="error",
                    error=str(e),
                    client_id=self.ufo_client.client_id,
                    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                )
                await self._ws.send(client_message.model_dump_json())

        self.current_task = asyncio.create_task(task_loop())

    async def handle_commands(self, server_response: ServerMessage):
        """
        Handle commands received from the server.
        """

        if not self.current_task:
            self.logger.error("[WS] Received command without an active task")
            return

        response_id = server_response.response_id
        task_status = server_response.status
        self.session_id = server_response.session_id

        if task_status == "continue":
            action_results = await self.ufo_client.step(server_response)

            client_message = ClientMessage(
                type="command_results",
                session_id=self.session_id,
                request_id=str(uuid4()),
                action_results=action_results,
                client_id=self.ufo_client.client_id,
                prev_response_id=response_id,
                status=task_status,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )

        elif task_status in ["completed", "failed"]:
            self.logger.info(
                f"[WS] Task {self.session_id} is ended with status: {task_status}"
            )
            self.current_task = None

            client_message = ClientMessage(
                type="task_end",
                client_id=self.ufo_client.client_id,
                session_id=self.session_id,
                prev_response_id=response_id,
                status=task_status,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )

        else:
            self.logger.warning(
                f"[WS] Unknown task status for {self.session_id}: {task_status}"
            )

        # self.logger.info(f"[WS] Sending client message: {client_message}")
        self.logger.info(
            f"Sending client message for prev_response_id: {client_message.prev_response_id}"
        )
        await self._ws.send(client_message.model_dump_json())

    async def handle_task_end(self, server_response: ServerMessage):
        """
        Handle task end messages from the server.
        :param server_response: The server response message.
        """

        if server_response.status == "completed":
            self.logger.info(f"[WS] Task {self.session_id} completed")
        elif server_response.status == "failed":
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
        """
        if self.retry_count < self.max_retries:
            wait_time = 2**self.retry_count
            self.logger.info(f"[WS] Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)

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
