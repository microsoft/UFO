# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Web UI Server.

FastAPI-based server that provides WebSocket communication for the Galaxy Web UI.
Integrates with the Galaxy event system to provide real-time updates.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from galaxy.core.events import get_event_bus
from galaxy.webui.websocket_observer import WebSocketObserver


# Global WebSocket observer instance
_websocket_observer: Optional[WebSocketObserver] = None
_galaxy_session = None
_galaxy_client = None
_request_counter = 0  # Counter for unique task names in Web UI mode


def _build_device_snapshot() -> Optional[Dict[str, Dict[str, Any]]]:
    """Construct a serializable snapshot of all known devices."""
    if not _galaxy_client:
        return None

    constellation_client = getattr(_galaxy_client, "_client", None)
    if not constellation_client:
        return None

    device_manager = getattr(constellation_client, "device_manager", None)
    if not device_manager:
        return None

    try:
        snapshot: Dict[str, Dict[str, Any]] = {}
        for device_id, device in device_manager.get_all_devices().items():
            snapshot[device_id] = {
                "device_id": device.device_id,
                "status": getattr(device.status, "value", str(device.status)),
                "os": device.os,
                "server_url": device.server_url,
                "capabilities": (
                    list(device.capabilities) if device.capabilities else []
                ),
                "metadata": dict(device.metadata) if device.metadata else {},
                "last_heartbeat": (
                    device.last_heartbeat.isoformat() if device.last_heartbeat else None
                ),
                "connection_attempts": device.connection_attempts,
                "max_retries": device.max_retries,
                "current_task_id": device.current_task_id,
            }
        return snapshot if snapshot else None
    except Exception as exc:  # pragma: no cover - defensive logging
        logging.getLogger(__name__).warning(
            "Failed to build device snapshot: %s", exc, exc_info=True
        )
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    global _websocket_observer

    # Startup
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Galaxy Web UI Server")
    print("🚀 Starting Galaxy Web UI Server")

    # Create and register WebSocket observer
    _websocket_observer = WebSocketObserver()
    event_bus = get_event_bus()
    event_bus.subscribe(_websocket_observer)

    logger.info(
        f"✅ WebSocket observer registered with event bus (observer: {_websocket_observer})"
    )
    print(f"✅ WebSocket observer registered with event bus")
    print(f"📊 Event bus has {len(event_bus._observers)} observers")

    yield

    # Shutdown
    logger.info("👋 Shutting down Galaxy Web UI Server")
    print("👋 Shutting down Galaxy Web UI Server")
    event_bus.unsubscribe(_websocket_observer)


# Create FastAPI app
app = FastAPI(
    title="Galaxy Web UI",
    description="Modern web interface for Galaxy Framework",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files if built
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
    logger = logging.getLogger(__name__)
    logger.info(f"Serving frontend from {frontend_dist}")


@app.get("/logo3.png")
async def logo():
    """Serve the logo file."""
    logo_path = Path(__file__).parent / "frontend" / "dist" / "logo3.png"
    if logo_path.exists():
        return FileResponse(logo_path, media_type="image/png")
    return HTMLResponse(content="Logo not found", status_code=404)


@app.get("/")
async def root():
    """Root endpoint that serves the web UI."""
    # Try to serve built React app first
    frontend_index = Path(__file__).parent / "frontend" / "dist" / "index.html"
    if frontend_index.exists():
        with open(frontend_index, "r", encoding="utf-8") as f:
            return HTMLResponse(
                content=f.read(),
                status_code=200,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )

    # Fallback to placeholder HTML
    return HTMLResponse(content=get_index_html(), status_code=200)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "connections": (
            _websocket_observer.connection_count if _websocket_observer else 0
        ),
        "events_sent": (
            _websocket_observer.total_events_sent if _websocket_observer else 0
        ),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming.

    Clients connect to this endpoint to receive real-time Galaxy events.
    """
    await websocket.accept()
    logger = logging.getLogger(__name__)
    logger.info(f"WebSocket connection established from {websocket.client}")

    # Add connection to observer
    if _websocket_observer:
        _websocket_observer.add_connection(websocket)

    try:
        # Send welcome message
        await websocket.send_json(
            {
                "type": "welcome",
                "message": "Connected to Galaxy Web UI",
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

        # Send an initial device snapshot so the UI can render current state immediately
        device_snapshot = _build_device_snapshot()
        if device_snapshot:
            await websocket.send_json(
                {
                    "event_type": "device_snapshot",
                    "source_id": "webui.server",
                    "timestamp": time.time(),
                    "data": {
                        "event_name": "device_snapshot",
                        "device_count": len(device_snapshot),
                    },
                    "all_devices": device_snapshot,
                }
            )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                await handle_client_message(websocket, data)
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error receiving WebSocket message: {e}")
                break

    finally:
        # Remove connection from observer
        if _websocket_observer:
            _websocket_observer.remove_connection(websocket)
        logger.info("WebSocket connection closed")


async def handle_client_message(websocket: WebSocket, data: dict):
    """
    Handle messages from WebSocket clients.

    :param websocket: The WebSocket connection
    :param data: The message data
    """
    global _request_counter

    logger = logging.getLogger(__name__)
    message_type = data.get("type")

    logger.info(f"Received message - Type: {message_type}, Full data: {data}")

    if message_type == "ping":
        # Respond to ping
        await websocket.send_json(
            {"type": "pong", "timestamp": asyncio.get_event_loop().time()}
        )

    elif message_type == "request":
        # Handle user request to start a Galaxy session
        request_text = data.get("text", "")
        logger.info(f"Received request: {request_text}")

        if _galaxy_client:
            # Send immediate acknowledgment
            await websocket.send_json(
                {
                    "type": "request_received",
                    "request": request_text,
                    "status": "processing",
                }
            )

            # Process request in background
            async def process_in_background():
                global _request_counter
                try:
                    # Increment counter and update task_name for this request
                    _request_counter += 1
                    base_task_name = (
                        _galaxy_client.task_name.rsplit("_", 1)[0]
                        if "_" in _galaxy_client.task_name
                        else _galaxy_client.task_name
                    )
                    _galaxy_client.task_name = f"{base_task_name}_{_request_counter}"

                    logger.info(
                        f"🚀 Starting to process request {_request_counter}: {request_text}"
                    )
                    result = await _galaxy_client.process_request(request_text)
                    logger.info(f"✅ Request processing completed")
                    await websocket.send_json(
                        {
                            "type": "request_completed",
                            "request": request_text,
                            "status": "completed",
                            "result": str(result),
                        }
                    )
                except Exception as e:
                    logger.error(f"❌ Error processing request: {e}", exc_info=True)
                    await websocket.send_json(
                        {
                            "type": "request_failed",
                            "request": request_text,
                            "status": "failed",
                            "error": str(e),
                        }
                    )

            # Start background task
            asyncio.create_task(process_in_background())
        else:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": "Galaxy client not initialized",
                }
            )

    elif message_type == "reset":
        # Handle session reset
        logger.info("Received reset request")

        if _galaxy_client:
            try:
                result = await _galaxy_client.reset_session()

                # Reset request counter on session reset
                _request_counter = 0

                await websocket.send_json(
                    {
                        "type": "reset_acknowledged",
                        "status": result.get("status", "success"),
                        "message": result.get("message", "Session reset"),
                        "timestamp": result.get("timestamp"),
                    }
                )
                logger.info(f"✅ Session reset completed: {result.get('message')}")
            except Exception as e:
                logger.error(f"Failed to reset session: {e}", exc_info=True)
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"Failed to reset session: {str(e)}",
                    }
                )
        else:
            await websocket.send_json(
                {
                    "type": "reset_acknowledged",
                    "status": "warning",
                    "message": "No active client to reset",
                }
            )

    elif message_type == "next_session":
        # Handle next session creation
        logger.info("Received next_session request")

        if _galaxy_client:
            try:
                result = await _galaxy_client.create_next_session()
                await websocket.send_json(
                    {
                        "type": "next_session_acknowledged",
                        "status": result.get("status", "success"),
                        "message": result.get("message", "Next session created"),
                        "session_name": result.get("session_name"),
                        "task_name": result.get("task_name"),
                        "timestamp": result.get("timestamp"),
                    }
                )
                logger.info(f"✅ Next session created: {result.get('session_name')}")
            except Exception as e:
                logger.error(f"Failed to create next session: {e}", exc_info=True)
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"Failed to create next session: {str(e)}",
                    }
                )
        else:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": "Galaxy client not initialized",
                }
            )

    elif message_type == "stop_task":
        # Handle task stop/cancel - shutdown client to clean up device tasks, then restart
        logger.info("Received stop_task request")

        if _galaxy_client:
            try:
                # Shutdown the galaxy client to properly clean up device agent tasks
                logger.info(
                    "🛑 Shutting down Galaxy client to clean up device tasks..."
                )
                await _galaxy_client.shutdown()
                logger.info("✅ Galaxy client shutdown completed")

                # Reinitialize the client to restore device connections
                logger.info("🔄 Reinitializing Galaxy client...")
                await _galaxy_client.initialize()
                logger.info("✅ Galaxy client reinitialized")

                # Reset request counter on stop
                _request_counter = 0

                # Create a new session
                new_session_result = await _galaxy_client.create_next_session()
                logger.info(f"✅ New session created: {new_session_result}")

                await websocket.send_json(
                    {
                        "type": "stop_acknowledged",
                        "status": "success",
                        "message": "Task stopped and client restarted",
                        "session_name": new_session_result.get("session_name"),
                        "timestamp": time.time(),
                    }
                )
            except Exception as e:
                logger.error(
                    f"Failed to stop task and restart client: {e}", exc_info=True
                )
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"Failed to stop task: {str(e)}",
                    }
                )
        else:
            logger.warning("No active galaxy client to stop")
            await websocket.send_json(
                {
                    "type": "stop_acknowledged",
                    "status": "warning",
                    "message": "No active task to stop",
                    "timestamp": time.time(),
                }
            )

    else:
        logger.warning(f"Unknown message type: {message_type}")
        await websocket.send_json(
            {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
            }
        )


def get_index_html() -> str:
    """
    Get the HTML content for the main UI page.

    For now, returns a simple HTML page. In production, this would serve
    the built React application.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Galaxy Web UI</title>
        <style>
            body {
                margin: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0a0e27 0%, #1a1a2e 50%, #16213e 100%);
                color: #e0e0e0;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }
            .container {
                text-align: center;
                padding: 2rem;
                max-width: 800px;
            }
            h1 {
                font-size: 3rem;
                background: linear-gradient(45deg, #00d4ff, #7b2cbf, #ff006e);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 1rem;
            }
            .subtitle {
                font-size: 1.2rem;
                color: #a0a0a0;
                margin-bottom: 2rem;
            }
            .status {
                padding: 1rem;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            .status-dot {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: #00ff00;
                animation: pulse 2s infinite;
                margin-right: 8px;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            a {
                color: #00d4ff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌌 Galaxy Web UI</h1>
            <p class="subtitle">Weaving the Digital Agent Galaxy</p>
            <div class="status">
                <span class="status-dot"></span>
                <span>Server is running</span>
            </div>
            <p style="margin-top: 2rem; color: #808080;">
                Frontend React application will be served here.<br>
                WebSocket endpoint: <code style="color: #00d4ff;">ws://localhost:8000/ws</code>
            </p>
            <p style="margin-top: 1rem;">
                <a href="/health">Health Check</a>
            </p>
        </div>
    </body>
    </html>
    """


def set_galaxy_session(session):
    """
    Set the Galaxy session for the web UI.

    :param session: The GalaxySession instance
    """
    global _galaxy_session
    _galaxy_session = session


def set_galaxy_client(client):
    """
    Set the Galaxy client for the web UI.

    :param client: The GalaxyClient instance
    """
    global _galaxy_client
    _galaxy_client = client


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Start the Galaxy Web UI server.

    :param host: Host to bind to
    :param port: Port to listen on
    """
    import uvicorn

    logger = logging.getLogger(__name__)
    logger.info(f"Starting Galaxy Web UI server on {host}:{port}")

    uvicorn.run(app, host=host, port=port, log_level="info")
