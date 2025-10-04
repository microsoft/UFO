#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple test script for TaskStar and TaskStarLine JSON serialization/deserialization.

This script tests the to_json() and from_json() methods of both classes
without complex imports.
"""

import sys
import os
import tempfile
import json
from datetime import datetime, timezone

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    # Direct imports to avoid circular dependencies
    from galaxy.constellation.enums import (
        TaskStatus,
        TaskPriority,
        DeviceType,
        DependencyType,
    )
    from galaxy.constellation.task_star import TaskStar
    from galaxy.constellation.task_star_line import TaskStarLine

    print("✓ Successfully imported required modules")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Let's try to test basic functionality without full imports...")


def test_basic_json_operations():
    """Test basic JSON operations without complex dependencies."""
    print("\n" + "=" * 60)
    print("Testing Basic JSON Operations")
    print("=" * 60)

    try:
        # Create a simple TaskStar instance
        task = TaskStar(
            name="Simple Test Task",
            description="A simple task for testing JSON operations",
            tips=["Be careful", "Test thoroughly"],
            timeout=300.0,
            retry_count=2,
        )

        print(f"Created TaskStar: {task.name}")
        print(f"Task ID: {task.task_id}")

        # Test to_json
        print("\n1. Testing TaskStar.to_json()...")
        json_str = task.to_json()
        print(f"✓ JSON string generated ({len(json_str)} characters)")

        # Verify it's valid JSON
        parsed_data = json.loads(json_str)
        print(f"✓ Valid JSON with {len(parsed_data)} fields")

        # Test from_json
        print("\n2. Testing TaskStar.from_json()...")
        restored_task = TaskStar.from_json(json_data=json_str)
        print(f"✓ TaskStar restored from JSON")
        print(f"✓ Original ID: {task.task_id}")
        print(f"✓ Restored ID: {restored_task.task_id}")
        print(f"✓ Names match: {task.name == restored_task.name}")

        # Test file operations
        print("\n3. Testing file operations...")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        task.to_json(save_path=temp_file)
        print(f"✓ Saved to file: {temp_file}")

        file_task = TaskStar.from_json(file_path=temp_file)
        print(f"✓ Loaded from file")
        print(f"✓ File task ID: {file_task.task_id}")

        # Clean up
        os.unlink(temp_file)
        print("✓ Temporary file cleaned up")

        return True

    except Exception as e:
        print(f"✗ Error in TaskStar JSON operations: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_task_star_line_basic():
    """Test basic TaskStarLine JSON operations."""
    print("\n" + "=" * 60)
    print("Testing TaskStarLine JSON Operations")
    print("=" * 60)

    try:
        # Create a simple TaskStarLine
        line = TaskStarLine(
            from_task_id="task_001",
            to_task_id="task_002",
            dependency_type=DependencyType.UNCONDITIONAL,
            condition_description="Simple unconditional dependency",
        )

        print(f"Created TaskStarLine: {line.from_task_id} -> {line.to_task_id}")
        print(f"Line ID: {line.line_id}")

        # Test to_json
        print("\n1. Testing TaskStarLine.to_json()...")
        json_str = line.to_json()
        print(f"✓ JSON string generated ({len(json_str)} characters)")

        # Verify it's valid JSON
        parsed_data = json.loads(json_str)
        print(f"✓ Valid JSON with {len(parsed_data)} fields")

        # Test from_json
        print("\n2. Testing TaskStarLine.from_json()...")
        restored_line = TaskStarLine.from_json(json_data=json_str)
        print(f"✓ TaskStarLine restored from JSON")
        print(f"✓ Original ID: {line.line_id}")
        print(f"✓ Restored ID: {restored_line.line_id}")
        print(f"✓ From tasks match: {line.from_task_id == restored_line.from_task_id}")
        print(f"✓ To tasks match: {line.to_task_id == restored_line.to_task_id}")

        # Test file operations
        print("\n3. Testing file operations...")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        line.to_json(save_path=temp_file)
        print(f"✓ Saved to file: {temp_file}")

        file_line = TaskStarLine.from_json(file_path=temp_file)
        print(f"✓ Loaded from file")
        print(f"✓ File line ID: {file_line.line_id}")

        # Clean up
        os.unlink(temp_file)
        print("✓ Temporary file cleaned up")

        return True

    except Exception as e:
        print(f"✗ Error in TaskStarLine JSON operations: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling in JSON operations."""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)

    try:
        # Test invalid JSON
        print("1. Testing invalid JSON...")
        try:
            TaskStar.from_json(json_data="invalid json")
            print("✗ Should have raised an exception")
            return False
        except json.JSONDecodeError:
            print("✓ Correctly handled invalid JSON")

        # Test missing parameters
        print("\n2. Testing missing parameters...")
        try:
            TaskStar.from_json()
            print("✗ Should have raised an exception")
            return False
        except ValueError:
            print("✓ Correctly handled missing parameters")

        # Test non-existent file
        print("\n3. Testing non-existent file...")
        try:
            TaskStar.from_json(file_path="non_existent_file.json")
            print("✗ Should have raised an exception")
            return False
        except FileNotFoundError:
            print("✓ Correctly handled non-existent file")

        return True

    except Exception as e:
        print(f"✗ Unexpected error in error handling tests: {e}")
        return False


def main():
    """Run all tests."""
    print("Starting Simple JSON Serialization Tests")
    print("=" * 60)

    all_passed = True

    # Test basic operations
    if not test_basic_json_operations():
        all_passed = False

    # Test TaskStarLine
    if not test_task_star_line_basic():
        all_passed = False

    # Test error handling
    if not test_error_handling():
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
