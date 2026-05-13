import logging
import secrets
from typing import Any, Dict
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException

from aip.protocol.task_execution import TaskExecutionProtocol
from aip.transport.websocket import WebSocketTransport
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.client_connection_manager import ClientConnectionManager
from ufo.utils import is_safe_task_name

logger = logging.getLogger(__name__)


def _make_auth_dependency(api_key: str):
    """Create a FastAPI dependency that validates the X-API-Key header."""

    async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
        if not secrets.compare_digest(x_api_key, api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")

    return verify_api_key


def create_api_router(
    session_manager: SessionManager,
    client_manager: ClientConnectionManager,
    api_key: str,
) -> APIRouter:
    """
    Create the API router for the UFO server.
    :param session_manager: The session manager instance.
    :param client_manager: The client connection manager instance.
    :param api_key: The API key required for authenticated endpoints.
    :return: The FastAPI APIRouter instance.
    """
    auth = _make_auth_dependency(api_key)
    router = APIRouter()

    @router.get("/api/clients", dependencies=[Depends(auth)])
    async def list_clients():
        return {"online_clients": client_manager.list_clients()}

    @router.post("/api/dispatch", dependencies=[Depends(auth)])
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

        # ``task_name`` is later used as a filesystem path component for log
        # storage. Reject values containing path separators, traversal
        # sequences, or any character outside ``[A-Za-z0-9._-]`` to prevent
        # path-traversal driven log writes outside ``logs/``.
        if not is_safe_task_name(task_name):
            logger.error(
                f"Rejected unsafe task_name {task_name!r} for client {client_id}."
            )
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid task_name: must be a non-empty string of "
                    "characters [A-Za-z0-9._-] and must not start with '.'"
                ),
            )

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

    @router.get("/api/task_result/{task_name}", dependencies=[Depends(auth)])
    async def get_task_result(task_name: str):
        result = session_manager.get_result_by_task(task_name)
        if not result:
            return {"status": "pending"}
        return {"status": "done", "result": result}

    @router.get("/api/health", dependencies=[Depends(auth)])
    async def health_check():
        return {"status": "healthy", "online_clients": client_manager.list_clients()}

    return router
