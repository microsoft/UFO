"""
Unit Tests for Device Info Provider

Tests the device information collection functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ufo.client.device_info_provider import DeviceInfoProvider, DeviceSystemInfo


class TestDeviceSystemInfo:
    """Test DeviceSystemInfo dataclass"""

    def test_device_system_info_creation(self):
        """Test creating DeviceSystemInfo instance"""
        info = DeviceSystemInfo(
            device_id="test_device",
            platform="windows",
            os_version="10.0.19041",
            cpu_count=8,
            memory_total_gb=16.0,
            hostname="test-pc",
            ip_address="192.168.1.100",
            supported_features=["gui", "cli"],
            platform_type="computer",
        )

        assert info.device_id == "test_device"
        assert info.platform == "windows"
        assert info.cpu_count == 8
        assert info.memory_total_gb == 16.0
        assert info.schema_version == "1.0"

    def test_to_dict(self):
        """Test converting DeviceSystemInfo to dictionary"""
        info = DeviceSystemInfo(
            device_id="test_device",
            platform="linux",
            os_version="5.10.0",
            cpu_count=4,
            memory_total_gb=8.0,
            hostname="linux-box",
            ip_address="10.0.0.1",
        )

        result = info.to_dict()

        assert isinstance(result, dict)
        assert result["device_id"] == "test_device"
        assert result["platform"] == "linux"
        assert result["schema_version"] == "1.0"


class TestDeviceInfoProvider:
    """Test DeviceInfoProvider class"""

    @patch("platform.system")
    @patch("platform.version")
    @patch("os.cpu_count")
    @patch("psutil.virtual_memory")
    @patch("socket.gethostname")
    @patch("socket.socket")
    def test_collect_system_info_success(
        self,
        mock_socket_class,
        mock_hostname,
        mock_memory,
        mock_cpu_count,
        mock_version,
        mock_system,
    ):
        """Test successful system info collection"""
        # Setup mocks
        mock_system.return_value = "Windows"
        mock_version.return_value = "10.0.19041"
        mock_cpu_count.return_value = 8

        mock_mem = Mock()
        mock_mem.total = 17179869184  # 16 GB in bytes
        mock_memory.return_value = mock_mem

        mock_hostname.return_value = "test-pc"

        # Mock socket for IP address
        mock_sock = Mock()
        mock_sock.getsockname.return_value = ("192.168.1.100", 0)
        mock_socket_class.return_value = mock_sock

        # Collect info
        info = DeviceInfoProvider.collect_system_info("test_device_001")

        # Assertions
        assert info.device_id == "test_device_001"
        assert info.platform == "windows"
        assert info.os_version == "10.0.19041"
        assert info.cpu_count == 8
        assert info.memory_total_gb == 16.0
        assert info.hostname == "test-pc"
        assert info.ip_address == "192.168.1.100"
        assert info.platform_type == "computer"
        assert "gui" in info.supported_features
        assert "cli" in info.supported_features

    @patch("platform.system")
    @patch("platform.version")
    @patch("os.cpu_count")
    def test_collect_system_info_with_custom_metadata(
        self,
        mock_cpu_count,
        mock_version,
        mock_system,
    ):
        """Test system info collection with custom metadata"""
        mock_system.return_value = "Linux"
        mock_version.return_value = "5.10.0"
        mock_cpu_count.return_value = 4

        custom_metadata = {
            "tags": ["production", "backend"],
            "tier": "high_performance",
        }

        info = DeviceInfoProvider.collect_system_info(
            "linux_server_001", custom_metadata=custom_metadata
        )

        assert info.custom_metadata == custom_metadata
        assert info.custom_metadata["tier"] == "high_performance"

    @patch("platform.system", side_effect=Exception("Platform error"))
    def test_collect_system_info_handles_errors(self, mock_system):
        """Test that errors are handled gracefully"""
        info = DeviceInfoProvider.collect_system_info("error_device")

        # Should return minimal info on error
        assert info.device_id == "error_device"
        assert info.platform == "unknown"
        assert info.cpu_count == 0
        assert info.memory_total_gb == 0.0

    @patch("platform.system")
    def test_detect_features_windows(self, mock_system):
        """Test feature detection for Windows"""
        mock_system.return_value = "Windows"

        features = DeviceInfoProvider._detect_features()

        assert "gui" in features
        assert "cli" in features
        assert "browser" in features
        assert "windows_apps" in features

    @patch("platform.system")
    def test_detect_features_linux(self, mock_system):
        """Test feature detection for Linux"""
        mock_system.return_value = "Linux"

        features = DeviceInfoProvider._detect_features()

        assert "gui" in features
        assert "cli" in features
        assert "linux_apps" in features

    @patch("platform.system")
    def test_detect_features_macos(self, mock_system):
        """Test feature detection for macOS"""
        mock_system.return_value = "Darwin"

        features = DeviceInfoProvider._detect_features()

        assert "gui" in features
        assert "macos_apps" in features

    @patch("platform.system")
    def test_get_platform_type_computer(self, mock_system):
        """Test platform type detection for computers"""
        mock_system.return_value = "Windows"
        assert DeviceInfoProvider._get_platform_type() == "computer"

        mock_system.return_value = "Linux"
        assert DeviceInfoProvider._get_platform_type() == "computer"

        mock_system.return_value = "Darwin"
        assert DeviceInfoProvider._get_platform_type() == "computer"

    def test_load_server_configured_metadata_no_file(self):
        """Test loading metadata when file doesn't exist"""
        metadata = DeviceInfoProvider.load_server_configured_metadata(
            "nonexistent_file.yaml"
        )

        assert metadata == {}

    @patch("builtins.open", create=True)
    @patch("os.path.exists")
    def test_load_server_configured_metadata_yaml(self, mock_exists, mock_open):
        """Test loading metadata from YAML file"""
        mock_exists.return_value = True

        yaml_content = """
device_metadata:
  tags:
    - production
  tier: high_performance
"""
        mock_open.return_value.__enter__.return_value.read.return_value = yaml_content

        with patch("yaml.safe_load") as mock_yaml:
            mock_yaml.return_value = {
                "device_metadata": {"tags": ["production"], "tier": "high_performance"}
            }

            metadata = DeviceInfoProvider.load_server_configured_metadata("config.yaml")

            assert metadata["tier"] == "high_performance"
            assert "production" in metadata["tags"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
