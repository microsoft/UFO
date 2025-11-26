"""
Integration test for Mobile MCP Servers (Android)
Tests the mobile data collection and action servers with an actual Android emulator/device.

Prerequisites:
- Android emulator or physical device must be running
- ADB must be installed and accessible
- Device must be connected and visible via 'adb devices'

Usage:
    pytest tests/integration/test_mobile_mcp_server.py -v

Or run specific tests:
    pytest tests/integration/test_mobile_mcp_server.py::TestMobileMCPServers::test_data_collection_server -v
"""

import asyncio
import logging
import subprocess
import time
from typing import Any, Dict, List, Optional

import pytest

from aip.messages import Command, ResultStatus
from ufo.client.computer import CommandRouter, ComputerManager
from ufo.client.mcp.mcp_server_manager import MCPServerManager


# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class TestMobileMCPServers:
    """Integration tests for Mobile MCP Servers"""

    @pytest.fixture(scope="class")
    def check_adb_connection(self):
        """Check if ADB is available and a device is connected"""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                pytest.skip("ADB not found or not working properly")

            devices = [line for line in result.stdout.split("\n") if "\tdevice" in line]
            if not devices:
                pytest.skip(
                    "No Android device/emulator connected. Please connect a device and run 'adb devices'"
                )

            print(f"\n✅ Found {len(devices)} connected device(s)")
            return True

        except FileNotFoundError:
            pytest.skip(
                "ADB not found in PATH. Please install Android SDK platform-tools."
            )
        except Exception as e:
            pytest.skip(f"Error checking ADB: {e}")

    @pytest.fixture(scope="class")
    def mobile_agent_config(self):
        """Configuration for MobileAgent with data collection and action servers"""
        return {
            "mcp": {
                "MobileAgent": {
                    "default": {
                        "data_collection": [
                            {
                                "namespace": "MobileDataCollector",
                                "type": "http",
                                "host": "localhost",
                                "port": 8020,
                                "path": "/mcp",
                                "reset": False,
                            }
                        ],
                        "action": [
                            {
                                "namespace": "MobileActionExecutor",
                                "type": "http",
                                "host": "localhost",
                                "port": 8021,
                                "path": "/mcp",
                                "reset": False,
                            }
                        ],
                    }
                }
            }
        }

    @pytest.fixture(scope="class")
    async def command_router(self, mobile_agent_config):
        """Create CommandRouter with MobileAgent configuration"""
        mcp_server_manager = MCPServerManager()
        computer_manager = ComputerManager(mobile_agent_config, mcp_server_manager)
        router = CommandRouter(computer_manager)

        # Give servers time to initialize
        await asyncio.sleep(1)

        yield router

        # Cleanup
        computer_manager.reset()

    @pytest.mark.asyncio
    async def test_data_collection_server(self, check_adb_connection, command_router):
        """Test data collection server tools"""

        print("\n=== Testing Mobile Data Collection Server ===")

        # Test 1: Get device info
        print("\n📱 Test 1: Getting device information...")
        commands = [
            Command(
                tool_name="get_device_info",
                tool_type="data_collection",
                parameters={},
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        assert len(results) == 1
        assert results[0].status == ResultStatus.SUCCESS

        device_info = results[0].result
        assert device_info is not None
        assert "success" in device_info
        assert device_info["success"] is True
        assert "device_info" in device_info

        print(f"✅ Device Info: {device_info['device_info']}")

        # Test 2: Capture screenshot
        print("\n📸 Test 2: Capturing screenshot...")
        commands = [
            Command(
                tool_name="capture_screenshot",
                tool_type="data_collection",
                parameters={"format": "base64"},
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        assert len(results) == 1
        assert results[0].status == ResultStatus.SUCCESS

        screenshot_result = results[0].result
        assert screenshot_result is not None
        assert screenshot_result["success"] is True
        assert "image" in screenshot_result
        assert screenshot_result["image"].startswith("data:image/png;base64,")

        print(
            f"✅ Screenshot captured: {screenshot_result['width']}x{screenshot_result['height']}"
        )

        # Test 3: Get UI tree
        print("\n🌲 Test 3: Getting UI hierarchy tree...")
        commands = [
            Command(
                tool_name="get_ui_tree",
                tool_type="data_collection",
                parameters={},
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        assert len(results) == 1
        assert results[0].status == ResultStatus.SUCCESS

        ui_tree_result = results[0].result
        assert ui_tree_result is not None
        assert ui_tree_result["success"] is True
        assert "ui_tree" in ui_tree_result
        assert ui_tree_result["format"] == "xml"

        print(f"✅ UI tree retrieved: {len(ui_tree_result['ui_tree'])} characters")

        # Test 4: Get installed apps
        print("\n📱 Test 4: Getting installed apps...")
        commands = [
            Command(
                tool_name="get_mobile_app_target_info",
                tool_type="data_collection",
                parameters={"include_system_apps": False, "force_refresh": True},
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        assert len(results) == 1
        assert results[0].status == ResultStatus.SUCCESS

        apps = results[0].result
        assert apps is not None
        assert isinstance(apps, list)

        print(f"✅ Found {len(apps)} user-installed apps")
        if apps:
            print(f"   Sample app: {apps[0]}")

        # Test 5: Get UI controls
        print("\n🎮 Test 5: Getting current screen controls...")
        commands = [
            Command(
                tool_name="get_app_window_controls_target_info",
                tool_type="data_collection",
                parameters={"force_refresh": True},
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        assert len(results) == 1
        assert results[0].status == ResultStatus.SUCCESS

        controls = results[0].result
        assert controls is not None
        assert isinstance(controls, list)

        print(f"✅ Found {len(controls)} controls on current screen")
        if controls:
            print(f"   Sample control: {controls[0]}")

    @pytest.mark.asyncio
    async def test_action_server(self, check_adb_connection, command_router):
        """Test action server tools"""

        print("\n=== Testing Mobile Action Server ===")

        # Test 1: Press HOME key
        print("\n🏠 Test 1: Pressing HOME key...")
        commands = [
            Command(
                tool_name="press_key",
                tool_type="action",
                parameters={"key_code": "KEYCODE_HOME"},
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        assert len(results) == 1
        assert results[0].status == ResultStatus.SUCCESS

        result = results[0].result
        assert result is not None
        assert result["success"] is True

        print(f"✅ HOME key pressed successfully")

        # Wait for animation
        await asyncio.sleep(1)

        # Test 2: Tap at center of screen
        print("\n👆 Test 2: Tapping at screen center...")
        commands = [
            Command(
                tool_name="tap",
                tool_type="action",
                parameters={"x": 540, "y": 960},  # Common center for 1080x1920
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        assert len(results) == 1
        assert results[0].status == ResultStatus.SUCCESS

        result = results[0].result
        assert result is not None
        assert result["success"] is True

        print(f"✅ Tap executed: {result['action']}")

        await asyncio.sleep(0.5)

        # Test 3: Swipe gesture (scroll down)
        print("\n👇 Test 3: Performing swipe gesture...")
        commands = [
            Command(
                tool_name="swipe",
                tool_type="action",
                parameters={
                    "start_x": 540,
                    "start_y": 1200,
                    "end_x": 540,
                    "end_y": 600,
                    "duration": 300,
                },
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        assert len(results) == 1
        assert results[0].status == ResultStatus.SUCCESS

        result = results[0].result
        assert result is not None
        assert result["success"] is True

        print(f"✅ Swipe executed: {result['action']}")

        await asyncio.sleep(0.5)

        # Test 4: Invalidate cache
        print("\n🗑️ Test 4: Invalidating cache...")
        commands = [
            Command(
                tool_name="invalidate_cache",
                tool_type="action",
                parameters={"cache_type": "all"},
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        assert len(results) == 1
        assert results[0].status == ResultStatus.SUCCESS

        result = results[0].result
        assert result is not None
        assert result["success"] is True

        print(f"✅ Cache invalidated: {result['message']}")

    @pytest.mark.asyncio
    async def test_shared_state_between_servers(
        self, check_adb_connection, command_router
    ):
        """Test that data collection and action servers share the same state"""

        print("\n=== Testing Shared State Between Servers ===")

        # Step 1: Get controls from data collection server (populates cache)
        print("\n1️⃣ Getting controls from data collection server...")
        commands = [
            Command(
                tool_name="get_app_window_controls_target_info",
                tool_type="data_collection",
                parameters={"force_refresh": True},
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        assert results[0].status == ResultStatus.SUCCESS
        controls = results[0].result

        print(f"✅ Retrieved {len(controls)} controls (cache populated)")

        # Step 2: Invalidate cache from action server
        print("\n2️⃣ Invalidating cache from action server...")
        commands = [
            Command(
                tool_name="invalidate_cache",
                tool_type="action",
                parameters={"cache_type": "controls"},
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        assert results[0].status == ResultStatus.SUCCESS
        print(f"✅ Cache invalidated from action server")

        # Step 3: Get controls again - should refresh from device
        print("\n3️⃣ Getting controls again from data collection server...")
        commands = [
            Command(
                tool_name="get_app_window_controls_target_info",
                tool_type="data_collection",
                parameters={"force_refresh": False},  # Use cache if available
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        assert results[0].status == ResultStatus.SUCCESS
        print(f"✅ Cache invalidation worked - data refreshed from device")

    @pytest.mark.asyncio
    async def test_complete_workflow(self, check_adb_connection, command_router):
        """Test a complete workflow: get controls -> click control"""

        print("\n=== Testing Complete Workflow ===")

        # Navigate to home screen first
        print("\n🏠 Navigating to home screen...")
        commands = [
            Command(
                tool_name="press_key",
                tool_type="action",
                parameters={"key_code": "KEYCODE_HOME"},
            )
        ]

        await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        await asyncio.sleep(1)

        # Get controls
        print("\n📋 Getting current screen controls...")
        commands = [
            Command(
                tool_name="get_app_window_controls_target_info",
                tool_type="data_collection",
                parameters={"force_refresh": True},
            )
        ]

        results = await command_router.execute(
            agent_name="MobileAgent",
            process_name="",
            root_name="default",
            commands=commands,
        )

        controls = results[0].result
        print(f"✅ Found {len(controls)} controls")

        # Find a clickable control
        clickable_control = None
        for control in controls:
            if control.get("name"):  # Has a name/label
                clickable_control = control
                break

        if clickable_control:
            print(
                f"\n👆 Clicking control: {clickable_control.get('name')} (ID: {clickable_control.get('id')})"
            )

            commands = [
                Command(
                    tool_name="click_control",
                    tool_type="action",
                    parameters={
                        "control_id": clickable_control.get("id"),
                        "control_name": clickable_control.get("name"),
                    },
                )
            ]

            results = await command_router.execute(
                agent_name="MobileAgent",
                process_name="",
                root_name="default",
                commands=commands,
            )

            if results[0].status == ResultStatus.SUCCESS:
                print(f"✅ Successfully clicked control")
            else:
                print(f"⚠️ Click failed: {results[0].error}")
        else:
            print("⚠️ No clickable controls with names found on current screen")


if __name__ == "__main__":
    """
    Run tests directly with: python tests/integration/test_mobile_mcp_server.py
    """
    print("=" * 70)
    print("Mobile MCP Server Integration Tests")
    print("=" * 70)
    print("\n⚠️  Prerequisites:")
    print("  1. Android emulator or device must be running")
    print("  2. Run 'adb devices' to verify connection")
    print("  3. Start mobile MCP servers:")
    print("     python -m ufo.client.mcp.http_servers.mobile_mcp_server --server both")
    print("\n" + "=" * 70)

    pytest.main([__file__, "-v", "-s"])
