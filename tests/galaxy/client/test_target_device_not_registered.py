# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Tests for handling scenario where target device is not registered on the server.

This test suite verifies the fix for the issue where constellation client
would incorrectly report success when the target device is not connected to
the UFO server.

Scenario:
1. Constellation client attempts to register with server
2. Server validates that the target_device_id exists
3. If target device is not connected, server rejects registration
4. Client should detect this failure and report connection failure

Before fix:
- _register_constellation_client() always returned True
- connect_device() would incorrectly report success
- Connection would immediately close, triggering reconnection
- Infinite reconnection loop until max_retries

After fix:
- _register_constellation_client() waits for server response
- Returns False if server rejects registration
- connect_device() correctly reports failure
- Reconnection logic can make informed decisions
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import websockets

from galaxy.client.device_manager import ConstellationDeviceManager
from galaxy.client.components import DeviceStatus, AgentProfile
from aip.messages import ServerMessage, ServerMessageType, TaskStatus


class TestTargetDeviceNotRegistered:
    """Test suite for target device not registered scenario"""

    @pytest.fixture
    def device_manager(self):
        """Create a device manager instance"""
        manager = ConstellationDeviceManager(
            task_name="test_task",
            heartbeat_interval=30.0,
            reconnect_delay=0.5,
        )
        return manager

    @pytest.fixture
    def target_device_id(self):
        """Target device ID that is not connected to the server"""
        return "unregistered_device"

    @pytest.fixture
    def server_url(self):
        """Server URL for testing"""
        return "ws://localhost:5000/ws"

    # ========================================================================
    # Test 1: Server rejects registration when target device not connected
    # ========================================================================

    @pytest.mark.asyncio
    async def test_registration_fails_when_target_device_not_connected(
        self, device_manager, target_device_id, server_url
    ):
        """
        Test that registration fails when target device is not connected.

        This is the core fix verification test.
        """
        # Setup: Register device in client (but it's not connected to server)
        await device_manager.register_device(
            device_id=target_device_id,
            server_url=server_url,
            os="Windows",
            capabilities=["ui_automation"],
            metadata={"test": True},
            auto_connect=False,  # Don't auto-connect yet
        )

        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.closed = False

        # Mock server response: ERROR because target device not connected
        error_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.ERROR,
            error=f"Target device '{target_device_id}' is not connected to the server",
            timestamp="2025-10-27T12:00:00Z",
            response_id="test_response",
        )

        # Setup mock to return error response
        mock_websocket.recv = AsyncMock(return_value=error_response.model_dump_json())
        mock_websocket.send = AsyncMock()
        mock_websocket.close = AsyncMock()

        # Mock websockets.connect as an async function
        async def mock_connect(*args, **kwargs):
            return mock_websocket

        # Patch websockets.connect to return our mock
        with patch("websockets.connect", side_effect=mock_connect):
            # Attempt to connect
            success = await device_manager.connect_device(target_device_id)

            # ✅ Verification: connect_device should return False
            assert (
                success is False
            ), "Connection should fail when target device not registered"

            # Verify device status is FAILED (not CONNECTED)
            device_info = device_manager.device_registry.get_device(target_device_id)
            assert (
                device_info.status == DeviceStatus.FAILED
            ), f"Device status should be FAILED, got {device_info.status}"

    # ========================================================================
    # Test 2: Reconnection continues after target device registration failure
    # ========================================================================

    @pytest.mark.asyncio
    async def test_reconnection_after_target_device_becomes_available(
        self, device_manager, target_device_id, server_url
    ):
        """
        Test that reconnection succeeds once target device becomes available.

        Scenario:
        1. First attempt: Target device not connected → Registration fails
        2. Target device connects to server
        3. Second attempt: Registration succeeds
        """
        # Setup: Register device
        await device_manager.register_device(
            device_id=target_device_id,
            server_url=server_url,
            os="Windows",
            auto_connect=False,
        )

        # Mock WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        mock_websocket.send = AsyncMock()
        mock_websocket.close = AsyncMock()

        # First attempt: Error response (device not connected)
        error_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.ERROR,
            error=f"Target device '{target_device_id}' is not connected",
            timestamp="2025-10-27T12:00:00Z",
            response_id="error_response",
        )

        # Second attempt: Success response (device now connected)
        success_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp="2025-10-27T12:00:01Z",
            response_id="success_response",
        )

        # Create two separate mock websockets for each connection attempt
        mock_websocket1 = AsyncMock()
        mock_websocket1.closed = False
        mock_websocket1.send = AsyncMock()
        mock_websocket1.close = AsyncMock()
        mock_websocket1.recv = AsyncMock(return_value=error_response.model_dump_json())

        mock_websocket2 = AsyncMock()
        mock_websocket2.closed = False
        mock_websocket2.send = AsyncMock()
        mock_websocket2.close = AsyncMock()
        mock_websocket2.recv = AsyncMock(
            return_value=success_response.model_dump_json()
        )

        # Mock websockets.connect to return different websockets for each call
        call_count = [0]

        async def mock_connect(*args, **kwargs):
            result = [mock_websocket1, mock_websocket2][call_count[0]]
            call_count[0] += 1
            return result

        with patch("websockets.connect", side_effect=mock_connect):
            # Mock additional methods needed for successful connection
            device_manager.heartbeat_manager.start_heartbeat = Mock()
            device_manager.connection_manager.request_device_info = AsyncMock(
                return_value={"os": "Windows", "version": "11"}
            )

            # First attempt: Should fail
            success1 = await device_manager.connect_device(target_device_id)
            assert success1 is False, "First connection attempt should fail"

            device_info = device_manager.device_registry.get_device(target_device_id)
            assert device_info.status == DeviceStatus.FAILED

            # Reset status for retry
            device_manager.device_registry.update_device_status(
                target_device_id, DeviceStatus.DISCONNECTED
            )

            # Second attempt: Should succeed (target device now available)
            success2 = await device_manager.connect_device(target_device_id)
            assert success2 is True, "Second connection attempt should succeed"

            device_info = device_manager.device_registry.get_device(target_device_id)
            assert device_info.status == DeviceStatus.IDLE

    # ========================================================================
    # Test 3: Validate registration response timeout handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_registration_timeout_when_server_not_responding(
        self, device_manager, target_device_id, server_url
    ):
        """
        Test that registration times out if server doesn't respond.
        """
        # Setup
        await device_manager.register_device(
            device_id=target_device_id,
            server_url=server_url,
            os="Windows",
            auto_connect=False,
        )

        # Mock WebSocket that never responds
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        mock_websocket.send = AsyncMock()
        mock_websocket.close = AsyncMock()

        # recv() will timeout
        async def mock_recv_timeout():
            await asyncio.sleep(20)  # Longer than validation timeout (10s)
            raise asyncio.TimeoutError()

        mock_websocket.recv = mock_recv_timeout

        # Mock websockets.connect as an async function
        async def mock_connect(*args, **kwargs):
            return mock_websocket

        with patch("websockets.connect", side_effect=mock_connect):
            # Attempt to connect
            success = await device_manager.connect_device(target_device_id)

            # Should fail due to timeout
            assert success is False, "Connection should fail on timeout"

            device_info = device_manager.device_registry.get_device(target_device_id)
            assert device_info.status == DeviceStatus.FAILED

    # ========================================================================
    # Test 4: Error message contains helpful information
    # ========================================================================

    @pytest.mark.asyncio
    async def test_error_message_indicates_target_device_not_connected(
        self, device_manager, target_device_id, server_url, caplog
    ):
        """
        Test that error messages clearly indicate the target device is not connected.
        """
        import logging

        # Capture all log levels including ERROR
        caplog.set_level(logging.DEBUG)

        # Setup
        await device_manager.register_device(
            device_id=target_device_id,
            server_url=server_url,
            os="Windows",
            auto_connect=False,
        )

        # Mock WebSocket with error response
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        mock_websocket.send = AsyncMock()
        mock_websocket.close = AsyncMock()

        error_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.ERROR,
            error=f"Target device '{target_device_id}' is not connected to the server",
            timestamp="2025-10-27T12:00:00Z",
            response_id="error_response",
        )

        mock_websocket.recv = AsyncMock(return_value=error_response.model_dump_json())

        # Mock websockets.connect as an async function
        async def mock_connect(*args, **kwargs):
            return mock_websocket

        with patch("websockets.connect", side_effect=mock_connect):
            # Attempt to connect
            await device_manager.connect_device(target_device_id)

            # Check that logs contain helpful error message
            log_messages = [record.message for record in caplog.records]

            # Debug: print all log messages
            # print("\n".join(log_messages))

            # Should contain error/warning about target device not connected
            # Check both in error message and in rejection message
            assert any(
                "not connected" in msg.lower() or "rejected" in msg.lower()
                for msg in log_messages
            ), f"Log should indicate target device is not connected. Got: {log_messages}"  # ========================================================================

    # Test 5: Connection attempts counter is properly managed
    # ========================================================================

    @pytest.mark.asyncio
    async def test_connection_attempts_incremented_on_failure(
        self, device_manager, target_device_id, server_url
    ):
        """
        Test that connection_attempts counter is incremented on failed attempts.
        """
        # Setup
        await device_manager.register_device(
            device_id=target_device_id,
            server_url=server_url,
            os="Windows",
            auto_connect=False,
        )

        device_info = device_manager.device_registry.get_device(target_device_id)
        initial_attempts = device_info.connection_attempts
        assert initial_attempts == 0

        # Mock WebSocket with error response
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        mock_websocket.send = AsyncMock()
        mock_websocket.close = AsyncMock()

        error_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.ERROR,
            error="Target device not connected",
            timestamp="2025-10-27T12:00:00Z",
            response_id="error_response",
        )

        mock_websocket.recv = AsyncMock(return_value=error_response.model_dump_json())

        # Mock websockets.connect as an async function
        async def mock_connect(*args, **kwargs):
            return mock_websocket

        with patch("websockets.connect", side_effect=mock_connect):
            # Attempt to connect
            await device_manager.connect_device(target_device_id)

            # Verify connection_attempts was incremented
            device_info = device_manager.device_registry.get_device(target_device_id)
            assert (
                device_info.connection_attempts == initial_attempts + 1
            ), "connection_attempts should be incremented on failure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
