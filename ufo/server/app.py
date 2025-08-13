import argparse
import asyncio
import logging

from ufo.server.services.api import create_api_router
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.task_manager import TaskManager
from ufo.server.services.ws_manager import WSManager
from ufo.server.ws.handler import UFOWebSocketHandler
from ufo.server.shared import SharedEventLoop
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn, json


def parse_args():
    parser = argparse.ArgumentParser(description="UFO Server")
    parser.add_argument("--port", type=int, default=5000, help="Flask API service port")
    return parser.parse_args()


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# app = Flask(__name__)

# Initialize FastAPI app
app = FastAPI()

# Initialize managers
session_manager = SessionManager()
task_manager = TaskManager()
ws_manager = WSManager()
shared_event_loop = SharedEventLoop()


# # Create API blueprint
# api_bp = create_api_blueprint(
#     session_manager, task_manager, ws_manager, shared_event_loop
# )
# app.register_blueprint(api_bp)

# Create API router
api_router = create_api_router(session_manager, task_manager, ws_manager)
app.include_router(api_router)

ws_handler = UFOWebSocketHandler(ws_manager, session_manager, task_manager)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = None
    try:
        reg_msg = await websocket.receive_text()
        reg_info = json.loads(reg_msg)
        client_id = reg_info.get("client_id")
        ws_handler.ws_manager.add_client(client_id, websocket)
        logger.info(f"[WS] {client_id} connected")

        while True:
            msg = await websocket.receive_text()
            await ws_handler.handle_message(msg, websocket, client_id)

    except WebSocketDisconnect:
        logger.info(f"[WS] {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"[WS] {client_id} error: {e}")
    finally:
        if client_id:
            ws_handler.ws_manager.remove_client(client_id)


def run_flask(port: int = 5000) -> None:
    """
    Run the Flask application on the specified port.
    :param port: Port number for the Flask application.
    """

    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)


def run_ws(port: int = 8765, ws_handler: UFOWebSocketHandler = ws_handler) -> None:
    """Run the WebSocket server on the specified port.
    This function initializes a new event loop and starts the WebSocket server.
    :param port: Port number for the WebSocket server.
    :param ws_handler: The WebSocket handler instance to handle incoming connections.
    """
    global ws_event_loop
    ws_event_loop = asyncio.new_event_loop()
    shared_event_loop.loop = ws_event_loop
    asyncio.set_event_loop(ws_event_loop)
    import websockets

    ws_server = websockets.serve(
        ws_handler,
        "0.0.0.0",
        port,
        ping_interval=100,
        ping_timeout=100,
    )
    ws_event_loop.run_until_complete(ws_server)
    logger.info(f"WebSocket server started on :0.0.0.0:{port}")
    ws_event_loop.run_forever()


if __name__ == "__main__":

    cli_args = parse_args()
    uvicorn.run(app, host="0.0.0.0", port=cli_args.port, reload=True)
