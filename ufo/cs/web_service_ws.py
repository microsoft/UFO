import asyncio
import json
import logging
import threading
from typing import Dict
from uuid import uuid4

import websockets
from flask import Flask, jsonify, request
from ufo.config import Config
from ufo.cs.contracts import UFORequest, UFOResponse
from ufo.cs.service_session import ServiceSession

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get application configuration
configs = Config.get_instance().config_data

# Dictionary to store active sessions
sessions: Dict[str, ServiceSession] = {}

online_clients = {}
task_results = {}  # 存任务执行结果
ws_event_loop = None
task_id_counter = 0  # 自增任务ID


def run_task_core(data: UFORequest):
    """
    Core logic for running a task based on the request data.
    This function is called by the run_task endpoint.
    :param data: UFORequest object containing session_id and request text.
    :return: UFOResponse object containing session_id, status, actions, and messages.
    """
    session_id = data.session_id

    if session_id is None or session_id not in sessions:
        # Create a new session if it doesn't exist
        session_id = str(uuid4())
        if data.request:
            logger.info(
                f"Session {session_id} initialized with request: {data.request}"
            )

        session = ServiceSession(
            task=session_id,
            should_evaluate=False,
            id=session_id,
            request=data.request,
        )
        sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")

    else:
        # Retrieve existing session
        session = sessions[session_id]
        # Update session state with action results
        if data.action_results:
            session.update_session_state_from_action_results(data.action_results)
            logger.info(f"Updated session {session_id} with action results")

    # Process the request and get actions
    status = "continue"
    try:
        session.run_coro.send(None)
    except StopIteration:
        status = "completed"

    actions = session.get_actions()

    response = UFOResponse(
        session_id=session_id,
        status=status,
        actions=actions,
        messages=[],  # Can add custom messages if needed
    )

    logger.info(f"Session {session_id} status: {status}, Actions: {len(actions)}")
    logger.info(f"Response: {response.model_dump()}")

    return response


@app.route("/api/ufo/task", methods=["POST"])
def run_task():
    """
    Handles task requests from clients.

    If session_id is None, creates a new session.
    Otherwise, updates the existing session with action results.

    Returns actions for the client to execute.
    """

    try:
        # Parse the request data
        data = request.json
        ufo_request = UFORequest(**data)

        # Run the core task logic
        response = run_task_core(ufo_request)

        return jsonify(response.model_dump())

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({"status": "failure", "error": f"Server error: {str(e)}"}), 500


# @app.route("/api/health", methods=["GET"])
# def health_check():
#     """Simple health check endpoint"""
#     return jsonify({"status": "healthy", "active_sessions": len(sessions)}), 200


@app.route("/api/health")
def health_check():
    return jsonify({"status": "healthy", "online_clients": list(online_clients.keys())})


@app.route("/api/clients")
def list_clients():
    return jsonify({"online_clients": list(online_clients.keys())})


@app.route("/api/dispatch", methods=["POST"])
def dispatch_task_api():
    """
    dispatch task to：POST {"client_id": "...", "request": "..."}
    """
    global task_id_counter
    global ws_event_loop

    data = request.json
    client_id = data["client_id"]
    task_content = data["request"]
    if client_id not in online_clients:
        return jsonify({"error": "client not online"}), 404
    # 生成唯一任务id
    task_id_counter += 1
    task_id = f"task_{task_id_counter}"
    # 通过WebSocket下发任务（关键改动）
    ws = online_clients[client_id]
    asyncio.run_coroutine_threadsafe(
        ws.send(
            json.dumps({"type": "task", "task_id": task_id, "request": task_content})
        ),
        ws_event_loop,
    )
    return jsonify({"status": "dispatched", "task_id": task_id})


@app.route("/api/task_result/<task_id>")
def get_task_result(task_id):
    if task_id not in task_results:
        return jsonify({"status": "pending"})
    return jsonify({"status": "done", "result": task_results[task_id]})


async def ws_handler(websocket, path):
    # Receive registration message at the first connection
    reg_msg = await websocket.recv()
    reg_info = json.loads(reg_msg)
    client_id = reg_info.get("client_id", None)
    online_clients[client_id] = websocket
    logger.info(f"[WS] {client_id} connected")

    try:
        async for msg in websocket:
            data = json.loads(msg)
            # 假设data里有 type/请求体
            if data.get("type") == "task_request":
                # 用UFORequest模型反序列化
                req = UFORequest(**data["body"])
                try:
                    resp = run_task_core(req)
                    await websocket.send(
                        json.dumps({"type": "task_response", "body": resp.model_dump()})
                    )
                except Exception as e:
                    await websocket.send(
                        json.dumps({"type": "task_response", "error": str(e)})
                    )
            # 你可以扩展其它消息类型，如action结果回传等
    except Exception as e:
        logger.error(f"WS client {client_id} error: {e}")
    finally:
        online_clients.pop(client_id, None)


def run_ws():
    global ws_event_loop
    ws_event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ws_event_loop)
    ws_server = websockets.serve(ws_handler, "0.0.0.0", 8765)
    ws_event_loop.run_until_complete(ws_server)
    print("WebSocket server started on :8765")
    ws_event_loop.run_forever()


def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)


def start_server(host="0.0.0.0", port=5000, debug=False):
    """Start the Flask server"""
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    # start the Flask server and WebSocket server in separate threads
    t1 = threading.Thread(target=run_flask, daemon=True)
    t1.start()
    run_ws()

# Old code for running Flask server
# if __name__ == "__main__":
#     # Default to running on localhost:5000
#     start_server(debug=True)
