# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation Device Management Client

Simplified client focused on device connection and basic task execution.
Serves as a support component for the main GalaxyClient system.
"""

import logging
from typing import Any, Dict, List, Optional

from .config_loader import ConstellationConfig, DeviceConfig
from .device_manager import ConstellationDeviceManager


class ConstellationClient:
    """
    Device Management Client for Constellation System.

    Simplified client focused on:
    - Device registration and connection management
    - Basic task execution interface
    - Configuration management
    - Status monitoring and reporting

    This client serves as a support component for the main GalaxyClient,
    handling device-level operations while complex DAG orchestration
    is handled by the TaskConstellationOrchestrator system.
    """

    def __init__(
        self,
        config: Optional[ConstellationConfig] = None,
        task_name: Optional[str] = None,
    ):
        """
        Initialize the constellation client for device management.

        :param config: Constellation configuration
        :param task_name: Override task name
        """
        self.config = config or ConstellationConfig()

        if task_name:
            self.config.task_name = task_name

        # Initialize device manager
        self.device_manager = ConstellationDeviceManager(
            task_name=self.config.task_name,
            heartbeat_interval=self.config.heartbeat_interval,
            reconnect_delay=self.config.reconnect_delay,
        )

        self.logger = logging.getLogger(__name__)

    # Configuration and Initialization
    async def initialize(self) -> Dict[str, bool]:
        """
        Initialize the constellation client and register devices from configuration.

        :return: Dictionary mapping device_id to registration success status
        """
        self.logger.info(
            f"🚀 Initializing Constellation Client: {self.config.task_name}"
        )
        results = {}

        # Register devices from configuration
        for device_config in self.config.devices:
            try:
                success = await self.register_device_from_config(device_config)
                results[device_config.device_id] = success
                if success:
                    self.logger.info(
                        f"✅ Device {device_config.device_id} registered successfully"
                    )
                else:
                    self.logger.error(
                        f"❌ Failed to register device {device_config.device_id}"
                    )
            except Exception as e:
                self.logger.error(
                    f"❌ Error registering device {device_config.device_id}: {e}"
                )
                results[device_config.device_id] = False

        return results

    async def register_device_from_config(self, device_config: DeviceConfig) -> bool:
        """
        Register a device from configuration.
        :param device_config: Device configuration
        :return: True if registration was successful, False otherwise
        """

        return await self.device_manager.register_device(
            device_id=device_config.device_id,
            server_url=device_config.server_url,
            os=device_config.os,
            capabilities=device_config.capabilities,
            metadata=device_config.metadata,
            auto_connect=device_config.auto_connect,
        )

    async def register_device(
        self,
        device_id: str,
        server_url: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_connect: bool = True,
    ) -> bool:
        """Register a device manually."""
        return await self.device_manager.register_device(
            device_id=device_id,
            server_url=server_url,
            capabilities=capabilities,
            metadata=metadata,
            auto_connect=auto_connect,
        )

    # Device Management Interface
    async def connect_device(self, device_id: str) -> bool:
        """Connect to a specific device."""
        return await self.device_manager.connect_device(device_id)

    async def disconnect_device(self, device_id: str) -> bool:
        """Disconnect from a specific device."""
        return await self.device_manager.disconnect_device(device_id)

    async def connect_all_devices(self) -> Dict[str, bool]:
        """Connect to all registered devices."""
        return await self.device_manager.connect_all_devices()

    async def disconnect_all_devices(self) -> None:
        """Disconnect from all devices."""
        await self.device_manager.disconnect_all_devices()

    async def ensure_devices_connected(self) -> Dict[str, bool]:
        """
        Ensure all registered devices are connected.
        Attempts to reconnect any disconnected devices.

        :return: Dictionary mapping device_id to connection status
        """
        return await self.device_manager.ensure_devices_connected()

    # Status and Information
    def get_device_status(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Get device status information."""
        if device_id:
            return self.device_manager.get_device_status(device_id)
        else:
            return {
                device_id: self.device_manager.get_device_status(device_id)
                for device_id in self.device_manager.get_connected_devices()
            }

    def get_connected_devices(self) -> List[str]:
        """Get list of connected device IDs."""
        return self.device_manager.get_connected_devices()

    def get_constellation_info(self) -> Dict[str, Any]:
        """Get constellation information and status."""
        return {
            "constellation_id": self.config.task_name,
            "connected_devices": len(self.device_manager.get_connected_devices()),
            "total_devices": len(self.config.devices),
            "configuration": {
                "heartbeat_interval": self.config.heartbeat_interval,
                "reconnect_delay": self.config.reconnect_delay,
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
            },
        }

    # Configuration Management
    def validate_config(
        self, config: Optional[ConstellationConfig] = None
    ) -> Dict[str, Any]:
        """Validate a constellation configuration."""
        target_config = config or self.config

        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Basic validation
        if not target_config.task_name:
            validation_result["valid"] = False
            validation_result["errors"].append("task_name is required")

        if not target_config.devices:
            validation_result["warnings"].append("No devices configured")

        return validation_result

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            "task_name": self.config.task_name,
            "devices_count": len(self.config.devices),
            "devices": [
                {
                    "device_id": device.device_id,
                    "server_url": device.server_url,
                    "capabilities": device.capabilities,
                    "auto_connect": device.auto_connect,
                }
                for device in self.config.devices
            ],
            "settings": {
                "heartbeat_interval": self.config.heartbeat_interval,
                "reconnect_delay": self.config.reconnect_delay,
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
            },
        }

    async def add_device_to_config(
        self,
        device_id: str,
        server_url: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_connect: bool = True,
        register_immediately: bool = True,
    ) -> bool:
        """Add a new device to the configuration and optionally register it."""
        # Create device config
        device_config = DeviceConfig(
            device_id=device_id,
            server_url=server_url,
            capabilities=capabilities or [],
            metadata=metadata or {},
            auto_connect=auto_connect,
        )

        # Add to configuration
        self.config.devices.append(device_config)

        # Register immediately if requested
        if register_immediately:
            return await self.register_device_from_config(device_config)

        return True

    # Lifecycle Management
    async def shutdown(self) -> None:
        """Shutdown the constellation client and disconnect all devices."""
        self.logger.info("🛑 Shutting down Constellation Client")

        # Shutdown device manager
        await self.device_manager.shutdown()

        self.logger.info("✅ Constellation Client shutdown complete")


# Convenience functions for backward compatibility and common operations


async def create_constellation_client(
    config_file: Optional[str] = None,
    task_name: Optional[str] = None,
    devices: Optional[List[Dict[str, Any]]] = None,
) -> ConstellationClient:
    """
    Create and initialize a modular constellation client.

    :param config_file: Path to configuration file
    :param constellation_id: Override constellation ID
    :param devices: List of device configurations
    :return: Initialized ConstellationClient
    """
    # Load configuration
    if config_file:
        config = ConstellationConfig.from_file(config_file)
    else:
        config = ConstellationConfig()

    # Add devices if provided
    if devices:
        for device in devices:
            config.add_device(
                device_id=device["device_id"],
                server_url=device["server_url"],
                capabilities=device.get("capabilities"),
                metadata=device.get("metadata"),
            )

    # Create and initialize client
    client = ConstellationClient(config=config, task_name=task_name)
    await client.initialize()

    return client
