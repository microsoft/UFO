# 改动点：Flask Blueprint -> FastAPI APIRouter，request.json -> Pydantic model
import datetime
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ufo.contracts.contracts import ClientMessage, ServerMessage
from ufo.module.context import ContextNames
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.task_manager import TaskManager
from ufo.server.services.ws_manager import WSManager
from uuid import uuid4


logger = logging.getLogger(__name__)


# Pydantic Model 替代 request.json
class RunTaskRequest(BaseModel):
    session_id: Optional[str]
    request: Optional[str]
    action_results: Optional[dict]


def create_api_router(
    session_manager: SessionManager, task_manager: TaskManager, ws_manager: WSManager
):
    router = APIRouter()

    @router.get("/api/clients")
    async def list_clients():
        return {"online_clients": ws_manager.list_clients()}

    @router.post("/api/dispatch")
    async def dispatch_task_api(data: dict):
        import asyncio, json

        client_id = data.get("client_id")
        task_content = data.get("task_content", "")
        task_name = data.get("task_name", str(uuid4()))

        if not task_content:
            logger.error(f"Got empty task content for client {client_id}.")
            raise HTTPException(status_code=400, detail="Empty task content")

        if not client_id:
            logger.error("Client ID must be provided.")
            raise HTTPException(status_code=400, detail="Empty client ID")

        if not task_name:
            logger.warning(f"Task name not provided, using {task_name}.")
        else:
            logger.info(f"Task name: {task_name}.")

        logger.info(f"Dispatching task '{task_content}' to client '{client_id}'")

        ws = ws_manager.get_client(client_id)
        if not ws:
            logger.error(f"Client {client_id} not online.")
            raise HTTPException(status_code=404, detail="Client not online")

        ws_event_loop = asyncio.get_event_loop()

        message = ServerMessage(
            user_request=task_content,
            task_name=task_name,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        asyncio.run_coroutine_threadsafe(
            ws.send_text(message.model_dump()),
            ws_event_loop,
        )
        return {"status": "dispatched", "task_name": task_name, "client_id": client_id}

    @router.get("/api/task_result/{task_name}")
    async def get_task_result(task_name: str):
        result = task_manager.get_result(task_name)
        if not result:
            return {"status": "pending"}
        return {"status": "done", "result": result}

    @router.get("/api/health")
    async def health_check():
        return {"status": "healthy", "online_clients": ws_manager.list_clients()}

    return router
