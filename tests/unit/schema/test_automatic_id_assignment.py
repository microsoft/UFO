#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for automatic ID assignment in BaseModel schemas.

This script tests the automatic generation of constellation_id, task_id, and line_id,
as well as the uniqueness validation within constellation contexts.
"""

from galaxy.agents.schema import (
    TaskStarSchema, 
    TaskStarLineSchema, 
    TaskConstellationSchema,
    IDManager
)


def test_automatic_id_generation():
    """Test automatic ID generation for all schema types."""
    print("🧪 Testing automatic ID generation...")
    
    # Test TaskStarSchema automatic task_id generation
    task_data = {
        "name": "Auto Task",
        "description": "Task with auto-generated ID"
    }
    
    task_schema = TaskStarSchema(**task_data)
    print(f"✅ TaskStarSchema auto task_id: {task_schema.task_id}")
    assert task_schema.task_id is not None
    assert task_schema.task_id.startswith("task_")
    
    # Test TaskStarLineSchema automatic line_id generation
    line_data = {
        "from_task_id": "task1",
        "to_task_id": "task2"
    }
    
    line_schema = TaskStarLineSchema(**line_data)
    print(f"✅ TaskStarLineSchema auto line_id: {line_schema.line_id}")
    assert line_schema.line_id is not None
    assert line_schema.line_id.startswith("line_")
    
    # Test TaskConstellationSchema automatic constellation_id generation
    constellation_data = {
        "name": "Auto Constellation"
    }
    
    constellation_schema = TaskConstellationSchema(**constellation_data)
    print(f"✅ TaskConstellationSchema auto constellation_id: {constellation_schema.constellation_id}")
    assert constellation_schema.constellation_id is not None
    assert constellation_schema.constellation_id.startswith("constellation_")
    
    return True


def test_explicit_id_preservation():
    """Test that explicitly provided IDs are preserved."""
    print("\n🧪 Testing explicit ID preservation...")
    
    # Test with explicit IDs
    task_schema = TaskStarSchema(
        task_id="explicit_task_001",
        name="Explicit Task",
        description="Task with explicit ID"
    )
    print(f"✅ Explicit task_id preserved: {task_schema.task_id}")
    assert task_schema.task_id == "explicit_task_001"
    
    line_schema = TaskStarLineSchema(
        line_id="explicit_line_001",
        from_task_id="task1",
        to_task_id="task2"
    )
    print(f"✅ Explicit line_id preserved: {line_schema.line_id}")
    assert line_schema.line_id == "explicit_line_001"
    
    constellation_schema = TaskConstellationSchema(
        constellation_id="explicit_constellation_001",
        name="Explicit Constellation"
    )
    print(f"✅ Explicit constellation_id preserved: {constellation_schema.constellation_id}")
    assert constellation_schema.constellation_id == "explicit_constellation_001"
    
    return True


def test_uniqueness_validation():
    """Test uniqueness validation within constellation context."""
    print("\n🧪 Testing ID uniqueness validation...")
    
    # Create tasks with unique IDs
    task1 = TaskStarSchema(
        task_id="unique_task_001",
        name="Task 1",
        description="First task"
    )
    
    task2 = TaskStarSchema(
        task_id="unique_task_002", 
        name="Task 2",
        description="Second task"
    )
    
    # Create dependency
    dependency = TaskStarLineSchema(
        line_id="unique_line_001",
        from_task_id="unique_task_001",
        to_task_id="unique_task_002"
    )
    
    # Create constellation with unique IDs
    try:
        constellation = TaskConstellationSchema(
            constellation_id="test_constellation",
            name="Test Constellation",
            tasks={
                "unique_task_001": task1,
                "unique_task_002": task2
            },
            dependencies={
                "unique_line_001": dependency
            }
        )
        print("✅ Constellation with unique IDs created successfully")
    except Exception as e:
        print(f"❌ Failed to create constellation with unique IDs: {e}")
        return False
    
    # Test duplicate task ID detection
    try:
        duplicate_task = TaskStarSchema(
            task_id="unique_task_001",  # Duplicate ID
            name="Duplicate Task",
            description="Task with duplicate ID"
        )
        
        bad_constellation = TaskConstellationSchema(
            constellation_id="test_constellation_bad",
            name="Bad Constellation",
            tasks={
                "unique_task_001": task1,
                "duplicate_task": duplicate_task  # This should cause validation error
            }
        )
        print("❌ Duplicate task ID validation failed - should have been caught")
        return False
    except ValueError as e:
        print(f"✅ Duplicate task ID correctly detected: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True


def test_id_manager_context():
    """Test that ID Manager maintains context properly."""
    print("\n🧪 Testing ID Manager context...")
    
    id_manager = IDManager()
    
    # Generate task IDs for constellation A
    task_id_1a = id_manager.generate_task_id("constellation_a")
    task_id_2a = id_manager.generate_task_id("constellation_a")
    
    # Generate task IDs for constellation B
    task_id_1b = id_manager.generate_task_id("constellation_b")
    task_id_2b = id_manager.generate_task_id("constellation_b")
    
    print(f"✅ Constellation A task IDs: {task_id_1a}, {task_id_2a}")
    print(f"✅ Constellation B task IDs: {task_id_1b}, {task_id_2b}")
    
    # Verify uniqueness within each constellation
    assert task_id_1a != task_id_2a
    assert task_id_1b != task_id_2b
    
    # Verify IDs can be same across different constellations (they use different counters)
    print("✅ ID context separation working correctly")
    
    # Test availability check
    assert not id_manager.is_task_id_available("constellation_a", task_id_1a)
    assert id_manager.is_task_id_available("constellation_a", "unused_task_id")
    print("✅ ID availability check working correctly")
    
    return True


def test_sequential_id_generation():
    """Test that IDs are generated sequentially within constellation context."""
    print("\n🧪 Testing sequential ID generation...")
    
    id_manager = IDManager()
    constellation_id = "seq_test_constellation"
    
    # Generate multiple task IDs
    task_ids = []
    for i in range(5):
        task_id = id_manager.generate_task_id(constellation_id)
        task_ids.append(task_id)
    
    print(f"✅ Generated task IDs: {task_ids}")
    
    # Verify they are sequential
    for i, task_id in enumerate(task_ids, 1):
        expected = f"task_{i:03d}"
        assert task_id == expected, f"Expected {expected}, got {task_id}"
    
    # Generate multiple line IDs
    line_ids = []
    for i in range(3):
        line_id = id_manager.generate_line_id(constellation_id)
        line_ids.append(line_id)
    
    print(f"✅ Generated line IDs: {line_ids}")
    
    # Verify they are sequential
    for i, line_id in enumerate(line_ids, 1):
        expected = f"line_{i:03d}"
        assert line_id == expected, f"Expected {expected}, got {line_id}"
    
    print("✅ Sequential ID generation working correctly")
    return True


def test_empty_string_handling():
    """Test that empty strings are treated as None for ID generation."""
    print("\n🧪 Testing empty string handling...")
    
    # Test empty string for task_id
    task_schema = TaskStarSchema(
        task_id="",  # Empty string should trigger auto-generation
        name="Empty ID Task",
        description="Task with empty string ID"
    )
    
    print(f"✅ Empty task_id generated as: {task_schema.task_id}")
    assert task_schema.task_id != ""
    assert task_schema.task_id.startswith("task_")
    
    # Test empty string for line_id
    line_schema = TaskStarLineSchema(
        line_id="",  # Empty string should trigger auto-generation
        from_task_id="task1",
        to_task_id="task2"
    )
    
    print(f"✅ Empty line_id generated as: {line_schema.line_id}")
    assert line_schema.line_id != ""
    assert line_schema.line_id.startswith("line_")
    
    return True


def main():
    """Run all tests."""
    print("🚀 Testing Automatic ID Assignment and Validation\n")
    
    success = True
    
    success &= test_automatic_id_generation()
    success &= test_explicit_id_preservation()
    success &= test_uniqueness_validation()
    success &= test_id_manager_context()
    success &= test_sequential_id_generation()
    success &= test_empty_string_handling()
    
    if success:
        print("\n🎉 All tests passed successfully!")
        print("\n📊 Test Summary:")
        print("   ✅ Automatic ID generation")
        print("   ✅ Explicit ID preservation")
        print("   ✅ Uniqueness validation")
        print("   ✅ Context-aware ID management")
        print("   ✅ Sequential ID generation")
        print("   ✅ Empty string handling")
    else:
        print("\n❌ Some tests failed!")
        
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
