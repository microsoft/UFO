"""
Integration Tests for Constellation-Server Communication via AIP

Tests verify that:
1. Constellation client sends messages in correct format
2. Mock server can parse and respond to messages
3. End-to-end message flows work correctly
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
import json

from aip.messages import (
    ClientMessage,
    ClientMessageType,
    ClientType,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from aip.protocol.registration import RegistrationProtocol
from aip.protocol.heartbeat import HeartbeatProtocol
from aip.protocol.task_execution import TaskExecutionProtocol
from aip.protocol.device_info import DeviceInfoProtocol
from aip.transport.websocket import WebSocketTransport


class MockServer:
    """Mock UFO server for testing constellation communication."""

    def __init__(self):
        self.received_messages = []
        self.client_registry = {}

    async def handle_client_message(self, message: ClientMessage) -> ServerMessage:
        """Handle incoming client message and generate appropriate response."""
        self.received_messages.append(message)

        # Handle registration
        if message.type == ClientMessageType.REGISTER:
            if message.client_type == ClientType.CONSTELLATION:
                self.client_registry[message.client_id] = {
                    "target_device": message.target_id,
                    "metadata": message.metadata,
                }
                return ServerMessage(
                    type=ServerMessageType.HEARTBEAT,
                    status=TaskStatus.OK,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    message="Registration successful",
                )

        # Handle heartbeat
        elif message.type == ClientMessageType.HEARTBEAT:
            return ServerMessage(
                type=ServerMessageType.HEARTBEAT,
                status=TaskStatus.OK,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Handle task
        elif message.type == ClientMessageType.TASK:
            # Simulate task processing
            return ServerMessage(
                type=ServerMessageType.TASK_END,
                session_id=message.session_id,
                status=TaskStatus.COMPLETED,
                result={"task": "completed", "request": message.request},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Handle device info request
        elif message.type == ClientMessageType.DEVICE_INFO_REQUEST:
            return ServerMessage(
                type=ServerMessageType.DEVICE_INFO_RESPONSE,
                response_id=message.request_id,
                status=TaskStatus.OK,
                result={
                    "device_id": message.target_id,
                    "os": "Windows",
                    "version": "11",
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Default error response
        return ServerMessage(
            type=ServerMessageType.ERROR,
            status=TaskStatus.ERROR,
            error=f"Unknown message type: {message.type}",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


@pytest.fixture
def mock_server():
    """Provide a mock server instance."""
    return MockServer()


class TestConstellationRegistrationCompatibility:
    """Test constellation registration message compatibility."""

    @pytest.mark.asyncio
    async def test_registration_message_can_be_parsed_by_server(self, mock_server):
        """Test that server can parse constellation registration message."""
        # Create registration message
        constellation_id = "test_constellation@device_001"
        target_device = "device_001"

        reg_msg = ClientMessage(
            type=ClientMessageType.REGISTER,
            client_type=ClientType.CONSTELLATION,
            client_id=constellation_id,
            target_id=target_device,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                "type": "constellation_client",
                "task_name": "test_constellation",
                "targeted_device_id": target_device,
            },
        )

        # Server processes message
        response = await mock_server.handle_client_message(reg_msg)

        # Verify server handled registration correctly
        assert response.status == TaskStatus.OK
        assert constellation_id in mock_server.client_registry
        assert mock_server.client_registry[constellation_id]["target_device"] == target_device

    @pytest.mark.asyncio
    async def test_registration_via_protocol(self, mock_server):
        """Test registration using RegistrationProtocol."""
        # Setup mock transport
        transport = AsyncMock(spec=WebSocketTransport)
        sent_messages = []

        async def capture_send(data):
            msg = ClientMessage.model_validate_json(data.decode())
            sent_messages.append(msg)
            # Simulate server response
            response = await mock_server.handle_client_message(msg)
            return response

        transport.send = capture_send

        # Create protocol and register
        protocol = RegistrationProtocol(transport)

        # Mock receive_message to return server response
        async def mock_receive(msg_type):
            if sent_messages:
                return await mock_server.handle_client_message(sent_messages[-1])
            return None

        protocol.receive_message = mock_receive

        success = await protocol.register_as_constellation(
            constellation_id="test@device_001",
            target_device="device_001",
            metadata={"task_name": "test"},
        )

        # Verify
        assert success is True
        assert len(sent_messages) == 1
        assert sent_messages[0].type == ClientMessageType.REGISTER
        assert sent_messages[0].client_type == ClientType.CONSTELLATION


class TestConstellationHeartbeatCompatibility:
    """Test heartbeat message compatibility."""

    @pytest.mark.asyncio
    async def test_heartbeat_message_format(self, mock_server):
        """Test that server can parse heartbeat messages."""
        heartbeat_msg = ClientMessage(
            type=ClientMessageType.HEARTBEAT,
            client_id="test_constellation@device_001",
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"device_id": "device_001"},
        )

        response = await mock_server.handle_client_message(heartbeat_msg)

        assert response.type == ServerMessageType.HEARTBEAT
        assert response.status == TaskStatus.OK

    @pytest.mark.asyncio
    async def test_heartbeat_via_protocol(self, mock_server):
        """Test heartbeat using HeartbeatProtocol."""
        transport = AsyncMock(spec=WebSocketTransport)
        sent_messages = []

        async def capture_send(data):
            msg = ClientMessage.model_validate_json(data.decode())
            sent_messages.append(msg)

        transport.send = capture_send

        protocol = HeartbeatProtocol(transport)

        await protocol.send_heartbeat(
            client_id="test@device_001",
            metadata={"device_id": "device_001"},
        )

        # Verify message format
        assert len(sent_messages) == 1
        assert sent_messages[0].type == ClientMessageType.HEARTBEAT
        assert sent_messages[0].metadata["device_id"] == "device_001"

        # Verify server can parse it
        response = await mock_server.handle_client_message(sent_messages[0])
        assert response.status == TaskStatus.OK


class TestConstellationTaskCompatibility:
    """Test task assignment message compatibility."""

    @pytest.mark.asyncio
    async def test_task_message_format(self, mock_server):
        """Test that server can parse task messages."""
        task_msg = ClientMessage(
            type=ClientMessageType.TASK,
            client_type=ClientType.CONSTELLATION,
            client_id="test_constellation@device_001",
            target_id="device_001",
            task_name="galaxy/test/excel_task",
            request="Open Excel",
            session_id="test@task_123",
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=TaskStatus.CONTINUE,
        )

        response = await mock_server.handle_client_message(task_msg)

        assert response.type == ServerMessageType.TASK_END
        assert response.session_id == "test@task_123"
        assert response.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_task_via_protocol(self, mock_server):
        """Test task execution using TaskExecutionProtocol."""
        transport = AsyncMock(spec=WebSocketTransport)
        sent_messages = []

        async def capture_send(data):
            msg = ClientMessage.model_validate_json(data.decode())
            sent_messages.append(msg)

        transport.send = capture_send

        protocol = TaskExecutionProtocol(transport)

        # Mock receive_message
        async def mock_receive(msg_type):
            if sent_messages:
                return await mock_server.handle_client_message(sent_messages[-1])
            return None

        protocol.receive_message = mock_receive

        # Send task request (constellation role)
        await protocol.send_task_request(
            request="test request",
            task_name="test_task",
            session_id="test@session_123",
            client_id="test@device_001",
            target_id="device_001",
            client_type=ClientType.CONSTELLATION,
        )

        # Verify
        assert len(sent_messages) == 1
        assert sent_messages[0].type == ClientMessageType.TASK
        assert sent_messages[0].request == "test request"


class TestConstellationDeviceInfoCompatibility:
    """Test device info request compatibility."""

    @pytest.mark.asyncio
    async def test_device_info_request_format(self, mock_server):
        """Test that server can parse device info requests."""
        request_msg = ClientMessage(
            type=ClientMessageType.DEVICE_INFO_REQUEST,
            client_type=ClientType.CONSTELLATION,
            client_id="test_constellation@device_001",
            target_id="device_001",
            request_id="device_info_123",
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=TaskStatus.OK,
        )

        response = await mock_server.handle_client_message(request_msg)

        assert response.type == ServerMessageType.DEVICE_INFO_RESPONSE
        assert response.response_id == "device_info_123"
        assert response.result is not None
        assert "device_id" in response.result

    @pytest.mark.asyncio
    async def test_device_info_via_protocol(self, mock_server):
        """Test device info request using DeviceInfoProtocol."""
        transport = AsyncMock(spec=WebSocketTransport)
        sent_messages = []

        async def capture_send(data):
            msg = ClientMessage.model_validate_json(data.decode())
            sent_messages.append(msg)

        transport.send = capture_send

        protocol = DeviceInfoProtocol(transport)

        # Mock receive_message
        async def mock_receive(msg_type):
            if sent_messages:
                return await mock_server.handle_client_message(sent_messages[-1])
            return None

        protocol.receive_message = mock_receive

        # Request device info (constellation-side method)
        await protocol.request_device_info(
            constellation_id="test@device_001",
            target_device="device_001",
            request_id="req_123",
        )

        # Verify
        assert len(sent_messages) == 1
        assert sent_messages[0].type == ClientMessageType.DEVICE_INFO_REQUEST


class TestMessageSerializationConsistency:
    """Test that message serialization is consistent."""

    def test_registration_message_json_format(self):
        """Test registration message JSON structure."""
        msg = ClientMessage(
            type=ClientMessageType.REGISTER,
            client_type=ClientType.CONSTELLATION,
            client_id="test@device_001",
            target_id="device_001",
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        json_str = msg.model_dump_json()
        parsed = json.loads(json_str)

        # Verify key fields are present and correct
        assert "type" in parsed
        assert "client_type" in parsed
        assert "client_id" in parsed
        assert parsed["client_id"] == "test@device_001"

        # Verify can be deserialized
        msg_copy = ClientMessage.model_validate_json(json_str)
        assert msg_copy.client_id == msg.client_id

    def test_task_message_json_format(self):
        """Test task message JSON structure."""
        msg = ClientMessage(
            type=ClientMessageType.TASK,
            client_type=ClientType.CONSTELLATION,
            client_id="test@device_001",
            target_id="device_001",
            task_name="test_task",
            request="test request",
            session_id="test@session_123",
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=TaskStatus.CONTINUE,
        )

        json_str = msg.model_dump_json()
        parsed = json.loads(json_str)

        # Verify key fields
        assert parsed["request"] == "test request"
        assert parsed["session_id"] == "test@session_123"

        # Verify roundtrip
        msg_copy = ClientMessage.model_validate_json(json_str)
        assert msg_copy.request == msg.request

    def test_server_response_parsing(self):
        """Test that client can parse server responses."""
        response = ServerMessage(
            type=ServerMessageType.TASK_END,
            session_id="test@session_123",
            status=TaskStatus.COMPLETED,
            result={"data": "success"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        json_str = response.model_dump_json()
        parsed = ServerMessage.model_validate_json(json_str)

        assert parsed.type == ServerMessageType.TASK_END
        assert parsed.session_id == "test@session_123"
        assert parsed.result["data"] == "success"


class TestEndToEndMessageFlow:
    """Test complete message flows end-to-end."""

    @pytest.mark.asyncio
    async def test_complete_registration_flow(self, mock_server):
        """Test complete registration flow from client to server."""
        # Setup
        transport = AsyncMock(spec=WebSocketTransport)
        messages_sent = []

        async def send_and_respond(data):
            # Parse sent message
            msg = ClientMessage.model_validate_json(data.decode())
            messages_sent.append(msg)

            # Get server response
            response = await mock_server.handle_client_message(msg)
            return response

        transport.send = send_and_respond

        # Create protocol
        protocol = RegistrationProtocol(transport)

        # Mock receive to get server response
        async def mock_receive(msg_type):
            if messages_sent:
                return await mock_server.handle_client_message(messages_sent[-1])
            return None

        protocol.receive_message = mock_receive

        # Execute registration
        success = await protocol.register_as_constellation(
            constellation_id="constellation_123@device_001",
            target_device="device_001",
            metadata={"task_name": "test_task"},
        )

        # Verify complete flow
        assert success is True
        assert len(messages_sent) == 1
        assert messages_sent[0].client_type == ClientType.CONSTELLATION
        assert "constellation_123@device_001" in mock_server.client_registry

    @pytest.mark.asyncio
    async def test_complete_task_execution_flow(self, mock_server):
        """Test complete task execution flow."""
        # First register
        await mock_server.handle_client_message(
            ClientMessage(
                type=ClientMessageType.REGISTER,
                client_type=ClientType.CONSTELLATION,
                client_id="test@device_001",
                target_id="device_001",
                status=TaskStatus.OK,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

        # Send task
        task_msg = ClientMessage(
            type=ClientMessageType.TASK,
            client_type=ClientType.CONSTELLATION,
            client_id="test@device_001",
            target_id="device_001",
            task_name="test_task",
            request="Test request",
            session_id="test@task_123",
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=TaskStatus.CONTINUE,
        )

        response = await mock_server.handle_client_message(task_msg)

        # Verify response
        assert response.type == ServerMessageType.TASK_END
        assert response.status == TaskStatus.COMPLETED
        assert response.session_id == "test@task_123"

    @pytest.mark.asyncio
    async def test_heartbeat_sequence(self, mock_server):
        """Test sequence of heartbeat messages."""
        client_id = "test@device_001"

        # Send multiple heartbeats
        for i in range(3):
            heartbeat = ClientMessage(
                type=ClientMessageType.HEARTBEAT,
                client_id=client_id,
                status=TaskStatus.OK,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={"device_id": "device_001", "sequence": i},
            )

            response = await mock_server.handle_client_message(heartbeat)
            assert response.status == TaskStatus.OK

        # Verify all heartbeats received
        heartbeats = [
            msg
            for msg in mock_server.received_messages
            if msg.type == ClientMessageType.HEARTBEAT
        ]
        assert len(heartbeats) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
