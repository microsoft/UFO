"""
Comprehensive Unit Tests for Constellation Client AIP Migration

Tests verify that AIP migration maintains:
1. Message format compatibility
2. Protocol behavior consistency
3. Error handling
4. State management
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone

from aip.messages import (
    ClientMessage,
    ClientMessageType,
    ClientType,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from aip.protocol.heartbeat import HeartbeatProtocol
from aip.protocol.registration import RegistrationProtocol
from aip.transport.websocket import WebSocketTransport
from galaxy.client.components.connection_manager import WebSocketConnectionManager
from galaxy.client.components.heartbeat_manager import HeartbeatManager
from galaxy.client.components.message_processor import MessageProcessor
from galaxy.client.components.device_registry import DeviceRegistry
from galaxy.client.components.types import AgentProfile, TaskRequest


class TestConnectionManagerAIPMigration:
    """Test ConnectionManager AIP integration."""

    @pytest.mark.asyncio
    async def test_transport_initialization(self):
        """Test that transports are properly initialized."""
        manager = WebSocketConnectionManager(task_name="test_task")

        assert hasattr(manager, "_transports")
        assert hasattr(manager, "_registration_protocols")
        assert hasattr(manager, "_task_protocols")
        assert hasattr(manager, "_device_info_protocols")
        assert len(manager._transports) == 0

    @pytest.mark.asyncio
    async def test_protocol_instance_creation(self):
        """Test that protocol instances are created per device."""
        manager = WebSocketConnectionManager(task_name="test_task")

        # Mock transport
        mock_transport = Mock(spec=WebSocketTransport)
        mock_transport.is_connected = True

        device_id = "device_001"
        manager._transports[device_id] = mock_transport

        # Create protocols
        manager._registration_protocols[device_id] = RegistrationProtocol(
            mock_transport
        )
        manager._task_protocols[device_id] = Mock()
        manager._device_info_protocols[device_id] = Mock()

        assert device_id in manager._transports
        assert device_id in manager._registration_protocols
        assert device_id in manager._task_protocols
        assert device_id in manager._device_info_protocols

    @pytest.mark.asyncio
    async def test_is_connected_uses_transport(self):
        """Test that is_connected checks transport state."""
        manager = WebSocketConnectionManager(task_name="test_task")
        device_id = "device_001"

        # No transport - should be False
        assert manager.is_connected(device_id) is False

        # Transport exists but not connected
        mock_transport = Mock(spec=WebSocketTransport)
        mock_transport.is_connected = False
        manager._transports[device_id] = mock_transport
        assert manager.is_connected(device_id) is False

        # Transport connected
        mock_transport.is_connected = True
        assert manager.is_connected(device_id) is True

    @pytest.mark.asyncio
    async def test_cleanup_removes_all_protocols(self):
        """Test that cleanup removes all protocol instances."""
        manager = WebSocketConnectionManager(task_name="test_task")
        device_id = "device_001"

        # Setup protocols
        manager._transports[device_id] = Mock()
        manager._registration_protocols[device_id] = Mock()
        manager._task_protocols[device_id] = Mock()
        manager._device_info_protocols[device_id] = Mock()

        # Cleanup
        manager._cleanup_device_protocols(device_id)

        # Verify all removed
        assert device_id not in manager._transports
        assert device_id not in manager._registration_protocols
        assert device_id not in manager._task_protocols
        assert device_id not in manager._device_info_protocols


class TestMessageProcessorAIPMigration:
    """Test MessageProcessor AIP integration."""

    @pytest.mark.asyncio
    async def test_uses_transport_not_websocket(self):
        """Test that message processor uses Transport instead of WebSocket."""
        device_registry = DeviceRegistry()
        heartbeat_manager = Mock(spec=HeartbeatManager)
        connection_manager = Mock(spec=WebSocketConnectionManager)
        message_processor = MessageProcessor(
            device_registry, heartbeat_manager, connection_manager
        )

        device_id = "device_001"
        mock_transport = Mock(spec=WebSocketTransport)
        mock_transport.is_connected = False  # Will stop loop immediately

        # Should accept Transport, not WebSocket
        message_processor.start_message_handler(device_id, mock_transport)

        assert device_id in message_processor._message_handlers

    @pytest.mark.asyncio
    async def test_message_loop_uses_transport_receive(self):
        """Test that message loop uses transport.receive()."""
        device_registry = DeviceRegistry()
        heartbeat_manager = Mock(spec=HeartbeatManager)
        connection_manager = Mock(spec=WebSocketConnectionManager)
        message_processor = MessageProcessor(
            device_registry, heartbeat_manager, connection_manager
        )

        device_id = "device_001"

        # Mock transport
        mock_transport = AsyncMock(spec=WebSocketTransport)
        mock_transport.is_connected = True

        # Prepare test message
        test_message = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Make receive return message once, then set is_connected to False
        call_count = 0

        async def mock_receive():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return test_message.model_dump_json().encode("utf-8")
            # After first message, disconnect to stop loop
            mock_transport.is_connected = False
            await asyncio.sleep(0.1)  # Give time for loop to check
            raise asyncio.CancelledError()

        mock_transport.receive = mock_receive

        # Start handler (will process one message then stop)
        task = asyncio.create_task(
            message_processor._handle_device_messages(device_id, mock_transport)
        )

        # Wait a bit for message processing
        await asyncio.sleep(0.2)

        # Cancel task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


class TestHeartbeatManagerAIPMigration:
    """Test HeartbeatManager AIP integration."""

    @pytest.mark.asyncio
    async def test_creates_heartbeat_protocol_instances(self):
        """Test that heartbeat manager creates HeartbeatProtocol instances."""
        connection_manager = Mock(spec=WebSocketConnectionManager)
        connection_manager.task_name = "test_task"
        connection_manager._transports = {}
        device_registry = DeviceRegistry()

        heartbeat_manager = HeartbeatManager(
            connection_manager=connection_manager,
            device_registry=device_registry,
            heartbeat_interval=1.0,
        )

        assert hasattr(heartbeat_manager, "_heartbeat_protocols")
        assert len(heartbeat_manager._heartbeat_protocols) == 0

    @pytest.mark.asyncio
    async def test_heartbeat_protocol_cleanup_on_stop(self):
        """Test that stopping heartbeat cleans up protocol instance."""
        connection_manager = Mock(spec=WebSocketConnectionManager)
        connection_manager.task_name = "test_task"
        connection_manager._transports = {}
        connection_manager.is_connected = Mock(return_value=False)
        device_registry = DeviceRegistry()

        heartbeat_manager = HeartbeatManager(
            connection_manager=connection_manager,
            device_registry=device_registry,
            heartbeat_interval=0.1,
        )

        device_id = "device_001"

        # Manually add protocol
        heartbeat_manager._heartbeat_protocols[device_id] = Mock()
        heartbeat_manager._heartbeat_tasks[device_id] = Mock()
        heartbeat_manager._heartbeat_tasks[device_id].done = Mock(return_value=True)

        # Stop heartbeat
        heartbeat_manager.stop_heartbeat(device_id)

        # Protocol should be cleaned up
        assert device_id not in heartbeat_manager._heartbeat_protocols


class TestMessageFormatCompatibility:
    """Test that message formats are compatible with server expectations."""

    def test_registration_message_format(self):
        """Test constellation registration message format."""
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
                "capabilities": ["task_distribution"],
            },
        )

        # Verify required fields
        assert reg_msg.type == ClientMessageType.REGISTER
        assert reg_msg.client_type == ClientType.CONSTELLATION
        assert reg_msg.client_id == constellation_id
        assert reg_msg.target_id == target_device
        assert reg_msg.metadata["targeted_device_id"] == target_device

        # Verify serialization
        json_str = reg_msg.model_dump_json()
        assert "REGISTER" in json_str or "register" in json_str
        assert constellation_id in json_str

    def test_heartbeat_message_format(self):
        """Test heartbeat message format."""
        client_id = "test_constellation@device_001"

        heartbeat_msg = ClientMessage(
            type=ClientMessageType.HEARTBEAT,
            client_id=client_id,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"device_id": "device_001"},
        )

        # Verify required fields
        assert heartbeat_msg.type == ClientMessageType.HEARTBEAT
        assert heartbeat_msg.client_id == client_id
        assert heartbeat_msg.status == TaskStatus.OK
        assert heartbeat_msg.metadata["device_id"] == "device_001"

        # Verify serialization
        json_str = heartbeat_msg.model_dump_json()
        assert client_id in json_str

    def test_task_message_format(self):
        """Test task assignment message format."""
        task_msg = ClientMessage(
            type=ClientMessageType.TASK,
            client_type=ClientType.CONSTELLATION,
            client_id="test_constellation@device_001",
            target_id="device_001",
            task_name="galaxy/test_constellation/excel_task",
            request="Open Excel and create a spreadsheet",
            session_id="test_constellation@task_123",
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=TaskStatus.CONTINUE,
        )

        # Verify required fields
        assert task_msg.type == ClientMessageType.TASK
        assert task_msg.client_type == ClientType.CONSTELLATION
        assert task_msg.target_id == "device_001"
        assert task_msg.session_id is not None
        assert task_msg.request is not None

        # Verify serialization
        json_str = task_msg.model_dump_json()
        assert "device_001" in json_str

    def test_device_info_request_format(self):
        """Test device info request message format."""
        request_msg = ClientMessage(
            type=ClientMessageType.DEVICE_INFO_REQUEST,
            client_type=ClientType.CONSTELLATION,
            client_id="test_constellation@device_001",
            target_id="device_001",
            request_id="device_info_001",
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=TaskStatus.OK,
        )

        # Verify required fields
        assert request_msg.type == ClientMessageType.DEVICE_INFO_REQUEST
        assert request_msg.client_type == ClientType.CONSTELLATION
        assert request_msg.request_id is not None

        # Verify serialization
        json_str = request_msg.model_dump_json()
        assert "device_info" in json_str.lower()


class TestProtocolBehaviorConsistency:
    """Test that protocol behavior is consistent before and after migration."""

    @pytest.mark.asyncio
    async def test_registration_workflow(self):
        """Test complete registration workflow."""
        # Setup
        transport = AsyncMock(spec=WebSocketTransport)
        protocol = RegistrationProtocol(transport)

        # Mock successful response
        response = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        async def mock_receive(msg_type):
            return response

        protocol.receive_message = mock_receive

        # Execute registration
        success = await protocol.register_as_constellation(
            constellation_id="test@device_001",
            target_device="device_001",
            metadata={"test": "data"},
        )

        # Verify
        assert success is True
        assert len(transport.send.call_args_list) > 0

    @pytest.mark.asyncio
    async def test_heartbeat_sending(self):
        """Test heartbeat sending workflow."""
        transport = AsyncMock(spec=WebSocketTransport)
        protocol = HeartbeatProtocol(transport)

        # Send heartbeat
        await protocol.send_heartbeat(
            client_id="test@device_001",
            metadata={"device_id": "device_001"},
        )

        # Verify message was sent
        assert transport.send.called
        sent_data = transport.send.call_args[0][0]
        msg = ClientMessage.model_validate_json(sent_data.decode())

        assert msg.type == ClientMessageType.HEARTBEAT
        assert msg.client_id == "test@device_001"
        assert msg.metadata["device_id"] == "device_001"

    @pytest.mark.asyncio
    async def test_error_handling_consistency(self):
        """Test that error handling remains consistent."""
        transport = AsyncMock(spec=WebSocketTransport)
        protocol = RegistrationProtocol(transport)

        # Mock error response
        error_response = ServerMessage(
            type=ServerMessageType.ERROR,
            status=TaskStatus.ERROR,
            error="Device not found",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        async def mock_receive(msg_type):
            return error_response

        protocol.receive_message = mock_receive

        # Execute registration - should return False on error
        success = await protocol.register_as_constellation(
            constellation_id="test@invalid_device",
            target_device="invalid_device",
        )

        assert success is False


class TestStateManagement:
    """Test state management across AIP migration."""

    @pytest.mark.asyncio
    async def test_pending_task_tracking(self):
        """Test that pending tasks are properly tracked."""
        manager = WebSocketConnectionManager(task_name="test_task")

        task_id = "task_123"
        device_id = "device_001"
        future = asyncio.Future()

        manager._pending_tasks[task_id] = (device_id, future)

        # Verify tracking
        assert task_id in manager._pending_tasks
        assert manager._pending_tasks[task_id][0] == device_id
        assert manager._pending_tasks[task_id][1] == future

    @pytest.mark.asyncio
    async def test_pending_task_completion(self):
        """Test that pending tasks are completed correctly."""
        manager = WebSocketConnectionManager(task_name="test_task")

        task_id = "task_123"
        device_id = "device_001"
        future = asyncio.Future()

        manager._pending_tasks[task_id] = (device_id, future)

        # Complete task
        response = ServerMessage(
            type=ServerMessageType.TASK_END,
            status=TaskStatus.COMPLETED,
            session_id=task_id,
            result={"data": "success"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        manager.complete_task_response(task_id, response)

        # Verify future is resolved
        assert future.done()
        assert future.result() == response

    @pytest.mark.asyncio
    async def test_pending_task_cancellation(self):
        """Test that pending tasks are cancelled on disconnect."""
        manager = WebSocketConnectionManager(task_name="test_task")

        device_id = "device_001"
        task_id = "task_123"
        future = asyncio.Future()

        manager._pending_tasks[task_id] = (device_id, future)

        # Cancel pending tasks for device
        manager._cancel_pending_tasks_for_device(device_id)

        # Verify future is cancelled with exception
        assert future.done()
        with pytest.raises(ConnectionError):
            future.result()

    @pytest.mark.asyncio
    async def test_device_info_request_tracking(self):
        """Test device info request tracking."""
        manager = WebSocketConnectionManager(task_name="test_task")

        request_id = "device_info_123"
        future = asyncio.Future()

        manager._pending_device_info[request_id] = future

        # Complete request
        device_info = {"os": "Windows", "version": "11"}
        manager.complete_device_info_response(request_id, device_info)

        # Verify
        assert future.done()
        assert future.result() == device_info


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
