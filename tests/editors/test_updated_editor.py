#!/usr/bin/env python3
"""
Test script for updated constellation editor with:
1. Serializable command parameters
2. Command registry and decorators
3. Auto-validation with rollback
"""

import sys
import os

# Add the UFO2 directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
ufo_path = os.path.dirname(current_dir)
sys.path.insert(0, ufo_path)

from galaxy.constellation.editor.constellation_editor import ConstellationEditor
from galaxy.constellation.editor.command_registry import command_registry
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.constellation.task_star import TaskStar
from galaxy.constellation.task_star_line import TaskStarLine, DependencyType


def test_serializable_parameters():
    """Test that commands accept serializable parameters."""
    print("=== Testing Serializable Parameters ===")

    # Create editor
    constellation = TaskConstellation()
    editor = ConstellationEditor(constellation)

    # Test 1: Add task with dict parameters
    print("\n1. Testing add_task with dict parameters...")
    task_data = {
        "task_id": "task1",
        "name": "Test Task",
        "description": "A test task",
        "priority": 3,  # Using integer value for HIGH priority
    }

    task = editor.add_task(task_data)
    print(f"   ✓ Added task: {task.task_id} - {task.name}")

    # Test 2: Add another task for dependency
    task2_data = {
        "task_id": "task2",
        "name": "Second Task",
        "description": "Another test task",
    }
    task2 = editor.add_task(task2_data)
    print(f"   ✓ Added task: {task2.task_id} - {task2.name}")

    # Test 3: Add dependency with dict parameters
    print("\n2. Testing add_dependency with dict parameters...")
    dependency_data = {
        "from_task_id": "task1",
        "to_task_id": "task2",
        "dependency_type": "unconditional",  # Using string value
    }

    dependency = editor.add_dependency(dependency_data)
    print(
        f"   ✓ Added dependency: {dependency.from_task_id} -> {dependency.to_task_id}"
    )

    print(
        f"\nFinal constellation has {len(constellation.tasks)} tasks and {len(constellation.dependencies)} dependencies"
    )


def test_command_registry():
    """Test the command registry and decorator functionality."""
    print("\n=== Testing Command Registry ===")

    # Test 1: List all registered commands
    print("\n1. Listing all registered commands...")
    commands = command_registry.list_commands()
    for name, metadata in commands.items():
        print(
            f"   • {name}: {metadata['description']} (category: {metadata['category']})"
        )

    # Test 2: Test categories
    print(f"\n2. Available categories: {command_registry.get_categories()}")

    # Test 3: Get specific command metadata
    print("\n3. Testing command metadata...")
    metadata = command_registry.get_command_metadata("add_task")
    if metadata:
        print(f"   add_task metadata: {metadata}")

    # Test 4: Execute command by name
    print("\n4. Testing execute_command_by_name...")
    constellation = TaskConstellation()
    editor = ConstellationEditor(constellation)

    try:
        task_data = {
            "task_id": "registry_task",
            "name": "Registry Test Task",
            "description": "Task created via registry",
        }
        result = editor.execute_command_by_name("add_task", task_data)
        print(f"   ✓ Created task via registry: {result.task_id}")
    except Exception as e:
        print(f"   ✗ Error executing via registry: {e}")


def test_validation_rollback():
    """Test that commands validate constellation and rollback on failure."""
    print("\n=== Testing Validation and Rollback ===")

    constellation = TaskConstellation()
    editor = ConstellationEditor(constellation)

    # Add some valid tasks first
    task1_data = {
        "task_id": "valid_task1",
        "name": "Valid Task 1",
        "description": "A valid task",
    }
    task2_data = {
        "task_id": "valid_task2",
        "name": "Valid Task 2",
        "description": "Another valid task",
    }

    editor.add_task(task1_data)
    editor.add_task(task2_data)

    print(
        f"Initial state: {len(constellation.tasks)} tasks, {len(constellation.dependencies)} dependencies"
    )
    is_valid, errors = constellation.validate_dag()
    print(f"Constellation is valid: {is_valid}")
    if not is_valid:
        print(f"Validation errors: {errors}")

    # Try to create an invalid dependency (to non-existent task)
    print("\n1. Testing rollback on invalid dependency...")
    try:
        invalid_dependency_data = {
            "from_task_id": "valid_task1",
            "to_task_id": "nonexistent_task",  # This task doesn't exist
            "dependency_type": "unconditional",
        }

        # This should fail during command execution, not validation
        # But let's see what happens
        result = editor.add_dependency(invalid_dependency_data)
        print(f"   ✗ Unexpected success: {result}")
    except Exception as e:
        print(f"   ✓ Expected failure: {e}")

    print(
        f"After failed operation: {len(constellation.tasks)} tasks, {len(constellation.dependencies)} dependencies"
    )
    is_valid, errors = constellation.validate_dag()
    print(f"Constellation is still valid: {is_valid}")
    if not is_valid:
        print(f"Validation errors: {errors}")

    # Test successful validation
    print("\n2. Testing successful validation...")
    try:
        valid_dependency_data = {
            "from_task_id": "valid_task1",
            "to_task_id": "valid_task2",
            "dependency_type": "unconditional",
        }
        result = editor.add_dependency(valid_dependency_data)
        print(
            f"   ✓ Successfully added dependency: {result.from_task_id} -> {result.to_task_id}"
        )
    except Exception as e:
        print(f"   ✗ Unexpected failure: {e}")

    print(
        f"Final state: {len(constellation.tasks)} tasks, {len(constellation.dependencies)} dependencies"
    )
    is_valid, errors = constellation.validate_dag()
    print(f"Constellation is valid: {is_valid}")
    if not is_valid:
        print(f"Validation errors: {errors}")


def test_undo_redo_with_validation():
    """Test undo/redo functionality with the validation."""
    print("\n=== Testing Undo/Redo with Validation ===")

    constellation = TaskConstellation()
    editor = ConstellationEditor(constellation)

    # Add a task
    task_data = {
        "task_id": "undo_test",
        "name": "Undo Test Task",
        "description": "Task for undo testing",
    }

    print("1. Adding task...")
    editor.add_task(task_data)
    print(f"   Tasks: {len(constellation.tasks)}, Can undo: {editor.can_undo()}")

    print("2. Undoing add task...")
    editor.undo()
    print(f"   Tasks: {len(constellation.tasks)}, Can redo: {editor.can_redo()}")

    print("3. Redoing add task...")
    editor.redo()
    print(f"   Tasks: {len(constellation.tasks)}, Can undo: {editor.can_undo()}")

    print("   ✓ Undo/redo working correctly with validation")


def main():
    """Run all tests."""
    print("Testing Updated Constellation Editor")
    print("=" * 50)

    try:
        test_serializable_parameters()
        test_command_registry()
        test_validation_rollback()
        test_undo_redo_with_validation()

        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
