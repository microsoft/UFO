"""
Tests for Galaxy WebUI WebSocket Server.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from galaxy.webui.server import app, set_galaxy_client


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_health_endpoint(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "connections" in data
    assert "events_sent" in data


def test_root_endpoint(test_client):
    """Test the root endpoint returns HTML."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Should contain either built React app or placeholder
    assert "Galaxy" in response.text


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection establishment."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            # Should receive welcome message
            data = websocket.receive_json()
            assert data["type"] == "welcome"
            assert "Connected to Galaxy Web UI" in data["message"]


@pytest.mark.asyncio
async def test_websocket_ping_pong():
    """Test WebSocket ping/pong mechanism."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            # Receive welcome message
            websocket.receive_json()

            # Send ping
            websocket.send_json({"type": "ping"})

            # Should receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
            assert "timestamp" in response


@pytest.mark.asyncio
async def test_websocket_request_without_client():
    """Test sending request when Galaxy client is not set."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            # Receive welcome message
            websocket.receive_json()

            # Send request without Galaxy client
            websocket.send_json({"type": "request", "text": "Test request"})

            # Should receive error
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "not initialized" in response["message"]


@pytest.mark.asyncio
async def test_websocket_request_with_client():
    """Test sending request with Galaxy client set."""
    # Create mock Galaxy client
    mock_client = Mock()
    mock_client.process_request = AsyncMock(return_value={"status": "success"})

    # Set the mock client
    set_galaxy_client(mock_client)

    try:
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Receive welcome message
                websocket.receive_json()

                # Send request
                websocket.send_json({"type": "request", "text": "Test request"})

                # Should receive completion
                response = websocket.receive_json()
                assert response["type"] == "request_completed"
                assert response["status"] == "completed"
                assert "result" in response

                # Verify client was called
                mock_client.process_request.assert_called_once_with("Test request")
    finally:
        # Clean up
        set_galaxy_client(None)


@pytest.mark.asyncio
async def test_websocket_reset():
    """Test reset message handling."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            # Receive welcome message
            websocket.receive_json()

            # Send reset
            websocket.send_json({"type": "reset"})

            # Should receive acknowledgment
            response = websocket.receive_json()
            assert response["type"] == "reset_acknowledged"
            assert response["status"] == "ready"


@pytest.mark.asyncio
async def test_websocket_unknown_message():
    """Test handling of unknown message types."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            # Receive welcome message
            websocket.receive_json()

            # Send unknown message type
            websocket.send_json({"type": "unknown_type"})

            # Should receive error
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Unknown message type" in response["message"]


def test_static_file_serving(test_client):
    """Test that static files are served if frontend is built."""
    # This test will pass whether frontend is built or not
    # If built, assets should be accessible
    # If not built, should still not crash
    response = test_client.get("/")
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
