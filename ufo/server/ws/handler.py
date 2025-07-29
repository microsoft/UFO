import datetime
import json
import logging
from typing import Any, Dict

import websockets

from ufo.contracts.contracts import ClientRequest, ServerResponse
from ufo.module.context import ContextNames
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.task_manager import TaskManager
from ufo.server.services.ws_manager import WSManager


class UFOWebSocketHandler:
    def __init__(
        self,
        ws_manager: WSManager,
        session_manager: SessionManager,
        task_manager: TaskManager,
    ):
        """
        Initialize the WebSocket handler with the necessary managers.
        :param ws_manager: The WebSocket manager to handle client connections.
        :param session_manager: The session manager to handle user sessions.
        :param task_manager: The task manager to handle tasks and their execution.
        """
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
                self.logger.info(f"[WS] Task request from {client_id}: {data}")
                await self.handle_task_request(data, websocket)

            elif data.get("type") == "heartbeat":
                # Handle heartbeat messages to keep the connection alive
                self.logger.info(f"[WS] Heartbeat from {client_id}")
                await websocket.send(json.dumps({"type": "heartbeat", "status": "ok"}))

            elif data.get("type") == "result":
                # Handle result messages from the client
                task_id = data.get("task_id")
                result = data.get("result")
                self.task_manager.set_result(task_id, result)
                self.logger.info(
                    f"[WS] Result for task {task_id} from {client_id}: {result}"
                )
                await websocket.send(
                    json.dumps({"type": "result_ack", "task_id": task_id})
                )

            elif data.get("type") == "get_result":
                # Handle requests for results
                task_id = data.get("task_id")
                result = self.task_manager.get_result(task_id)

                if result:
                    await websocket.send(
                        json.dumps(
                            {"type": "result", "task_id": task_id, "result": result}
                        )
                    )
                else:
                    await websocket.send(
                        json.dumps({"type": "error", "error": "Result not found"})
                    )

            elif data.get("type") == "notify":
                # Handle notification messages from the client
                notification = data.get("notification")
                self.logger.info(f"[WS] Notification from {client_id}: {notification}")
                await websocket.send(
                    json.dumps({"type": "notify_ack", "status": "received"})
                )

            else:
                self.logger.warning(f"[WS] Unknown message type: {data.get('type')}")
                await websocket.send(
                    json.dumps({"type": "error", "error": "Unknown message type"})
                )
            # Future: add more handlers (heartbeat, result, notify, ...)
        except Exception as e:
            self.logger.error(f"[WS] Error handling message from {client_id}: {e}")
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
        self.logger.info(f"[WS] Handling task request: {req}")

        session_id = req.session_id
        session = self.session_manager.get_or_create_session(session_id, req.request)
        status = "continue"
        try:
            session.run_coro.send(None)
        except StopIteration:
            status = "completed"

        commands = session.get_commands()

        response = ServerResponse(
            status=status,
            agent_name=session.current_round.agent.__class__.__name__,
            root_name=session.context.get(ContextNames.APPLICATION_ROOT_NAME),
            process_name=session.context.get(ContextNames.APPLICATION_PROCESS_NAME),
            actions=commands,
            session_id=session_id,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        resp = {"type": "task_response", "body": response.model_dump()}
        await websocket.send(json.dumps(resp))
