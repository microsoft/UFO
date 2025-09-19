# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Device Selector

Handles device selection based on capabilities, load balancing, and availability.
Single responsibility: Device selection logic.
"""

import logging
from typing import Dict, List, Optional, Any

from ..device_manager import ConstellationDeviceManager


class DeviceSelector:
    """
    Manages device selection based on capabilities and availability.
    Single responsibility: Device selection coordination.
    """

    def __init__(self, device_manager: ConstellationDeviceManager):
        """
        Initialize the device selector.

        :param device_manager: Device manager for device information
        """
        self.device_manager = device_manager
        self.logger = logging.getLogger(f"{__name__}.DeviceSelector")

    async def select_best_device(
        self,
        capabilities_required: Optional[List[str]] = None,
        device_type_preference: Optional[str] = None,
        exclude_devices: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Select the best available device for task execution.

        :param capabilities_required: Required capabilities
        :param device_type_preference: Preferred device type (e.g., "windows", "linux")
        :param exclude_devices: Devices to exclude from selection
        :return: Selected device ID or None
        """
        connected_devices = self.device_manager.get_connected_devices()

        if not connected_devices:
            self.logger.warning("❌ No connected devices available for task execution")
            return None

        # Filter out excluded devices
        if exclude_devices:
            connected_devices = [
                d for d in connected_devices if d not in exclude_devices
            ]
            if not connected_devices:
                self.logger.warning("❌ All connected devices are excluded")
                return None

        # If no specific capabilities required, use first available device
        if not capabilities_required:
            selected = connected_devices[0]
            self.logger.info(
                f"🎯 Selected device {selected} (no specific capabilities required)"
            )
            return selected

        # Find devices with required capabilities
        suitable_devices = []

        for device_id in connected_devices:
            if self._device_has_capabilities(device_id, capabilities_required):
                suitable_devices.append(device_id)

        if not suitable_devices:
            # Fallback to any connected device if no perfect match
            self.logger.warning(
                f"⚠️ No devices found with capabilities {capabilities_required}, "
                f"falling back to first available device"
            )
            selected = connected_devices[0]
            self.logger.info(f"🎯 Selected fallback device {selected}")
            return selected

        # Apply device type preference if specified
        if device_type_preference:
            preferred_devices = []
            for device_id in suitable_devices:
                device_info = self.device_manager.get_device_info(device_id)
                if (
                    device_info
                    and device_info.metadata.get("os", "").lower()
                    == device_type_preference.lower()
                ):
                    preferred_devices.append(device_id)

            if preferred_devices:
                suitable_devices = preferred_devices

        # Use load balancing - select device with least recent activity
        # For now, use simple round-robin (first device)
        # TODO: Implement proper load balancing based on task history
        selected = suitable_devices[0]

        self.logger.info(
            f"🎯 Selected device {selected} from {len(suitable_devices)} suitable devices "
            f"(capabilities: {capabilities_required})"
        )
        return selected

    def _device_has_capabilities(
        self, device_id: str, required_capabilities: List[str]
    ) -> bool:
        """
        Check if a device has the required capabilities.

        :param device_id: Device to check
        :param required_capabilities: Required capabilities
        :return: True if device has all required capabilities
        """
        device_info = self.device_manager.get_device_info(device_id)
        device_capabilities = self.device_manager.get_device_capabilities(device_id)

        if not device_info:
            return False

        # Combine capabilities from device info and runtime capabilities
        available_caps = device_info.capabilities + device_capabilities.get(
            "capabilities", []
        )

        # Check if device has all required capabilities
        return all(cap in available_caps for cap in required_capabilities)

    def get_device_suitability_score(
        self,
        device_id: str,
        capabilities_required: Optional[List[str]] = None,
        device_type_preference: Optional[str] = None,
    ) -> float:
        """
        Calculate a suitability score for a device based on requirements.

        :param device_id: Device to score
        :param capabilities_required: Required capabilities
        :param device_type_preference: Preferred device type
        :return: Suitability score (0.0 to 1.0, higher is better)
        """
        device_info = self.device_manager.get_device_info(device_id)
        if not device_info:
            return 0.0

        score = 0.0

        # Base score for being connected
        if device_id in self.device_manager.get_connected_devices():
            score += 0.3

        # Capability match score
        if capabilities_required:
            if self._device_has_capabilities(device_id, capabilities_required):
                score += 0.5
            else:
                # Partial capability match
                device_capabilities = self.device_manager.get_device_capabilities(
                    device_id
                )
                available_caps = device_info.capabilities + device_capabilities.get(
                    "capabilities", []
                )
                matched_caps = sum(
                    1 for cap in capabilities_required if cap in available_caps
                )
                score += 0.3 * (matched_caps / len(capabilities_required))
        else:
            # No specific requirements, small bonus
            score += 0.1

        # Device type preference score
        if device_type_preference:
            device_os = device_info.metadata.get("os", "").lower()
            if device_os == device_type_preference.lower():
                score += 0.2

        return min(score, 1.0)

    def rank_devices_by_suitability(
        self,
        capabilities_required: Optional[List[str]] = None,
        device_type_preference: Optional[str] = None,
        exclude_devices: Optional[List[str]] = None,
    ) -> List[tuple]:
        """
        Rank all connected devices by their suitability for a task.

        :param capabilities_required: Required capabilities
        :param device_type_preference: Preferred device type
        :param exclude_devices: Devices to exclude
        :return: List of (device_id, score) tuples sorted by score (descending)
        """
        connected_devices = self.device_manager.get_connected_devices()

        if exclude_devices:
            connected_devices = [
                d for d in connected_devices if d not in exclude_devices
            ]

        rankings = []
        for device_id in connected_devices:
            score = self.get_device_suitability_score(
                device_id, capabilities_required, device_type_preference
            )
            rankings.append((device_id, score))

        # Sort by score in descending order
        rankings.sort(key=lambda x: x[1], reverse=True)

        self.logger.debug(f"📊 Device rankings: {rankings}")
        return rankings
