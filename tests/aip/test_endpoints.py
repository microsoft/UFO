# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test AIP Endpoints

Tests endpoint implementations for server, client, and constellation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aip.endpoints import (
    AIPEndpoint,
    DeviceServerEndpoint,
    DeviceClientEndpoint,
    ConstellationEndpoint,
)


class TestDeviceServerEndpoint:
    """Test device server endpoint."""

    @pytest.fixture
    def mock_managers(self):
        """Create mock managers."""
        ws_manager = MagicMock()
        ws_manager.get_device_sessions.return_value = []

        session_manager = MagicMock()
        session_manager.cancel_task = AsyncMock()

        return ws_manager, session_manager

    @pytest.mark.asyncio
    async def test_endpoint_creation(self, mock_managers):
        """Test creating device server endpoint."""
        ws_manager, session_manager = mock_managers

        endpoint = DeviceServerEndpoint(
            ws_manager=ws_manager,
            session_manager=session_manager,
            local=False,
        )

        assert endpoint.ws_manager == ws_manager
        assert endpoint.session_manager == session_manager
        assert endpoint.local is False

    @pytest.mark.asyncio
    async def test_start_stop(self, mock_managers):
        """Test starting and stopping endpoint."""
        ws_manager, session_manager = mock_managers

        endpoint = DeviceServerEndpoint(
            ws_manager=ws_manager,
            session_manager=session_manager,
        )

        await endpoint.start()
        await endpoint.stop()

    @pytest.mark.asyncio
    async def test_cancel_device_tasks(self, mock_managers):
        """Test cancelling device tasks."""
        ws_manager, session_manager = mock_managers
        ws_manager.get_device_sessions.return_value = ["session1", "session2"]

        endpoint = DeviceServerEndpoint(
            ws_manager=ws_manager,
            session_manager=session_manager,
        )

        await endpoint.cancel_device_tasks("test_device", "test_reason")

        # Verify cancel_task was called for each session
        assert session_manager.cancel_task.call_count == 2


class TestConstellationEndpoint:
    """Test constellation endpoint."""

    @pytest.mark.asyncio
    async def test_endpoint_creation(self):
        """Test creating constellation endpoint."""
        endpoint = ConstellationEndpoint(
            task_name="test_task",
            message_processor=None,
        )

        assert endpoint.task_name == "test_task"
        assert endpoint.connection_manager is not None

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping endpoint."""
        endpoint = ConstellationEndpoint(
            task_name="test_task",
        )

        await endpoint.start()

        # Mock disconnect_all
        endpoint.connection_manager.disconnect_all = AsyncMock()

        await endpoint.stop()

        endpoint.connection_manager.disconnect_all.assert_called_once()


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_import_from_contracts(self):
        """Test importing from ufo.contracts.contracts works."""
        from aip.messages import (
            ClientMessage,
            ClientMessageType,
            ServerMessage,
            TaskStatus,
        )

        # Should not raise ImportError
        assert ClientMessage is not None
        assert ClientMessageType is not None
        assert ServerMessage is not None
        assert TaskStatus is not None

    def test_message_creation_compatibility(self):
        """Test creating messages with old import path."""
        from aip.messages import ClientMessage, ClientMessageType, TaskStatus

        msg = ClientMessage(
            type=ClientMessageType.HEARTBEAT,
            client_id="test",
            status=TaskStatus.OK,
        )

        assert msg.type == ClientMessageType.HEARTBEAT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
