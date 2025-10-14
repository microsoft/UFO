# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Tests for BaseConstellationPrompter formatting functions.

This module tests the formatting functions used to convert complex objects
into LLM-friendly string representations.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from galaxy.agents.prompters.base_constellation_prompter import (
    BaseConstellationPrompter,
)
from galaxy.client.components.types import AgentProfile, DeviceStatus
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.constellation.task_star import TaskStar
from galaxy.constellation.task_star_line import TaskStarLine
from galaxy.constellation.enums import (
    TaskStatus,
    ConstellationState,
    DependencyType,
    TaskPriority,
)


class TestBaseConstellationPrompter:
    """Test cases for BaseConstellationPrompter formatting methods."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock the parent class initialization to avoid file loading
        with patch.object(BaseConstellationPrompter, "__init__", lambda x, y, z: None):
            self.prompter = BaseConstellationPrompter("mock_template", "mock_example")
            # Manually set required attributes that would normally be set by parent __init__
            self.prompter.prompt_template = {}
            self.prompter.example_prompt_template = {}

    def test_format_device_info_empty(self):
        """Test formatting empty device info."""
        result = self.prompter._format_device_info({})
        assert result == "No devices available."

    def test_format_device_info_single_device(self):
        """Test formatting single device info."""
        device_info = AgentProfile(
            device_id="laptop_001",
            server_url="ws://192.168.1.100:5000/ws",
            capabilities=["web_browsing", "office_applications"],
            metadata={"os": "windows", "location": "office"},
            status=DeviceStatus.CONNECTED,
            last_heartbeat=datetime(2025, 9, 25, 14, 30, 15, tzinfo=timezone.utc),
            connection_attempts=1,
            max_retries=5,
        )

        device_dict = {"laptop_001": device_info}
        result = self.prompter._format_device_info(device_dict)

        assert "Available Devices:" in result
        assert "Device ID: laptop_001" in result
        assert "web_browsing, office_applications" in result
        assert "os: windows, location: office" in result

    def test_format_device_info_multiple_devices(self):
        """Test formatting multiple devices."""
        device1 = AgentProfile(
            device_id="laptop_001",
            server_url="ws://192.168.1.100:5000/ws",
            capabilities=["web_browsing"],
            metadata={"os": "windows"},
            status=DeviceStatus.CONNECTED,
        )

        device2 = AgentProfile(
            device_id="server_002",
            server_url="ws://192.168.1.101:5000/ws",
            capabilities=["database_management"],
            metadata={"os": "linux"},
            status=DeviceStatus.DISCONNECTED,
        )

        device_dict = {"laptop_001": device1, "server_002": device2}
        result = self.prompter._format_device_info(device_dict)

        assert "laptop_001" in result
        assert "server_002" in result
        assert "web_browsing" in result
        assert "database_management" in result

    def test_format_constellation_none(self):
        """Test formatting None constellation."""
        result = self.prompter._format_constellation(None)
        assert result == "No constellation information available."

    def test_format_constellation_basic(self):
        """Test formatting basic constellation structure."""
        # Create a mock constellation with to_dict method
        mock_constellation = Mock()
        mock_constellation.to_dict.return_value = {
            "name": "Test Constellation",
            "state": "ready",
            "tasks": {
                "task_001": {
                    "name": "Web Search",
                    "status": "pending",
                    "target_device_id": "laptop_001",
                    "description": "Search for information on the web",
                    "tips": ["Use reliable sources", "Check multiple websites"],
                    "result": None,
                    "error": None,
                }
            },
            "dependencies": {
                "dep_001": {
                    "from_task_id": "task_001",
                    "to_task_id": "task_002",
                    "dependency_type": "unconditional",
                    "condition_description": "",
                    "is_satisfied": False,
                }
            },
            "execution_start_time": "2025-09-25T14:30:00+00:00",
            "execution_end_time": None,
            "execution_duration": None,
        }

        result = self.prompter._format_constellation(mock_constellation)

        # Check header information
        assert "Task Constellation: Test Constellation" in result
        assert "Status: ready" in result
        assert "Total Tasks: 1" in result

        # Check task information
        assert "[task_001] Web Search" in result
        assert "Status: pending" in result
        assert "Device: laptop_001" in result
        assert "Description: Search for information on the web" in result
        assert "Tips:" in result
        assert "- Use reliable sources" in result
        assert "- Check multiple websites" in result

        # Check dependency information
        assert "Task Dependencies:" in result
        assert "task_001 → task_002 (unconditional)" in result
        assert "✗ Not Satisfied" in result

        # Check execution info
        assert "Execution Info:" in result
        assert "Started: 2025-09-25T14:30:00+00:00" in result

    def test_format_constellation_with_completed_task(self):
        """Test formatting constellation with completed task and result."""
        mock_constellation = Mock()
        mock_constellation.to_dict.return_value = {
            "name": "Completed Task Constellation",
            "state": "executing",
            "tasks": {
                "task_001": {
                    "name": "Data Analysis",
                    "status": "completed",
                    "target_device_id": "workstation_001",
                    "description": "Analyze the dataset",
                    "tips": ["Check data quality", "Use appropriate algorithms"],
                    "result": {
                        "analysis_complete": True,
                        "accuracy": 0.95,
                        "details": "Analysis showed positive trends with 95% accuracy across all metrics",
                    },
                    "error": None,
                }
            },
            "dependencies": {},
            "execution_start_time": "2025-09-25T14:00:00+00:00",
            "execution_end_time": "2025-09-25T14:30:00+00:00",
            "execution_duration": 1800.0,
        }

        result = self.prompter._format_constellation(mock_constellation)

        assert "Data Analysis" in result
        assert "Status: completed" in result
        assert (
            "Result: {'analysis_complete': True, 'accuracy': 0.95, 'details': 'Analysis showed positive trends with 95% a"
            in result
        )
        assert "Duration: 1800.00s" in result

    def test_format_constellation_with_failed_task(self):
        """Test formatting constellation with failed task."""
        mock_constellation = Mock()
        mock_constellation.to_dict.return_value = {
            "name": "Failed Task Constellation",
            "state": "failed",
            "tasks": {
                "task_001": {
                    "name": "Database Query",
                    "status": "failed",
                    "target_device_id": "server_001",
                    "description": "Query customer database",
                    "tips": ["Check connection", "Verify credentials"],
                    "result": None,
                    "error": "Connection timeout to database server",
                }
            },
            "dependencies": {},
            "execution_start_time": None,
            "execution_end_time": None,
            "execution_duration": None,
        }

        result = self.prompter._format_constellation(mock_constellation)

        assert "Database Query" in result
        assert "Status: failed" in result
        assert "Error: Connection timeout to database server" in result

    def test_format_constellation_complex_dependencies(self):
        """Test formatting constellation with complex dependencies."""
        mock_constellation = Mock()
        mock_constellation.to_dict.return_value = {
            "name": "Complex Dependencies",
            "state": "ready",
            "tasks": {
                "task_001": {
                    "name": "Prepare Data",
                    "status": "completed",
                    "target_device_id": "laptop_001",
                    "description": "Prepare input data",
                    "tips": [],
                    "result": "Data prepared successfully",
                    "error": None,
                },
                "task_002": {
                    "name": "Process Data",
                    "status": "pending",
                    "target_device_id": "workstation_001",
                    "description": "Process the prepared data",
                    "tips": ["Use parallel processing"],
                    "result": None,
                    "error": None,
                },
            },
            "dependencies": {
                "dep_001": {
                    "from_task_id": "task_001",
                    "to_task_id": "task_002",
                    "dependency_type": "conditional",
                    "condition_description": "Only if data quality is acceptable",
                    "is_satisfied": True,
                }
            },
            "execution_start_time": None,
            "execution_end_time": None,
            "execution_duration": None,
        }

        result = self.prompter._format_constellation(mock_constellation)

        assert "task_001 → task_002 (conditional)" in result
        assert "Only if data quality is acceptable" in result
        assert "✓ Satisfied" in result

    def test_format_constellation_exception_handling(self):
        """Test handling of constellation formatting exceptions."""
        mock_constellation = Mock()
        mock_constellation.to_dict.side_effect = Exception("Mock exception")

        result = self.prompter._format_constellation(mock_constellation)

        assert (
            result == "Constellation information unavailable due to formatting error."
        )

    def test_format_constellation_empty_tasks_and_dependencies(self):
        """Test formatting constellation with no tasks or dependencies."""
        mock_constellation = Mock()
        mock_constellation.to_dict.return_value = {
            "name": "Empty Constellation",
            "state": "created",
            "tasks": {},
            "dependencies": {},
            "execution_start_time": None,
            "execution_end_time": None,
            "execution_duration": None,
        }

        result = self.prompter._format_constellation(mock_constellation)

        assert "Task Constellation: Empty Constellation" in result
        assert "Status: created" in result
        assert "Total Tasks: 0" in result
        # Should not have Tasks: or Task Dependencies: sections when empty
        # Note: "Total Tasks: 0" is in the header which is correct
        # Only the section header "Tasks:" should not appear for empty task list
        lines = result.split("\n")
        task_section_lines = [line for line in lines if line.strip() == "Tasks:"]
        assert (
            len(task_section_lines) == 0
        )  # No "Tasks:" section header for empty tasks
        assert "Task Dependencies:" not in result


if __name__ == "__main__":
    pytest.main([__file__])
