#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for optional fields in BaseModel schemas.

This script verifies that created_at and updated_at fields are now optional
and that task_description has been removed from TaskStarSchema.
"""

from ufo.galaxy.agents.schema import (
    TaskStarSchema,
    TaskStarLineSchema,
    TaskConstellationSchema,
)


def test_optional_fields():
    """Test that created_at and updated_at fields are optional."""
    print("🧪 Testing optional fields...")

    # Test TaskStarSchema with minimal required fields
    minimal_task_data = {
        "task_id": "minimal_task",
        "name": "Minimal Task",
        "description": "A task with minimal fields",
    }

    try:
        task_schema = TaskStarSchema(**minimal_task_data)
        print("✅ TaskStarSchema with minimal fields created successfully")
        print(f"   - created_at: {task_schema.created_at}")
        print(f"   - updated_at: {task_schema.updated_at}")
        assert task_schema.created_at is None
        assert task_schema.updated_at is None
    except Exception as e:
        print(f"❌ Failed to create TaskStarSchema with minimal fields: {e}")
        return False

    # Test TaskStarLineSchema with minimal required fields
    minimal_line_data = {
        "line_id": "minimal_line",
        "from_task_id": "task1",
        "to_task_id": "task2",
    }

    try:
        line_schema = TaskStarLineSchema(**minimal_line_data)
        print("✅ TaskStarLineSchema with minimal fields created successfully")
        print(f"   - created_at: {line_schema.created_at}")
        print(f"   - updated_at: {line_schema.updated_at}")
        assert line_schema.created_at is None
        assert line_schema.updated_at is None
    except Exception as e:
        print(f"❌ Failed to create TaskStarLineSchema with minimal fields: {e}")
        return False

    # Test TaskConstellationSchema with minimal required fields
    minimal_constellation_data = {
        "constellation_id": "minimal_constellation",
        "name": "Minimal Constellation",
    }

    try:
        constellation_schema = TaskConstellationSchema(**minimal_constellation_data)
        print("✅ TaskConstellationSchema with minimal fields created successfully")
        print(f"   - created_at: {constellation_schema.created_at}")
        print(f"   - updated_at: {constellation_schema.updated_at}")
        assert constellation_schema.created_at is None
        assert constellation_schema.updated_at is None
    except Exception as e:
        print(f"❌ Failed to create TaskConstellationSchema with minimal fields: {e}")
        return False

    return True


def test_task_description_removed():
    """Test that task_description field has been removed from TaskStarSchema."""
    print("\n🧪 Testing task_description field removal...")

    # Check that task_description is not in the model fields
    task_schema_fields = set(TaskStarSchema.model_fields.keys())

    if "task_description" in task_schema_fields:
        print("❌ task_description field still exists in TaskStarSchema")
        return False
    else:
        print("✅ task_description field has been successfully removed")

    # Test creating a schema with task_description should work (it will be ignored)
    try:
        task_data = {
            "task_id": "test_task",
            "name": "Test Task",
            "description": "Test description",
            "task_description": "This should be ignored",  # This should be ignored
        }

        task_schema = TaskStarSchema(**task_data)

        # Check that task_description is not accessible
        if hasattr(task_schema, "task_description"):
            print("❌ task_description attribute still accessible")
            return False
        else:
            print("✅ task_description attribute not accessible (as expected)")

    except Exception as e:
        print(f"❌ Unexpected error when testing task_description: {e}")
        return False

    return True


def test_backwards_compatibility():
    """Test that the changes don't break backwards compatibility."""
    print("\n🧪 Testing backwards compatibility...")

    # Test with full data including timestamps
    full_task_data = {
        "task_id": "full_task",
        "name": "Full Task",
        "description": "A task with all fields",
        "created_at": "2025-09-29T06:44:00.951923+00:00",
        "updated_at": "2025-09-29T06:44:00.951923+00:00",
        "priority": "HIGH",
        "status": "PENDING",
    }

    try:
        task_schema = TaskStarSchema(**full_task_data)
        print("✅ TaskStarSchema with timestamps works correctly")
        assert task_schema.created_at == "2025-09-29T06:44:00.951923+00:00"
        assert task_schema.updated_at == "2025-09-29T06:44:00.951923+00:00"
    except Exception as e:
        print(f"❌ Failed with timestamps: {e}")
        return False

    # Test JSON serialization
    try:
        json_data = task_schema.model_dump_json()
        restored_schema = TaskStarSchema.model_validate_json(json_data)
        print("✅ JSON serialization/deserialization works correctly")
    except Exception as e:
        print(f"❌ JSON processing failed: {e}")
        return False

    return True


def main():
    """Run all tests."""
    print("🚀 Testing BaseModel Schema Modifications\n")

    success = True

    success &= test_optional_fields()
    success &= test_task_description_removed()
    success &= test_backwards_compatibility()

    if success:
        print("\n🎉 All tests passed successfully!")
        print("\n📊 Test Summary:")
        print("   ✅ created_at and updated_at are now optional")
        print("   ✅ task_description field has been removed")
        print("   ✅ Backwards compatibility maintained")
    else:
        print("\n❌ Some tests failed!")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
