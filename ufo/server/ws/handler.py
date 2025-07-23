import json
import logging
from ufo.cs.contracts import UFORequest

logger = logging.getLogger(__name__)


async def ws_handler(websocket, path, ws_manager, session_manager, task_manager):
    reg_msg = await websocket.recv()
    reg_info = json.loads(reg_msg)
    client_id = reg_info.get("client_id", None)
    ws_manager.add_client(client_id, websocket)
    logger.info(f"[WS] {client_id} connected")

    try:
        async for msg in websocket:
            data = json.loads(msg)
            if data.get("type") == "task_request":
                req = UFORequest(**data["body"])
                try:
                    session_id = req.session_id
                    session = session_manager.get_or_create_session(
                        session_id, req.request
                    )
                    status = "continue"
                    try:
                        session.run_coro.send(None)
                    except StopIteration:
                        status = "completed"
                    actions = session.get_actions()

                    resp = {
                        "type": "task_response",
                        "body": {
                            "session_id": session_id,
                            "status": status,
                            "actions": actions,
                            "messages": [],
                        },
                    }
                    await websocket.send(json.dumps(resp))
                except Exception as e:
                    await websocket.send(
                        json.dumps({"type": "task_response", "error": str(e)})
                    )
            # Handle other message types as needed
    except Exception as e:
        logger.error(f"WS client {client_id} error: {e}")
    finally:
        ws_manager.remove_client(client_id)
