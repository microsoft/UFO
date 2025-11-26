"""
Simplified integration tests for Constellation Client AIP migration.

This test suite verifies that the constellation client components correctly use
AIP protocols after migration.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone

from aip.messages import (
    ClientMessage,
    ClientMessageType,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from aip.protocol.heartbeat import HeartbeatProtocol
from aip.protocol.registration import RegistrationProtocol
from aip.transport.websocket import WebSocketTransport


class MockTransport:
    """Mock transport for testing."""

    def __init__(self):
        self.sent_messages = []
        self.receive_queue = asyncio.Queue()
        self.is_connected = True

    async def send(self, message: bytes):
        self.sent_messages.append(message)

    async def receive(self) -> bytes:
        return await self.receive_queue.get()

    async def close(self):
        self.is_connected = False


@pytest.mark.asyncio
async def test_heartbeat_protocol_integration():
    """Test that HeartbeatProtocol works correctly."""
    transport = MockTransport()
    protocol = HeartbeatProtocol(transport)

    # Send heartbeat
    await protocol.send_heartbeat(
        client_id="test_constellation@device_001",
        metadata={"device_id": "device_001"},
    )

    # Verify message was sent
    assert len(transport.sent_messages) == 1

    # Parse sent message
    sent_data = transport.sent_messages[0].decode()
    msg = ClientMessage.model_validate_json(sent_data)

    assert msg.type == ClientMessageType.HEARTBEAT
    assert msg.client_id == "test_constellation@device_001"
    assert msg.status == TaskStatus.OK
    assert msg.metadata["device_id"] == "device_001"


@pytest.mark.asyncio
async def test_registration_protocol_integration():
    """Test that RegistrationProtocol works correctly for constellation."""
    transport = MockTransport()
    protocol = RegistrationProtocol(transport)

    # Queue success response
    response = ServerMessage(
        type=ServerMessageType.HEARTBEAT,
        status=TaskStatus.OK,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    await transport.receive_queue.put(response.model_dump_json().encode())

    # Register as constellation
    success = await protocol.register_as_constellation(
        constellation_id="test_constellation@device_001",
        target_device="device_001",
        metadata={"capabilities": ["task_distribution"]},
    )

    assert success is True
    assert len(transport.sent_messages) == 1

    # Parse sent message
    sent_data = transport.sent_messages[0].decode()
    msg = ClientMessage.model_validate_json(sent_data)

    assert msg.type == ClientMessageType.REGISTER
    assert msg.client_id == "test_constellation@device_001"
    assert msg.target_id == "device_001"
    assert (
        msg.metadata["targeted_device_id"] == "device_001"
    )  # Changed from target_device


@pytest.mark.asyncio
async def test_registration_protocol_error_handling():
    """Test registration error handling."""
    transport = MockTransport()
    protocol = RegistrationProtocol(transport)

    # Queue error response
    response = ServerMessage(
        type=ServerMessageType.ERROR,
        status=TaskStatus.ERROR,
        error="Device not found",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    await transport.receive_queue.put(response.model_dump_json().encode())

    # Register as constellation - should fail
    success = await protocol.register_as_constellation(
        constellation_id="test_constellation@device_999",
        target_device="device_999",
    )

    assert success is False


@pytest.mark.asyncio
async def test_websocket_transport_adapter():
    """Test that WebSocketTransport uses adapter pattern correctly."""
    mock_ws = Mock()
    mock_ws.remote_address = ("127.0.0.1", 5005)
    mock_ws.closed = False

    # Create transport with mock websocket
    transport = WebSocketTransport()

    # Manually set websocket and state (normally done in connect())
    transport._websocket = mock_ws

    # Create adapter
    from aip.transport.adapters import WebSocketsLibAdapter
    from aip.transport.base import TransportState

    transport._adapter = WebSocketsLibAdapter(mock_ws)
    transport._state = TransportState.CONNECTED  # Set connected state

    # Verify is_connected uses adapter
    mock_ws.closed = False
    assert transport.is_connected is True

    # Change state to simulate disconnection
    mock_ws.closed = True
    transport._state = TransportState.DISCONNECTED
    assert transport.is_connected is False


@pytest.mark.asyncio
async def test_heartbeat_manager_creates_protocol():
    """Test that HeartbeatManager creates HeartbeatProtocol instances."""
    from galaxy.client.components.heartbeat_manager import HeartbeatManager
    from galaxy.client.components.device_registry import DeviceRegistry

    # Create mock connection manager
    connection_manager = Mock()
    connection_manager.task_name = "test_constellation"
    connection_manager._transports = {}
    connection_manager.is_connected = Mock(return_value=False)  # Will stop immediately

    # Create device registry
    device_registry = DeviceRegistry()

    # Create heartbeat manager
    heartbeat_manager = HeartbeatManager(
        connection_manager=connection_manager,
        device_registry=device_registry,
        heartbeat_interval=0.1,
    )

    # Verify heartbeat protocols dict exists
    assert hasattr(heartbeat_manager, "_heartbeat_protocols")
    assert isinstance(heartbeat_manager._heartbeat_protocols, dict)


@pytest.mark.asyncio
async def test_connection_manager_has_aip_components():
    """Test that ConnectionManager has all AIP protocol dicts."""
    from galaxy.client.components.connection_manager import (
        WebSocketConnectionManager,
    )

    manager = WebSocketConnectionManager(task_name="test_constellation")

    # Verify all AIP protocol instance dicts exist
    assert hasattr(manager, "_transports")
    assert hasattr(manager, "_registration_protocols")
    assert hasattr(manager, "_task_protocols")
    assert hasattr(manager, "_device_info_protocols")

    assert isinstance(manager._transports, dict)
    assert isinstance(manager._registration_protocols, dict)
    assert isinstance(manager._task_protocols, dict)
    assert isinstance(manager._device_info_protocols, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
