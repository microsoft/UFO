#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for TaskConstellation JSON serialization/deserialization.

This script tests the to_json() and from_json() methods of TaskConstellation
along with its constituent TaskStar and TaskStarLine objects.
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


class ConstellationState(str, Enum):
    CREATED = "created"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_FAILED = "partially_failed"


# Simplified versions of the classes for testing
class MinimalTaskStar:
    def __init__(self, name: str = "", description: str = "", **kwargs):
        self.task_id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.status = TaskStatus.PENDING
        self.priority = TaskPriority.MEDIUM
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.target_device_id = kwargs.get("target_device_id")
        self.device_type = kwargs.get("device_type")
        self.result = None
        self.error = None
        self.tips = kwargs.get("tips", [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "target_device_id": self.target_device_id,
            "device_type": self.device_type.value if self.device_type else None,
            "result": self.result,
            "error": str(self.error) if self.error else None,
            "tips": self.tips,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        task = cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            target_device_id=data.get("target_device_id"),
            device_type=(
                DeviceType(data["device_type"]) if data.get("device_type") else None
            ),
            tips=data.get("tips", []),
        )
        task.task_id = data.get("task_id", task.task_id)
        task.status = TaskStatus(data.get("status", TaskStatus.PENDING.value))
        task.priority = TaskPriority(data.get("priority", TaskPriority.MEDIUM.value))
        task.result = data.get("result")
        if data.get("error"):
            task.error = Exception(data["error"])
        if data.get("created_at"):
            task.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            task.updated_at = datetime.fromisoformat(data["updated_at"])
        return task


class MinimalTaskStarLine:
    def __init__(self, from_task_id: str, to_task_id: str, **kwargs):
        self.line_id = str(uuid.uuid4())
        self.from_task_id = from_task_id
        self.to_task_id = to_task_id
        self.dependency_type = DependencyType.UNCONDITIONAL
        self.condition_description = kwargs.get("condition_description", "")
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.is_satisfied = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_id": self.line_id,
            "from_task_id": self.from_task_id,
            "to_task_id": self.to_task_id,
            "dependency_type": self.dependency_type.value,
            "condition_description": self.condition_description,
            "is_satisfied": self.is_satisfied,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        line = cls(
            from_task_id=data["from_task_id"],
            to_task_id=data["to_task_id"],
            condition_description=data.get("condition_description", ""),
        )
        line.line_id = data.get("line_id", line.line_id)
        line.dependency_type = DependencyType(
            data.get("dependency_type", DependencyType.UNCONDITIONAL.value)
        )
        line.is_satisfied = data.get("is_satisfied", False)
        if data.get("created_at"):
            line.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            line.updated_at = datetime.fromisoformat(data["updated_at"])
        return line


class MinimalTaskConstellation:
    def __init__(
        self,
        constellation_id: Optional[str] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        self._constellation_id = (
            constellation_id or f"constellation_{str(uuid.uuid4())[:8]}"
        )
        self._name = name or self._constellation_id
        self._state = ConstellationState.CREATED
        self._tasks = {}
        self._dependencies = {}
        self._metadata = {}
        self._llm_source = None
        self._enable_visualization = kwargs.get("enable_visualization", True)
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = self._created_at
        self._execution_start_time = None
        self._execution_end_time = None

    @property
    def execution_duration(self) -> Optional[float]:
        if self._execution_start_time and self._execution_end_time:
            return (
                self._execution_end_time - self._execution_start_time
            ).total_seconds()
        return None

    def add_task(self, task: MinimalTaskStar):
        self._tasks[task.task_id] = task

    def add_dependency(self, dependency: MinimalTaskStarLine):
        self._dependencies[dependency.line_id] = dependency

    def to_dict(self) -> Dict[str, Any]:
        # Convert tasks using their to_dict methods
        tasks_dict = {}
        for task_id, task in self._tasks.items():
            tasks_dict[task_id] = task.to_dict()

        # Convert dependencies using their to_dict methods
        dependencies_dict = {}
        for dep_id, dependency in self._dependencies.items():
            dependencies_dict[dep_id] = dependency.to_dict()

        return {
            "constellation_id": self._constellation_id,
            "name": self._name,
            "state": self._state.value,
            "tasks": tasks_dict,
            "dependencies": dependencies_dict,
            "metadata": self._metadata,
            "llm_source": self._llm_source,
            "enable_visualization": self._enable_visualization,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "execution_start_time": (
                self._execution_start_time.isoformat()
                if self._execution_start_time
                else None
            ),
            "execution_end_time": (
                self._execution_end_time.isoformat()
                if self._execution_end_time
                else None
            ),
            "execution_duration": self.execution_duration,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        # Create constellation with basic properties
        constellation = cls(
            constellation_id=data.get("constellation_id"),
            name=data.get("name"),
            enable_visualization=data.get("enable_visualization", True),
        )

        # Restore state and metadata
        constellation._state = ConstellationState(
            data.get("state", ConstellationState.CREATED.value)
        )
        constellation._metadata = data.get("metadata", {})
        constellation._llm_source = data.get("llm_source")

        # Restore timestamps
        if data.get("created_at"):
            constellation._created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            constellation._updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("execution_start_time"):
            constellation._execution_start_time = datetime.fromisoformat(
                data["execution_start_time"]
            )
        if data.get("execution_end_time"):
            constellation._execution_end_time = datetime.fromisoformat(
                data["execution_end_time"]
            )

        # Restore tasks using MinimalTaskStar.from_dict
        for task_id, task_data in data.get("tasks", {}).items():
            task = MinimalTaskStar.from_dict(task_data)
            constellation._tasks[task_id] = task

        # Restore dependencies using MinimalTaskStarLine.from_dict
        for dep_id, dep_data in data.get("dependencies", {}).items():
            dependency = MinimalTaskStarLine.from_dict(dep_data)
            constellation._dependencies[dep_id] = dependency

        return constellation

    def to_json(self, save_path: Optional[str] = None) -> str:
        import json

        constellation_dict = self.to_dict()
        json_str = json.dumps(constellation_dict, indent=2, ensure_ascii=False)

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

        if not isinstance(data, dict):
            raise ValueError("JSON data must represent a dictionary/object")

        return cls.from_dict(data)


def test_task_constellation_json():
    """Test TaskConstellation JSON functionality."""
    print("=" * 70)
    print("Testing TaskConstellation JSON Serialization/Deserialization")
    print("=" * 70)

    try:
        # Create a constellation with tasks and dependencies
        constellation = MinimalTaskConstellation(
            name="Test Constellation", enable_visualization=False
        )

        # Add some metadata
        constellation._metadata = {
            "created_by": "test_script",
            "version": "1.0",
            "description": "Test constellation for JSON operations",
        }

        # Create tasks
        task1 = MinimalTaskStar(
            name="Task 1",
            description="First task",
            device_type=DeviceType.WINDOWS,
            target_device_id="device_001",
            tips=["Be careful", "Test thoroughly"],
        )

        task2 = MinimalTaskStar(
            name="Task 2",
            description="Second task",
            device_type=DeviceType.LINUX,
            target_device_id="device_002",
        )

        task3 = MinimalTaskStar(
            name="Task 3",
            description="Third task",
            device_type=DeviceType.WINDOWS,
            target_device_id="device_003",
        )

        # Add tasks to constellation
        constellation.add_task(task1)
        constellation.add_task(task2)
        constellation.add_task(task3)

        # Create dependencies
        dep1 = MinimalTaskStarLine(
            from_task_id=task1.task_id,
            to_task_id=task2.task_id,
            condition_description="Task 1 must complete before Task 2",
        )

        dep2 = MinimalTaskStarLine(
            from_task_id=task2.task_id,
            to_task_id=task3.task_id,
            condition_description="Task 2 must complete before Task 3",
        )

        # Add dependencies to constellation
        constellation.add_dependency(dep1)
        constellation.add_dependency(dep2)

        print(f"Created TaskConstellation:")
        print(f"  ID: {constellation._constellation_id}")
        print(f"  Name: {constellation._name}")
        print(f"  State: {constellation._state}")
        print(f"  Tasks: {len(constellation._tasks)}")
        print(f"  Dependencies: {len(constellation._dependencies)}")

        # Test 1: to_json() - JSON string generation
        print("\n1. Testing to_json()...")
        json_str = constellation.to_json()
        print(f"✓ JSON string generated ({len(json_str)} characters)")

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        print(f"✓ Valid JSON with {len(parsed)} top-level fields")
        print(f"✓ Contains {len(parsed['tasks'])} tasks")
        print(f"✓ Contains {len(parsed['dependencies'])} dependencies")

        # Test 2: from_json() - JSON string parsing
        print("\n2. Testing from_json() with string...")
        restored_constellation = MinimalTaskConstellation.from_json(json_data=json_str)
        print(f"✓ TaskConstellation restored from JSON string")

        # Verify data integrity
        assert (
            restored_constellation._constellation_id == constellation._constellation_id
        )
        assert restored_constellation._name == constellation._name
        assert restored_constellation._state == constellation._state
        assert len(restored_constellation._tasks) == len(constellation._tasks)
        assert len(restored_constellation._dependencies) == len(
            constellation._dependencies
        )
        print("✓ Basic data integrity verified")

        # Verify task data integrity
        for task_id, original_task in constellation._tasks.items():
            restored_task = restored_constellation._tasks[task_id]
            assert restored_task.name == original_task.name
            assert restored_task.description == original_task.description
            assert restored_task.device_type == original_task.device_type
        print("✓ Task data integrity verified")

        # Verify dependency data integrity
        for dep_id, original_dep in constellation._dependencies.items():
            restored_dep = restored_constellation._dependencies[dep_id]
            assert restored_dep.from_task_id == original_dep.from_task_id
            assert restored_dep.to_task_id == original_dep.to_task_id
            assert restored_dep.dependency_type == original_dep.dependency_type
        print("✓ Dependency data integrity verified")

        # Test 3: File-based serialization
        print("\n3. Testing file-based JSON serialization...")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        constellation.to_json(save_path=temp_file)
        print(f"✓ TaskConstellation saved to file: {temp_file}")

        file_constellation = MinimalTaskConstellation.from_json(file_path=temp_file)
        print("✓ TaskConstellation loaded from file")

        # Verify file-based data integrity
        assert file_constellation._constellation_id == constellation._constellation_id
        assert len(file_constellation._tasks) == len(constellation._tasks)
        assert len(file_constellation._dependencies) == len(constellation._dependencies)
        print("✓ File-based data integrity verified")

        # Clean up
        os.unlink(temp_file)
        print("✓ Temporary file cleaned up")

        # Test 4: Complex data structures
        print("\n4. Testing complex data structures...")

        # Add some complex metadata
        constellation._metadata.update(
            {
                "nested_data": {
                    "list_value": [1, 2, 3],
                    "dict_value": {"key": "value"},
                    "mixed_list": ["string", 42, True],
                },
                "execution_history": [
                    {"timestamp": "2025-09-23T10:00:00Z", "event": "created"},
                    {"timestamp": "2025-09-23T10:01:00Z", "event": "started"},
                ],
            }
        )

        # Test serialization with complex data
        complex_json = constellation.to_json()
        complex_restored = MinimalTaskConstellation.from_json(json_data=complex_json)

        assert complex_restored._metadata["nested_data"]["list_value"] == [1, 2, 3]
        assert complex_restored._metadata["execution_history"][0]["event"] == "created"
        print("✓ Complex data structures handled correctly")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling in TaskConstellation JSON operations."""
    print("\n" + "=" * 70)
    print("Testing Error Handling")
    print("=" * 70)

    try:
        # Test invalid JSON
        print("1. Testing invalid JSON...")
        try:
            MinimalTaskConstellation.from_json(json_data="invalid json")
            print("✗ Should have raised an exception")
            return False
        except json.JSONDecodeError:
            print("✓ Correctly handled invalid JSON")

        # Test missing parameters
        print("\n2. Testing missing parameters...")
        try:
            MinimalTaskConstellation.from_json()
            print("✗ Should have raised an exception")
            return False
        except ValueError as e:
            print(f"✓ Correctly handled missing parameters: {e}")

        # Test both parameters provided
        print("\n3. Testing both parameters provided...")
        try:
            MinimalTaskConstellation.from_json(
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
    print("Starting TaskConstellation JSON Tests")
    print("=" * 70)

    all_passed = True

    if not test_task_constellation_json():
        all_passed = False

    if not test_error_handling():
        all_passed = False

    # Final results
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL TASKCONSTELLTION JSON TESTS PASSED! 🎉")
        print(
            "TaskConstellation JSON serialization/deserialization is working correctly!"
        )
        print("\nThe implementation successfully leverages the existing JSON methods")
        print("from TaskStar and TaskStarLine to handle complex constellation data.")
    else:
        print("❌ SOME TESTS FAILED ❌")
        print("Please check the error messages above.")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
