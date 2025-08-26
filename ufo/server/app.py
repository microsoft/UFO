import argparse
import logging

import uvicorn
from fastapi import FastAPI, WebSocket

from ufo.server.services.api import create_api_router
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.ws_manager import WSManager
from ufo.server.ws.handler import UFOWebSocketHandler


def parse_args():
    parser = argparse.ArgumentParser(description="UFO Server")
    parser.add_argument("--port", type=int, default=5000, help="Flask API service port")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Flask API service host"
    )
    return parser.parse_args()


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Initialize FastAPI app
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
    """
    WebSocket endpoint for handling client connections.
    :param websocket: The WebSocket connection.
    """
    await ws_handler.handler(websocket)


if __name__ == "__main__":

    cli_args = parse_args()
    uvicorn.run(app, host=cli_args.host, port=cli_args.port, reload=True)
