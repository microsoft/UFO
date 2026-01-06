# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Status Manager

Handles status reporting and information management for ConstellationClient.
Single responsibility: Status and information coordination.
"""

import logging
from typing import Dict, List, Optional, Any

from ..device_manager import ConstellationDeviceManager
from ..config_loader import ConstellationConfig


class StatusManager:
    """
    Manages client status reporting and information aggregation.
    Single responsibility: Status information coordination.
    """

    def __init__(
        self,
        device_manager: ConstellationDeviceManager,
        config: ConstellationConfig,
        pending_task_tracker: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the status manager.

        :param device_manager: Device manager for device information
        :param config: Constellation configuration
        :param pending_task_tracker: Reference to pending task tracker
        """
        self.device_manager = device_manager
        self.config = config
        self.pending_task_tracker = pending_task_tracker or {}
        self.logger = logging.getLogger(f"{__name__}.StatusManager")

    def get_device_status(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get device status information.

        :param device_id: Specific device ID, or None for all devices
        :return: Device status information
        """
        if device_id:
            return self._get_single_device_status(device_id)
        else:
            return self._get_all_devices_status()

    def _get_single_device_status(self, device_id: str) -> Dict[str, Any]:
        """
        Get status for a single device.

        :param device_id: Device ID
        :return: Device status information
        """
        device_info = self.device_manager.get_device_info(device_id)
        device_caps = self.device_manager.get_device_capabilities(device_id)

        if device_info:
            return {
                "device_id": device_id,
                "status": device_info.status.value,
                "server_url": device_info.server_url,
                "local_clients": device_info.local_client_ids,
                "capabilities": device_info.capabilities
                + device_caps.get("capabilities", []),
                "metadata": {
                    **device_info.metadata,
                    **device_caps.get("metadata", {}),
                },
                "last_heartbeat": (
                    device_info.last_heartbeat.isoformat()
                    if device_info.last_heartbeat
                    else None
                ),
                "connection_attempts": device_info.connection_attempts,
                "max_retries": device_info.max_retries,
            }
        else:
            return {"error": f"Device {device_id} not found"}

    def _get_all_devices_status(self) -> Dict[str, Any]:
        """
        Get status for all devices.

        :return: All devices status information
        """
        all_devices = self.device_manager.get_all_devices()
        return {
            device_id: self._get_single_device_status(device_id)
            for device_id in all_devices.keys()
        }

    def get_connected_devices(self) -> List[str]:
        """Get list of connected device IDs."""
        return self.device_manager.get_connected_devices()

    def get_constellation_info(self) -> Dict[str, Any]:
        """
        Get constellation information and status.

        :return: Constellation status and statistics
        """
        connected_devices = self.get_connected_devices()
        all_devices = self.device_manager.get_all_devices()

        return {
            "task_name": self.config.task_name,
            "total_devices": len(all_devices),
            "connected_devices": len(connected_devices),
            "device_list": connected_devices,
            "max_concurrent_tasks": self.config.max_concurrent_tasks,
            "heartbeat_interval": self.config.heartbeat_interval,
            "reconnect_delay": self.config.reconnect_delay,
            "pending_tasks": len(self.pending_task_tracker),
            "configuration": {
                "auto_connect": getattr(self.config, "auto_connect", True),
                "retry_attempts": getattr(self.config, "retry_attempts", 3),
            },
        }

    def get_device_health_summary(self) -> Dict[str, Any]:
        """
        Get a health summary of all devices.

        :return: Device health summary
        """
        all_devices = self.device_manager.get_all_devices()
        connected_devices = self.get_connected_devices()

        health_summary = {
            "total_devices": len(all_devices),
            "connected_devices": len(connected_devices),
            "disconnected_devices": len(all_devices) - len(connected_devices),
            "connection_rate": (
                len(connected_devices) / len(all_devices) if all_devices else 0
            ),
            "devices_by_status": {},
            "devices_with_issues": [],
        }

        # Count devices by status
        status_counts = {}
        for device_id, device_info in all_devices.items():
            status = device_info.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            # Identify devices with issues
            if device_info.connection_attempts > 2:
                health_summary["devices_with_issues"].append(
                    {
                        "device_id": device_id,
                        "issue": "multiple_connection_attempts",
                        "attempts": device_info.connection_attempts,
                        "max_retries": device_info.max_retries,
                    }
                )

        health_summary["devices_by_status"] = status_counts

        return health_summary

    def get_task_statistics(self) -> Dict[str, Any]:
        """
        Get task execution statistics.

        :return: Task statistics
        """
        # Note: This is a basic implementation. In a full system, you'd track
        # completed tasks, success rates, execution times, etc.
        return {
            "pending_tasks": len(self.pending_task_tracker),
            "task_queue_health": (
                "healthy" if len(self.pending_task_tracker) < 100 else "overloaded"
            ),
            # TODO: Add completed task tracking
            "completed_tasks": 0,
            "success_rate": 0.0,
            "average_execution_time": 0.0,
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the constellation.

        :return: Performance metrics
        """
        device_health = self.get_device_health_summary()
        task_stats = self.get_task_statistics()

        return {
            "device_performance": {
                "connection_rate": device_health["connection_rate"],
                "devices_with_issues": len(device_health["devices_with_issues"]),
                "average_connection_attempts": self._calculate_average_connection_attempts(),
            },
            "task_performance": task_stats,
            "overall_health": self._calculate_overall_health_score(
                device_health, task_stats
            ),
        }

    def _calculate_average_connection_attempts(self) -> float:
        """Calculate the average number of connection attempts across all devices."""
        all_devices = self.device_manager.get_all_devices()
        if not all_devices:
            return 0.0

        total_attempts = sum(
            device.connection_attempts for device in all_devices.values()
        )
        return total_attempts / len(all_devices)

    def _calculate_overall_health_score(
        self, device_health: Dict[str, Any], task_stats: Dict[str, Any]
    ) -> float:
        """
        Calculate an overall health score (0.0 to 1.0).

        :param device_health: Device health summary
        :param task_stats: Task statistics
        :return: Health score between 0.0 and 1.0
        """
        # Simple health calculation
        connection_score = device_health["connection_rate"]

        # Task queue health score
        pending_tasks = task_stats["pending_tasks"]
        task_score = (
            1.0 if pending_tasks < 10 else max(0.0, 1.0 - (pending_tasks - 10) / 90)
        )

        # Weight the scores
        overall_score = (connection_score * 0.7) + (task_score * 0.3)

        return round(overall_score, 3)

    def get_diagnostics_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive diagnostics report.

        :return: Comprehensive diagnostics information
        """
        return {
            "constellation_info": self.get_constellation_info(),
            "device_health": self.get_device_health_summary(),
            "performance_metrics": self.get_performance_metrics(),
            "detailed_device_status": self.get_device_status(),
        }
