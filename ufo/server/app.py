import argparse
import asyncio
import logging
import threading

from flask import Flask
from ufo.server.services.api import create_api_blueprint
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.task_manager import TaskManager
from ufo.server.services.ws_manager import WSManager
from ufo.server.ws.handler import UFOWebSocketHandler
from ufo.server.shared import SharedEventLoop


def parse_args():
    parser = argparse.ArgumentParser(description="UFO Server")
    parser.add_argument(
        "--flask-port", type=int, default=5000, help="Flask API service port"
    )
    parser.add_argument(
        "--ws-port", type=int, default=8765, help="WebSocket service port"
    )
    return parser.parse_args()


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize managers
session_manager = SessionManager()
task_manager = TaskManager()
ws_manager = WSManager()
shared_event_loop = SharedEventLoop()


# Create API blueprint
api_bp = create_api_blueprint(
    session_manager, task_manager, ws_manager, shared_event_loop
)
app.register_blueprint(api_bp)

ws_handler = UFOWebSocketHandler(ws_manager, session_manager, task_manager)


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
    flask_thread = threading.Thread(
        target=run_flask, args=(cli_args.flask_port,), daemon=True
    )

    # Start the Flask server in a separate thread
    flask_thread.start()

    # Start the WebSocket server
    run_ws(cli_args.ws_port, ws_handler)
