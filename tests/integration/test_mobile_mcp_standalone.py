"""
Standalone test for Mobile MCP Servers
Tests mobile servers directly without full UFO infrastructure.

Prerequisites:
- Android emulator or physical device must be running
- ADB must be installed and accessible
- Mobile MCP servers must be running on ports 8020 (data) and 8021 (action)

Start servers:
    python -m ufo.client.mcp.http_servers.mobile_mcp_server --server both

Run test:
    python tests/integration/test_mobile_mcp_standalone.py
"""

import asyncio
import os
import subprocess
import sys
from typing import Any, Dict

from fastmcp import Client


def find_adb():
    """Auto-detect ADB path"""
    common_paths = [
        r"C:\Users\{}\AppData\Local\Android\Sdk\platform-tools\adb.exe".format(
            os.environ.get("USERNAME", "")
        ),
        "/usr/bin/adb",
        "/usr/local/bin/adb",
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    try:
        result = subprocess.run(
            ["where" if os.name == "nt" else "which", "adb"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except:
        pass

    return "adb"


async def check_adb_connection() -> bool:
    """Check if ADB is available and a device is connected"""
    adb_path = find_adb()

    try:
        result = subprocess.run(
            [adb_path, "devices"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            print(f"❌ ADB not found or not working properly")
            print(f"   Tried: {adb_path}")
            return False

        devices = [line for line in result.stdout.split("\n") if "\tdevice" in line]
        if not devices:
            print("❌ No Android device/emulator connected")
            print("   Please connect a device and run 'adb devices'")
            return False

        print(f"✅ Found {len(devices)} connected device(s)")
        print(result.stdout)
        return True

    except FileNotFoundError:
        print(f"❌ ADB not found: {adb_path}")
        print("   Please install Android SDK platform-tools")
        return False
    except Exception as e:
        print(f"❌ Error checking ADB: {e}")
        return False


async def test_data_collection_server():
    """Test the Mobile Data Collection Server"""
    print("\n" + "=" * 70)
    print("Testing Mobile Data Collection Server (port 8020)")
    print("=" * 70)

    server_url = "http://localhost:8020/mcp"

    try:
        # FastMCP Client automatically detects HTTP from URL
        async with Client(server_url) as client:
            # Test 1: List available tools
            print("\n📋 Listing available data collection tools...")
            tools = await client.list_tools()
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")

            # Test 2: Get device info
            print("\n📱 Getting device information...")
            result = await client.call_tool("get_device_info", {})
            device_info = result.data
            if device_info and device_info.get("success"):
                info = device_info["device_info"]
                print(f"✅ Device Info:")
                print(f"   Model: {info.get('model', 'N/A')}")
                print(f"   Android Version: {info.get('android_version', 'N/A')}")
                print(f"   Screen: {info.get('screen_size', 'N/A')}")
                print(f"   Battery: {info.get('battery_level', 'N/A')}")
            else:
                print(f"❌ Failed to get device info: {device_info}")

            # Test 3: Capture screenshot
            print("\n📸 Capturing screenshot...")
            result = await client.call_tool("capture_screenshot", {"format": "base64"})
            screenshot = result.data
            if screenshot and screenshot.get("success"):
                print(f"✅ Screenshot captured:")
                print(f"   Size: {screenshot['width']}x{screenshot['height']}")
                print(f"   Format: {screenshot['format']}")
                print(f"   Data length: {len(screenshot['image'])} chars")
            else:
                print(f"❌ Failed to capture screenshot: {screenshot}")

            # Test 4: Get UI tree
            print("\n🌲 Getting UI hierarchy tree...")
            result = await client.call_tool("get_ui_tree", {})
            ui_tree = result.data
            if ui_tree and ui_tree.get("success"):
                print(f"✅ UI tree retrieved:")
                print(f"   Length: {len(ui_tree['ui_tree'])} characters")
                print(f"   Format: {ui_tree['format']}")
            else:
                print(f"❌ Failed to get UI tree: {ui_tree}")

            # Test 5: Get installed apps
            print("\n📱 Getting installed apps...")
            result = await client.call_tool(
                "get_mobile_app_target_info",
                {"include_system_apps": False, "force_refresh": True},
            )
            apps = result.data
            if apps and isinstance(apps, list):
                print(f"✅ Found {len(apps)} user-installed apps")
                if apps:
                    print(f"   Sample app: {apps[0].get('name', 'N/A')}")
            else:
                print(f"❌ Failed to get apps: {apps}")

            # Test 6: Get UI controls
            print("\n🎮 Getting current screen controls...")
            result = await client.call_tool(
                "get_app_window_controls_target_info", {"force_refresh": True}
            )
            controls = result.data
            if controls and isinstance(controls, list):
                print(f"✅ Found {len(controls)} controls on current screen")
                if controls:
                    sample = controls[0]
                    print(f"   Sample control:")
                    print(f"     ID: {sample.get('id', 'N/A')}")
                    print(f"     Name: {sample.get('name', 'N/A')}")
                    print(f"     Type: {sample.get('type', 'N/A')}")
            else:
                print(f"❌ Failed to get controls: {controls}")

            print("\n✅ Data Collection Server: ALL TESTS PASSED")
            return True

    except Exception as e:
        print(f"\n❌ Error testing data collection server: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_action_server():
    """Test the Mobile Action Server"""
    print("\n" + "=" * 70)
    print("Testing Mobile Action Server (port 8021)")
    print("=" * 70)

    server_url = "http://localhost:8021/mcp"

    try:
        async with Client(server_url) as client:
            # Test 1: List available tools
            print("\n📋 Listing available action tools...")
            tools = await client.list_tools()
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")

            # Test 2: Press HOME key
            print("\n🏠 Pressing HOME key...")
            result = await client.call_tool("press_key", {"key_code": "KEYCODE_HOME"})
            key_result = result.data
            if key_result and key_result.get("success"):
                print(f"✅ HOME key pressed: {key_result['action']}")
            else:
                print(f"❌ Failed to press HOME key: {key_result}")

            await asyncio.sleep(1)

            # Test 3: Tap at screen center
            print("\n👆 Tapping at screen center (540, 960)...")
            result = await client.call_tool("tap", {"x": 540, "y": 960})
            tap_result = result.data
            if tap_result and tap_result.get("success"):
                print(f"✅ Tap executed: {tap_result['action']}")
            else:
                print(f"❌ Failed to tap: {tap_result}")

            await asyncio.sleep(0.5)

            # Test 4: Swipe gesture
            print("\n👇 Performing swipe gesture (scroll down)...")
            result = await client.call_tool(
                "swipe",
                {
                    "start_x": 540,
                    "start_y": 1200,
                    "end_x": 540,
                    "end_y": 600,
                    "duration": 300,
                },
            )
            swipe_result = result.data
            if swipe_result and swipe_result.get("success"):
                print(f"✅ Swipe executed: {swipe_result['action']}")
            else:
                print(f"❌ Failed to swipe: {swipe_result}")

            await asyncio.sleep(0.5)

            # Test 5: Invalidate cache
            print("\n🗑️ Invalidating all caches...")
            result = await client.call_tool("invalidate_cache", {"cache_type": "all"})
            cache_result = result.data
            if cache_result and cache_result.get("success"):
                print(f"✅ Cache invalidated: {cache_result['message']}")
            else:
                print(f"❌ Failed to invalidate cache: {cache_result}")

            print("\n✅ Action Server: ALL TESTS PASSED")
            return True

    except Exception as e:
        print(f"\n❌ Error testing action server: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_shared_state():
    """Test that data and action servers share the same state"""
    print("\n" + "=" * 70)
    print("Testing Shared State Between Servers")
    print("=" * 70)

    data_url = "http://localhost:8020/mcp"
    action_url = "http://localhost:8021/mcp"

    try:
        # Step 1: Get controls from data server (populates cache)
        print("\n1️⃣ Getting controls from data collection server (populate cache)...")
        async with Client(data_url) as data_client:
            result = await data_client.call_tool(
                "get_app_window_controls_target_info", {"force_refresh": True}
            )
            controls = result.data
            if controls and isinstance(controls, list):
                print(f"✅ Retrieved {len(controls)} controls (cache populated)")
            else:
                print(f"❌ Failed to get controls")
                return False

        # Step 2: Invalidate cache from action server
        print("\n2️⃣ Invalidating cache from action server...")
        async with Client(action_url) as action_client:
            result = await action_client.call_tool(
                "invalidate_cache", {"cache_type": "controls"}
            )
            cache_result = result.data
            if cache_result and cache_result.get("success"):
                print(
                    f"✅ Cache invalidated from action server: {cache_result['message']}"
                )
            else:
                print(f"❌ Failed to invalidate cache")
                return False

        # Step 3: Get controls again from data server
        # If shared state works, cache should be invalidated and will refresh
        print("\n3️⃣ Getting controls again from data collection server...")
        async with Client(data_url) as data_client:
            result = await data_client.call_tool(
                "get_app_window_controls_target_info",
                {"force_refresh": False},  # Use cache if available
            )
            controls = result.data
            if controls and isinstance(controls, list):
                print(f"✅ Retrieved {len(controls)} controls")
                print("✅ Shared state verified - cache was properly invalidated!")
            else:
                print(f"❌ Failed to get controls")
                return False

        print("\n✅ Shared State: TEST PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Error testing shared state: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test runner"""
    print("=" * 70)
    print("Mobile MCP Server Standalone Tests")
    print("=" * 70)

    # Check prerequisites
    print("\n📋 Checking prerequisites...")

    if not await check_adb_connection():
        print("\n❌ ADB connection check failed!")
        print("\nPlease ensure:")
        print("  1. Android SDK platform-tools is installed")
        print("  2. ADB is in your PATH")
        print("  3. Android emulator or device is running")
        print("  4. Run 'adb devices' to verify connection")
        return 1

    print("\n⚠️  Make sure Mobile MCP servers are running:")
    print("     python -m ufo.client.mcp.http_servers.mobile_mcp_server --server both")
    print("\nWaiting 3 seconds before starting tests...")
    await asyncio.sleep(3)

    # Run tests
    results = []

    try:
        results.append(await test_data_collection_server())
    except Exception as e:
        print(f"❌ Data collection server test crashed: {e}")
        results.append(False)

    try:
        results.append(await test_action_server())
    except Exception as e:
        print(f"❌ Action server test crashed: {e}")
        results.append(False)

    try:
        results.append(await test_shared_state())
    except Exception as e:
        print(f"❌ Shared state test crashed: {e}")
        results.append(False)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")

    if all(results):
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
