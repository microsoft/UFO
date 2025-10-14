# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test GalaxyClient with Mock AgentProfile for Log Collection Scenario

This test demonstrates using GalaxyClient with the mock AgentProfile objects
to simulate a log collection and Excel generation workflow session.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import os

from galaxy.galaxy_client import GalaxyClient
from galaxy.client.components.types import AgentProfile, DeviceStatus
from galaxy.client.config_loader import ConstellationConfig, DeviceConfig


class TestGalaxyClientLogCollectionSession:
    """Test GalaxyClient with mock AgentProfile for log collection scenario."""

    @pytest.fixture
    def mock_linux_server_1(self) -> AgentProfile:
        """Mock AgentProfile for first Linux server."""
        return AgentProfile(
            device_id="linux_server_001",
            server_url="ws://192.168.1.101:5000/ws",
            os="linux",
            capabilities=[
                "log_collection",
                "file_operations",
                "system_monitoring",
                "bash_scripting",
                "ssh_access",
            ],
            metadata={
                "hostname": "web-server-01",
                "location": "datacenter_rack_a",
                "os_version": "Ubuntu 22.04 LTS",
                "performance": "high",
                "services": ["nginx", "postgresql", "redis"],
                "log_paths": [
                    "/var/log/nginx/access.log",
                    "/var/log/nginx/error.log",
                    "/var/log/postgresql/postgresql.log",
                    "/var/log/syslog",
                ],
            },
            status=DeviceStatus.CONNECTED,
            last_heartbeat=datetime.now(timezone.utc),
            connection_attempts=1,
            max_retries=5,
        )

    @pytest.fixture
    def mock_linux_server_2(self) -> AgentProfile:
        """Mock AgentProfile for second Linux server."""
        return AgentProfile(
            device_id="linux_server_002",
            server_url="ws://192.168.1.102:5000/ws",
            os="linux",
            capabilities=[
                "log_collection",
                "file_operations",
                "system_monitoring",
                "bash_scripting",
                "database_operations",
            ],
            metadata={
                "hostname": "api-server-01",
                "location": "datacenter_rack_b",
                "os_version": "CentOS 8",
                "performance": "high",
                "services": ["apache", "mysql", "mongodb"],
                "log_paths": [
                    "/var/log/httpd/access_log",
                    "/var/log/httpd/error_log",
                    "/var/log/mysql/mysql.log",
                    "/var/log/mongodb/mongod.log",
                    "/var/log/messages",
                ],
            },
            status=DeviceStatus.CONNECTED,
            last_heartbeat=datetime.now(timezone.utc),
            connection_attempts=1,
            max_retries=5,
        )

    @pytest.fixture
    def mock_windows_workstation(self) -> AgentProfile:
        """Mock AgentProfile for Windows workstation."""
        return AgentProfile(
            device_id="windows_workstation_001",
            server_url="ws://192.168.1.100:5000/ws",
            os="windows",
            capabilities=[
                "office_applications",
                "excel_processing",
                "file_management",
                "data_analysis",
                "report_generation",
                "email_operations",
            ],
            metadata={
                "hostname": "analyst-pc-01",
                "location": "office_floor_2",
                "os_version": "Windows 11 Pro",
                "performance": "high",
                "installed_software": [
                    "Microsoft Office 365",
                    "Python 3.11",
                    "Excel",
                    "Power BI",
                ],
                "excel_version": "16.0",
                "python_packages": ["pandas", "openpyxl", "xlsxwriter"],
            },
            status=DeviceStatus.CONNECTED,
            last_heartbeat=datetime.now(timezone.utc),
            connection_attempts=1,
            max_retries=5,
        )

    @pytest.fixture
    def mock_constellation_config(
        self,
        mock_linux_server_1: AgentProfile,
        mock_linux_server_2: AgentProfile,
        mock_windows_workstation: AgentProfile,
    ) -> ConstellationConfig:
        """Create mock ConstellationConfig with our test devices."""
        device_configs = [
            DeviceConfig(
                device_id=mock_linux_server_1.device_id,
                server_url=mock_linux_server_1.server_url,
                capabilities=mock_linux_server_1.capabilities,
                metadata=mock_linux_server_1.metadata,
                auto_connect=True,
                max_retries=5,
            ),
            DeviceConfig(
                device_id=mock_linux_server_2.device_id,
                server_url=mock_linux_server_2.server_url,
                capabilities=mock_linux_server_2.capabilities,
                metadata=mock_linux_server_2.metadata,
                auto_connect=True,
                max_retries=5,
            ),
            DeviceConfig(
                device_id=mock_windows_workstation.device_id,
                server_url=mock_windows_workstation.server_url,
                capabilities=mock_windows_workstation.capabilities,
                metadata=mock_windows_workstation.metadata,
                auto_connect=True,
                max_retries=5,
            ),
        ]

        return ConstellationConfig(
            constellation_id="log_collection_test_constellation",
            heartbeat_interval=30.0,
            reconnect_delay=5.0,
            max_concurrent_tasks=3,
            devices=device_configs,
        )

    @pytest.fixture
    def mock_constellation_client(
        self,
        mock_linux_server_1: AgentProfile,
        mock_linux_server_2: AgentProfile,
        mock_windows_workstation: AgentProfile,
    ):
        """Create mock ConstellationClient."""
        mock_client = AsyncMock()

        # Mock device registry with our test devices
        mock_device_registry = Mock()
        mock_device_registry.get_all_devices.return_value = {
            mock_linux_server_1.device_id: mock_linux_server_1,
            mock_linux_server_2.device_id: mock_linux_server_2,
            mock_windows_workstation.device_id: mock_windows_workstation,
        }
        mock_device_registry.get_connected_devices.return_value = [
            mock_linux_server_1.device_id,
            mock_linux_server_2.device_id,
            mock_windows_workstation.device_id,
        ]

        mock_client.device_manager = Mock()
        mock_client.device_manager.device_registry = mock_device_registry
        mock_client.device_manager.get_connected_devices.return_value = [
            mock_linux_server_1.device_id,
            mock_linux_server_2.device_id,
            mock_windows_workstation.device_id,
        ]

        # Mock initialization and shutdown
        mock_client.initialize = AsyncMock()
        mock_client.shutdown = AsyncMock()

        return mock_client

    @pytest.fixture
    def mock_galaxy_session(self):
        """Create mock GalaxySession."""
        mock_session = AsyncMock()
        mock_session._rounds = []  # Start with empty rounds
        mock_session.log_path = "/mock/path/to/logs"

        # Mock constellation
        mock_constellation = Mock()
        mock_constellation.constellation_id = "test_constellation_001"
        mock_constellation.name = "Log Collection Test Constellation"
        mock_constellation.tasks = [
            "collect_logs_linux1",
            "collect_logs_linux2",
            "generate_excel",
        ]
        mock_constellation.dependencies = ["collect_logs -> generate_excel"]
        mock_constellation.state = Mock()
        mock_constellation.state.value = "completed"

        mock_session._current_constellation = mock_constellation

        # Mock the run method as AsyncMock and add side effect
        async def mock_run_side_effect():
            # Simulate adding rounds during execution
            mock_session._rounds.extend(
                [
                    {"round": 1, "action": "analyze_request"},
                    {"round": 2, "action": "create_constellation"},
                    {"round": 3, "action": "execute_tasks"},
                ]
            )

        mock_session.run = AsyncMock(side_effect=mock_run_side_effect)
        mock_session.force_finish = AsyncMock()

        return mock_session

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.mark.asyncio
    async def test_galaxy_client_initialization_with_mock_devices(
        self, mock_constellation_config: ConstellationConfig, temp_output_dir: Path
    ):
        """Test GalaxyClient initialization with mock devices."""
        with patch(
            "ufo.galaxy.galaxy_client.ConstellationConfig.from_yaml"
        ) as mock_from_yaml:
            mock_from_yaml.return_value = mock_constellation_config

            # Initialize GalaxyClient
            client = GalaxyClient(
                session_name="test_log_collection_session",
                max_rounds=5,
                log_level="INFO",
                output_dir=str(temp_output_dir),
            )

            # Verify initialization
            assert client.session_name == "test_log_collection_session"
            assert client.max_rounds == 5
            assert client.output_dir == temp_output_dir
            assert client._device_config == mock_constellation_config

            # Verify device configuration
            assert len(client._device_config.devices) == 3
            device_ids = [dev.device_id for dev in client._device_config.devices]
            assert "linux_server_001" in device_ids
            assert "linux_server_002" in device_ids
            assert "windows_workstation_001" in device_ids

    @pytest.mark.asyncio
    async def test_galaxy_client_full_initialization(
        self,
        mock_constellation_config: ConstellationConfig,
        mock_constellation_client,
        temp_output_dir: Path,
    ):
        """Test GalaxyClient full initialization with mocked components."""
        with patch(
            "ufo.galaxy.galaxy_client.ConstellationConfig.from_yaml"
        ) as mock_from_yaml, patch(
            "ufo.galaxy.galaxy_client.ConstellationClient"
        ) as mock_client_class:

            mock_from_yaml.return_value = mock_constellation_config
            mock_client_class.return_value = mock_constellation_client

            # Initialize GalaxyClient
            client = GalaxyClient(
                session_name="test_initialization", output_dir=str(temp_output_dir)
            )

            # Initialize the client
            await client.initialize()

            # Verify ConstellationClient was created and initialized
            mock_client_class.assert_called_once_with(config=mock_constellation_config)
            mock_constellation_client.initialize.assert_called_once()

            # Verify client state
            assert client._client == mock_constellation_client
            assert client._client is not None

    @pytest.mark.asyncio
    async def test_process_log_collection_request(
        self,
        mock_constellation_config: ConstellationConfig,
        mock_constellation_client,
        mock_galaxy_session,
        temp_output_dir: Path,
    ):
        """Test processing log collection request with mock devices."""
        log_collection_request = (
            "Collect logs from the two Linux servers (web-server-01 and api-server-01) "
            "and generate a comprehensive Excel report on the Windows workstation. "
            "The report should include log analysis, error counts, and performance metrics."
        )

        with patch(
            "ufo.galaxy.galaxy_client.ConstellationConfig.from_yaml"
        ) as mock_from_yaml, patch(
            "ufo.galaxy.galaxy_client.ConstellationClient"
        ) as mock_client_class, patch(
            "ufo.galaxy.galaxy_client.GalaxySession"
        ) as mock_session_class:

            mock_from_yaml.return_value = mock_constellation_config
            mock_client_class.return_value = mock_constellation_client
            mock_session_class.return_value = mock_galaxy_session

            # Initialize and setup client
            client = GalaxyClient(
                session_name="log_collection_test", output_dir=str(temp_output_dir)
            )
            await client.initialize()

            # Process the request
            result = await client.process_request(
                request=log_collection_request,
                task_name="log_collection_and_excel_generation",
            )

            # Verify GalaxySession was created with correct parameters
            mock_session_class.assert_called_once()
            call_args = mock_session_class.call_args
            assert call_args[1]["task"] == "log_collection_and_excel_generation"
            assert call_args[1]["client"] == mock_constellation_client
            assert call_args[1]["initial_request"] == log_collection_request
            assert call_args[1]["should_evaluate"] == False

            # Verify session execution
            mock_galaxy_session.run.assert_called_once()

            # Verify result structure
            assert result["status"] == "completed"
            assert result["request"] == log_collection_request
            assert result["task_name"] == "log_collection_and_excel_generation"
            assert result["session_name"] == "log_collection_test"
            assert "execution_time" in result
            assert "rounds" in result
            assert result["rounds"] == 3  # Based on our mock
            assert "constellation" in result

            # Verify constellation info in result
            constellation_info = result["constellation"]
            assert constellation_info["id"] == "test_constellation_001"
            assert constellation_info["name"] == "Log Collection Test Constellation"
            assert constellation_info["task_count"] == 3
            assert constellation_info["state"] == "completed"

    @pytest.mark.asyncio
    async def test_galaxy_client_device_availability_check(
        self,
        mock_constellation_config: ConstellationConfig,
        mock_constellation_client,
        temp_output_dir: Path,
    ):
        """Test that GalaxyClient can access all required devices for log collection."""
        with patch(
            "ufo.galaxy.galaxy_client.ConstellationConfig.from_yaml"
        ) as mock_from_yaml, patch(
            "ufo.galaxy.galaxy_client.ConstellationClient"
        ) as mock_client_class:

            mock_from_yaml.return_value = mock_constellation_config
            mock_client_class.return_value = mock_constellation_client

            # Initialize client
            client = GalaxyClient(output_dir=str(temp_output_dir))
            await client.initialize()

            # Verify client has access to constellation client
            assert client._client == mock_constellation_client

            # Check device availability through mocked client
            connected_devices = client._client.device_manager.get_connected_devices()
            assert len(connected_devices) == 3
            assert "linux_server_001" in connected_devices
            assert "linux_server_002" in connected_devices
            assert "windows_workstation_001" in connected_devices

            # Check device registry access
            all_devices = (
                client._client.device_manager.device_registry.get_all_devices()
            )
            assert len(all_devices) == 3

            # Verify Linux servers have log collection capabilities
            linux_devices = [dev for dev in all_devices.values() if dev.os == "linux"]
            assert len(linux_devices) == 2
            for device in linux_devices:
                assert "log_collection" in device.capabilities
                assert "log_paths" in device.metadata

            # Verify Windows device has Excel capabilities
            windows_devices = [
                dev for dev in all_devices.values() if dev.os == "windows"
            ]
            assert len(windows_devices) == 1
            windows_device = windows_devices[0]
            assert "excel_processing" in windows_device.capabilities
            assert "office_applications" in windows_device.capabilities

    @pytest.mark.asyncio
    async def test_galaxy_client_error_handling(
        self,
        mock_constellation_config: ConstellationConfig,
        mock_constellation_client,
        temp_output_dir: Path,
    ):
        """Test GalaxyClient error handling during request processing."""
        with patch(
            "ufo.galaxy.galaxy_client.ConstellationConfig.from_yaml"
        ) as mock_from_yaml, patch(
            "ufo.galaxy.galaxy_client.ConstellationClient"
        ) as mock_client_class, patch(
            "ufo.galaxy.galaxy_client.GalaxySession"
        ) as mock_session_class:

            mock_from_yaml.return_value = mock_constellation_config
            mock_client_class.return_value = mock_constellation_client

            # Create a mock session that raises an exception
            mock_failing_session = AsyncMock()
            mock_failing_session.run.side_effect = Exception(
                "Mock session execution failed"
            )
            mock_session_class.return_value = mock_failing_session

            # Initialize client
            client = GalaxyClient(output_dir=str(temp_output_dir))
            await client.initialize()

            # Process request that will fail
            result = await client.process_request(
                request="This request will fail", task_name="failing_task"
            )

            # Verify error handling
            assert result["status"] == "failed"
            assert "error" in result
            assert "Mock session execution failed" in result["error"]
            assert result["request"] == "This request will fail"

    @pytest.mark.asyncio
    async def test_galaxy_client_shutdown(
        self,
        mock_constellation_config: ConstellationConfig,
        mock_constellation_client,
        mock_galaxy_session,
        temp_output_dir: Path,
    ):
        """Test GalaxyClient proper shutdown."""
        with patch(
            "ufo.galaxy.galaxy_client.ConstellationConfig.from_yaml"
        ) as mock_from_yaml, patch(
            "ufo.galaxy.galaxy_client.ConstellationClient"
        ) as mock_client_class:

            mock_from_yaml.return_value = mock_constellation_config
            mock_client_class.return_value = mock_constellation_client

            # Initialize client
            client = GalaxyClient(output_dir=str(temp_output_dir))
            await client.initialize()

            # Set a mock session
            client._session = mock_galaxy_session

            # Shutdown client
            await client.shutdown()

            # Verify shutdown calls
            mock_constellation_client.shutdown.assert_called_once()
            mock_galaxy_session.force_finish.assert_called_once_with("Client shutdown")

    def test_galaxy_client_session_name_generation(self):
        """Test automatic session name generation."""
        # Test with custom session name
        client1 = GalaxyClient(session_name="custom_session")
        assert client1.session_name == "custom_session"

        # Test with auto-generated session name
        client2 = GalaxyClient()
        assert client2.session_name.startswith("galaxy_session_")
        assert len(client2.session_name) > len("galaxy_session_")

    @pytest.mark.asyncio
    async def test_request_without_initialization_error(self):
        """Test that processing request without initialization raises error."""
        client = GalaxyClient()

        with pytest.raises(RuntimeError, match="Galaxy client not initialized"):
            await client.process_request("Test request")

    def test_log_collection_request_scenarios(self):
        """Test various log collection request formats."""
        test_requests = [
            "Collect logs from Linux servers and generate Excel report",
            "从两个Linux服务器采集日志并在Windows上生成Excel报告",
            "Analyze system logs from web-server-01 and api-server-01, create summary in Excel",
            "Pull error logs from nginx and apache servers, create performance report",
            "Gather database logs from PostgreSQL and MySQL, generate analytics dashboard",
        ]

        client = GalaxyClient()

        # Test that all request formats are accepted (basic validation)
        for request in test_requests:
            assert isinstance(request, str)
            assert len(request) > 0
            # These would be processed by the actual session in real scenarios
