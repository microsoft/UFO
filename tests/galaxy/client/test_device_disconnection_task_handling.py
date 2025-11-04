# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Tests for device disconnection during task execution.

Verifies that tasks return ExecutionResult with FAILED status and proper
disconnection messages when device disconnects during execution.
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
async def test_device_disconnection_during_task_execution_returns_failed_result(
    device_manager,
):
    """
    Test that device disconnection during task execution returns ExecutionResult
    with FAILED status and disconnection message.
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

    # Set device to IDLE (ready to execute)
    device_manager.device_registry.update_device_status(device_id, DeviceStatus.IDLE)

    # Mock connection manager to simulate disconnection
    with patch.object(
        device_manager.connection_manager,
        "send_task_to_device",
        side_effect=ConnectionError(
            "Device test_device_1 connection is closed (disconnected)"
        ),
    ):
        # Execute task
        result = await device_manager.assign_task_to_device(
            task_id=task_id,
            device_id=device_id,
            task_description="Test task",
            task_data={},
            timeout=10.0,
        )

    # Verify result
    assert isinstance(result, ExecutionResult)
    assert result.status == TaskStatus.FAILED
    assert result.task_id == task_id
    assert result.error is not None
    assert (
        "disconnected" in str(result.error).lower()
        or "connection" in str(result.error).lower()
    )

    # Verify result contains disconnection information
    assert result.result is not None
    assert result.result["error_type"] == "device_disconnection"
    assert result.result["device_id"] == device_id
    assert result.result["task_id"] == task_id
    assert "disconnected" in result.result["message"].lower()

    # Verify metadata
    assert result.metadata["device_id"] == device_id
    assert result.metadata["disconnected"] is True
    assert result.metadata["error_category"] == "connection_error"


@pytest.mark.asyncio
async def test_task_timeout_returns_failed_result_with_timeout_info(device_manager):
    """
    Test that task timeout returns ExecutionResult with FAILED status
    and timeout information.
    """
    device_id = "test_device_2"
    task_id = "task_456"

    # Register device
    device_manager.device_registry.register_device(
        device_id=device_id,
        server_url="ws://localhost:8000",
        os="Windows",
        capabilities=["ui_automation"],
    )

    # Set device to IDLE
    device_manager.device_registry.update_device_status(device_id, DeviceStatus.IDLE)

    # Mock connection manager to simulate timeout
    with patch.object(
        device_manager.connection_manager,
        "send_task_to_device",
        side_effect=asyncio.TimeoutError("Task task_456 timed out"),
    ):
        # Execute task
        result = await device_manager.assign_task_to_device(
            task_id=task_id,
            device_id=device_id,
            task_description="Test task",
            task_data={},
            timeout=5.0,
        )

    # Verify result
    assert isinstance(result, ExecutionResult)
    assert result.status == TaskStatus.FAILED
    assert result.task_id == task_id
    assert result.error is not None
    assert "timed out" in str(result.error).lower()

    # Verify result contains timeout information
    assert result.result is not None
    assert result.result["error_type"] == "timeout"
    assert result.result["device_id"] == device_id
    assert result.metadata["error_category"] == "timeout_error"
    assert result.metadata["timeout"] == 5.0


@pytest.mark.asyncio
async def test_websocket_connection_closed_exception_during_task(device_manager):
    """
    Test that WebSocket ConnectionClosed exception is properly converted
    to ConnectionError and returns FAILED ExecutionResult.
    """
    device_id = "test_device_3"
    task_id = "task_789"

    # Register device
    device_manager.device_registry.register_device(
        device_id=device_id,
        server_url="ws://localhost:8000",
        os="Windows",
        capabilities=["ui_automation"],
    )

    # Set device to IDLE
    device_manager.device_registry.update_device_status(device_id, DeviceStatus.IDLE)

    # Simulate ConnectionError from WebSocket
    with patch.object(
        device_manager.connection_manager,
        "send_task_to_device",
        side_effect=ConnectionError(
            f"Device {device_id} disconnected during task execution"
        ),
    ):
        # Execute task
        result = await device_manager.assign_task_to_device(
            task_id=task_id,
            device_id=device_id,
            task_description="Test task",
            task_data={},
            timeout=10.0,
        )

    # Verify result
    assert isinstance(result, ExecutionResult)
    assert result.status == TaskStatus.FAILED
    assert "disconnected" in str(result.error).lower()
    assert result.metadata["disconnected"] is True


@pytest.mark.asyncio
async def test_general_exception_returns_failed_result(device_manager):
    """
    Test that general exceptions during task execution return ExecutionResult
    with FAILED status and error information.
    """
    device_id = "test_device_5"
    task_id = "task_error"

    # Register device
    device_manager.device_registry.register_device(
        device_id=device_id,
        server_url="ws://localhost:8000",
        os="Windows",
        capabilities=["ui_automation"],
    )

    # Set device to IDLE
    device_manager.device_registry.update_device_status(device_id, DeviceStatus.IDLE)

    # Mock connection manager to simulate general error
    with patch.object(
        device_manager.connection_manager,
        "send_task_to_device",
        side_effect=RuntimeError("Unexpected error during task execution"),
    ):
        # Execute task
        result = await device_manager.assign_task_to_device(
            task_id=task_id,
            device_id=device_id,
            task_description="Test task",
            task_data={},
            timeout=10.0,
        )

    # Verify result
    assert isinstance(result, ExecutionResult)
    assert result.status == TaskStatus.FAILED
    assert result.task_id == task_id
    assert result.error is not None
    assert result.result["error_type"] == "execution_error"
    assert result.metadata["error_category"] == "general_error"


@pytest.mark.asyncio
async def test_successful_task_execution_returns_completed_result(device_manager):
    """
    Test that successful task execution returns ExecutionResult with
    COMPLETED status.
    """
    device_id = "test_device_6"
    task_id = "task_success"

    # Register device
    device_manager.device_registry.register_device(
        device_id=device_id,
        server_url="ws://localhost:8000",
        os="Windows",
        capabilities=["ui_automation"],
    )

    # Set device to IDLE
    device_manager.device_registry.update_device_status(device_id, DeviceStatus.IDLE)

    # Mock successful task execution
    success_result = ExecutionResult(
        task_id=task_id,
        status=TaskStatus.COMPLETED,
        result={"output": "success"},
        metadata={"device_id": device_id},
    )

    with patch.object(
        device_manager.connection_manager,
        "send_task_to_device",
        return_value=success_result,
    ):
        # Execute task
        result = await device_manager.assign_task_to_device(
            task_id=task_id,
            device_id=device_id,
            task_description="Test task",
            task_data={},
            timeout=10.0,
        )

    # Verify result
    assert isinstance(result, ExecutionResult)
    assert result.status == TaskStatus.COMPLETED
    assert result.task_id == task_id
    assert result.result == {"output": "success"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
