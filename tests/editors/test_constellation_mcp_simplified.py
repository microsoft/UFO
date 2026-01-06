#!/usr/bin/env python3
"""
Test script for the Constellation Editor MCP Server.
Tests only the available MCP tools.
"""

import sys
import os
import json

# Add the UFO2 directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
ufo_path = os.path.dirname(current_dir)
sys.path.insert(0, ufo_path)

from ufo.client.mcp.local_servers.constellation_mcp_server import (
    create_constellation_mcp_server,
)


def test_mcp_server():
    """Test all available MCP server tools."""
    print("=== Testing Constellation Editor MCP Server ===")

    # Create the MCP server instance
    mcp_server = create_constellation_mcp_server()

    # Get all available tools using the tool manager
    tools_dict = mcp_server._tool_manager._tools
    print(f"\nAvailable tools: {len(tools_dict)}")
    for tool_name in tools_dict.keys():
        print(f"  - {tool_name}")

    # Helper function to call tools
    def call_tool(tool_name, *args, **kwargs):
        """Call a tool by name with arguments"""
        tool = tools_dict[tool_name]
        # Call the tool function directly
        return tool.fn(*args, **kwargs)

    # Test 1: Add tasks
    print("\n1. Testing add_task...")

    try:
        result1 = call_tool(
            "add_task",
            task_id="mcp_test_task1",
            name="MCP Test Task 1",
            description="First test task created through MCP server with detailed steps and instructions for completion",
            target_device_id="test_device_1",
            tips="Make sure to complete this task before moving to the next one. Check all prerequisites and verify results.",
        )
        result2 = call_tool(
            "add_task",
            task_id="mcp_test_task2",
            name="MCP Test Task 2",
            description="Second test task created through MCP server for dependency testing and validation",
            target_device_id="test_device_2",
            tips="This task depends on task1 completion. Wait for the prerequisite task to finish before starting.",
        )
        print(f"   ✓ Added task1: {json.loads(result1)['task_id']}")
        print(f"   ✓ Added task2: {json.loads(result2)['task_id']}")
    except Exception as e:
        print(f"   ✗ Failed to add tasks: {e}")
        return False

    # Test 2: Add dependency
    print("\n2. Testing add_dependency...")
    try:
        dep_result = call_tool(
            "add_dependency",
            from_task_id="mcp_test_task1",
            to_task_id="mcp_test_task2",
            condition_description="Task2 should wait for Task1 to complete successfully before starting execution. This ensures proper sequencing and prevents conflicts between the two tasks.",
        )
        dep = json.loads(dep_result)
        print(f"   ✓ Added dependency: {dep['from_task_id']} -> {dep['to_task_id']}")
        dep_id = dep["line_id"]  # Save for later tests
    except Exception as e:
        print(f"   ✗ Failed to add dependency: {e}")
        return False

    # Test 3: Update task
    print("\n3. Testing update_task...")
    try:
        updated_result = call_tool(
            "update_task",
            task_id="mcp_test_task1",
            name="MCP Test Task 1 (Updated)",
            description="This is an updated task description with more details and enhanced requirements for better execution",
            target_device_id="updated_device_1",
            tips="Updated tips: Focus on accuracy and precision. Double-check all inputs and validate outputs thoroughly.",
        )
        updated_task = json.loads(updated_result)
        print(f"   ✓ Updated task: {updated_task['name']}")
    except Exception as e:
        print(f"   ✗ Failed to update task: {e}")
        return False

    # Test 4: Update dependency
    print("\n4. Testing update_dependency...")
    try:
        updated_dep_result = call_tool(
            "update_dependency",
            dependency_id=dep_id,
            condition_description="Updated condition: Task2 must wait for Task1 to complete successfully with full validation and verification of results before proceeding with its own execution.",
        )
        updated_dep = json.loads(updated_dep_result)
        print(f"   ✓ Updated dependency condition")
    except Exception as e:
        print(f"   ✗ Failed to update dependency: {e}")
        return False

    # Test 5: Build constellation (batch operations)
    print("\n5. Testing build_constellation...")
    try:
        config = {
            "tasks": [
                {
                    "task_id": "batch_task1",
                    "name": "Batch Task 1",
                    "description": "First batch task created in bulk operation",
                    "priority": 1,
                },
                {
                    "task_id": "batch_task2",
                    "name": "Batch Task 2",
                    "description": "Second batch task created in bulk operation",
                    "priority": 2,
                },
            ],
            "dependencies": [
                {
                    "from_task_id": "batch_task1",
                    "to_task_id": "batch_task2",
                    "dependency_type": "unconditional",
                }
            ],
            "metadata": {"batch_created": True, "test_constellation": True},
        }

        build_result = call_tool("build_constellation", config)
        built = json.loads(build_result)
        print(f"   ✓ Built constellation with {len(built['tasks'])} tasks")
    except Exception as e:
        print(f"   ✗ Failed to build constellation: {e}")
        return False

    # Test 6: Remove dependency
    print("\n6. Testing remove_dependency...")
    try:
        # Get current constellation to find valid dependency IDs
        constellation_result = call_tool(
            "build_constellation", {"tasks": [], "dependencies": [], "metadata": {}}
        )
        constellation = json.loads(constellation_result)

        # Find a dependency to remove
        valid_dep_id = None
        for dep_key in constellation.get("dependencies", {}):
            valid_dep_id = dep_key
            break

        if valid_dep_id:
            remove_dep_result = call_tool(
                "remove_dependency", dependency_id=valid_dep_id
            )
            print(f"   ✓ Removed dependency: {remove_dep_result}")
        else:
            print(f"   ⚠ Skipped remove_dependency test (no dependencies found)")
    except Exception as e:
        print(f"   ✗ Failed to remove dependency: {e}")
        return False

    # Test 7: Remove task
    print("\n7. Testing remove_task...")
    try:
        remove_result = call_tool("remove_task", task_id="mcp_test_task2")
        print(f"   ✓ Removed task: {remove_result}")
    except Exception as e:
        print(f"   ✗ Failed to remove task: {e}")
        return False

    return True


def main():
    """Run all MCP server tests."""
    print("Testing Constellation Editor MCP Server (Simplified)")
    print("=" * 60)

    try:
        success = test_mcp_server()

        if success:
            print("\n" + "=" * 60)
            print("✓ All available MCP server tests completed successfully!")
        else:
            print("\n" + "=" * 60)
            print("✗ Some tests failed")
            return 1

    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
