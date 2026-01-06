# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation Manager for managing TaskConstellation lifecycle and state.

This module handles the management logic for TaskConstellation objects,
including device assignment, status tracking, and execution coordination.
"""

import logging
from typing import Any, Dict, List, Optional

from galaxy.client.device_manager import ConstellationDeviceManager

from ..task_constellation import TaskConstellation


class ConstellationManager:
    """
    Manages TaskConstellation lifecycle, device assignments, and execution state.

    This class handles:
    - Device assignment strategies
    - Constellation status tracking
    - Resource management
    - Execution coordination
    """

    def __init__(
        self,
        device_manager: Optional[ConstellationDeviceManager] = None,
        enable_logging: bool = True,
    ):
        """
        Initialize the ConstellationManager.

        :param device_manager: Optional device manager for device operations
        :param enable_logging: Whether to enable logging
        """
        self._device_manager = device_manager
        self._logger = logging.getLogger(__name__) if enable_logging else None

        # Track managed constellations
        self._managed_constellations: Dict[str, TaskConstellation] = {}
        self._constellation_metadata: Dict[str, Dict[str, Any]] = {}

    def set_device_manager(self, device_manager: ConstellationDeviceManager) -> None:
        """
        Set the device manager for device operations.

        :param device_manager: The constellation device manager instance
        """
        self._device_manager = device_manager
        if self._logger:
            self._logger.info("Device manager updated")

    def register_constellation(
        self,
        constellation: TaskConstellation,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a constellation for management.

        :param constellation: TaskConstellation to manage
        :param metadata: Optional metadata for the constellation
        :return: Constellation ID
        """
        constellation_id = constellation.constellation_id
        self._managed_constellations[constellation_id] = constellation
        self._constellation_metadata[constellation_id] = metadata or {}

        if self._logger:
            self._logger.info(
                f"Registered constellation '{constellation.name}' ({constellation_id})"
            )

        return constellation_id

    def unregister_constellation(self, constellation_id: str) -> bool:
        """
        Unregister a constellation from management.

        :param constellation_id: ID of constellation to unregister
        :return: True if unregistered, False if not found
        """
        if constellation_id in self._managed_constellations:
            constellation = self._managed_constellations[constellation_id]
            del self._managed_constellations[constellation_id]
            del self._constellation_metadata[constellation_id]

            if self._logger:
                self._logger.info(
                    f"Unregistered constellation '{constellation.name}' ({constellation_id})"
                )
            return True

        return False

    def get_constellation(self, constellation_id: str) -> Optional[TaskConstellation]:
        """
        Get a managed constellation by ID.

        :param constellation_id: Constellation ID
        :return: TaskConstellation if found, None otherwise
        """
        return self._managed_constellations.get(constellation_id)

    def list_constellations(self) -> List[Dict[str, Any]]:
        """
        List all managed constellations with their basic information.

        :return: List of constellation information dictionaries
        """
        result = []
        for constellation_id, constellation in self._managed_constellations.items():
            metadata = self._constellation_metadata.get(constellation_id, {})
            result.append(
                {
                    "constellation_id": constellation_id,
                    "name": constellation.name,
                    "state": constellation.state.value,
                    "task_count": constellation.task_count,
                    "dependency_count": constellation.dependency_count,
                    "metadata": metadata,
                }
            )

        return result

    async def assign_devices_automatically(
        self,
        constellation: TaskConstellation,
        strategy: str = "round_robin",
        device_preferences: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Automatically assign devices to tasks in a constellation.

        :param constellation: Target constellation
        :param strategy: Assignment strategy ("round_robin", "capability_match", "load_balance")
        :param device_preferences: Optional device preferences by task ID
        :return: Dictionary mapping task IDs to assigned device IDs
        """
        if not self._device_manager:
            raise ValueError("Device manager not available for device assignment")

        available_devices = await self._get_available_devices()
        if not available_devices:
            raise ValueError("No available devices for assignment")

        if self._logger:
            self._logger.info(
                f"Assigning devices to constellation '{constellation.name}' "
                f"using strategy '{strategy}'"
            )

        assignments = {}

        if strategy == "round_robin":
            assignments = await self._assign_round_robin(
                constellation, available_devices, device_preferences
            )
        elif strategy == "capability_match":
            assignments = await self._assign_capability_match(
                constellation, available_devices, device_preferences
            )
        elif strategy == "load_balance":
            assignments = await self._assign_load_balance(
                constellation, available_devices, device_preferences
            )
        else:
            raise ValueError(f"Unknown assignment strategy: {strategy}")

        # Apply assignments to tasks
        for task_id, device_id in assignments.items():
            task = constellation.get_task(task_id)
            if task:
                task.target_device_id = device_id

        if self._logger:
            self._logger.info(f"Assigned {len(assignments)} tasks to devices")

        return assignments

    async def _assign_round_robin(
        self,
        constellation: TaskConstellation,
        available_devices: List[Dict[str, Any]],
        preferences: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Round robin device assignment strategy."""
        assignments = {}
        device_index = 0

        for task_id, task in constellation.tasks.items():
            # Check preferences first
            if preferences and task_id in preferences:
                preferred_device = preferences[task_id]
                if any(d["device_id"] == preferred_device for d in available_devices):
                    assignments[task_id] = preferred_device
                    continue

            # Round robin assignment
            device = available_devices[device_index % len(available_devices)]
            assignments[task_id] = device["device_id"]
            device_index += 1

        return assignments

    async def _assign_capability_match(
        self,
        constellation: TaskConstellation,
        available_devices: List[Dict[str, Any]],
        preferences: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Capability-based device assignment strategy."""
        assignments = {}

        for task_id, task in constellation.tasks.items():
            # Check preferences first
            if preferences and task_id in preferences:
                preferred_device = preferences[task_id]
                if any(d["device_id"] == preferred_device for d in available_devices):
                    assignments[task_id] = preferred_device
                    continue

            # Find devices matching task requirements
            matching_devices = []

            if task.device_type:
                matching_devices = [
                    d
                    for d in available_devices
                    if d.get("device_type") == task.device_type.value
                ]

            # Fall back to any available device if no matches
            if not matching_devices:
                matching_devices = available_devices

            # Choose first matching device
            if matching_devices:
                assignments[task_id] = matching_devices[0]["device_id"]

        return assignments

    async def _assign_load_balance(
        self,
        constellation: TaskConstellation,
        available_devices: List[Dict[str, Any]],
        preferences: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Load-balanced device assignment strategy."""
        assignments = {}
        device_load = {d["device_id"]: 0 for d in available_devices}

        for task_id, task in constellation.tasks.items():
            # Check preferences first
            if preferences and task_id in preferences:
                preferred_device = preferences[task_id]
                if any(d["device_id"] == preferred_device for d in available_devices):
                    assignments[task_id] = preferred_device
                    device_load[preferred_device] += 1
                    continue

            # Find device with lowest load
            min_load_device = min(device_load.keys(), key=lambda d: device_load[d])
            assignments[task_id] = min_load_device
            device_load[min_load_device] += 1

        return assignments

    async def get_constellation_status(
        self, constellation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed status of a managed constellation.

        :param constellation_id: Constellation ID
        :return: Status information dictionary or None if not found
        """
        constellation = self._managed_constellations.get(constellation_id)
        if not constellation:
            return None

        metadata = self._constellation_metadata.get(constellation_id, {})

        return {
            "constellation_id": constellation_id,
            "name": constellation.name,
            "state": constellation.state.value,
            "statistics": constellation.get_statistics(),
            "ready_tasks": [task.task_id for task in constellation.get_ready_tasks()],
            "running_tasks": [
                task.task_id for task in constellation.get_running_tasks()
            ],
            "completed_tasks": [
                task.task_id for task in constellation.get_completed_tasks()
            ],
            "failed_tasks": [task.task_id for task in constellation.get_failed_tasks()],
            "metadata": metadata,
        }

    async def get_available_devices(self) -> List[Dict[str, Any]]:
        """
        Get list of available devices from device manager.

        :return: List of available device information
        """
        return await self._get_available_devices()

    async def _get_available_devices(self) -> List[Dict[str, Any]]:
        """Internal method to get available devices."""
        if not self._device_manager:
            return []

        try:
            connected_device_ids = self._device_manager.get_connected_devices()
            devices = []

            for device_id in connected_device_ids:
                device_info = self._device_manager.device_registry.get_device_info(
                    device_id
                )
                if device_info:
                    devices.append(
                        {
                            "device_id": device_id,
                            "device_type": getattr(
                                device_info, "device_type", "unknown"
                            ),
                            "capabilities": getattr(device_info, "capabilities", []),
                            "status": "connected",
                            "metadata": getattr(device_info, "metadata", {}),
                        }
                    )

            return devices
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to get available devices: {e}")
            return []

    def validate_constellation_assignments(
        self, constellation: TaskConstellation
    ) -> tuple[bool, List[str]]:
        """
        Validate that all tasks in a constellation have valid device assignments.

        :param constellation: Constellation to validate
        :return: Tuple of (is_valid, list_of_errors)
        """
        errors = []

        for task_id, task in constellation.tasks.items():
            if not task.target_device_id:
                errors.append(f"Task '{task_id}' has no device assignment")

        is_valid = len(errors) == 0

        if self._logger:
            if is_valid:
                self._logger.info(
                    f"All tasks in constellation '{constellation.name}' have valid assignments"
                )
            else:
                self._logger.warning(
                    f"Constellation '{constellation.name}' has {len(errors)} assignment errors"
                )

        return is_valid, errors

    def get_task_device_info(
        self, constellation: TaskConstellation, task_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get device information for a specific task.

        :param constellation: Target constellation
        :param task_id: Task ID
        :return: Device information or None if not assigned/found
        """
        task = constellation.get_task(task_id)
        if not task or not task.target_device_id:
            return None

        # Get device info from device manager
        if self._device_manager:
            try:
                device_info = self._device_manager.device_registry.get_device_info(
                    task.target_device_id
                )
                if device_info:
                    return {
                        "device_id": task.target_device_id,
                        "device_type": getattr(device_info, "device_type", "unknown"),
                        "capabilities": getattr(device_info, "capabilities", []),
                        "metadata": getattr(device_info, "metadata", {}),
                    }
            except Exception as e:
                if self._logger:
                    self._logger.error(
                        f"Failed to get device info for task '{task_id}': {e}"
                    )

        return None

    def reassign_task_device(
        self,
        constellation: TaskConstellation,
        task_id: str,
        new_device_id: str,
    ) -> bool:
        """
        Reassign a task to a different device.

        :param constellation: Target constellation
        :param task_id: Task ID to reassign
        :param new_device_id: New device ID
        :return: True if reassigned successfully, False otherwise
        """
        task = constellation.get_task(task_id)
        if not task:
            return False

        old_device_id = task.target_device_id
        task.target_device_id = new_device_id

        if self._logger:
            self._logger.info(
                f"Reassigned task '{task_id}' from device '{old_device_id}' to '{new_device_id}'"
            )

        return True

    def clear_device_assignments(self, constellation: TaskConstellation) -> int:
        """
        Clear all device assignments from a constellation.

        :param constellation: Target constellation
        :return: Number of assignments cleared
        """
        cleared_count = 0

        for task in constellation.tasks.values():
            if task.target_device_id:
                task.target_device_id = None
                cleared_count += 1

        if self._logger:
            self._logger.info(
                f"Cleared {cleared_count} device assignments from constellation '{constellation.name}'"
            )

        return cleared_count

    def get_device_utilization(
        self, constellation: TaskConstellation
    ) -> Dict[str, int]:
        """
        Get device utilization statistics for a constellation.

        :param constellation: Target constellation
        :return: Dictionary mapping device IDs to task counts
        """
        utilization = {}

        for task in constellation.tasks.values():
            if task.target_device_id:
                utilization[task.target_device_id] = (
                    utilization.get(task.target_device_id, 0) + 1
                )

        return utilization
