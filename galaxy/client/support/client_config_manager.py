# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Client Config Manager

Handles configuration-based initialization and device registration.
Single responsibility: Configuration coordination.
"""

import logging
from typing import Dict, List, Optional, Any

from ..device_manager import ConstellationDeviceManager
from ..config_loader import ConstellationConfig, DeviceConfig


class ClientConfigManager:
    """
    Manages configuration-based initialization and device registration.
    Single responsibility: Configuration coordination.
    """

    def __init__(self, device_manager: ConstellationDeviceManager):
        """
        Initialize the client config manager.

        :param device_manager: Device manager for device operations
        """
        self.device_manager = device_manager
        self.logger = logging.getLogger(f"{__name__}.ClientConfigManager")

    async def initialize_from_config(
        self, config: ConstellationConfig
    ) -> Dict[str, bool]:
        """
        Initialize devices from configuration.

        :param config: Constellation configuration
        :return: Dictionary mapping device_id to registration success status
        """
        self.logger.info(
            f"🚀 Initializing constellation from config: {config.task_name}"
        )

        registration_results = {}

        # Register devices from configuration
        for device_config in config.devices:
            success = await self.register_device_from_config(device_config)
            registration_results[device_config.device_id] = success

            if success:
                self.logger.info(f"✅ Registered device {device_config.device_id}")
            else:
                self.logger.error(
                    f"❌ Failed to register device {device_config.device_id}"
                )

        # Summary
        successful_registrations = sum(
            1 for success in registration_results.values() if success
        )
        total_devices = len(registration_results)

        self.logger.info(
            f"📊 Device registration complete: {successful_registrations}/{total_devices} successful"
        )

        return registration_results

    async def register_device_from_config(self, device_config: DeviceConfig) -> bool:
        """
        Register a device from configuration.

        :param device_config: Device configuration
        :return: True if registration successful
        """
        try:
            return await self.device_manager.register_device(
                device_id=device_config.device_id,
                server_url=device_config.server_url,
                local_client_ids=device_config.local_client_ids,
                capabilities=device_config.capabilities,
                metadata=device_config.metadata,
                auto_connect=device_config.auto_connect,
            )
        except Exception as e:
            self.logger.error(
                f"❌ Failed to register device {device_config.device_id}: {e}"
            )
            return False

    async def add_device_to_config(
        self,
        config: ConstellationConfig,
        device_id: str,
        server_url: str,
        local_client_ids: List[str],
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_connect: bool = True,
        register_immediately: bool = True,
    ) -> bool:
        """
        Add a new device to the configuration and optionally register it.

        :param config: Constellation configuration to update
        :param device_id: Unique device identifier
        :param server_url: UFO WebSocket server URL
        :param local_client_ids: List of local client IDs on this device
        :param capabilities: Device capabilities
        :param metadata: Additional device metadata
        :param auto_connect: Whether to automatically connect
        :param register_immediately: Whether to register the device immediately
        :return: True if operation successful
        """
        try:
            # Add to configuration
            config.add_device(
                device_id=device_id,
                server_url=server_url,
                local_client_ids=local_client_ids,
                capabilities=capabilities,
                metadata=metadata,
                auto_connect=auto_connect,
            )

            self.logger.info(f"📝 Added device {device_id} to configuration")

            # Register immediately if requested
            if register_immediately:
                device_config = DeviceConfig(
                    device_id=device_id,
                    server_url=server_url,
                    local_client_ids=local_client_ids,
                    capabilities=capabilities or [],
                    metadata=metadata or {},
                    auto_connect=auto_connect,
                )

                success = await self.register_device_from_config(device_config)
                if success:
                    self.logger.info(
                        f"✅ Device {device_id} added and registered successfully"
                    )
                else:
                    self.logger.error(
                        f"❌ Device {device_id} added to config but registration failed"
                    )
                return success

            return True

        except Exception as e:
            self.logger.error(
                f"❌ Failed to add device {device_id} to configuration: {e}"
            )
            return False

    def validate_config(self, config: ConstellationConfig) -> Dict[str, Any]:
        """
        Validate a constellation configuration.

        :param config: Configuration to validate
        :return: Validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "device_count": len(config.devices),
            "device_validation": {},
        }

        # Validate task name
        if not config.task_name or len(config.task_name.strip()) == 0:
            validation_results["errors"].append("Task name is required")
            validation_results["valid"] = False

        # Validate device configurations
        device_ids = set()
        for device_config in config.devices:
            device_validation = self._validate_device_config(device_config)
            validation_results["device_validation"][
                device_config.device_id
            ] = device_validation

            if not device_validation["valid"]:
                validation_results["valid"] = False
                validation_results["errors"].extend(device_validation["errors"])

            # Check for duplicate device IDs
            if device_config.device_id in device_ids:
                validation_results["errors"].append(
                    f"Duplicate device ID: {device_config.device_id}"
                )
                validation_results["valid"] = False
            device_ids.add(device_config.device_id)

        # Validate configuration parameters
        if config.heartbeat_interval <= 0:
            validation_results["errors"].append("Heartbeat interval must be positive")
            validation_results["valid"] = False

        if config.max_concurrent_tasks <= 0:
            validation_results["errors"].append("Max concurrent tasks must be positive")
            validation_results["valid"] = False

        # Warnings
        if len(config.devices) == 0:
            validation_results["warnings"].append("No devices configured")

        if config.heartbeat_interval < 10:
            validation_results["warnings"].append(
                "Heartbeat interval is very short (< 10s)"
            )

        return validation_results

    def _validate_device_config(self, device_config: DeviceConfig) -> Dict[str, Any]:
        """
        Validate a single device configuration.

        :param device_config: Device configuration to validate
        :return: Validation results
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Required fields
        if not device_config.device_id or len(device_config.device_id.strip()) == 0:
            validation["errors"].append(f"Device ID is required")
            validation["valid"] = False

        if not device_config.server_url or len(device_config.server_url.strip()) == 0:
            validation["errors"].append(
                f"Server URL is required for device {device_config.device_id}"
            )
            validation["valid"] = False

        if (
            not device_config.local_client_ids
            or len(device_config.local_client_ids) == 0
        ):
            validation["errors"].append(
                f"At least one local client ID is required for device {device_config.device_id}"
            )
            validation["valid"] = False

        # URL format validation
        if device_config.server_url and not (
            device_config.server_url.startswith("ws://")
            or device_config.server_url.startswith("wss://")
        ):
            validation["warnings"].append(
                f"Server URL for {device_config.device_id} should start with ws:// or wss://"
            )

        # Client ID validation
        for client_id in device_config.local_client_ids:
            if not client_id or len(client_id.strip()) == 0:
                validation["errors"].append(
                    f"Empty local client ID found for device {device_config.device_id}"
                )
                validation["valid"] = False

        return validation

    def get_config_summary(self, config: ConstellationConfig) -> Dict[str, Any]:
        """
        Get a summary of the configuration.

        :param config: Configuration to summarize
        :return: Configuration summary
        """
        return {
            "task_name": config.task_name,
            "device_count": len(config.devices),
            "total_local_clients": sum(len(d.local_client_ids) for d in config.devices),
            "devices_with_capabilities": sum(
                1 for d in config.devices if d.capabilities
            ),
            "auto_connect_devices": sum(1 for d in config.devices if d.auto_connect),
            "configuration_parameters": {
                "heartbeat_interval": config.heartbeat_interval,
                "reconnect_delay": config.reconnect_delay,
                "max_concurrent_tasks": config.max_concurrent_tasks,
            },
            "validation": self.validate_config(config),
        }
