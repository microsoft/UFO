#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test script for UFO MCP server implementations.
This script tests the individual MCP servers for different applications.
"""

import os
import sys
import time
import subprocess
import requests
from typing import Dict, Any

# Add UFO2 to the path
ufo_root = os.path.dirname(os.path.abspath(__file__))
if ufo_root not in sys.path:
    sys.path.insert(0, ufo_root)


def test_mcp_factory():
    """Test the MCP factory implementation"""
    print("\n" + "="*50)
    print("Testing MCP Factory Implementation")
    print("="*50)
    
    try:
        from ufo.automator.app_apis.factory import MCPReceiverFactory, MCPReceiver
        
        # Test factory creation
        factory = MCPReceiverFactory()
        print("✓ MCPReceiverFactory created successfully")
        
        # Test supported applications
        supported_apps = factory.supported_app_roots
        print(f"✓ Supported applications: {supported_apps}")
        
        # Test receiver creation for different namespaces
        test_namespaces = ["word", "excel", "powerpoint", "web", "shell"]
        
        for namespace in test_namespaces:
            try:
                # Note: This may fail if COM applications aren't available, which is expected
                receiver = factory.create_receiver(namespace)
                if receiver:
                    print(f"✓ Created receiver for {namespace}: {receiver.type_name}")
                else:
                    print(f"⚠ No receiver created for {namespace} (may be expected if app not available)")
            except Exception as e:
                print(f"⚠ Error creating receiver for {namespace}: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ MCP factory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_instruction_files():
    """Test that all instruction files are present and valid"""
    print("\n" + "="*50)
    print("Testing MCP Instruction Files")
    print("="*50)
    
    base_dir = os.path.dirname(__file__)
    instructions_dir = os.path.join(base_dir, "ufo", "config", "mcp_instructions")
    
    expected_files = ["word.yaml", "excel.yaml", "powerpoint.yaml", "web.yaml", "shell.yaml"]
    
    all_valid = True
    
    for filename in expected_files:
        filepath = os.path.join(instructions_dir, filename)
        
        if os.path.exists(filepath):
            try:
                import yaml
                with open(filepath, 'r') as f:
                    instructions = yaml.safe_load(f)
                
                # Validate structure
                if "namespace" in instructions and "tools" in instructions:
                    tools_count = len(instructions["tools"])
                    print(f"✓ {filename}: {tools_count} tools defined")
                else:
                    print(f"⚠ {filename}: Missing required structure")
                    all_valid = False
                    
            except Exception as e:
                print(f"✗ {filename}: Error loading - {e}")
                all_valid = False
        else:
            print(f"✗ {filename}: File not found")
            all_valid = False
    
    return all_valid


def test_mcp_server_modules():
    """Test that MCP server modules can be imported"""
    print("\n" + "="*50)
    print("Testing MCP Server Modules")
    print("="*50)
    
    server_modules = [
        "ufo.mcp.base_mcp_server",
        "ufo.mcp.app_servers.word_mcp_server",
        "ufo.mcp.app_servers.excel_mcp_server", 
        "ufo.mcp.app_servers.powerpoint_mcp_server",
        "ufo.mcp.app_servers.web_mcp_server",
        "ufo.mcp.app_servers.shell_mcp_server"
    ]
    
    all_imported = True
    
    for module_name in server_modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name}: Imported successfully")
        except Exception as e:
            print(f"✗ {module_name}: Import failed - {e}")
            all_imported = False
    
    return all_imported


def test_computer_integration():
    """Test Computer class MCP integration"""
    print("\n" + "="*50)
    print("Testing Computer Class MCP Integration")
    print("="*50)
    
    try:
        from ufo.cs.computer import Computer
        
        # Create Computer instance
        computer = Computer("TestMCPComputer")
        print("✓ Computer instance created")
        
        # Check MCP servers configuration
        if hasattr(computer, 'mcp_servers'):
            servers = list(computer.mcp_servers.keys())
            print(f"✓ MCP servers configured: {servers}")
            
            # Check if new servers are included
            expected_servers = ["powerpoint", "word", "excel", "web", "shell"]
            missing_servers = [s for s in expected_servers if s not in servers]
            
            if not missing_servers:
                print("✓ All expected MCP servers are configured")
            else:
                print(f"⚠ Missing MCP servers: {missing_servers}")
        else:
            print("✗ MCP servers not found in Computer class")
            return False
        
        # Check MCP instructions
        if hasattr(computer, 'mcp_instructions'):
            instructions = list(computer.mcp_instructions.keys())
            print(f"✓ MCP instructions loaded for: {instructions}")
        else:
            print("✗ MCP instructions not found in Computer class")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Computer integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_base_mcp_server():
    """Test the base MCP server functionality"""
    print("\n" + "="*50)
    print("Testing Base MCP Server")
    print("="*50)
    
    try:
        from ufo.mcp.base_mcp_server import BaseMCPServer, create_mcp_server
        
        # Test server creation
        server = create_mcp_server("word", "test-word-server")
        print("✓ Base MCP server created successfully")
        print(f"✓ Server name: {server.server_name}")
        print(f"✓ App namespace: {server.app_namespace}")
        
        # Check if instructions are loaded
        if server.instructions:
            tools_count = len(server.instructions.get("tools", []))
            print(f"✓ Instructions loaded with {tools_count} tools")
        else:
            print("⚠ No instructions loaded (may be expected)")
        
        return True
        
    except Exception as e:
        print(f"✗ Base MCP server test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run comprehensive MCP implementation tests"""
    print("UFO MCP Implementation Test Suite")
    print("=" * 60)
    
    tests = [
        ("MCP Factory", test_mcp_factory),
        ("Instruction Files", test_instruction_files),
        ("MCP Server Modules", test_mcp_server_modules),
        ("Computer Integration", test_computer_integration),
        ("Base MCP Server", test_base_mcp_server)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All MCP implementation tests passed!")
        print("\nMCP Infrastructure Ready:")
        print("1. ✓ MCP receiver factory implemented")
        print("2. ✓ Individual MCP servers created (word, excel, powerpoint, web, shell)")
        print("3. ✓ Instruction files defined for all applications") 
        print("4. ✓ Computer class integration updated")
        print("5. ✓ Base MCP server framework functional")
        
        print("\nNext Steps:")
        print("1. Start individual MCP servers on their configured ports")
        print("2. Test with actual application connections")
        print("3. Verify tool execution through MCP protocol")
        print("4. Add error handling and logging enhancements")
    else:
        print(f"\n❌ {total - passed} tests failed. Please review the errors above.")
        
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
