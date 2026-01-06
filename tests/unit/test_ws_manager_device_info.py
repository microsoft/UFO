"""
Unit Tests for WSManager Device Info Management

Tests the server-side device information storage and retrieval.
"""

import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi import WebSocket

from ufo.server.services.ws_manager import WSManager, ClientInfo
from aip.messages import ClientType


class TestWSManagerAgentProfile:
    """Test WSManager device info functionality"""

    def test_add_device_client_with_system_info(self):
        """Test adding a device client with system info"""
        ws_manager = WSManager()
        mock_ws = Mock(spec=WebSocket)

        system_info = {
            "device_id": "test_device",
            "platform": "windows",
            "cpu_count": 8,
            "memory_total_gb": 16.0,
        }

        metadata = {
            "system_info": system_info,
            "registration_time": datetime.now().isoformat(),
        }

        ws_manager.add_client(
            client_id="test_device",
            ws=mock_ws,
            client_type=ClientType.DEVICE,
            metadata=metadata,
        )

        # Verify client was added
        assert "test_device" in ws_manager.online_clients
        client_info = ws_manager.online_clients["test_device"]
        assert client_info.system_info is not None
        assert client_info.system_info["platform"] == "windows"
        assert client_info.system_info["cpu_count"] == 8

    def test_add_constellation_client_no_system_info(self):
        """Test that constellation clients don't get system info processing"""
        ws_manager = WSManager()
        mock_ws = Mock(spec=WebSocket)

        metadata = {
            "type": "constellation_client",
            "constellation_id": "const_001",
        }

        ws_manager.add_client(
            client_id="constellation_001",
            ws=mock_ws,
            client_type=ClientType.CONSTELLATION,
            metadata=metadata,
        )

        client_info = ws_manager.online_clients["constellation_001"]
        assert client_info.system_info is None

    def test_get_device_system_info(self):
        """Test retrieving device system info"""
        ws_manager = WSManager()
        mock_ws = Mock(spec=WebSocket)

        system_info = {
            "device_id": "device_001",
            "platform": "linux",
            "cpu_count": 4,
        }

        metadata = {"system_info": system_info}

        ws_manager.add_client(
            client_id="device_001",
            ws=mock_ws,
            client_type=ClientType.DEVICE,
            metadata=metadata,
        )

        # Retrieve system info
        retrieved_info = ws_manager.get_device_system_info("device_001")

        assert retrieved_info is not None
        assert retrieved_info["platform"] == "linux"
        assert retrieved_info["cpu_count"] == 4

    def test_get_device_system_info_not_found(self):
        """Test retrieving system info for non-existent device"""
        ws_manager = WSManager()

        retrieved_info = ws_manager.get_device_system_info("nonexistent")

        assert retrieved_info is None

    def test_get_all_devices_info(self):
        """Test retrieving all devices info"""
        ws_manager = WSManager()
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws2 = Mock(spec=WebSocket)
        mock_ws3 = Mock(spec=WebSocket)

        # Add two devices
        ws_manager.add_client(
            "device_001",
            mock_ws1,
            ClientType.DEVICE,
            {"system_info": {"platform": "windows"}},
        )
        ws_manager.add_client(
            "device_002",
            mock_ws2,
            ClientType.DEVICE,
            {"system_info": {"platform": "linux"}},
        )

        # Add a constellation (should not be included)
        ws_manager.add_client(
            "constellation_001",
            mock_ws3,
            ClientType.CONSTELLATION,
            {},
        )

        # Get all devices info
        all_info = ws_manager.get_all_devices_info()

        assert len(all_info) == 2
        assert "device_001" in all_info
        assert "device_002" in all_info
        assert "constellation_001" not in all_info
        assert all_info["device_001"]["platform"] == "windows"
        assert all_info["device_002"]["platform"] == "linux"

    def test_load_device_configs_yaml(self):
        """Test loading device configs from YAML file"""
        # Create temporary YAML config file
        yaml_content = """
devices:
  device_001:
    tags:
      - production
    tier: high_performance
    additional_features:
      - excel_macros
  device_002:
    tags:
      - development
    tier: standard
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            ws_manager = WSManager(device_config_path=temp_path)

            # Verify configs were loaded
            assert "device_001" in ws_manager._device_configs
            assert "device_002" in ws_manager._device_configs
            assert (
                ws_manager._device_configs["device_001"]["tier"] == "high_performance"
            )
            assert "production" in ws_manager._device_configs["device_001"]["tags"]
        finally:
            os.unlink(temp_path)

    def test_load_device_configs_json(self):
        """Test loading device configs from JSON file"""
        import json

        json_content = {
            "devices": {
                "device_001": {"tags": ["production"], "tier": "high_performance"}
            }
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(json_content, f)
            temp_path = f.name

        try:
            ws_manager = WSManager(device_config_path=temp_path)

            assert "device_001" in ws_manager._device_configs
            assert (
                ws_manager._device_configs["device_001"]["tier"] == "high_performance"
            )
        finally:
            os.unlink(temp_path)

    def test_merge_device_info(self):
        """Test merging system info with server config"""
        ws_manager = WSManager()

        system_info = {
            "device_id": "device_001",
            "platform": "windows",
            "cpu_count": 8,
            "supported_features": ["gui", "cli"],
            "custom_metadata": {},
        }

        server_config = {
            "tags": ["production", "office"],
            "tier": "high_performance",
            "additional_features": ["excel_macros", "power_automate"],
            "max_concurrent_tasks": 3,
        }

        merged = ws_manager._merge_device_info(system_info, server_config)

        # Check that system info is preserved
        assert merged["platform"] == "windows"
        assert merged["cpu_count"] == 8

        # Check that server config is added to custom_metadata
        assert "tags" in merged["custom_metadata"]
        assert merged["custom_metadata"]["tier"] == "high_performance"

        # Check that features are merged
        assert "gui" in merged["supported_features"]
        assert "excel_macros" in merged["supported_features"]

        # Check that tags are added
        assert merged["tags"] == ["production", "office"]

    def test_add_client_with_server_config(self):
        """Test adding client with server-side config merging"""
        # Create config file
        yaml_content = """
devices:
  device_001:
    tags:
      - production
    tier: high_performance
    additional_features:
      - excel_macros
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            ws_manager = WSManager(device_config_path=temp_path)
            mock_ws = Mock(spec=WebSocket)

            system_info = {
                "device_id": "device_001",
                "platform": "windows",
                "cpu_count": 8,
                "supported_features": ["gui", "cli"],
                "custom_metadata": {},
            }

            metadata = {"system_info": system_info}

            ws_manager.add_client(
                "device_001",
                mock_ws,
                ClientType.DEVICE,
                metadata,
            )

            # Retrieve and verify merged info
            merged_info = ws_manager.get_device_system_info("device_001")

            assert merged_info is not None
            assert merged_info["platform"] == "windows"
            assert "tags" in merged_info["custom_metadata"]
            assert merged_info["custom_metadata"]["tier"] == "high_performance"
            assert "excel_macros" in merged_info["supported_features"]

        finally:
            os.unlink(temp_path)

    def test_load_device_configs_file_not_found(self):
        """Test that missing config file is handled gracefully"""
        ws_manager = WSManager(device_config_path="nonexistent_file.yaml")

        # Should not raise exception
        assert len(ws_manager._device_configs) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
