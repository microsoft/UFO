import argparse
import logging

import uvicorn
from fastapi import FastAPI, WebSocket

from ufo.logging.setup import setup_logger
from ufo.server.services.api import create_api_router
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.ws_manager import WSManager
from ufo.server.ws.handler import UFOWebSocketHandler


parser = argparse.ArgumentParser(description="UFO Server")
parser.add_argument("--port", type=int, default=5000, help="Flask API service port")
parser.add_argument(
    "--host", type=str, default="0.0.0.0", help="Flask API service host"
)
parser.add_argument(
    "--log-level",
    dest="log_level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL, OFF). Use OFF to disable logs (default: INFO)",
)
args = parser.parse_args()


setup_logger(args.log_level)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    :return: Configured FastAPI application.
    """
    app = FastAPI()

    # Initialize managers
    session_manager = SessionManager()
    ws_manager = WSManager()

    # Create API router for http requests
    api_router = create_api_router(session_manager, ws_manager)
    app.include_router(api_router)

    # Initialize WebSocket handler
    ws_handler = UFOWebSocketHandler(ws_manager, session_manager)

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for handling client connections."""
        await ws_handler.handler(websocket)

    return app


def main():
    """
    Main entry point for starting the FastAPI app with Uvicorn.
    """
    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port, reload=True)


if __name__ == "__main__":

    main()
