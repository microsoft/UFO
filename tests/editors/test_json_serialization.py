#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for TaskStar and TaskStarLine JSON serialization/deserialization.

This script tests the to_json() and from_json() methods of both classes
to ensure they work correctly with various data types and edge cases.
"""

import os
import tempfile
import json
from datetime import datetime, timezone

# Import the classes to test
from galaxy.constellation.task_star import TaskStar
from galaxy.constellation.task_star_line import TaskStarLine
from galaxy.constellation.enums import (
    TaskStatus,
    TaskPriority,
    DeviceType,
    DependencyType,
)


def test_task_star_json():
    """Test TaskStar JSON serialization and deserialization."""
    print("=" * 60)
    print("Testing TaskStar JSON Serialization/Deserialization")
    print("=" * 60)

    # Create a TaskStar instance with various data types
    task = TaskStar(
        name="Test Task",
        description="This is a test task for JSON serialization",
        tips=["Tip 1: Be careful", "Tip 2: Double-check results"],
        target_device_id="device_001",
        device_type=DeviceType.WINDOWS,
        priority=TaskPriority.HIGH,
        timeout=300.0,
        retry_count=3,
        task_data={
            "string_value": "test",
            "number_value": 42,
            "list_value": [1, 2, 3],
            "dict_value": {"nested": "data"},
            "bool_value": True,
        },
        expected_output_type="json",
    )

    # Simulate some execution data
    task.start_execution()
    task.complete_with_success({"result": "success", "data": [1, 2, 3]})

    print(f"Original TaskStar:")
    print(f"  ID: {task.task_id}")
    print(f"  Name: {task.name}")
    print(f"  Status: {task.status}")
    print(f"  Priority: {task.priority}")
    print(f"  Device Type: {task.device_type}")
    print(f"  Result: {task.result}")
    print()

    # Test 1: to_json() - JSON string generation
    print("Test 1: Converting to JSON string...")
    try:
        json_str = task.to_json()
        print("✓ JSON string generation successful")
        print(f"JSON length: {len(json_str)} characters")

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        print("✓ Generated JSON is valid")
        print(f"JSON contains {len(parsed)} fields")
    except Exception as e:
        print(f"✗ JSON string generation failed: {e}")
        return False

    # Test 2: from_json() - JSON string parsing
    print("\nTest 2: Creating TaskStar from JSON string...")
    try:
        restored_task = TaskStar.from_json(json_data=json_str)
        print("✓ TaskStar creation from JSON string successful")

        # Verify data integrity
        assert restored_task.task_id == task.task_id
        assert restored_task.name == task.name
        assert restored_task.description == task.description
        assert restored_task.status == task.status
        assert restored_task.priority == task.priority
        assert restored_task.device_type == task.device_type
        print("✓ Data integrity verified")
    except Exception as e:
        print(f"✗ TaskStar creation from JSON string failed: {e}")
        return False

    # Test 3: File-based serialization
    print("\nTest 3: File-based JSON serialization...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

    try:
        # Save to file
        task.to_json(save_path=temp_file)
        print(f"✓ TaskStar saved to file: {temp_file}")

        # Load from file
        file_task = TaskStar.from_json(file_path=temp_file)
        print("✓ TaskStar loaded from file")

        # Verify data integrity
        assert file_task.task_id == task.task_id
        assert file_task.name == task.name
        print("✓ File-based data integrity verified")

        # Clean up
        os.unlink(temp_file)
        print("✓ Temporary file cleaned up")
    except Exception as e:
        print(f"✗ File-based serialization failed: {e}")
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        return False

    print("\n🎉 All TaskStar JSON tests passed!")
    return True


def test_task_star_line_json():
    """Test TaskStarLine JSON serialization and deserialization."""
    print("\n" + "=" * 60)
    print("Testing TaskStarLine JSON Serialization/Deserialization")
    print("=" * 60)

    # Create a TaskStarLine instance
    def condition_evaluator(result):
        return result is not None and result.get("success", False)

    line = TaskStarLine.create_conditional(
        from_task_id="task_001",
        to_task_id="task_002",
        condition_description="Task 001 must complete successfully",
        condition_evaluator=condition_evaluator,
    )

    # Add some metadata
    line.update_metadata(
        {
            "priority": "high",
            "created_by": "test_script",
            "tags": ["test", "conditional"],
        }
    )

    # Simulate condition evaluation
    line.evaluate_condition({"success": True, "data": "test_result"})

    print(f"Original TaskStarLine:")
    print(f"  ID: {line.line_id}")
    print(f"  From Task: {line.from_task_id}")
    print(f"  To Task: {line.to_task_id}")
    print(f"  Type: {line.dependency_type}")
    print(f"  Satisfied: {line.is_satisfied()}")
    print(f"  Last Evaluation: {line.last_evaluation_result}")
    print()

    # Test 1: to_json() - JSON string generation
    print("Test 1: Converting to JSON string...")
    try:
        json_str = line.to_json()
        print("✓ JSON string generation successful")
        print(f"JSON length: {len(json_str)} characters")

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        print("✓ Generated JSON is valid")
        print(f"JSON contains {len(parsed)} fields")

        # Note: condition_evaluator should be converted to string representation
        if "condition_evaluator" in parsed:
            print(
                f"✓ Condition evaluator serialized as: {parsed.get('condition_evaluator', 'N/A')}"
            )
    except Exception as e:
        print(f"✗ JSON string generation failed: {e}")
        return False

    # Test 2: from_json() - JSON string parsing
    print("\nTest 2: Creating TaskStarLine from JSON string...")
    try:
        restored_line = TaskStarLine.from_json(json_data=json_str)
        print("✓ TaskStarLine creation from JSON string successful")

        # Verify data integrity
        assert restored_line.line_id == line.line_id
        assert restored_line.from_task_id == line.from_task_id
        assert restored_line.to_task_id == line.to_task_id
        assert restored_line.dependency_type == line.dependency_type
        assert restored_line.condition_description == line.condition_description
        print("✓ Data integrity verified")

        # Note: condition_evaluator won't be restored and needs to be set manually
        print("⚠ Note: condition_evaluator needs to be manually restored")
        restored_line.set_condition_evaluator(condition_evaluator)
        print("✓ Condition evaluator manually restored")
    except Exception as e:
        print(f"✗ TaskStarLine creation from JSON string failed: {e}")
        return False

    # Test 3: File-based serialization
    print("\nTest 3: File-based JSON serialization...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

    try:
        # Save to file
        line.to_json(save_path=temp_file)
        print(f"✓ TaskStarLine saved to file: {temp_file}")

        # Load from file
        file_line = TaskStarLine.from_json(file_path=temp_file)
        print("✓ TaskStarLine loaded from file")

        # Verify data integrity
        assert file_line.line_id == line.line_id
        assert file_line.from_task_id == line.from_task_id
        assert file_line.to_task_id == line.to_task_id
        print("✓ File-based data integrity verified")

        # Clean up
        os.unlink(temp_file)
        print("✓ Temporary file cleaned up")
    except Exception as e:
        print(f"✗ File-based serialization failed: {e}")
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        return False

    print("\n🎉 All TaskStarLine JSON tests passed!")
    return True


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "=" * 60)
    print("Testing Edge Cases and Error Handling")
    print("=" * 60)

    # Test 1: Invalid JSON string
    print("Test 1: Invalid JSON string...")
    try:
        TaskStar.from_json(json_data="invalid json {")
        print("✗ Should have raised an exception")
        return False
    except json.JSONDecodeError:
        print("✓ Correctly raised JSONDecodeError for invalid JSON")
    except Exception as e:
        print(f"✗ Unexpected exception: {e}")
        return False

    # Test 2: Missing parameters
    print("\nTest 2: Missing parameters...")
    try:
        TaskStar.from_json()
        print("✗ Should have raised an exception")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"✗ Unexpected exception: {e}")
        return False

    # Test 3: Both parameters provided
    print("\nTest 3: Both parameters provided...")
    try:
        TaskStar.from_json(json_data='{"test": "data"}', file_path="test.json")
        print("✗ Should have raised an exception")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"✗ Unexpected exception: {e}")
        return False

    # Test 4: Non-existent file
    print("\nTest 4: Non-existent file...")
    try:
        TaskStar.from_json(file_path="non_existent_file.json")
        print("✗ Should have raised an exception")
        return False
    except FileNotFoundError as e:
        print(f"✓ Correctly raised FileNotFoundError: {e}")
    except Exception as e:
        print(f"✗ Unexpected exception: {e}")
        return False

    print("\n🎉 All edge case tests passed!")
    return True


def main():
    """Run all tests."""
    print("Starting JSON Serialization Tests")
    print("=" * 60)

    all_passed = True

    # Test TaskStar
    if not test_task_star_json():
        all_passed = False

    # Test TaskStarLine
    if not test_task_star_line_json():
        all_passed = False

    # Test edge cases
    if not test_edge_cases():
        all_passed = False

    # Final results
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! 🎉")
        print("JSON serialization/deserialization is working correctly.")
    else:
        print("❌ SOME TESTS FAILED ❌")
        print("Please check the error messages above.")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
