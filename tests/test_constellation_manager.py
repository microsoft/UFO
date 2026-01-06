# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for ConstellationManager.

Tests device assignment, status tracking, and resource management
for TaskConstellation objects.
"""

import asyncio
import pytest
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock

from galaxy.constellation.orchestrator.constellation_manager import (
    ConstellationManager,
)
from galaxy.constellation.enums import TaskStatus, DeviceType
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.constellation.task_star import TaskStar


class MockDeviceManager:
    """Mock device manager for testing."""

    def __init__(self):
        self.device_registry = Mock()
        self._connected_devices = ["device1", "device2", "device3"]

    def get_connected_devices(self):
        return self._connected_devices.copy()


class MockAgentProfile:
    """Mock device info for testing."""

    def __init__(self, device_id: str, device_type: str = "desktop"):
        self.device_id = device_id
        self.device_type = device_type
        self.capabilities = ["ui_automation", "web_browsing"]
        self.metadata = {"platform": "windows", "version": "11"}


class TestConstellationManager:
    """Test cases for ConstellationManager class."""

    @pytest.fixture
    def mock_device_manager(self):
        """Create a mock device manager for testing."""
        device_manager = MockDeviceManager()

        # Set up device registry mock
        def get_device_info(device_id):
            if device_id in device_manager._connected_devices:
                return MockAgentProfile(device_id)
            return None

        device_manager.device_registry.get_device_info.side_effect = get_device_info
        return device_manager

    @pytest.fixture
    def manager(self, mock_device_manager):
        """Create a ConstellationManager instance for testing."""
        return ConstellationManager(mock_device_manager, enable_logging=False)

    @pytest.fixture
    def manager_no_device(self):
        """Create a ConstellationManager without device manager."""
        return ConstellationManager(enable_logging=False)

    @pytest.fixture
    def sample_constellation(self):
        """Create a sample constellation for testing."""
        constellation = TaskConstellation(name="Test Constellation")

        # Add tasks
        task1 = TaskStar(task_id="task1", description="First task")
        task2 = TaskStar(task_id="task2", description="Second task")
        task3 = TaskStar(task_id="task3", description="Third task")

        constellation.add_task(task1)
        constellation.add_task(task2)
        constellation.add_task(task3)

        return constellation

    def test_init_with_device_manager(self, mock_device_manager):
        """Test initialization with device manager."""
        manager = ConstellationManager(mock_device_manager, enable_logging=True)

        assert manager._device_manager is mock_device_manager
        assert manager._logger is not None

    def test_init_without_device_manager(self):
        """Test initialization without device manager."""
        manager = ConstellationManager(enable_logging=False)

        assert manager._device_manager is None
        assert manager._logger is None

    def test_set_device_manager(self, manager_no_device, mock_device_manager):
        """Test setting device manager after initialization."""
        manager_no_device.set_device_manager(mock_device_manager)

        assert manager_no_device._device_manager is mock_device_manager

    def test_register_constellation(self, manager, sample_constellation):
        """Test registering a constellation for management."""
        metadata = {"priority": "high", "user": "test_user"}

        constellation_id = manager.register_constellation(
            sample_constellation, metadata
        )

        assert constellation_id == sample_constellation.constellation_id
        assert constellation_id in manager._managed_constellations
        assert manager._managed_constellations[constellation_id] is sample_constellation
        assert manager._constellation_metadata[constellation_id] == metadata

    def test_register_constellation_without_metadata(
        self, manager, sample_constellation
    ):
        """Test registering constellation without metadata."""
        constellation_id = manager.register_constellation(sample_constellation)

        assert constellation_id in manager._managed_constellations
        assert manager._constellation_metadata[constellation_id] == {}

    def test_unregister_constellation(self, manager, sample_constellation):
        """Test unregistering a constellation."""
        # Register first
        constellation_id = manager.register_constellation(sample_constellation)

        # Unregister
        success = manager.unregister_constellation(constellation_id)

        assert success
        assert constellation_id not in manager._managed_constellations
        assert constellation_id not in manager._constellation_metadata

    def test_unregister_nonexistent_constellation(self, manager):
        """Test unregistering a nonexistent constellation."""
        success = manager.unregister_constellation("nonexistent_id")

        assert not success

    def test_get_constellation(self, manager, sample_constellation):
        """Test getting a managed constellation by ID."""
        constellation_id = manager.register_constellation(sample_constellation)

        retrieved = manager.get_constellation(constellation_id)

        assert retrieved is sample_constellation

    def test_get_nonexistent_constellation(self, manager):
        """Test getting a nonexistent constellation."""
        retrieved = manager.get_constellation("nonexistent_id")

        assert retrieved is None

    def test_list_constellations(self, manager, sample_constellation):
        """Test listing all managed constellations."""
        metadata = {"priority": "high"}
        constellation_id = manager.register_constellation(
            sample_constellation, metadata
        )

        constellations = manager.list_constellations()

        assert len(constellations) == 1
        constellation_info = constellations[0]
        assert constellation_info["constellation_id"] == constellation_id
        assert constellation_info["name"] == sample_constellation.name
        assert constellation_info["task_count"] == sample_constellation.task_count
        assert constellation_info["metadata"] == metadata

    def test_list_constellations_empty(self, manager):
        """Test listing constellations when none are registered."""
        constellations = manager.list_constellations()

        assert len(constellations) == 0

    @pytest.mark.asyncio
    async def test_assign_devices_round_robin(self, manager, sample_constellation):
        """Test round robin device assignment strategy."""
        assignments = await manager.assign_devices_automatically(
            sample_constellation, strategy="round_robin"
        )

        assert len(assignments) == 3  # 3 tasks
        assert all(
            task_id in assignments for task_id in sample_constellation.tasks.keys()
        )

        # Verify round robin distribution
        assigned_devices = list(assignments.values())
        assert len(set(assigned_devices)) <= 3  # At most 3 different devices

    @pytest.mark.asyncio
    async def test_assign_devices_capability_match(self, manager, sample_constellation):
        """Test capability matching device assignment strategy."""
        # Set device types for tasks
        sample_constellation.tasks["task1"].device_type = DeviceType.WINDOWS
        sample_constellation.tasks["task2"].device_type = (
            DeviceType.MACOS
        )  # Will fall back

        assignments = await manager.assign_devices_automatically(
            sample_constellation, strategy="capability_match"
        )

        assert len(assignments) == 3
        assert all(
            task_id in assignments for task_id in sample_constellation.tasks.keys()
        )

    @pytest.mark.asyncio
    async def test_assign_devices_load_balance(self, manager, sample_constellation):
        """Test load balanced device assignment strategy."""
        assignments = await manager.assign_devices_automatically(
            sample_constellation, strategy="load_balance"
        )

        assert len(assignments) == 3
        assert all(
            task_id in assignments for task_id in sample_constellation.tasks.keys()
        )

    @pytest.mark.asyncio
    async def test_assign_devices_with_preferences(self, manager, sample_constellation):
        """Test device assignment with preferences."""
        preferences = {"task1": "device2", "task2": "device1"}

        assignments = await manager.assign_devices_automatically(
            sample_constellation, strategy="round_robin", device_preferences=preferences
        )

        assert assignments["task1"] == "device2"
        assert assignments["task2"] == "device1"
        assert "task3" in assignments  # Should be assigned automatically

    @pytest.mark.asyncio
    async def test_assign_devices_invalid_strategy(self, manager, sample_constellation):
        """Test device assignment with invalid strategy."""
        with pytest.raises(ValueError, match="Unknown assignment strategy"):
            await manager.assign_devices_automatically(
                sample_constellation, strategy="invalid_strategy"
            )

    @pytest.mark.asyncio
    async def test_assign_devices_no_device_manager(
        self, manager_no_device, sample_constellation
    ):
        """Test device assignment without device manager."""
        with pytest.raises(ValueError, match="Device manager not available"):
            await manager_no_device.assign_devices_automatically(sample_constellation)

    @pytest.mark.asyncio
    async def test_assign_devices_no_available_devices(
        self, manager, sample_constellation
    ):
        """Test device assignment when no devices are available."""
        # Mock empty device list
        manager._device_manager._connected_devices = []

        with pytest.raises(ValueError, match="No available devices"):
            await manager.assign_devices_automatically(sample_constellation)

    @pytest.mark.asyncio
    async def test_get_constellation_status(self, manager, sample_constellation):
        """Test getting constellation status."""
        constellation_id = manager.register_constellation(
            sample_constellation, {"priority": "high"}
        )

        status = await manager.get_constellation_status(constellation_id)

        assert status is not None
        assert status["constellation_id"] == constellation_id
        assert status["name"] == sample_constellation.name
        assert "statistics" in status
        assert "ready_tasks" in status
        assert "metadata" in status
        assert status["metadata"]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_get_constellation_status_nonexistent(self, manager):
        """Test getting status of nonexistent constellation."""
        status = await manager.get_constellation_status("nonexistent_id")

        assert status is None

    @pytest.mark.asyncio
    async def test_get_available_devices(self, manager):
        """Test getting available devices."""
        devices = await manager.get_available_devices()

        assert len(devices) == 3
        for device in devices:
            assert "device_id" in device
            assert "device_type" in device
            assert "capabilities" in device
            assert "status" in device
            assert device["status"] == "connected"

    @pytest.mark.asyncio
    async def test_get_available_devices_no_manager(self, manager_no_device):
        """Test getting available devices without device manager."""
        devices = await manager_no_device.get_available_devices()

        assert len(devices) == 0

    def test_validate_constellation_assignments_valid(
        self, manager, sample_constellation
    ):
        """Test validating constellation with valid device assignments."""
        # Assign devices to all tasks
        for i, task in enumerate(sample_constellation.tasks.values()):
            task.target_device_id = f"device{i+1}"

        is_valid, errors = manager.validate_constellation_assignments(
            sample_constellation
        )

        assert is_valid
        assert len(errors) == 0

    def test_validate_constellation_assignments_invalid(
        self, manager, sample_constellation
    ):
        """Test validating constellation with missing device assignments."""
        # Leave one task without device assignment
        sample_constellation.tasks["task1"].target_device_id = "device1"
        sample_constellation.tasks["task2"].target_device_id = "device2"
        # task3 has no assignment

        is_valid, errors = manager.validate_constellation_assignments(
            sample_constellation
        )

        assert not is_valid
        assert len(errors) == 1
        assert "task3" in errors[0]
        assert "no device assignment" in errors[0]

    def test_get_task_device_info(self, manager, sample_constellation):
        """Test getting device info for a specific task."""
        # Assign device to task
        sample_constellation.tasks["task1"].target_device_id = "device1"

        device_info = manager.get_task_device_info(sample_constellation, "task1")

        assert device_info is not None
        assert device_info["device_id"] == "device1"
        assert "device_type" in device_info
        assert "capabilities" in device_info

    def test_get_task_device_info_no_assignment(self, manager, sample_constellation):
        """Test getting device info for task without assignment."""
        device_info = manager.get_task_device_info(sample_constellation, "task1")

        assert device_info is None

    def test_get_task_device_info_nonexistent_task(self, manager, sample_constellation):
        """Test getting device info for nonexistent task."""
        device_info = manager.get_task_device_info(
            sample_constellation, "nonexistent_task"
        )

        assert device_info is None

    def test_reassign_task_device(self, manager, sample_constellation):
        """Test reassigning a task to a different device."""
        # Initial assignment
        sample_constellation.tasks["task1"].target_device_id = "device1"

        success = manager.reassign_task_device(sample_constellation, "task1", "device2")

        assert success
        assert sample_constellation.tasks["task1"].target_device_id == "device2"

    def test_reassign_nonexistent_task(self, manager, sample_constellation):
        """Test reassigning a nonexistent task."""
        success = manager.reassign_task_device(
            sample_constellation, "nonexistent_task", "device1"
        )

        assert not success

    def test_clear_device_assignments(self, manager, sample_constellation):
        """Test clearing all device assignments."""
        # Assign devices to all tasks
        for i, task in enumerate(sample_constellation.tasks.values()):
            task.target_device_id = f"device{i+1}"

        cleared_count = manager.clear_device_assignments(sample_constellation)

        assert cleared_count == 3
        for task in sample_constellation.tasks.values():
            assert task.target_device_id is None

    def test_clear_device_assignments_none_assigned(
        self, manager, sample_constellation
    ):
        """Test clearing device assignments when none are assigned."""
        cleared_count = manager.clear_device_assignments(sample_constellation)

        assert cleared_count == 0

    def test_get_device_utilization(self, manager, sample_constellation):
        """Test getting device utilization statistics."""
        # Assign devices (some devices get multiple tasks)
        sample_constellation.tasks["task1"].target_device_id = "device1"
        sample_constellation.tasks["task2"].target_device_id = "device1"
        sample_constellation.tasks["task3"].target_device_id = "device2"

        utilization = manager.get_device_utilization(sample_constellation)

        assert utilization["device1"] == 2
        assert utilization["device2"] == 1
        assert "device3" not in utilization  # No tasks assigned

    def test_get_device_utilization_no_assignments(self, manager, sample_constellation):
        """Test getting device utilization with no assignments."""
        utilization = manager.get_device_utilization(sample_constellation)

        assert len(utilization) == 0

    @pytest.mark.asyncio
    async def test_assign_devices_with_device_manager_error(
        self, manager, sample_constellation
    ):
        """Test device assignment when device manager throws error."""
        # Mock device manager to raise exception
        manager._device_manager.get_connected_devices = Mock(
            side_effect=Exception("Device manager error")
        )

        with pytest.raises(ValueError, match="No available devices"):
            await manager.assign_devices_automatically(sample_constellation)


class TestConstellationManagerIntegration:
    """Integration tests for ConstellationManager with other components."""

    @pytest.fixture
    def mock_device_manager(self):
        """Create a mock device manager for integration testing."""
        device_manager = MockDeviceManager()

        def get_device_info(device_id):
            if device_id in device_manager._connected_devices:
                return MockAgentProfile(device_id)
            return None

        device_manager.device_registry.get_device_info.side_effect = get_device_info
        return device_manager

    @pytest.fixture
    def manager(self, mock_device_manager):
        """Create a ConstellationManager for integration testing."""
        return ConstellationManager(mock_device_manager, enable_logging=False)

    @pytest.mark.asyncio
    async def test_full_constellation_lifecycle(self, manager):
        """Test complete constellation management lifecycle."""
        # Create constellation
        constellation = TaskConstellation(name="Lifecycle Test")
        for i in range(5):
            task = TaskStar(task_id=f"task_{i+1}", description=f"Task {i+1}")
            constellation.add_task(task)

        # Register
        constellation_id = manager.register_constellation(
            constellation, {"test": "lifecycle"}
        )

        # Assign devices
        assignments = await manager.assign_devices_automatically(
            constellation, strategy="load_balance"
        )
        assert len(assignments) == 5

        # Validate assignments
        is_valid, errors = manager.validate_constellation_assignments(constellation)
        assert is_valid

        # Get status
        status = await manager.get_constellation_status(constellation_id)
        assert status is not None
        assert status["name"] == "Lifecycle Test"

        # Get utilization
        utilization = manager.get_device_utilization(constellation)
        assert len(utilization) > 0

        # Reassign one task
        success = manager.reassign_task_device(constellation, "task_1", "device1")
        assert success

        # Clear assignments
        cleared = manager.clear_device_assignments(constellation)
        assert cleared == 5

        # Unregister
        success = manager.unregister_constellation(constellation_id)
        assert success

    @pytest.mark.asyncio
    async def test_multiple_constellations_management(self, manager):
        """Test managing multiple constellations simultaneously."""
        constellations = []

        # Create and register multiple constellations
        for i in range(3):
            constellation = TaskConstellation(name=f"Constellation {i+1}")
            for j in range(2):
                task = TaskStar(
                    task_id=f"c{i+1}_task_{j+1}",
                    description=f"Task {j+1} in constellation {i+1}",
                )
                constellation.add_task(task)

            constellation_id = manager.register_constellation(constellation)
            constellations.append((constellation_id, constellation))

        # List all constellations
        constellation_list = manager.list_constellations()
        assert len(constellation_list) == 3

        # Assign devices to all constellations
        for constellation_id, constellation in constellations:
            assignments = await manager.assign_devices_automatically(constellation)
            assert len(assignments) == 2

        # Validate all have assignments
        for constellation_id, constellation in constellations:
            is_valid, errors = manager.validate_constellation_assignments(constellation)
            assert is_valid

        # Unregister all
        for constellation_id, constellation in constellations:
            success = manager.unregister_constellation(constellation_id)
            assert success

        # Verify list is empty
        constellation_list = manager.list_constellations()
        assert len(constellation_list) == 0

    @pytest.mark.asyncio
    async def test_device_assignment_strategies_comparison(self, manager):
        """Test and compare different device assignment strategies."""
        constellation = TaskConstellation(name="Strategy Test")

        # Create tasks with different device type preferences
        task1 = TaskStar(task_id="task1", description="Windows task")
        task1.device_type = DeviceType.WINDOWS

        task2 = TaskStar(task_id="task2", description="MacOS task")
        task2.device_type = DeviceType.MACOS

        task3 = TaskStar(task_id="task3", description="Any device task")

        constellation.add_task(task1)
        constellation.add_task(task2)
        constellation.add_task(task3)

        # Test round robin
        manager.clear_device_assignments(constellation)
        assignments_rr = await manager.assign_devices_automatically(
            constellation, strategy="round_robin"
        )

        # Test capability match
        manager.clear_device_assignments(constellation)
        assignments_cm = await manager.assign_devices_automatically(
            constellation, strategy="capability_match"
        )

        # Test load balance
        manager.clear_device_assignments(constellation)
        assignments_lb = await manager.assign_devices_automatically(
            constellation, strategy="load_balance"
        )

        # All strategies should assign all tasks
        assert len(assignments_rr) == 3
        assert len(assignments_cm) == 3
        assert len(assignments_lb) == 3

        # Assignments may differ between strategies
        # but all should be valid device IDs
        all_device_ids = ["device1", "device2", "device3"]
        for assignments in [assignments_rr, assignments_cm, assignments_lb]:
            assert all(
                device_id in all_device_ids for device_id in assignments.values()
            )
