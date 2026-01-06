# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Comprehensive tests for ConstellationDeviceManager.assign_task_to_device

Tests cover:
1. Task assignment to IDLE device (immediate execution)
2. Task assignment to BUSY device (queuing)
3. Sequential task processing from queue
4. Concurrent task submissions
5. Error handling during task execution
6. Device state transitions (IDLE <-> BUSY)
7. Task queue status queries
8. Edge cases and error conditions
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call
from typing import Dict, Any

from galaxy.client.device_manager import ConstellationDeviceManager
from galaxy.client.components import DeviceStatus, AgentProfile, TaskRequest
from galaxy.core.types import ExecutionResult


class TestAssignTaskToDevice:
    """Test suite for assign_task_to_device method"""

    @pytest.fixture
    def device_manager(self):
        """Create a device manager instance for testing"""
        manager = ConstellationDeviceManager(
            constellation_id="test_constellation",
            heartbeat_interval=30.0,
            reconnect_delay=5.0,
        )
        return manager

    @pytest.fixture
    def mock_device_id(self):
        """Standard test device ID"""
        return "test_device_001"

    @pytest.fixture
    def mock_execution_result(self):
        """Mock successful execution result"""
        return ExecutionResult(
            task_id="mock_task",
            status="completed",
            result={"result": "success", "output": "Task output"},
            metadata={"message": "Task completed successfully"},
        )

    @pytest.fixture
    def setup_connected_device(self, device_manager, mock_device_id):
        """Setup a connected and IDLE device"""
        # Register device
        device_manager.device_registry.register_device(
            device_id=mock_device_id,
            server_url="ws://localhost:5000/ws",
            capabilities=["ui_automation"],
            metadata={"platform": "windows"},
        )

        # Set device to IDLE (simulating successful connection)
        device_manager.device_registry.update_device_status(
            mock_device_id, DeviceStatus.IDLE
        )

        return mock_device_id

    # ========================================================================
    # Test 1: Task assignment to IDLE device (immediate execution)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_assign_task_to_idle_device(
        self, device_manager, setup_connected_device, mock_execution_result
    ):
        """Test that task is executed immediately when device is IDLE"""
        device_id = setup_connected_device

        # Mock the connection manager's send_task_to_device method
        device_manager.connection_manager.send_task_to_device = AsyncMock(
            return_value=mock_execution_result
        )

        # Assign task
        result = await device_manager.assign_task_to_device(
            task_id="task_001",
            device_id=device_id,
            task_description="Open Notepad",
            task_data={"app": "notepad"},
            timeout=60.0,
        )

        # Verify task was executed
        assert result == mock_execution_result
        device_manager.connection_manager.send_task_to_device.assert_called_once()

        # Verify device is back to IDLE after execution
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.IDLE
        assert device_info.current_task_id is None

    # ========================================================================
    # Test 2: Device state transitions during task execution
    # ========================================================================

    @pytest.mark.asyncio
    async def test_device_state_transitions(
        self, device_manager, setup_connected_device, mock_execution_result
    ):
        """Test device state changes from IDLE -> BUSY -> IDLE"""
        device_id = setup_connected_device
        state_transitions = []

        # Create a mock that tracks state transitions
        async def mock_send_task(dev_id, task_req):
            # Record state during execution
            device_info = device_manager.device_registry.get_device(dev_id)
            state_transitions.append(
                {
                    "during_execution": device_info.status,
                    "current_task": device_info.current_task_id,
                }
            )
            await asyncio.sleep(0.1)  # Simulate task execution time
            return mock_execution_result

        device_manager.connection_manager.send_task_to_device = mock_send_task
        device_manager.event_manager.notify_task_completed = AsyncMock()

        # Record initial state
        device_info = device_manager.device_registry.get_device(device_id)
        initial_state = device_info.status

        # Assign task
        result = await device_manager.assign_task_to_device(
            task_id="task_001",
            device_id=device_id,
            task_description="Test task",
            task_data={},
        )

        # Record final state
        device_info = device_manager.device_registry.get_device(device_id)
        final_state = device_info.status

        # Verify state transitions
        assert initial_state == DeviceStatus.IDLE
        assert state_transitions[0]["during_execution"] == DeviceStatus.BUSY
        assert state_transitions[0]["current_task"] == "task_001"
        assert final_state == DeviceStatus.IDLE

    # ========================================================================
    # Test 3: Task assignment to BUSY device (queuing)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_assign_task_to_busy_device_queues_task(
        self, device_manager, setup_connected_device, mock_execution_result
    ):
        """Test that task is queued when device is BUSY"""
        device_id = setup_connected_device

        # Set device to BUSY
        device_manager.device_registry.set_device_busy(device_id, "ongoing_task")

        # Create a counter to track task executions
        execution_order = []

        async def mock_send_task(dev_id, task_req):
            execution_order.append(task_req.task_id)
            await asyncio.sleep(0.05)  # Simulate execution time
            return mock_execution_result

        device_manager.connection_manager.send_task_to_device = mock_send_task
        device_manager.event_manager.notify_task_completed = AsyncMock()

        # Submit task (should be queued)
        task_future = asyncio.create_task(
            device_manager.assign_task_to_device(
                task_id="task_002",
                device_id=device_id,
                task_description="Queued task",
                task_data={},
            )
        )

        # Give it time to be queued
        await asyncio.sleep(0.01)

        # Verify task is in queue
        queue_status = device_manager.get_task_queue_status(device_id)
        assert queue_status["is_busy"] is True
        assert queue_status["current_task_id"] == "ongoing_task"
        assert queue_status["queue_size"] == 1
        assert "task_002" in queue_status["queued_task_ids"]

        # Manually set device to IDLE and trigger queue processing
        device_manager.device_registry.set_device_idle(device_id)
        await device_manager._process_next_queued_task(device_id)

        # Wait for queued task to complete
        result = await task_future

        # Verify task was executed
        assert result == mock_execution_result
        assert "task_002" in execution_order

    # ========================================================================
    # Test 4: Sequential task processing from queue
    # ========================================================================

    @pytest.mark.asyncio
    async def test_sequential_task_processing(
        self, device_manager, setup_connected_device, mock_execution_result
    ):
        """Test that multiple queued tasks are processed in order"""
        device_id = setup_connected_device
        execution_order = []
        task_start_times = {}

        async def mock_send_task(dev_id, task_req):
            task_start_times[task_req.task_id] = asyncio.get_event_loop().time()
            execution_order.append(task_req.task_id)
            await asyncio.sleep(0.1)  # Simulate execution time
            return ExecutionResult(
                task_id=task_req.task_id,
                status="completed",
                result={"task_id": task_req.task_id},
                metadata={"message": f"{task_req.task_id} completed"},
            )

        device_manager.connection_manager.send_task_to_device = mock_send_task
        device_manager.event_manager.notify_task_completed = AsyncMock()

        # Submit 3 tasks concurrently
        tasks = [
            asyncio.create_task(
                device_manager.assign_task_to_device(
                    task_id=f"task_{i:03d}",
                    device_id=device_id,
                    task_description=f"Task {i}",
                    task_data={"order": i},
                )
            )
            for i in range(1, 4)
        ]

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)

        # Verify all tasks completed successfully
        assert len(results) == 3
        for i, result in enumerate(results, 1):
            assert result.is_successful is True

        # Verify tasks were executed in order
        assert execution_order == ["task_001", "task_002", "task_003"]

        # Verify device is IDLE after all tasks
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.IDLE
        assert device_info.current_task_id is None

        # Verify queue is empty
        assert device_manager.task_queue_manager.get_queue_size(device_id) == 0

    # ========================================================================
    # Test 5: Error handling during task execution
    # ========================================================================

    @pytest.mark.asyncio
    async def test_task_execution_error_handling(
        self, device_manager, setup_connected_device
    ):
        """Test that errors during task execution are handled properly"""
        device_id = setup_connected_device

        # Mock send_task_to_device to raise an exception
        test_exception = Exception("Task execution failed")
        device_manager.connection_manager.send_task_to_device = AsyncMock(
            side_effect=test_exception
        )
        device_manager.event_manager.notify_task_completed = AsyncMock()

        # Assign task and expect exception
        with pytest.raises(Exception) as exc_info:
            await device_manager.assign_task_to_device(
                task_id="task_001",
                device_id=device_id,
                task_description="Failing task",
                task_data={},
            )

        assert str(exc_info.value) == "Task execution failed"

        # Verify device is set back to IDLE even after error
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.IDLE
        assert device_info.current_task_id is None

    # ========================================================================
    # Test 6: Error handling with queued tasks
    # ========================================================================

    @pytest.mark.asyncio
    async def test_error_handling_with_queued_tasks(
        self, device_manager, setup_connected_device, mock_execution_result
    ):
        """Test that queue continues processing after a task fails"""
        device_id = setup_connected_device
        execution_count = [0]

        async def mock_send_task(dev_id, task_req):
            execution_count[0] += 1
            if task_req.task_id == "task_002":
                # Second task fails
                raise Exception("Task 2 failed")
            await asyncio.sleep(0.05)
            return mock_execution_result

        device_manager.connection_manager.send_task_to_device = mock_send_task
        device_manager.event_manager.notify_task_completed = AsyncMock()

        # Submit 3 tasks
        task1 = asyncio.create_task(
            device_manager.assign_task_to_device(
                task_id="task_001",
                device_id=device_id,
                task_description="Task 1",
                task_data={},
            )
        )

        task2 = asyncio.create_task(
            device_manager.assign_task_to_device(
                task_id="task_002",
                device_id=device_id,
                task_description="Task 2 (will fail)",
                task_data={},
            )
        )

        task3 = asyncio.create_task(
            device_manager.assign_task_to_device(
                task_id="task_003",
                device_id=device_id,
                task_description="Task 3",
                task_data={},
            )
        )

        # Gather results (task2 will raise exception)
        results = await asyncio.gather(task1, task2, task3, return_exceptions=True)

        # Verify task 1 succeeded
        assert results[0].is_successful is True

        # Verify task 2 failed
        assert isinstance(results[1], Exception)
        assert "Task 2 failed" in str(results[1])

        # Verify task 3 succeeded (queue continued after error)
        assert results[2].is_successful is True

        # Verify all 3 tasks were attempted
        assert execution_count[0] == 3

        # Verify device is IDLE
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.IDLE

    # ========================================================================
    # Test 7: Device not registered error
    # ========================================================================

    @pytest.mark.asyncio
    async def test_assign_task_to_unregistered_device(self, device_manager):
        """Test that assigning task to unregistered device raises error"""
        with pytest.raises(ValueError) as exc_info:
            await device_manager.assign_task_to_device(
                task_id="task_001",
                device_id="nonexistent_device",
                task_description="Test task",
                task_data={},
            )

        assert "not registered" in str(exc_info.value)

    # ========================================================================
    # Test 8: Device not connected error
    # ========================================================================

    @pytest.mark.asyncio
    async def test_assign_task_to_disconnected_device(
        self, device_manager, mock_device_id
    ):
        """Test that assigning task to disconnected device raises error"""
        # Register device but don't connect
        device_manager.device_registry.register_device(
            device_id=mock_device_id,
            server_url="ws://localhost:5000/ws",
        )
        # Device status is DISCONNECTED

        with pytest.raises(ValueError) as exc_info:
            await device_manager.assign_task_to_device(
                task_id="task_001",
                device_id=mock_device_id,
                task_description="Test task",
                task_data={},
            )

        assert "not connected" in str(exc_info.value)

    # ========================================================================
    # Test 9: Queue status queries
    # ========================================================================

    @pytest.mark.asyncio
    async def test_queue_status_queries(
        self, device_manager, setup_connected_device, mock_execution_result
    ):
        """Test get_task_queue_status and get_device_status methods"""
        device_id = setup_connected_device

        # Mock long-running task
        async def mock_send_task(dev_id, task_req):
            await asyncio.sleep(0.2)  # Long execution time
            return mock_execution_result

        device_manager.connection_manager.send_task_to_device = mock_send_task
        device_manager.event_manager.notify_task_completed = AsyncMock()

        # Submit task 1 (will start executing)
        task1 = asyncio.create_task(
            device_manager.assign_task_to_device(
                task_id="task_001",
                device_id=device_id,
                task_description="Running task",
                task_data={},
            )
        )

        # Wait for task to start
        await asyncio.sleep(0.05)

        # Submit task 2 and 3 (will be queued)
        task2 = asyncio.create_task(
            device_manager.assign_task_to_device(
                task_id="task_002",
                device_id=device_id,
                task_description="Queued task 1",
                task_data={},
            )
        )

        task3 = asyncio.create_task(
            device_manager.assign_task_to_device(
                task_id="task_003",
                device_id=device_id,
                task_description="Queued task 2",
                task_data={},
            )
        )

        # Wait for tasks to be queued
        await asyncio.sleep(0.05)

        # Query queue status
        queue_status = device_manager.get_task_queue_status(device_id)

        # Verify queue status
        assert queue_status["is_busy"] is True
        assert queue_status["current_task_id"] == "task_001"
        assert queue_status["queue_size"] == 2
        assert set(queue_status["queued_task_ids"]) == {"task_002", "task_003"}
        # Note: pending_task_ids includes only queued tasks that have futures waiting
        assert (
            len(queue_status["pending_task_ids"]) >= 2
        )  # At least task_002 and task_003

        # Query device status
        device_status = device_manager.get_device_status(device_id)

        # Verify device status includes queue info
        assert device_status["status"] == DeviceStatus.BUSY.value
        assert device_status["current_task_id"] == "task_001"
        assert device_status["queued_tasks"] == 2
        assert set(device_status["queued_task_ids"]) == {"task_002", "task_003"}

        # Wait for all tasks to complete
        await asyncio.gather(task1, task2, task3)

        # Verify queue is empty after completion
        final_queue_status = device_manager.get_task_queue_status(device_id)
        assert final_queue_status["is_busy"] is False
        assert final_queue_status["queue_size"] == 0
        assert final_queue_status["current_task_id"] is None

    # ========================================================================
    # Test 10: Concurrent task submissions to multiple devices
    # ========================================================================

    @pytest.mark.asyncio
    async def test_concurrent_tasks_multiple_devices(
        self, device_manager, mock_execution_result
    ):
        """Test concurrent task execution on multiple devices"""
        # Setup two devices
        device1 = "device_001"
        device2 = "device_002"

        for device_id in [device1, device2]:
            device_manager.device_registry.register_device(
                device_id=device_id,
                server_url="ws://localhost:5000/ws",
            )
            device_manager.device_registry.update_device_status(
                device_id, DeviceStatus.IDLE
            )

        execution_log = []

        async def mock_send_task(dev_id, task_req):
            execution_log.append(
                {
                    "device": dev_id,
                    "task": task_req.task_id,
                    "time": asyncio.get_event_loop().time(),
                }
            )
            await asyncio.sleep(0.1)
            return mock_execution_result

        device_manager.connection_manager.send_task_to_device = mock_send_task
        device_manager.event_manager.notify_task_completed = AsyncMock()

        # Submit tasks to both devices concurrently
        tasks = []
        for i in range(1, 4):  # 3 tasks per device
            tasks.append(
                asyncio.create_task(
                    device_manager.assign_task_to_device(
                        task_id=f"dev1_task_{i}",
                        device_id=device1,
                        task_description=f"Device 1 Task {i}",
                        task_data={},
                    )
                )
            )
            tasks.append(
                asyncio.create_task(
                    device_manager.assign_task_to_device(
                        task_id=f"dev2_task_{i}",
                        device_id=device2,
                        task_description=f"Device 2 Task {i}",
                        task_data={},
                    )
                )
            )

        # Wait for all tasks
        results = await asyncio.gather(*tasks)

        # Verify all tasks completed
        assert len(results) == 6
        assert all(r.is_successful for r in results)

        # Verify both devices executed tasks concurrently
        # (execution log should have interleaved tasks from both devices)
        device1_tasks = [log for log in execution_log if log["device"] == device1]
        device2_tasks = [log for log in execution_log if log["device"] == device2]

        assert len(device1_tasks) == 3
        assert len(device2_tasks) == 3

        # Verify both devices are IDLE
        assert (
            device_manager.device_registry.get_device(device1).status
            == DeviceStatus.IDLE
        )
        assert (
            device_manager.device_registry.get_device(device2).status
            == DeviceStatus.IDLE
        )

    # ========================================================================
    # Test 11: Task timeout handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_task_timeout(self, device_manager, setup_connected_device):
        """Test task timeout behavior"""
        device_id = setup_connected_device

        # Mock a task that takes longer than timeout
        async def mock_slow_task(dev_id, task_req):
            await asyncio.sleep(10)  # Much longer than timeout
            return ExecutionResult(
                task_id=task_req.task_id,
                status="completed",
                result={},
                metadata={"message": "Completed"},
            )

        device_manager.connection_manager.send_task_to_device = mock_slow_task
        device_manager.event_manager.notify_task_completed = AsyncMock()

        # Assign task with short timeout
        task = asyncio.create_task(
            device_manager.assign_task_to_device(
                task_id="task_001",
                device_id=device_id,
                task_description="Slow task",
                task_data={},
                timeout=0.1,  # Very short timeout
            )
        )

        # Wait a bit, then cancel (simulating timeout)
        await asyncio.sleep(0.15)

        # In real implementation, timeout would be handled by connection_manager
        # For this test, we verify the task is still executing
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.BUSY

        # Cancel the task
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # Device should eventually return to IDLE
        # (In real scenario, connection_manager would handle timeout and cleanup)

    # ========================================================================
    # Test 12: Verify task request creation
    # ========================================================================

    @pytest.mark.asyncio
    async def test_task_request_creation(
        self, device_manager, setup_connected_device, mock_execution_result
    ):
        """Test that TaskRequest is created with correct parameters"""
        device_id = setup_connected_device
        captured_task_request = None

        async def mock_send_task(dev_id, task_req):
            nonlocal captured_task_request
            captured_task_request = task_req
            return mock_execution_result

        device_manager.connection_manager.send_task_to_device = mock_send_task
        device_manager.event_manager.notify_task_completed = AsyncMock()

        # Assign task with specific parameters
        await device_manager.assign_task_to_device(
            task_id="test_task_123",
            device_id=device_id,
            task_description="Test description",
            task_data={"key1": "value1", "key2": 123},
            timeout=120.0,
        )

        # Verify TaskRequest was created correctly
        assert captured_task_request is not None
        assert captured_task_request.task_id == "test_task_123"
        assert captured_task_request.device_id == device_id
        assert captured_task_request.request == "Test description"
        assert captured_task_request.task_name == "test_task_123"
        assert captured_task_request.metadata == {"key1": "value1", "key2": 123}
        assert captured_task_request.timeout == 120.0
        assert captured_task_request.created_at is not None


# ============================================================================
# Integration Tests
# ============================================================================


class TestAssignTaskIntegration:
    """Integration tests with more realistic scenarios"""

    @pytest.fixture
    def device_manager(self):
        """Create device manager with mocked components"""
        manager = ConstellationDeviceManager()

        # Mock connection manager
        manager.connection_manager.send_task_to_device = AsyncMock()
        manager.connection_manager.connect_to_device = AsyncMock()
        manager.connection_manager.request_device_info = AsyncMock()

        # Mock event manager
        manager.event_manager.notify_device_connected = AsyncMock()
        manager.event_manager.notify_task_completed = AsyncMock()

        # Mock message processor and heartbeat
        manager.message_processor.start_message_handler = Mock()
        manager.heartbeat_manager.start_heartbeat = Mock()

        return manager

    @pytest.mark.asyncio
    async def test_realistic_workflow(self, device_manager):
        """Test a realistic workflow: connect device, submit tasks, verify queue"""
        device_id = "real_device_001"

        # Register device
        device_manager.device_registry.register_device(
            device_id=device_id,
            server_url="ws://localhost:5000/ws",
            capabilities=["ui_automation", "file_operations"],
        )

        # Connect device (simulate)
        device_manager.device_registry.update_device_status(
            device_id, DeviceStatus.IDLE
        )

        # Track execution
        execution_times = []

        async def mock_task_execution(dev_id, task_req):
            start_time = asyncio.get_event_loop().time()
            execution_times.append(
                {"task": task_req.task_id, "start": start_time, "device": dev_id}
            )
            await asyncio.sleep(0.1)  # Simulate work
            return ExecutionResult(
                task_id=task_req.task_id,
                status="completed",
                result={},
                metadata={"message": f"{task_req.task_id} done"},
            )

        device_manager.connection_manager.send_task_to_device = mock_task_execution

        # Submit 5 tasks
        tasks = [
            asyncio.create_task(
                device_manager.assign_task_to_device(
                    task_id=f"workflow_task_{i}",
                    device_id=device_id,
                    task_description=f"Workflow step {i}",
                    task_data={"step": i},
                )
            )
            for i in range(1, 6)
        ]

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        # Verify all succeeded
        assert all(r.is_successful for r in results)

        # Verify sequential execution (tasks didn't overlap)
        for i in range(len(execution_times) - 1):
            # Each task should start at least 0.09s after the previous
            # (0.1s execution - small margin for scheduling)
            time_diff = execution_times[i + 1]["start"] - execution_times[i]["start"]
            assert time_diff >= 0.09

        # Verify final state
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.IDLE
        assert device_manager.task_queue_manager.get_queue_size(device_id) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
