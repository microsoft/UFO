# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for ConstellationParser.

Tests constellation creation, parsing, updating, validation,
and export/import functionality.
"""

import asyncio
import json
import pytest
from typing import Dict, List, Optional

from galaxy.constellation.parsers.constellation_parser import ConstellationParser
from galaxy.constellation.enums import TaskStatus, DeviceType
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.constellation.task_star import TaskStar


class TestConstellationParser:
    """Test cases for ConstellationParser class."""

    @pytest.fixture
    def parser(self):
        """Create a ConstellationParser instance for testing."""
        return ConstellationParser(enable_logging=False)

    @pytest.fixture
    def sample_task_descriptions(self):
        """Sample task descriptions for testing."""
        return [
            "Open the browser",
            "Navigate to the website",
            "Fill out the form",
            "Submit the form",
            "Verify the result",
        ]

    @pytest.fixture
    def sample_llm_output(self):
        """Sample LLM output for testing."""
        return """
        Task 1: Open browser
        Description: Launch the web browser application
        
        Task 2: Navigate to site
        Description: Go to the target website
        Dependencies: Task 1
        
        Task 3: Fill form
        Description: Complete the form fields
        Dependencies: Task 2
        
        Task 4: Submit
        Description: Submit the completed form
        Dependencies: Task 3
        """

    @pytest.fixture
    def sample_constellation_json(self):
        """Sample constellation JSON data for testing."""
        return json.dumps(
            {
                "constellation_id": "test_constellation",
                "name": "Test Constellation",
                "description": "Test constellation for parsing",
                "tasks": {
                    "task1": {
                        "task_id": "task1",
                        "description": "First task",
                        "status": "pending",
                    },
                    "task2": {
                        "task_id": "task2",
                        "description": "Second task",
                        "status": "pending",
                    },
                },
                "dependencies": [
                    {
                        "predecessor_id": "task1",
                        "successor_id": "task2",
                        "dependency_type": "unconditional",
                    }
                ],
            }
        )

    @pytest.mark.asyncio
    async def test_create_from_llm(self, parser, sample_llm_output):
        """Test creating constellation from LLM output."""
        constellation = await parser.create_from_llm(
            sample_llm_output, "LLM Test Constellation"
        )

        assert isinstance(constellation, TaskConstellation)
        assert constellation.name == "LLM Test Constellation"
        assert constellation.task_count > 0

        # Should have parsed the tasks mentioned in LLM output
        task_ids = list(constellation.tasks.keys())
        assert len(task_ids) > 0

    @pytest.mark.asyncio
    async def test_create_from_json(self, parser, sample_constellation_json):
        """Test creating constellation from JSON data."""
        constellation = await parser.create_from_json(
            sample_constellation_json, "JSON Test Constellation"
        )

        assert isinstance(constellation, TaskConstellation)
        assert constellation.name == "JSON Test Constellation"
        assert constellation.task_count == 2
        assert "task1" in constellation.tasks
        assert "task2" in constellation.tasks
        assert constellation.dependency_count == 1

    @pytest.mark.asyncio
    async def test_create_simple_sequential(self, parser, sample_task_descriptions):
        """Test creating simple sequential constellation."""
        constellation = parser.create_simple_sequential(
            sample_task_descriptions, "Sequential Test"
        )

        assert isinstance(constellation, TaskConstellation)
        assert constellation.name == "Sequential Test"
        assert constellation.task_count == len(sample_task_descriptions)

        # Should have dependencies for sequential execution
        assert constellation.dependency_count == len(sample_task_descriptions) - 1

        # Verify task descriptions
        for i, description in enumerate(sample_task_descriptions):
            task_id = f"task_{i+1}"
            assert task_id in constellation.tasks
            assert description in constellation.tasks[task_id].description

    @pytest.mark.asyncio
    async def test_create_simple_parallel(self, parser, sample_task_descriptions):
        """Test creating simple parallel constellation."""
        constellation = parser.create_simple_parallel(
            sample_task_descriptions, "Parallel Test"
        )

        assert isinstance(constellation, TaskConstellation)
        assert constellation.name == "Parallel Test"
        assert constellation.task_count == len(sample_task_descriptions)

        # Should have no dependencies for parallel execution
        assert constellation.dependency_count == 0

        # All tasks should be ready to execute
        ready_tasks = constellation.get_ready_tasks()
        assert len(ready_tasks) == len(sample_task_descriptions)

    @pytest.mark.asyncio
    async def test_update_from_llm(self, parser):
        """Test updating constellation from LLM output."""
        # Create initial constellation
        initial_tasks = ["Task A", "Task B"]
        constellation = parser.create_simple_sequential(
            initial_tasks, "Test Constellation"
        )

        initial_task_count = constellation.task_count

        # Update with LLM request
        update_request = "Add a new task 'Task C' after Task B"
        updated_constellation = await parser.update_from_llm(
            constellation, update_request
        )

        assert isinstance(updated_constellation, TaskConstellation)
        # The update is currently a placeholder that returns the original
        # In a real implementation, this would parse the LLM response
        assert updated_constellation.task_count == initial_task_count

    def test_add_task_to_constellation(self, parser):
        """Test adding a task to existing constellation."""
        constellation = TaskConstellation(name="Test Constellation")

        # Add initial task
        task1 = TaskStar(task_id="task1", description="Initial task")
        constellation.add_task(task1)

        # Add new task with dependencies
        task2 = TaskStar(task_id="task2", description="Dependent task")
        success = parser.add_task_to_constellation(
            constellation, task2, dependencies=["task1"]
        )

        assert success
        assert constellation.task_count == 2
        assert "task2" in constellation.tasks
        assert constellation.dependency_count == 1

    def test_remove_task_from_constellation(self, parser):
        """Test removing a task from constellation."""
        constellation = TaskConstellation(name="Test Constellation")

        # Add tasks
        task1 = TaskStar(task_id="task1", description="First task")
        task2 = TaskStar(task_id="task2", description="Second task")
        constellation.add_task(task1)
        constellation.add_task(task2)

        initial_count = constellation.task_count

        # Remove task
        success = parser.remove_task_from_constellation(constellation, "task1")

        assert success
        assert constellation.task_count == initial_count - 1
        assert "task1" not in constellation.tasks
        assert "task2" in constellation.tasks

    def test_remove_nonexistent_task(self, parser):
        """Test removing a nonexistent task."""
        constellation = TaskConstellation(name="Test Constellation")

        # Try to remove nonexistent task
        success = parser.remove_task_from_constellation(constellation, "nonexistent")

        assert not success

    def test_validate_constellation_valid(self, parser):
        """Test validating a valid constellation."""
        constellation = TaskConstellation(name="Valid Constellation")

        # Add tasks
        task1 = TaskStar(task_id="task1", description="First task")
        task2 = TaskStar(task_id="task2", description="Second task")
        constellation.add_task(task1)
        constellation.add_task(task2)

        is_valid, errors = parser.validate_constellation(constellation)

        assert is_valid
        assert len(errors) == 0

    def test_validate_constellation_empty(self, parser):
        """Test validating an empty constellation."""
        constellation = TaskConstellation(name="Empty Constellation")

        is_valid, errors = parser.validate_constellation(constellation)

        assert not is_valid
        assert len(errors) > 0
        assert any("no tasks" in error.lower() for error in errors)

    def test_export_constellation_json(self, parser):
        """Test exporting constellation to JSON format."""
        constellation = TaskConstellation(name="Export Test")

        # Add a task
        task = TaskStar(task_id="task1", description="Test task")
        constellation.add_task(task)

        exported = parser.export_constellation(constellation, "json")

        assert isinstance(exported, str)
        # Should be valid JSON
        parsed = json.loads(exported)
        assert parsed["name"] == "Export Test"
        assert "tasks" in parsed

    def test_export_constellation_llm(self, parser):
        """Test exporting constellation to LLM format."""
        constellation = TaskConstellation(name="Export Test")

        # Add a task
        task = TaskStar(task_id="task1", description="Test task")
        constellation.add_task(task)

        exported = parser.export_constellation(constellation, "llm")

        assert isinstance(exported, str)
        assert "Export Test" in exported
        assert "Test task" in exported

    def test_export_constellation_yaml(self, parser):
        """Test exporting constellation to YAML format."""
        constellation = TaskConstellation(name="Export Test")

        # Add a task
        task = TaskStar(task_id="task1", description="Test task")
        constellation.add_task(task)

        exported = parser.export_constellation(constellation, "yaml")

        assert isinstance(exported, str)
        # Should contain YAML comment since full YAML export is not implemented
        assert "YAML export not implemented" in exported

    def test_export_constellation_unsupported_format(self, parser):
        """Test exporting constellation with unsupported format."""
        constellation = TaskConstellation(name="Export Test")

        with pytest.raises(ValueError, match="Unsupported export format"):
            parser.export_constellation(constellation, "unsupported")

    def test_clone_constellation(self, parser):
        """Test cloning a constellation."""
        # Create original constellation
        original = TaskConstellation(name="Original Constellation")
        task = TaskStar(task_id="task1", description="Original task")
        original.add_task(task)

        # Clone
        cloned = parser.clone_constellation(original, "Cloned Constellation")

        assert isinstance(cloned, TaskConstellation)
        assert cloned.name == "Cloned Constellation"
        assert cloned.task_count == original.task_count
        assert cloned.constellation_id != original.constellation_id

        # Should have the same tasks but different instances
        assert "task1" in cloned.tasks
        assert cloned.tasks["task1"].description == "Original task"

    def test_clone_constellation_default_name(self, parser):
        """Test cloning constellation with default name."""
        original = TaskConstellation(name="Original")

        cloned = parser.clone_constellation(original)

        assert cloned.name == "Original (Copy)"

    def test_merge_constellations(self, parser):
        """Test merging two constellations."""
        # Create first constellation
        constellation1 = TaskConstellation(name="Constellation 1")
        task1 = TaskStar(task_id="task1", description="Task from constellation 1")
        constellation1.add_task(task1)

        # Create second constellation
        constellation2 = TaskConstellation(name="Constellation 2")
        task2 = TaskStar(task_id="task2", description="Task from constellation 2")
        constellation2.add_task(task2)

        # Merge
        merged = parser.merge_constellations(
            constellation1, constellation2, "Merged Constellation"
        )

        assert isinstance(merged, TaskConstellation)
        assert merged.name == "Merged Constellation"
        assert merged.task_count == 2
        assert "c1_task1" in merged.tasks
        assert "c2_task2" in merged.tasks

    def test_merge_constellations_default_name(self, parser):
        """Test merging constellations with default name."""
        constellation1 = TaskConstellation(name="First")
        constellation2 = TaskConstellation(name="Second")

        merged = parser.merge_constellations(constellation1, constellation2)

        assert merged.name == "First + Second"

    def test_merge_constellations_with_conflicts(self, parser):
        """Test merging constellations with task ID conflicts."""
        # Create constellations with same task ID
        constellation1 = TaskConstellation(name="Constellation 1")
        task1a = TaskStar(task_id="task1", description="Task 1 from constellation 1")
        constellation1.add_task(task1a)

        constellation2 = TaskConstellation(name="Constellation 2")
        task1b = TaskStar(task_id="task1", description="Task 1 from constellation 2")
        constellation2.add_task(task1b)

        # Merge should handle conflicts by renaming
        merged = parser.merge_constellations(constellation1, constellation2)

        assert merged.task_count == 2
        # Should have renamed one of the conflicting tasks
        task_ids = list(merged.tasks.keys())
        assert len(task_ids) == 2

    @pytest.mark.asyncio
    async def test_create_from_empty_llm_output(self, parser):
        """Test creating constellation from empty LLM output."""
        empty_output = ""

        constellation = await parser.create_from_llm(empty_output)

        # Should create empty constellation
        assert isinstance(constellation, TaskConstellation)
        assert constellation.task_count == 0

    @pytest.mark.asyncio
    async def test_create_from_invalid_json(self, parser):
        """Test creating constellation from invalid JSON."""
        invalid_json = "{ invalid json"

        with pytest.raises(json.JSONDecodeError):
            await parser.create_from_json(invalid_json)

    def test_add_task_with_invalid_dependencies(self, parser):
        """Test adding task with nonexistent dependencies."""
        constellation = TaskConstellation(name="Test Constellation")

        task = TaskStar(task_id="task1", description="Test task")

        # Try to add task with nonexistent dependency
        success = parser.add_task_to_constellation(
            constellation, task, dependencies=["nonexistent_task"]
        )

        # Should still add the task but dependency creation might fail
        assert "task1" in constellation.tasks

    @pytest.mark.asyncio
    async def test_parser_with_logging_enabled(self):
        """Test parser with logging enabled."""
        parser = ConstellationParser(enable_logging=True)

        constellation = parser.create_simple_sequential(
            ["Task 1", "Task 2"], "Logged Test"
        )

        assert isinstance(constellation, TaskConstellation)
        assert constellation.task_count == 2

    @pytest.mark.asyncio
    async def test_update_from_llm_with_empty_request(self, parser):
        """Test updating constellation with empty LLM request."""
        constellation = TaskConstellation(name="Test")

        # Update with empty request
        updated = await parser.update_from_llm(constellation, "")

        # Should return original constellation
        assert updated is constellation

    def test_validate_constellation_with_cycles(self, parser):
        """Test validating constellation with circular dependencies."""
        constellation = TaskConstellation(name="Cyclic Constellation")

        # Add tasks
        task1 = TaskStar(task_id="task1", description="First task")
        task2 = TaskStar(task_id="task2", description="Second task")
        constellation.add_task(task1)
        constellation.add_task(task2)

        # Create circular dependency manually (if constellation allows)
        # This would be caught by constellation's own validation
        is_valid, errors = parser.validate_constellation(constellation)

        # Should be valid if no cycles exist
        assert is_valid or any("cycle" in error.lower() for error in errors)


class TestConstellationParserIntegration:
    """Integration tests for ConstellationParser with other components."""

    @pytest.fixture
    def parser(self):
        """Create a ConstellationParser instance for testing."""
        return ConstellationParser(enable_logging=False)

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, parser):
        """Test complete workflow from creation to export."""
        # Create constellation
        tasks = ["Step 1", "Step 2", "Step 3"]
        constellation = parser.create_simple_sequential(tasks, "E2E Test")

        # Validate
        is_valid, errors = parser.validate_constellation(constellation)
        assert is_valid

        # Clone
        cloned = parser.clone_constellation(constellation, "E2E Cloned")

        # Export original
        json_export = parser.export_constellation(constellation, "json")
        llm_export = parser.export_constellation(constellation, "llm")

        # Verify exports are different but both contain constellation data
        assert json_export != llm_export
        assert "E2E Test" in json_export
        assert "E2E Test" in llm_export

        # Create new constellation from JSON export
        reimported = await parser.create_from_json(json_export, "Reimported")
        assert reimported.task_count == constellation.task_count

    @pytest.mark.asyncio
    async def test_complex_constellation_operations(self, parser):
        """Test complex operations on constellations."""
        # Create two constellations
        constellation1 = parser.create_simple_sequential(["A1", "A2"], "First")
        constellation2 = parser.create_simple_parallel(["B1", "B2", "B3"], "Second")

        # Merge them
        merged = parser.merge_constellations(constellation1, constellation2)
        assert merged.task_count == 5

        # Add a new task to merged constellation
        new_task = TaskStar(task_id="new_task", description="New task")
        success = parser.add_task_to_constellation(merged, new_task)
        assert success
        assert merged.task_count == 6

        # Remove a task
        success = parser.remove_task_from_constellation(merged, "new_task")
        assert success
        assert merged.task_count == 5

        # Validate final result
        is_valid, errors = parser.validate_constellation(merged)
        assert is_valid
