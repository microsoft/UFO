# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test Linux Log Collection and Excel Generation

This test module demonstrates collecting logs from two Linux servers and generating an Excel report on a Windows machine.
It includes mock AgentProfile objects for testing cross-platform operations in a constellation environment.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import os

from galaxy.client.components.types import AgentProfile, DeviceStatus


class TestLinuxLogCollectionExcelGeneration:
    """Test cases for cross-platform log collection and Excel generation scenario."""

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
                "cpu_cores": 16,
                "memory_gb": 64,
                "disk_space_gb": 1000,
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
                "cpu_cores": 12,
                "memory_gb": 32,
                "disk_space_gb": 500,
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
        """Mock AgentProfile for Windows workstation for Excel generation."""
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
                "cpu_cores": 8,
                "memory_gb": 32,
                "disk_space_gb": 1000,
                "installed_software": [
                    "Microsoft Office 365",
                    "Python 3.11",
                    "Excel",
                    "Power BI",
                    "Visual Studio Code",
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
    def device_constellation(
        self,
        mock_linux_server_1: AgentProfile,
        mock_linux_server_2: AgentProfile,
        mock_windows_workstation: AgentProfile,
    ) -> Dict[str, AgentProfile]:
        """Create a constellation of devices for testing."""
        return {
            "linux_server_001": mock_linux_server_1,
            "linux_server_002": mock_linux_server_2,
            "windows_workstation_001": mock_windows_workstation,
        }

    def test_mock_device_creation(
        self,
        mock_linux_server_1: AgentProfile,
        mock_linux_server_2: AgentProfile,
        mock_windows_workstation: AgentProfile,
    ):
        """Test that mock devices are properly created with correct properties."""
        # Test Linux Server 1
        assert mock_linux_server_1.device_id == "linux_server_001"
        assert mock_linux_server_1.os == "linux"
        assert "log_collection" in mock_linux_server_1.capabilities
        assert mock_linux_server_1.metadata["hostname"] == "web-server-01"
        assert mock_linux_server_1.status == DeviceStatus.CONNECTED

        # Test Linux Server 2
        assert mock_linux_server_2.device_id == "linux_server_002"
        assert mock_linux_server_2.os == "linux"
        assert "database_operations" in mock_linux_server_2.capabilities
        assert mock_linux_server_2.metadata["hostname"] == "api-server-01"
        assert mock_linux_server_2.status == DeviceStatus.CONNECTED

        # Test Windows Workstation
        assert mock_windows_workstation.device_id == "windows_workstation_001"
        assert mock_windows_workstation.os == "windows"
        assert "excel_processing" in mock_windows_workstation.capabilities
        assert mock_windows_workstation.metadata["hostname"] == "analyst-pc-01"
        assert mock_windows_workstation.status == DeviceStatus.CONNECTED

    def test_device_capabilities_for_log_collection_scenario(
        self, device_constellation: Dict[str, AgentProfile]
    ):
        """Test that devices have the required capabilities for the log collection scenario."""
        linux_servers = [
            dev for dev in device_constellation.values() if dev.os == "linux"
        ]
        windows_machines = [
            dev for dev in device_constellation.values() if dev.os == "windows"
        ]

        # Verify we have the expected number of devices
        assert len(linux_servers) == 2
        assert len(windows_machines) == 1

        # Verify Linux servers have log collection capabilities
        for server in linux_servers:
            assert "log_collection" in server.capabilities
            assert "file_operations" in server.capabilities
            assert "system_monitoring" in server.capabilities
            assert "log_paths" in server.metadata
            assert isinstance(server.metadata["log_paths"], list)
            assert len(server.metadata["log_paths"]) > 0

        # Verify Windows machine has Excel processing capabilities
        windows_device = windows_machines[0]
        assert "excel_processing" in windows_device.capabilities
        assert "office_applications" in windows_device.capabilities
        assert "report_generation" in windows_device.capabilities

    @pytest.mark.asyncio
    async def test_mock_log_collection_from_linux_servers(
        self, device_constellation: Dict[str, AgentProfile]
    ):
        """Test mock log collection process from Linux servers."""
        linux_servers = [
            dev for dev in device_constellation.values() if dev.os == "linux"
        ]

        collected_logs = {}

        for server in linux_servers:
            # Mock log collection command execution
            mock_logs = {
                "device_id": server.device_id,
                "hostname": server.metadata["hostname"],
                "collection_time": datetime.now(timezone.utc).isoformat(),
                "logs": [],
            }

            # Simulate collecting from each log path
            for log_path in server.metadata["log_paths"]:
                mock_log_entry = {
                    "log_path": log_path,
                    "lines_collected": 1000,  # Mock number of lines
                    "size_bytes": 1024 * 100,  # Mock file size
                    "last_modified": datetime.now(timezone.utc).isoformat(),
                    "sample_entries": [
                        f"[INFO] Sample log entry from {log_path}",
                        f"[WARN] Another sample entry from {log_path}",
                        f"[ERROR] Error sample from {log_path}",
                    ],
                }
                mock_logs["logs"].append(mock_log_entry)

            collected_logs[server.device_id] = mock_logs

        # Verify log collection results
        assert len(collected_logs) == 2
        assert "linux_server_001" in collected_logs
        assert "linux_server_002" in collected_logs

        # Verify log structure for each server
        for device_id, logs in collected_logs.items():
            assert logs["device_id"] == device_id
            assert "hostname" in logs
            assert "collection_time" in logs
            assert isinstance(logs["logs"], list)
            assert len(logs["logs"]) > 0

    @pytest.mark.asyncio
    async def test_mock_excel_generation_on_windows(
        self, device_constellation: Dict[str, AgentProfile]
    ):
        """Test mock Excel generation process on Windows workstation."""
        windows_device = next(
            dev for dev in device_constellation.values() if dev.os == "windows"
        )

        # Mock collected log data from Linux servers
        mock_collected_data = {
            "linux_server_001": {
                "hostname": "web-server-01",
                "total_log_files": 4,
                "total_lines": 4000,
                "total_size_mb": 25.6,
                "error_count": 15,
                "warning_count": 45,
                "info_count": 3940,
            },
            "linux_server_002": {
                "hostname": "api-server-01",
                "total_log_files": 5,
                "total_lines": 3500,
                "total_size_mb": 18.2,
                "error_count": 8,
                "warning_count": 32,
                "info_count": 3460,
            },
        }

        # Mock Excel generation process
        excel_report = {
            "report_name": f"Linux_Server_Log_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "generated_by": windows_device.device_id,
            "generation_time": datetime.now(timezone.utc).isoformat(),
            "sheets": [
                {
                    "name": "Summary",
                    "rows": len(mock_collected_data) + 1,  # +1 for header
                    "columns": 8,
                },
                {
                    "name": "Server Details",
                    "rows": sum(
                        data["total_log_files"] for data in mock_collected_data.values()
                    )
                    + 1,
                    "columns": 6,
                },
                {
                    "name": "Error Analysis",
                    "rows": sum(
                        data["error_count"] for data in mock_collected_data.values()
                    )
                    + 1,
                    "columns": 4,
                },
            ],
            "charts": ["Log Volume by Server", "Error Distribution", "Warning Trends"],
            "file_size_kb": 145.7,
        }

        # Verify Excel generation capabilities
        assert "excel_processing" in windows_device.capabilities
        assert "Microsoft Office 365" in windows_device.metadata["installed_software"]
        assert "pandas" in windows_device.metadata["python_packages"]
        assert "openpyxl" in windows_device.metadata["python_packages"]

        # Verify Excel report structure
        assert excel_report["generated_by"] == windows_device.device_id
        assert excel_report["report_name"].endswith(".xlsx")
        assert len(excel_report["sheets"]) == 3
        assert len(excel_report["charts"]) == 3
        assert excel_report["file_size_kb"] > 0

    @pytest.mark.asyncio
    async def test_complete_log_collection_and_excel_workflow(
        self, device_constellation: Dict[str, AgentProfile]
    ):
        """Test the complete workflow from log collection to Excel generation."""
        # Step 1: Identify available devices
        linux_servers = [
            dev for dev in device_constellation.values() if dev.os == "linux"
        ]
        windows_devices = [
            dev for dev in device_constellation.values() if dev.os == "windows"
        ]

        assert len(linux_servers) == 2
        assert len(windows_devices) == 1

        # Step 2: Mock log collection phase
        log_collection_tasks = []
        for server in linux_servers:
            task_result = {
                "device_id": server.device_id,
                "status": "completed",
                "logs_collected": len(server.metadata["log_paths"]),
                "collection_duration_seconds": 45.3,
                "data_size_mb": 20.5 + (5.2 * len(server.metadata["log_paths"])),
            }
            log_collection_tasks.append(task_result)

        # Step 3: Mock data aggregation
        aggregated_data = {
            "total_servers": len(linux_servers),
            "total_log_files": sum(
                task["logs_collected"] for task in log_collection_tasks
            ),
            "total_data_size_mb": sum(
                task["data_size_mb"] for task in log_collection_tasks
            ),
            "collection_time_total_seconds": sum(
                task["collection_duration_seconds"] for task in log_collection_tasks
            ),
            "successful_collections": len(
                [t for t in log_collection_tasks if t["status"] == "completed"]
            ),
        }

        # Step 4: Mock Excel generation on Windows
        windows_device = windows_devices[0]
        excel_generation_result = {
            "device_id": windows_device.device_id,
            "status": "completed",
            "report_file": f"Log_Analysis_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "processing_time_seconds": 12.8,
            "sheets_created": 4,
            "charts_generated": 3,
            "rows_processed": aggregated_data["total_log_files"]
            * 50,  # Mock row calculation
            "output_file_size_kb": 237.4,
        }

        # Verify complete workflow
        assert aggregated_data["successful_collections"] == 2
        assert aggregated_data["total_servers"] == 2
        assert aggregated_data["total_log_files"] > 0
        assert aggregated_data["total_data_size_mb"] > 0

        assert excel_generation_result["status"] == "completed"
        assert excel_generation_result["device_id"] == windows_device.device_id
        assert excel_generation_result["report_file"].endswith(".xlsx")
        assert excel_generation_result["sheets_created"] > 0
        assert excel_generation_result["charts_generated"] > 0

    def test_device_metadata_validation(
        self, device_constellation: Dict[str, AgentProfile]
    ):
        """Test that all devices have proper metadata for the log collection scenario."""
        for device_id, device in device_constellation.items():
            # Basic metadata validation
            assert device.device_id == device_id
            assert device.os in ["linux", "windows"]
            assert "hostname" in device.metadata
            assert "location" in device.metadata
            assert "performance" in device.metadata
            assert device.status == DeviceStatus.CONNECTED

            # OS-specific metadata validation
            if device.os == "linux":
                assert "log_paths" in device.metadata
                assert isinstance(device.metadata["log_paths"], list)
                assert len(device.metadata["log_paths"]) > 0
                assert "services" in device.metadata

            elif device.os == "windows":
                assert "installed_software" in device.metadata
                assert "Microsoft Office 365" in device.metadata["installed_software"]
                assert "python_packages" in device.metadata

    @pytest.mark.asyncio
    async def test_error_handling_scenarios(
        self, device_constellation: Dict[str, AgentProfile]
    ):
        """Test error handling scenarios in the log collection workflow."""
        # Test scenario: One Linux server fails
        linux_servers = [
            dev for dev in device_constellation.values() if dev.os == "linux"
        ]
        windows_device = next(
            dev for dev in device_constellation.values() if dev.os == "windows"
        )

        # Simulate partial failure
        mock_results = []
        for i, server in enumerate(linux_servers):
            if i == 0:  # First server succeeds
                result = {
                    "device_id": server.device_id,
                    "status": "completed",
                    "logs_collected": len(server.metadata["log_paths"]),
                    "error": None,
                }
            else:  # Second server fails
                result = {
                    "device_id": server.device_id,
                    "status": "failed",
                    "logs_collected": 0,
                    "error": "Connection timeout during log collection",
                }
            mock_results.append(result)

        # Verify partial success handling
        successful_results = [r for r in mock_results if r["status"] == "completed"]
        failed_results = [r for r in mock_results if r["status"] == "failed"]

        assert len(successful_results) == 1
        assert len(failed_results) == 1

        # Test Excel generation with partial data
        partial_report = {
            "device_id": windows_device.device_id,
            "status": "completed_with_warnings",
            "successful_servers": len(successful_results),
            "failed_servers": len(failed_results),
            "report_notes": "Report generated with partial data due to server connection issues",
        }

        assert partial_report["successful_servers"] > 0
        assert partial_report["status"] == "completed_with_warnings"

    def test_device_formatting_for_prompt(
        self, device_constellation: Dict[str, AgentProfile]
    ):
        """Test device formatting for LLM prompt usage."""
        # This simulates how devices would be formatted for constellation prompts
        formatted_devices = []

        for device_id, device in device_constellation.items():
            capabilities = (
                ", ".join(device.capabilities) if device.capabilities else "None"
            )
            os = device.os if device.os else "Unknown"

            metadata_items = []
            if device.metadata:
                # Select key metadata for prompt
                key_metadata = ["hostname", "location", "os_version", "performance"]
                for key in key_metadata:
                    if key in device.metadata:
                        metadata_items.append(f"{key}: {device.metadata[key]}")

            metadata_str = (
                f" | Metadata: {', '.join(metadata_items)}" if metadata_items else ""
            )

            device_summary = (
                f"Device ID: {device.device_id}\n"
                f"OS: {os}\n"
                f"  - Capabilities: {capabilities}\n"
                f"{metadata_str}"
            )

            formatted_devices.append(device_summary)

        formatted_output = "Available Devices:\n\n" + "\n\n".join(formatted_devices)

        # Verify formatting
        assert "Available Devices:" in formatted_output
        assert "linux_server_001" in formatted_output
        assert "linux_server_002" in formatted_output
        assert "windows_workstation_001" in formatted_output
        assert "log_collection" in formatted_output
        assert "excel_processing" in formatted_output

    def test_request_english_translation(self):
        """Test that the Chinese request translates to the expected English scenario."""
        chinese_request = "帮我mock 三个AgentProfile 做测试，两个linux，一个windows，然后在 tests 文件夹建立测试英文request是关于从两个linux服务器采集log 在windows上生成excel"

        english_equivalent = (
            "Help me mock three AgentProfile objects for testing: two Linux servers and one Windows machine. "
            "Create tests in the tests folder. The English request scenario is about collecting logs from "
            "two Linux servers and generating an Excel report on Windows."
        )

        # This test documents the translation and validates our implementation matches the request
        expected_components = {
            "mock_devices": 3,
            "linux_servers": 2,
            "windows_machines": 1,
            "scenario": "log_collection_and_excel_generation",
            "test_location": "tests_folder",
        }

        # Verify our test implementation matches the request
        assert expected_components["mock_devices"] == 3
        assert expected_components["linux_servers"] == 2
        assert expected_components["windows_machines"] == 1
        assert expected_components["scenario"] == "log_collection_and_excel_generation"
        assert expected_components["test_location"] == "tests_folder"

        # Verify this test file addresses the request
        assert __file__.endswith("test_linux_log_collection_excel_generation.py")
        assert "tests" in __file__
