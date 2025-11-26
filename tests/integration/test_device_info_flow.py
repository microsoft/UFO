"""
Integration Tests for Device Info Flow

Tests the complete flow of device info from device client to constellation client.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from aip.messages import (
    ClientMessage,
    ClientMessageType,
    ClientType,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from ufo.server.services.ws_manager import WSManager
from ufo.server.ws.handler import UFOWebSocketHandler
from ufo.server.services.session_manager import SessionManager


class TestAgentProfileIntegration:
    """Integration tests for device info flow"""

    @pytest.mark.asyncio
    async def test_device_registration_with_system_info(self):
        """Test device registering with system info"""
        ws_manager = WSManager()
        session_manager = SessionManager()
        handler = UFOWebSocketHandler(ws_manager, session_manager)

        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.receive_text = AsyncMock()

        # Simulate device registration message with system info
        device_reg_message = ClientMessage(
            type=ClientMessageType.REGISTER,
            client_id="device_001",
            client_type=ClientType.DEVICE,
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                "system_info": {
                    "device_id": "device_001",
                    "platform": "windows",
                    "os_version": "10.0.19041",
                    "cpu_count": 8,
                    "memory_total_gb": 16.0,
                    "hostname": "test-pc",
                    "ip_address": "192.168.1.100",
                    "supported_features": ["gui", "cli", "browser"],
                    "platform_type": "computer",
                    "schema_version": "1.0",
                    "custom_metadata": {},
                },
                "registration_time": datetime.now(timezone.utc).isoformat(),
            },
        )

        mock_websocket.receive_text.return_value = device_reg_message.model_dump_json()

        # Connect device
        client_id = await handler.connect(mock_websocket)

        # Verify device was registered
        assert client_id == "device_001"
        assert ws_manager.is_device_connected("device_001")

        # Verify system info was stored
        device_info = ws_manager.get_device_system_info("device_001")
        assert device_info is not None
        assert device_info["platform"] == "windows"
        assert device_info["cpu_count"] == 8
        assert device_info["memory_total_gb"] == 16.0
        assert "gui" in device_info["supported_features"]

    @pytest.mark.asyncio
    async def test_constellation_request_device_info(self):
        """Test constellation requesting device info via handler"""
        ws_manager = WSManager()
        session_manager = SessionManager()
        handler = UFOWebSocketHandler(ws_manager, session_manager)

        # First, register a device with system info
        mock_device_ws = Mock()
        device_system_info = {
            "device_id": "device_001",
            "platform": "linux",
            "cpu_count": 4,
            "memory_total_gb": 8.0,
        }

        ws_manager.add_client(
            "device_001",
            mock_device_ws,
            ClientType.DEVICE,
            {"system_info": device_system_info},
        )

        # Now constellation requests device info
        mock_constellation_ws = AsyncMock()

        constellation_request = ClientMessage(
            type=ClientMessageType.DEVICE_INFO_REQUEST,
            client_type=ClientType.CONSTELLATION,
            client_id="constellation_001@device_001",
            target_id="device_001",
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Handle the request
        await handler.handle_device_info_request(
            constellation_request, mock_constellation_ws
        )

        # Verify response was sent
        mock_constellation_ws.send_text.assert_called_once()

        # Parse the response
        response_json = mock_constellation_ws.send_text.call_args[0][0]
        response = ServerMessage.model_validate_json(response_json)

        assert response.type == ServerMessageType.DEVICE_INFO_RESPONSE
        assert response.status == TaskStatus.OK
        assert response.result is not None
        assert response.result["platform"] == "linux"
        assert response.result["cpu_count"] == 4

    @pytest.mark.asyncio
    async def test_request_device_info_not_found(self):
        """Test requesting info for non-existent device"""
        ws_manager = WSManager()
        session_manager = SessionManager()
        handler = UFOWebSocketHandler(ws_manager, session_manager)

        mock_constellation_ws = AsyncMock()

        constellation_request = ClientMessage(
            type=ClientMessageType.DEVICE_INFO_REQUEST,
            client_type=ClientType.CONSTELLATION,
            client_id="constellation_001@device_999",
            target_id="device_999",
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        await handler.handle_device_info_request(
            constellation_request, mock_constellation_ws
        )

        # Verify error response
        response_json = mock_constellation_ws.send_text.call_args[0][0]
        response = ServerMessage.model_validate_json(response_json)

        assert response.type == ServerMessageType.DEVICE_INFO_RESPONSE
        assert response.status == TaskStatus.ERROR
        assert "not found" in response.result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_device_info_with_server_config(self):
        """Test device info merging with server config"""
        import tempfile
        import os

        # Create server config
        yaml_content = """
devices:
  device_001:
    tags:
      - production
      - high_priority
    tier: enterprise
    additional_features:
      - advanced_automation
    max_concurrent_tasks: 5
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Create WSManager with config
            ws_manager = WSManager(device_config_path=temp_path)

            # Register device
            mock_ws = Mock()
            device_system_info = {
                "device_id": "device_001",
                "platform": "windows",
                "cpu_count": 16,
                "memory_total_gb": 32.0,
                "supported_features": ["gui", "cli"],
                "custom_metadata": {},
            }

            ws_manager.add_client(
                "device_001",
                mock_ws,
                ClientType.DEVICE,
                {"system_info": device_system_info},
            )

            # Retrieve merged info
            merged_info = ws_manager.get_device_system_info("device_001")

            # Verify system info is preserved
            assert merged_info["platform"] == "windows"
            assert merged_info["cpu_count"] == 16

            # Verify server config was merged
            assert "tags" in merged_info
            assert "production" in merged_info["tags"]
            assert "high_priority" in merged_info["tags"]
            assert merged_info["custom_metadata"]["tier"] == "enterprise"

            # Verify features were merged
            assert "gui" in merged_info["supported_features"]
            assert "advanced_automation" in merged_info["supported_features"]

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_multiple_devices_different_info(self):
        """Test managing multiple devices with different system info"""
        ws_manager = WSManager()

        # Register Windows device
        mock_ws1 = Mock()
        ws_manager.add_client(
            "windows_device",
            mock_ws1,
            ClientType.DEVICE,
            {
                "system_info": {
                    "device_id": "windows_device",
                    "platform": "windows",
                    "cpu_count": 8,
                    "memory_total_gb": 16.0,
                    "supported_features": ["gui", "windows_apps"],
                }
            },
        )

        # Register Linux device
        mock_ws2 = Mock()
        ws_manager.add_client(
            "linux_device",
            mock_ws2,
            ClientType.DEVICE,
            {
                "system_info": {
                    "device_id": "linux_device",
                    "platform": "linux",
                    "cpu_count": 32,
                    "memory_total_gb": 128.0,
                    "supported_features": ["cli", "docker", "kubernetes"],
                }
            },
        )

        # Register macOS device
        mock_ws3 = Mock()
        ws_manager.add_client(
            "macos_device",
            mock_ws3,
            ClientType.DEVICE,
            {
                "system_info": {
                    "device_id": "macos_device",
                    "platform": "darwin",
                    "cpu_count": 10,
                    "memory_total_gb": 32.0,
                    "supported_features": ["gui", "macos_apps"],
                }
            },
        )

        # Get all devices info
        all_info = ws_manager.get_all_devices_info()

        assert len(all_info) == 3
        assert all_info["windows_device"]["platform"] == "windows"
        assert all_info["linux_device"]["platform"] == "linux"
        assert all_info["macos_device"]["platform"] == "darwin"

        # Verify specific device info
        windows_info = ws_manager.get_device_system_info("windows_device")
        assert "windows_apps" in windows_info["supported_features"]

        linux_info = ws_manager.get_device_system_info("linux_device")
        assert linux_info["cpu_count"] == 32
        assert "docker" in linux_info["supported_features"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
