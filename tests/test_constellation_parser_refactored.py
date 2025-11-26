"""
Tests for refactored ConstellationParser integration.
Validates that ConstellationParser properly uses ConstellationSerializer and ConstellationUpdater.
"""

import pytest
import json
from unittest.mock import Mock, patch

from galaxy.constellation.parsers.constellation_parser import ConstellationParser
from galaxy.constellation.parsers.constellation_serializer import (
    ConstellationSerializer,
)
from galaxy.constellation.parsers.constellation_updater import ConstellationUpdater
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.constellation.task_star import TaskStar, TaskPriority


class TestConstellationParserRefactored:
    """Test refactored ConstellationParser functionality."""

    @pytest.fixture
    def parser(self):
        """Create a ConstellationParser instance."""
        return ConstellationParser(enable_logging=False)

    @pytest.fixture
    def sample_json_data(self):
        """Create sample JSON data for testing."""
        return {
            "name": "Test Constellation",
            "tasks": {
                "task_1": {
                    "task_id": "task_1",
                    "description": "First task",
                    "priority": 2,  # TaskPriority.MEDIUM
                    "status": "pending",
                    "metadata": {},
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                }
            },
            "dependencies": {},
            "metadata": {},
        }

    def test_parser_uses_serializer_for_json_creation(self, parser, sample_json_data):
        """Test that parser uses ConstellationSerializer for JSON creation."""
        with patch.object(
            ConstellationSerializer, "normalize_json_data"
        ) as mock_normalize, patch.object(
            ConstellationSerializer, "from_dict"
        ) as mock_from_dict:

            mock_normalize.return_value = sample_json_data
            mock_constellation = TaskConstellation(name="Test")
            mock_from_dict.return_value = mock_constellation

            result = parser.create_from_json(json.dumps(sample_json_data))

            mock_normalize.assert_called_once()
            mock_from_dict.assert_called_once()
            assert result == mock_constellation

    def test_parser_uses_updater_for_llm_updates(self, parser):
        """Test that parser uses ConstellationUpdater for LLM updates."""
        constellation = TaskConstellation(name="Test")
        modification_request = "ADD TASK: New task"

        with patch.object(parser._updater, "update_from_llm_output") as mock_update:
            result = parser.update_from_llm(constellation, modification_request)

            mock_update.assert_called_once_with(constellation, modification_request)
            assert result == constellation

    def test_parser_uses_updater_for_task_addition(self, parser):
        """Test that parser uses ConstellationUpdater for adding tasks."""
        constellation = TaskConstellation(name="Test")
        constellation.add_task(
            TaskStar(task_id="existing_task", description="Existing")
        )

        task = TaskStar(task_id="new_task", description="New task")
        dependencies = ["existing_task"]

        with patch.object(parser._updater, "add_dependencies") as mock_add_deps:
            result = parser.add_task_to_constellation(constellation, task, dependencies)

            assert result is True
            assert "new_task" in constellation.tasks
            mock_add_deps.assert_called_once()

    def test_parser_uses_updater_for_task_removal(self, parser):
        """Test that parser uses ConstellationUpdater for removing tasks."""
        constellation = TaskConstellation(name="Test")
        constellation.add_task(
            TaskStar(task_id="task_to_remove", description="Remove me")
        )

        with patch.object(parser._updater, "remove_tasks") as mock_remove:
            result = parser.remove_task_from_constellation(
                constellation, "task_to_remove"
            )

            mock_remove.assert_called_once_with(
                constellation, ["task_to_remove"], remove_dependencies=True
            )
            assert result is True

    def test_parser_uses_serializer_for_export(self, parser):
        """Test that parser uses ConstellationSerializer for export operations."""
        constellation = TaskConstellation(name="Test")

        with patch.object(ConstellationSerializer, "to_json") as mock_to_json:
            mock_to_json.return_value = '{"test": "data"}'

            result = parser.export_constellation(constellation, "json")

            mock_to_json.assert_called_once_with(constellation, indent=2)
            assert result == '{"test": "data"}'

    def test_parser_uses_serializer_for_cloning(self, parser):
        """Test that parser uses ConstellationSerializer for cloning."""
        constellation = TaskConstellation(name="Original")

        with patch.object(
            ConstellationSerializer, "to_json"
        ) as mock_to_json, patch.object(
            ConstellationSerializer, "from_json"
        ) as mock_from_json:

            mock_to_json.return_value = '{"test": "data"}'
            mock_cloned = TaskConstellation(name="Cloned")
            mock_from_json.return_value = mock_cloned

            result = parser.clone_constellation(constellation, "Cloned")

            mock_to_json.assert_called_once()
            mock_from_json.assert_called_once_with('{"test": "data"}')
            assert result.name == "Cloned"

    def test_json_normalization_with_list_dependencies(self, parser):
        """Test that parser properly normalizes JSON with list dependencies."""
        json_data = {
            "name": "Test",
            "tasks": {},
            "dependencies": [{"predecessor_id": "task_1", "successor_id": "task_2"}],
        }

        result = parser.create_from_json(json.dumps(json_data))

        assert result.name == "Test"
        # The normalization should have converted the list to dict format

    def test_constellation_name_override(self, parser, sample_json_data):
        """Test that constellation name can be overridden during creation."""
        result = parser.create_from_json(
            json.dumps(sample_json_data), constellation_name="Override Name"
        )

        assert result.name == "Override Name"

    def test_error_handling_invalid_json(self, parser):
        """Test error handling for invalid JSON input."""
        with pytest.raises(ValueError, match="Invalid JSON data"):
            parser.create_from_json("invalid json")

    def test_create_simple_sequential_delegation(self, parser):
        """Test that simple sequential creation still works after refactoring."""
        descriptions = ["Task 1", "Task 2", "Task 3"]

        result = parser.create_simple_sequential(descriptions, "Sequential Test")

        assert result.name == "Sequential Test"
        assert len(result.tasks) == 3
        assert len(result.dependencies) == 2  # Sequential dependencies

    def test_create_simple_parallel_delegation(self, parser):
        """Test that simple parallel creation still works after refactoring."""
        descriptions = ["Task 1", "Task 2", "Task 3"]

        result = parser.create_simple_parallel(descriptions, "Parallel Test")

        assert result.name == "Parallel Test"
        assert len(result.tasks) == 3
        assert len(result.dependencies) == 0  # No dependencies in parallel

    def test_parser_initialization(self):
        """Test that parser properly initializes its dependencies."""
        parser = ConstellationParser(enable_logging=True)

        assert parser._updater is not None
        assert isinstance(parser._updater, ConstellationUpdater)
        assert parser._logger is not None

    def test_parser_initialization_no_logging(self):
        """Test parser initialization without logging."""
        parser = ConstellationParser(enable_logging=False)

        assert parser._updater is not None
        assert parser._logger is None

    def test_export_format_validation(self, parser):
        """Test that export validates format properly."""
        constellation = TaskConstellation(name="Test")

        with pytest.raises(ValueError, match="Unsupported export format"):
            parser.export_constellation(constellation, "invalid_format")

    def test_export_llm_format(self, parser):
        """Test export in LLM format uses constellation method."""
        constellation = TaskConstellation(name="Test")

        result = parser.export_constellation(constellation, "llm")

        # Should call constellation.to_llm_string() directly
        assert isinstance(result, str)
        assert "TaskConstellation: Test" in result

    def test_task_addition_error_handling(self, parser):
        """Test error handling in task addition."""
        constellation = TaskConstellation(name="Test")
        task = TaskStar(task_id="duplicate", description="Task")

        # Add the task first
        constellation.add_task(task)

        # Try to add the same task again (should cause error)
        result = parser.add_task_to_constellation(constellation, task)

        assert result is False

    def test_task_removal_nonexistent_task(self, parser):
        """Test removing a nonexistent task."""
        constellation = TaskConstellation(name="Test")

        result = parser.remove_task_from_constellation(constellation, "nonexistent")

        assert result is False

    def test_integration_create_and_update(self, parser):
        """Test integration: create constellation and then update it."""
        # Create constellation from JSON
        json_data = {
            "name": "Integration Test",
            "tasks": {
                "task_1": {
                    "task_id": "task_1",
                    "description": "Initial task",
                    "priority": 2,  # TaskPriority.MEDIUM
                    "status": "pending",
                    "metadata": {},
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                }
            },
            "dependencies": {},
            "metadata": {},
        }

        constellation = parser.create_from_json(json.dumps(json_data))
        assert len(constellation.tasks) == 1

        # Update with LLM output
        llm_update = "ADD TASK: Second task from LLM"
        updated = parser.update_from_llm(constellation, llm_update)

        # Should be the same constellation object, but with updates applied
        assert updated == constellation
        assert len(constellation.tasks) == 2
