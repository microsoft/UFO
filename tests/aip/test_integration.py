# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Integration Tests for AIP

Tests end-to-end protocol flows and integration between components.
"""

import asyncio

import pytest

from aip import (
    AIPProtocol,
    ClientMessage,
    ClientMessageType,
    ClientType,
    RegistrationProtocol,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
    WebSocketTransport,
)
from aip.transport import TransportState


class MockWebSocketTransport(WebSocketTransport):
    """Mock WebSocket transport for integration testing."""

    def __init__(self):
        super().__init__()
        self.sent_data = []
        self.receive_queue = asyncio.Queue()
        self._state = TransportState.CONNECTED

    async def connect(self, url: str, **kwargs) -> None:
        self._state = TransportState.CONNECTED

    async def send(self, data: bytes) -> None:
        self.sent_data.append(data)

    async def receive(self) -> bytes:
        return await self.receive_queue.get()

    async def close(self) -> None:
        self._state = TransportState.DISCONNECTED


class TestProtocolIntegration:
    """Test integration between protocol components."""

    @pytest.mark.asyncio
    async def test_registration_flow(self):
        """Test complete registration flow."""
        # Setup client protocol
        client_transport = MockWebSocketTransport()
        client_protocol = RegistrationProtocol(client_transport)

        # Setup server protocol
        server_transport = MockWebSocketTransport()
        server_protocol = RegistrationProtocol(server_transport)

        # Client sends registration
        registration_task = asyncio.create_task(
            client_protocol.register_as_device(
                device_id="test_device",
                metadata={"platform": "windows"},
            )
        )

        # Wait for message to be sent
        await asyncio.sleep(0.1)

        # Server receives registration
        assert len(client_transport.sent_data) == 1
        reg_data = client_transport.sent_data[0]

        # Server sends response
        response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
        )
        await client_transport.receive_queue.put(response.model_dump_json().encode())

        # Client should complete registration
        success = await registration_task
        assert success is True

    @pytest.mark.asyncio
    async def test_heartbeat_exchange(self):
        """Test heartbeat message exchange."""
        from aip.protocol.heartbeat import HeartbeatProtocol

        # Client protocol
        client_transport = MockWebSocketTransport()
        client_protocol = HeartbeatProtocol(client_transport)

        # Send heartbeat
        await client_protocol.send_heartbeat("test_client")

        # Verify message sent
        assert len(client_transport.sent_data) == 1
        sent_data = client_transport.sent_data[0].decode()
        assert "heartbeat" in sent_data
        assert "test_client" in sent_data


class TestMessageFlow:
    """Test message flow scenarios."""

    @pytest.mark.asyncio
    async def test_task_request_flow(self):
        """Test task request and response flow."""
        from aip.protocol.task_execution import TaskExecutionProtocol

        transport = MockWebSocketTransport()
        protocol = TaskExecutionProtocol(transport)

        # Send task request
        await protocol.send_task_request(
            request="Execute test task",
            task_name="test_task",
            session_id="session_123",
            client_id="test_device",
            client_type=ClientType.DEVICE,
        )

        # Verify message
        assert len(transport.sent_data) == 1
        msg_data = transport.sent_data[0].decode()
        assert "Execute test task" in msg_data
        assert "test_task" in msg_data

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error message handling."""
        transport = MockWebSocketTransport()
        protocol = AIPProtocol(transport)

        # Create error message
        error_msg = ClientMessage(
            type=ClientMessageType.ERROR,
            client_id="test_device",
            status=TaskStatus.ERROR,
            error="Test error message",
        )

        # Send error
        await protocol.send_message(error_msg)

        # Verify error sent
        assert len(transport.sent_data) == 1
        msg_data = transport.sent_data[0].decode()
        assert "error" in msg_data
        assert "Test error message" in msg_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
