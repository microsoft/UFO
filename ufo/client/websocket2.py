import asyncio
import datetime
import json
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

import websockets
from contracts.contracts import ClientMessage, ServerMessage
from websockets import WebSocketClientProtocol
from uuid import uuid4

if TYPE_CHECKING:
    from ufo.client.ufo_client2 import UFOClient


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
        self.current_task_id: Optional[str] = None

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
                    await self.register_client(ws)
                    self.retry_count = 0
                    await self.handle_messages(ws)
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

    async def register_client(self, ws: WebSocketClientProtocol):
        """
        Send client_id to server upon connection.
        """

        client_message = ClientMessage(
            type="register",
            client_id=self.ufo_client.client_id,
            status="ok",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            task_id=self.current_task_id,
        )

        await ws.send(client_message.model_dump_json())

        self.logger.info(f"[WS] Registered as {self.ufo_client.client_id}")

    async def handle_messages(self, ws: WebSocketClientProtocol):
        """
        Listen for messages from server and dispatch them.
        """
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=self.timeout)
            except asyncio.TimeoutError:
                self.logger.warning(
                    f"[WS] Message receive timed out after {self.timeout} seconds, sending heartbeat"
                )
                client_message = ClientMessage(
                    type="heartbeat",
                    client_id=self.ufo_client.client_id,
                    status="ok",
                    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    task_id=self.current_task_id,
                )
                await ws.send(client_message.model_dump_json())
                continue

            await self.handle_message(msg, ws)

    async def handle_message(self, msg: str, ws: WebSocketClientProtocol):
        """
        Dispatch messages based on their type.
        """
        try:
            data = ServerMessage.model_validate_json(msg)
            msg_type = data.type

            self.logger.info(f"[WS] Received message: {data}")

            if msg_type == "task":
                await self.start_task(data, ws)
            elif msg_type == "heartbeat":
                self.logger.info("[WS] Heartbeat received")
                client_message = ClientMessage(
                    type="heartbeat",
                    status="ok",
                    client_id=self.ufo_client.client_id,
                    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    task_id=self.current_task_id,
                )
                await ws.send(client_message.model_dump_json())
            elif msg_type == "task_end":
                await self.handle_task_end(data)
            elif msg_type == "error":
                self.logger.error(f"[WS] Server error: {data.error}")
            elif msg_type == "commands":
                await self.handle_commands(data, ws)
            else:
                self.logger.warning(f"[WS] Unknown message type: {msg_type}")

        except Exception as e:
            self.logger.error(f"[WS] Error handling message: {e}", exc_info=True)

    async def start_task(
        self, server_response: ServerMessage, ws: WebSocketClientProtocol
    ):
        """
        Start a new task based on the received data.
        :param data: The data received from the server.
        :param ws: The WebSocket connection.
        """
        if self.current_task is not None and not self.current_task.done():
            self.logger.warning(
                f"[WS] Task {self.current_task_id} is still running, ignoring new task"
            )
            return

        self.current_task_id = str(uuid4())
        request_text = server_response.user_request

        self.logger.info(f"[WS] Starting task {self.current_task_id}: {request_text}")

        async def task_loop():

            try:
                async with self.ufo_client.task_lock:
                    self.ufo_client.reset()

                    client_message = ClientMessage(
                        type="task",
                        request=request_text,
                        session_id=self.ufo_client.session_id,
                        client_id=self.ufo_client.client_id,
                        request_id=str(uuid4()),
                        timestamp=datetime.datetime.now(
                            datetime.timezone.utc
                        ).isoformat(),
                        status="continue",
                        timestamp=datetime.datetime.now(
                            datetime.timezone.utc
                        ).isoformat(),
                        task_id=self.current_task_id,
                    )

                    await ws.send(client_message.model_dump_json())
            except Exception as e:
                self.logger.error(
                    f"[WS] Error sending task request: {e}", exc_info=True
                )
                client_message = ClientMessage(
                    type="error",
                    error=str(e),
                    client_id=self.ufo_client.client_id,
                    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    task_id=self.current_task_id,
                )
                await ws.send(client_message.model_dump_json())

        self.current_task = asyncio.create_task(task_loop())

    async def handle_commands(
        self, server_response: ServerMessage, ws: WebSocketClientProtocol
    ):
        """
        Handle commands received from the server.
        """

        if not self.current_task_id:
            self.logger.error("[WS] Received command without an active task")
            return

        response_id = server_response.response_id
        task_status = server_response.status

        if task_status == "continue":
            action_results = await self.ufo_client.step(server_response)

            client_message = ClientMessage(
                type="command_results",
                session_id=self.ufo_client.session_id,
                request_id=str(uuid4()),
                action_results=action_results,
                client_id=self.ufo_client.client_id,
                prev_response_id=response_id,
                status=task_status,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                task_id=self.current_task_id,
            )

        elif task_status in ["completed", "failed"]:
            self.logger.info(
                f"[WS] Task {self.current_task_id} is ended with status: {task_status}"
            )
            self.current_task = None
            self.current_task_id = None

            client_message = ClientMessage(
                type="task_end",
                client_id=self.ufo_client.client_id,
                prev_response_id=response_id,
                status=task_status,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                task_id=self.current_task_id,
            )

        else:
            self.logger.warning(
                f"[WS] Unknown task status for {self.current_task_id}: {task_status}"
            )

        await ws.send(client_message.model_dump_json())

    async def handle_task_end(self, server_response: ServerMessage):
        """
        Handle task end messages from the server.
        :param server_response: The server response message.
        """

        if server_response.status == "completed":
            self.logger.info(f"[WS] Task {self.current_task_id} completed")
        elif server_response.status == "failed":
            self.logger.info(
                f"[WS] Task {self.current_task_id} failed, with error: {server_response.error}"
            )
        else:
            self.logger.warning(
                f"[WS] Unknown task status for {self.current_task_id}: {server_response.status}"
            )

    async def _maybe_retry(self):
        """
        Exponential backoff before retrying connection.
        """
        if self.retry_count < self.max_retries:
            wait_time = 2**self.retry_count
            self.logger.info(f"[WS] Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
