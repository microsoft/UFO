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

    @router.post("/api/ufo/task")
    async def run_task(req: RunTaskRequest):
        try:
            ufo_request = ClientMessage(**req.model_dump())
            session_id = ufo_request.session_id

            if not session_id or session_id not in session_manager.sessions:
                session_id = ufo_request.session_id or str(uuid4())

            session = session_manager.get_or_create_session(
                session_id, ufo_request.request
            )

            if ufo_request.action_results:
                session_manager.process_action_results(
                    session_id, ufo_request.action_results
                )

            status = "continue"
            try:
                session.run_coro.send(None)
            except StopIteration:
                status = "completed"

            commands = session.get_commands()
            response = ServerMessage(
                status=status,
                agent_name=session.current_round.agent.__class__.__name__,
                root_name=session.context.get(ContextNames.APPLICATION_ROOT_NAME),
                process_name=session.context.get(ContextNames.APPLICATION_PROCESS_NAME),
                actions=commands,
                session_id=session_id,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )
            return response.model_dump()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

    @router.get("/api/clients")
    async def list_clients():
        return {"online_clients": ws_manager.list_clients()}

    @router.post("/api/dispatch")
    async def dispatch_task_api(data: dict):
        import asyncio, json

        client_id = data["client_id"]
        task_content = data["request"]
        ws = ws_manager.get_client(client_id)
        if not ws:
            logger.error(f"Client {client_id} not online.")
            raise HTTPException(status_code=404, detail="Client not online")

        task_id = task_manager.new_task_id()
        ws_event_loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(
            ws.send_text(
                json.dumps(
                    {"type": "task", "task_id": task_id, "request": task_content}
                )
            ),
            ws_event_loop,
        )
        return {"status": "dispatched", "task_id": task_id}

    @router.get("/api/task_result/{task_id}")
    async def get_task_result(task_id: str):
        result = task_manager.get_result(task_id)
        if not result:
            return {"status": "pending"}
        return {"status": "done", "result": result}

    @router.get("/api/health")
    async def health_check():
        return {"status": "healthy", "online_clients": ws_manager.list_clients()}

    return router
