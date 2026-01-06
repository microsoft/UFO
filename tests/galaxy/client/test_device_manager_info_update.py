"""
Test for Device Manager AgentProfile Update

Tests that device system info is properly retrieved and stored in AgentProfile.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from galaxy.client.device_manager import ConstellationDeviceManager
from galaxy.client.components.types import DeviceStatus


class TestDeviceManagerInfoUpdate:
    """Test device info update in device manager"""

    @pytest.mark.asyncio
    async def test_connect_device_updates_device_info(self):
        """Test that connecting to device retrieves and updates AgentProfile"""
        manager = ConstellationDeviceManager(constellation_id="test_constellation")

        # Register a device
        device_id = "test_device_001"
        server_url = "ws://localhost:8000/ws"

        manager.device_registry.register_device(
            device_id=device_id,
            server_url=server_url,
            capabilities=["basic"],
            metadata={"initial": "data"},
        )

        # Mock the connection manager methods
        mock_websocket = AsyncMock()
        manager.connection_manager.connect_to_device = AsyncMock(
            return_value=mock_websocket
        )

        # Mock request_device_info to return system info
        mock_system_info = {
            "device_id": device_id,
            "platform": "windows",
            "os_version": "10.0.19041",
            "cpu_count": 8,
            "memory_total_gb": 16.0,
            "hostname": "test-pc",
            "ip_address": "192.168.1.100",
            "supported_features": ["gui", "cli", "browser"],
            "platform_type": "computer",
            "schema_version": "1.0",
            "custom_metadata": {"tier": "high_performance", "tags": ["production"]},
            "tags": ["production", "windows"],
        }

        manager.connection_manager.request_device_info = AsyncMock(
            return_value=mock_system_info
        )

        # Mock background services
        manager.message_processor.start_message_handler = Mock()
        manager.heartbeat_manager.start_heartbeat = Mock()
        manager.event_manager.notify_device_connected = AsyncMock()

        # Connect to device
        success = await manager.connect_device(device_id)

        assert success

        # Verify device info was updated
        device_info = manager.get_device_info(device_id)
        assert device_info is not None

        # Check OS was updated
        assert device_info.os == "windows"

        # Check capabilities were merged with features
        assert "gui" in device_info.capabilities
        assert "cli" in device_info.capabilities
        assert "browser" in device_info.capabilities
        assert "basic" in device_info.capabilities  # Original capability preserved

        # Check metadata was updated with system info
        assert "system_info" in device_info.metadata
        system_info = device_info.metadata["system_info"]
        assert system_info["platform"] == "windows"
        assert system_info["cpu_count"] == 8
        assert system_info["memory_total_gb"] == 16.0
        assert system_info["hostname"] == "test-pc"

        # Check custom metadata from server
        assert "custom_metadata" in device_info.metadata
        assert device_info.metadata["custom_metadata"]["tier"] == "high_performance"

        # Check tags
        assert "tags" in device_info.metadata
        assert "production" in device_info.metadata["tags"]
        assert "windows" in device_info.metadata["tags"]

        # Verify status is IDLE after connection
        assert device_info.status == DeviceStatus.IDLE

    @pytest.mark.asyncio
    async def test_get_device_system_info(self):
        """Test getting device system info"""
        manager = ConstellationDeviceManager(constellation_id="test_constellation")

        device_id = "test_device_002"
        manager.device_registry.register_device(
            device_id=device_id, server_url="ws://localhost:8000/ws"
        )

        # Initially no system info
        system_info = manager.get_device_system_info(device_id)
        assert system_info is None

        # Manually update device info (simulate connection)
        device_info = manager.get_device_info(device_id)
        device_info.metadata["system_info"] = {
            "platform": "linux",
            "cpu_count": 32,
            "memory_total_gb": 128.0,
        }

        # Now system info should be available
        system_info = manager.get_device_system_info(device_id)
        assert system_info is not None
        assert system_info["platform"] == "linux"
        assert system_info["cpu_count"] == 32

    @pytest.mark.asyncio
    async def test_connect_device_without_system_info(self):
        """Test connecting when server doesn't return system info"""
        manager = ConstellationDeviceManager(constellation_id="test_constellation")

        device_id = "test_device_003"
        manager.device_registry.register_device(
            device_id=device_id,
            server_url="ws://localhost:8000/ws",
            capabilities=["basic"],
        )

        # Mock connection manager
        mock_websocket = AsyncMock()
        manager.connection_manager.connect_to_device = AsyncMock(
            return_value=mock_websocket
        )

        # Mock request_device_info to return None (server has no info)
        manager.connection_manager.request_device_info = AsyncMock(return_value=None)

        # Mock background services
        manager.message_processor.start_message_handler = Mock()
        manager.heartbeat_manager.start_heartbeat = Mock()
        manager.event_manager.notify_device_connected = AsyncMock()

        # Connect to device
        success = await manager.connect_device(device_id)

        assert success

        # Device should still be connected even without system info
        device_info = manager.get_device_info(device_id)
        assert device_info.status == DeviceStatus.IDLE

        # Original capabilities should be preserved
        assert "basic" in device_info.capabilities

        # System info should not be present
        system_info = manager.get_device_system_info(device_id)
        assert system_info is None

    @pytest.mark.asyncio
    async def test_multiple_devices_different_system_info(self):
        """Test managing multiple devices with different system info"""
        manager = ConstellationDeviceManager(constellation_id="test_constellation")

        # Setup multiple devices
        devices_config = [
            {
                "device_id": "windows_device",
                "platform": "windows",
                "cpu_count": 8,
                "features": ["gui", "windows_apps"],
            },
            {
                "device_id": "linux_device",
                "platform": "linux",
                "cpu_count": 32,
                "features": ["cli", "docker"],
            },
            {
                "device_id": "macos_device",
                "platform": "darwin",
                "cpu_count": 10,
                "features": ["gui", "macos_apps"],
            },
        ]

        for config in devices_config:
            device_id = config["device_id"]

            # Register device
            manager.device_registry.register_device(
                device_id=device_id, server_url="ws://localhost:8000/ws"
            )

            # Mock connection
            mock_websocket = AsyncMock()
            manager.connection_manager.connect_to_device = AsyncMock(
                return_value=mock_websocket
            )

            # Mock system info response
            mock_system_info = {
                "device_id": device_id,
                "platform": config["platform"],
                "cpu_count": config["cpu_count"],
                "memory_total_gb": 16.0,
                "supported_features": config["features"],
            }
            manager.connection_manager.request_device_info = AsyncMock(
                return_value=mock_system_info
            )

            # Mock background services
            manager.message_processor.start_message_handler = Mock()
            manager.heartbeat_manager.start_heartbeat = Mock()
            manager.event_manager.notify_device_connected = AsyncMock()

            # Connect device
            await manager.connect_device(device_id)

        # Verify all devices have correct system info
        for config in devices_config:
            device_id = config["device_id"]
            system_info = manager.get_device_system_info(device_id)

            assert system_info is not None
            assert system_info["platform"] == config["platform"]
            assert system_info["cpu_count"] == config["cpu_count"]

            device_info = manager.get_device_info(device_id)
            for feature in config["features"]:
                assert feature in device_info.capabilities


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
