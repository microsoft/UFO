#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Integration tests for WebUI stop_task_and_restart functionality.

Tests the complete flow from WebUI Stop button through to Galaxy client restart.
"""

import asyncio
import pytest
import pytest_asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
UFO_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(UFO_ROOT))

from galaxy.webui.services.galaxy_service import GalaxyService
from galaxy.webui.dependencies import AppState
from galaxy.galaxy_client import GalaxyClient


@pytest_asyncio.fixture
async def mock_app_state():
    """Create a mock AppState with GalaxyClient for testing."""
    app_state = AppState()

    with patch("galaxy.galaxy_client.get_galaxy_config"), patch(
        "galaxy.galaxy_client.ConstellationConfig"
    ), patch("galaxy.galaxy_client.setup_logger"):

        # Create a mock Galaxy client
        client = GalaxyClient(
            session_name="webui_test_session",
            task_name="webui_test_task",
            log_level="ERROR",
        )

        # Mock internal components
        client._client = MagicMock()
        client._client.initialize = AsyncMock()
        client._client.shutdown = AsyncMock()
        client._client.ensure_devices_connected = AsyncMock(
            return_value={"device1": True}
        )

        client._session = MagicMock()
        client._session.force_finish = AsyncMock()

        app_state.galaxy_client = client
        app_state._request_counter = 5  # Simulate some requests processed

        yield app_state


@pytest_asyncio.fixture
def galaxy_service(mock_app_state):
    """Create GalaxyService with mocked app state."""
    service = GalaxyService(app_state=mock_app_state)
    return service


@pytest.mark.asyncio
async def test_stop_task_and_restart_full_flow(galaxy_service, mock_app_state):
    """Test the complete stop_task_and_restart flow."""
    # Arrange
    original_counter = mock_app_state._request_counter

    # Mock create_next_session
    with patch.object(
        mock_app_state.galaxy_client, "create_next_session", new_callable=AsyncMock
    ) as mock_create_session:
        mock_create_session.return_value = {
            "status": "success",
            "session_name": "new_session_123",
            "task_name": "new_task_123",
        }

        # Act
        result = await galaxy_service.stop_task_and_restart()

        # Assert
        # 1. shutdown(force=True) 应该被调用
        mock_app_state.galaxy_client._client.shutdown.assert_called_once()
        mock_app_state.galaxy_client._session.force_finish.assert_called()

        # 2. initialize 应该被调用
        mock_app_state.galaxy_client._client.initialize.assert_called_once()

        # 3. request counter 应该被重置
        assert mock_app_state._request_counter == 0
        assert mock_app_state._request_counter != original_counter

        # 4. create_next_session 应该被调用
        mock_create_session.assert_called_once()

        # 5. 返回结果应该包含新session信息
        assert result["status"] == "success"
        assert result["session_name"] == "new_session_123"


@pytest.mark.asyncio
async def test_stop_task_cancels_running_task(galaxy_service, mock_app_state):
    """Test that stop_task_and_restart cancels a running task."""

    # Arrange
    # Create a mock running task
    async def long_running_task():
        await asyncio.sleep(10)  # Simulate long task
        return {"status": "completed"}

    mock_task = asyncio.create_task(long_running_task())
    mock_app_state.galaxy_client._current_request_task = mock_task

    with patch.object(
        mock_app_state.galaxy_client, "create_next_session", new_callable=AsyncMock
    ) as mock_create_session:
        mock_create_session.return_value = {
            "status": "success",
            "session_name": "new_session",
        }

        # Act
        result = await galaxy_service.stop_task_and_restart()

        # Assert
        # Task should be cancelled
        assert mock_task.cancelled()
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_stop_task_without_active_client(galaxy_service, mock_app_state):
    """Test stop_task_and_restart when no Galaxy client is active."""
    # Arrange
    mock_app_state.galaxy_client = None

    # Act & Assert
    with pytest.raises(ValueError, match="Galaxy client not initialized"):
        await galaxy_service.stop_task_and_restart()


@pytest.mark.asyncio
async def test_stop_task_handles_shutdown_error(galaxy_service, mock_app_state):
    """Test that stop_task_and_restart handles shutdown errors gracefully."""
    # Arrange
    mock_app_state.galaxy_client._session.force_finish.side_effect = RuntimeError(
        "Shutdown error"
    )

    # Act & Assert
    with pytest.raises(RuntimeError, match="Shutdown error"):
        await galaxy_service.stop_task_and_restart()


@pytest.mark.asyncio
async def test_stop_task_handles_initialization_error(galaxy_service, mock_app_state):
    """Test that stop_task_and_restart handles initialization errors."""
    # Arrange
    mock_app_state.galaxy_client._client.initialize.side_effect = RuntimeError(
        "Init error"
    )

    # Act & Assert
    with pytest.raises(RuntimeError, match="Init error"):
        await galaxy_service.stop_task_and_restart()


@pytest.mark.asyncio
async def test_stop_task_resets_counter_even_on_error(galaxy_service, mock_app_state):
    """Test that request counter is NOT reset if error occurs before reset point."""
    # Arrange
    original_counter = mock_app_state._request_counter
    # Make shutdown fail
    mock_app_state.galaxy_client._session.force_finish.side_effect = RuntimeError(
        "Test error"
    )

    # Act
    with pytest.raises(RuntimeError):
        await galaxy_service.stop_task_and_restart()

    # Assert
    # Counter should NOT be reset because error occurred before reset
    assert mock_app_state._request_counter == original_counter


@pytest.mark.asyncio
async def test_stop_task_with_no_running_task(galaxy_service, mock_app_state):
    """Test stop_task_and_restart when no task is currently running."""
    # Arrange
    mock_app_state.galaxy_client._current_request_task = None

    with patch.object(
        mock_app_state.galaxy_client, "create_next_session", new_callable=AsyncMock
    ) as mock_create_session:
        mock_create_session.return_value = {
            "status": "success",
            "session_name": "new_session",
        }

        # Act
        result = await galaxy_service.stop_task_and_restart()

        # Assert
        # Should complete successfully without trying to cancel non-existent task
        assert result["status"] == "success"
        mock_create_session.assert_called_once()


@pytest.mark.asyncio
async def test_stop_task_shutdown_uses_force_true(galaxy_service, mock_app_state):
    """Test that stop_task_and_restart calls shutdown with force=True."""
    # Arrange
    original_shutdown = mock_app_state.galaxy_client.shutdown
    shutdown_called_with_force = None

    async def track_shutdown_call(force=False):
        nonlocal shutdown_called_with_force
        shutdown_called_with_force = force
        await original_shutdown(force=force)

    with patch.object(
        mock_app_state.galaxy_client, "shutdown", side_effect=track_shutdown_call
    ):
        with patch.object(
            mock_app_state.galaxy_client, "create_next_session", new_callable=AsyncMock
        ) as mock_create_session:
            mock_create_session.return_value = {"status": "success"}

            # Act
            await galaxy_service.stop_task_and_restart()

            # Assert
            assert shutdown_called_with_force is True


@pytest.mark.asyncio
async def test_is_client_available_returns_correct_status(
    galaxy_service, mock_app_state
):
    """Test is_client_available method."""
    # When client exists
    assert galaxy_service.is_client_available() is True

    # When client is None
    mock_app_state.galaxy_client = None
    assert galaxy_service.is_client_available() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
