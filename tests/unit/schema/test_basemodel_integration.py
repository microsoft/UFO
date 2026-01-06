#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for BaseModel integration with TaskStar, TaskStarLine, and TaskConstellation.

This script tests the serialization and deserialization functionality between
the constellation classes and their corresponding Pydantic BaseModel schemas.
"""

import json
from datetime import datetime
from typing import Dict, Any

# Import the classes and schemas
from galaxy.constellation.task_star import TaskStar
from galaxy.constellation.task_star_line import TaskStarLine
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.constellation.enums import (
    TaskStatus,
    TaskPriority,
    DeviceType,
    DependencyType,
    ConstellationState,
)
from galaxy.agents.schema import (
    TaskStarSchema,
    TaskStarLineSchema,
    TaskConstellationSchema,
)


def test_task_star_basemodel():
    """Test TaskStar BaseModel integration."""
    print("🧪 Testing TaskStar BaseModel integration...")

    # Create a TaskStar instance
    task = TaskStar(
        task_id="test_task_001",
        name="Test Task",
        description="This is a test task for BaseModel integration",
        tips=["Tip 1: Be careful", "Tip 2: Check the output"],
        target_device_id="device_001",
        device_type=DeviceType.WINDOWS,
        priority=TaskPriority.HIGH,
        timeout=300.0,
        retry_count=3,
        task_data={"key1": "value1", "key2": 42},
        expected_output_type="json",
    )

    # Test to_basemodel
    schema = task.to_basemodel()
    print(f"✅ TaskStar to BaseModel: {type(schema).__name__}")
    assert isinstance(schema, TaskStarSchema)
    assert schema.task_id == "test_task_001"
    assert schema.name == "Test Task"
    assert schema.description == "This is a test task for BaseModel integration"

    # Test from_basemodel
    task_restored = TaskStar.from_basemodel(schema)
    print(f"✅ TaskStar from BaseModel: {task_restored.task_id}")
    assert task_restored.task_id == task.task_id
    assert task_restored.name == task.name
    assert task_restored.description == task.description
    assert task_restored.target_device_id == task.target_device_id

    # Test JSON serialization roundtrip through BaseModel
    json_data = schema.model_dump_json()
    schema_restored = TaskStarSchema.model_validate_json(json_data)
    task_final = TaskStar.from_basemodel(schema_restored)

    assert task_final.task_id == task.task_id
    assert task_final.name == task.name
    print("✅ TaskStar JSON roundtrip successful")


def test_task_star_line_basemodel():
    """Test TaskStarLine BaseModel integration."""
    print("\n🧪 Testing TaskStarLine BaseModel integration...")

    # Create a TaskStarLine instance
    dependency = TaskStarLine(
        from_task_id="task_001",
        to_task_id="task_002",
        dependency_type=DependencyType.SUCCESS_ONLY,
        condition_description="Task 001 must complete successfully",
        metadata={"priority": "high", "category": "data_flow"},
    )

    # Test to_basemodel
    schema = dependency.to_basemodel()
    print(f"✅ TaskStarLine to BaseModel: {type(schema).__name__}")
    assert isinstance(schema, TaskStarLineSchema)
    assert schema.from_task_id == "task_001"
    assert schema.to_task_id == "task_002"
    assert schema.dependency_type == "SUCCESS_ONLY"

    # Test from_basemodel
    dependency_restored = TaskStarLine.from_basemodel(schema)
    print(f"✅ TaskStarLine from BaseModel: {dependency_restored.line_id}")
    assert dependency_restored.from_task_id == dependency.from_task_id
    assert dependency_restored.to_task_id == dependency.to_task_id
    assert dependency_restored.dependency_type == dependency.dependency_type

    # Test JSON serialization roundtrip through BaseModel
    json_data = schema.model_dump_json()
    schema_restored = TaskStarLineSchema.model_validate_json(json_data)
    dependency_final = TaskStarLine.from_basemodel(schema_restored)

    assert dependency_final.from_task_id == dependency.from_task_id
    assert dependency_final.to_task_id == dependency.to_task_id
    print("✅ TaskStarLine JSON roundtrip successful")


def test_task_constellation_basemodel():
    """Test TaskConstellation BaseModel integration."""
    print("\n🧪 Testing TaskConstellation BaseModel integration...")

    # Create a TaskConstellation with tasks and dependencies
    constellation = TaskConstellation(
        constellation_id="test_constellation_001",
        name="Test Constellation",
        enable_visualization=False,
    )

    # Add some tasks
    task1 = TaskStar(
        task_id="task_001",
        name="First Task",
        description="First task in constellation",
        device_type=DeviceType.WINDOWS,
    )

    task2 = TaskStar(
        task_id="task_002",
        name="Second Task",
        description="Second task in constellation",
        device_type=DeviceType.WINDOWS,
    )

    constellation.add_task(task1)
    constellation.add_task(task2)

    # Add a dependency
    dependency = TaskStarLine(
        from_task_id="task_001",
        to_task_id="task_002",
        dependency_type=DependencyType.UNCONDITIONAL,
    )
    constellation.add_dependency(dependency)

    # Add metadata
    constellation.update_metadata(
        {"author": "test_user", "version": "1.0.0", "tags": ["test", "automation"]}
    )

    # Test to_basemodel
    schema = constellation.to_basemodel()
    print(f"✅ TaskConstellation to BaseModel: {type(schema).__name__}")
    assert isinstance(schema, TaskConstellationSchema)
    assert schema.constellation_id == "test_constellation_001"
    assert schema.name == "Test Constellation"
    assert len(schema.tasks) == 2
    assert len(schema.dependencies) == 1

    # Test from_basemodel
    constellation_restored = TaskConstellation.from_basemodel(schema)
    print(
        f"✅ TaskConstellation from BaseModel: {constellation_restored.constellation_id}"
    )
    assert constellation_restored.constellation_id == constellation.constellation_id
    assert constellation_restored.name == constellation.name
    assert len(constellation_restored.tasks) == 2
    assert len(constellation_restored.dependencies) == 1

    # Test JSON serialization roundtrip through BaseModel
    json_data = schema.model_dump_json()
    schema_restored = TaskConstellationSchema.model_validate_json(json_data)
    constellation_final = TaskConstellation.from_basemodel(schema_restored)

    assert constellation_final.constellation_id == constellation.constellation_id
    assert constellation_final.name == constellation.name
    assert len(constellation_final.tasks) == len(constellation.tasks)
    print("✅ TaskConstellation JSON roundtrip successful")


def test_complex_scenario():
    """Test a complex scenario with all components together."""
    print("\n🧪 Testing complex scenario with all components...")

    # Create a more complex constellation
    constellation = TaskConstellation(
        constellation_id="complex_test_001", name="Complex Test Constellation"
    )

    # Create multiple tasks with different configurations
    tasks_data = [
        {
            "task_id": "data_extraction",
            "name": "Extract Data",
            "description": "Extract data from source system",
            "tips": ["Check API credentials", "Validate data format"],
            "device_type": DeviceType.API,
            "priority": TaskPriority.HIGH,
            "timeout": 600.0,
        },
        {
            "task_id": "data_processing",
            "name": "Process Data",
            "description": "Process the extracted data",
            "device_type": DeviceType.LINUX,
            "priority": TaskPriority.MEDIUM,
            "task_data": {"batch_size": 1000, "parallel": True},
        },
        {
            "task_id": "data_validation",
            "name": "Validate Results",
            "description": "Validate processed data quality",
            "device_type": DeviceType.WINDOWS,
            "priority": TaskPriority.LOW,
        },
    ]

    # Create and add tasks
    for task_data in tasks_data:
        task = TaskStar(**task_data)
        constellation.add_task(task)

    # Create dependencies
    dependencies = [
        TaskStarLine("data_extraction", "data_processing", DependencyType.SUCCESS_ONLY),
        TaskStarLine(
            "data_processing", "data_validation", DependencyType.UNCONDITIONAL
        ),
    ]

    for dep in dependencies:
        constellation.add_dependency(dep)

    # Convert to BaseModel and back
    schema = constellation.to_basemodel()
    constellation_restored = TaskConstellation.from_basemodel(schema)

    # Validate structure
    assert len(constellation_restored.tasks) == 3
    assert len(constellation_restored.dependencies) == 2

    # Check task details
    extraction_task = constellation_restored.get_task("data_extraction")
    assert extraction_task is not None
    assert extraction_task.device_type == DeviceType.API
    assert extraction_task.priority == TaskPriority.HIGH

    processing_task = constellation_restored.get_task("data_processing")
    assert processing_task is not None
    assert processing_task.task_data.get("batch_size") == 1000

    print("✅ Complex scenario test successful")


def test_validation_and_error_handling():
    """Test validation and error handling."""
    print("\n🧪 Testing validation and error handling...")

    # Test invalid schema types
    try:
        TaskStar.from_basemodel("invalid_schema")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print("✅ Correctly caught invalid schema type for TaskStar")

    try:
        TaskStarLine.from_basemodel(42)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print("✅ Correctly caught invalid schema type for TaskStarLine")

    try:
        TaskConstellation.from_basemodel({"invalid": "dict"})
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print("✅ Correctly caught invalid schema type for TaskConstellation")

    # Test BaseModel validation
    try:
        # Missing required fields
        invalid_schema = TaskStarSchema(
            task_id="",  # Invalid empty task_id
            name="",
            description="",
            created_at="invalid_date",  # Invalid date format
            updated_at="invalid_date",
        )
        print("⚠️ BaseModel validation may be lenient")
    except Exception as e:
        print(f"✅ BaseModel validation caught error: {e}")


def main():
    """Run all tests."""
    print("🚀 Starting BaseModel Integration Tests\n")

    try:
        test_task_star_basemodel()
        test_task_star_line_basemodel()
        test_task_constellation_basemodel()
        test_complex_scenario()
        test_validation_and_error_handling()

        print("\n🎉 All tests passed successfully!")
        print("\n📊 Test Summary:")
        print("   ✅ TaskStar BaseModel integration")
        print("   ✅ TaskStarLine BaseModel integration")
        print("   ✅ TaskConstellation BaseModel integration")
        print("   ✅ Complex scenario testing")
        print("   ✅ Validation and error handling")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
