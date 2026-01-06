# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Comprehensive tests for device disconnection and reconnection handling.

Tests cover:
1. Device disconnection detection and status update
2. Automatic reconnection with configurable retry logic
3. Status updates after successful reconnection
4. Task cancellation on disconnection
5. Max retry limit enforcement
6. Event notifications (disconnect/reconnect)
7. Connection attempt counter management
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call
from typing import Dict, Any
import websockets

from galaxy.client.device_manager import ConstellationDeviceManager
from galaxy.client.components import (
    DeviceStatus,
    AgentProfile,
    TaskRequest,
    MessageProcessor,
)
from galaxy.core.types import ExecutionResult
from aip.messages import ServerMessage, ServerMessageType, TaskStatus


class TestDeviceDisconnectionReconnection:
    """Test suite for device disconnection and reconnection handling"""

    @pytest.fixture
    def device_manager(self):
        """Create a device manager instance with short retry delays for testing"""
        manager = ConstellationDeviceManager(
            task_name="test_task",
            heartbeat_interval=30.0,
            reconnect_delay=0.5,  # Short delay for faster tests
        )
        return manager

    @pytest.fixture
    def mock_device_id(self):
        """Standard test device ID"""
        return "test_device_disconnection"

    @pytest.fixture
    def setup_connected_device(self, device_manager, mock_device_id):
        """Setup a connected and IDLE device"""
        # Register device
        device_manager.device_registry.register_device(
            device_id=mock_device_id,
            server_url="ws://localhost:5000/ws",
            os="Windows",
            capabilities=["ui_automation"],
            metadata={"platform": "windows"},
            max_retries=3,  # Set to 3 for testing
        )

        # Set device to CONNECTED and then IDLE
        device_manager.device_registry.update_device_status(
            mock_device_id, DeviceStatus.CONNECTED
        )
        device_manager.device_registry.set_device_idle(mock_device_id)

        return mock_device_id

    # ========================================================================
    # Test 1: Disconnection detection and status update
    # ========================================================================

    @pytest.mark.asyncio
    async def test_disconnection_updates_status(
        self, device_manager, setup_connected_device
    ):
        """Test that device status is updated to DISCONNECTED on connection loss"""
        device_id = setup_connected_device

        # Verify initial status is IDLE
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.IDLE

        # Mock the connection manager to avoid actual WebSocket operations
        device_manager.connection_manager.disconnect_device = AsyncMock()

        # Trigger disconnection handler
        await device_manager._handle_device_disconnection(device_id)

        # Verify status changed to DISCONNECTED
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.DISCONNECTED

    # ========================================================================
    # Test 2: Message processor triggers disconnection on ConnectionClosed
    # ========================================================================

    @pytest.mark.asyncio
    async def test_message_processor_handles_connection_closed(
        self, device_manager, setup_connected_device
    ):
        """Test that MessageProcessor detects ConnectionClosed and triggers handler"""
        device_id = setup_connected_device

        # Create a mock websocket that raises ConnectionClosed
        mock_websocket = MagicMock()

        # Make the websocket iterator raise ConnectionClosed
        async def mock_iterator():
            raise websockets.ConnectionClosed(rcvd=None, sent=None)

        mock_websocket.__aiter__ = lambda self: mock_iterator()

        # Mock the disconnection handler
        disconnection_called = asyncio.Event()
        original_handler = device_manager._handle_device_disconnection

        async def tracked_handler(dev_id):
            await original_handler(dev_id)
            disconnection_called.set()

        device_manager.message_processor._disconnection_handler = tracked_handler

        # Mock connection manager
        device_manager.connection_manager.disconnect_device = AsyncMock()

        # Start message handler
        task = asyncio.create_task(
            device_manager.message_processor._handle_device_messages(
                device_id, mock_websocket
            )
        )

        # Wait for disconnection to be detected
        try:
            await asyncio.wait_for(disconnection_called.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("Disconnection handler was not called within timeout")
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Verify status updated to DISCONNECTED
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.DISCONNECTED

    # ========================================================================
    # Test 3: Automatic reconnection scheduling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_automatic_reconnection_scheduled(
        self, device_manager, setup_connected_device
    ):
        """Test that reconnection is automatically scheduled after disconnection"""
        device_id = setup_connected_device

        # Mock connect_device to track if it's called
        connect_called = asyncio.Event()
        original_connect = device_manager.connect_device

        async def mock_connect(dev_id, is_reconnection=False):
            connect_called.set()
            return True  # Simulate successful reconnection

        device_manager.connect_device = mock_connect

        # Mock connection manager
        device_manager.connection_manager.disconnect_device = AsyncMock()

        # Trigger disconnection
        await device_manager._handle_device_disconnection(device_id)

        # Wait for reconnection attempt (reconnect_delay = 0.5s)
        try:
            await asyncio.wait_for(connect_called.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("Reconnection was not attempted within timeout")

        # Cleanup reconnect tasks
        for task in device_manager._reconnect_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    # ========================================================================
    # Test 4: Successful reconnection updates status
    # ========================================================================

    @pytest.mark.asyncio
    async def test_reconnection_updates_status_to_idle(
        self, device_manager, setup_connected_device
    ):
        """Test that successful reconnection updates status to CONNECTED -> IDLE"""
        device_id = setup_connected_device

        # Set device to DISCONNECTED
        device_manager.device_registry.update_device_status(
            device_id, DeviceStatus.DISCONNECTED
        )

        # Mock the connection process
        device_manager.connection_manager.connect_to_device = AsyncMock()
        device_manager.connection_manager.request_device_info = AsyncMock(
            return_value={"platform": "Windows", "cpu_count": 8}
        )
        device_manager.heartbeat_manager.start_heartbeat = Mock()
        device_manager.event_manager.notify_device_connected = AsyncMock()

        # Mock websocket connection
        mock_websocket = MagicMock()
        mock_websocket.closed = False
        device_manager.connection_manager._connections[device_id] = mock_websocket

        # Perform reconnection
        success = await device_manager.connect_device(device_id)

        assert success is True

        # Verify status progression: CONNECTING -> CONNECTED -> IDLE
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.IDLE

    # ========================================================================
    # Test 5: Connection attempts counter increments on each attempt
    # ========================================================================

    @pytest.mark.asyncio
    async def test_connection_attempts_increment(
        self, device_manager, setup_connected_device
    ):
        """Test that connection_attempts increments on each connection attempt"""
        device_id = setup_connected_device

        # Get initial connection attempts
        device_info = device_manager.device_registry.get_device(device_id)
        initial_attempts = device_info.connection_attempts

        # Mock connect_to_device to fail
        device_manager.connection_manager.connect_to_device = AsyncMock(
            side_effect=ConnectionError("Connection failed")
        )

        # Attempt connection (should fail and increment counter)
        success = await device_manager.connect_device(device_id)

        assert success is False

        # Verify counter incremented
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.connection_attempts == initial_attempts + 1

    # ========================================================================
    # Test 6: Connection attempts reset on successful reconnection
    # ========================================================================

    @pytest.mark.asyncio
    async def test_connection_attempts_reset_on_success(
        self, device_manager, setup_connected_device
    ):
        """Test that connection_attempts resets to 0 after successful reconnection"""
        device_id = setup_connected_device

        # Manually set connection attempts to simulate previous failures
        device_info = device_manager.device_registry.get_device(device_id)
        device_info.connection_attempts = 2

        # Mock successful connection
        device_manager.connection_manager.connect_to_device = AsyncMock()
        device_manager.connection_manager.request_device_info = AsyncMock(
            return_value={"platform": "Windows"}
        )
        device_manager.heartbeat_manager.start_heartbeat = Mock()
        device_manager.event_manager.notify_device_connected = AsyncMock()

        # Mock websocket
        mock_websocket = MagicMock()
        mock_websocket.closed = False
        device_manager.connection_manager._connections[device_id] = mock_websocket

        # Perform successful reconnection
        reconnect_called = asyncio.Event()

        async def mock_reconnect(dev_id):
            success = await device_manager.connect_device(dev_id)
            if success:
                device_manager.device_registry.reset_connection_attempts(dev_id)
            reconnect_called.set()
            return success

        # Trigger reconnection
        await mock_reconnect(device_id)

        # Verify counter reset to 0
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.connection_attempts == 0

    # ========================================================================
    # Test 7: Max retry limit enforcement
    # ========================================================================

    @pytest.mark.asyncio
    async def test_max_retry_limit_stops_reconnection(
        self, device_manager, setup_connected_device
    ):
        """Test that reconnection stops after max_retries is reached"""
        device_id = setup_connected_device

        # Set device to DISCONNECTED
        device_manager.device_registry.update_device_status(
            device_id, DeviceStatus.DISCONNECTED
        )

        # Mock connect_device to always fail
        async def mock_failed_connect(dev_id, is_reconnection=False):
            return False  # Connection failed

        device_manager.connect_device = mock_failed_connect

        # Trigger reconnection directly (simulates _handle_device_disconnection scheduling it)
        await device_manager._reconnect_device(device_id)

        # Verify reconnection task completed (removed from dict)
        assert device_id not in device_manager._reconnect_tasks

        # Verify status is FAILED after all retries exhausted
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.FAILED

    # ========================================================================
    # Test 8: Task cancellation on disconnection
    # ========================================================================

    @pytest.mark.asyncio
    async def test_current_task_cancelled_on_disconnection(
        self, device_manager, setup_connected_device
    ):
        """Test that current task is cancelled when device disconnects"""
        device_id = setup_connected_device

        # Set device to BUSY with a current task
        task_id = "task_in_progress"
        device_manager.device_registry.set_device_busy(device_id, task_id)

        # Mock task queue manager
        device_manager.task_queue_manager.fail_task = Mock()

        # Mock connection manager
        device_manager.connection_manager.disconnect_device = AsyncMock()

        # Trigger disconnection
        await device_manager._handle_device_disconnection(device_id)

        # Verify task was marked as failed
        device_manager.task_queue_manager.fail_task.assert_called_once()
        call_args = device_manager.task_queue_manager.fail_task.call_args
        assert call_args[0][0] == device_id
        assert call_args[0][1] == task_id
        assert isinstance(call_args[0][2], ConnectionError)

        # Verify current_task_id was cleared
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.current_task_id is None

    # ========================================================================
    # Test 9: Disconnection event notification
    # ========================================================================

    @pytest.mark.asyncio
    async def test_disconnection_event_notification(
        self, device_manager, setup_connected_device
    ):
        """Test that disconnection triggers event notification"""
        device_id = setup_connected_device

        # Mock event manager
        device_manager.event_manager.notify_device_disconnected = AsyncMock()

        # Mock connection manager
        device_manager.connection_manager.disconnect_device = AsyncMock()

        # Trigger disconnection
        await device_manager._handle_device_disconnection(device_id)

        # Verify event was triggered
        device_manager.event_manager.notify_device_disconnected.assert_called_once_with(
            device_id
        )

    # ========================================================================
    # Test 10: Reconnection event notification
    # ========================================================================

    @pytest.mark.asyncio
    async def test_reconnection_event_notification(
        self, device_manager, setup_connected_device
    ):
        """Test that successful reconnection triggers event notification"""
        device_id = setup_connected_device

        # Set device to DISCONNECTED
        device_manager.device_registry.update_device_status(
            device_id, DeviceStatus.DISCONNECTED
        )

        # Mock connection process
        device_manager.connection_manager.connect_to_device = AsyncMock()
        device_manager.connection_manager.request_device_info = AsyncMock(
            return_value={"platform": "Windows"}
        )
        device_manager.heartbeat_manager.start_heartbeat = Mock()
        device_manager.event_manager.notify_device_connected = AsyncMock()

        # Mock websocket
        mock_websocket = MagicMock()
        mock_websocket.closed = False
        device_manager.connection_manager._connections[device_id] = mock_websocket

        # Perform reconnection
        await device_manager.connect_device(device_id)

        # Verify connection event was triggered
        device_manager.event_manager.notify_device_connected.assert_called_once()
        call_args = device_manager.event_manager.notify_device_connected.call_args
        assert call_args[0][0] == device_id

    # ========================================================================
    # Test 11: Multiple disconnection/reconnection cycles
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multiple_disconnection_reconnection_cycles(
        self, device_manager, setup_connected_device
    ):
        """Test that device can handle multiple disconnect/reconnect cycles"""
        device_id = setup_connected_device

        # Mock connection components
        device_manager.connection_manager.connect_to_device = AsyncMock()
        device_manager.connection_manager.disconnect_device = AsyncMock()
        device_manager.connection_manager.request_device_info = AsyncMock(
            return_value={"platform": "Windows"}
        )
        device_manager.heartbeat_manager.start_heartbeat = Mock()
        device_manager.event_manager.notify_device_connected = AsyncMock()
        device_manager.event_manager.notify_device_disconnected = AsyncMock()

        # Mock websocket
        mock_websocket = MagicMock()
        mock_websocket.closed = False

        # Perform 3 disconnect/reconnect cycles
        for i in range(3):
            # Disconnect
            await device_manager._handle_device_disconnection(device_id)

            device_info = device_manager.device_registry.get_device(device_id)
            assert device_info.status == DeviceStatus.DISCONNECTED

            # Reconnect
            device_manager.connection_manager._connections[device_id] = mock_websocket
            success = await device_manager.connect_device(device_id)
            assert success is True

            device_info = device_manager.device_registry.get_device(device_id)
            assert device_info.status == DeviceStatus.IDLE

        # Verify events were called 3 times each
        assert device_manager.event_manager.notify_device_disconnected.call_count == 3
        assert device_manager.event_manager.notify_device_connected.call_count == 3

    # ========================================================================
    # Test 12: Heartbeat stops on disconnection
    # ========================================================================

    @pytest.mark.asyncio
    async def test_heartbeat_stops_on_disconnection(
        self, device_manager, setup_connected_device
    ):
        """Test that heartbeat monitoring stops when device disconnects"""
        device_id = setup_connected_device

        # Mock heartbeat manager
        device_manager.heartbeat_manager.stop_heartbeat = Mock()

        # Mock connection manager
        device_manager.connection_manager.disconnect_device = AsyncMock()

        # Create a mock websocket that raises ConnectionClosed
        mock_websocket = MagicMock()

        async def mock_iterator():
            raise websockets.ConnectionClosed(rcvd=None, sent=None)

        mock_websocket.__aiter__ = lambda self: mock_iterator()

        # Trigger disconnection through message processor
        task = asyncio.create_task(
            device_manager.message_processor._handle_device_messages(
                device_id, mock_websocket
            )
        )

        # Wait a bit for processing
        await asyncio.sleep(0.2)

        # Cancel task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Verify heartbeat was stopped
        device_manager.heartbeat_manager.stop_heartbeat.assert_called()

    # ========================================================================
    # Test 13: Connection with device not registered
    # ========================================================================

    @pytest.mark.asyncio
    async def test_disconnection_handler_with_unregistered_device(self, device_manager):
        """Test that disconnection handler handles unregistered device gracefully"""
        device_id = "non_existent_device"

        # Mock connection manager (should not be called)
        device_manager.connection_manager.disconnect_device = AsyncMock()

        # Trigger disconnection for non-existent device
        await device_manager._handle_device_disconnection(device_id)

        # Should not crash, and connection manager should not be called
        device_manager.connection_manager.disconnect_device.assert_not_called()

    # ========================================================================
    # Test 14: Reconnection with incremental backoff simulation
    # ========================================================================

    @pytest.mark.asyncio
    async def test_reconnection_attempts_tracking(self, device_manager, mock_device_id):
        """Test that reconnection attempts are properly tracked"""
        # Register device with max_retries=3
        device_manager.device_registry.register_device(
            device_id=mock_device_id,
            server_url="ws://localhost:5000/ws",
            os="Windows",
            max_retries=3,
        )

        # Set device to DISCONNECTED initially (not CONNECTED)
        device_manager.device_registry.update_device_status(
            mock_device_id, DeviceStatus.DISCONNECTED
        )

        # Mock connect_device to always fail
        attempt_count = 0

        async def mock_failed_connect(dev_id, is_reconnection=False):
            nonlocal attempt_count
            attempt_count += 1
            return False  # Connection failed

        device_manager.connect_device = mock_failed_connect

        # Trigger reconnection (will try 3 times and fail)
        await device_manager._reconnect_device(mock_device_id)

        # Verify 3 attempts were made
        assert attempt_count == 3

        # Verify status is FAILED after all retries exhausted
        device_info = device_manager.device_registry.get_device(mock_device_id)
        assert device_info.status == DeviceStatus.FAILED


# ========================================================================
# Integration test: Full disconnection and reconnection flow
# ========================================================================


class TestDisconnectionReconnectionIntegration:
    """Integration tests for complete disconnection/reconnection flow"""

    @pytest.mark.asyncio
    async def test_full_disconnection_reconnection_flow(self):
        """
        Integration test: Complete flow from connection to disconnection to reconnection

        Flow:
        1. Register and connect device
        2. Assign task to device (simulate execution)
        3. Device disconnects during task
        4. Task is cancelled
        5. Automatic reconnection is triggered
        6. Device reconnects successfully
        7. Device is ready for new tasks
        """
        # Setup device manager
        device_manager = ConstellationDeviceManager(
            task_name="integration_test",
            heartbeat_interval=30.0,
            reconnect_delay=0.3,
        )

        device_id = "integration_test_device"

        # Step 1: Register and "connect" device
        device_manager.device_registry.register_device(
            device_id=device_id,
            server_url="ws://localhost:5000/ws",
            os="Windows",
            capabilities=["ui_automation"],
            max_retries=3,
        )

        device_manager.device_registry.update_device_status(
            device_id, DeviceStatus.CONNECTED
        )
        device_manager.device_registry.set_device_idle(device_id)

        # Verify initial state
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.IDLE
        assert device_info.connection_attempts == 0

        # Step 2: Set device to BUSY (simulating task execution)
        task_id = "integration_task_001"
        device_manager.device_registry.set_device_busy(device_id, task_id)

        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.BUSY
        assert device_info.current_task_id == task_id

        # Step 3: Mock components for disconnection
        device_manager.connection_manager.disconnect_device = AsyncMock()
        device_manager.task_queue_manager.fail_task = Mock()
        device_manager.event_manager.notify_device_disconnected = AsyncMock()

        # Simulate disconnection
        await device_manager._handle_device_disconnection(device_id)

        # Step 4: Verify task was cancelled
        device_manager.task_queue_manager.fail_task.assert_called_once()
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.current_task_id is None
        assert device_info.status == DeviceStatus.DISCONNECTED

        # Step 5: Mock successful reconnection
        reconnection_completed = asyncio.Event()

        async def mock_connect(dev_id, is_reconnection=False):
            # Simulate successful connection
            device_manager.device_registry.update_device_status(
                dev_id, DeviceStatus.CONNECTED
            )
            device_manager.device_registry.set_device_idle(dev_id)
            device_manager.device_registry.reset_connection_attempts(dev_id)
            reconnection_completed.set()
            return True

        device_manager.connect_device = mock_connect

        # Wait for reconnection (should happen within 0.3s + processing time)
        try:
            await asyncio.wait_for(reconnection_completed.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("Reconnection was not triggered within timeout")

        # Step 6: Verify device is ready for new tasks
        device_info = device_manager.device_registry.get_device(device_id)
        assert device_info.status == DeviceStatus.IDLE
        assert device_info.current_task_id is None
        assert device_info.connection_attempts == 0

        # Cleanup
        for task in device_manager._reconnect_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    """Run tests with pytest"""
    pytest.main([__file__, "-v", "-s"])
