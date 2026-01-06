"""
Tests for ConstellationUpdater class.
Validates constellation update and modification functionality.
"""

import pytest
from unittest.mock import Mock

from galaxy.constellation.parsers.constellation_updater import ConstellationUpdater
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.constellation.task_star import TaskStar, TaskPriority, TaskStatus
from galaxy.constellation.task_star_line import TaskStarLine


class TestConstellationUpdater:
    """Test ConstellationUpdater functionality."""

    @pytest.fixture
    def updater(self):
        """Create a ConstellationUpdater instance."""
        return ConstellationUpdater()

    @pytest.fixture
    def sample_constellation(self):
        """Create a sample constellation for testing."""
        constellation = TaskConstellation(name="Test Constellation")

        task1 = TaskStar(task_id="task_1", description="First task")
        task2 = TaskStar(task_id="task_2", description="Second task")
        constellation.add_task(task1)
        constellation.add_task(task2)

        return constellation

    def test_add_tasks(self, updater, sample_constellation):
        """Test adding tasks to a constellation."""
        descriptions = ["Third task", "Fourth task"]

        created_tasks = updater.add_tasks(
            sample_constellation, descriptions, priority=TaskPriority.HIGH
        )

        assert len(created_tasks) == 2
        assert len(sample_constellation.tasks) == 4

        # Check that tasks were added with correct properties
        for task in created_tasks:
            assert task.priority == TaskPriority.HIGH
            assert task.task_id in sample_constellation.tasks

    def test_remove_tasks(self, updater, sample_constellation):
        """Test removing tasks from a constellation."""
        original_count = len(sample_constellation.tasks)

        updater.remove_tasks(sample_constellation, ["task_1"])

        assert len(sample_constellation.tasks) == original_count - 1
        assert "task_1" not in sample_constellation.tasks
        assert "task_2" in sample_constellation.tasks

    def test_remove_tasks_with_dependencies(self, updater, sample_constellation):
        """Test removing tasks also removes related dependencies."""
        # Add a dependency
        dep = TaskStarLine.create_unconditional("task_1", "task_2", "Test dependency")
        sample_constellation.add_dependency(dep)

        assert len(sample_constellation.dependencies) == 1

        # Remove task_1, which should also remove the dependency
        updater.remove_tasks(sample_constellation, ["task_1"], remove_dependencies=True)

        assert "task_1" not in sample_constellation.tasks
        assert len(sample_constellation.dependencies) == 0

    def test_add_dependencies(self, updater, sample_constellation):
        """Test adding dependencies to a constellation."""
        dep_specs = [
            {
                "from_task_id": "task_1",
                "to_task_id": "task_2",
                "description": "Sequential dependency",
            }
        ]

        created_deps = updater.add_dependencies(sample_constellation, dep_specs)

        assert len(created_deps) == 1
        assert len(sample_constellation.dependencies) == 1

        dep = created_deps[0]
        assert dep.from_task_id == "task_1"
        assert dep.to_task_id == "task_2"

    def test_add_dependencies_invalid_tasks(self, updater, sample_constellation):
        """Test adding dependencies with invalid task IDs."""
        dep_specs = [
            {
                "from_task_id": "nonexistent_task",
                "to_task_id": "task_2",
                "description": "Invalid dependency",
            }
        ]

        created_deps = updater.add_dependencies(sample_constellation, dep_specs)

        assert len(created_deps) == 0
        assert len(sample_constellation.dependencies) == 0

    def test_update_from_llm_output_add_task(self, updater, sample_constellation):
        """Test updating constellation from LLM output with add task instruction."""
        llm_output = """
        ADD TASK: New task from LLM
        """

        original_count = len(sample_constellation.tasks)
        updater.update_from_llm_output(sample_constellation, llm_output)

        assert len(sample_constellation.tasks) == original_count + 1

    def test_update_from_llm_output_remove_task(self, updater, sample_constellation):
        """Test updating constellation from LLM output with remove task instruction."""
        llm_output = """
        REMOVE TASK: task_1
        """

        # Test with preserve_existing=False to allow removal
        updater.update_from_llm_output(
            sample_constellation, llm_output, preserve_existing=False
        )

        assert "task_1" not in sample_constellation.tasks

    def test_update_from_llm_output_add_dependency(self, updater, sample_constellation):
        """Test updating constellation from LLM output with add dependency instruction."""
        llm_output = """
        ADD DEPENDENCY: task_1 -> task_2
        """

        updater.update_from_llm_output(sample_constellation, llm_output)

        assert len(sample_constellation.dependencies) == 1

    def test_parse_llm_update_instructions(self, updater):
        """Test parsing LLM output for update instructions."""
        llm_output = """
        ADD TASK: First new task
        ADD TASK: Second new task
        REMOVE TASK: old_task
        ADD DEPENDENCY: task_1 -> task_2
        """

        instructions = updater._parse_llm_update_instructions(llm_output)

        assert len(instructions) == 4
        assert instructions[0]["type"] == "add_task"
        assert instructions[0]["description"] == "First new task"
        assert instructions[1]["type"] == "add_task"
        assert instructions[2]["type"] == "remove_task"
        assert instructions[3]["type"] == "add_dependency"

    def test_parse_dependency_spec(self, updater):
        """Test parsing dependency specification strings."""
        spec = updater._parse_dependency_spec("task_1 -> task_2")

        assert spec is not None
        assert spec["from_task_id"] == "task_1"
        assert spec["to_task_id"] == "task_2"

    def test_parse_dependency_spec_invalid(self, updater):
        """Test parsing invalid dependency specification."""
        spec = updater._parse_dependency_spec("invalid spec")
        assert spec is None

    def test_create_dependency_from_spec(self, updater, sample_constellation):
        """Test creating dependency from specification."""
        dep_spec = {
            "from_task_id": "task_1",
            "to_task_id": "task_2",
            "description": "Test dependency",
        }

        dep = updater._create_dependency_from_spec(sample_constellation, dep_spec)

        assert dep is not None
        assert dep.from_task_id == "task_1"
        assert dep.to_task_id == "task_2"

    def test_create_dependency_from_spec_invalid(self, updater, sample_constellation):
        """Test creating dependency with invalid task IDs."""
        dep_spec = {"from_task_id": "nonexistent", "to_task_id": "task_2"}

        dep = updater._create_dependency_from_spec(sample_constellation, dep_spec)
        assert dep is None

    def test_remove_task_dependencies(self, updater, sample_constellation):
        """Test removing all dependencies related to a task."""
        # Add some dependencies
        dep1 = TaskStarLine.create_unconditional("task_1", "task_2", "Dep 1")
        sample_constellation.add_dependency(dep1)

        # Add a task and dependency that shouldn't be affected
        task3 = TaskStar(task_id="task_3", description="Third task")
        sample_constellation.add_task(task3)
        dep2 = TaskStarLine.create_unconditional("task_2", "task_3", "Dep 2")
        sample_constellation.add_dependency(dep2)

        assert len(sample_constellation.dependencies) == 2

        # Remove dependencies for task_1
        updater._remove_task_dependencies(sample_constellation, "task_1")

        assert len(sample_constellation.dependencies) == 1
        remaining_dep = list(sample_constellation.dependencies.values())[0]
        assert remaining_dep.from_task_id == "task_2"
        assert remaining_dep.to_task_id == "task_3"

    def test_updater_with_logger(self):
        """Test updater functionality with logger."""
        mock_logger = Mock()
        updater = ConstellationUpdater(logger=mock_logger)
        constellation = TaskConstellation(name="Logger Test")

        updater.add_tasks(constellation, ["Test task"])

        # Verify logger was called
        mock_logger.info.assert_called()

    def test_preserve_existing_tasks(self, updater, sample_constellation):
        """Test that preserve_existing flag prevents task removal."""
        llm_output = "REMOVE TASK: task_1"

        # With preserve_existing=True (default), task should not be removed
        updater.update_from_llm_output(
            sample_constellation, llm_output, preserve_existing=True
        )

        assert "task_1" in sample_constellation.tasks

    def test_alternative_dependency_spec_format(self, updater, sample_constellation):
        """Test adding dependencies with alternative spec format."""
        dep_specs = [
            {
                "predecessor_id": "task_1",  # Alternative format
                "successor_id": "task_2",
                "description": "Alternative format dependency",
            }
        ]

        created_deps = updater.add_dependencies(sample_constellation, dep_specs)

        assert len(created_deps) == 1
        dep = created_deps[0]
        assert dep.from_task_id == "task_1"
        assert dep.to_task_id == "task_2"
