import datetime
import json
import logging
from typing import Any, Dict

import websockets
from ufo.contracts.contracts import ServerResponse, ClientRequest
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.task_manager import TaskManager
from ufo.server.services.ws_manager import WSManager

logger = logging.getLogger(__name__)


class UFOWebSocketHandler:
    def __init__(
        self,
        ws_manager: WSManager,
        session_manager: SessionManager,
        task_manager: TaskManager,
    ):
        self.ws_manager = ws_manager
        self.session_manager = session_manager
        self.task_manager = task_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    async def __call__(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """
        Entry point for the WebSocket server.
        :param websocket: The WebSocket connection object.
        :param path: The path of the WebSocket connection.
        """
        reg_msg = await websocket.recv()
        reg_info = json.loads(reg_msg)
        client_id = reg_info.get("client_id", None)
        self.ws_manager.add_client(client_id, websocket)
        self.logger.info(f"[WS] {client_id} connected")

        try:
            async for msg in websocket:
                await self.handle_message(msg, websocket, client_id)
        except Exception as e:
            self.logger.error(f"WS client {client_id} error: {e}")
        finally:
            self.ws_manager.remove_client(client_id)

    async def handle_message(
        self, msg: str, websocket: websockets.WebSocketServerProtocol, client_id: str
    ):
        """
        Parse and dispatch incoming WS messages.
        :param msg: The message received from the WebSocket server.
        :param websocket: The WebSocket connection object.
        :param client_id: The ID of the client sending the message.
        """
        try:
            data = json.loads(msg)
            self.logger.info(f"[WS] Received message from {client_id}: {data}")

            if data.get("type") == "task_request":
                await self.handle_task_request(data, websocket)
            # Future: add more handlers (heartbeat, result, notify, ...)
        except Exception as e:
            await websocket.send(json.dumps({"type": "error", "error": str(e)}))

    async def handle_task_request(
        self, data: Dict[str, Any], websocket: websockets.WebSocketServerProtocol
    ):
        """
        Handle a task request message from the client.
        :param data: The parsed message data.
        :param websocket: The WebSocket connection object.
        """

        req = ClientRequest(**data["body"])
        session_id = req.session_id
        session = self.session_manager.get_or_create_session(session_id, req.request)
        status = "continue"
        try:
            session.run_coro.send(None)
        except StopIteration:
            status = "completed"
        actions = session.get_actions()

        response = ServerResponse(
            session_id=session_id,
            status=status,
            actions=actions,
            agent_name="Placeholder Agent",  # Replace with actual agent name if available
            process_name="Placeholder Process",  # Replace with actual process name if available
            root_name="Placeholder Root",  # Replace with actual root name if available
            messages=[],
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        resp = {"type": "task_response", "body": response.model_dump()}
        await websocket.send(json.dumps(resp))
