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
task_results = {}  # Dictionary to store task results
ws_event_loop = None
task_id_counter = 0  # Counter for task IDs


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
    Handles task requests from clients. If session_id is None, creates a new session.
    Otherwise, updates the existing session with action results.
    :return: JSON response with session_id, status, actions, and messages.
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


@app.route("/api/health")
def health_check():
    return jsonify({"status": "healthy", "online_clients": list(online_clients.keys())})


@app.route("/api/clients")
def list_clients():
    """
    List all online clients.
    :return: JSON response with a list of online client IDs.
    """
    return jsonify({"online_clients": list(online_clients.keys())})


@app.route("/api/dispatch", methods=["POST"])
def dispatch_task_api():
    """
    dispatch task to：POST {"client_id": "...", "request": "..."}
    :param request: The request containing client_id and task content.
    :return: JSON response indicating the status of the task dispatch.
    """
    global task_id_counter
    global ws_event_loop

    data = request.json
    client_id = data["client_id"]
    task_content = data["request"]
    if client_id not in online_clients:
        return jsonify({"error": "client not online"}), 404
    # generate a unique task ID
    task_id_counter += 1
    task_id = f"task_{task_id_counter}"
    # dispatch the task to the specified client
    ws = online_clients[client_id]
    asyncio.run_coroutine_threadsafe(
        ws.send(
            json.dumps({"type": "task", "task_id": task_id, "request": task_content})
        ),
        ws_event_loop,
    )
    return jsonify({"status": "dispatched", "task_id": task_id})


@app.route("/api/task_result/<task_id>")
def get_task_result(task_id: str):
    """Retrieve the result of a task by its ID.
    This endpoint checks if the task has been completed and returns the result if available.
    :param task_id: The ID of the task to retrieve the result for.
    :return: JSON response with task status and result if available.
    """
    if task_id not in task_results:
        return jsonify({"status": "pending"})
    return jsonify({"status": "done", "result": task_results[task_id]})


async def ws_handler(websocket: websockets.WebSocketServerProtocol, path: str):
    """
    WebSocket handler for managing client connections and task requests.
    :param websocket: The WebSocket connection object.
    :param path: The path of the WebSocket connection.
    """
    # Receive registration message at the first connection
    reg_msg = await websocket.recv()
    reg_info = json.loads(reg_msg)
    client_id = reg_info.get("client_id", None)
    online_clients[client_id] = websocket
    logger.info(f"[WS] {client_id} connected")

    try:
        async for msg in websocket:
            data = json.loads(msg)
            # If the message is a task request, process it
            if data.get("type") == "task_request":
                # Extract the request data
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
            # Handle other message types as needed
    except Exception as e:
        logger.error(f"WS client {client_id} error: {e}")
    finally:
        online_clients.pop(client_id, None)


# def run_ws():
#     global ws_event_loop
#     ws_event_loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(ws_event_loop)
#     ws_server = websockets.serve(
#         ws_handler, "0.0.0.0", 8765, ping_interval=100, ping_timeout=100
#     )
#     ws_event_loop.run_until_complete(ws_server)
#     print("WebSocket server started on :8765")
#     ws_event_loop.run_forever()


def run_ws():
    """
    Run the WebSocket server in a separate event loop. The port is fixed at 8765.
    This function initializes a new event loop and starts the WebSocket server.
    """
    global ws_event_loop
    ws_event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ws_event_loop)

    async def start_ws_server():
        await websockets.serve(
            ws_handler, "0.0.0.0", 8765, ping_interval=100, ping_timeout=100
        )
        print("WebSocket server started on Localhost:8765")
        await asyncio.Future()  # keep running

    try:
        ws_event_loop.run_until_complete(start_ws_server())
    except Exception as e:
        logger.error(f"Error starting WebSocket server: {e}")
    finally:
        ws_event_loop.close()


def run_flask():
    """
    Run the Flask web service.
    This function starts the Flask application on port 5000.
    """
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)


if __name__ == "__main__":
    # start the Flask server and WebSocket server in separate threads
    t1 = threading.Thread(target=run_flask, daemon=True)
    t1.start()
    run_ws()
