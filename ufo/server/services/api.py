import logging
from typing import Any, Dict
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from aip.protocol.task_execution import TaskExecutionProtocol
from aip.transport.websocket import WebSocketTransport
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.client_connection_manager import ClientConnectionManager

logger = logging.getLogger(__name__)


def create_api_router(
    session_manager: SessionManager, client_manager: ClientConnectionManager
) -> APIRouter:
    """
    Create the API router for the UFO server.
    :param session_manager: The session manager instance.
    :param client_manager: The client connection manager instance.
    :return: The FastAPI APIRouter instance.
    """
    router = APIRouter()

    @router.get("/api/clients")
    async def list_clients():
        return {"online_clients": client_manager.list_clients()}

    @router.post("/api/dispatch")
    async def dispatch_task_api(data: Dict[str, Any]):

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

        ws = client_manager.get_client(client_id)
        if not ws:
            logger.error(f"Client {client_id} not online.")
            raise HTTPException(status_code=404, detail="Client not online")

        # Use AIP protocol to send task assignment
        transport = WebSocketTransport(ws)
        task_protocol = TaskExecutionProtocol(transport)

        session_id = str(uuid4())
        response_id = str(uuid4())

        logger.info(
            f"[AIP] Sending task assignment via API: task_name={task_name}, "
            f"session_id={session_id}, client_id={client_id}"
        )

        await task_protocol.send_task_assignment(
            user_request=user_request,
            task_name=task_name,
            session_id=session_id,
            response_id=response_id,
        )

        return {
            "status": "dispatched",
            "task_name": task_name,
            "client_id": client_id,
            "session_id": session_id,
        }

    @router.get("/api/task_result/{task_name}")
    async def get_task_result(task_name: str):
        result = session_manager.get_result_by_task(task_name)
        if not result:
            return {"status": "pending"}
        return {"status": "done", "result": result}

    @router.get("/api/health")
    async def health_check():
        return {"status": "healthy", "online_clients": client_manager.list_clients()}

    return router
