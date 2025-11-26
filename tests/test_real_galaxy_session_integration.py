# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Real GalaxySession Integration Test with Mock AgentProfile

This test uses REAL GalaxySession.run() (not mocked) to test the complete
agent workflow and identify potential bugs in the system.
"""

import pytest
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch

from galaxy.galaxy_client import GalaxyClient
from galaxy.session.galaxy_session import GalaxySession
from galaxy.client.components.types import AgentProfile, DeviceStatus
from galaxy.client.config_loader import ConstellationConfig, DeviceConfig
from galaxy.client.constellation_client import ConstellationClient
from galaxy.core.types import ExecutionResult, TaskStatus


class TestRealGalaxySessionWithMockDevices:
    """Test real GalaxySession execution with mock AgentProfile to find bugs."""

    class NoComputerRunActionFilter(logging.Filter):
        """Filter to exclude Computer._run_action logs."""

        def filter(self, record):
            # Filter out Computer logger's _run_action messages
            if record.name == "Computer" and record.funcName == "_run_action":
                return False
            # Also filter out any ufo.agents.agent.basic logs which might be noisy
            if "ufo.agents" in record.name and record.funcName == "_run_action":
                return False
            return True

    def _setup_comprehensive_logging(self):
        """Setup comprehensive logging for all galaxy components."""
        # Set root logger to info
        root_logger = logging.getLogger()
        original_level = root_logger.level
        root_logger.setLevel(logging.INFO)

        # Create detailed console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Add filter to exclude Computer._run_action logs
        log_filter = self.NoComputerRunActionFilter()
        console_handler.addFilter(log_filter)

        # Use detailed formatter
        detailed_formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler.setFormatter(detailed_formatter)

        # Configure all relevant loggers
        loggers_to_configure = [
            "ufo.galaxy.session",
            "ufo.galaxy.agents",
            "ufo.galaxy.constellation",
            "ufo.galaxy.client",
            "ufo.galaxy.core",
            "galaxy.session",
            "galaxy.agents",
            "galaxy.constellation",
            "galaxy.client",
            "galaxy.core",
            "",
        ]

        configured_loggers = []
        for logger_name in loggers_to_configure:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)
            # Clear existing handlers to avoid duplicate logging
            logger.handlers.clear()
            logger.addHandler(console_handler)
            logger.propagate = False
            configured_loggers.append(logger)

        return console_handler, configured_loggers, original_level

    def _cleanup_logging(self, console_handler, configured_loggers, original_level):
        """Clean up logging configuration."""
        for logger in configured_loggers:
            logger.removeHandler(console_handler)
        logging.getLogger().setLevel(original_level)

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
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_constellation_client(
        self,
        mock_linux_server_1: AgentProfile,
        mock_linux_server_2: AgentProfile,
        mock_windows_workstation: AgentProfile,
    ):
        """Create real ConstellationClient with mocked device manager."""
        # Create a real ConstellationClient but mock its device manager
        mock_client = Mock(spec=ConstellationClient)

        # Mock device registry with our test devices
        mock_device_registry = Mock()
        device_dict = {
            mock_linux_server_1.device_id: mock_linux_server_1,
            mock_linux_server_2.device_id: mock_linux_server_2,
            mock_windows_workstation.device_id: mock_windows_workstation,
        }

        mock_device_registry.get_all_devices.return_value = device_dict
        mock_device_registry.get_connected_devices.return_value = [
            mock_linux_server_1.device_id,
            mock_linux_server_2.device_id,
            mock_windows_workstation.device_id,
        ]
        mock_device_registry.get_device.side_effect = lambda device_id: device_dict.get(
            device_id
        )

        # Mock device manager
        mock_device_manager = Mock()
        mock_device_manager.device_registry = mock_device_registry
        mock_device_manager.get_connected_devices.return_value = [
            mock_linux_server_1.device_id,
            mock_linux_server_2.device_id,
            mock_windows_workstation.device_id,
        ]

        # Fix the get_all_devices method to return proper format for context
        def mock_get_all_devices(connected=False):
            devices = {
                mock_linux_server_1.device_id: mock_linux_server_1,
                mock_linux_server_2.device_id: mock_linux_server_2,
                mock_windows_workstation.device_id: mock_windows_workstation,
            }
            if connected:
                return {
                    k: v
                    for k, v in devices.items()
                    if v.status == DeviceStatus.CONNECTED
                }
            return devices

        mock_device_manager.get_all_devices = Mock(side_effect=mock_get_all_devices)

        # Mock task execution - this is where real device communication would happen
        async def mock_assign_task_to_device(
            task_id: str,
            device_id: str,
            task_description: str,
            task_data: dict,
            timeout: float = 300.0,
        ):
            """Mock task assignment with realistic responses."""
            device = device_dict.get(device_id)
            if not device:
                raise ValueError(f"Device {device_id} not found")

            start_time = datetime.now(timezone.utc)

            # Simulate different responses based on device type and task description
            if device.os == "linux" and "log_collection" in task_description.lower():
                return ExecutionResult(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED.value,
                    result={
                        "logs_collected": len(device.metadata.get("log_paths", [])),
                        "total_size_mb": 25.6,
                        "files_processed": device.metadata.get("log_paths", []),
                        "execution_time": 12.3,
                    },
                    start_time=start_time,
                    end_time=datetime.now(timezone.utc),
                    metadata={"device_id": device_id, "device_os": device.os},
                )
            elif device.os == "windows" and "excel" in task_description.lower():
                return ExecutionResult(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED.value,
                    result={
                        "report_generated": True,
                        "file_path": "C:\\Reports\\log_analysis_report.xlsx",
                        "sheets_created": 3,
                        "charts_generated": 5,
                        "execution_time": 8.7,
                    },
                    start_time=start_time,
                    end_time=datetime.now(timezone.utc),
                    metadata={"device_id": device_id, "device_os": device.os},
                )
            else:
                return ExecutionResult(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED.value,
                    result={
                        "message": f"Task {task_description} completed on {device_id}"
                    },
                    start_time=start_time,
                    end_time=datetime.now(timezone.utc),
                    metadata={"device_id": device_id, "device_os": device.os},
                )

        mock_device_manager.assign_task_to_device = AsyncMock(
            side_effect=mock_assign_task_to_device
        )

        mock_client.device_manager = mock_device_manager
        mock_client.get_constellation_info.return_value = {
            "constellation_id": "test_constellation",
            "connected_devices": 3,
            "total_devices": 3,
        }

        return mock_client

    @pytest.mark.asyncio
    async def test_real_galaxy_session_execution_with_mock_devices(
        self,
        mock_constellation_client,
        mock_linux_server_1: AgentProfile,
        mock_linux_server_2: AgentProfile,
        mock_windows_workstation: AgentProfile,
        temp_output_dir: Path,
    ):
        """Test real GalaxySession.run() with mock devices to identify bugs."""

        print("\n🔍 Starting REAL GalaxySession execution test...")

        # Real log collection request
        log_collection_request = (
            "I need to collect logs from two Linux servers and create an Excel report. "
            f"First, collect logs from {mock_linux_server_1.metadata['hostname']} "
            f"(device: {mock_linux_server_1.device_id}) including nginx, postgresql, and system logs. "
            f"Second, collect logs from {mock_linux_server_2.metadata['hostname']} "
            f"(device: {mock_linux_server_2.device_id}) including apache, mysql, and mongodb logs. "
            f"Finally, use the Windows workstation {mock_windows_workstation.metadata['hostname']} "
            f"(device: {mock_windows_workstation.device_id}) to create a comprehensive Excel report "
            "with log analysis, error statistics, and performance charts."
        )

        print(f"📝 Request: {log_collection_request[:100]}...")

        # Create real GalaxySession (not mocked)
        session = GalaxySession(
            task="real_log_collection_test",
            should_evaluate=False,
            id="real_test_session_001",
            client=mock_constellation_client,
            initial_request=log_collection_request,
        )

        print("🚀 Created real GalaxySession instance")
        print(f"   Session ID: {session._id}")
        print(f"   Task: {session.task}")
        print(f"   Client: {type(session._client)}")

        # Configure comprehensive logging to capture ALL logs
        console_handler, configured_loggers, original_level = (
            self._setup_comprehensive_logging()
        )
        print(f"📋 Configured {len(configured_loggers)} loggers for detailed output")

        try:
            print("\n🎬 Starting real session execution...")
            print("=" * 60)

            # This is the REAL session.run() - no mocking!
            start_time = datetime.now()
            await session.run()
            end_time = datetime.now()

            execution_time = (end_time - start_time).total_seconds()
            print("=" * 60)
            print(f"✅ Session completed in {execution_time:.2f} seconds")

        except Exception as e:
            print(f"❌ Session execution failed: {e}")
            print(f"Exception type: {type(e).__name__}")
            import traceback

            traceback.print_exc()

            # Still collect what we can for analysis
            print("\n🔍 Session state at failure:")
            print(f"   Rounds completed: {len(getattr(session, '_rounds', []))}")
            print(
                f"   Current constellation: {getattr(session, '_current_constellation', None)}"
            )

            # Re-raise to mark test as failed but with detailed info
            raise

        finally:
            # Clean up all configured loggers to avoid duplicate logs in subsequent tests
            print(f"\n🧹 Cleaning up {len(configured_loggers)} loggers")
            self._cleanup_logging(console_handler, configured_loggers, original_level)

        # Analyze session results
        print("\n📊 Session Analysis:")
        print(f"   Total rounds: {len(getattr(session, '_rounds', []))}")
        print(f"   Session state: {getattr(session, 'state', 'unknown')}")

        # Check if constellation was created
        constellation = getattr(session, "_current_constellation", None)
        if constellation:
            print(f"   Constellation created: ✅")
            print(
                f"   Constellation ID: {getattr(constellation, 'constellation_id', 'unknown')}"
            )
            print(f"   Task count: {len(getattr(constellation, 'tasks', []))}")
            print(
                f"   Dependency count: {len(getattr(constellation, 'dependencies', []))}"
            )
        else:
            print(f"   Constellation created: ❌")

        # Check rounds for issues
        rounds = getattr(session, "_rounds", [])
        if rounds:
            print(f"\n🔄 Round Details:")
            for i, round_info in enumerate(rounds, 1):
                round_type = (
                    type(round_info).__name__
                    if hasattr(round_info, "__class__")
                    else str(type(round_info))
                )
                print(f"   Round {i}: {round_type}")

                # Check for errors in round
                if hasattr(round_info, "error") and round_info.error:
                    print(f"     ❌ Error: {round_info.error}")
                if hasattr(round_info, "status"):
                    print(f"     📊 Status: {round_info.status}")

        # Verify device interactions
        print(f"\n🔧 Device Interaction Analysis:")
        assign_task_calls = (
            mock_constellation_client.device_manager.assign_task_to_device.call_count
        )
        print(f"   Total device task executions: {assign_task_calls}")

        if assign_task_calls > 0:
            print(f"   Device tasks executed: ✅")
            # Analyze call arguments
            for (
                call
            ) in (
                mock_constellation_client.device_manager.assign_task_to_device.call_args_list
            ):
                args, kwargs = call
                device_id = (
                    args[1] if len(args) > 1 else kwargs.get("device_id", "unknown")
                )
                task_description = (
                    args[2]
                    if len(args) > 2
                    else kwargs.get("task_description", "unknown")
                )
                print(f"     • {device_id}: {task_description}")
        else:
            print(f"   Device tasks executed: ❌ (No device interactions detected)")

        # Check for common issues
        print(f"\n🐛 Bug Detection:")

        issues_found = []

        # Check 1: Session completed successfully
        if not hasattr(session, "_rounds") or len(session._rounds) == 0:
            issues_found.append("No rounds were executed")

        # Check 2: Constellation was created
        if not constellation:
            issues_found.append("No constellation was created")

        # Check 3: Device tasks were executed
        if assign_task_calls == 0:
            issues_found.append("No device tasks were executed")

        # Check 4: All expected devices were used
        device_calls = set()
        for (
            call
        ) in (
            mock_constellation_client.device_manager.assign_task_to_device.call_args_list
        ):
            args, kwargs = call
            device_id = args[1] if len(args) > 1 else kwargs.get("device_id")
            if device_id:
                device_calls.add(device_id)

        expected_devices = {
            mock_linux_server_1.device_id,
            mock_linux_server_2.device_id,
            mock_windows_workstation.device_id,
        }

        unused_devices = expected_devices - device_calls
        if unused_devices:
            issues_found.append(f"Unused devices: {unused_devices}")

        # Report results
        if issues_found:
            print(f"   ❌ Issues detected:")
            for issue in issues_found:
                print(f"     • {issue}")
        else:
            print(f"   ✅ No obvious issues detected")

        # Performance analysis
        print(f"\n⚡ Performance Analysis:")
        print(f"   Execution time: {execution_time:.2f}s")
        if execution_time > 30:
            print(f"   ⚠️  Slow execution (>30s)")
        elif execution_time > 10:
            print(f"   ⚠️  Moderate execution time (>10s)")
        else:
            print(f"   ✅ Fast execution (<10s)")

        print(f"\n🎯 Test Summary:")
        print(f"   Real session execution: ✅ Completed")
        print(f"   Issues found: {len(issues_found)}")
        print(f"   Device interactions: {assign_task_calls}")
        print(f"   Execution time: {execution_time:.2f}s")

        # Assert basic success criteria
        assert (
            len(getattr(session, "_rounds", [])) > 0
        ), "Session should have executed at least one round"

        return {
            "success": True,
            "execution_time": execution_time,
            "rounds": len(getattr(session, "_rounds", [])),
            "constellation_created": constellation is not None,
            "device_interactions": assign_task_calls,
            "issues": issues_found,
        }

    @pytest.mark.asyncio
    async def test_session_with_different_request_types(
        self,
        mock_constellation_client,
        mock_linux_server_1: AgentProfile,
        mock_windows_workstation: AgentProfile,
        temp_output_dir: Path,
    ):
        """Test different types of requests to find parsing/handling bugs."""

        # Setup logging for this test too
        console_handler, configured_loggers, original_level = (
            self._setup_comprehensive_logging()
        )

        test_requests = [
            # Simple request
            "Collect logs from linux_server_001 and create Excel report on windows_workstation_001",
            # Complex multi-step request
            "First collect nginx logs from web-server-01, then analyze errors, then create detailed Excel charts with performance metrics on the Windows analyst workstation",
            # Chinese request
            "从linux服务器收集日志并在Windows工作站生成Excel报告",
            # Technical request with specific paths
            "Execute 'tail -n 1000 /var/log/nginx/error.log' on linux_server_001 and save results to Excel file using openpyxl on windows_workstation_001",
        ]

        results = []

        try:
            for i, request in enumerate(test_requests, 1):
                print(f"\n🧪 Test {i}/{len(test_requests)}: {request[:50]}...")

                session = GalaxySession(
                    task=f"test_request_{i}",
                    should_evaluate=False,
                    id=f"test_session_{i:03d}",
                    client=mock_constellation_client,
                    initial_request=request,
                )

                try:
                    await session.run()

                    result = {
                        "request": request[:100],
                        "success": True,
                        "rounds": len(getattr(session, "_rounds", [])),
                        "error": None,
                    }
                    print(f"   ✅ Success: {result['rounds']} rounds")

                except Exception as e:
                    result = {
                        "request": request[:100],
                        "success": False,
                        "rounds": len(getattr(session, "_rounds", [])),
                        "error": str(e),
                    }
                    print(f"   ❌ Failed: {e}")

                results.append(result)

            # Analyze results
            print(f"\n📈 Request Type Analysis:")
            success_count = sum(1 for r in results if r["success"])
            print(
                f"   Success rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)"
            )

            for i, result in enumerate(results, 1):
                status = "✅" if result["success"] else "❌"
                print(
                    f"   {i}. {status} {result['request']} (rounds: {result['rounds']})"
                )
                if not result["success"]:
                    print(f"      Error: {result['error']}")

        finally:
            # Clean up logging configuration
            self._cleanup_logging(console_handler, configured_loggers, original_level)

        return results

    @pytest.mark.asyncio
    async def test_session_error_handling(
        self, mock_constellation_client, temp_output_dir: Path
    ):
        """Test session error handling with problematic scenarios."""

        # Setup logging for this test too
        console_handler, configured_loggers, original_level = (
            self._setup_comprehensive_logging()
        )

        try:
            # Make device manager fail for specific tasks
            original_assign_task = (
                mock_constellation_client.device_manager.assign_task_to_device
            )

            async def failing_assign_task(
                task_id: str,
                device_id: str,
                task_description: str,
                task_data: dict,
                timeout: float = 300.0,
            ):
                if "fail_test" in task_description.lower():
                    error = ConnectionError(f"Mock connection failure to {device_id}")
                    return ExecutionResult(
                        task_id=task_id,
                        status=TaskStatus.FAILED.value,
                        error=str(error),
                        start_time=datetime.now(timezone.utc),
                        end_time=datetime.now(timezone.utc),
                        metadata={"device_id": device_id},
                    )
                return await original_assign_task(
                    task_id, device_id, task_description, task_data, timeout
                )

            mock_constellation_client.device_manager.assign_task_to_device = AsyncMock(
                side_effect=failing_assign_task
            )

            error_request = (
                "Execute a fail_test task on any device to test error handling"
            )

            session = GalaxySession(
                task="error_handling_test",
                should_evaluate=False,
                id="error_test_session",
                client=mock_constellation_client,
                initial_request=error_request,
            )

            print(f"\n🚨 Testing error handling with failing task...")

            try:
                await session.run()
                print(
                    f"   ⚠️  Session completed despite errors (error recovery working)"
                )

            except Exception as e:
                print(f"   ❌ Session failed with error: {e}")
                print(f"   Error type: {type(e).__name__}")

            # Check if session handled errors gracefully
            rounds = getattr(session, "_rounds", [])
            print(f"   Rounds completed before/during error: {len(rounds)}")

            # Restore original method
            mock_constellation_client.device_manager.assign_task_to_device = (
                original_assign_task
            )

        finally:
            # Clean up logging configuration
            self._cleanup_logging(console_handler, configured_loggers, original_level)
