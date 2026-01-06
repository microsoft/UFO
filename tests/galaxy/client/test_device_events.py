# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test device event publishing in ConstellationDeviceManager
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from galaxy.client.device_manager import ConstellationDeviceManager
from galaxy.client.components import DeviceStatus
from galaxy.core.events import EventType, DeviceEvent, IEventObserver


class TestDeviceEventObserver(IEventObserver):
    """Test observer to capture device events"""

    def __init__(self):
        self.events = []

    async def on_event(self, event):
        """Capture events"""
        self.events.append(event)


@pytest.mark.asyncio
async def test_device_connected_event():
    """Test that DEVICE_CONNECTED event is published when device connects"""
    manager = ConstellationDeviceManager(task_name="test_task")
    observer = TestDeviceEventObserver()

    # Subscribe to device events
    manager.event_bus.subscribe(
        observer,
        event_types={
            EventType.DEVICE_CONNECTED,
            EventType.DEVICE_DISCONNECTED,
            EventType.DEVICE_STATUS_CHANGED,
        },
    )

    # Mock WebSocket connection
    with patch.object(
        manager.connection_manager, "connect_to_device", new_callable=AsyncMock
    ):
        with patch.object(
            manager.connection_manager, "request_device_info", return_value={}
        ):
            # Register and connect device
            await manager.register_device(
                device_id="test_device",
                server_url="ws://localhost:8000",
                os="Windows",
                capabilities=["ui_control"],
                metadata={"test": "data"},
            )

    # Wait for event propagation
    await asyncio.sleep(0.1)

    # Check that DEVICE_CONNECTED event was published
    assert len(observer.events) > 0
    connected_events = [
        e for e in observer.events if e.event_type == EventType.DEVICE_CONNECTED
    ]
    assert len(connected_events) == 1

    event = connected_events[0]
    assert isinstance(event, DeviceEvent)
    assert event.device_id == "test_device"
    assert event.device_status == DeviceStatus.IDLE.value
    assert "all_devices" in event.__dict__
    assert "test_device" in event.all_devices


@pytest.mark.asyncio
async def test_device_disconnected_event():
    """Test that DEVICE_DISCONNECTED event is published when device disconnects"""
    manager = ConstellationDeviceManager(task_name="test_task")
    observer = TestDeviceEventObserver()

    # Subscribe to device events
    manager.event_bus.subscribe(observer, event_types={EventType.DEVICE_DISCONNECTED})

    # Mock WebSocket connection
    with patch.object(
        manager.connection_manager, "connect_to_device", new_callable=AsyncMock
    ):
        with patch.object(
            manager.connection_manager, "request_device_info", return_value={}
        ):
            with patch.object(
                manager.connection_manager, "disconnect_device", new_callable=AsyncMock
            ):
                # Register and connect device
                await manager.register_device(
                    device_id="test_device",
                    server_url="ws://localhost:8000",
                    os="Windows",
                )

                # Disconnect device
                await manager.disconnect_device("test_device")

    # Wait for event propagation
    await asyncio.sleep(0.1)

    # Check that DEVICE_DISCONNECTED event was published
    disconnected_events = [
        e for e in observer.events if e.event_type == EventType.DEVICE_DISCONNECTED
    ]
    assert len(disconnected_events) == 1

    event = disconnected_events[0]
    assert isinstance(event, DeviceEvent)
    assert event.device_id == "test_device"
    assert event.device_status == DeviceStatus.DISCONNECTED.value


@pytest.mark.asyncio
async def test_device_status_changed_event():
    """Test that DEVICE_STATUS_CHANGED event is published when device status changes"""
    manager = ConstellationDeviceManager(task_name="test_task")
    observer = TestDeviceEventObserver()

    # Subscribe to device events
    manager.event_bus.subscribe(observer, event_types={EventType.DEVICE_STATUS_CHANGED})

    # Mock WebSocket connection and task execution
    with patch.object(
        manager.connection_manager, "connect_to_device", new_callable=AsyncMock
    ):
        with patch.object(
            manager.connection_manager, "request_device_info", return_value={}
        ):
            with patch.object(
                manager.connection_manager,
                "send_task_to_device",
                new_callable=AsyncMock,
            ) as mock_send_task:
                from galaxy.core.types import ExecutionResult
                from aip.messages import TaskStatus

                # Mock successful task execution
                mock_send_task.return_value = ExecutionResult(
                    task_id="test_task_1",
                    status=TaskStatus.COMPLETED,
                    result={"success": True},
                )

                # Register and connect device
                await manager.register_device(
                    device_id="test_device",
                    server_url="ws://localhost:8000",
                    os="Windows",
                )

                # Execute task (should trigger BUSY -> IDLE status changes)
                await manager.assign_task_to_device(
                    task_id="test_task_1",
                    device_id="test_device",
                    task_description="Test task",
                    task_data={},
                )

    # Wait for event propagation
    await asyncio.sleep(0.1)

    # Check that DEVICE_STATUS_CHANGED events were published
    status_changed_events = [
        e for e in observer.events if e.event_type == EventType.DEVICE_STATUS_CHANGED
    ]
    assert len(status_changed_events) >= 2  # BUSY and IDLE

    # Check BUSY event
    busy_events = [
        e for e in status_changed_events if e.device_status == DeviceStatus.BUSY.value
    ]
    assert len(busy_events) >= 1

    # Check IDLE event
    idle_events = [
        e for e in status_changed_events if e.device_status == DeviceStatus.IDLE.value
    ]
    assert len(idle_events) >= 1


@pytest.mark.asyncio
async def test_device_registry_snapshot_in_events():
    """Test that device events contain snapshot of all devices"""
    manager = ConstellationDeviceManager(task_name="test_task")
    observer = TestDeviceEventObserver()

    # Subscribe to all device events
    manager.event_bus.subscribe(
        observer,
        event_types={
            EventType.DEVICE_CONNECTED,
            EventType.DEVICE_DISCONNECTED,
            EventType.DEVICE_STATUS_CHANGED,
        },
    )

    # Mock WebSocket connection
    with patch.object(
        manager.connection_manager, "connect_to_device", new_callable=AsyncMock
    ):
        with patch.object(
            manager.connection_manager, "request_device_info", return_value={}
        ):
            # Register multiple devices
            await manager.register_device(
                device_id="device1",
                server_url="ws://localhost:8001",
                os="Windows",
            )
            await manager.register_device(
                device_id="device2",
                server_url="ws://localhost:8002",
                os="macOS",
            )

    # Wait for event propagation
    await asyncio.sleep(0.1)

    # Check that we received events for both devices
    assert len(observer.events) >= 2

    # The first event should have 1 device (device1)
    first_event = observer.events[0]
    assert isinstance(first_event, DeviceEvent)
    assert "all_devices" in first_event.__dict__
    assert len(first_event.all_devices) == 1
    assert "device1" in first_event.all_devices

    # The second event should have 2 devices (device1 and device2)
    second_event = observer.events[1]
    assert isinstance(second_event, DeviceEvent)
    assert len(second_event.all_devices) == 2
    assert "device1" in second_event.all_devices
    assert "device2" in second_event.all_devices
