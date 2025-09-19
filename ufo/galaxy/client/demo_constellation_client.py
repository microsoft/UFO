#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation v2 Client Demo

This demo script shows how to use the Constellation v2 Client to register devices,
execute tasks, and manage multi-device coordination.

Usage:
    python demo_constellation_client.py [--config CONFIG_FILE] [--create-sample]
"""

import asyncio
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, Any

from ufo.galaxy.client import (
    ConstellationClient,
    create_constellation_client,
    ConstellationConfig,
    DeviceConfig,
)


async def demo_basic_usage() -> None:
    """Demonstrate basic constellation client usage."""
    print("\n🚀 Demo: Basic Constellation Client Usage")
    print("=" * 50)

    # Create a simple configuration
    config = ConstellationConfig(
        constellation_id="demo_constellation",
        heartbeat_interval=15.0,
        max_concurrent_tasks=4,
    )

    # Add a demo device (would normally connect to real UFO server)
    config.add_device(
        device_id="demo_device",
        server_url="ws://localhost:8765",
        local_client_ids=["demo_client_1", "demo_client_2"],
        capabilities=["automation", "screenshot", "text_input"],
        metadata={"environment": "demo", "os": "Windows"},
    )

    # Create client
    client = ConstellationClient(config=config)

    try:
        # Show constellation info
        info = client.get_constellation_info()
        print(f"📊 Constellation Info:")
        for key, value in info.items():
            print(f"  {key}: {value}")

        # Show device status
        print(f"\n📱 Device Status:")
        status = client.get_device_status()
        for device_id, device_status in status.items():
            print(f"  Device {device_id}:")
            print(f"    Status: {device_status.get('status', 'unknown')}")
            print(f"    URL: {device_status.get('server_url', 'N/A')}")
            print(f"    Clients: {device_status.get('local_clients', [])}")
            print(f"    Capabilities: {device_status.get('capabilities', [])}")

        print(f"\n✅ Basic demo completed successfully!")

    finally:
        await client.shutdown()


async def demo_config_file_usage() -> None:
    """Demonstrate configuration file usage."""
    print("\n📁 Demo: Configuration File Usage")
    print("=" * 50)

    # Create a sample config file
    demo_config_path = Path("demo_constellation_config.json")

    demo_config = {
        "constellation_id": "file_demo_constellation",
        "heartbeat_interval": 20.0,
        "reconnect_delay": 3.0,
        "max_concurrent_tasks": 6,
        "devices": [
            {
                "device_id": "workstation_alpha",
                "server_url": "ws://192.168.1.100:8765",
                "local_client_ids": ["alpha_client_1", "alpha_client_2"],
                "capabilities": ["automation", "screenshot", "office_apps"],
                "metadata": {
                    "location": "office",
                    "os": "Windows",
                    "role": "workstation",
                },
                "auto_connect": True,
            },
            {
                "device_id": "server_beta",
                "server_url": "ws://192.168.1.101:8765",
                "local_client_ids": ["beta_server_client"],
                "capabilities": ["database", "api_services", "file_ops"],
                "metadata": {"location": "datacenter", "os": "Linux", "role": "server"},
                "auto_connect": True,
            },
        ],
    }

    # Write config file
    with open(demo_config_path, "w", encoding="utf-8") as f:
        json.dump(demo_config, f, indent=2)

    print(f"📝 Created demo config: {demo_config_path}")

    try:
        # Load client from config file
        client = await create_constellation_client(config_file=str(demo_config_path))

        # Show loaded configuration
        info = client.get_constellation_info()
        print(f"\n📊 Loaded Configuration:")
        print(f"  Constellation ID: {info['constellation_id']}")
        print(f"  Total Devices: {info['total_devices']}")
        print(f"  Max Concurrent Tasks: {info['max_concurrent_tasks']}")

        # Show device details
        print(f"\n📱 Configured Devices:")
        for device_id in ["workstation_alpha", "server_beta"]:
            device_status = client.get_device_status(device_id)
            if "error" not in device_status:
                print(f"  {device_id}:")
                print(f"    URL: {device_status['server_url']}")
                print(f"    Clients: {device_status['local_clients']}")
                print(f"    Capabilities: {device_status['capabilities']}")
                print(f"    Metadata: {device_status['metadata']}")

        print(f"\n✅ Config file demo completed successfully!")

    finally:
        await client.shutdown()
        # Clean up
        demo_config_path.unlink(missing_ok=True)


async def demo_task_execution_simulation() -> None:
    """Demonstrate task execution workflow (simulated)."""
    print("\n⚡ Demo: Task Execution Simulation")
    print("=" * 50)

    # Create client with multiple devices
    client = await create_constellation_client(
        constellation_id="task_demo_constellation",
        devices=[
            {
                "device_id": "windows_workstation",
                "server_url": "ws://localhost:8765",
                "local_client_ids": ["win_client_1", "win_client_2"],
                "capabilities": ["screenshot", "text_input", "office_apps"],
                "metadata": {"os": "Windows", "performance": "high"},
            },
            {
                "device_id": "linux_server",
                "server_url": "ws://localhost:8766",
                "local_client_ids": ["linux_client"],
                "capabilities": ["terminal", "file_ops", "database"],
                "metadata": {"os": "Linux", "performance": "medium"},
            },
        ],
    )

    try:
        print(f"📋 Simulating task execution scenarios...")

        # Scenario 1: Simple task execution
        print(f"\n🎯 Scenario 1: Simple Task")
        try:
            # This would normally execute on a connected device
            print(f"  Task: 'take a screenshot'")
            print(f"  Target: Any available device")
            print(f"  ⚠️  Would execute if UFO servers were running")

        except Exception as e:
            print(f"  ❌ Expected connection error: {type(e).__name__}")

        # Scenario 2: Capability-based device selection
        print(f"\n🎯 Scenario 2: Capability-Based Selection")
        try:
            print(f"  Task: 'run database query'")
            print(f"  Required Capabilities: ['database']")
            print(f"  Expected Device: linux_server")
            print(f"  ⚠️  Would execute if UFO servers were running")

        except Exception as e:
            print(f"  ❌ Expected connection error: {type(e).__name__}")

        # Scenario 3: Parallel task execution
        print(f"\n🎯 Scenario 3: Parallel Tasks")
        tasks = [
            {"request": "take screenshot", "device_id": "windows_workstation"},
            {"request": "check disk usage", "device_id": "linux_server"},
            {"request": "list running processes"},  # Auto-select device
        ]

        print(f"  Tasks: {len(tasks)} parallel tasks")
        print(f"  Max Concurrent: 2")
        print(f"  ⚠️  Would execute if UFO servers were running")

        print(f"\n✅ Task execution simulation completed!")

    finally:
        await client.shutdown()


async def demo_event_handling() -> None:
    """Demonstrate event handling capabilities."""
    print("\n🔔 Demo: Event Handling")
    print("=" * 50)

    # Event tracking
    events = []

    async def on_device_connected(device_id: str, device_info) -> None:
        events.append(f"✅ Device {device_id} connected")
        print(f"  Event: Device {device_id} connected")

    async def on_device_disconnected(device_id: str) -> None:
        events.append(f"❌ Device {device_id} disconnected")
        print(f"  Event: Device {device_id} disconnected")

    async def on_task_completed(
        device_id: str, task_id: str, result: Dict[str, Any]
    ) -> None:
        events.append(f"🎯 Task {task_id} completed on {device_id}")
        print(f"  Event: Task {task_id} completed on {device_id}")

    # Create client
    client = ConstellationClient(constellation_id="event_demo_constellation")

    # Register event handlers
    client.device_manager.add_connection_handler(on_device_connected)
    client.device_manager.add_disconnection_handler(on_device_disconnected)
    client.device_manager.add_task_completion_handler(on_task_completed)

    try:
        print(f"📡 Event handlers registered:")
        print(f"  - Connection handler")
        print(f"  - Disconnection handler")
        print(f"  - Task completion handler")

        # Simulate device registration (would trigger events with real connections)
        await client.register_device(
            device_id="event_test_device",
            server_url="ws://localhost:8765",
            local_client_ids=["event_client"],
            capabilities=["test"],
            auto_connect=False,  # Don't actually try to connect
        )

        print(f"\n📊 Event Summary:")
        for event in events:
            print(f"  {event}")

        if not events:
            print(f"  ⚠️  No events triggered (expected without real UFO servers)")

        print(f"\n✅ Event handling demo completed!")

    finally:
        await client.shutdown()


async def run_all_demos() -> None:
    """Run all demonstration scenarios."""
    print("🌟 Constellation v2 Client Demonstration")
    print("=" * 60)
    print("This demo showcases the capabilities of the Constellation v2 Client")
    print("for multi-device orchestration and task distribution.")
    print("")
    print("⚠️  Note: Actual task execution requires running UFO WebSocket servers.")
    print("   This demo focuses on client-side functionality and configuration.")

    demos = [
        ("Basic Usage", demo_basic_usage),
        ("Configuration File", demo_config_file_usage),
        ("Task Execution Simulation", demo_task_execution_simulation),
        ("Event Handling", demo_event_handling),
    ]

    for demo_name, demo_func in demos:
        try:
            await demo_func()
            print(f"\n✅ {demo_name} demo completed successfully!\n")

        except Exception as e:
            print(f"\n❌ {demo_name} demo failed: {e}\n")

    print("🎉 All demonstrations completed!")
    print("")
    print("Next Steps:")
    print("1. Start UFO WebSocket servers on target devices")
    print("2. Update configuration with real server URLs")
    print("3. Use the Constellation Client for actual task orchestration")


def main() -> None:
    """Main entry point for the demo."""
    parser = argparse.ArgumentParser(description="Constellation v2 Client Demo")
    parser.add_argument(
        "--config", type=str, help="Path to constellation configuration file"
    )
    parser.add_argument(
        "--create-sample",
        type=str,
        help="Create a sample configuration file at the specified path",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Handle sample config creation
    if args.create_sample:
        ConstellationConfig.create_sample_config(args.create_sample)
        print(f"✅ Sample configuration created: {args.create_sample}")
        return

    # Run demos
    asyncio.run(run_all_demos())


if __name__ == "__main__":
    main()
