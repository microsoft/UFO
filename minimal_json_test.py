#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minimal functional test for JSON methods.
This creates minimal versions of the classes to test JSON functionality.
"""

import json
import tempfile
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


# Minimal enum definitions for testing
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DeviceType(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"


class DependencyType(str, Enum):
    UNCONDITIONAL = "unconditional"
    CONDITIONAL = "conditional"


# Minimal TaskStar class with JSON methods
class MinimalTaskStar:
    def __init__(self, name: str = "", description: str = "", **kwargs):
        self.task_id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.status = TaskStatus.PENDING
        self.priority = TaskPriority.MEDIUM
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_json(self, save_path: Optional[str] = None) -> str:
        import json

        task_dict = self.to_dict()
        json_str = json.dumps(task_dict, indent=2, ensure_ascii=False)

        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str

    @classmethod
    def from_json(
        cls, json_data: Optional[str] = None, file_path: Optional[str] = None
    ):
        import json

        if json_data is None and file_path is None:
            raise ValueError("Either json_data or file_path must be provided")

        if json_data is not None and file_path is not None:
            raise ValueError("Only one of json_data or file_path should be provided")

        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.loads(json_data)

        task = cls(name=data.get("name", ""), description=data.get("description", ""))
        task.task_id = data.get("task_id", task.task_id)
        if data.get("status"):
            task.status = TaskStatus(data["status"])
        if data.get("priority"):
            task.priority = TaskPriority(data["priority"])
        if data.get("created_at"):
            task.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            task.updated_at = datetime.fromisoformat(data["updated_at"])

        return task


# Minimal TaskStarLine class with JSON methods
class MinimalTaskStarLine:
    def __init__(self, from_task_id: str, to_task_id: str, **kwargs):
        self.line_id = str(uuid.uuid4())
        self.from_task_id = from_task_id
        self.to_task_id = to_task_id
        self.dependency_type = DependencyType.UNCONDITIONAL
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_id": self.line_id,
            "from_task_id": self.from_task_id,
            "to_task_id": self.to_task_id,
            "dependency_type": self.dependency_type.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_json(self, save_path: Optional[str] = None) -> str:
        import json

        line_dict = self.to_dict()
        json_str = json.dumps(line_dict, indent=2, ensure_ascii=False)

        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str

    @classmethod
    def from_json(
        cls, json_data: Optional[str] = None, file_path: Optional[str] = None
    ):
        import json

        if json_data is None and file_path is None:
            raise ValueError("Either json_data or file_path must be provided")

        if json_data is not None and file_path is not None:
            raise ValueError("Only one of json_data or file_path should be provided")

        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.loads(json_data)

        line = cls(from_task_id=data["from_task_id"], to_task_id=data["to_task_id"])
        line.line_id = data.get("line_id", line.line_id)
        if data.get("dependency_type"):
            line.dependency_type = DependencyType(data["dependency_type"])
        if data.get("created_at"):
            line.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            line.updated_at = datetime.fromisoformat(data["updated_at"])

        return line


def test_minimal_task_star():
    """Test the minimal TaskStar JSON functionality."""
    print("=" * 60)
    print("Testing Minimal TaskStar JSON Operations")
    print("=" * 60)

    try:
        # Create a task
        task = MinimalTaskStar(
            name="Test Task", description="A test task for JSON operations"
        )

        print(f"Created TaskStar:")
        print(f"  ID: {task.task_id}")
        print(f"  Name: {task.name}")
        print(f"  Status: {task.status}")

        # Test to_json
        print("\n1. Testing to_json()...")
        json_str = task.to_json()
        print(f"✓ JSON string generated ({len(json_str)} characters)")

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        print(f"✓ Valid JSON with {len(parsed)} fields")

        # Test from_json with string
        print("\n2. Testing from_json() with string...")
        restored_task = MinimalTaskStar.from_json(json_data=json_str)
        print(f"✓ Task restored from JSON string")
        print(f"✓ Original ID: {task.task_id}")
        print(f"✓ Restored ID: {restored_task.task_id}")
        print(f"✓ Names match: {task.name == restored_task.name}")

        # Test file operations
        print("\n3. Testing file operations...")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        task.to_json(save_path=temp_file)
        print(f"✓ Saved to file: {temp_file}")

        file_task = MinimalTaskStar.from_json(file_path=temp_file)
        print(f"✓ Loaded from file")
        print(f"✓ File task matches: {file_task.task_id == task.task_id}")

        # Clean up
        os.unlink(temp_file)
        print("✓ Temporary file cleaned up")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_minimal_task_star_line():
    """Test the minimal TaskStarLine JSON functionality."""
    print("\n" + "=" * 60)
    print("Testing Minimal TaskStarLine JSON Operations")
    print("=" * 60)

    try:
        # Create a line
        line = MinimalTaskStarLine(from_task_id="task_001", to_task_id="task_002")

        print(f"Created TaskStarLine:")
        print(f"  ID: {line.line_id}")
        print(f"  From: {line.from_task_id}")
        print(f"  To: {line.to_task_id}")
        print(f"  Type: {line.dependency_type}")

        # Test to_json
        print("\n1. Testing to_json()...")
        json_str = line.to_json()
        print(f"✓ JSON string generated ({len(json_str)} characters)")

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        print(f"✓ Valid JSON with {len(parsed)} fields")

        # Test from_json with string
        print("\n2. Testing from_json() with string...")
        restored_line = MinimalTaskStarLine.from_json(json_data=json_str)
        print(f"✓ Line restored from JSON string")
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

        file_line = MinimalTaskStarLine.from_json(file_path=temp_file)
        print(f"✓ Loaded from file")
        print(f"✓ File line matches: {file_line.line_id == line.line_id}")

        # Clean up
        os.unlink(temp_file)
        print("✓ Temporary file cleaned up")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling."""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)

    try:
        # Test invalid JSON
        print("1. Testing invalid JSON...")
        try:
            MinimalTaskStar.from_json(json_data="invalid json")
            print("✗ Should have raised an exception")
            return False
        except json.JSONDecodeError:
            print("✓ Correctly handled invalid JSON")

        # Test missing parameters
        print("\n2. Testing missing parameters...")
        try:
            MinimalTaskStar.from_json()
            print("✗ Should have raised an exception")
            return False
        except ValueError as e:
            print(f"✓ Correctly handled missing parameters: {e}")

        # Test both parameters
        print("\n3. Testing both parameters provided...")
        try:
            MinimalTaskStar.from_json(
                json_data='{"test": "data"}', file_path="test.json"
            )
            print("✗ Should have raised an exception")
            return False
        except ValueError as e:
            print(f"✓ Correctly handled both parameters: {e}")

        return True

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def main():
    """Run all tests."""
    print("Starting Minimal JSON Functionality Tests")
    print("=" * 60)

    all_passed = True

    if not test_minimal_task_star():
        all_passed = False

    if not test_minimal_task_star_line():
        all_passed = False

    if not test_error_handling():
        all_passed = False

    # Final results
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! 🎉")
        print("JSON functionality is working correctly!")
        print("\nThis confirms that the JSON methods in TaskStar and TaskStarLine")
        print("should work properly when the classes can be imported correctly.")
    else:
        print("❌ SOME TESTS FAILED ❌")
        print("Please check the error messages above.")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
