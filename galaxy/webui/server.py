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
from datetime import datetime
from typing import Any, Dict, Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
import yaml

from galaxy.core.events import get_event_bus
from galaxy.webui.websocket_observer import WebSocketObserver


# Pydantic models for API
class DeviceAddRequest(BaseModel):
    """Request model for adding a new device."""

    device_id: str
    server_url: str
    os: str
    capabilities: List[str]
    metadata: Optional[Dict[str, Any]] = None
    auto_connect: Optional[bool] = True
    max_retries: Optional[int] = 5


# Global WebSocket observer instance
_websocket_observer: Optional[WebSocketObserver] = None
# Global Galaxy session and client instances
_galaxy_session: Optional[Any] = None
_galaxy_client: Optional[Any] = None
# Counter for unique task names in Web UI mode
_request_counter: int = 0


def _build_device_snapshot() -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Construct a serializable snapshot of all known devices.

    Retrieves device information from the Galaxy client's device manager
    and formats it for transmission to the frontend.

    :return: Dictionary mapping device IDs to device information, or None if unavailable
    """
    if not _galaxy_client:
        return None

    # Get constellation client from Galaxy client
    constellation_client = getattr(_galaxy_client, "_client", None)
    if not constellation_client:
        return None

    # Get device manager from constellation client
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
    """
    Lifespan context manager for FastAPI application.

    Handles startup and shutdown logic including:
    - Creating and registering the WebSocket observer on startup
    - Unsubscribing the observer on shutdown

    :param app: The FastAPI application instance
    """
    global _websocket_observer

    # Startup phase
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Galaxy Web UI Server")
    print("🚀 Starting Galaxy Web UI Server")

    # Create and register WebSocket observer with event bus
    _websocket_observer = WebSocketObserver()
    event_bus = get_event_bus()
    event_bus.subscribe(_websocket_observer)

    logger.info(
        f"✅ WebSocket observer registered with event bus (observer: {_websocket_observer})"
    )
    print(f"✅ WebSocket observer registered with event bus")
    print(f"📊 Event bus has {len(event_bus._observers)} observers")

    yield

    # Shutdown phase
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
async def logo() -> FileResponse:
    """
    Serve the logo file.

    :return: FileResponse containing the logo image, or 404 if not found
    """
    logo_path: Path = Path(__file__).parent / "frontend" / "dist" / "logo3.png"
    if logo_path.exists():
        return FileResponse(logo_path, media_type="image/png")
    return HTMLResponse(content="Logo not found", status_code=404)


@app.get("/")
async def root() -> HTMLResponse:
    """
    Root endpoint that serves the web UI.

    Attempts to serve the built React application if available,
    otherwise returns a placeholder HTML page.

    :return: HTMLResponse containing the web UI or placeholder
    """
    # Try to serve built React app first
    frontend_index: Path = Path(__file__).parent / "frontend" / "dist" / "index.html"
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
async def health() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns the current status of the server including connection count
    and total events sent.

    :return: Dictionary containing health status information
    """
    return {
        "status": "healthy",
        "connections": (
            _websocket_observer.connection_count if _websocket_observer else 0
        ),
        "events_sent": (
            _websocket_observer.total_events_sent if _websocket_observer else 0
        ),
    }


@app.post("/api/devices")
async def add_device(device: DeviceAddRequest) -> Dict[str, Any]:
    """
    Add a new device to the configuration.

    Validates the device data, checks for conflicts, saves to devices.yaml,
    and triggers device manager to connect the new device.

    :param device: Device configuration data
    :return: Success message with device info
    :raises HTTPException: If validation fails or device_id conflicts
    """
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info(f"Received request to add device: {device.device_id}")

    # Path to devices.yaml
    config_path = Path("config/galaxy/devices.yaml")
    if not config_path.exists():
        raise HTTPException(status_code=500, detail="devices.yaml not found")

    try:
        # Load existing configuration
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        # Ensure devices list exists
        if "devices" not in config_data:
            config_data["devices"] = []

        # Check for device_id conflict
        existing_ids = [
            d.get("device_id") for d in config_data["devices"] if isinstance(d, dict)
        ]
        if device.device_id in existing_ids:
            raise HTTPException(
                status_code=409, detail=f"Device ID '{device.device_id}' already exists"
            )

        # Create new device entry
        new_device = {
            "device_id": device.device_id,
            "server_url": device.server_url,
            "os": device.os,
            "capabilities": device.capabilities,
            "auto_connect": device.auto_connect,
            "max_retries": device.max_retries,
        }

        # Add metadata if provided
        if device.metadata:
            new_device["metadata"] = device.metadata

        # Append new device to configuration
        config_data["devices"].append(new_device)

        # Save updated configuration
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                config_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        logger.info(f"✅ Device '{device.device_id}' added to configuration")

        # Attempt to connect the device via device manager
        if _galaxy_client:
            constellation_client = getattr(_galaxy_client, "_client", None)
            if constellation_client:
                device_manager = getattr(constellation_client, "device_manager", None)
                if device_manager:
                    try:
                        # Register the device with device manager
                        device_manager.device_registry.register_device(
                            device_id=device.device_id,
                            server_url=device.server_url,
                            os=device.os,
                            capabilities=device.capabilities,
                            metadata=device.metadata or {},
                            max_retries=device.max_retries,
                        )
                        logger.info(
                            f"✅ Device '{device.device_id}' registered with device manager"
                        )

                        # If auto_connect is enabled, try to connect
                        if device.auto_connect:
                            asyncio.create_task(
                                device_manager.connect_device(device.device_id)
                            )
                            logger.info(
                                f"🔄 Initiated connection for device '{device.device_id}'"
                            )
                    except Exception as e:
                        logger.warning(
                            f"⚠️ Failed to register/connect device with manager: {e}"
                        )

        return {
            "status": "success",
            "message": f"Device '{device.device_id}' added successfully",
            "device": new_device,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding device: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add device: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time event streaming.

    Clients connect to this endpoint to receive real-time Galaxy events.
    The endpoint handles:
    - Sending welcome messages and initial device snapshots
    - Processing incoming client messages
    - Broadcasting events to all connected clients

    :param websocket: The WebSocket connection from the client
    """
    await websocket.accept()
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info(f"WebSocket connection established from {websocket.client}")

    # Add connection to observer for event broadcasting
    if _websocket_observer:
        _websocket_observer.add_connection(websocket)

    try:
        # Send welcome message to client
        await websocket.send_json(
            {
                "type": "welcome",
                "message": "Connected to Galaxy Web UI",
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

        # Send an initial device snapshot so the UI can render current state immediately
        device_snapshot: Optional[Dict[str, Dict[str, Any]]] = _build_device_snapshot()
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
                data: dict = await websocket.receive_json()
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


async def handle_client_message(websocket: WebSocket, data: dict) -> None:
    """
    Handle messages from WebSocket clients.

    Processes different message types including:
    - ping: Health check ping-pong
    - request: Process user request to start a Galaxy session
    - reset: Reset the current session
    - next_session: Create a new session
    - stop_task: Stop current task execution

    :param websocket: The WebSocket connection
    :param data: The message data from client
    """
    global _request_counter

    logger: logging.Logger = logging.getLogger(__name__)
    message_type: Optional[str] = data.get("type")

    logger.info(f"Received message - Type: {message_type}, Full data: {data}")

    if message_type == "ping":
        # Respond to ping with pong
        await websocket.send_json(
            {"type": "pong", "timestamp": asyncio.get_event_loop().time()}
        )

    elif message_type == "request":
        # Handle user request to start a Galaxy session
        request_text: str = data.get("text", "")
        logger.info(f"Received request: {request_text}")

        if _galaxy_client:
            # Send immediate acknowledgment to client
            await websocket.send_json(
                {
                    "type": "request_received",
                    "request": request_text,
                    "status": "processing",
                }
            )

            # Process request in background task
            async def process_in_background() -> None:
                global _request_counter
                try:
                    # Increment counter and update task_name for this request with timestamp
                    _request_counter += 1
                    timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    _galaxy_client.task_name = f"request_{timestamp}_{_request_counter}"

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

    Returns a placeholder HTML page with Galaxy branding.
    In production, this serves as a fallback when the React build is not available.

    :return: HTML string for the placeholder page
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


def set_galaxy_session(session: Any) -> None:
    """
    Set the Galaxy session for the web UI.

    :param session: The GalaxySession instance
    """
    global _galaxy_session
    _galaxy_session = session


def set_galaxy_client(client: Any) -> None:
    """
    Set the Galaxy client for the web UI.

    :param client: The GalaxyClient instance
    """
    global _galaxy_client
    _galaxy_client = client


def start_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """
    Start the Galaxy Web UI server.

    :param host: Host address to bind to (default: "0.0.0.0")
    :param port: Port number to listen on (default: 8000)
    """
    import uvicorn

    logger: logging.Logger = logging.getLogger(__name__)
    logger.info(f"Starting Galaxy Web UI server on {host}:{port}")

    uvicorn.run(app, host=host, port=port, log_level="info")
