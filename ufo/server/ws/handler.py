import datetime
import json
import logging
from typing import Any, Dict

from fastapi import WebSocket, WebSocketDisconnect

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
        self.ws_manager = ws_manager
        self.session_manager = session_manager
        self.task_manager = task_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    async def connect(self, websocket: WebSocket):
        """
        Connects a client and registers it in the WS manager.
        Expects the first message to contain {"client_id": ...}.
        """
        await websocket.accept()
        reg_msg = await websocket.receive_text()
        reg_info = json.loads(reg_msg)
        client_id = reg_info.get("client_id", None)
        self.ws_manager.add_client(client_id, websocket)
        self.logger.info(f"[WS] {client_id} connected")
        return client_id

    async def disconnect(self, client_id: str):
        self.ws_manager.remove_client(client_id)
        self.logger.info(f"[WS] {client_id} disconnected")

    async def handler(self, websocket: WebSocket):
        """
        FastAPI WebSocket entry point.
        """
        client_id = await self.connect(websocket)
        try:
            while True:
                msg = await websocket.receive_text()
                await self.handle_message(msg, websocket, client_id)
        except WebSocketDisconnect:
            await self.disconnect(client_id)
        except Exception as e:
            self.logger.error(f"[WS] Error with client {client_id}: {e}")
            await self.disconnect(client_id)

    async def handle_message(self, msg: str, websocket: WebSocket, client_id: str):
        """
        Dispatch incoming WS messages to specific handlers.
        """
        try:
            data = json.loads(msg)
            self.logger.info(f"[WS] Received message from {client_id}: {data}")
            msg_type = data.get("type")

            if msg_type == "task_request":
                await self.handle_task_request(data, websocket)
            elif msg_type == "heartbeat":
                await self.handle_heartbeat(websocket, client_id)
            elif msg_type == "result":
                await self.handle_result(data, websocket, client_id)
            elif msg_type == "get_result":
                await self.handle_get_result(data, websocket)
            elif msg_type == "notify":
                await self.handle_notify(data, websocket, client_id)
            else:
                await self.handle_unknown(data, websocket)
        except Exception as e:
            self.logger.error(f"[WS] Error handling message from {client_id}: {e}")
            await websocket.send_text(json.dumps({"type": "error", "error": str(e)}))

    async def handle_heartbeat(self, websocket: WebSocket, client_id: str):
        self.logger.info(f"[WS] Heartbeat from {client_id}")
        await websocket.send_text(json.dumps({"type": "heartbeat", "status": "ok"}))

    async def handle_result(
        self, data: Dict[str, Any], websocket: WebSocket, client_id: str
    ):
        task_id = data.get("task_id")
        result = data.get("result")
        self.task_manager.set_result(task_id, result)
        self.logger.info(f"[WS] Result for task {task_id} from {client_id}: {result}")
        await websocket.send_text(
            json.dumps({"type": "result_ack", "task_id": task_id})
        )

    async def handle_get_result(self, data: Dict[str, Any], websocket: WebSocket):
        task_id = data.get("task_id")
        result = self.task_manager.get_result(task_id)
        if result:
            await websocket.send_text(
                json.dumps({"type": "result", "task_id": task_id, "result": result})
            )
        else:
            await websocket.send_text(
                json.dumps({"type": "error", "error": "Result not found"})
            )

    async def handle_notify(
        self, data: Dict[str, Any], websocket: WebSocket, client_id: str
    ):
        notification = data.get("notification")
        self.logger.info(f"[WS] Notification from {client_id}: {notification}")
        await websocket.send_text(
            json.dumps({"type": "notify_ack", "status": "received"})
        )

    async def handle_unknown(self, data: Dict[str, Any], websocket: WebSocket):
        self.logger.warning(f"[WS] Unknown message type: {data.get('type')}")
        await websocket.send_text(
            json.dumps({"type": "error", "error": "Unknown message type"})
        )

    async def handle_task_request(self, data: Dict[str, Any], websocket: WebSocket):
        """
        Handle a task request message from the client.
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
        await websocket.send_text(json.dumps(resp))
