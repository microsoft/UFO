# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Web UI Server.

FastAPI-based server that provides WebSocket communication for the Galaxy Web UI.
Integrates with the Galaxy event system to provide real-time updates.

This is the refactored version with improved architecture:
- Pydantic models and enums in separate modules
- Business logic separated into services
- Routers for endpoint organization
- Dependency injection for state management
"""

import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from galaxy.core.events import get_event_bus
from galaxy.webui.dependencies import get_app_state
from galaxy.webui.routers import health_router, devices_router, websocket_router
from galaxy.webui.websocket_observer import WebSocketObserver

if TYPE_CHECKING:
    from galaxy.galaxy_client import GalaxyClient
    from galaxy.session.galaxy_session import GalaxySession


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.

    Handles startup and shutdown logic including:
    - Creating and registering the WebSocket observer on startup
    - Unsubscribing the observer on shutdown

    :param app: The FastAPI application instance
    """
    # Startup phase
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Galaxy Web UI Server")
    print("🚀 Starting Galaxy Web UI Server")

    # Get application state
    app_state = get_app_state()

    # Generate API key if not already set (e.g. via start_server)
    if not app_state.api_key:
        app_state.api_key = secrets.token_urlsafe(32)

    logger.info("🔑 Galaxy WebUI API key: %s", app_state.api_key)
    print(f"🔑 Galaxy WebUI API key: {app_state.api_key}")

    # Create and register WebSocket observer with event bus
    websocket_observer = WebSocketObserver()
    app_state.websocket_observer = websocket_observer

    event_bus = get_event_bus()
    event_bus.subscribe(websocket_observer)

    logger.info(
        f"✅ WebSocket observer registered with event bus (observer: {websocket_observer})"
    )
    print(f"✅ WebSocket observer registered with event bus")
    print(f"📊 Event bus has {len(event_bus._observers)} observers")

    yield

    # Shutdown phase
    logger.info("👋 Shutting down Galaxy Web UI Server")
    print("👋 Shutting down Galaxy Web UI Server")
    event_bus.unsubscribe(websocket_observer)


# Create FastAPI app with lifespan management
app = FastAPI(
    title="Galaxy Web UI",
    description="Modern web interface for Galaxy Framework",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware with restricted origins
_allowed_origins = os.environ.get(
    "GALAXY_CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for different endpoint groups
app.include_router(health_router)
app.include_router(devices_router)
app.include_router(websocket_router)

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
    otherwise returns a placeholder HTML page from templates.

    :return: HTMLResponse containing the web UI or placeholder
    """
    # Try to serve built React app first
    frontend_index: Path = Path(__file__).parent / "frontend" / "dist" / "index.html"
    if frontend_index.exists():
        with open(frontend_index, "r", encoding="utf-8") as f:
            content = f.read()

        # Inject API key so the frontend can authenticate WS and HTTP requests
        app_state = get_app_state()
        api_key = app_state.api_key or ""
        api_key_script = (
            f'<script>window.__GALAXY_API_KEY__="{api_key}";</script>'
        )
        content = content.replace("</head>", f"{api_key_script}</head>", 1)

        return HTMLResponse(
            content=content,
                status_code=200,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )

    # Fallback to placeholder HTML from templates
    template_path: Path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)

    # Ultimate fallback if template file doesn't exist
    return HTMLResponse(
        content="<h1>Galaxy Web UI</h1><p>Server is running</p>", status_code=200
    )


def set_galaxy_session(session: "GalaxySession") -> None:
    """
    Set the Galaxy session for the web UI.

    :param session: The GalaxySession instance
    """
    app_state = get_app_state()
    app_state.galaxy_session = session


def set_galaxy_client(client: "GalaxyClient") -> None:
    """
    Set the Galaxy client for the web UI.

    :param client: The GalaxyClient instance
    """
    app_state = get_app_state()
    app_state.galaxy_client = client


def start_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    api_key: Optional[str] = None,
) -> None:
    """
    Start the Galaxy Web UI server.

    :param host: Host address to bind to (default: "127.0.0.1")
    :param port: Port number to listen on (default: 8000)
    :param api_key: API key for authenticating requests. Auto-generated if not provided.
    """
    import uvicorn

    # Set API key before starting the server so lifespan picks it up
    app_state = get_app_state()
    app_state.api_key = api_key or secrets.token_urlsafe(32)

    logger: logging.Logger = logging.getLogger(__name__)
    logger.info(f"Starting Galaxy Web UI server on {host}:{port}")

    uvicorn.run(app, host=host, port=port, log_level="info")
