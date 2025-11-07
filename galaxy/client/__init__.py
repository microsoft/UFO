# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation v2 Client Package

This package provides the client-side implementation for the Constellation v2 system,
enabling multi-device orchestration and task distribution across UFO WebSocket servers.

Main Components:
- ConstellationClient: Device management and connection support component
- ConstellationDeviceManager: Low-level device registration and connection management
- ConstellationConfig: Configuration loading from files, CLI, and environment variables

Note: For task execution, use the main GalaxyClient which provides DAG orchestration
and complex task management. ConstellationClient serves as a device management
support component.

Example Usage:

    # Device management
    await client.connect_device("windows_device")
    devices = client.get_connected_devices()
    status = client.get_constellation_info()

    # For task execution, use GalaxyClient instead:
    # from galaxy import GalaxyClient
    # galaxy = GalaxyClient()
    # result = await galaxy.process_request("take a screenshot")
"""

from .constellation_client import ConstellationClient
from .device_manager import ConstellationDeviceManager
from .components import AgentProfile, DeviceStatus, TaskRequest
from .config_loader import ConstellationConfig, DeviceConfig
from .support import (
    StatusManager,
    ClientConfigManager,
)

__all__ = [
    "ConstellationClient",
    "ConstellationDeviceManager",
    "ConstellationConfig",
    "DeviceConfig",
    "AgentProfile",
    "DeviceStatus",
    "TaskRequest",
    # Support components
    "StatusManager",
    "ClientConfigManager",
]

__version__ = "2.0.0"
