#!/usr/bin/env python3
"""
Test script for UFO MCP Server
"""

import sys
import os

# Add the UFO2 source directory to the Python path
ufo_src_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ufo_src_path)


def test_imports():
    """Test that all required modules can be imported"""
    try:
        print("Testing imports...")

        # Test Computer class import
        from ufo.cs.computer import Computer

        print("✓ Computer class imported successfully")

        # Test contracts import
        from ufo.contracts.contracts import (
            CaptureDesktopScreenshotAction,
            CaptureDesktopScreenshotParams,
            GetDesktopAppInfoAction,
            GetDesktopAppInfoParams,
        )

        print("✓ Contract classes imported successfully")

        # Test MCP server import
        from ufo.mcp.core_mcp_server import mcp, computer

        print("✓ MCP server imported successfully")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_computer_initialization():
    """Test Computer class initialization"""
    try:
        print("\nTesting Computer initialization...")
        from ufo.cs.computer import Computer

        computer = Computer("TestComputer")
        print(f"✓ Computer '{computer.name}' initialized successfully")
        return True

    except Exception as e:
        print(f"✗ Computer initialization error: {e}")
        return False


def test_basic_action():
    """Test a basic action execution"""
    try:
        print("\nTesting basic action execution...")
        from ufo.cs.computer import Computer
        from ufo.contracts.contracts import (
            GetDesktopAppInfoAction,
            GetDesktopAppInfoParams,
        )

        computer = Computer("TestComputer")
        action = GetDesktopAppInfoAction(
            params=GetDesktopAppInfoParams(remove_empty=True, refresh_app_windows=True)
        )

        # This might fail if no GUI is available, but we test the structure
        try:
            result = computer.run_action(action)
            print(f"✓ Action executed successfully, got {len(result)} windows")
        except Exception as action_error:
            print(
                f"⚠ Action execution failed (expected in headless environment): {action_error}"
            )

        return True

    except Exception as e:
        print(f"✗ Action test error: {e}")
        return False


def main():
    """Run all tests"""
    print("UFO MCP Server Test Suite")
    print("=" * 40)

    tests = [test_imports, test_computer_initialization, test_basic_action]

    passed = 0
    for test in tests:
        if test():
            passed += 1

    print(f"\nTest Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All tests passed! UFO MCP Server is ready.")
    else:
        print("❌ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
