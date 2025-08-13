import asyncio
import json
import logging
from typing import TYPE_CHECKING, Dict, Any

import websockets
from websockets import WebSocketClientProtocol

if TYPE_CHECKING:
    from ufo.client.ufo_client import UFOClient


class UFOWebSocketClient:
    """
    WebSocket client compatible with FastAPI UFO server.
    Handles task_request, heartbeat, result_ack, notify_ack.
    """

    def __init__(self, ws_url: str, ufo_client: "UFOClient", max_retries: int = 3):
        self.ws_url = ws_url
        self.ufo_client = ufo_client
        self.max_retries = max_retries
        self.retry_count = 0
        self.logger = logging.getLogger(self.__class__.__name__)

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
        await ws.send(json.dumps({"client_id": self.ufo_client.client_id}))
        self.logger.info(f"[WS] Registered as {self.ufo_client.client_id}")

    async def handle_messages(self, ws: WebSocketClientProtocol):
        """
        Listen for messages from server and dispatch them.
        """
        async for msg in ws:
            await self.handle_message(msg, ws)

    async def handle_message(self, msg: str, ws: WebSocketClientProtocol):
        """
        Dispatch messages based on their type.
        """
        try:
            data = json.loads(msg)
            msg_type = data.get("type")
            self.logger.info(f"[WS] Received message: {data}")

            if msg_type == "task":
                await self.handle_task_request(data, ws)
            elif msg_type == "heartbeat":
                await ws.send(json.dumps({"type": "heartbeat", "status": "ok"}))
            elif msg_type == "result_ack":
                self.logger.info(f"[WS] Result acknowledged: {data.get('task_id')}")
            elif msg_type == "notify_ack":
                self.logger.info(f"[WS] Notification acknowledged")
            elif msg_type == "error":
                self.logger.error(f"[WS] Server error: {data.get('error')}")
            else:
                self.logger.warning(f"[WS] Unknown message type: {msg_type}")

        except Exception as e:
            self.logger.error(f"[WS] Error handling message: {e}", exc_info=True)

    async def handle_task_request(
        self, data: Dict[str, Any], ws: WebSocketClientProtocol
    ):
        """
        Execute task_request received from server and send result.
        """
        try:
            request_text = data.get("request", "No request provided")
            task_id = data.get("task_id", "unknown")

            self.logger.info(f"[WS] Executing task {task_id}: {request_text}")
            async with self.ufo_client.task_lock:
                self.ufo_client.reset()
                success = await self.ufo_client.run(request_text)

            # Send result back to server
            result = {"success": success}
            await ws.send(
                json.dumps({"type": "result", "task_id": task_id, "result": result})
            )
            self.logger.info(f"[WS] Sent result for {task_id}")

        except Exception as e:
            self.logger.error(f"[WS] Failed to handle task_request: {e}", exc_info=True)

    async def _maybe_retry(self):
        """
        Exponential backoff before retrying connection.
        """
        if self.retry_count < self.max_retries:
            wait_time = 2**self.retry_count
            self.logger.info(f"[WS] Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
