import argparse
import asyncio
import logging

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from ufo.contracts.contracts import ClientMessage, ClientMessageType
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


# Create API router
api_router = create_api_router(session_manager, ws_manager)
app.include_router(api_router)

ws_handler = UFOWebSocketHandler(ws_manager, session_manager)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = None
    try:
        reg_msg = await websocket.receive_text()
        reg_info = ClientMessage.model_validate_json(reg_msg)
        if not reg_info.client_id:
            raise ValueError("Client ID is required for WebSocket registration")

        if reg_info.type != ClientMessageType.REGISTER:
            raise ValueError("First message must be a registration message")

        client_id = reg_info.client_id
        ws_handler.ws_manager.add_client(client_id, websocket)
        logger.info(f"[WS] {client_id} connected")

        while True:
            msg = await websocket.receive_text()
            asyncio.create_task(ws_handler.handle_message(msg, websocket))

    except WebSocketDisconnect:
        logger.info(f"[WS] {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"[WS] {client_id} error: {e}")
    finally:
        if client_id:
            ws_handler.ws_manager.remove_client(client_id)


if __name__ == "__main__":

    cli_args = parse_args()
    uvicorn.run(app, host=cli_args.host, port=cli_args.port, reload=True)
