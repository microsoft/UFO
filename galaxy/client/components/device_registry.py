# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Device Registry

Manages device registration and information storage.
Single responsibility: Device data management.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .types import AgentProfile, DeviceStatus


class DeviceRegistry:
    """
    Manages device registration and information storage.
    Single responsibility: Device data management.
    """

    def __init__(self):
        self._devices: Dict[str, AgentProfile] = {}
        self._device_capabilities: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(f"{__name__}.DeviceRegistry")

    def register_device(
        self,
        device_id: str,
        server_url: str,
        os: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 5,
    ) -> AgentProfile:
        """
        Register a new device.

        :param device_id: Unique device identifier
        :param server_url: UFO WebSocket server URL
        :param capabilities: Device capabilities
        :param metadata: Additional metadata
        :param max_retries: Maximum connection retry attempts
        :return: Created AgentProfile object
        """
        device_info = AgentProfile(
            device_id=device_id,
            server_url=server_url,
            os=os,
            capabilities=capabilities.copy() if capabilities else [],
            metadata=metadata.copy() if metadata else {},
            status=DeviceStatus.DISCONNECTED,
            max_retries=max_retries,
        )

        self._devices[device_id] = device_info
        self.logger.info(
            f"📝 Registered device {device_id} with capabilities: {capabilities}"
        )
        return device_info

    def get_device(self, device_id: str) -> Optional[AgentProfile]:
        """Get device information by ID"""
        return self._devices.get(device_id)

    def get_all_devices(self, connected: bool = False) -> Dict[str, AgentProfile]:
        """
        Get all registered devices
        :param connected: If True, return only connected devices
        :return: Dictionary of device_id to AgentProfile
        """
        if connected:
            return {
                device_id: device_info
                for device_id, device_info in self._devices.items()
                if device_info.status
                in [DeviceStatus.CONNECTED, DeviceStatus.IDLE, DeviceStatus.BUSY]
            }
        return self._devices.copy()

    def update_device_status(self, device_id: str, status: DeviceStatus) -> None:
        """Update device connection status"""
        if device_id in self._devices:
            self._devices[device_id].status = status

    def set_device_busy(self, device_id: str, task_id: str) -> None:
        """
        Set device to BUSY status and track current task.

        :param device_id: Device ID
        :param task_id: Task ID being executed
        """
        if device_id in self._devices:
            self._devices[device_id].status = DeviceStatus.BUSY
            self._devices[device_id].current_task_id = task_id
            self.logger.info(f"🔄 Device {device_id} set to BUSY (task: {task_id})")

    def set_device_idle(self, device_id: str) -> None:
        """
        Set device to IDLE status and clear current task.

        :param device_id: Device ID
        """
        if device_id in self._devices:
            self._devices[device_id].status = DeviceStatus.IDLE
            self._devices[device_id].current_task_id = None
            self.logger.info(f"✅ Device {device_id} set to IDLE")

    def is_device_busy(self, device_id: str) -> bool:
        """
        Check if device is currently busy.

        :param device_id: Device ID
        :return: True if device is busy
        """
        if device_id in self._devices:
            return self._devices[device_id].status == DeviceStatus.BUSY
        return False

    def get_current_task(self, device_id: str) -> Optional[str]:
        """
        Get the current task ID being executed on device.

        :param device_id: Device ID
        :return: Current task ID or None
        """
        if device_id in self._devices:
            return self._devices[device_id].current_task_id
        return None

    def increment_connection_attempts(self, device_id: str) -> int:
        """Increment connection attempts counter"""
        if device_id in self._devices:
            self._devices[device_id].connection_attempts += 1
            return self._devices[device_id].connection_attempts
        return 0

    def reset_connection_attempts(self, device_id: str) -> None:
        """Reset connection attempts counter to 0"""
        if device_id in self._devices:
            self._devices[device_id].connection_attempts = 0
            self.logger.info(f"🔄 Reset connection attempts for device {device_id}")

    def update_heartbeat(self, device_id: str) -> None:
        """Update last heartbeat timestamp"""
        if device_id in self._devices:
            self._devices[device_id].last_heartbeat = datetime.now(timezone.utc)

    def set_device_capabilities(
        self, device_id: str, capabilities: Dict[str, Any]
    ) -> None:
        """Store device capabilities information"""
        self._device_capabilities[device_id] = capabilities

        # Also update device info with capabilities
        if device_id in self._devices:
            device_info = self._devices[device_id]
            if "capabilities" in capabilities:
                device_info.capabilities.extend(capabilities["capabilities"])
            if "metadata" in capabilities:
                device_info.metadata.update(capabilities["metadata"])

    def get_device_capabilities(self, device_id: str) -> Dict[str, Any]:
        """Get device capabilities"""
        return self._device_capabilities.get(device_id, {})

    def get_connected_devices(self) -> List[str]:
        """Get list of connected device IDs"""
        return [
            device_id
            for device_id, device_info in self._devices.items()
            if device_info.status == DeviceStatus.CONNECTED
        ]

    def is_device_registered(self, device_id: str) -> bool:
        """Check if device is registered"""
        return device_id in self._devices

    def remove_device(self, device_id: str) -> bool:
        """Remove a device from registry"""
        if device_id in self._devices:
            del self._devices[device_id]
            self._device_capabilities.pop(device_id, None)
            return True
        return False

    def update_device_system_info(
        self, device_id: str, system_info: Dict[str, Any]
    ) -> bool:
        """
        Update AgentProfile with system information retrieved from server.

        This method updates the device's OS, capabilities, and metadata with
        the system information that was automatically collected by the device
        and stored on the server.

        :param device_id: Device ID
        :param system_info: System information dictionary from server
        :return: True if update successful, False if device not found
        """
        device_info = self.get_device(device_id)
        if not device_info:
            self.logger.warning(
                f"Cannot update system info: device {device_id} not found"
            )
            return False

        # Update OS information
        if "platform" in system_info:
            device_info.os = system_info["platform"]

        # Update capabilities with supported features
        if "supported_features" in system_info:
            features = system_info["supported_features"]
            # Merge with existing capabilities (avoid duplicates)
            existing_caps = set(device_info.capabilities)
            new_caps = existing_caps.union(set(features))
            device_info.capabilities = list(new_caps)
            self.logger.debug(
                f"Updated capabilities for {device_id}: {device_info.capabilities}"
            )

        # Update metadata with system information
        device_info.metadata.update(
            {
                "system_info": {
                    "platform": system_info.get("platform"),
                    "os_version": system_info.get("os_version"),
                    "cpu_count": system_info.get("cpu_count"),
                    "memory_total_gb": system_info.get("memory_total_gb"),
                    "hostname": system_info.get("hostname"),
                    "ip_address": system_info.get("ip_address"),
                    "platform_type": system_info.get("platform_type"),
                    "schema_version": system_info.get("schema_version"),
                }
            }
        )

        # Add custom metadata from server config if present
        if "custom_metadata" in system_info:
            device_info.metadata["custom_metadata"] = system_info["custom_metadata"]

        # Add tags if present
        if "tags" in system_info:
            device_info.metadata["tags"] = system_info["tags"]

        self.logger.info(
            f"📊 Updated system info for {device_id}: "
            f"platform={system_info.get('platform')}, "
            f"cpu={system_info.get('cpu_count')}, "
            f"memory={system_info.get('memory_total_gb')}GB"
        )

        return True

    def get_device_system_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device system information (hardware, OS, features).

        :param device_id: Device ID
        :return: System information dictionary or None if not available
        """
        device_info = self.get_device(device_id)
        if not device_info:
            return None

        return device_info.metadata.get("system_info")
