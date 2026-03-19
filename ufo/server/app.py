import argparse
import logging
import secrets
import sys


# Parse arguments FIRST before importing other modules
# This allows us to set up logging before any module initialization
def parse_args():
    parser = argparse.ArgumentParser(description="UFO Server")
    parser.add_argument("--port", type=int, default=5000, help="Flask API service port")
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="API service host (default: 127.0.0.1, use 0.0.0.0 only if remote access is intended)"
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        type=str,
        default=None,
        help="API key for authenticating HTTP and WebSocket requests. Auto-generated if not provided.",
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
from fastapi import FastAPI, WebSocket, Query
from starlette.status import WS_1008_POLICY_VIOLATION

from ufo.server.services.api import create_api_router
from ufo.server.services.session_manager import SessionManager
from ufo.server.services.client_connection_manager import ClientConnectionManager
from ufo.server.ws.handler import UFOWebSocketHandler


logger = logging.getLogger(__name__)

# Resolve API key: use provided key or generate one
_api_key = (cli_args.api_key if cli_args else None) or secrets.token_urlsafe(32)


# Initialize FastAPI app
app = FastAPI()

# Initialize managers with default platform (will be overridden if run directly)
session_manager = SessionManager(platform_override=None)
client_manager = ClientConnectionManager()


# Create API router for http requests
api_router = create_api_router(session_manager, client_manager, _api_key)
app.include_router(api_router)

# Initialize WebSocket handler
ws_handler = UFOWebSocketHandler(client_manager, session_manager, cli_args.local if cli_args else False)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(default=None)) -> None:
    """
    WebSocket endpoint for handling client connections.
    Requires a valid API key passed as the 'token' query parameter.
    :param websocket: The WebSocket connection.
    :param token: API key for authentication.
    """
    if not secrets.compare_digest(token or "", _api_key):
        await websocket.close(code=WS_1008_POLICY_VIOLATION, reason="Invalid or missing token")
        return
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

    # Update the module-level API key if specified via CLI
    if cli_args.api_key:
        _api_key = cli_args.api_key
    else:
        _api_key = secrets.token_urlsafe(32)

    # Rebuild the API router with the final key
    app.router.routes = [
        r for r in app.router.routes
        if not (hasattr(r, 'path') and getattr(r, 'path', '').startswith('/api/'))
    ]
    api_router = create_api_router(session_manager, client_manager, _api_key)
    app.include_router(api_router)

    logger.info(f"Starting UFO Server on {cli_args.host}:{cli_args.port}")
    logger.info(f"Platform: {cli_args.platform or 'auto-detected'}")
    logger.info(f"Log level: {cli_args.log_level}")
    print(f"\n** UFO Server API key: {_api_key}")
    print("** Pass this key as 'X-API-Key' header for HTTP requests and 'token' query param for WebSocket.\n")
    uvicorn.run(
        app,
        host=cli_args.host,
        port=cli_args.port,
        reload=False,
        ws_max_size=100 * 1024 * 1024,
    )
