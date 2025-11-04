# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test that pending tasks are immediately cancelled when device disconnects.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import websockets

from galaxy.client.device_manager import ConstellationDeviceManager
from galaxy.client.components import DeviceStatus
from galaxy.core.types import ExecutionResult
from aip.messages import TaskStatus


@pytest.fixture
def device_manager():
    """Create a device manager instance for testing."""
    return ConstellationDeviceManager(
        task_name="test_task",
        heartbeat_interval=30.0,
        reconnect_delay=5.0,
    )


@pytest.mark.asyncio
async def test_pending_task_future_stored_with_device_id(device_manager):
    """
    Test that _pending_tasks stores (device_id, Future) tuples.
    """
    device_id = "test_device_1"
    task_id = "test_task@task_123"

    # Create a mock future
    mock_future = asyncio.Future()

    # Store it with device_id
    device_manager.connection_manager._pending_tasks[task_id] = (device_id, mock_future)

    # Verify structure
    assert task_id in device_manager.connection_manager._pending_tasks
    stored_device_id, stored_future = device_manager.connection_manager._pending_tasks[
        task_id
    ]
    assert stored_device_id == device_id
    assert stored_future is mock_future


@pytest.mark.asyncio
async def test_cancel_pending_tasks_for_device(device_manager):
    """
    Test that _cancel_pending_tasks_for_device cancels only tasks for specific device.
    """
    device_id_1 = "device_1"
    device_id_2 = "device_2"

    # Create multiple pending tasks for different devices
    task_1_future = asyncio.Future()
    task_2_future = asyncio.Future()
    task_3_future = asyncio.Future()

    device_manager.connection_manager._pending_tasks["task_1"] = (
        device_id_1,
        task_1_future,
    )
    device_manager.connection_manager._pending_tasks["task_2"] = (
        device_id_1,
        task_2_future,
    )
    device_manager.connection_manager._pending_tasks["task_3"] = (
        device_id_2,
        task_3_future,
    )

    # Cancel tasks for device_1 only
    device_manager.connection_manager._cancel_pending_tasks_for_device(device_id_1)

    # Verify device_1 tasks were cancelled with exception
    assert task_1_future.done()
    assert task_2_future.done()
    with pytest.raises(ConnectionError, match="disconnected while waiting"):
        task_1_future.result()
    with pytest.raises(ConnectionError, match="disconnected while waiting"):
        task_2_future.result()

    # Verify device_2 task was NOT cancelled
    assert not task_3_future.done()

    # Verify device_1 tasks were removed from pending
    assert "task_1" not in device_manager.connection_manager._pending_tasks
    assert "task_2" not in device_manager.connection_manager._pending_tasks
    assert "task_3" in device_manager.connection_manager._pending_tasks


@pytest.mark.asyncio
async def test_disconnect_device_cancels_pending_tasks(device_manager):
    """
    Test that disconnect_device() automatically cancels all pending tasks.
    """
    device_id = "test_device_1"

    # Create mock websocket
    mock_websocket = AsyncMock()
    device_manager.connection_manager._connections[device_id] = mock_websocket

    # Create pending tasks
    task_1_future = asyncio.Future()
    task_2_future = asyncio.Future()

    device_manager.connection_manager._pending_tasks["test_task@task_1"] = (
        device_id,
        task_1_future,
    )
    device_manager.connection_manager._pending_tasks["test_task@task_2"] = (
        device_id,
        task_2_future,
    )

    # Disconnect device
    await device_manager.connection_manager.disconnect_device(device_id)

    # Verify tasks were cancelled
    assert task_1_future.done()
    assert task_2_future.done()
    with pytest.raises(ConnectionError):
        task_1_future.result()
    with pytest.raises(ConnectionError):
        task_2_future.result()

    # Verify websocket was closed
    mock_websocket.close.assert_called_once()


@pytest.mark.asyncio
async def test_task_returns_immediately_when_device_disconnects(device_manager):
    """
    Test that when a device disconnects while a task is waiting,
    the task receives ConnectionError immediately and returns FAILED result.
    """
    device_id = "test_device_1"
    task_id = "task_123"

    # Register device
    device_manager.device_registry.register_device(
        device_id=device_id,
        server_url="ws://localhost:8000",
        os="Windows",
        capabilities=["ui_automation"],
    )

    # Set device to IDLE
    device_manager.device_registry.update_device_status(device_id, DeviceStatus.IDLE)

    # Track when task starts and completes
    task_started = asyncio.Event()
    task_completed = asyncio.Event()

    async def simulate_disconnect_during_task(*args, **kwargs):
        """Simulate device disconnecting while task is waiting for response"""
        task_started.set()

        # Wait a bit to simulate task in progress
        await asyncio.sleep(0.1)

        # Simulate disconnection - this should cancel the pending task
        await device_manager.connection_manager.disconnect_device(device_id)

        # This should trigger ConnectionError for the waiting task
        raise ConnectionError(
            f"Device {device_id} disconnected while waiting for task response"
        )

    with patch.object(
        device_manager.connection_manager,
        "send_task_to_device",
        side_effect=simulate_disconnect_during_task,
    ):
        # Execute task - should return quickly with FAILED status
        start_time = asyncio.get_event_loop().time()

        result = await device_manager.assign_task_to_device(
            task_id=task_id,
            device_id=device_id,
            task_description="Test task",
            task_data={},
            timeout=1000.0,  # Very long timeout to ensure we're not hitting it
        )

        elapsed_time = asyncio.get_event_loop().time() - start_time

    # Verify task returned quickly (should be < 1 second, not waiting for 1000s timeout)
    assert (
        elapsed_time < 1.0
    ), f"Task should return immediately, but took {elapsed_time}s"

    # Verify result is FAILED with disconnection info
    assert isinstance(result, ExecutionResult)
    assert result.status == TaskStatus.FAILED
    assert result.metadata["disconnected"] is True
    assert "disconnected" in result.result["message"].lower()

    print(f"✅ Task returned in {elapsed_time:.3f}s (expected < 1s)")


@pytest.mark.asyncio
async def test_multiple_pending_tasks_all_cancelled_on_disconnection(device_manager):
    """
    Test that when device disconnects, ALL its pending tasks are cancelled immediately.
    """
    device_id = "test_device_multi"

    # Create multiple task futures as if they're waiting for responses
    task_ids = ["test_task@task_1", "test_task@task_2", "test_task@task_3"]
    task_futures = []

    for task_id in task_ids:
        future = asyncio.Future()
        device_manager.connection_manager._pending_tasks[task_id] = (device_id, future)
        task_futures.append(future)

    # Create mock websocket
    mock_websocket = AsyncMock()
    device_manager.connection_manager._connections[device_id] = mock_websocket

    # Trigger disconnection
    await device_manager.connection_manager.disconnect_device(device_id)

    # Verify all tasks were cancelled with exception
    for i, future in enumerate(task_futures):
        assert future.done(), f"Task {i} should be done"
        with pytest.raises(ConnectionError, match="disconnected while waiting"):
            future.result()

    # Verify all tasks were removed from pending
    for task_id in task_ids:
        assert task_id not in device_manager.connection_manager._pending_tasks


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
