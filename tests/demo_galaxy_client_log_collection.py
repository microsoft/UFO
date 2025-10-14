#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Demo Script: GalaxyClient with Mock AgentProfile for Log Collection

This script demonstrates how to use GalaxyClient with mock AgentProfile objects
to simulate the log collection and Excel generation scenario.

Usage:
    python demo_galaxy_client_log_collection.py
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from unittest.mock import Mock, AsyncMock, patch

from galaxy.galaxy_client import GalaxyClient
from galaxy.client.components.types import AgentProfile, DeviceStatus
from galaxy.client.config_loader import ConstellationConfig, DeviceConfig

# Suppress debug logs for cleaner demo output
logging.getLogger("ufo.galaxy.galaxy_client").setLevel(logging.WARNING)


def create_mock_devices():
    """Create mock AgentProfile objects for demonstration."""

    # Linux Server 1 - Web Server
    linux_server_1 = AgentProfile(
        device_id="linux_server_001",
        server_url="ws://192.168.1.101:5000/ws",
        os="linux",
        capabilities=[
            "log_collection",
            "file_operations",
            "system_monitoring",
            "bash_scripting",
            "ssh_access",
        ],
        metadata={
            "hostname": "web-server-01",
            "location": "datacenter_rack_a",
            "os_version": "Ubuntu 22.04 LTS",
            "performance": "high",
            "cpu_cores": 16,
            "memory_gb": 64,
            "services": ["nginx", "postgresql", "redis"],
            "log_paths": [
                "/var/log/nginx/access.log",
                "/var/log/nginx/error.log",
                "/var/log/postgresql/postgresql.log",
                "/var/log/syslog",
            ],
        },
        status=DeviceStatus.CONNECTED,
        last_heartbeat=datetime.now(timezone.utc),
        connection_attempts=1,
        max_retries=5,
    )

    # Linux Server 2 - API Server
    linux_server_2 = AgentProfile(
        device_id="linux_server_002",
        server_url="ws://192.168.1.102:5000/ws",
        os="linux",
        capabilities=[
            "log_collection",
            "file_operations",
            "system_monitoring",
            "bash_scripting",
            "database_operations",
        ],
        metadata={
            "hostname": "api-server-01",
            "location": "datacenter_rack_b",
            "os_version": "CentOS 8",
            "performance": "high",
            "cpu_cores": 12,
            "memory_gb": 32,
            "services": ["apache", "mysql", "mongodb"],
            "log_paths": [
                "/var/log/httpd/access_log",
                "/var/log/httpd/error_log",
                "/var/log/mysql/mysql.log",
                "/var/log/mongodb/mongod.log",
                "/var/log/messages",
            ],
        },
        status=DeviceStatus.CONNECTED,
        last_heartbeat=datetime.now(timezone.utc),
        connection_attempts=1,
        max_retries=5,
    )

    # Windows Workstation - Analyst PC
    windows_workstation = AgentProfile(
        device_id="windows_workstation_001",
        server_url="ws://192.168.1.100:5000/ws",
        os="windows",
        capabilities=[
            "office_applications",
            "excel_processing",
            "file_management",
            "data_analysis",
            "report_generation",
            "email_operations",
        ],
        metadata={
            "hostname": "analyst-pc-01",
            "location": "office_floor_2",
            "os_version": "Windows 11 Pro",
            "performance": "high",
            "cpu_cores": 8,
            "memory_gb": 32,
            "installed_software": [
                "Microsoft Office 365",
                "Python 3.11",
                "Excel",
                "Power BI",
                "Visual Studio Code",
            ],
            "excel_version": "16.0",
            "python_packages": ["pandas", "openpyxl", "xlsxwriter"],
        },
        status=DeviceStatus.CONNECTED,
        last_heartbeat=datetime.now(timezone.utc),
        connection_attempts=1,
        max_retries=5,
    )

    return linux_server_1, linux_server_2, windows_workstation


def create_mock_constellation_config(devices):
    """Create ConstellationConfig with mock devices."""
    device_configs = []

    for device in devices:
        device_config = DeviceConfig(
            device_id=device.device_id,
            server_url=device.server_url,
            capabilities=device.capabilities,
            metadata=device.metadata,
            auto_connect=True,
            max_retries=5,
        )
        device_configs.append(device_config)

    return ConstellationConfig(
        constellation_id="log_collection_demo_constellation",
        heartbeat_interval=30.0,
        reconnect_delay=5.0,
        max_concurrent_tasks=3,
        devices=device_configs,
    )


def create_mock_constellation_client(devices):
    """Create mock ConstellationClient with devices."""
    mock_client = AsyncMock()

    # Mock device registry
    mock_device_registry = Mock()
    device_dict = {device.device_id: device for device in devices}

    mock_device_registry.get_all_devices.return_value = device_dict
    mock_device_registry.get_connected_devices.return_value = [
        d.device_id for d in devices
    ]

    mock_client.device_manager = Mock()
    mock_client.device_manager.device_registry = mock_device_registry
    mock_client.device_manager.get_connected_devices.return_value = [
        d.device_id for d in devices
    ]

    # Mock initialization and shutdown
    mock_client.initialize = AsyncMock()
    mock_client.shutdown = AsyncMock()

    return mock_client


def create_mock_galaxy_session():
    """Create mock GalaxySession for demonstration."""
    mock_session = AsyncMock()
    mock_session._rounds = []
    mock_session.log_path = "./logs/demo_log_collection_session.log"

    # Mock constellation result
    mock_constellation = Mock()
    mock_constellation.constellation_id = "demo_constellation_001"
    mock_constellation.name = "Log Collection Demo Constellation"
    mock_constellation.tasks = [
        "collect_nginx_logs_server1",
        "collect_postgresql_logs_server1",
        "collect_apache_logs_server2",
        "collect_mysql_logs_server2",
        "aggregate_log_data",
        "generate_excel_report",
        "send_email_notification",
    ]
    mock_constellation.dependencies = [
        "collect_logs -> aggregate_log_data",
        "aggregate_log_data -> generate_excel_report",
        "generate_excel_report -> send_email_notification",
    ]
    mock_constellation.state = Mock()
    mock_constellation.state.value = "completed"

    mock_session._current_constellation = mock_constellation

    # Mock run method with realistic execution simulation
    async def mock_run_side_effect():
        print("  🔄 Analyzing user request...")
        mock_session._rounds.append(
            {"round": 1, "action": "analyze_request", "duration": 2.1}
        )

        print("  🏗️  Creating task constellation...")
        mock_session._rounds.append(
            {"round": 2, "action": "create_constellation", "duration": 1.8}
        )

        print("  📋 Planning device assignments...")
        mock_session._rounds.append(
            {"round": 3, "action": "plan_assignments", "duration": 1.5}
        )

        print("  🚀 Executing tasks across devices...")
        mock_session._rounds.append(
            {"round": 4, "action": "execute_tasks", "duration": 15.3}
        )

        print("  📊 Generating final report...")
        mock_session._rounds.append(
            {"round": 5, "action": "generate_report", "duration": 3.2}
        )

    mock_session.run = AsyncMock(side_effect=mock_run_side_effect)
    mock_session.force_finish = AsyncMock()

    return mock_session


async def demo_galaxy_client_log_collection():
    """Demonstrate GalaxyClient with mock devices for log collection."""

    print("🌟 Galaxy Client Log Collection Demo")
    print("=" * 50)

    # Create mock devices
    print("\n📱 Creating mock devices...")
    devices = create_mock_devices()
    linux1, linux2, windows = devices

    print(f"  ✅ Linux Server 1: {linux1.metadata['hostname']} ({linux1.device_id})")
    print(f"  ✅ Linux Server 2: {linux2.metadata['hostname']} ({linux2.device_id})")
    print(
        f"  ✅ Windows Workstation: {windows.metadata['hostname']} ({windows.device_id})"
    )

    # Create constellation config
    constellation_config = create_mock_constellation_config(devices)
    print(f"\n🏛️  Created constellation: {constellation_config.constellation_id}")
    print(f"    📊 Total devices: {len(constellation_config.devices)}")
    print(f"    ⚡ Max concurrent tasks: {constellation_config.max_concurrent_tasks}")

    # Create mocks for dependencies
    mock_constellation_client = create_mock_constellation_client(devices)
    mock_galaxy_session = create_mock_galaxy_session()

    # Setup patches and run demo
    with patch(
        "ufo.galaxy.galaxy_client.ConstellationConfig.from_yaml"
    ) as mock_from_yaml, patch(
        "ufo.galaxy.galaxy_client.ConstellationClient"
    ) as mock_client_class, patch(
        "ufo.galaxy.galaxy_client.GalaxySession"
    ) as mock_session_class:

        mock_from_yaml.return_value = constellation_config
        mock_client_class.return_value = mock_constellation_client
        mock_session_class.return_value = mock_galaxy_session

        # Initialize GalaxyClient
        print("\n🚀 Initializing Galaxy Client...")
        with tempfile.TemporaryDirectory() as temp_dir:
            client = GalaxyClient(
                session_name="demo_log_collection_session",
                max_rounds=10,
                log_level="WARNING",  # Reduce noise for demo
                output_dir=temp_dir,
            )

            await client.initialize()
            print("    ✅ Galaxy Client initialized successfully")

            # Verify device availability
            print("\n🔍 Checking device availability...")
            connected_devices = client._client.device_manager.get_connected_devices()
            print(f"    📡 Connected devices: {len(connected_devices)}")

            all_devices = (
                client._client.device_manager.device_registry.get_all_devices()
            )
            for device_id, device in all_devices.items():
                capabilities_summary = ", ".join(device.capabilities[:3])
                if len(device.capabilities) > 3:
                    capabilities_summary += f" (+{len(device.capabilities)-3} more)"
                print(f"      • {device_id}: {device.os} - {capabilities_summary}")

            # Process log collection request
            print("\n📝 Processing log collection request...")

            log_collection_request = (
                "Collect comprehensive logs from both Linux servers (web-server-01 and api-server-01). "
                "From web-server-01, gather nginx access/error logs, PostgreSQL logs, and system logs. "
                "From api-server-01, collect Apache logs, MySQL logs, MongoDB logs, and system messages. "
                "Then, on the Windows workstation, create a detailed Excel report with log analysis, "
                "error statistics, performance metrics, and trend analysis. "
                "Finally, email the report to the operations team."
            )

            print(f"    Request: {log_collection_request[:100]}...")

            print("\n🔄 Executing session...")
            result = await client.process_request(
                request=log_collection_request,
                task_name="comprehensive_log_collection_and_reporting",
            )

            # Display results
            print("\n📊 Session Results:")
            print(f"    ✅ Status: {result['status']}")
            print(f"    ⏱️  Execution time: {result['execution_time']:.2f} seconds")
            print(f"    🔄 Total rounds: {result['rounds']}")
            print(f"    📅 Start time: {result['start_time']}")

            if "constellation" in result:
                constellation_info = result["constellation"]
                print(f"\n🏛️  Constellation Details:")
                print(f"    🆔 ID: {constellation_info['id']}")
                print(f"    📛 Name: {constellation_info['name']}")
                print(f"    📋 Tasks: {constellation_info['task_count']}")
                print(f"    🔗 Dependencies: {constellation_info['dependency_count']}")
                print(f"    📊 State: {constellation_info['state']}")

            # Show mock task execution details
            print(f"\n📋 Task Execution Summary:")
            tasks = mock_galaxy_session._current_constellation.tasks
            for i, task in enumerate(tasks, 1):
                print(f"    {i}. {task}")

            print(f"\n🔗 Dependency Chain:")
            dependencies = mock_galaxy_session._current_constellation.dependencies
            for dep in dependencies:
                print(f"    • {dep}")

            # Cleanup
            print("\n🛑 Shutting down...")
            await client.shutdown()
            print("    ✅ Galaxy Client shutdown complete")

    print("\n🎉 Demo completed successfully!")
    print("\nKey Behaviors Demonstrated:")
    print("  ✅ Mock AgentProfile creation and configuration")
    print("  ✅ ConstellationConfig setup with multiple devices")
    print("  ✅ GalaxyClient initialization and request processing")
    print("  ✅ Cross-platform task orchestration simulation")
    print("  ✅ Session lifecycle management")
    print("  ✅ Error handling and resource cleanup")


if __name__ == "__main__":
    print("🌌 Starting Galaxy Client Demo with Mock AgentProfile")
    print(
        "🎯 Scenario: Log Collection from Linux Servers + Excel Generation on Windows"
    )
    print()

    try:
        asyncio.run(demo_galaxy_client_log_collection())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
