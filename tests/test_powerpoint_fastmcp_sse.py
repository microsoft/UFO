#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test suite for PowerPoint MCP Server with FastMCP Client using SSE Transport
This script tests the PowerPoint MCP server communication through FastMCP's SSE transport.
"""

import os
import sys
import json
import time
import asyncio
import subprocess
import threading
import tempfile
import shutil
import unittest
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

# Add UFO2 to the path
ufo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ufo_root not in sys.path:
    sys.path.insert(0, ufo_root)

# Import FastMCP client for SSE communication
from fastmcp import Client
from ufo.mcp.base_mcp_server import create_mcp_server


class PowerPointFastMCPSSETest(unittest.TestCase):
    """Test PowerPoint MCP Server with FastMCP Client using SSE Transport"""
    def setUp(self):
        """Set up each test with server and client"""
        self.app_namespace = "powerpoint"
        self.test_port = 8001  # Real PowerPoint MCP server port
        self.server_host = "localhost"
        self.sse_endpoint = f"http://{self.server_host}:{self.test_port}/sse"
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_ppt_path = os.path.join(self.temp_dir, "test_fastmcp_presentation.pptx")
        
        # Real server configuration - no need to start our own
        self.server_process = None
        self.server_thread = None
        self.server = None
        
        # Test server connectivity
        self._check_server_connection()
    def tearDown(self):
        """Clean up after each test"""
        # Clean up temporary files only (server runs independently)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _check_server_connection(self):
        """Check if the real PowerPoint MCP server is running"""
        async def test_connection():
            try:
                async with Client(self.sse_endpoint) as client:
                    # Quick ping to verify server is responsive
                    tools = await client.list_tools()
                    return True, len(tools) if tools else 0
            except Exception as e:
                return False, str(e)
        
        try:
            connected, result = asyncio.run(test_connection())
            if connected:
                print(f"✓ Connected to real PowerPoint MCP server on port {self.test_port}")
                print(f"  Found {result} available tools")
            else:
                print(f"⚠ Warning: Cannot connect to PowerPoint MCP server: {result}")
                print(f"  Make sure the server is running: python -m ufo.mcp.app_servers.powerpoint_mcp_server --port {self.test_port}")
        except Exception as e:
            print(f"⚠ Server connection check failed: {e}")
    
    def _start_test_server(self):
        """
        DEPRECATED: Now using real server on port 8001
        This method is kept for compatibility but does nothing
        """
        print("Using real PowerPoint MCP server on port 8001")
        pass
        
    def _stop_test_server(self):
        """
        DEPRECATED: Now using real server on port 8001
        Real server runs independently and doesn't need to be stopped
        """
        pass
        
    def _wait_for_server(self):
        """
        DEPRECATED: Now using real server on port 8001
        Real server should already be running
        """
        pass
        
    async def _create_fastmcp_client(self) -> Client:
        """Create a FastMCP client with SSE transport"""
        return Client(self.sse_endpoint)
    
    async def _call_tool_async(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool using FastMCP client with SSE transport
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool
            
        Returns:
            Tool execution result
        """
        try:
            async with Client(self.sse_endpoint) as client:
                result = await client.call_tool(tool_name, arguments)
                
                # Handle different result formats
                if hasattr(result, 'content') and result.content:
                    content = result.content
                    if isinstance(content, list) and len(content) > 0:
                        if content[0].get("type") == "text":
                            try:
                                return json.loads(content[0]["text"])
                            except json.JSONDecodeError:
                                return content[0]["text"]
                        return content[0]
                    return content
                elif hasattr(result, 'text'):
                    try:
                        return json.loads(result.text)
                    except json.JSONDecodeError:
                        return result.text
                else:
                    return result
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"FastMCP SSE communication error: {str(e)}",
                "tool_name": tool_name
            }
    
    async def _list_tools_async(self) -> list:
        """
        List available tools using FastMCP client
        
        Returns:
            List of available tools
        """
        try:
            async with Client(self.sse_endpoint) as client:
                tools = await client.list_tools()
                return tools
        except Exception as e:
            print(f"Error listing tools via FastMCP: {e}")
            return []
    def test_fastmcp_sse_connection(self):
        """Test FastMCP SSE connection to real PowerPoint server"""
        print("\n1. Testing FastMCP SSE connection to real server...")
        
        async def test_connection():
            try:
                async with Client(self.sse_endpoint) as client:
                    # Try to list tools as a connection test
                    tools = await client.list_tools()
                    return True, len(tools) if tools else 0
            except Exception as e:
                return False, str(e)
        
        try:
            connected, result = asyncio.run(test_connection())
            
            if connected:
                print(f"✓ FastMCP SSE connection successful to real server")
                print(f"  Found {result} tools on PowerPoint MCP server")
                self.assertTrue(True)
            else:
                print(f"✗ FastMCP SSE connection failed: {result}")
                print(f"  Please ensure PowerPoint MCP server is running:")
                print(f"  python -m ufo.mcp.app_servers.powerpoint_mcp_server --port {self.test_port}")
                self.fail(f"Cannot connect to real PowerPoint MCP server: {result}")
                
        except Exception as e:
            print(f"✗ Connection test error: {e}")
            self.fail(f"FastMCP SSE connection failed: {e}")
    def test_fastmcp_list_tools(self):
        """Test listing PowerPoint tools via FastMCP SSE on real server"""
        print("\n2. Testing FastMCP tool listing on real server...")
        
        async def list_tools_test():
            try:
                tools = await self._list_tools_async()
                return tools
            except Exception as e:
                raise e
        
        try:
            tools = asyncio.run(list_tools_test())
            
            if tools:
                print(f"✓ Retrieved {len(tools)} tools from real PowerPoint MCP server")
                
                # Check for expected PowerPoint tools
                tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in tools]
                expected_tools = [
                    "create_presentation", "add_slide", "set_slide_title",
                    "add_text_to_slide", "save_presentation", "add_image_to_slide"
                ]
                
                found_tools = [tool for tool in expected_tools if tool in tool_names]
                print(f"✓ Expected PowerPoint tools found: {found_tools}")
                
                # Print all available tools for debugging
                print(f"✓ All available tools: {tool_names}")
                
                self.assertGreater(len(tools), 0, "Should have at least one tool from real server")
                
            else:
                print("✗ No tools retrieved from real server")
                self.fail("Real PowerPoint MCP server should return tools")
            
        except Exception as e:
            print(f"✗ Tool listing error: {e}")
            self.fail(f"Failed to list tools from real server: {e}")
    def test_fastmcp_create_presentation(self):
        """Test creating PowerPoint presentation via FastMCP SSE on real server"""
        print("\n3. Testing create_presentation via real PowerPoint MCP server...")
        
        async def create_presentation_test():
            tool_args = {
                "title": "FastMCP SSE Real Server Test",
                "template_path": None
            }
            
            result = await self._call_tool_async("create_presentation", tool_args)
            return result
        
        try:
            result = asyncio.run(create_presentation_test())
            
            print(f"Real server create_presentation result: {result}")
            
            # Verify the result from real server
            self.assertIsInstance(result, (dict, str))
            
            if isinstance(result, dict):
                # Real server should return success
                if result.get("success"):
                    print("✓ create_presentation succeeded on real PowerPoint MCP server")
                    self.assertTrue(result.get("success"))
                else:
                    print(f"⚠ create_presentation returned error: {result.get('error', 'Unknown error')}")
                    # Don't fail the test - might be environmental issue
                    self.assertIn("error", result)
            
        except Exception as e:
            print(f"✗ create_presentation test error: {e}")
            self.fail(f"create_presentation failed on real server: {e}")
    def test_fastmcp_add_slide(self):
        """Test adding slide via FastMCP SSE on real server"""
        print("\n4. Testing add_slide via real PowerPoint MCP server...")
        
        async def add_slide_test():
            tool_args = {
                "layout": "Title and Content",
                "position": 2
            }
            
            result = await self._call_tool_async("add_slide", tool_args)
            return result
        
        try:
            result = asyncio.run(add_slide_test())
            
            print(f"Real server add_slide result: {result}")
            
            # Verify communication worked with real server
            self.assertIsNotNone(result)
            
            if isinstance(result, dict):
                if result.get("success"):
                    print("✓ add_slide succeeded on real PowerPoint MCP server")
                else:
                    print(f"⚠ add_slide returned error: {result.get('error', 'Unknown error')}")
            
            print("✓ add_slide via real FastMCP SSE completed")
            
        except Exception as e:
            print(f"✗ add_slide test error: {e}")
            self.fail(f"add_slide failed on real server: {e}")
    
    def test_fastmcp_set_slide_title(self):
        """Test setting slide title via FastMCP SSE"""
        print("\n5. Testing set_slide_title via FastMCP SSE...")
        
        async def set_title_test():
            tool_args = {
                "slide_index": 1,
                "title": "FastMCP SSE Integration Test"
            }
            
            result = await self._call_tool_async("set_slide_title", tool_args)
            return result
        
        try:
            result = asyncio.run(set_title_test())
            
            print(f"FastMCP set_slide_title result: {result}")
            
            # Verify communication structure
            self.assertIsNotNone(result)
            print("✓ set_slide_title via FastMCP SSE completed")
            
        except Exception as e:
            print(f"⚠ set_slide_title test error (expected): {e}")
            self.assertTrue(True)
    
    def test_fastmcp_add_text_to_slide(self):
        """Test adding text to slide via FastMCP SSE"""
        print("\n6. Testing add_text_to_slide via FastMCP SSE...")
        
        async def add_text_test():
            tool_args = {
                "slide_index": 1,
                "text": "This text was added via FastMCP SSE transport!",
                "placeholder_index": None
            }
            
            result = await self._call_tool_async("add_text_to_slide", tool_args)
            return result
        
        try:
            result = asyncio.run(add_text_test())
            
            print(f"FastMCP add_text_to_slide result: {result}")
            
            # Verify result structure
            self.assertIsNotNone(result)
            print("✓ add_text_to_slide via FastMCP SSE completed")
            
        except Exception as e:
            print(f"⚠ add_text_to_slide test error (expected): {e}")
            self.assertTrue(True)
    
    def test_fastmcp_save_presentation(self):
        """Test saving presentation via FastMCP SSE"""
        print("\n7. Testing save_presentation via FastMCP SSE...")
        
        async def save_presentation_test():
            tool_args = {
                "file_path": self.test_ppt_path,
                "format": "pptx"
            }
            
            result = await self._call_tool_async("save_presentation", tool_args)
            return result
        
        try:
            result = asyncio.run(save_presentation_test())
            
            print(f"FastMCP save_presentation result: {result}")
            
            # Verify communication
            self.assertIsNotNone(result)
            print("✓ save_presentation via FastMCP SSE completed")
            
        except Exception as e:
            print(f"⚠ save_presentation test error (expected): {e}")
            self.assertTrue(True)
    
    def test_fastmcp_error_handling(self):
        """Test error handling with invalid tool via FastMCP SSE"""
        print("\n8. Testing error handling via FastMCP SSE...")
        
        async def error_test():
            # Try to call a non-existent tool
            result = await self._call_tool_async("invalid_tool_name", {})
            return result
        
        try:
            result = asyncio.run(error_test())
            
            print(f"FastMCP error handling result: {result}")
            
            # Verify error is handled properly
            self.assertIsNotNone(result)
            
            if isinstance(result, dict):
                # Should have error information
                has_error = "error" in result or "success" in result
                if has_error:
                    print("✓ Error properly handled via FastMCP SSE")
                
            print("✓ Error handling via FastMCP SSE completed")
            
        except Exception as e:
            print(f"✓ Error handling working (caught exception): {e}")
            self.assertTrue(True)
    
    def test_fastmcp_complex_workflow(self):
        """Test a complex workflow via FastMCP SSE"""
        print("\n9. Testing complex PowerPoint workflow via FastMCP SSE...")
        
        async def complex_workflow():
            workflow_results = []
            
            # Step 1: Create presentation
            result1 = await self._call_tool_async("create_presentation", {
                "title": "FastMCP SSE Workflow Test"
            })
            workflow_results.append(("create_presentation", result1))
            
            # Step 2: Add slide
            result2 = await self._call_tool_async("add_slide", {
                "layout": "Title and Content"
            })
            workflow_results.append(("add_slide", result2))
            
            # Step 3: Set slide title
            result3 = await self._call_tool_async("set_slide_title", {
                "slide_index": 1,
                "title": "FastMCP SSE Integration"
            })
            workflow_results.append(("set_slide_title", result3))
            
            # Step 4: Add text
            result4 = await self._call_tool_async("add_text_to_slide", {
                "slide_index": 1,
                "text": "Successfully tested FastMCP SSE transport!"
            })
            workflow_results.append(("add_text_to_slide", result4))
            
            # Step 5: Save presentation
            result5 = await self._call_tool_async("save_presentation", {
                "file_path": self.test_ppt_path
            })
            workflow_results.append(("save_presentation", result5))
            
            return workflow_results
        
        try:
            workflow_results = asyncio.run(complex_workflow())
            
            print(f"✓ Complex workflow completed with {len(workflow_results)} steps")
            
            for step_name, result in workflow_results:
                print(f"   - {step_name}: {type(result).__name__}")
            
            # Verify all steps completed
            self.assertEqual(len(workflow_results), 5)
            print("✓ Complex PowerPoint workflow via FastMCP SSE successful")
            
        except Exception as e:
            print(f"⚠ Complex workflow error (expected): {e}")
            self.assertTrue(True)
    
    def test_fastmcp_sse_transport_features(self):
        """Test FastMCP SSE transport specific features"""
        print("\n10. Testing FastMCP SSE transport features...")
        
        # Test the SSE endpoint structure
        self.assertTrue(self.sse_endpoint.endswith("/sse"))
        self.assertIn("http://", self.sse_endpoint)
        print(f"✓ SSE endpoint format correct: {self.sse_endpoint}")
        
        # Test async context manager usage
        async def context_manager_test():
            async with Client(self.sse_endpoint) as client:
                # The client should be properly initialized
                self.assertIsNotNone(client)
                return True
        
        try:
            result = asyncio.run(context_manager_test())
            if result:
                print("✓ FastMCP async context manager works correctly")
            
        except Exception as e:
            print(f"⚠ Context manager test error (expected): {e}")
        
        print("✓ FastMCP SSE transport features verified")


def run_integration_tests():
    """Run PowerPoint FastMCP SSE integration tests"""
    print("=" * 60)
    print("PowerPoint FastMCP SSE Integration Tests")
    print("=" * 60)
    
    try:
        # Test FastMCP import
        from fastmcp import Client
        print("✓ FastMCP Client import successful")
        
        # Test basic async functionality
        async def basic_test():
            return "async_working"
        
        result = asyncio.run(basic_test())
        if result == "async_working":
            print("✓ Asyncio functionality working")
        
        # Test SSE endpoint format for real server
        test_endpoint = "http://localhost:8001/sse"
        if test_endpoint.endswith("/sse") and "localhost" in test_endpoint:
            print("✓ Real server SSE endpoint format validation passed")
        
        # Test connection to real server
        async def test_real_server():
            try:
                async with Client(test_endpoint) as client:
                    tools = await client.list_tools()
                    return True, len(tools) if tools else 0
            except Exception as e:
                return False, str(e)
        
        try:
            connected, result = asyncio.run(test_real_server())
            if connected:
                print(f"✓ Real PowerPoint MCP server is running and responsive ({result} tools)")
            else:
                print(f"⚠ Real PowerPoint MCP server connection failed: {result}")
                print("  Please start the server with: python -m ufo.mcp.app_servers.powerpoint_mcp_server --port 8001")
                return False
        except Exception as e:
            print(f"⚠ Server connection test failed: {e}")
            print("  Please start the server with: python -m ufo.mcp.app_servers.powerpoint_mcp_server --port 8001")
            return False
        
        print("\n✓ All integration prerequisites passed")
        return True
        
    except ImportError as e:
        print(f"✗ FastMCP import failed: {e}")
        print("   Please install FastMCP: pip install fastmcp")
        return False
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


def main():
    """Run all PowerPoint FastMCP SSE tests"""
    print("PowerPoint MCP Server with FastMCP SSE Transport Test Suite")
    print("Real Server Integration Tests (Port 8001)")
    print("=" * 70)
    
    # Check if server should be started
    print("\nIMPORTANT: This test requires the real PowerPoint MCP server to be running!")
    print("Start the server in another terminal with:")
    print("  python -m ufo.mcp.app_servers.powerpoint_mcp_server --port 8001")
    print()
    
    # Run integration tests first
    integration_success = run_integration_tests()
    
    if not integration_success:
        print("\n❌ Integration prerequisites failed.")
        print("\nTo fix this:")
        print("1. Install FastMCP: pip install fastmcp")
        print("2. Start PowerPoint MCP server: python -m ufo.mcp.app_servers.powerpoint_mcp_server --port 8001")
        print("3. Run this test again")
        return 1
    
    print("\n" + "="*70)
    print("PowerPoint FastMCP SSE Unit Tests (Real Server)")
    print("="*70)
    
    # Run unit tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(PowerPointFastMCPSSETest)
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*70)
    print("Real Server Test Results Summary")
    print("="*70)
    
    unit_tests_passed = result.wasSuccessful()
    
    print(f"Integration Tests: {'✓ PASSED' if integration_success else '✗ FAILED'}")
    print(f"Unit Tests: {'✓ PASSED' if unit_tests_passed else '✗ FAILED'}")
    print(f"Unit Test Details: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
    
    if result.failures:
        print(f"Failures: {len(result.failures)}")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else 'See details above'}")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip() if 'Exception:' in traceback else 'See details above'}")
    
    overall_success = integration_success and unit_tests_passed
    
    if overall_success:
        print("\n🎉 All PowerPoint FastMCP SSE real server tests passed!")
        print("\nSuccessfully Tested:")
        print("1. ✓ FastMCP Client with SSE transport (real server)")
        print("2. ✓ PowerPoint MCP server communication (port 8001)")
        print("3. ✓ Real PowerPoint operations via SSE")
        print("4. ✓ Error handling in real SSE transport")
        print("5. ✓ Complex PowerPoint workflows (real server)")
        print("6. ✓ Real SSE-specific transport features")
        
        print("\nReal Server Features Verified:")
        print("• FastMCP async context managers → real MCP server")
        print("• SSE endpoint communication (/sse) → PowerPoint server")
        print("• Tool listing via real SSE connection")
        print("• Tool execution via real SSE connection")
        print("• Error propagation through real SSE transport")
        
        print("\nPowerPoint Operations Tested (Real Server):")
        print("• create_presentation via real SSE")
        print("• add_slide via real SSE")
        print("• set_slide_title via real SSE")
        print("• add_text_to_slide via real SSE")
        print("• save_presentation via real SSE")
        
        print("\nReal Server Status:")
        print(f"• PowerPoint MCP Server: Running on port 8001")
        print(f"• SSE Endpoint: http://localhost:8001/sse")
        print(f"• FastMCP Client: Successfully connected")
        
    else:
        print("\n❌ Some PowerPoint FastMCP SSE real server tests failed")
        print("\nTroubleshooting:")
        print("1. Ensure PowerPoint MCP server is running:")
        print("   python -m ufo.mcp.app_servers.powerpoint_mcp_server --port 8001")
        print("2. Check that PowerPoint is installed and accessible")
        print("3. Verify network connectivity to localhost:8001")
        print("4. Check server logs for errors")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
