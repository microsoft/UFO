import datetime
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ufo.contracts.contracts import ServerMessage
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.ws_manager import WSManager
from uuid import uuid4


logger = logging.getLogger(__name__)


def create_api_router(
    session_manager: SessionManager, ws_manager: WSManager
) -> APIRouter:
    """
    Create the API router for the UFO server.
    :param session_manager: The session manager instance.
    :param ws_manager: The WebSocket manager instance.
    :return: The FastAPI APIRouter instance.
    """
    router = APIRouter()

    @router.get("/api/clients")
    async def list_clients():
        return {"online_clients": ws_manager.list_clients()}

    @router.post("/api/dispatch")
    async def dispatch_task_api(data: Dict[str, Any]):
        import asyncio, json

        client_id = data.get("client_id")
        user_request = data.get("request", "")
        task_name = data.get("task_name", str(uuid4()))

        if not user_request:
            logger.error(f"Got empty task content for client {client_id}.")
            raise HTTPException(status_code=400, detail="Empty task content")

        if not client_id:
            logger.error("Client ID must be provided.")
            raise HTTPException(status_code=400, detail="Empty client ID")

        if not task_name:
            logger.warning(f"Task name not provided, using {task_name}.")
        else:
            logger.info(f"Task name: {task_name}.")

        logger.info(f"Dispatching task '{user_request}' to client '{client_id}'")

        ws = ws_manager.get_client(client_id)
        if not ws:
            logger.error(f"Client {client_id} not online.")
            raise HTTPException(status_code=404, detail="Client not online")

        server_message = ServerMessage(
            type="task",
            status="continue",
            user_request=user_request,
            task_name=task_name,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        await ws.send_text(server_message.model_dump_json())

        return {"status": "dispatched", "task_name": task_name, "client_id": client_id}

    @router.get("/api/task_result/{task_name}")
    async def get_task_result(task_name: str):
        result = session_manager.get_result_by_task(task_name)
        if not result:
            return {"status": "pending"}
        return {"status": "done", "result": result}

    @router.get("/api/health")
    async def health_check():
        return {"status": "healthy", "online_clients": ws_manager.list_clients()}

    return router
