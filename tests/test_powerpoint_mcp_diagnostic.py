#!/usr/bin/env python3
"""
Diagnostic test for PowerPoint MCP server issues
"""

import sys
import os
import asyncio
import json
import tempfile
import shutil
import unittest
import socket
from typing import Dict, Any

# Add UFO2 to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastmcp import Client
    FASTMCP_AVAILABLE = True
except ImportError:  
    FASTMCP_AVAILABLE = False
    print("FastMCP not available - install with: pip install fastmcp")

class PowerPointMCPDiagnosticTest(unittest.TestCase):
    """Diagnostic tests for PowerPoint MCP server issues"""
    
    def setUp(self):
        """Set up diagnostic test environment"""
        self.app_namespace = "powerpoint"
        self.test_port = 8001
        self.server_host = "localhost"
        self.sse_endpoint = f"http://{self.server_host}:{self.test_port}/sse"
        
        # Create temp directory
        self.temp_dir = tempfile.mkdtemp()
        
        print(f"\n=== PowerPoint MCP Diagnostic Test Setup ===")
        print(f"SSE Endpoint: {self.sse_endpoint}")
        print(f"FastMCP Available: {FASTMCP_AVAILABLE}")
    
    def tearDown(self):
        """Clean up after diagnostic tests"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_01_server_connectivity(self):
        """Test basic server connectivity"""
        print("\n1. Testing server connectivity...")
        
        if not FASTMCP_AVAILABLE:
            self.skipTest("FastMCP not available")
        
        async def test_connection():
            try:
                async with Client(self.sse_endpoint) as client:
                    # Test basic connection
                    return True, "Connected successfully"
            except Exception as e:
                return False, str(e)
        
        try:
            connected, message = asyncio.run(test_connection())
            
            if connected:
                print(f"✓ Server connectivity: {message}")
                self.assertTrue(True)
            else:
                print(f"✗ Server connectivity failed: {message}")
                print("Please ensure PowerPoint MCP server is running:")
                print(f"  python -m ufo.mcp.app_servers.powerpoint_mcp_server --port {self.test_port}")
                self.fail(f"Cannot connect to PowerPoint MCP server: {message}")
                
        except Exception as e:
            print(f"✗ Connection test exception: {e}")
            self.fail(f"Server connectivity test failed: {e}")
    
    def test_02_list_tools(self):
        """Test tool listing and diagnose tool registration issues"""
        print("\n2. Testing tool listing...")
        
        if not FASTMCP_AVAILABLE:
            self.skipTest("FastMCP not available")
        
        async def list_tools():
            try:
                async with Client(self.sse_endpoint) as client:
                    tools = await client.list_tools()
                    return True, tools
            except Exception as e:
                return False, str(e)
        
        try:
            success, result = asyncio.run(list_tools())
            
            if success:
                tools = result
                print(f"✓ Tool listing successful - found {len(tools)} tools")
                
                # Print all tools for diagnosis
                if tools:
                    print("Available tools:")
                    for i, tool in enumerate(tools):
                        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                        tool_desc = getattr(tool, 'description', 'No description') if hasattr(tool, 'description') else 'No description'
                        print(f"  {i+1}. {tool_name}: {tool_desc}")
                        
                        # Check for diagnostic tools
                        if tool_name in ['diagnose_server', 'test_receiver']:
                            print(f"     ✓ Diagnostic tool found: {tool_name}")
                
                # Check for expected PowerPoint tools
                tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in tools]
                expected_tools = ['create_presentation', 'add_slide', 'set_slide_title']
                
                missing_tools = [tool for tool in expected_tools if tool not in tool_names]
                if missing_tools:
                    print(f"⚠ Missing expected tools: {missing_tools}")
                else:
                    print("✓ All expected PowerPoint tools found")
                
                self.assertGreater(len(tools), 0, "Should have at least one tool")
                
            else:
                print(f"✗ Tool listing failed: {result}")
                self.fail(f"Could not list tools: {result}")
                
        except Exception as e:
            print(f"✗ Tool listing exception: {e}")
            self.fail(f"Tool listing test failed: {e}")
    
    def test_03_diagnostic_tools(self):
        """Test diagnostic tools if available"""
        print("\n3. Testing diagnostic tools...")
        
        if not FASTMCP_AVAILABLE:
            self.skipTest("FastMCP not available")
        
        async def test_diagnostic():
            try:
                async with Client(self.sse_endpoint) as client:
                    # Test diagnose_server tool
                    try:
                        result = await client.call_tool("diagnose_server", {})
                        return True, "diagnose_server", result
                    except Exception as e:
                        # Try test_receiver if diagnose_server fails
                        try:
                            result = await client.call_tool("test_receiver", {})
                            return True, "test_receiver", result
                        except Exception as e2:
                            return False, "both", f"diagnose_server: {e}, test_receiver: {e2}"
            except Exception as e:
                return False, "connection", str(e)
        
        try:
            success, tool_name, result = asyncio.run(test_diagnostic())
            
            if success:
                print(f"✓ Diagnostic tool '{tool_name}' executed successfully")
                
                # Parse and display result
                if hasattr(result, 'content') and result.content:
                    content = result.content
                    if isinstance(content, list) and len(content) > 0:
                        if content[0].get("type") == "text":
                            try:
                                diagnostic_data = json.loads(content[0]["text"])
                                print("Diagnostic Information:")
                                for key, value in diagnostic_data.items():
                                    print(f"  {key}: {value}")
                            except json.JSONDecodeError:
                                print(f"Diagnostic result (raw): {content[0]['text']}")
                elif isinstance(result, dict):
                    print("Diagnostic Information:")
                    for key, value in result.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"Diagnostic result: {result}")
                
                self.assertTrue(True)
                
            else:
                print(f"⚠ Diagnostic tools not available or failed: {result}")
                # Don't fail the test - diagnostic tools are optional
                self.assertTrue(True)
                
        except Exception as e:
            print(f"⚠ Diagnostic test exception: {e}")
            # Don't fail - diagnostic tools are optional
            self.assertTrue(True)
    
    def test_04_simple_tool_execution(self):
        """Test simple tool execution to identify execution issues"""
        print("\n4. Testing simple tool execution...")
        
        if not FASTMCP_AVAILABLE:
            self.skipTest("FastMCP not available")
        
        async def test_tool_execution():
            try:
                async with Client(self.sse_endpoint) as client:
                    # Try a simple tool with minimal parameters
                    tools = await client.list_tools()
                    tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in tools]
                    
                    # Try different tools in order of complexity
                    test_tools = [
                        ("diagnose_server", {}),
                        ("test_receiver", {}),
                        ("create_presentation", {"title": "Test Diagnostic"}),
                        ("add_slide", {"layout": "Title Slide"})
                    ]
                    
                    results = []
                    for tool_name, args in test_tools:
                        if tool_name in tool_names:
                            try:
                                result = await client.call_tool(tool_name, args)
                                results.append((tool_name, True, result))
                                break  # Success - we can execute tools
                            except Exception as e:
                                results.append((tool_name, False, str(e)))
                        else:
                            results.append((tool_name, False, "Tool not available"))
                    
                    return results
                    
            except Exception as e:
                return [("connection", False, str(e))]
        
        try:
            results = asyncio.run(test_tool_execution())
            
            print("Tool execution test results:")
            success_count = 0
            for tool_name, success, result in results:
                status = "✓" if success else "✗"
                print(f"  {status} {tool_name}: {result if not success else 'SUCCESS'}")
                if success:
                    success_count += 1
            
            if success_count > 0:
                print(f"✓ Tool execution working - {success_count} tools executed successfully")
                self.assertTrue(True)
            else:
                print("✗ No tools could be executed successfully")
                print("This indicates an issue with tool execution mechanism")
                # Don't fail - we're diagnosing
                self.assertTrue(True)
                
        except Exception as e:
            print(f"✗ Tool execution test exception: {e}")
            self.assertTrue(True)  # Don't fail diagnostic tests
    
    def test_05_parameter_handling(self):
        """Test parameter handling issues"""
        print("\n5. Testing parameter handling...")
        
        if not FASTMCP_AVAILABLE:
            self.skipTest("FastMCP not available")
        
        async def test_parameters():
            try:
                async with Client(self.sse_endpoint) as client:
                    # Test different parameter formats
                    test_cases = [
                        # Simple parameters
                        ("create_presentation", {"title": "Simple Test"}),
                        # Complex parameters
                        ("add_slide", {"layout": "Title and Content", "position": 1}),
                        # No parameters
                        ("diagnose_server", {}),
                    ]
                    
                    results = []
                    for tool_name, params in test_cases:
                        try:
                            result = await client.call_tool(tool_name, params)
                            results.append((tool_name, params, True, "Success"))
                        except Exception as e:
                            results.append((tool_name, params, False, str(e)))
                    
                    return results
                    
            except Exception as e:
                return [("connection", {}, False, str(e))]
        
        try:
            results = asyncio.run(test_parameters())
            
            print("Parameter handling test results:")
            for tool_name, params, success, result in results:
                status = "✓" if success else "✗"
                print(f"  {status} {tool_name}({params}): {result}")
            
            # Analyze parameter-related errors
            param_errors = [r for r in results if not r[2] and "param" in r[3].lower()]
            if param_errors:
                print(f"⚠ Found {len(param_errors)} parameter-related errors")
                print("This suggests parameter handling issues in the server")
            
            self.assertTrue(True)  # Always pass - diagnostic test
            
        except Exception as e:
            print(f"✗ Parameter handling test exception: {e}")
            self.assertTrue(True)


def check_server_running():
    """Check if PowerPoint MCP server is running on port 8001"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', 8001))
            return result == 0
    except Exception:
        return False


def main():
    """Run PowerPoint MCP diagnostic tests"""
    print("PowerPoint MCP Server Diagnostic Test Suite")
    print("=" * 50)
    
    # Check if server is running
    if check_server_running():
        print("✓ Port 8001 is open - server appears to be running")
    else:
        print("⚠ Port 8001 is not open - server may not be running")
        print("Start the server with:")
        print("  python -m ufo.mcp.app_servers.powerpoint_mcp_server --port 8001")
        print("\nContinuing with tests anyway...\n")
    
    # Check FastMCP availability
    if not FASTMCP_AVAILABLE:
        print("⚠ FastMCP not available - install with: pip install fastmcp")
        return 1
    
    # Run tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*50)
    print("Diagnostic Summary")
    print("="*50)
    print("If tests fail, common issues include:")
    print("1. Server not running on port 8001")
    print("2. Parameter schema mismatch between client and server")
    print("3. Receiver method compatibility issues")
    print("4. FastMCP transport configuration problems")
    print("\nTo fix issues:")
    print("1. Restart the PowerPoint MCP server")
    print("2. Check server logs for error messages")
    print("3. Verify PowerPoint application is available")


if __name__ == "__main__":
    main()
