"""
Tests for ConstellationSerializer class.
Validates serialization and deserialization functionality.
"""

import json
import pytest
from datetime import datetime

from galaxy.constellation.parsers.constellation_serializer import (
    ConstellationSerializer,
)
from galaxy.constellation.task_constellation import (
    TaskConstellation,
    ConstellationState,
)
from galaxy.constellation.task_star import TaskStar, TaskPriority, TaskStatus
from galaxy.constellation.task_star_line import TaskStarLine


class TestConstellationSerializer:
    """Test ConstellationSerializer functionality."""

    def test_to_dict_basic(self):
        """Test basic constellation to dictionary conversion."""
        constellation = TaskConstellation(name="Test Constellation")

        # Add a task
        task = TaskStar(
            task_id="task_1", description="Test task", priority=TaskPriority.HIGH
        )
        constellation.add_task(task)

        # Convert to dict
        data = ConstellationSerializer.to_dict(constellation)

        assert data["name"] == "Test Constellation"
        assert data["state"] == ConstellationState.CREATED.value
        assert "task_1" in data["tasks"]
        assert data["tasks"]["task_1"]["description"] == "Test task"
        assert data["metadata"] == {}

    def test_from_dict_basic(self):
        """Test basic constellation from dictionary creation."""
        data = {
            "constellation_id": "test_id",
            "name": "Test Constellation",
            "state": ConstellationState.CREATED.value,
            "tasks": {
                "task_1": {
                    "task_id": "task_1",
                    "description": "Test task",
                    "priority": TaskPriority.HIGH.value,
                    "status": TaskStatus.PENDING.value,
                    "metadata": {},
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
            },
            "dependencies": {},
            "metadata": {"test": "value"},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        constellation = ConstellationSerializer.from_dict(data)

        assert constellation.name == "Test Constellation"
        assert constellation.constellation_id == "test_id"
        assert constellation.state == ConstellationState.CREATED
        assert len(constellation.tasks) == 1
        assert "task_1" in constellation.tasks
        assert constellation.metadata == {"test": "value"}

    def test_to_json_and_from_json(self):
        """Test JSON serialization round trip."""
        # Create constellation with task and dependency
        constellation = TaskConstellation(name="JSON Test")

        task1 = TaskStar(task_id="task_1", description="First task")
        task2 = TaskStar(task_id="task_2", description="Second task")
        constellation.add_task(task1)
        constellation.add_task(task2)

        # Add dependency
        dep = TaskStarLine.create_unconditional(
            "task_1", "task_2", "Sequential dependency"
        )
        constellation.add_dependency(dep)

        # Convert to JSON and back
        json_str = ConstellationSerializer.to_json(constellation)
        restored = ConstellationSerializer.from_json(json_str)

        assert restored.name == constellation.name
        assert len(restored.tasks) == len(constellation.tasks)
        assert len(restored.dependencies) == len(constellation.dependencies)

        # Verify task details
        for task_id, task in constellation.tasks.items():
            assert task_id in restored.tasks
            assert restored.tasks[task_id].description == task.description

    def test_normalize_json_data_dependencies_list(self):
        """Test normalization of dependencies in list format."""
        data = {
            "name": "Test",
            "tasks": {},
            "dependencies": [
                {
                    "predecessor_id": "task_1",
                    "successor_id": "task_2",
                    "dependency_type": "unconditional",
                }
            ],
        }

        normalized = ConstellationSerializer.normalize_json_data(data)

        assert isinstance(normalized["dependencies"], dict)
        assert "dep_0" in normalized["dependencies"]
        dep = normalized["dependencies"]["dep_0"]
        assert dep["from_task_id"] == "task_1"
        assert dep["to_task_id"] == "task_2"
        assert dep["dependency_type"] == "unconditional"

    def test_normalize_json_data_dependencies_dict(self):
        """Test normalization preserves dict format dependencies."""
        data = {
            "name": "Test",
            "tasks": {},
            "dependencies": {
                "dep_1": {"from_task_id": "task_1", "to_task_id": "task_2"}
            },
        }

        normalized = ConstellationSerializer.normalize_json_data(data)

        assert normalized["dependencies"] == data["dependencies"]

    def test_serialization_with_timestamps(self):
        """Test serialization preserves timestamps correctly."""
        constellation = TaskConstellation(name="Timestamp Test")
        constellation.start_execution()
        constellation.complete_execution()

        # Serialize and deserialize
        json_str = ConstellationSerializer.to_json(constellation)
        restored = ConstellationSerializer.from_json(json_str)

        assert restored.execution_start_time is not None
        assert restored.execution_end_time is not None
        assert restored.created_at is not None
        assert restored.updated_at is not None

    def test_serialization_with_metadata(self):
        """Test serialization preserves metadata correctly."""
        constellation = TaskConstellation(name="Metadata Test")
        constellation.update_metadata({"custom_field": "custom_value"})
        constellation.update_metadata({"nested": {"key": "value"}})

        # Serialize and deserialize
        data = ConstellationSerializer.to_dict(constellation)
        restored = ConstellationSerializer.from_dict(data)

        assert restored.metadata["custom_field"] == "custom_value"
        assert restored.metadata["nested"]["key"] == "value"

    def test_empty_constellation_serialization(self):
        """Test serialization of empty constellation."""
        constellation = TaskConstellation(name="Empty")

        data = ConstellationSerializer.to_dict(constellation)
        restored = ConstellationSerializer.from_dict(data)

        assert restored.name == "Empty"
        assert len(restored.tasks) == 0
        assert len(restored.dependencies) == 0
        assert restored.state == ConstellationState.CREATED

    def test_json_serialization_invalid_input(self):
        """Test error handling for invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            ConstellationSerializer.from_json("invalid json")

    def test_dict_serialization_missing_fields(self):
        """Test serialization handles missing fields gracefully."""
        minimal_data = {"name": "Minimal Test"}

        constellation = ConstellationSerializer.from_dict(minimal_data)

        assert constellation.name == "Minimal Test"
        assert constellation.state == ConstellationState.CREATED
        assert len(constellation.tasks) == 0
        assert len(constellation.dependencies) == 0
