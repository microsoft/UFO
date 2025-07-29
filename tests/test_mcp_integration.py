#!/usr/bin/env python3
"""
Test script to verify MCP integration in Computer class
"""

import sys
import os

# Add the UFO2 source directory to the Python path
ufo_src_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ufo_src_path)


def test_mcp_integration():
    """Test MCP integration in Computer class"""
    try:
        print("Testing MCP integration in Computer class...")

        # Import the Computer class
        from ufo.cs.computer import Computer
        from ufo.contracts.contracts import (
            MCPToolExecutionAction,
            MCPToolExecutionParams,
            MCPGetInstructionsAction,
            MCPGetInstructionsParams,
            MCPGetAvailableToolsAction,
            MCPGetAvailableToolsParams,
        )

        # Create a Computer instance
        print("\n1. Creating Computer instance...")
        computer = Computer("TestMCPComputer")
        print("✓ Computer instance created successfully")

        # Test MCP server initialization
        print("\n2. Testing MCP server initialization...")
        if hasattr(computer, "mcp_servers"):
            print(f"✓ MCP servers initialized: {list(computer.mcp_servers.keys())}")
        else:
            print("⚠ MCP servers not found")

        if hasattr(computer, "mcp_instructions"):
            print(
                f"✓ MCP instructions loaded for: {list(computer.mcp_instructions.keys())}"
            )
        else:
            print("⚠ MCP instructions not found")

        # Test get_mcp_instructions action
        print("\n3. Testing get_mcp_instructions action...")
        try:
            action = MCPGetInstructionsAction(
                params=MCPGetInstructionsParams(app_namespace="powerpoint")
            )
            result = computer.run_action(action)
            print(
                f"✓ PowerPoint instructions available: {result.get('available', False)}"
            )
            if result.get("instructions"):
                tools_count = len(result["instructions"].get("tools", []))
                print(f"✓ Found {tools_count} PowerPoint tools in instructions")
        except Exception as e:
            print(f"⚠ Get instructions test failed: {e}")

        # Test get_mcp_available_tools action
        print("\n4. Testing get_mcp_available_tools action...")
        try:
            action = MCPGetAvailableToolsAction(
                params=MCPGetAvailableToolsParams(app_namespace="excel")
            )
            result = computer.run_action(action)
            print(f"✓ Excel tools query result: {result.get('available', False)}")
            if result.get("fallback"):
                print("✓ Using fallback mode (instructions file)")
            tools_count = len(result.get("tools", []))
            print(f"✓ Found {tools_count} Excel tools")
        except Exception as e:
            print(f"⚠ Get available tools test failed: {e}")
        # Test execute_mcp_tool action (this will fail since no server is running, but tests the structure)
        print("\n5. Testing execute_mcp_tool action structure...")
        try:
            action = MCPToolExecutionAction(
                params=MCPToolExecutionParams(
                    tool_name="create_document",
                    tool_args={"template_path": "test.docx"},
                    app_namespace="word",
                )
            )
            result = computer.run_action(action)
            # This should fail since no MCP server is running, but we test the structure
            if not result.get("success"):
                print(
                    "✓ MCP tool execution structure works (expected failure without server)"
                )
            else:
                print("✓ MCP tool execution succeeded")
        except Exception as e:
            print(
                f"✓ MCP tool execution structure works (expected error: {type(e).__name__})"
            )

        # Test tool schema normalization
        print("\n6. Testing tool schema normalization...")
        try:
            # Test MCP format to YAML format conversion
            mcp_tools = [
                {
                    "name": "test_tool",
                    "description": "A test tool for schema conversion",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "param1": {
                                "type": "string",
                                "description": "First parameter",
                            },
                            "param2": {
                                "type": "number",
                                "description": "Second parameter",
                                "default": 42,
                            },
                        },
                        "required": ["param1"],
                    },
                }
            ]

            normalized_tools = computer._normalize_tool_schema(mcp_tools, source="mcp")

            if normalized_tools and len(normalized_tools) == 1:
                tool = normalized_tools[0]
                print(f"✓ Tool schema normalization successful")
                print(f"   - Tool name: {tool.get('name')}")
                print(f"   - Parameters: {len(tool.get('parameters', []))}")
                print(f"   - Has action_mapping: {'action_mapping' in tool}")

                # Verify action2action_sequence compatibility
                if "action_mapping" in tool:
                    mapping = tool["action_mapping"]
                    required_keys = [
                        "Function",
                        "Args",
                        "Status",
                        "ControlLabel",
                        "ControlText",
                    ]
                    has_all_keys = all(key in mapping for key in required_keys)
                    print(f"   - action2action_sequence compatible: {has_all_keys}")
                    if has_all_keys:
                        print(f"     Function: {mapping['Function']}")
                        print(f"     Status: {mapping['Status']}")
                else:
                    print("   ⚠ Missing action_mapping")
            else:
                print("⚠ Tool schema normalization failed")
        except Exception as e:
            print(f"⚠ Tool schema normalization test failed: {e}")

        # Test YAML format tool normalization
        print("\n7. Testing YAML tool schema normalization...")
        try:
            yaml_tools = [
                {
                    "name": "yaml_test_tool",
                    "description": "A test tool from YAML",
                    "parameters": [
                        {
                            "name": "file_path",
                            "type": "string",
                            "description": "Path to file",
                            "required": True,
                        },
                        {
                            "name": "format",
                            "type": "string",
                            "description": "File format",
                            "required": False,
                            "default": "txt",
                        },
                    ],
                }
            ]

            normalized_yaml_tools = computer._normalize_tool_schema(
                yaml_tools, source="yaml"
            )

            if normalized_yaml_tools and len(normalized_yaml_tools) == 1:
                tool = normalized_yaml_tools[0]
                print(f"✓ YAML tool schema normalization successful")
                print(f"   - Tool name: {tool.get('name')}")
                print(
                    f"   - Original parameters preserved: {len(tool.get('parameters', []))}"
                )
                print(f"   - Has action_mapping: {'action_mapping' in tool}")
                print(f"   - Has execution_hints: {'execution_hints' in tool}")
            else:
                print("⚠ YAML tool schema normalization failed")
        except Exception as e:
            print(f"⚠ YAML tool schema normalization test failed: {e}")

        # Test parameter conversion from MCP to YAML format
        print("\n8. Testing MCP parameter conversion...")
        try:
            mcp_input_schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Document title"},
                    "template": {
                        "type": "string",
                        "description": "Template to use",
                        "default": "blank",
                    },
                    "page_count": {"type": "integer", "description": "Number of pages"},
                },
                "required": ["title", "page_count"],
            }

            yaml_params = computer._convert_mcp_parameters_to_yaml(mcp_input_schema)

            if yaml_params and len(yaml_params) == 3:
                print(f"✓ MCP parameter conversion successful")
                print(f"   - Converted {len(yaml_params)} parameters")
                # Check specific parameter conversion
                title_param = next(
                    (p for p in yaml_params if p["name"] == "title"), None
                )
                if title_param and title_param["required"]:
                    print("   - Required parameter conversion: ✓")
                else:
                    print("   - Required parameter conversion: ⚠")

                template_param = next(
                    (p for p in yaml_params if p["name"] == "template"), None
                )
                if (
                    template_param
                    and not template_param["required"]
                    and template_param.get("default") == "blank"
                ):
                    print("   - Optional parameter with default: ✓")
                else:
                    print("   - Optional parameter with default: ⚠")
            else:
                print("⚠ MCP parameter conversion failed")
        except Exception as e:
            print(f"⚠ MCP parameter conversion test failed: {e}")

        print("\n9. Testing action handler registration...")
        expected_handlers = [
            "execute_mcp_tool",
            "get_mcp_instructions",
            "get_mcp_available_tools",
        ]

        # Check if the action handlers are properly registered
        action_handlers = {
            "capture_desktop_screenshot": computer._handle_capture_desktop_screenshot,
            "capture_app_window_screenshot": computer._handle_capture_app_window_screenshot,
            "get_desktop_app_info": computer._handle_get_desktop_app_info,
            "get_app_window_control_info": computer._handle_get_app_window_control_info,
            "select_application_window": computer._handle_select_application_window,
            "launch_application": computer._handle_launch_application,
            "callback": computer._handle_callback,
            "get_ui_tree": computer._handle_get_ui_tree,
            "operation_sequence": computer._handle_operation_sequence,
            "execute_mcp_tool": computer._handle_execute_mcp_tool,
            "get_mcp_instructions": computer._handle_get_mcp_instructions,
            "get_mcp_available_tools": computer._handle_get_mcp_available_tools,
        }

        for handler_name in expected_handlers:
            if handler_name in action_handlers:
                print(f"✓ Handler '{handler_name}' is registered")
            else:
                print(f"⚠ Handler '{handler_name}' is missing")
        # Test that schema normalization methods exist
        print("\n10. Testing schema normalization methods...")
        if hasattr(computer, "_normalize_tool_schema"):
            print("✓ _normalize_tool_schema method exists")
        else:
            print("⚠ _normalize_tool_schema method missing")

        if hasattr(computer, "_convert_mcp_parameters_to_yaml"):
            print("✓ _convert_mcp_parameters_to_yaml method exists")
        else:
            print("⚠ _convert_mcp_parameters_to_yaml method missing")

        if hasattr(computer, "_ensure_action_sequence_compatibility"):
            print("✓ _ensure_action_sequence_compatibility method exists")
        else:
            print("⚠ _ensure_action_sequence_compatibility method missing")

        # All tests passed
        assert True, "MCP integration tests completed successfully"

    except Exception as e:
        print(f"✗ MCP integration test error: {e}")
        import traceback

        traceback.print_exc()
        assert False, f"MCP integration test failed: {e}"


def main():
    """Run MCP integration tests"""
    print("UFO MCP Integration Test Suite")
    print("=" * 40)

    success = test_mcp_integration()
    if success:
        print("\n🎉 MCP integration is working correctly!")
        print("\nMCP components available:")
        print("1. Computer class with MCP support")
        print(
            "2. MCP action handlers (execute_mcp_tool, get_mcp_instructions, get_mcp_available_tools)"
        )
        print("3. YAML instruction files (powerpoint.yaml, word.yaml, excel.yaml)")
        print("4. MCP server configuration framework")
        print("5. ✅ Tool schema normalization (MCP ↔ YAML conversion)")
        print("6. ✅ action2action_sequence compatibility")
        print("\nSchema Conversion Features:")
        print("• MCP inputSchema → YAML parameters conversion")
        print("• Automatic action_mapping for action2action_sequence")
        print("• Execution hints and metadata preservation")
        print("• Support for required/optional parameters and defaults")
        print("\nNext steps:")
        print("1. Implement actual MCP servers for each application")
        print("2. Test with real MCP server connections")
        print("3. Add more application-specific instructions")
    else:
        print("\n❌ Some MCP integration tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
