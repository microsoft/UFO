# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test server restart and automatic reconnection scenarios.

Simulates real-world scenarios:
1. Device connected → Server killed → Server restarted → Auto-reconnected
2. Multiple retry attempts until success
3. Connection failure after max retries
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

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
        reconnect_delay=1.0,  # Shorter delay for testing (1 second instead of 5)
    )


@pytest.mark.asyncio
async def test_server_restart_automatic_reconnection(device_manager):
    """
    Test scenario: Server is killed and restarted, device should auto-reconnect.

    Timeline:
    t=0: Device connected
    t=1: Server killed (disconnect detected)
    t=2: Reconnection attempt 1 fails (server still down)
    t=3: Reconnection attempt 2 fails (server still down)
    t=4: Server restarted
    t=5: Reconnection attempt 3 succeeds
    """
    device_id = "test_device_1"

    # Register device
    device_manager.device_registry.register_device(
        device_id=device_id,
        server_url="ws://localhost:8000",
        os="Windows",
        capabilities=["ui_automation"],
        max_retries=5,  # Allow 5 retry attempts
    )

    # Initial connection succeeds
    with patch.object(
        device_manager.connection_manager, "connect_to_device", new_callable=AsyncMock
    ) as mock_connect:
        mock_websocket = MagicMock()
        mock_connect.return_value = mock_websocket

        # Mock device info request
        with patch.object(
            device_manager.connection_manager,
            "request_device_info",
            new_callable=AsyncMock,
            return_value={"os": "Windows", "hostname": "test-pc"},
        ):
            success = await device_manager.connect_device(device_id)

    assert success is True
    assert (
        device_manager.device_registry.get_device(device_id).status == DeviceStatus.IDLE
    )

    # Simulate server killed - trigger disconnection
    connection_attempt_count = 0

    def mock_connect_with_retry(*args, **kwargs):
        """Mock connection that fails first 2 times, then succeeds on 3rd attempt"""
        nonlocal connection_attempt_count
        connection_attempt_count += 1

        if connection_attempt_count <= 2:
            # Server still down - first 2 reconnection attempts fail
            raise ConnectionError(
                f"Connection refused (attempt {connection_attempt_count})"
            )
        else:
            # Server restarted - 3rd attempt succeeds
            return MagicMock()

    with patch.object(
        device_manager.connection_manager,
        "connect_to_device",
        side_effect=mock_connect_with_retry,
    ):
        with patch.object(
            device_manager.connection_manager,
            "request_device_info",
            new_callable=AsyncMock,
            return_value={"os": "Windows", "hostname": "test-pc"},
        ):
            # Trigger disconnection
            await device_manager._handle_device_disconnection(device_id)

            # Wait for reconnection loop to complete
            # It should retry 3 times with 1 second delay each = ~3 seconds
            await asyncio.sleep(4.0)

    # Verify device reconnected successfully
    device_info = device_manager.device_registry.get_device(device_id)
    assert device_info.status == DeviceStatus.IDLE
    assert connection_attempt_count == 3  # Failed 2 times, succeeded on 3rd
    assert device_info.connection_attempts == 0  # Reset after successful reconnection


@pytest.mark.asyncio
async def test_reconnection_with_multiple_retries(device_manager):
    """
    Test that reconnection retries multiple times before giving up.
    """
    device_id = "test_device_2"

    # Register device with max_retries=3
    device_manager.device_registry.register_device(
        device_id=device_id,
        server_url="ws://localhost:8000",
        os="Windows",
        capabilities=["ui_automation"],
        max_retries=3,
    )

    # Set device to DISCONNECTED (simulating previous connection)
    device_manager.device_registry.update_device_status(
        device_id, DeviceStatus.DISCONNECTED
    )

    # Track connection attempts
    connection_attempts = []

    async def mock_failed_connect(dev_id, is_reconnection=False):
        """Mock connect_device that always fails"""
        connection_attempts.append(asyncio.get_event_loop().time())
        return False  # Connection failed

    with patch.object(
        device_manager, "connect_device", side_effect=mock_failed_connect
    ):
        # Start reconnection
        await device_manager._reconnect_device(device_id)

    # Verify it tried exactly 3 times
    assert len(connection_attempts) == 3

    # Verify delays between attempts (should be ~1 second each)
    if len(connection_attempts) > 1:
        delay1 = connection_attempts[1] - connection_attempts[0]
        delay2 = connection_attempts[2] - connection_attempts[1]
        assert 0.9 < delay1 < 1.2  # Allow some timing variance
        assert 0.9 < delay2 < 1.2

    # Verify device status is FAILED after all retries exhausted
    device_info = device_manager.device_registry.get_device(device_id)
    assert device_info.status == DeviceStatus.FAILED


@pytest.mark.asyncio
async def test_reconnection_succeeds_on_first_attempt(device_manager):
    """
    Test that reconnection succeeds immediately if server is back online.
    """
    device_id = "test_device_3"

    # Register device
    device_manager.device_registry.register_device(
        device_id=device_id,
        server_url="ws://localhost:8000",
        os="Windows",
        capabilities=["ui_automation"],
        max_retries=5,
    )

    # Set device to DISCONNECTED
    device_manager.device_registry.update_device_status(
        device_id, DeviceStatus.DISCONNECTED
    )

    # Mock connection to succeed immediately
    connection_attempt_count = 0

    async def mock_successful_connect(*args, **kwargs):
        nonlocal connection_attempt_count
        connection_attempt_count += 1
        return MagicMock()

    with patch.object(
        device_manager.connection_manager,
        "connect_to_device",
        side_effect=mock_successful_connect,
    ):
        with patch.object(
            device_manager.connection_manager,
            "request_device_info",
            new_callable=AsyncMock,
            return_value={"os": "Windows"},
        ):
            # Start reconnection
            start_time = asyncio.get_event_loop().time()
            await device_manager._reconnect_device(device_id)
            elapsed_time = asyncio.get_event_loop().time() - start_time

    # Verify reconnection succeeded on first attempt
    assert connection_attempt_count == 1
    assert (
        elapsed_time < 2.0
    )  # Should complete quickly (1 second delay + connection time)

    # Verify device status is IDLE
    device_info = device_manager.device_registry.get_device(device_id)
    assert device_info.status == DeviceStatus.IDLE
    assert device_info.connection_attempts == 0  # Reset after success


@pytest.mark.asyncio
async def test_is_reconnection_flag_prevents_attempt_increment(device_manager):
    """
    Test that connect_device(is_reconnection=True) doesn't increment connection_attempts.
    """
    device_id = "test_device_4"

    # Register device
    device_manager.device_registry.register_device(
        device_id=device_id,
        server_url="ws://localhost:8000",
        os="Windows",
        capabilities=["ui_automation"],
    )

    initial_attempts = device_manager.device_registry.get_device(
        device_id
    ).connection_attempts

    # Mock successful connection
    with patch.object(
        device_manager.connection_manager,
        "connect_to_device",
        new_callable=AsyncMock,
        return_value=MagicMock(),
    ):
        with patch.object(
            device_manager.connection_manager,
            "request_device_info",
            new_callable=AsyncMock,
            return_value={},
        ):
            # Call with is_reconnection=True
            await device_manager.connect_device(device_id, is_reconnection=True)

    # Verify connection_attempts was NOT incremented
    final_attempts = device_manager.device_registry.get_device(
        device_id
    ).connection_attempts
    assert final_attempts == initial_attempts


@pytest.mark.asyncio
async def test_normal_connection_increments_attempts(device_manager):
    """
    Test that normal connect_device() (not reconnection) increments connection_attempts.
    """
    device_id = "test_device_5"

    # Register device
    device_manager.device_registry.register_device(
        device_id=device_id,
        server_url="ws://localhost:8000",
        os="Windows",
        capabilities=["ui_automation"],
    )

    initial_attempts = device_manager.device_registry.get_device(
        device_id
    ).connection_attempts
    assert initial_attempts == 0

    # Mock successful connection
    with patch.object(
        device_manager.connection_manager,
        "connect_to_device",
        new_callable=AsyncMock,
        return_value=MagicMock(),
    ):
        with patch.object(
            device_manager.connection_manager,
            "request_device_info",
            new_callable=AsyncMock,
            return_value={},
        ):
            # Call with is_reconnection=False (default)
            await device_manager.connect_device(device_id, is_reconnection=False)

    # Verify connection_attempts WAS incremented
    final_attempts = device_manager.device_registry.get_device(
        device_id
    ).connection_attempts
    assert final_attempts == initial_attempts + 1


@pytest.mark.asyncio
async def test_full_server_restart_scenario_integration(device_manager):
    """
    Integration test: Full server restart scenario.

    1. Device initially connected
    2. Server killed → disconnect detected
    3. Reconnection attempts fail (server down)
    4. Server comes back online
    5. Reconnection succeeds
    6. Device back to IDLE and ready for tasks
    """
    device_id = "linux_agent_1"

    # Step 1: Register and connect device
    device_manager.device_registry.register_device(
        device_id=device_id,
        server_url="ws://localhost:8765",
        os="Linux",
        capabilities=["ui_automation"],
        max_retries=5,
    )

    # Initial connection succeeds
    with patch.object(
        device_manager.connection_manager,
        "connect_to_device",
        new_callable=AsyncMock,
        return_value=MagicMock(),
    ):
        with patch.object(
            device_manager.connection_manager,
            "request_device_info",
            new_callable=AsyncMock,
            return_value={"os": "Linux", "hostname": "linux-server"},
        ):
            success = await device_manager.connect_device(device_id)

    assert success is True
    assert (
        device_manager.device_registry.get_device(device_id).status == DeviceStatus.IDLE
    )
    print(f"✅ Step 1: Device {device_id} initially connected")

    # Step 2: Simulate server killed
    server_online = False
    connection_attempt_count = 0

    async def mock_connect_with_server_state(*args, **kwargs):
        """Mock connection that respects server_online flag"""
        nonlocal connection_attempt_count
        connection_attempt_count += 1

        if not server_online:
            raise ConnectionError(
                f"[WinError 1225] The remote computer refused the network connection"
            )
        else:
            return MagicMock()

    with patch.object(
        device_manager.connection_manager,
        "connect_to_device",
        side_effect=mock_connect_with_server_state,
    ):
        with patch.object(
            device_manager.connection_manager,
            "request_device_info",
            new_callable=AsyncMock,
            return_value={"os": "Linux", "hostname": "linux-server"},
        ):
            # Trigger disconnection
            print(f"🔌 Step 2: Simulating server killed")
            disconnect_task = asyncio.create_task(
                device_manager._handle_device_disconnection(device_id)
            )

            # Wait for disconnection to be handled
            await asyncio.sleep(0.1)

            # Verify device is DISCONNECTED
            assert (
                device_manager.device_registry.get_device(device_id).status
                == DeviceStatus.DISCONNECTED
            )
            print(f"✅ Step 3: Device status → DISCONNECTED")

            # Step 3: Wait for first 2 reconnection attempts to fail
            await asyncio.sleep(2.5)  # 2 attempts × 1 second delay
            print(f"⚠️ Step 4: Reconnection attempts 1-2 failed (server still down)")
            print(f"   Attempts made so far: {connection_attempt_count}")

            # Step 4: Bring server back online
            server_online = True
            print(f"🔄 Step 5: Server restarted (online)")

            # Step 5: Wait for reconnection to succeed
            await asyncio.sleep(2.0)  # Wait for next retry

            await disconnect_task

    # Step 6: Verify device reconnected successfully
    device_info = device_manager.device_registry.get_device(device_id)
    assert device_info.status == DeviceStatus.IDLE
    assert device_info.connection_attempts == 0  # Reset after success
    print(f"✅ Step 6: Device {device_id} auto-reconnected successfully!")
    print(f"   Final status: {device_info.status.value}")
    print(f"   Total connection attempts made: {connection_attempt_count}")
    print(f"   Connection attempts counter (reset): {device_info.connection_attempts}")


@pytest.mark.asyncio
async def test_reconnection_stops_after_max_retries(device_manager):
    """
    Test that reconnection stops after max_retries and sets status to FAILED.
    """
    device_id = "test_device_6"
    max_retries = 3

    # Register device with limited retries
    device_manager.device_registry.register_device(
        device_id=device_id,
        server_url="ws://localhost:8000",
        os="Windows",
        capabilities=["ui_automation"],
        max_retries=max_retries,
    )

    # Set device to DISCONNECTED
    device_manager.device_registry.update_device_status(
        device_id, DeviceStatus.DISCONNECTED
    )

    # Mock connection to always fail
    connection_attempt_count = 0

    async def mock_always_fail(dev_id, is_reconnection=False):
        nonlocal connection_attempt_count
        connection_attempt_count += 1
        return False  # Connection failed

    with patch.object(device_manager, "connect_device", side_effect=mock_always_fail):
        # Start reconnection
        await device_manager._reconnect_device(device_id)

    # Verify exactly max_retries attempts were made
    assert connection_attempt_count == max_retries

    # Verify device status is FAILED
    device_info = device_manager.device_registry.get_device(device_id)
    assert device_info.status == DeviceStatus.FAILED

    print(f"✅ Test passed: Stopped after {connection_attempt_count} attempts")
    print(f"   Device status: {device_info.status.value}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
