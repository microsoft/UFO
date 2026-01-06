# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test AIP Protocol Layer

Tests protocol implementations including registration, task execution, and heartbeat.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aip.messages import (
    ClientMessage,
    ClientMessageType,
    ClientType,
    Command,
    Result,
    ResultStatus,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from aip.protocol import (
    AIPProtocol,
    DeviceInfoProtocol,
    HeartbeatProtocol,
    RegistrationProtocol,
    TaskExecutionProtocol,
)
from aip.transport import Transport, TransportState


class MockTransport(Transport):
    """Mock transport for protocol testing."""

    def __init__(self):
        super().__init__()
        self.sent_messages = []
        self.receive_queue = asyncio.Queue()
        self._state = TransportState.CONNECTED

    async def connect(self, url: str, **kwargs) -> None:
        self._state = TransportState.CONNECTED

    async def send(self, data: bytes) -> None:
        self.sent_messages.append(data)

    async def receive(self) -> bytes:
        return await self.receive_queue.get()

    async def close(self) -> None:
        self._state = TransportState.DISCONNECTED

    async def wait_closed(self) -> None:
        pass


class TestAIPProtocol:
    """Test core AIP protocol functionality."""

    @pytest.mark.asyncio
    async def test_protocol_send_message(self):
        """Test sending a message through protocol."""
        transport = MockTransport()
        protocol = AIPProtocol(transport)

        msg = ClientMessage(
            type=ClientMessageType.HEARTBEAT,
            client_id="test_device",
            status=TaskStatus.OK,
        )

        await protocol.send_message(msg)

        assert len(transport.sent_messages) == 1
        assert b"heartbeat" in transport.sent_messages[0]

    @pytest.mark.asyncio
    async def test_protocol_receive_message(self):
        """Test receiving a message through protocol."""
        transport = MockTransport()
        protocol = AIPProtocol(transport)

        # Queue a message for receiving
        msg = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
        )
        await transport.receive_queue.put(msg.model_dump_json().encode())

        received = await protocol.receive_message(ServerMessage)

        assert received.type == ServerMessageType.HEARTBEAT
        assert received.status == TaskStatus.OK

    def test_protocol_is_connected(self):
        """Test protocol connection status."""
        transport = MockTransport()
        protocol = AIPProtocol(transport)

        assert protocol.is_connected()

        transport._state = TransportState.DISCONNECTED
        assert not protocol.is_connected()


class TestRegistrationProtocol:
    """Test registration protocol."""

    @pytest.mark.asyncio
    async def test_register_as_device(self):
        """Test device registration."""
        transport = MockTransport()
        protocol = RegistrationProtocol(transport)

        # Queue a successful response
        response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
        )
        await transport.receive_queue.put(response.model_dump_json().encode())

        success = await protocol.register_as_device(
            device_id="test_device",
            metadata={"cpu_count": 8},
            platform="windows",
        )

        assert success is True
        assert len(transport.sent_messages) == 1

        # Verify sent message
        sent_data = transport.sent_messages[0].decode()
        assert "register" in sent_data
        assert "test_device" in sent_data

    @pytest.mark.asyncio
    async def test_register_as_constellation(self):
        """Test constellation registration."""
        transport = MockTransport()
        protocol = RegistrationProtocol(transport)

        # Queue a successful response
        response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
        )
        await transport.receive_queue.put(response.model_dump_json().encode())

        success = await protocol.register_as_constellation(
            constellation_id="test_constellation",
            target_device="target_device",
            metadata={"capabilities": ["task_distribution"]},
        )

        assert success is True
        assert len(transport.sent_messages) == 1

        # Verify sent message
        sent_data = transport.sent_messages[0].decode()
        assert "register" in sent_data
        assert "constellation" in sent_data


class TestTaskExecutionProtocol:
    """Test task execution protocol."""

    @pytest.mark.asyncio
    async def test_send_task_request(self):
        """Test sending task request."""
        transport = MockTransport()
        protocol = TaskExecutionProtocol(transport)

        await protocol.send_task_request(
            request="Execute task",
            task_name="test_task",
            session_id="session_123",
            client_id="test_device",
        )

        assert len(transport.sent_messages) == 1
        sent_data = transport.sent_messages[0].decode()
        assert "task" in sent_data
        assert "Execute task" in sent_data

    @pytest.mark.asyncio
    async def test_send_command(self):
        """Test sending commands."""
        transport = MockTransport()
        protocol = TaskExecutionProtocol(transport)

        commands = [
            Command(tool_name="screenshot", tool_type="data_collection"),
            Command(tool_name="click", tool_type="action"),
        ]

        # Use send_commands instead of send_command
        await protocol.send_commands(
            actions=commands,
            session_id="session_123",
            response_id="resp_123",
        )

        assert len(transport.sent_messages) == 1
        sent_data = transport.sent_messages[0].decode()
        assert "command" in sent_data
        assert "screenshot" in sent_data

    @pytest.mark.asyncio
    async def test_send_task_end(self):
        """Test sending task end."""
        transport = MockTransport()
        protocol = TaskExecutionProtocol(transport)

        await protocol.send_task_end(
            session_id="session_123",
            status=TaskStatus.COMPLETED,
            result={"output": "success"},
        )

        assert len(transport.sent_messages) == 1
        sent_data = transport.sent_messages[0].decode()
        assert "task_end" in sent_data
        assert "completed" in sent_data


class TestHeartbeatProtocol:
    """Test heartbeat protocol."""

    @pytest.mark.asyncio
    async def test_send_heartbeat(self):
        """Test sending heartbeat."""
        transport = MockTransport()
        protocol = HeartbeatProtocol(transport)

        await protocol.send_heartbeat(client_id="test_device")

        assert len(transport.sent_messages) == 1
        sent_data = transport.sent_messages[0].decode()
        assert "heartbeat" in sent_data

    @pytest.mark.asyncio
    async def test_heartbeat_loop(self):
        """Test automatic heartbeat loop."""
        transport = MockTransport()
        protocol = HeartbeatProtocol(transport)

        await protocol.start_heartbeat(client_id="test_device", interval=0.1)

        # Wait for a few heartbeats
        await asyncio.sleep(0.3)

        # Stop heartbeat
        await protocol.stop_heartbeat()

        # Should have sent at least 2 heartbeats
        assert len(transport.sent_messages) >= 2


class TestDeviceInfoProtocol:
    """Test device info protocol."""

    @pytest.mark.asyncio
    async def test_request_device_info(self):
        """Test requesting device info."""
        transport = MockTransport()
        protocol = DeviceInfoProtocol(transport)

        await protocol.request_device_info(
            constellation_id="test_constellation",
            target_device="test_device",
            request_id="req_123",
        )

        assert len(transport.sent_messages) == 1
        sent_data = transport.sent_messages[0].decode()
        assert "device_info_request" in sent_data

    @pytest.mark.asyncio
    async def test_send_device_info_response(self):
        """Test sending device info response."""
        transport = MockTransport()
        protocol = DeviceInfoProtocol(transport)

        device_info = {
            "platform": "windows",
            "cpu_count": 8,
            "memory_gb": 16,
        }

        await protocol.send_device_info_response(
            device_info=device_info,
            request_id="req_123",
        )

        assert len(transport.sent_messages) == 1
        sent_data = transport.sent_messages[0].decode()
        assert "device_info_response" in sent_data
        assert "windows" in sent_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
