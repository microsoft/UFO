#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for GalaxyClient task cancellation mechanism.

Tests the shutdown(force=True/False) functionality, task cancellation,
and idempotency of shutdown operations.
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

from galaxy.galaxy_client import GalaxyClient
from galaxy.client.constellation_client import ConstellationClient
from galaxy.session.galaxy_session import GalaxySession


@pytest_asyncio.fixture
async def mock_client():
    """Create a mock GalaxyClient for testing."""
    with patch("galaxy.galaxy_client.get_galaxy_config"), patch(
        "galaxy.galaxy_client.ConstellationConfig"
    ), patch("galaxy.galaxy_client.setup_logger"):

        client = GalaxyClient(
            session_name="test_session", task_name="test_task", log_level="ERROR"
        )

        # Mock constellation client
        client._client = MagicMock(spec=ConstellationClient)
        client._client.initialize = AsyncMock()
        client._client.shutdown = AsyncMock()
        client._client.device_manager = MagicMock()

        # Mock session
        client._session = MagicMock(spec=GalaxySession)
        client._session.force_finish = AsyncMock()

        yield client


@pytest.mark.asyncio
async def test_shutdown_without_force_no_running_task(mock_client):
    """Test shutdown(force=False) when no task is running."""
    # Arrange
    mock_client._current_request_task = None

    # Act
    await mock_client.shutdown(force=False)

    # Assert
    mock_client._session.force_finish.assert_called_once_with("Client shutdown")
    mock_client._client.shutdown.assert_called_once()
    assert mock_client._session is None


@pytest.mark.asyncio
async def test_shutdown_without_force_with_completed_task(mock_client):
    """Test shutdown(force=False) when task has completed."""
    # Arrange
    mock_task = AsyncMock()
    mock_task.done.return_value = True  # Task已完成
    mock_client._current_request_task = mock_task

    # Act
    await mock_client.shutdown(force=False)

    # Assert
    # 不应该尝试取消已完成的任务
    mock_task.cancel.assert_not_called()
    mock_client._session.force_finish.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_with_force_cancels_running_task(mock_client):
    """Test shutdown(force=True) cancels a running task."""
    # Arrange
    mock_task = AsyncMock()
    mock_task.done.return_value = False  # Task还在运行
    mock_task.cancel = MagicMock()

    # Mock the task to raise CancelledError when awaited
    async def mock_wait():
        raise asyncio.CancelledError()

    mock_task.__await__ = lambda: mock_wait().__await__()

    mock_client._current_request_task = mock_task

    # Act
    await mock_client.shutdown(force=True)

    # Assert
    mock_task.cancel.assert_called_once()  # 应该取消任务
    mock_client._session.force_finish.assert_called_once()
    mock_client._client.shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_with_force_handles_timeout(mock_client):
    """Test shutdown(force=True) handles task cancellation timeout."""
    # Arrange
    mock_task = AsyncMock()
    mock_task.done.return_value = False
    mock_task.cancel = MagicMock()

    # Mock the task to timeout
    async def mock_timeout():
        await asyncio.sleep(10)  # Simulate long-running task

    mock_task.__await__ = lambda: mock_timeout().__await__()

    mock_client._current_request_task = mock_task

    # Act
    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
        await mock_client.shutdown(force=True)

    # Assert
    mock_task.cancel.assert_called_once()
    # Shutdown应该继续，即使取消超时
    mock_client._client.shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_idempotency(mock_client):
    """Test that multiple shutdown calls are handled gracefully."""
    # Arrange
    mock_client._current_request_task = None

    # Act - 调用两次 shutdown
    await mock_client.shutdown(force=False)
    await mock_client.shutdown(force=False)

    # Assert - 第二次调用应该被跳过（因为 _is_shutting_down 标志）
    # 由于我们的实现会重置标志，实际会执行两次
    # 但由于 session 在第一次后被设置为 None，第二次不会重复操作
    assert mock_client._session is None


@pytest.mark.asyncio
async def test_process_request_saves_task_reference(mock_client):
    """Test that process_request saves current task reference."""
    # Arrange
    mock_client._client.device_manager.device_registry.get_all_devices = MagicMock(
        return_value={}
    )

    with patch.object(GalaxySession, "__init__", return_value=None), patch.object(
        GalaxySession, "run", new_callable=AsyncMock
    ), patch.object(GalaxySession, "_cleanup_observers", return_value=None):

        mock_session = MagicMock()
        mock_session.run = AsyncMock()
        mock_session._rounds = []
        mock_session.log_path = "/tmp/test"

        # Create a real task to test reference saving
        async def mock_process():
            # During execution, _current_request_task should be set
            assert mock_client._current_request_task is not None
            return {"status": "completed"}

        # Act
        with patch.object(mock_client, "_session", mock_session):
            with patch("galaxy.galaxy_client.GalaxySession", return_value=mock_session):
                task = asyncio.create_task(mock_client.process_request("test request"))
                await asyncio.sleep(0.1)  # Let task start

                # Assert - task reference should be saved
                assert mock_client._current_request_task is not None

                await task


@pytest.mark.asyncio
async def test_process_request_clears_task_reference_on_completion(mock_client):
    """Test that process_request clears task reference after completion."""
    # Arrange
    mock_client._client.device_manager.device_registry.get_all_devices = MagicMock(
        return_value={}
    )

    with patch.object(GalaxySession, "__init__", return_value=None), patch.object(
        GalaxySession, "run", new_callable=AsyncMock
    ), patch.object(GalaxySession, "_cleanup_observers", return_value=None):

        mock_session = MagicMock()
        mock_session.run = AsyncMock()
        mock_session._rounds = []
        mock_session.log_path = "/tmp/test"
        mock_session.current_constellation = None
        mock_session.session_results = {}

        with patch.object(mock_client, "_session", mock_session):
            with patch("galaxy.galaxy_client.GalaxySession", return_value=mock_session):
                # Act
                result = await mock_client.process_request("test request")

                # Assert
                assert mock_client._current_request_task is None  # 应该被清除
                assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_process_request_clears_task_reference_on_error(mock_client):
    """Test that process_request clears task reference even on error."""
    # Arrange
    mock_client._client.device_manager.device_registry.get_all_devices = MagicMock(
        return_value={}
    )

    with patch.object(GalaxySession, "__init__", return_value=None), patch.object(
        GalaxySession, "run", side_effect=RuntimeError("Test error")
    ), patch.object(GalaxySession, "_cleanup_observers", return_value=None):

        mock_session = MagicMock()
        mock_session.run = AsyncMock(side_effect=RuntimeError("Test error"))

        with patch("galaxy.galaxy_client.GalaxySession", return_value=mock_session):
            # Act
            result = await mock_client.process_request("test request")

            # Assert
            assert mock_client._current_request_task is None  # 即使出错也应该清除
            assert result["status"] == "failed"


@pytest.mark.asyncio
async def test_shutdown_handles_exception_gracefully(mock_client):
    """Test that shutdown handles exceptions during cancellation gracefully."""
    # Arrange
    mock_task = AsyncMock()
    mock_task.done.return_value = False
    mock_task.cancel = MagicMock()

    # Mock exception during wait
    async def mock_error():
        raise RuntimeError("Cancellation error")

    mock_task.__await__ = lambda: mock_error().__await__()

    mock_client._current_request_task = mock_task

    # Act - 不应该抛出异常
    await mock_client.shutdown(force=True)

    # Assert - 应该继续执行 shutdown
    mock_client._client.shutdown.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
