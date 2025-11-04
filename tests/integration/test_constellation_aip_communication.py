"""
Integration tests for Galaxy Constellation Client communication using AIP.

Tests the complete message flow between Constellation Client and UFO Server using
the refactored AIP protocol implementation.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from datetime import datetime, timezone

from aip.messages import (
    ClientMessage,
    ClientMessageType,
    ClientType,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from galaxy.client.components.connection_manager import WebSocketConnectionManager
from galaxy.client.components.heartbeat_manager import HeartbeatManager
from galaxy.client.components.message_processor import MessageProcessor
from galaxy.client.components.device_registry import DeviceRegistry
from galaxy.client.components.types import TaskRequest, AgentProfile


class MockWebSocket:
    """Mock WebSocket for testing (simulates websockets library)."""

    def __init__(self):
        self.sent_messages = []
        self.closed = False
        self.receive_queue = asyncio.Queue()
        self._remote_address = ("127.0.0.1", 5005)

    async def send(self, message: str):
        """Mock send method."""
        self.sent_messages.append(message)

    async def recv(self):
        """Mock receive method."""
        return await self.receive_queue.get()

    async def close(self):
        """Mock close method."""
        self.closed = True

    def add_message(self, message: str):
        """Add a message to the receive queue."""
        self.receive_queue.put_nowait(message)

    @property
    def remote_address(self):
        """Mock remote_address property."""
        return self._remote_address


@pytest.fixture
def device_registry():
    """Create a device registry for testing."""
    registry = DeviceRegistry()
    return registry


@pytest.fixture
def connection_manager():
    """Create a connection manager for testing."""
    manager = WebSocketConnectionManager(
        task_name="test_constellation",
    )
    return manager


@pytest.fixture
def message_processor(connection_manager):
    """Create a message processor for testing."""
    processor = MessageProcessor(connection_manager)
    return processor


@pytest.fixture
def heartbeat_manager(connection_manager, device_registry):
    """Create a heartbeat manager for testing."""
    manager = HeartbeatManager(
        connection_manager=connection_manager,
        device_registry=device_registry,
        heartbeat_interval=0.5,  # Short interval for testing
    )
    return manager


@pytest.mark.asyncio
async def test_connection_manager_uses_aip_transport(
    connection_manager, message_processor
):
    """Test that ConnectionManager initializes AIP Transport correctly."""
    device_id = "test_device"
    ws_url = "ws://localhost:5005/ws"

    # Create device profile
    device_info = AgentProfile(
        device_id=device_id,
        server_url=ws_url,
        os_type="Windows",
        os_version="11",
    )

    # Mock websockets.connect
    mock_ws = MockWebSocket()

    with patch("websockets.connect", return_value=mock_ws):
        # Add registration response to queue (server responds with HEARTBEAT status=OK)
        reg_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        mock_ws.add_message(reg_response.model_dump_json())

        # Connect to device
        await connection_manager.connect_to_device(device_info, message_processor)

        # Verify AIP transport was created
        assert device_id in connection_manager._transports
        assert connection_manager._transports[device_id] is not None

        # Verify registration protocol was used
        assert device_id in connection_manager._registration_protocols

        # Verify connection is active
        assert connection_manager.is_connected(device_id)

        # Cleanup
        await connection_manager.disconnect_device(device_id)


@pytest.mark.asyncio
async def test_registration_with_aip_protocol(connection_manager):
    """Test constellation registration using AIP RegistrationProtocol."""
    device_id = "test_device"
    ws_url = "ws://localhost:5005/ws"

    mock_ws = MockWebSocket()

    with patch("websockets.connect", return_value=mock_ws):
        # Prepare registration response
        reg_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        mock_ws.add_message(reg_response.model_dump_json())

        # Connect and register
        await connection_manager.connect_to_device(device_id, ws_url)

        # Verify registration message was sent
        assert len(mock_ws.sent_messages) > 0

        # Parse the registration message
        reg_msg = ClientMessage.model_validate_json(mock_ws.sent_messages[0])
        assert reg_msg.type == ClientMessageType.REGISTER
        assert reg_msg.client_type == ClientType.CONSTELLATION
        assert reg_msg.client_id == f"test_constellation@{device_id}"
        assert reg_msg.metadata["target_device"] == device_id

        # Verify registration future was resolved
        assert connection_manager.is_connected(device_id)

        # Cleanup
        await connection_manager.disconnect_device(device_id)


@pytest.mark.asyncio
async def test_send_task_to_device_with_aip(connection_manager):
    """Test sending task to device using AIP Transport."""
    device_id = "test_device"
    ws_url = "ws://localhost:5005/ws"

    mock_ws = MockWebSocket()

    with patch("websockets.connect", return_value=mock_ws):
        # Setup: Register first
        reg_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        mock_ws.add_message(reg_response.model_dump_json())

        await connection_manager.connect_to_device(device_id, ws_url)

        # Clear sent messages from registration
        mock_ws.sent_messages.clear()

        # Send task
        task_name = "excel_task"
        task_id = "task_123"
        task_request = TaskRequest(
            task_id=task_id,
            device_id=device_id,
            request="Open Excel and create a spreadsheet",
            task_name=task_name,
            timeout=1.0,
        )

        # Prepare task response
        task_response = ServerMessage(
            type=ServerMessageType.TASK_END,
            session_id=f"{task_name}@{task_id}",
            result={"status": "completed"},
            status=TaskStatus.COMPLETED,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        mock_ws.add_message(task_response.model_dump_json())

        # Send task
        result = await connection_manager.send_task_to_device(
            device_id=device_id,
            task_request=task_request,
        )

        # Verify task message was sent through AIP Transport
        assert len(mock_ws.sent_messages) > 0

        # Parse the task message
        task_msg = ClientMessage.model_validate_json(mock_ws.sent_messages[0])
        assert task_msg.type == ClientMessageType.TASK
        assert task_msg.session_id == f"{task_name}@{task_id}"
        assert task_msg.request == "Open Excel and create a spreadsheet"

        # Verify result
        assert result is not None
        assert result.status == TaskStatus.COMPLETED

        # Cleanup
        await connection_manager.disconnect_device(device_id)


@pytest.mark.asyncio
async def test_heartbeat_with_aip_protocol(connection_manager, heartbeat_manager):
    """Test heartbeat sending using AIP HeartbeatProtocol."""
    device_id = "test_device"
    ws_url = "ws://localhost:5005/ws"

    mock_ws = MockWebSocket()

    with patch("websockets.connect", return_value=mock_ws):
        # Setup: Register first
        reg_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        mock_ws.add_message(reg_response.model_dump_json())

        await connection_manager.connect_to_device(device_id, ws_url)

        # Clear sent messages
        mock_ws.sent_messages.clear()

        # Start heartbeat
        heartbeat_manager.start_heartbeat(device_id)

        # Wait for at least one heartbeat
        await asyncio.sleep(0.7)

        # Stop heartbeat
        heartbeat_manager.stop_heartbeat(device_id)

        # Verify heartbeat messages were sent
        assert len(mock_ws.sent_messages) >= 1

        # Parse first heartbeat message
        heartbeat_msg = ClientMessage.model_validate_json(mock_ws.sent_messages[0])
        assert heartbeat_msg.type == ClientMessageType.HEARTBEAT
        assert heartbeat_msg.client_id == f"test_constellation@{device_id}"
        assert heartbeat_msg.status == TaskStatus.OK
        assert heartbeat_msg.metadata["device_id"] == device_id

        # Verify heartbeat protocol was created
        assert device_id in heartbeat_manager._heartbeat_protocols

        # Cleanup
        await connection_manager.disconnect_device(device_id)


@pytest.mark.asyncio
async def test_request_device_info_with_aip(connection_manager):
    """Test requesting device info using AIP Transport."""
    device_id = "test_device"
    ws_url = "ws://localhost:5005/ws"

    mock_ws = MockWebSocket()

    with patch("websockets.connect", return_value=mock_ws):
        # Setup: Register first
        reg_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        mock_ws.add_message(reg_response.model_dump_json())

        await connection_manager.connect_to_device(device_id, ws_url)

        # Clear sent messages
        mock_ws.sent_messages.clear()

        # Prepare device info response
        device_info_response = ServerMessage(
            type=ServerMessageType.DEVICE_INFO_RESPONSE,
            device_info={
                "os": "Windows",
                "version": "11",
                "capabilities": ["ui_automation"],
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        mock_ws.add_message(device_info_response.model_dump_json())

        # Request device info
        info = await connection_manager.request_device_info(device_id, timeout=1.0)

        # Verify device info request was sent
        assert len(mock_ws.sent_messages) > 0

        # Parse the request message
        request_msg = ClientMessage.model_validate_json(mock_ws.sent_messages[0])
        assert request_msg.type == ClientMessageType.DEVICE_INFO_REQUEST

        # Verify response
        assert info is not None
        assert info.device_info["os"] == "Windows"

        # Cleanup
        await connection_manager.disconnect_device(device_id)


@pytest.mark.asyncio
async def test_message_processor_handles_aip_messages(
    connection_manager, message_processor
):
    """Test that MessageProcessor correctly processes AIP ServerMessages."""
    device_id = "test_device"
    ws_url = "ws://localhost:5005/ws"

    mock_ws = MockWebSocket()

    with patch("websockets.connect", return_value=mock_ws):
        # Setup connection
        reg_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        mock_ws.add_message(reg_response.model_dump_json())

        await connection_manager.connect_to_device(device_id, ws_url)

        # Create a task future
        task_id = "task_123"
        session_id = f"excel_task@{task_id}"
        future = asyncio.get_event_loop().create_future()
        connection_manager._pending_task_responses[session_id] = future

        # Process a task result message
        task_result_msg = ServerMessage(
            type=ServerMessageType.TASK_END,
            session_id=session_id,
            status=TaskStatus.COMPLETED,
            result={"status": "completed", "data": "result_data"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        await message_processor.process_message(device_id, task_result_msg)

        # Verify future was resolved
        assert future.done()
        result = future.result()
        assert result.result["status"] == "completed"

        # Cleanup
        await connection_manager.disconnect_device(device_id)


@pytest.mark.asyncio
async def test_disconnect_cleans_up_aip_protocols(connection_manager):
    """Test that disconnecting cleans up all AIP protocol instances."""
    device_id = "test_device"
    ws_url = "ws://localhost:5005/ws"

    mock_ws = MockWebSocket()

    with patch("websockets.connect", return_value=mock_ws):
        # Setup connection
        reg_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        mock_ws.add_message(reg_response.model_dump_json())

        await connection_manager.connect_to_device(device_id, ws_url)

        # Verify protocols were created
        assert device_id in connection_manager._transports
        assert device_id in connection_manager._registration_protocols

        # Disconnect
        await connection_manager.disconnect_device(device_id)

        # Verify all protocols were cleaned up
        assert device_id not in connection_manager._transports
        assert device_id not in connection_manager._registration_protocols
        assert device_id not in connection_manager._task_protocols
        assert device_id not in connection_manager._device_info_protocols

        # Verify WebSocket was closed
        assert mock_ws.closed


@pytest.mark.asyncio
async def test_error_handling_in_aip_communication(connection_manager):
    """Test error handling when AIP communication fails."""
    device_id = "test_device"
    ws_url = "ws://localhost:5005/ws"

    # Test connection failure
    with patch("websockets.connect", side_effect=ConnectionError("Network error")):
        with pytest.raises(ConnectionError):
            await connection_manager.connect_to_device(device_id, ws_url)

    # Test send failure after connection
    mock_ws = MockWebSocket()

    with patch("websockets.connect", return_value=mock_ws):
        # Setup connection
        reg_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        mock_ws.add_message(reg_response.model_dump_json())

        await connection_manager.connect_to_device(device_id, ws_url)

        # Mock transport send to fail
        transport = connection_manager._transports[device_id]
        original_send = transport.send

        async def failing_send(msg):
            raise IOError("Send failed")

        transport.send = failing_send

        # Try to send task - should raise error
        task_request = TaskRequest(
            task_id="task_123",
            device_id=device_id,
            request="test request",
            task_name="test_task",
            timeout=1.0,
        )
        with pytest.raises(IOError):
            await connection_manager.send_task_to_device(
                device_id=device_id,
                task_request=task_request,
            )

        # Cleanup
        transport.send = original_send
        await connection_manager.disconnect_device(device_id)


@pytest.mark.asyncio
async def test_concurrent_operations_with_aip(connection_manager):
    """Test concurrent operations on multiple devices using AIP."""
    devices = ["device_1", "device_2", "device_3"]
    ws_url = "ws://localhost:5005/ws"

    mock_websockets = {}

    async def mock_connect(url, **kwargs):
        # Extract device_id from URL or create a new mock for each connection
        device_id = (
            url.split("/")[-1] if "/" in url else f"device_{len(mock_websockets)}"
        )
        mock_ws = MockWebSocket()
        mock_websockets[device_id] = mock_ws
        return mock_ws

    with patch("websockets.connect", side_effect=mock_connect):
        # Connect to all devices concurrently
        connection_tasks = []
        for device_id in devices:
            # Prepare registration response
            mock_ws = MockWebSocket()
            mock_websockets[device_id] = mock_ws
            reg_response = ServerMessage(
                type=ServerMessageType.HEARTBEAT,
                client_id=f"test_constellation@{device_id}",
                session_id=f"session_{device_id}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            mock_ws.add_message(reg_response.model_dump_json())

        # Actually connect
        for device_id in devices:
            task = connection_manager.connect_to_device(
                device_id, f"{ws_url}/{device_id}"
            )
            connection_tasks.append(task)

        # Wait for all connections
        await asyncio.gather(*connection_tasks)

        # Verify all devices are connected
        for device_id in devices:
            assert connection_manager.is_connected(device_id)
            assert device_id in connection_manager._transports

        # Cleanup all
        for device_id in devices:
            await connection_manager.disconnect_device(device_id)

        # Verify all cleaned up
        for device_id in devices:
            assert not connection_manager.is_connected(device_id)


@pytest.mark.asyncio
async def test_heartbeat_cleanup_on_stop(heartbeat_manager, connection_manager):
    """Test that heartbeat manager properly cleans up protocol instances."""
    device_id = "test_device"
    ws_url = "ws://localhost:5005/ws"

    mock_ws = MockWebSocket()

    with patch("websockets.connect", return_value=mock_ws):
        # Setup connection
        reg_response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        mock_ws.add_message(reg_response.model_dump_json())

        await connection_manager.connect_to_device(device_id, ws_url)

        # Start heartbeat
        heartbeat_manager.start_heartbeat(device_id)
        await asyncio.sleep(0.3)

        # Verify protocol was created
        assert device_id in heartbeat_manager._heartbeat_protocols

        # Stop heartbeat
        heartbeat_manager.stop_heartbeat(device_id)

        # Verify protocol was cleaned up
        assert device_id not in heartbeat_manager._heartbeat_protocols

        # Cleanup
        await connection_manager.disconnect_device(device_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
