# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for the refactored TaskConstellationOrchestrator.

Tests orchestration functionality with separated responsibilities
using ConstellationParser and ConstellationManager.
"""

import asyncio
import pytest
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from galaxy.constellation.orchestrator.orchestrator import (
    TaskConstellationOrchestrator,
)
from galaxy.constellation.enums import TaskStatus, DeviceType
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.constellation.task_star import TaskStar


class MockConstellationDeviceManager:
    """Mock device manager for testing orchestrator."""

    def __init__(self):
        self.device_registry = Mock()
        self._connected_devices = ["device1", "device2"]

    def get_connected_devices(self):
        return self._connected_devices.copy()


class MockAgentProfile:
    """Mock device info for testing."""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.device_type = "desktop"
        self.capabilities = ["ui_automation"]
        self.metadata = {"platform": "windows"}


class TestTaskConstellationOrchestrator:
    """Test cases for the refactored TaskConstellationOrchestrator."""

    @pytest.fixture
    def mock_device_manager(self):
        """Create a mock device manager for testing."""
        device_manager = MockConstellationDeviceManager()

        def get_device_info(device_id):
            if device_id in device_manager._connected_devices:
                return MockAgentProfile(device_id)
            return None

        device_manager.device_registry.get_device_info.side_effect = get_device_info
        return device_manager

    @pytest.fixture
    def mock_event_bus(self):
        """Create a mock event bus for testing."""
        event_bus = Mock()
        event_bus.publish_event = AsyncMock()
        return event_bus

    @pytest.fixture
    def orchestrator(self, mock_device_manager, mock_event_bus):
        """Create a TaskConstellationOrchestrator for testing."""
        return TaskConstellationOrchestrator(
            device_manager=mock_device_manager,
            enable_logging=False,
            event_bus=mock_event_bus,
        )

    @pytest.fixture
    def orchestrator_no_device(self, mock_event_bus):
        """Create orchestrator without device manager."""
        return TaskConstellationOrchestrator(
            enable_logging=False, event_bus=mock_event_bus
        )

    @pytest.fixture
    def sample_tasks(self):
        """Create sample task descriptions for testing."""
        return ["Open browser", "Navigate to website", "Fill form", "Submit form"]

    def test_init_with_device_manager(self, mock_device_manager, mock_event_bus):
        """Test orchestrator initialization with device manager."""
        orchestrator = TaskConstellationOrchestrator(
            device_manager=mock_device_manager,
            enable_logging=True,
            event_bus=mock_event_bus,
        )

        assert orchestrator._device_manager is mock_device_manager
        assert orchestrator._event_bus is mock_event_bus
        assert orchestrator._logger is not None

    def test_init_without_device_manager(self, mock_event_bus):
        """Test orchestrator initialization without device manager."""
        orchestrator = TaskConstellationOrchestrator(
            enable_logging=False, event_bus=mock_event_bus
        )

        assert orchestrator._device_manager is None
        assert orchestrator._event_bus is mock_event_bus

    def test_set_device_manager(self, orchestrator_no_device, mock_device_manager):
        """Test setting device manager after initialization."""
        orchestrator_no_device.set_device_manager(mock_device_manager)

        assert orchestrator_no_device._device_manager is mock_device_manager
        assert (
            orchestrator_no_device._constellation_manager._device_manager
            is mock_device_manager
        )

    @pytest.mark.asyncio
    async def test_create_constellation_from_llm(self, orchestrator):
        """Test creating constellation from LLM output."""
        llm_output = """
        Task 1: Open browser
        Task 2: Navigate to site
        Dependencies: Task 1 -> Task 2
        """

        constellation = await orchestrator.create_constellation_from_llm(
            llm_output, "LLM Test Constellation"
        )

        assert isinstance(constellation, TaskConstellation)
        assert constellation.name == "LLM Test Constellation"
        # Should be registered with constellation manager
        assert (
            constellation.constellation_id
            in orchestrator._constellation_manager._managed_constellations
        )

    @pytest.mark.asyncio
    async def test_create_constellation_from_json(self, orchestrator):
        """Test creating constellation from JSON data."""
        json_data = """{
            "name": "JSON Test",
            "tasks": {
                "task1": {"task_id": "task1", "description": "Test task"}
            },
            "dependencies": []
        }"""

        constellation = await orchestrator.create_constellation_from_json(
            json_data, "JSON Constellation"
        )

        assert isinstance(constellation, TaskConstellation)
        assert constellation.name == "JSON Constellation"

    @pytest.mark.asyncio
    async def test_create_simple_constellation_sequential(
        self, orchestrator, sample_tasks
    ):
        """Test creating simple sequential constellation."""
        constellation = await orchestrator.create_simple_constellation(
            sample_tasks, "Sequential Test", sequential=True
        )

        assert isinstance(constellation, TaskConstellation)
        assert constellation.name == "Sequential Test"
        assert constellation.task_count == len(sample_tasks)
        assert constellation.dependency_count == len(sample_tasks) - 1

    @pytest.mark.asyncio
    async def test_create_simple_constellation_parallel(
        self, orchestrator, sample_tasks
    ):
        """Test creating simple parallel constellation."""
        constellation = await orchestrator.create_simple_constellation(
            sample_tasks, "Parallel Test", sequential=False
        )

        assert isinstance(constellation, TaskConstellation)
        assert constellation.name == "Parallel Test"
        assert constellation.task_count == len(sample_tasks)
        assert constellation.dependency_count == 0

    @pytest.mark.asyncio
    async def test_orchestrate_constellation_no_device_manager(
        self, orchestrator_no_device
    ):
        """Test orchestration without device manager raises error."""
        constellation = TaskConstellation(name="Test")

        with pytest.raises(ValueError, match="ConstellationDeviceManager not set"):
            await orchestrator_no_device.orchestrate_constellation(constellation)

    @pytest.mark.asyncio
    async def test_orchestrate_constellation_invalid_dag(self, orchestrator):
        """Test orchestration with invalid DAG structure."""
        constellation = TaskConstellation(name="Invalid DAG")
        # Create constellation that will fail validation
        # (empty constellation is considered invalid)

        with pytest.raises(ValueError, match="Invalid DAG"):
            await orchestrator.orchestrate_constellation(constellation)

    @pytest.mark.asyncio
    async def test_orchestrate_constellation_assignment_validation_failed(
        self, orchestrator
    ):
        """Test orchestration when device assignment validation fails."""
        constellation = TaskConstellation(name="Test Constellation")

        # Add a task
        task = TaskStar(task_id="task1", description="Test task")
        constellation.add_task(task)

        # Mock device manager to have no devices
        orchestrator._device_manager._connected_devices = []

        with pytest.raises(ValueError, match="No available devices"):
            await orchestrator.orchestrate_constellation(constellation)

    @pytest.mark.asyncio
    async def test_orchestrate_constellation_with_manual_assignments(
        self, orchestrator
    ):
        """Test orchestration with manual device assignments."""
        constellation = TaskConstellation(name="Manual Assignment Test")

        # Add tasks
        task1 = TaskStar(task_id="task1", description="First task")
        task2 = TaskStar(task_id="task2", description="Second task")
        constellation.add_task(task1)
        constellation.add_task(task2)

        # Mock task execution to complete immediately
        with patch.object(TaskStar, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Mock(result="success")

            device_assignments = {"task1": "device1", "task2": "device2"}
            result = await orchestrator.orchestrate_constellation(
                constellation, device_assignments
            )

            assert result["status"] == "completed"
            assert (
                result["total_tasks"] == 0
            )  # No results captured in this simplified version

    @pytest.mark.asyncio
    async def test_execute_single_task(self, orchestrator):
        """Test executing a single task."""
        task = TaskStar(task_id="single_task", description="Single test task")

        # Mock task execution
        with patch.object(TaskStar, "execute", new_callable=AsyncMock) as mock_execute:
            mock_result = Mock()
            mock_result.result = "task_completed"
            mock_execute.return_value = mock_result

            result = await orchestrator.execute_single_task(task, "device1")

            assert result == "task_completed"
            assert task.target_device_id == "device1"

    @pytest.mark.asyncio
    async def test_execute_single_task_auto_assign(self, orchestrator):
        """Test executing single task with auto device assignment."""
        task = TaskStar(task_id="auto_task", description="Auto assign task")

        with patch.object(TaskStar, "execute", new_callable=AsyncMock) as mock_execute:
            mock_result = Mock()
            mock_result.result = "auto_completed"
            mock_execute.return_value = mock_result

            result = await orchestrator.execute_single_task(task)

            assert result == "auto_completed"
            assert task.target_device_id in ["device1", "device2"]

    @pytest.mark.asyncio
    async def test_execute_single_task_no_devices(self, orchestrator):
        """Test executing single task when no devices available."""
        task = TaskStar(task_id="no_device_task", description="No device task")

        # Mock no available devices
        orchestrator._constellation_manager._device_manager._connected_devices = []

        with pytest.raises(ValueError, match="No available devices"):
            await orchestrator.execute_single_task(task)

    @pytest.mark.asyncio
    async def test_modify_constellation_with_llm(self, orchestrator):
        """Test modifying constellation with LLM request."""
        constellation = TaskConstellation(name="Original Constellation")
        task = TaskStar(task_id="original_task", description="Original task")
        constellation.add_task(task)

        modification_request = "Add a new task after the original task"

        modified = await orchestrator.modify_constellation_with_llm(
            constellation, modification_request
        )

        assert isinstance(modified, TaskConstellation)
        # In current implementation, this returns the same constellation
        # as LLM integration is not fully implemented

    @pytest.mark.asyncio
    async def test_get_constellation_status(self, orchestrator):
        """Test getting constellation status."""
        constellation = TaskConstellation(name="Status Test")
        task = TaskStar(task_id="status_task", description="Status task")
        constellation.add_task(task)

        # Register constellation
        orchestrator._constellation_manager.register_constellation(constellation)

        status = await orchestrator.get_constellation_status(constellation)

        assert status is not None
        assert status["name"] == "Status Test"
        assert "statistics" in status

    @pytest.mark.asyncio
    async def test_get_available_devices(self, orchestrator):
        """Test getting available devices."""
        devices = await orchestrator.get_available_devices()

        assert len(devices) == 2
        assert all("device_id" in device for device in devices)

    @pytest.mark.asyncio
    async def test_assign_devices_automatically(self, orchestrator):
        """Test automatic device assignment."""
        constellation = TaskConstellation(name="Assignment Test")

        task1 = TaskStar(task_id="task1", description="First task")
        task2 = TaskStar(task_id="task2", description="Second task")
        constellation.add_task(task1)
        constellation.add_task(task2)

        assignments = await orchestrator.assign_devices_automatically(
            constellation, strategy="round_robin"
        )

        assert len(assignments) == 2
        assert "task1" in assignments
        assert "task2" in assignments

    @pytest.mark.asyncio
    async def test_assign_devices_with_preferences(self, orchestrator):
        """Test device assignment with preferences."""
        constellation = TaskConstellation(name="Preference Test")

        task1 = TaskStar(task_id="task1", description="Preferred task")
        constellation.add_task(task1)

        preferences = {"task1": "device2"}
        assignments = await orchestrator.assign_devices_automatically(
            constellation, device_preferences=preferences
        )

        assert assignments["task1"] == "device2"

    def test_export_constellation(self, orchestrator):
        """Test exporting constellation."""
        constellation = TaskConstellation(name="Export Test")
        task = TaskStar(task_id="export_task", description="Export task")
        constellation.add_task(task)

        # Test JSON export
        json_export = orchestrator.export_constellation(constellation, "json")
        assert isinstance(json_export, str)
        assert "Export Test" in json_export

        # Test LLM export
        llm_export = orchestrator.export_constellation(constellation, "llm")
        assert isinstance(llm_export, str)
        assert "Export Test" in llm_export

    @pytest.mark.asyncio
    async def test_import_constellation_json(self, orchestrator):
        """Test importing constellation from JSON."""
        json_data = """{
            "name": "Import Test",
            "tasks": {
                "import_task": {
                    "task_id": "import_task",
                    "description": "Imported task"
                }
            },
            "dependencies": []
        }"""

        constellation = await orchestrator.import_constellation(json_data, "json")

        assert isinstance(constellation, TaskConstellation)
        assert "import_task" in constellation.tasks

    @pytest.mark.asyncio
    async def test_import_constellation_llm(self, orchestrator):
        """Test importing constellation from LLM format."""
        llm_data = """
        Task: Import task
        Description: Task created from LLM import
        """

        constellation = await orchestrator.import_constellation(llm_data, "llm")

        assert isinstance(constellation, TaskConstellation)

    @pytest.mark.asyncio
    async def test_import_constellation_unsupported_format(self, orchestrator):
        """Test importing with unsupported format."""
        with pytest.raises(ValueError, match="Unsupported import format"):
            await orchestrator.import_constellation("data", "unsupported")

    def test_add_task_to_constellation(self, orchestrator):
        """Test adding task to constellation."""
        constellation = TaskConstellation(name="Add Task Test")
        original_task = TaskStar(task_id="original", description="Original task")
        constellation.add_task(original_task)

        new_task = TaskStar(task_id="new_task", description="New task")
        success = orchestrator.add_task_to_constellation(
            constellation, new_task, dependencies=["original"]
        )

        assert success
        assert "new_task" in constellation.tasks

    def test_remove_task_from_constellation(self, orchestrator):
        """Test removing task from constellation."""
        constellation = TaskConstellation(name="Remove Task Test")

        task1 = TaskStar(task_id="task1", description="Task 1")
        task2 = TaskStar(task_id="task2", description="Task 2")
        constellation.add_task(task1)
        constellation.add_task(task2)

        success = orchestrator.remove_task_from_constellation(constellation, "task1")

        assert success
        assert "task1" not in constellation.tasks
        assert "task2" in constellation.tasks

    def test_clone_constellation(self, orchestrator):
        """Test cloning a constellation."""
        original = TaskConstellation(name="Original")
        task = TaskStar(task_id="task1", description="Original task")
        original.add_task(task)

        cloned = orchestrator.clone_constellation(original, "Cloned")

        assert isinstance(cloned, TaskConstellation)
        assert cloned.name == "Cloned"
        assert cloned.constellation_id != original.constellation_id
        assert cloned.task_count == original.task_count

    def test_merge_constellations(self, orchestrator):
        """Test merging two constellations."""
        constellation1 = TaskConstellation(name="First")
        task1 = TaskStar(task_id="task1", description="Task 1")
        constellation1.add_task(task1)

        constellation2 = TaskConstellation(name="Second")
        task2 = TaskStar(task_id="task2", description="Task 2")
        constellation2.add_task(task2)

        merged = orchestrator.merge_constellations(
            constellation1, constellation2, "Merged"
        )

        assert isinstance(merged, TaskConstellation)
        assert merged.name == "Merged"
        assert merged.task_count == 2
        assert "c1_task1" in merged.tasks
        assert "c2_task2" in merged.tasks


class TestTaskConstellationOrchestratorIntegration:
    """Integration tests for TaskConstellationOrchestrator."""

    @pytest.fixture
    def mock_device_manager(self):
        """Create mock device manager for integration testing."""
        device_manager = MockConstellationDeviceManager()

        def get_device_info(device_id):
            if device_id in device_manager._connected_devices:
                return MockAgentProfile(device_id)
            return None

        device_manager.device_registry.get_device_info.side_effect = get_device_info
        return device_manager

    @pytest.fixture
    def orchestrator(self, mock_device_manager):
        """Create orchestrator for integration testing."""
        return TaskConstellationOrchestrator(
            device_manager=mock_device_manager, enable_logging=False
        )

    @pytest.mark.asyncio
    async def test_end_to_end_constellation_workflow(self, orchestrator):
        """Test complete constellation workflow from creation to execution."""
        # Create constellation from task descriptions
        task_descriptions = ["Open app", "Perform action", "Verify result"]
        constellation = await orchestrator.create_simple_constellation(
            task_descriptions, "E2E Test", sequential=True
        )

        # Export and reimport
        exported = orchestrator.export_constellation(constellation, "json")
        reimported = await orchestrator.import_constellation(exported, "json")

        assert reimported.task_count == constellation.task_count

        # Clone constellation
        cloned = orchestrator.clone_constellation(constellation, "E2E Cloned")
        assert cloned.task_count == constellation.task_count

        # Assign devices
        assignments = await orchestrator.assign_devices_automatically(cloned)
        assert len(assignments) == 3

        # Get status
        status = await orchestrator.get_constellation_status(cloned)
        assert status is not None
        assert status["name"] == "E2E Cloned"

    @pytest.mark.asyncio
    async def test_complex_constellation_operations(self, orchestrator):
        """Test complex constellation operations and modifications."""
        # Create base constellation
        constellation = await orchestrator.create_simple_constellation(
            ["Base task 1", "Base task 2"], "Complex Test"
        )

        # Add additional task
        new_task = TaskStar(task_id="additional", description="Additional task")
        success = orchestrator.add_task_to_constellation(constellation, new_task)
        assert success

        # Create another constellation to merge
        other_constellation = await orchestrator.create_simple_constellation(
            ["Other task"], "Other"
        )

        # Merge constellations
        merged = orchestrator.merge_constellations(
            constellation, other_constellation, "Complex Merged"
        )
        assert merged.task_count == 4  # 2 + 1 + 1

        # Assign devices with different strategies
        await orchestrator.assign_devices_automatically(merged, strategy="load_balance")

        # Verify all tasks have assignments
        for task in merged.tasks.values():
            assert task.target_device_id is not None

        # Remove a task (use the actual task ID from merged constellation)
        merged_task_ids = list(merged.tasks.keys())
        # Find a task that contains "additional" in its ID
        task_to_remove = next(
            (tid for tid in merged_task_ids if "additional" in tid), None
        )
        if task_to_remove:
            success = orchestrator.remove_task_from_constellation(
                merged, task_to_remove
            )
        else:
            # If no task with "additional" found, use the first task
            success = orchestrator.remove_task_from_constellation(
                merged, merged_task_ids[0]
            )
        assert success
        assert merged.task_count == 3

    @pytest.mark.asyncio
    async def test_orchestration_with_task_execution_mock(self, orchestrator):
        """Test orchestration with mocked task execution."""
        constellation = await orchestrator.create_simple_constellation(
            ["Mock task 1", "Mock task 2"], "Mock Test", sequential=True
        )

        # Mock task execution to return success
        with patch.object(TaskStar, "execute", new_callable=AsyncMock) as mock_execute:
            mock_result = Mock()
            mock_result.result = "mock_success"
            mock_execute.return_value = mock_result

            result = await orchestrator.orchestrate_constellation(constellation)

            assert result["status"] == "completed"
            # Verify task execution was called
            assert mock_execute.call_count >= 2  # Should execute both tasks

    @pytest.mark.asyncio
    async def test_error_handling_in_orchestration(self, orchestrator):
        """Test error handling during orchestration."""
        constellation = await orchestrator.create_simple_constellation(
            ["Error task"], "Error Test"
        )

        # Mock task execution to raise exception
        with patch.object(TaskStar, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = Exception("Task execution failed")

            # Execute orchestration (it should handle the exception)
            await orchestrator.orchestrate_constellation(constellation)

            # Check that the constellation is in failed state
            assert constellation.state.value == "failed"
