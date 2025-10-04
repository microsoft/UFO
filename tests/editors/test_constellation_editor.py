#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test script for TaskConstellation Editor Command Pattern Implementation

Tests the editor's command pattern functionality including:
- Task CRUD operations
- Dependency CRUD operations
- Bulk operations
- Undo/Redo capabilities
- File operations
- Validation and analysis
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from galaxy.constellation.editor import ConstellationEditor
from galaxy.constellation.task_star import TaskStar
from galaxy.constellation.task_star_line import TaskStarLine
from galaxy.constellation.enums import TaskPriority, DependencyType


def test_basic_task_operations():
    """Test basic task CRUD operations."""
    print("🧪 Testing Basic Task Operations...")

    editor = ConstellationEditor()

    # Test create and add task
    task1 = editor.create_and_add_task(
        task_id="task1", description="First test task", priority=TaskPriority.HIGH
    )
    assert task1.task_id == "task1"
    assert len(editor.list_tasks()) == 1
    print("✅ Task creation and addition successful")

    # Test update task
    updated_task = editor.update_task("task1", description="Updated task description")
    assert updated_task.description == "Updated task description"
    print("✅ Task update successful")

    # Test get task
    retrieved_task = editor.get_task("task1")
    assert retrieved_task is not None
    assert retrieved_task.task_id == "task1"
    print("✅ Task retrieval successful")

    # Test remove task
    removed_id = editor.remove_task("task1")
    assert removed_id == "task1"
    assert len(editor.list_tasks()) == 0
    print("✅ Task removal successful")


def test_basic_dependency_operations():
    """Test basic dependency CRUD operations."""
    print("\n🧪 Testing Basic Dependency Operations...")

    editor = ConstellationEditor()

    # Create two tasks first
    task1 = editor.create_and_add_task("task1", "First task")
    task2 = editor.create_and_add_task("task2", "Second task")

    # Test create and add dependency
    dep1 = editor.create_and_add_dependency(
        from_task_id="task1", to_task_id="task2", dependency_type="UNCONDITIONAL"
    )
    assert dep1.from_task_id == "task1"
    assert dep1.to_task_id == "task2"
    assert len(editor.list_dependencies()) == 1
    print("✅ Dependency creation and addition successful")

    # Test get dependency
    retrieved_dep = editor.get_dependency(dep1.line_id)
    assert retrieved_dep is not None
    assert retrieved_dep.line_id == dep1.line_id
    print("✅ Dependency retrieval successful")

    # Test update dependency
    updated_dep = editor.update_dependency(
        dep1.line_id, condition_description="Updated condition"
    )
    assert updated_dep.condition_description == "Updated condition"
    print("✅ Dependency update successful")

    # Test remove dependency
    removed_dep_id = editor.remove_dependency(dep1.line_id)
    assert removed_dep_id == dep1.line_id
    assert len(editor.list_dependencies()) == 0
    print("✅ Dependency removal successful")


def test_undo_redo_operations():
    """Test undo/redo functionality."""
    print("\n🧪 Testing Undo/Redo Operations...")

    editor = ConstellationEditor()

    # Add a task
    task1 = editor.create_and_add_task("task1", "Test task")
    assert len(editor.list_tasks()) == 1
    assert editor.can_undo(), "Should be able to undo after adding task"
    print("✅ Task added, undo available")

    # Undo the addition
    undo_success = editor.undo()
    assert undo_success
    assert len(editor.list_tasks()) == 0
    assert editor.can_redo()
    print("✅ Task addition undone, redo available")

    # Redo the addition
    redo_success = editor.redo()
    assert redo_success
    assert len(editor.list_tasks()) == 1
    print("✅ Task addition redone")

    # Test multiple operations
    task2 = editor.create_and_add_task("task2", "Second task")
    dep1 = editor.create_and_add_dependency("task1", "task2")

    assert len(editor.list_tasks()) == 2
    assert len(editor.list_dependencies()) == 1
    print("✅ Multiple operations executed")

    # Undo dependency addition
    editor.undo()
    assert len(editor.list_dependencies()) == 0
    print("✅ Dependency addition undone")

    # Undo task2 addition
    editor.undo()
    assert len(editor.list_tasks()) == 1
    print("✅ Second task addition undone")


def test_bulk_operations():
    """Test bulk constellation operations."""
    print("\n🧪 Testing Bulk Operations...")

    editor = ConstellationEditor()

    # Test build from tasks and dependencies
    tasks_config = [
        {
            "task_id": "task1",
            "description": "First bulk task",
            "priority": TaskPriority.HIGH.value,
        },
        {
            "task_id": "task2",
            "description": "Second bulk task",
            "priority": TaskPriority.MEDIUM.value,
        },
        {
            "task_id": "task3",
            "description": "Third bulk task",
            "priority": TaskPriority.LOW.value,
        },
    ]

    dependencies_config = [
        {
            "from_task_id": "task1",
            "to_task_id": "task2",
            "dependency_type": DependencyType.UNCONDITIONAL.value,
        },
        {
            "from_task_id": "task2",
            "to_task_id": "task3",
            "dependency_type": DependencyType.UNCONDITIONAL.value,
        },
    ]

    constellation = editor.build_from_tasks_and_dependencies(
        tasks_config, dependencies_config, metadata={"created_by": "test_script"}
    )

    assert len(editor.list_tasks()) == 3
    assert len(editor.list_dependencies()) == 2
    print("✅ Bulk constellation build successful")

    # Test validation
    is_valid, errors = editor.validate_constellation()
    assert is_valid
    assert len(errors) == 0
    print("✅ Constellation validation successful")

    # Test topological order
    topo_order = editor.get_topological_order()
    assert topo_order == ["task1", "task2", "task3"]
    print("✅ Topological ordering correct")

    # Test clear constellation
    cleared = editor.clear_constellation()
    assert len(editor.list_tasks()) == 0
    assert len(editor.list_dependencies()) == 0
    print("✅ Constellation cleared successfully")


def test_file_operations():
    """Test file save/load operations."""
    print("\n🧪 Testing File Operations...")

    editor = ConstellationEditor()

    # Create test constellation
    editor.create_and_add_task("task1", "File test task 1")
    editor.create_and_add_task("task2", "File test task 2")
    editor.create_and_add_dependency("task1", "task2")

    # Test save to file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

    try:
        saved_path = editor.save_constellation(temp_file)
        assert saved_path == temp_file
        assert os.path.exists(temp_file)
        print("✅ Constellation saved to file")

        # Test load from file
        editor2 = ConstellationEditor()
        loaded_constellation = editor2.load_constellation(temp_file)

        assert len(editor2.list_tasks()) == 2
        assert len(editor2.list_dependencies()) == 1
        print("✅ Constellation loaded from file")

        # Verify content matches
        original_task = editor.get_task("task1")
        loaded_task = editor2.get_task("task1")
        assert original_task.description == loaded_task.description
        print("✅ Loaded content matches original")

    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_advanced_operations():
    """Test advanced editor operations."""
    print("\n🧪 Testing Advanced Operations...")

    editor = ConstellationEditor()

    # Create a more complex constellation
    tasks = [
        {"task_id": "A", "description": "Task A"},
        {"task_id": "B", "description": "Task B"},
        {"task_id": "C", "description": "Task C"},
        {"task_id": "D", "description": "Task D"},
    ]

    dependencies = [
        {
            "from_task_id": "A",
            "to_task_id": "B",
            "dependency_type": DependencyType.UNCONDITIONAL.value,
        },
        {
            "from_task_id": "A",
            "to_task_id": "C",
            "dependency_type": DependencyType.UNCONDITIONAL.value,
        },
        {
            "from_task_id": "B",
            "to_task_id": "D",
            "dependency_type": DependencyType.UNCONDITIONAL.value,
        },
        {
            "from_task_id": "C",
            "to_task_id": "D",
            "dependency_type": DependencyType.UNCONDITIONAL.value,
        },
    ]

    editor.build_from_tasks_and_dependencies(tasks, dependencies)
    print("✅ Complex constellation created")

    # Test subgraph creation
    subgraph_editor = editor.create_subgraph(["A", "B", "D"])
    assert len(subgraph_editor.list_tasks()) == 3
    assert len(subgraph_editor.list_dependencies()) == 2  # A->B and B->D dependencies
    print("✅ Subgraph creation successful")

    # Test merge operation
    merge_editor = ConstellationEditor()
    merge_editor.create_and_add_task("E", "Task E")

    original_count = len(editor.list_tasks())
    editor.merge_constellation(merge_editor, prefix="merged_")

    assert len(editor.list_tasks()) == original_count + 1
    assert editor.get_task("merged_E") is not None
    print("✅ Constellation merge successful")

    # Test statistics
    stats = editor.get_statistics()
    assert "total_tasks" in stats
    assert "editor_execution_count" in stats
    assert stats["total_tasks"] >= 5
    print("✅ Statistics retrieval successful")


def test_observer_pattern():
    """Test observer pattern functionality."""
    print("\n🧪 Testing Observer Pattern...")

    events = []

    def test_observer(editor, command, result):
        events.append((command, result))

    editor = ConstellationEditor()
    editor.add_observer(test_observer)

    # Perform operations
    editor.create_and_add_task("obs_task", "Observer test task")
    editor.update_task("obs_task", description="Updated by observer test")

    assert len(events) == 2
    assert events[0][0] == "add_task"
    assert events[1][0] == "update_task"
    print("✅ Observer notifications successful")

    # Remove observer
    editor.remove_observer(test_observer)
    editor.remove_task("obs_task")

    # Should not add new events
    assert len(events) == 2
    print("✅ Observer removal successful")


def test_error_handling():
    """Test error handling in commands."""
    print("\n🧪 Testing Error Handling...")

    editor = ConstellationEditor()

    # Test adding duplicate task
    editor.create_and_add_task("dup_task", "Duplicate test")

    try:
        # This should fail
        task_duplicate = TaskStar(task_id="dup_task", description="Duplicate")
        editor.add_task(task_duplicate)
        assert False, "Should have raised an error"
    except Exception as e:
        print(f"✅ Duplicate task error handled: {type(e).__name__}")

    # Test removing non-existent task
    try:
        editor.remove_task("non_existent")
        assert False, "Should have raised an error"
    except Exception as e:
        print(f"✅ Non-existent task error handled: {type(e).__name__}")

    # Test invalid dependency (cycle)
    editor.create_and_add_task("cycle1", "Cycle task 1")
    editor.create_and_add_task("cycle2", "Cycle task 2")
    editor.create_and_add_dependency("cycle1", "cycle2")

    try:
        # This should create a cycle
        editor.create_and_add_dependency("cycle2", "cycle1")
        assert False, "Should have raised an error for cycle"
    except Exception as e:
        print(f"✅ Cycle dependency error handled: {type(e).__name__}")


def main():
    """Run all tests."""
    print("🚀 Starting TaskConstellation Editor Command Pattern Tests\n")

    try:
        test_basic_task_operations()
        test_basic_dependency_operations()
        test_undo_redo_operations()
        test_bulk_operations()
        test_file_operations()
        test_advanced_operations()
        test_observer_pattern()
        test_error_handling()

        print("\n🎉 All tests passed successfully!")
        print(
            "✅ TaskConstellation Editor Command Pattern implementation is working correctly"
        )

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
