# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation v2 Client Package

This package provides the client-side implementation for the Constellation v2 system,
enabling multi-device orchestration and task distribution across UFO WebSocket servers.

Main Components:
- ConstellationClient: High-level client for device management and task execution
- ConstellationDeviceManager: Low-level device registration and connection management
- ConstellationConfig: Configuration loading from files, CLI, and environment variables

Example Usage:
    # Create client from config file
    client = await create_constellation_client(config_file="constellation.json")

    # Execute task on any available device
    result = await client.execute_task("take a screenshot")

    # Execute task on specific device
    result = await client.execute_task(
        "open notepad",
        device_id="windows_device"
    )

    # Execute multiple tasks in parallel
    tasks = [
        {"request": "take screenshot", "device_id": "device1"},
        {"request": "list files", "device_id": "device2"}
    ]
    results = await client.execute_tasks_parallel(tasks)
"""

from .constellation_client import ConstellationClient, create_constellation_client
from .constellation_client_modular import (
    ModularConstellationClient,
    create_modular_constellation_client,
)
from .device_manager import ConstellationDeviceManager
from .components import DeviceInfo, DeviceStatus, TaskRequest
from .config_loader import ConstellationConfig, DeviceConfig
from .orchestration import (
    TaskOrchestrator,
    ParallelTaskManager,
    DeviceSelector,
    ClientEventHandler,
    StatusManager,
    ClientConfigManager,
)

__all__ = [
    "ConstellationClient",
    "create_constellation_client",
    "ModularConstellationClient",
    "create_modular_constellation_client",
    "ConstellationDeviceManager",
    "ConstellationConfig",
    "DeviceConfig",
    "DeviceInfo",
    "DeviceStatus",
    "TaskRequest",
    # Orchestration components
    "TaskOrchestrator",
    "ParallelTaskManager",
    "DeviceSelector",
    "ClientEventHandler",
    "StatusManager",
    "ClientConfigManager",
]

__version__ = "2.0.0"
