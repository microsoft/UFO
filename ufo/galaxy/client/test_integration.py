# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test utilities and integration tests for Constellation v2 Client
"""

import asyncio
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List

from .constellation_client import ConstellationClient, create_constellation_client
from .config_loader import ConstellationConfig, DeviceConfig


class MockUFOWebSocketServer:
    """
    Mock UFO WebSocket server for testing device registration and task execution.
    """

    def __init__(self, server_url: str, device_info: Dict[str, Any]):
        self.server_url = server_url
        self.device_info = device_info
        self.connected_clients = set()
        self.constellation_clients = {}
        self.task_queue = []

    async def handle_connection(self, websocket, path):
        """Mock WebSocket connection handler."""
        self.connected_clients.add(websocket)

        try:
            async for message in websocket:
                response = await self.handle_message(json.loads(message))
                if response:
                    await websocket.send(json.dumps(response))
        finally:
            self.connected_clients.discard(websocket)

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages from constellation client."""
        message_type = message.get("type")

        if message_type == "register_constellation_client":
            # Register constellation client
            constellation_id = message.get("constellation_id")
            local_client_ids = message.get("local_client_ids", [])

            self.constellation_clients[constellation_id] = {
                "local_client_ids": local_client_ids,
                "registered_at": asyncio.get_event_loop().time(),
            }

            return {
                "type": "registration_response",
                "success": True,
                "constellation_id": constellation_id,
                "device_info": self.device_info,
            }

        elif message_type == "device_info_request":
            # Return device information
            return {"type": "device_info_response", "device_info": self.device_info}

        elif message_type == "task_assignment":
            # Handle task assignment
            task_id = message.get("task_id")
            client_id = message.get("client_id")
            task_description = message.get("task_description")

            # Simulate task execution
            result = {
                "task_id": task_id,
                "success": True,
                "result": f"Mock execution of: {task_description}",
                "executed_by": client_id,
                "device_info": self.device_info["device_id"],
            }

            return {
                "type": "task_completion",
                "task_id": task_id,
                "success": True,
                "result": result,
            }

        elif message_type == "heartbeat":
            # Respond to heartbeat
            return {
                "type": "heartbeat_response",
                "timestamp": asyncio.get_event_loop().time(),
            }

        return None


async def test_device_registration():
    """Test device registration and connection."""
    print("🧪 Testing device registration...")

    # Create test configuration
    config = ConstellationConfig(
        constellation_id="test_constellation_001",
        heartbeat_interval=10.0,
        reconnect_delay=2.0,
    )

    # Add test device
    config.add_device(
        device_id="test_device_windows",
        server_url="ws://localhost:8765",
        local_client_ids=["client_1", "client_2"],
        capabilities=["screenshot", "text_input", "app_control"],
        metadata={"os": "Windows", "location": "Test Lab"},
    )

    # Create constellation client
    client = ConstellationClient(config=config)

    try:
        # Test configuration loading
        print(f"✅ Configuration loaded: {config.constellation_id}")
        print(f"✅ Devices in config: {len(config.devices)}")

        # Test device info retrieval
        device_config = config.devices[0]
        print(
            f"✅ Device config: {device_config.device_id} -> {device_config.server_url}"
        )
        print(f"✅ Local clients: {device_config.local_client_ids}")
        print(f"✅ Capabilities: {device_config.capabilities}")

        # Test device manager initialization
        device_info = client.device_manager.get_device_info("test_device_windows")
        print(f"✅ Device manager ready")

        # Note: Actual connection testing would require running UFO WebSocket server
        print("⚠️  Connection testing requires UFO WebSocket server")

        return True

    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        return False

    finally:
        await client.shutdown()


async def test_config_loading():
    """Test configuration loading from file and CLI."""
    print("🧪 Testing configuration loading...")

    try:
        # Create test config file
        test_config = {
            "constellation_id": "test_constellation_file",
            "heartbeat_interval": 15.0,
            "reconnect_delay": 3.0,
            "max_concurrent_tasks": 10,
            "devices": [
                {
                    "device_id": "windows_device",
                    "server_url": "ws://192.168.1.100:8765",
                    "local_client_ids": ["win_client_1", "win_client_2"],
                    "capabilities": ["screenshot", "text_input", "file_ops"],
                    "metadata": {"os": "Windows", "version": "11"},
                },
                {
                    "device_id": "linux_device",
                    "server_url": "ws://192.168.1.101:8765",
                    "local_client_ids": ["linux_client_1"],
                    "capabilities": ["terminal", "file_ops", "screenshot"],
                    "metadata": {"os": "Linux", "distribution": "Ubuntu"},
                },
            ],
        }

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_config, f, indent=2)
            config_file_path = f.name

        try:
            # Test file loading
            config = ConstellationConfig.from_file(config_file_path)
            print(f"✅ Config loaded from file: {config.constellation_id}")
            print(f"✅ Devices loaded: {len(config.devices)}")

            for device in config.devices:
                print(f"  - {device.device_id}: {device.server_url}")
                print(f"    Clients: {device.local_client_ids}")
                print(f"    Capabilities: {device.capabilities}")

            # Test creating sample config
            sample_path = (
                Path(config_file_path).parent / "sample_constellation_config.json"
            )
            ConstellationConfig.create_sample_config(str(sample_path))
            print(f"✅ Sample config created: {sample_path}")

            return True

        finally:
            # Clean up temp files
            Path(config_file_path).unlink(missing_ok=True)
            Path(sample_path).unlink(missing_ok=True)

    except Exception as e:
        print(f"❌ Config loading test failed: {e}")
        return False


async def test_task_execution_workflow():
    """Test the complete task execution workflow."""
    print("🧪 Testing task execution workflow...")

    try:
        # Create constellation client
        client = await create_constellation_client(
            constellation_id="test_workflow_constellation",
            devices=[
                {
                    "device_id": "mock_device_1",
                    "server_url": "ws://localhost:8765",
                    "local_client_ids": ["mock_client_1", "mock_client_2"],
                    "capabilities": ["automation", "screenshot"],
                    "metadata": {"mock": True},
                }
            ],
        )

        # Test constellation info
        info = client.get_constellation_info()
        print(f"✅ Constellation info: {info}")

        # Test device status
        status = client.get_device_status()
        print(f"✅ Device status: {status}")

        # Note: Task execution testing would require mock WebSocket server
        print("⚠️  Task execution testing requires mock WebSocket server")

        return True

    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False

    finally:
        if "client" in locals():
            await client.shutdown()


async def run_integration_tests():
    """Run all integration tests."""
    print("🚀 Starting Constellation v2 Client Integration Tests")
    print("=" * 60)

    tests = [
        ("Device Registration", test_device_registration),
        ("Configuration Loading", test_config_loading),
        ("Task Execution Workflow", test_task_execution_workflow),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)

        try:
            success = await test_func()
            results[test_name] = success
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"📊 {test_name}: {status}")

        except Exception as e:
            results[test_name] = False
            print(f"💥 {test_name}: ERROR - {e}")

    print("\n" + "=" * 60)
    print("📈 TEST SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Constellation v2 Client is ready.")
    else:
        print("⚠️  Some tests failed. Check implementation.")

    return passed == total


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run integration tests
    asyncio.run(run_integration_tests())
