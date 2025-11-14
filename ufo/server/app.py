import argparse
import logging
import sys


# Parse arguments FIRST before importing other modules
# This allows us to set up logging before any module initialization
def parse_args():
    parser = argparse.ArgumentParser(description="UFO Server")
    parser.add_argument("--port", type=int, default=5000, help="Flask API service port")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Flask API service host"
    )
    parser.add_argument(
        "--platform",
        type=str,
        default=None,
        choices=["windows", "linux", "mobile"],
        help="Platform override (windows, linux, or mobile). Auto-detected if not specified.",
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        default="WARNING",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL, OFF). Use OFF to disable logs (default: WARNING)",
    )
    parser.add_argument(
        "--local",
        dest="local",
        action="store_true",
        help="Run the server in local mode (default: False)",
    )
    return parser.parse_args()


# Parse arguments early (only when running with uvicorn, parse_args won't be called at import time)
# When running directly with python, it will be called in __main__ block
cli_args = None
if __name__ == "__main__":
    cli_args = parse_args()

# Setup logger before importing other UFO modules
if cli_args:
    from ufo.logging.setup import setup_logger

    setup_logger(cli_args.log_level)
else:
    # Default logging setup when imported by uvicorn
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

# Now import other modules after logging is configured
import uvicorn
from fastapi import FastAPI, WebSocket

from ufo.server.services.api import create_api_router
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.client_connection_manager import ClientConnectionManager
from ufo.server.ws.handler import UFOWebSocketHandler


logger = logging.getLogger(__name__)


# Initialize FastAPI app
app = FastAPI()

# Initialize managers with default platform (will be overridden if run directly)
session_manager = SessionManager(platform_override=None)
client_manager = ClientConnectionManager()


# Create API router for http requests
api_router = create_api_router(session_manager, client_manager)
app.include_router(api_router)

# Initialize WebSocket handler
ws_handler = UFOWebSocketHandler(client_manager, session_manager, cli_args.local)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for handling client connections.
    :param websocket: The WebSocket connection.
    """
    await ws_handler.handler(websocket)


if __name__ == "__main__":
    # Arguments already parsed at module level
    if cli_args is None:
        cli_args = parse_args()
        from ufo.logging.setup import setup_logger

        setup_logger(cli_args.log_level)

    # Update session manager with platform override if specified
    if cli_args.platform:
        session_manager._platform_override = cli_args.platform

    logger.info(f"Starting UFO Server on {cli_args.host}:{cli_args.port}")
    logger.info(f"Platform: {cli_args.platform or 'auto-detected'}")
    logger.info(f"Log level: {cli_args.log_level}")
    uvicorn.run(
        app,
        host=cli_args.host,
        port=cli_args.port,
        reload=False,
        ws_max_size=100 * 1024 * 1024,
    )
