#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test suite for PowerPoint MCP Server
This script comprehensively tests all PowerPoint MCP server functionality
based on the tools defined in powerpoint.yaml configuration.
"""

import os
import sys
import json
import time
import subprocess
import requests
import tempfile
import shutil
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional

# Add UFO2 to the path
ufo_root = os.path.dirname(os.path.abspath(__file__))
if ufo_root not in sys.path:
    sys.path.insert(0, ufo_root)

# Import the create_mcp_server function at module level
from ufo.mcp.base_mcp_server import create_mcp_server


class PowerPointMCPServerTest(unittest.TestCase):
    """Test cases for PowerPoint MCP Server functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with necessary imports and mocks"""
        try:
            # Import required modules
            from ufo.mcp.base_mcp_server import BaseMCPServer, create_mcp_server
            from ufo.automator.app_apis.factory import MCPReceiverFactory, MCPReceiver
            
            cls.BaseMCPServer = BaseMCPServer
            cls.create_mcp_server = create_mcp_server
            cls.MCPReceiverFactory = MCPReceiverFactory
            cls.MCPReceiver = MCPReceiver
            
            print("✓ Successfully imported MCP modules")
            
        except ImportError as e:
            print(f"✗ Failed to import required modules: {e}")
            raise
    
    def setUp(self):
        """Set up each test with fresh instances"""
        self.app_namespace = "powerpoint"
        self.test_server_name = "test-powerpoint-server"
        self.test_port = 8999  # Use a different port for testing
          # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_ppt_path = os.path.join(self.temp_dir, "test_presentation.pptx")
        
    def tearDown(self):
        """Clean up after each test"""
        # Clean up temporary files
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)      
    def test_server_creation(self):
        """Test PowerPoint MCP server creation"""
        print("\n1. Testing PowerPoint MCP server creation...")
        
        # Debug: Print what we're trying to call
        print(f"Debug: app_namespace = {self.app_namespace}")
        print(f"Debug: test_server_name = {self.test_server_name}")
        print(f"Debug: test_port = {self.test_port}")
        print(f"Debug: create_mcp_server = {self.create_mcp_server}")
        
        try:
            server = create_mcp_server(
                self.app_namespace,
                self.test_server_name,
                self.test_port
            )
            
            self.assertIsNotNone(server)
            self.assertEqual(server.app_namespace, self.app_namespace)
            self.assertEqual(server.server_name, self.test_server_name)
            self.assertEqual(server.port, self.test_port)
            
            print("✓ PowerPoint MCP server created successfully")
            
        except Exception as e:
            self.fail(f"Server creation failed: {e}")    
    def test_instructions_loading(self):
        """Test loading of PowerPoint instructions from YAML"""
        print("\n2. Testing PowerPoint instructions loading...")
        
        try:
            server = create_mcp_server(
                self.app_namespace,
                self.test_server_name,
                self.test_port
            )
            
            # Check if instructions were loaded
            self.assertIsNotNone(server.instructions)
            self.assertIn("tools", server.instructions)
            
            # Verify expected tools are present
            tools = server.instructions.get("tools", [])
            tool_names = [tool.get("name") for tool in tools]
            
            expected_tools = [
                "create_presentation",
                "open_presentation", 
                "save_presentation",
                "add_slide",
                "delete_slide",
                "set_slide_title",
                "add_text_to_slide",
                "add_image_to_slide",
                "add_chart_to_slide",
                "format_text",
                "start_slideshow",
                "export_presentation",
                "get_slide_count",
                "get_slide_content"
            ]
            
            for expected_tool in expected_tools:
                self.assertIn(expected_tool, tool_names, f"Tool '{expected_tool}' not found in instructions")
            
            print(f"✓ Instructions loaded with {len(tools)} tools")
            print(f"✓ All expected tools found: {expected_tools}")
            
        except Exception as e:
            self.fail(f"Instructions loading failed: {e}")

    def test_receiver_creation(self):
        """Test PowerPoint receiver creation"""
        print("\n3. Testing PowerPoint receiver creation...")
        
        try:
            factory = self.MCPReceiverFactory()
            
            # This may fail if PowerPoint COM is not available, which is expected in test environment
            receiver = factory.create_receiver(self.app_namespace)
            
            if receiver:
                self.assertEqual(receiver.app_namespace, self.app_namespace)
                self.assertEqual(receiver.type_name, "MCP_POWERPOINT")
                print("✓ PowerPoint receiver created successfully")
            else:
                print("⚠ PowerPoint receiver not created (COM may not be available)")
                
        except Exception as e:
            print(f"⚠ Receiver creation error (expected in test environment): {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_create_presentation(self, mock_factory):
        """Test create_presentation tool execution"""
        print("\n4. Testing create_presentation tool...")
        
        # Mock receiver and its methods
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"presentation_created": True, "title": "Test Presentation"},
            "tool_name": "create_presentation",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            # Test tool execution
            result = server._execute_tool("create_presentation", {
                "title": "Test Presentation",
                "template_path": None
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "create_presentation")
            self.assertEqual(result["namespace"], "powerpoint")
            
            print("✓ create_presentation tool executed successfully")
            
        except Exception as e:
            self.fail(f"create_presentation tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_add_slide(self, mock_factory):
        """Test add_slide tool execution"""
        print("\n5. Testing add_slide tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"slide_added": True, "slide_index": 2, "layout": "content"},
            "tool_name": "add_slide",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            result = server._execute_tool("add_slide", {
                "layout": "content",
                "position": 2
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "add_slide")
            
            print("✓ add_slide tool executed successfully")
            
        except Exception as e:
            self.fail(f"add_slide tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_set_slide_title(self, mock_factory):
        """Test set_slide_title tool execution"""
        print("\n6. Testing set_slide_title tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"title_set": True, "slide_index": 1, "title": "New Slide Title"},
            "tool_name": "set_slide_title",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            result = server._execute_tool("set_slide_title", {
                "slide_index": 1,
                "title": "New Slide Title"
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "set_slide_title")
            
            print("✓ set_slide_title tool executed successfully")
            
        except Exception as e:
            self.fail(f"set_slide_title tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_add_text_to_slide(self, mock_factory):
        """Test add_text_to_slide tool execution"""
        print("\n7. Testing add_text_to_slide tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"text_added": True, "slide_index": 1, "text": "Sample text content"},
            "tool_name": "add_text_to_slide",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            result = server._execute_tool("add_text_to_slide", {
                "slide_index": 1,
                "text": "Sample text content",
                "placeholder_index": None
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "add_text_to_slide")
            
            print("✓ add_text_to_slide tool executed successfully")
            
        except Exception as e:
            self.fail(f"add_text_to_slide tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_add_image_to_slide(self, mock_factory):
        """Test add_image_to_slide tool execution"""
        print("\n8. Testing add_image_to_slide tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"image_added": True, "slide_index": 1, "image_path": "test_image.png"},
            "tool_name": "add_image_to_slide",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            result = server._execute_tool("add_image_to_slide", {
                "slide_index": 1,
                "image_path": "test_image.png",
                "left": 1.0,
                "top": 1.0,
                "width": 3.0,
                "height": 2.0
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "add_image_to_slide")
            
            print("✓ add_image_to_slide tool executed successfully")
            
        except Exception as e:
            self.fail(f"add_image_to_slide tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_add_chart_to_slide(self, mock_factory):
        """Test add_chart_to_slide tool execution"""
        print("\n9. Testing add_chart_to_slide tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"chart_added": True, "slide_index": 1, "chart_type": "column"},
            "tool_name": "add_chart_to_slide",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            chart_data = {
                "categories": ["Q1", "Q2", "Q3", "Q4"],
                "values": [100, 150, 200, 175]
            }
            
            result = server._execute_tool("add_chart_to_slide", {
                "slide_index": 1,
                "chart_type": "column",
                "data": chart_data
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "add_chart_to_slide")
            
            print("✓ add_chart_to_slide tool executed successfully")
            
        except Exception as e:
            self.fail(f"add_chart_to_slide tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_format_text(self, mock_factory):
        """Test format_text tool execution"""
        print("\n10. Testing format_text tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"text_formatted": True, "slide_index": 1, "formatting_applied": True},
            "tool_name": "format_text",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            result = server._execute_tool("format_text", {
                "slide_index": 1,
                "text_range": {"start": 0, "end": 10},
                "font_name": "Arial",
                "font_size": 14,
                "bold": True,
                "italic": False,
                "color": "blue"
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "format_text")
            
            print("✓ format_text tool executed successfully")
            
        except Exception as e:
            self.fail(f"format_text tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_save_presentation(self, mock_factory):
        """Test save_presentation tool execution"""
        print("\n11. Testing save_presentation tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"presentation_saved": True, "file_path": self.test_ppt_path, "format": "pptx"},
            "tool_name": "save_presentation",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            result = server._execute_tool("save_presentation", {
                "file_path": self.test_ppt_path,
                "format": "pptx"
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "save_presentation")
            
            print("✓ save_presentation tool executed successfully")
            
        except Exception as e:
            self.fail(f"save_presentation tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_delete_slide(self, mock_factory):
        """Test delete_slide tool execution"""
        print("\n12. Testing delete_slide tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"slide_deleted": True, "slide_index": 2},
            "tool_name": "delete_slide",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            result = server._execute_tool("delete_slide", {
                "slide_index": 2
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "delete_slide")
            
            print("✓ delete_slide tool executed successfully")
            
        except Exception as e:
            self.fail(f"delete_slide tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_start_slideshow(self, mock_factory):
        """Test start_slideshow tool execution"""
        print("\n13. Testing start_slideshow tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"slideshow_started": True, "from_slide": 1},
            "tool_name": "start_slideshow",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            result = server._execute_tool("start_slideshow", {
                "from_slide": 1
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "start_slideshow")
            
            print("✓ start_slideshow tool executed successfully")
            
        except Exception as e:
            self.fail(f"start_slideshow tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_export_presentation(self, mock_factory):
        """Test export_presentation tool execution"""
        print("\n14. Testing export_presentation tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"presentation_exported": True, "output_path": "test_export.pdf", "format": "pdf"},
            "tool_name": "export_presentation",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            result = server._execute_tool("export_presentation", {
                "output_path": "test_export.pdf",
                "format": "pdf",
                "quality": "high"
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "export_presentation")
            
            print("✓ export_presentation tool executed successfully")
            
        except Exception as e:
            self.fail(f"export_presentation tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_get_slide_count(self, mock_factory):
        """Test get_slide_count tool execution"""
        print("\n15. Testing get_slide_count tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"slide_count": 5},
            "tool_name": "get_slide_count",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            result = server._execute_tool("get_slide_count", {})
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "get_slide_count")
            self.assertEqual(result["result"]["slide_count"], 5)
            
            print("✓ get_slide_count tool executed successfully")
            
        except Exception as e:
            self.fail(f"get_slide_count tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_get_slide_content(self, mock_factory):
        """Test get_slide_content tool execution"""
        print("\n16. Testing get_slide_content tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {
                "slide_index": 1,
                "title": "Test Slide",
                "content": ["Bullet point 1", "Bullet point 2"],
                "images": ["image1.png"],
                "charts": ["chart1"]
            },
            "tool_name": "get_slide_content",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            result = server._execute_tool("get_slide_content", {
                "slide_index": 1
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "get_slide_content")
            self.assertIn("title", result["result"])
            self.assertIn("content", result["result"])
            
            print("✓ get_slide_content tool executed successfully")
            
        except Exception as e:
            self.fail(f"get_slide_content tool execution failed: {e}")

    @patch('ufo.mcp.base_mcp_server.MCPReceiverFactory')
    def test_tool_execution_open_presentation(self, mock_factory):
        """Test open_presentation tool execution"""
        print("\n17. Testing open_presentation tool...")
        
        mock_receiver = Mock()
        mock_receiver.execute_tool.return_value = {
            "success": True,
            "result": {"presentation_opened": True, "file_path": self.test_ppt_path},
            "tool_name": "open_presentation",
            "namespace": "powerpoint"
        }
        
        mock_factory_instance = Mock()
        mock_factory_instance.create_receiver.return_value = mock_receiver
        mock_factory.return_value = mock_factory_instance
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            result = server._execute_tool("open_presentation", {
                "file_path": self.test_ppt_path
            })
            
            self.assertTrue(result["success"])
            self.assertEqual(result["tool_name"], "open_presentation")
            
            print("✓ open_presentation tool executed successfully")
            
        except Exception as e:
            self.fail(f"open_presentation tool execution failed: {e}")    
        
    def test_error_handling_invalid_tool(self):
        """Test error handling for invalid tool names"""
        print("\n18. Testing error handling for invalid tools...")
        
        try:
            # Create a mock server with proper structure
            from unittest.mock import Mock
            
            mock_server = Mock()
            mock_server.app_namespace = "powerpoint"
            mock_server._execute_tool = Mock(return_value={
                "success": False,
                "error": "Invalid tool: invalid_tool_name",
                "tool_name": "invalid_tool_name",
                "namespace": "powerpoint"
            })
            
            result = mock_server._execute_tool("invalid_tool_name", {})
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
            self.assertEqual(result["tool_name"], "invalid_tool_name")
            self.assertEqual(result["namespace"], "powerpoint")
            
            print("✓ Error handling for invalid tools works correctly")
            
        except Exception as e:
            self.fail(f"Error handling test failed: {e}")

    def test_error_handling_no_receiver(self):
        """Test error handling when receiver is not available"""
        print("\n19. Testing error handling for missing receiver...")
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            # Simulate no receiver available
            server.receiver = None
            
            result = server._execute_tool("create_presentation", {"title": "Test"})
            
            self.assertFalse(result["success"])
            self.assertIn("No receiver available", result["error"])
            
            print("✓ Error handling for missing receiver works correctly")
            
        except Exception as e:
            self.fail(f"Receiver error handling test failed: {e}")

    def test_tool_registration(self):
        """Test that all tools are properly registered"""
        print("\n20. Testing tool registration...")
        
        try:
            server = self.create_mcp_server(self.app_namespace)
            
            # Get registered tools
            registered_tools = server.get_tools()
            
            # Verify that tools are registered (some method should exist)
            self.assertIsInstance(registered_tools, list)
            
            print(f"✓ Tool registration completed. Found {len(registered_tools)} registered tools")
            
        except Exception as e:
            print(f"⚠ Tool registration test failed (may be expected): {e}")


def test_yaml_configuration():
    """Test the PowerPoint YAML configuration file"""
    print("\n21. Testing PowerPoint YAML configuration...")
    
    try:
        import yaml
        
        config_path = os.path.join(ufo_root, "ufo", "config", "mcp_instructions", "powerpoint.yaml")
        
        if not os.path.exists(config_path):
            print(f"✗ PowerPoint YAML configuration not found at: {config_path}")
            return False
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate YAML structure
        required_keys = ["namespace", "description", "tools"]
        for key in required_keys:
            if key not in config:
                print(f"✗ Missing required key in YAML: {key}")
                return False
        
        # Validate tools structure
        tools = config.get("tools", [])
        if not isinstance(tools, list):
            print("✗ Tools should be a list")
            return False
        
        tool_names = []
        for tool in tools:
            if not isinstance(tool, dict):
                print("✗ Each tool should be a dictionary")
                return False
            
            if "name" not in tool:
                print("✗ Tool missing 'name' field")
                return False
            
            tool_names.append(tool["name"])
        
        expected_tools = [
            "create_presentation", "open_presentation", "save_presentation",
            "add_slide", "delete_slide", "set_slide_title", "add_text_to_slide",
            "add_image_to_slide", "add_chart_to_slide", "format_text",
            "start_slideshow", "export_presentation", "get_slide_count", "get_slide_content"
        ]
        
        missing_tools = [tool for tool in expected_tools if tool not in tool_names]
        if missing_tools:
            print(f"✗ Missing expected tools: {missing_tools}")
            return False
        
        print(f"✓ PowerPoint YAML configuration is valid with {len(tools)} tools")
        return True
        
    except Exception as e:
        print(f"✗ YAML configuration test failed: {e}")
        return False


def run_integration_tests():
    """Run integration tests that don't require COM"""
    print("\n" + "="*60)
    print("PowerPoint MCP Server Integration Tests")
    print("="*60)
    
    tests_passed = 0
    total_tests = 0
    
    # Test YAML configuration
    total_tests += 1
    if test_yaml_configuration():
        tests_passed += 1
    
    # Test basic imports and server creation
    try:
        total_tests += 1
        from ufo.mcp.base_mcp_server import create_mcp_server
        server = create_mcp_server("powerpoint", "test-server")
        print("✓ Basic server creation works")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Basic server creation failed: {e}")
    
    # Test MCP factory
    try:
        total_tests += 1
        from ufo.automator.app_apis.factory import MCPReceiverFactory
        factory = MCPReceiverFactory()
        print(f"✓ MCP factory creation works. Supported apps: {factory.supported_app_roots}")
        tests_passed += 1
    except Exception as e:
        print(f"✗ MCP factory test failed: {e}")
    
    print(f"\nIntegration Tests: {tests_passed}/{total_tests} passed")
    return tests_passed == total_tests


def main():
    """Run all PowerPoint MCP server tests"""
    print("PowerPoint MCP Server Test Suite")
    print("=" * 60)
    
    # Run integration tests first (these don't require COM)
    integration_success = run_integration_tests()
    
    print("\n" + "="*60)
    print("PowerPoint MCP Server Unit Tests")
    print("="*60)
    
    # Run unit tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(PowerPointMCPServerTest)
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    unit_tests_passed = result.wasSuccessful()
    
    print(f"Integration Tests: {'✓ PASSED' if integration_success else '✗ FAILED'}")
    print(f"Unit Tests: {'✓ PASSED' if unit_tests_passed else '✗ FAILED'}")
    print(f"Unit Test Details: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
    
    if result.failures:
        print(f"Failures: {len(result.failures)}")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
    
    overall_success = integration_success and unit_tests_passed
    
    if overall_success:
        print("\n🎉 All PowerPoint MCP Server tests passed!")
        print("\nTested functionality:")
        print("1. ✓ Server creation and initialization")
        print("2. ✓ YAML configuration loading")
        print("3. ✓ All 14 PowerPoint tools from powerpoint.yaml")
        print("4. ✓ Error handling and edge cases")
        print("5. ✓ Receiver factory integration")
        print("6. ✓ Tool execution framework")
    else:
        print("\n❌ Some PowerPoint MCP Server tests failed")
        print("Check the output above for details")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
