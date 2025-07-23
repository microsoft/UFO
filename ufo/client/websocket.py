import asyncio
import json
import logging
import websockets
from websockets import WebSocketClientProtocol

from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from ufo.client.client import UFOClient


class UFOWebSocketClient:
    def __init__(self, server_addr: str, ufo_client: "UFOClient", max_retries: int = 3):
        """
        Initialize the WebSocket client.
        :param server_addr: The WebSocket server address.
        :param ufo_client: The UFOClient instance to use for running tasks.
        :param max_retries: Maximum number of retries for connection attempts.
        """
        self.server_addr = server_addr
        self.ufo_client = ufo_client
        self.max_retries = max_retries
        self.retry_count = 0
        self.logger = logging.getLogger(self.__class__.__name__)

    async def connect_and_listen(self):
        """
        Connect to the WebSocket server and listen for incoming messages.
        This method will retry the connection if it fails, up to the maximum number of retries.
        """
        while self.retry_count < self.max_retries:
            try:
                self.logger.info(
                    f"Connecting to {self.server_addr} (attempt {self.retry_count + 1}/{self.max_retries})"
                )
                async with websockets.connect(self.server_addr) as ws:
                    await self.register_client(ws)
                    self.retry_count = 0
                    await self.handle_messages(ws)
            except (
                websockets.ConnectionClosedError,
                websockets.ConnectionClosedOK,
            ) as e:
                self.logger.error(f"WebSocket connection closed: {e}")
                self.retry_count += 1
                await self._maybe_retry()
            except Exception as e:
                self.logger.error(
                    f"Unexpected WebSocket client error: {e}", exc_info=True
                )
                self.retry_count += 1
                await self._maybe_retry()
        self.logger.error("Max retries reached. Exiting websocket client.")

    async def register_client(self, ws: WebSocketClientProtocol):
        """
        Register the client with the WebSocket server.
        This method sends the client ID to the server upon connection.
        :param ws: The WebSocket connection object.
        """
        client_id = self.ufo_client.client_id
        await ws.send(json.dumps({"client_id": client_id}))
        self.logger.info(f"[WebSocket] Registered as {client_id}, waiting for task...")

    async def handle_messages(self, ws: WebSocketClientProtocol):
        """
        Handle incoming messages from the WebSocket server.
        This method listens for messages and processes them accordingly.
        :param ws: The WebSocket connection object.
        """
        async for msg in ws:
            await self.handle_message(msg, ws)

    async def handle_message(self, msg: str, ws: WebSocketClientProtocol):
        """
        Handle a single message received from the WebSocket server.
        This method processes the message and executes tasks if applicable.
        :param msg: The message received from the WebSocket server.
        :param ws: The WebSocket connection object.
        """
        try:
            task = json.loads(msg)
            if task.get("type") == "task":
                await self.handle_task(task, ws)
            else:
                self.logger.info(f"Received non-task message: {task}")
        except Exception as task_exc:
            self.logger.error(f"Error handling task message: {task_exc}", exc_info=True)

    async def handle_task(self, task: Dict[str, Any], ws: WebSocketClientProtocol):
        """
        Handle a task received from the WebSocket server.
        This method processes the task and sends the result back to the server.
        :param task: The task dictionary containing task details.
        :param ws: The WebSocket connection object.
        """
        task_id = task["task_id"]
        request_text = task["request"]
        self.logger.info(f"[WebSocket] Got task {task_id}: {request_text}")

        async with self.ufo_client.task_lock:
            self.ufo_client.reset()
            success = await self.ufo_client.run(request_text)
            result = {"success": success}
            await ws.send(
                json.dumps(
                    {
                        "type": "result",
                        "task_id": task_id,
                        "result": result,
                    }
                )
            )
            self.logger.info(f"[WebSocket] Sent result for {task_id}")

    async def _maybe_retry(self):
        """
        If the retry count is less than the maximum, wait for an exponential backoff
        before retrying the connection.
        """
        if self.retry_count < self.max_retries:
            self.logger.info(
                f"Retrying WebSocket connection ({self.retry_count}/{self.max_retries}) after {2 ** self.retry_count}s..."
            )
            await asyncio.sleep(2**self.retry_count)
