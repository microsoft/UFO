# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Configuration service for Galaxy Web UI.

This service handles reading and writing configuration files,
particularly the devices.yaml file.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigService:
    """
    Service for managing configuration files.

    Provides methods to read and write YAML configuration files,
    with specific support for the devices.yaml file.
    """

    def __init__(self, config_dir: Path = Path("config/galaxy")) -> None:
        """
        Initialize the configuration service.

        :param config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir
        self.devices_config_path = config_dir / "devices.yaml"
        self.logger: logging.Logger = logging.getLogger(__name__)

    def load_devices_config(self) -> Dict[str, Any]:
        """
        Load the devices configuration from devices.yaml.

        :return: Dictionary containing the devices configuration
        :raises FileNotFoundError: If devices.yaml does not exist
        :raises yaml.YAMLError: If YAML parsing fails
        """
        if not self.devices_config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.devices_config_path}"
            )

        try:
            with open(self.devices_config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}

            self.logger.debug(f"Loaded devices config from {self.devices_config_path}")
            return config_data

        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse YAML config: {e}")
            raise

    def save_devices_config(self, config_data: Dict[str, Any]) -> None:
        """
        Save the devices configuration to devices.yaml.

        :param config_data: Dictionary containing the devices configuration
        :raises IOError: If file writing fails
        """
        try:
            # Ensure the directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            with open(self.devices_config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    config_data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )

            self.logger.debug(f"Saved devices config to {self.devices_config_path}")

        except IOError as e:
            self.logger.error(f"Failed to write config file: {e}")
            raise

    def get_all_device_ids(self) -> List[str]:
        """
        Get a list of all device IDs in the configuration.

        :return: List of device IDs
        """
        try:
            config_data = self.load_devices_config()
            devices = config_data.get("devices", [])
            return [
                d.get("device_id")
                for d in devices
                if isinstance(d, dict) and "device_id" in d
            ]
        except Exception as e:
            self.logger.error(f"Failed to get device IDs: {e}")
            return []

    def device_id_exists(self, device_id: str) -> bool:
        """
        Check if a device ID already exists in the configuration.

        :param device_id: Device ID to check
        :return: True if device ID exists, False otherwise
        """
        existing_ids = self.get_all_device_ids()
        return device_id in existing_ids

    def add_device_to_config(
        self,
        device_id: str,
        server_url: str,
        os: str,
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]],
        auto_connect: bool,
        max_retries: int,
    ) -> Dict[str, Any]:
        """
        Add a new device to the configuration.

        :param device_id: Unique identifier for the device
        :param server_url: URL of the device's server endpoint
        :param os: Operating system of the device
        :param capabilities: List of capabilities the device supports
        :param metadata: Additional metadata about the device
        :param auto_connect: Whether to automatically connect to the device
        :param max_retries: Maximum number of connection retry attempts
        :return: The device entry that was added
        :raises ValueError: If device ID already exists
        """
        # Load existing configuration
        config_data = self.load_devices_config()

        # Ensure devices list exists
        if "devices" not in config_data:
            config_data["devices"] = []

        # Check for device_id conflict
        if self.device_id_exists(device_id):
            raise ValueError(f"Device ID '{device_id}' already exists")

        # Create new device entry
        new_device = {
            "device_id": device_id,
            "server_url": server_url,
            "os": os,
            "capabilities": capabilities,
            "auto_connect": auto_connect,
            "max_retries": max_retries,
        }

        # Add metadata if provided
        if metadata:
            new_device["metadata"] = metadata

        # Append new device to configuration
        config_data["devices"].append(new_device)

        # Save updated configuration
        self.save_devices_config(config_data)

        self.logger.info(f"✅ Device '{device_id}' added to configuration")
        return new_device
