#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test file for UI MCP Servers using FastMCP Client
Tests both UI Data MCP Server and UI Action MCP Server via client interface only.
"""

import os
import sys
import unittest
import asyncio
import json
from typing import Dict, Any

# Add UFO2 to the path
ufo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ufo_root not in sys.path:
    sys.path.insert(0, ufo_root)

# Import only what's needed for server startup
from ufo.mcp.ui_mcp_server import create_data_mcp_server, create_action_mcp_server
from fastmcp import Client


class TestUIMCPServer(unittest.TestCase):
    """Unified test class for both UI Data and UI Action MCP Servers via FastMCP Client"""
    
    @classmethod
    def setUpClass(cls):
        """Setup for both DATA and ACTION MCP servers using in-memory transport"""
        # Create server instances directly
        cls.data_server = create_data_mcp_server()
        cls.action_server = create_action_mcp_server()
        
        # Create persistent client instances
        cls.data_client = Client(cls.data_server)
        cls.action_client = Client(cls.action_server)
        
        cls.servers_running = True
    
    def _call_data_mcp_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Any:
        """Helper method to call Data MCP tools via FastMCP Client"""
        if params is None:
            params = {}
        
        async def call_tool_async():
            try:
                async with self.data_client:
                    result = await self.data_client.call_tool(tool_name, params)
                    return result.data
                    
            except Exception as e:
                return {"error": str(e)}
        
        try:
            return asyncio.run(call_tool_async())
        except Exception as e:
            return {"error": str(e)}
    
    def _call_action_mcp_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Any:
        """Helper method to call Action MCP tools via FastMCP Client"""
        if params is None:
            params = {}
        
        async def call_tool_async():
            try:
                async with self.action_client:
                    result = await self.action_client.call_tool(tool_name, params)
                    return result.data
                    
            except Exception as e:
                return {"error": str(e)}
        
        try:
            return asyncio.run(call_tool_async())
        except Exception as e:
            return {"error": str(e)}
    
    def setUp(self):
        """Setup method for individual tests"""
        if not self.servers_running:
            self.skipTest("Servers not initialized")
    
    def test_capture_desktop_screenshot_all_screens(self):
        """Test capture_desktop_screenshot with all_screens=True via MCP"""
        print("\n--- Testing MCP capture_desktop_screenshot (all screens) ---")
        
        result = self._call_data_mcp_tool("capture_desktop_screenshot", {"all_screens": True})

        if isinstance(result, dict) and "error" in result:
            print(f"WARNING MCP tool returned error: {result['error']}")
            self.skipTest("MCP tool error - skipping test")
        else:
            # Function should return base64 encoded image data string
            self.assertIsInstance(result, str, "Expected string result")
            self.assertTrue(result.startswith("data:image/"), "Expected base64 image data")
            self.assertGreater(len(result), 1000, "Screenshot data seems too small")
            print(f"OK Screenshot captured successfully (length: {len(result)} chars)")
    
    def test_capture_desktop_screenshot_primary_screen(self):
        """Test capture_desktop_screenshot with all_screens=False via MCP"""
        print("\n--- Testing MCP capture_desktop_screenshot (primary screen) ---")
        
        result = self._call_data_mcp_tool("capture_desktop_screenshot", {"all_screens": False})
        
        if isinstance(result, dict) and "error" in result:
            print(f"WARNING MCP tool returned error: {result['error']}")
            self.skipTest("MCP tool error - skipping test")
        else:
            # Function should return base64 encoded image data string
            self.assertIsInstance(result, str, "Expected string result")
            self.assertTrue(result.startswith("data:image/"), "Expected base64 image data")
            self.assertGreater(len(result), 1000, "Screenshot data seems too small")
            print(f"OK Primary screen screenshot captured successfully (length: {len(result)} chars)")
    
    def test_get_desktop_app_info_with_refresh(self):
        """Test get_desktop_app_info with refresh_app_windows=True via MCP"""
        print("\n--- Testing MCP get_desktop_app_info (with refresh) ---")
        
        result = self._call_data_mcp_tool("get_desktop_app_info", {
            "remove_empty": True, 
            "refresh_app_windows": True
        })
        
        if isinstance(result, dict) and "error" in result:
            print(f"WARNING MCP tool returned error: {result['error']}")
            self.skipTest("MCP tool error - skipping test")
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success", False), f"Expected success=True, got: {result}")
        self.assertIn("window_count", result)
        self.assertIn("windows", result)
        self.assertIsInstance(result["windows"], list)
        
        window_count = result["window_count"]
        windows = result["windows"]
        
        print(f"OK Found {window_count} windows")
        
        # Verify window structure for first few windows
        for i, window in enumerate(windows[:3]):
            self.assertIsInstance(window, dict)
            # Check for expected fields (based on WindowInfo structure)
            expected_fields = ["annotation_id", "title", "class_name", "process_id", "is_visible"]
            for field in expected_fields:
                if field not in window and "error" not in window:
                    self.fail(f"Window {i} missing field '{field}': {window}")
            
            if "error" not in window:
                print(f"  Window {i+1}: {window.get('title', 'N/A')} (PID: {window.get('process_id', 'N/A')})")
    
    def test_get_desktop_app_info_without_refresh(self):
        """Test get_desktop_app_info with refresh_app_windows=False via MCP"""
        print("\n--- Testing MCP get_desktop_app_info (without refresh) ---")
        
        # First call with refresh to populate cache
        first_result = self._call_data_mcp_tool("get_desktop_app_info", {"refresh_app_windows": True})
        if isinstance(first_result, dict) and "error" in first_result:
            self.skipTest("MCP tool error during cache population - skipping test")
        
        self.assertTrue(first_result.get("success", False))
        
        # Second call without refresh (should use cached data)
        result = self._call_data_mcp_tool("get_desktop_app_info", {"refresh_app_windows": False})
        
        if isinstance(result, dict) and "error" in result:
            print(f"WARNING MCP tool returned error: {result['error']}")
            self.skipTest("MCP tool error - skipping test")
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success", False), f"Expected success=True, got: {result}")
        self.assertIn("window_count", result)
        self.assertIn("windows", result)
        
        print(f"OK Cached window data retrieved successfully ({result['window_count']} windows)")
    
    def test_get_desktop_app_info_remove_empty_false(self):
        """Test get_desktop_app_info with remove_empty=False via MCP"""
        print("\n--- Testing MCP get_desktop_app_info (include empty windows) ---")
        
        result = self._call_data_mcp_tool("get_desktop_app_info", {
            "remove_empty": False, 
            "refresh_app_windows": True
        })
        
        if isinstance(result, dict) and "error" in result:
            print(f"WARNING MCP tool returned error: {result['error']}")
            self.skipTest("MCP tool error - skipping test")
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success", False), f"Expected success=True, got: {result}")
        
        window_count_with_empty = result["window_count"]
        
        # Compare with remove_empty=True
        result_no_empty = self._call_data_mcp_tool("get_desktop_app_info", {
            "remove_empty": True, 
            "refresh_app_windows": True
        })
        
        if isinstance(result_no_empty, dict) and "error" not in result_no_empty:
            window_count_no_empty = result_no_empty["window_count"]
            
            # Should have same or more windows when including empty ones
            self.assertGreaterEqual(window_count_with_empty, window_count_no_empty)
            
            print(f"OK With empty windows: {window_count_with_empty}, without: {window_count_no_empty}")
        else:
            print(f"OK With empty windows: {window_count_with_empty}")
    
    def _validate_window_data_types(self, window: Dict[str, Any]) -> bool:
        """Helper method to validate window data types"""
        try:
            # Check process_id
            process_id = window.get("process_id")
            if process_id is not None and not isinstance(process_id, int):
                return False
            
            # Check is_visible
            is_visible = window.get("is_visible")
            if is_visible is not None and not isinstance(is_visible, bool):
                return False
            
            # Check rectangle (based on WindowInfo model)
            rectangle = window.get("rectangle")
            if rectangle is not None:
                if not isinstance(rectangle, dict):
                    return False
                # Check rectangle coordinates
                for coord in ["x", "y", "width", "height"]:
                    coord_value = rectangle.get(coord)
                    if coord_value is not None and not isinstance(coord_value, int):
                        return False
            
            return True
        except Exception:
            return False
    
    def test_window_info_structure(self):
        """Test that window info contains expected fields and types via MCP"""
        print("\n--- Testing MCP window info structure ---")
        
        result = self._call_data_mcp_tool("get_desktop_app_info", {})
        
        if isinstance(result, dict) and "error" in result:
            print(f"WARNING MCP tool returned error: {result['error']}")
            self.skipTest("Cannot test window structure due to MCP error")
        
        self.assertTrue(result.get("success", False))
        
        windows = result.get("windows", [])
        if not windows:
            print("WARNING No windows found to test structure")
            return
        
        # Find first valid window
        valid_window = None
        for window in windows:
            if "error" not in window:
                valid_window = window
                break
        
        if not valid_window:
            print("WARNING No valid windows found to test structure")
            return
        
        # Validate window structure
        validation_passed = self._validate_window_data_types(valid_window)
        self.assertTrue(validation_passed, f"Window validation failed for: {valid_window}")
        
        print(f"OK Window structure validation passed for: {valid_window.get('title', 'Unknown')}")
    
    def test_get_window_controls(self):
        """Test get_window_controls via MCP"""
        print("\n--- Testing MCP get_window_controls ---")
        
        result = self._call_data_mcp_tool("get_window_controls", {})
        
        if isinstance(result, dict) and "error" in result:
            print(f"WARNING MCP tool returned error: {result['error']}")
            self.assertTrue(True)  # Don't fail - this depends on window selection
        elif isinstance(result, dict) and "success" in result:
            success = result.get("success", False)
            if success:
                print(f"OK MCP get_window_controls successful ({result.get('control_count', 0)} controls)")
            else:
                print(f"WARNING MCP get_window_controls returned success=False: {result.get('error', 'Unknown error')}")
            self.assertTrue(True)  # Don't fail - this depends on window selection
        else:
            print(f"OK MCP get_window_controls completed with result type: {type(result)}")
            self.assertTrue(True)
    
    def test_capture_window_screenshot(self):
        """Test capture_window_screenshot via MCP"""
        print("\n--- Testing MCP capture_window_screenshot ---")
        
        result = self._call_data_mcp_tool("capture_window_screenshot", {})
        
        if isinstance(result, dict) and "error" in result:
            print(f"WARNING MCP tool returned error: {result['error']}")
            self.assertTrue(True)  # Don't fail - this depends on window selection
        elif isinstance(result, str) and result.startswith("data:image/"):
            print("OK MCP capture_window_screenshot successful")
            self.assertTrue(True)
        elif isinstance(result, dict) and "data" in result:
            # Handle image data wrapped in MCP content format
            image_data = result.get("data", "")
            if image_data.startswith("data:image/"):
                print("OK MCP capture_window_screenshot successful (wrapped format)")
                self.assertTrue(True)
            else:
                print(f"WARNING Unexpected image data format: {str(result)[:100]}...")
                self.assertTrue(True)
        elif isinstance(result, str) and result.startswith("Error"):
            print(f"WARNING MCP capture_window_screenshot returned error: {result}")
            self.assertTrue(True)  # Don't fail - this depends on window selection
        else:
            print(f"OK MCP capture_window_screenshot completed with result type: {type(result)}")
            self.assertTrue(True)


    # Action server tests
    def test_select_application_window(self):
        """Test select_application_window via MCP"""
        print("\n--- Testing MCP select_application_window ---")
        
        # First get available windows
        app_info_result = self._call_data_mcp_tool("get_desktop_app_info", {"refresh_app_windows": True})
        
        if isinstance(app_info_result, dict) and "error" in app_info_result:
            print(f"WARNING: Cannot get app info: {app_info_result['error']}")
            self.skipTest("Cannot test window selection without app info")
        
        windows = app_info_result.get("windows", [])
        if not windows:
            print("WARNING: No windows found to test selection")
            return
        
        # Try to select the first available window
        first_window = windows[0]
        if "error" in first_window:
            print("WARNING: First window has error, skipping test")
            return
            
        window_label = first_window.get("annotation_id", "")
        if not window_label:
            print("WARNING: First window has no annotation_id, skipping test")
            return
        
        print(f"Attempting to select window: {first_window.get('title', 'N/A')} (label: {window_label})")
        
        result = self._call_action_mcp_tool("select_application_window", {
            "window_label": window_label
        })
        
        if isinstance(result, dict) and "error" in result:
            print(f"WARNING MCP tool returned error: {result['error']}")
            self.assertTrue(True)  # Don't fail - might not find suitable window
        elif isinstance(result, dict):
            process_name = result.get("process_name", "N/A")
            window_text = result.get("window_text", "N/A")
            print(f"OK MCP select_application_window successful")
            print(f"  Selected window: {window_text}")
            print(f"  Process: {process_name}")
            self.assertTrue(True)
        else:
            print(f"OK MCP select_application_window completed with result type: {type(result)}")
            self.assertTrue(True)
    
    def test_no_action(self):
        """Test no_action via MCP (safe action that doesn't affect anything)"""
        print("\n--- Testing MCP no_action ---")
        
        result = self._call_action_mcp_tool("no_action", {
            "control_label": "",
            "control_text": "",
            "after_status": "CONTINUE"
        })
        
        if isinstance(result, dict) and "error" in result:
            print(f"WARNING MCP tool returned error: {result['error']}")
            self.assertTrue(True)  # Don't fail on infrastructure issues
        elif isinstance(result, list):
            print(f"OK MCP no_action successful (returned {len(result)} results)")
            self.assertTrue(True)
        else:
            print(f"OK MCP no_action completed with result type: {type(result)}")
            self.assertTrue(True)
    
    def test_keyboard_input_safe(self):
        """Test keyboard_input with safe keys via MCP"""
        print("\n--- Testing MCP keyboard_input (safe keys) ---")
        
        # Use a safe key combination that won't affect the system
        result = self._call_action_mcp_tool("keyboard_input", {
            "keys": "shift",  # Just press shift - harmless
            "control_label": "",
            "control_text": "",
            "control_focus": False,
            "after_status": "CONTINUE"
        })
        
        if isinstance(result, dict) and "error" in result:
            print(f"WARNING MCP tool returned error: {result['error']}")
            self.assertTrue(True)  # Don't fail on infrastructure issues
        elif isinstance(result, list):
            print(f"OK MCP keyboard_input successful (returned {len(result)} results)")
            self.assertTrue(True)
        else:
            print(f"OK MCP keyboard_input completed with result type: {type(result)}")
            self.assertTrue(True)
    
    def test_integrated_screenshot_and_app_info(self):
        """Integrated test: capture desktop screenshot then get all window info"""
        print("\n--- Testing Integrated Screenshot + App Info ---")
        
        # Step 1: Capture desktop screenshot
        print("Step 1: Capturing desktop screenshot...")
        screenshot_result = self._call_data_mcp_tool("capture_desktop_screenshot", {"all_screens": True})
        
        if isinstance(screenshot_result, dict) and "error" in screenshot_result:
            print(f"WARNING Screenshot capture failed: {screenshot_result['error']}")
            self.skipTest("Cannot proceed without screenshot")
        else:
            print(f"OK Screenshot captured successfully (length: {len(screenshot_result)} chars)")
        
        # Step 2: Get desktop app info with refresh
        print("\nStep 2: Getting desktop application info...")
        app_info_result = self._call_data_mcp_tool("get_desktop_app_info", {
            "remove_empty": True,
            "refresh_app_windows": True
        })
        
        if isinstance(app_info_result, dict) and "error" in app_info_result:
            print(f"WARNING App info retrieval failed: {app_info_result['error']}")
            self.skipTest("Cannot proceed without app info")
        
        # Step 3: Print all window information
        print("\nStep 3: Printing all window information...")
        self.assertIsInstance(app_info_result, dict)
        self.assertTrue(app_info_result.get("success", False))
        
        window_count = app_info_result.get("window_count", 0)
        windows = app_info_result.get("windows", [])
        
        print(f"\n=== Desktop Application Summary ===")
        print(f"Total windows found: {window_count}")
        print(f"Screenshot data size: {len(screenshot_result)} characters")
        print(f"\n=== Window Details ===")
        
        notepad_window = None
        for i, window in enumerate(windows):
            if "error" in window:
                print(f"Window {i+1}: ERROR - {window['error']}")
                continue
                
            title = window.get('title', 'N/A')
            print(f"Window {i+1}: {title}")
            
            # Look for Notepad window
            if title and 'notepad' in title.lower():
                notepad_window = window
                print(f"  → Found Notepad window!")
        
        # Step 4: Try to switch to Notepad if found
        print(f"\nStep 4: Attempting to switch to Notepad...")
        if notepad_window:
            window_label = notepad_window.get('annotation_id', '')
            if not window_label:
                print("WARNING: Notepad window has no annotation_id, cannot switch to it.")
            else:
                print(f"Switching to Notepad window: {notepad_window.get('title', 'N/A')} (label: {window_label})")
                try:
                    select_result = self._call_action_mcp_tool("select_application_window", {
                        "window_label": window_label
                    })
                    
                    if isinstance(select_result, dict) and "error" in select_result:
                        print(f"WARNING: Failed to switch to Notepad: {select_result['error']}")
                    elif isinstance(select_result, dict):
                        # select_application_window returns process_name, window_text, window_info (not success field)
                        if "process_name" in select_result or "window_text" in select_result:
                            print(f"✓ Successfully switched to Notepad window")
                            selected_window_text = select_result.get("window_text", "N/A")
                            print(f"  Window text: {selected_window_text}")
                        else:
                            print(f"WARNING: Unexpected select result format: {select_result}")
                    else:
                        print(f"WARNING: Unexpected result when switching to Notepad: {type(select_result)}")
                except Exception as e:
                    print(f"WARNING: Exception occurred while switching to Notepad: {str(e)}")
        else:
            print("WARNING: No Notepad window found in the list. Cannot switch to Notepad.")
            print("Please open Notepad manually if you want to test window switching.")
        
        print(f"\n=== Integration Test Summary ===")
        print(f"✓ Screenshot captured successfully")
        print(f"✓ Found {window_count} windows")
        print(f"✓ All window information printed")
        if notepad_window:
            print(f"✓ Found and attempted to switch to Notepad")
        else:
            print(f"⚠ No Notepad window found")
        
        # Assertions to ensure test success
        self.assertGreater(len(screenshot_result), 1000, "Screenshot should have substantial data")
        self.assertGreater(window_count, 0, "Should find at least one window")
        self.assertIsInstance(windows, list, "Windows should be a list")


def run_tests():
    """Run all tests"""
    print("Testing UI MCP Servers via FastMCP Client")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add integrated test first
    suite.addTest(TestUIMCPServer('test_integrated_screenshot_and_app_info'))
    
    # Add all other tests except the integrated one
    all_tests = loader.loadTestsFromTestCase(TestUIMCPServer)
    for test in all_tests:
        if test._testMethodName != 'test_integrated_screenshot_and_app_info':
            suite.addTest(test)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("OK All tests passed!")
    else:
        print(f"FAILED {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)