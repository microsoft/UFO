# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task Orchestration Bridge for TaskConstellation V2.

This module provides the bridge between the TaskConstellation orchestration system
and the ModularConstellationClient device management infrastructure.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Union

from .enums import TaskStatus, DeviceType
from .task_star import TaskStar
from .task_constellation import TaskConstellation
from .executor import ConstellationExecutor
from .parser import LLMParser


class TaskOrchestration:
    """
    Bridge between TaskConstellation orchestration and ModularConstellationClient.

    This class provides the interface for managing TaskConstellation execution
    using the existing device management and client infrastructure.
    """

    def __init__(
        self,
        modular_client: Optional[Any] = None,
        enable_logging: bool = True,
    ):
        """
        Initialize the TaskOrchestration.

        Args:
            modular_client: Instance of ModularConstellationClient
            enable_logging: Whether to enable logging
        """
        self._modular_client = modular_client
        self._executor = ConstellationExecutor(enable_logging=enable_logging)
        self._parser = LLMParser()
        self._logger = logging.getLogger(__name__) if enable_logging else None

        # Set up client interface for executor
        self._executor.set_client_interface(self._execute_task_on_device)

    def set_modular_client(self, client: Any) -> None:
        """Set the modular constellation client for device communication."""
        self._modular_client = client

    async def create_constellation_from_llm(
        self,
        llm_output: str,
        constellation_name: Optional[str] = None,
    ) -> TaskConstellation:
        """
        Create a TaskConstellation from LLM output.

        Args:
            llm_output: Raw LLM output describing tasks and dependencies
            constellation_name: Optional name for the constellation

        Returns:
            TaskConstellation instance
        """
        if self._logger:
            self._logger.info(
                f"Creating constellation from LLM output: {constellation_name}"
            )

        constellation = self._parser.parse_from_string(llm_output, constellation_name)

        if self._logger:
            self._logger.info(
                f"Created constellation with {constellation.task_count} tasks "
                f"and {constellation.dependency_count} dependencies"
            )

        return constellation

    async def orchestrate_constellation(
        self,
        constellation: TaskConstellation,
        device_assignments: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable[[str, TaskStatus, Any], None]] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrate the execution of a TaskConstellation.

        Args:
            constellation: TaskConstellation to orchestrate
            device_assignments: Optional manual device assignments
            progress_callback: Optional progress callback

        Returns:
            Orchestration results and statistics
        """
        if not self._modular_client:
            raise ValueError(
                "ModularConstellationClient not set. Use set_modular_client() first."
            )

        if self._logger:
            self._logger.info(
                f"Starting orchestration of constellation {constellation.constellation_id}"
            )

        # Apply device assignments if provided
        if device_assignments:
            self._apply_device_assignments(constellation, device_assignments)

        # Get available devices from modular client
        device_client_map = await self._get_available_devices()

        # Execute the constellation
        result = await self._executor.execute_constellation(
            constellation,
            device_client_map=device_client_map,
            progress_callback=progress_callback,
        )

        if self._logger:
            self._logger.info(
                f"Completed orchestration of constellation {constellation.constellation_id}"
            )

        return result

    async def execute_single_task(
        self,
        task: TaskStar,
        target_device_id: Optional[str] = None,
    ) -> Any:
        """
        Execute a single task on a specific device.

        Args:
            task: TaskStar to execute
            target_device_id: Optional target device ID

        Returns:
            Task execution result
        """
        if target_device_id:
            task.target_device_id = target_device_id

        return await self._executor.execute_single_task(task)

    async def modify_constellation_with_llm(
        self,
        constellation: TaskConstellation,
        modification_request: str,
    ) -> TaskConstellation:
        """
        Modify an existing constellation using LLM.

        Args:
            constellation: Existing TaskConstellation
            modification_request: LLM request for modifications

        Returns:
            Modified TaskConstellation
        """
        # Generate prompt for LLM
        prompt = self._parser.generate_llm_prompt(constellation)
        full_prompt = f"{prompt}\n\nModification Request: {modification_request}"

        # In a real implementation, you would call an LLM service here
        # For now, we'll just log the prompt and return the original constellation
        if self._logger:
            self._logger.info(
                f"Generated LLM prompt for modification: {full_prompt[:200]}..."
            )

        # Placeholder for LLM integration
        # llm_response = await call_llm_service(full_prompt)
        # return self._parser.update_constellation_from_llm(constellation, llm_response)

        return constellation

    async def get_constellation_status(
        self, constellation: TaskConstellation
    ) -> Dict[str, Any]:
        """
        Get detailed status of a constellation.

        Args:
            constellation: TaskConstellation to check

        Returns:
            Status information
        """
        return {
            "constellation_id": constellation.constellation_id,
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
            "executor_stats": self._executor.stats,
        }

    async def get_available_devices(self) -> List[Dict[str, Any]]:
        """
        Get list of available devices from modular client.

        Returns:
            List of available device information
        """
        if not self._modular_client:
            return []

        try:
            # Get connected devices from ModularConstellationClient
            connected_device_ids = self._modular_client.get_connected_devices()
            devices = []

            for device_id in connected_device_ids:
                device_status = self._modular_client.get_device_status(device_id)
                if device_status:
                    devices.append(
                        {
                            "device_id": device_id,
                            "device_type": device_status.get("device_type", "unknown"),
                            "capabilities": device_status.get("capabilities", []),
                            "status": device_status.get("status", "unknown"),
                            "metadata": device_status.get("metadata", {}),
                        }
                    )

            return devices
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to get available devices: {e}")
            return []

    async def assign_devices_automatically(
        self,
        constellation: TaskConstellation,
        device_preferences: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Automatically assign devices to tasks based on capabilities and preferences.

        Args:
            constellation: TaskConstellation to assign devices to
            device_preferences: Optional device preferences by task ID
        """
        available_devices = await self.get_available_devices()

        if not available_devices:
            if self._logger:
                self._logger.warning("No available devices for task assignment")
            return

        # Simple assignment logic - can be enhanced
        for task in constellation.tasks.values():
            if task.target_device_id:
                continue  # Already assigned

            # Check preferences first
            if device_preferences and task.task_id in device_preferences:
                preferred_device = device_preferences[task.task_id]
                if any(d["device_id"] == preferred_device for d in available_devices):
                    task.target_device_id = preferred_device
                    continue

            # Auto-assign based on device type
            if task.device_type:
                matching_devices = [
                    d
                    for d in available_devices
                    if d["device_type"] == task.device_type.value
                ]
                if matching_devices:
                    task.target_device_id = matching_devices[0]["device_id"]
                    continue

            # Fall back to first available device
            if available_devices:
                task.target_device_id = available_devices[0]["device_id"]

    def export_constellation(
        self,
        constellation: TaskConstellation,
        format: str = "json",
    ) -> str:
        """
        Export constellation to various formats.

        Args:
            constellation: TaskConstellation to export
            format: Export format ("json", "yaml", "llm")

        Returns:
            Exported string representation
        """
        if format.lower() == "json":
            return constellation.to_json(indent=2)
        elif format.lower() == "llm":
            return constellation.to_llm_string()
        elif format.lower() == "yaml":
            # For YAML export, you would need PyYAML
            # For now, return JSON with a note
            return f"# YAML export not implemented, returning JSON:\n{constellation.to_json(indent=2)}"
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def import_constellation(
        self,
        data: str,
        format: str = "json",
    ) -> TaskConstellation:
        """
        Import constellation from various formats.

        Args:
            data: String data to import
            format: Import format ("json", "llm")

        Returns:
            TaskConstellation instance
        """
        if format.lower() == "json":
            return TaskConstellation.from_json(data)
        elif format.lower() == "llm":
            return self._parser.parse_from_string(data)
        else:
            raise ValueError(f"Unsupported import format: {format}")

    async def _execute_task_on_device(self, task: TaskStar) -> Any:
        """
        Execute a task on the assigned device using modular client.

        Args:
            task: TaskStar to execute

        Returns:
            Task execution result
        """
        if not self._modular_client:
            raise ValueError("ModularConstellationClient not configured")

        if not task.target_device_id:
            raise ValueError(f"No device assigned to task {task.task_id}")

        try:
            # Execute task using ModularConstellationClient with correct method signature
            result = await self._modular_client.execute_task(
                request=task.description,
                device_id=task.target_device_id,
                task_name=task.task_id,
                metadata=task.task_data,
                timeout=task._timeout,
            )

            return result

        except Exception as e:
            if self._logger:
                self._logger.error(
                    f"Failed to execute task {task.task_id} on device {task.target_device_id}: {e}"
                )
            raise

    async def _get_available_devices(self) -> Dict[str, Any]:
        """Get available devices as a map for the executor."""
        if not self._modular_client:
            return {}

        try:
            # Get connected devices from ModularConstellationClient
            connected_device_ids = self._modular_client.get_connected_devices()
            device_map = {}

            for device_id in connected_device_ids:
                device_status = self._modular_client.get_device_status(device_id)
                if device_status:
                    # Create a simple device info object
                    device_info = type(
                        "DeviceInfo",
                        (),
                        {
                            "device_id": device_id,
                            "device_type": device_status.get("device_type", "unknown"),
                            "capabilities": device_status.get("capabilities", []),
                            "status": device_status.get("status", "unknown"),
                            "metadata": device_status.get("metadata", {}),
                        },
                    )
                    device_map[device_id] = device_info

            return device_map
        except Exception:
            return {}

    def _apply_device_assignments(
        self,
        constellation: TaskConstellation,
        assignments: Dict[str, str],
    ) -> None:
        """Apply manual device assignments to tasks."""
        for task_id, device_id in assignments.items():
            task = constellation.get_task(task_id)
            if task:
                task.target_device_id = device_id


# Convenience functions for easier usage
async def create_and_orchestrate_from_llm(
    llm_output: str,
    modular_client: Any,
    constellation_name: Optional[str] = None,
    progress_callback: Optional[Callable[[str, TaskStatus, Any], None]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to create and orchestrate a constellation from LLM output.

    Args:
        llm_output: LLM output describing tasks
        modular_client: ModularConstellationClient instance
        constellation_name: Optional constellation name
        progress_callback: Optional progress callback

    Returns:
        Orchestration results
    """
    orchestrator = TaskOrchestration(modular_client)

    # Create constellation from LLM
    constellation = await orchestrator.create_constellation_from_llm(
        llm_output, constellation_name
    )

    # Assign devices automatically
    await orchestrator.assign_devices_automatically(constellation)

    # Orchestrate constellation
    return await orchestrator.orchestrate_constellation(
        constellation, progress_callback=progress_callback
    )


def create_simple_constellation(
    task_descriptions: List[str],
    constellation_name: str = "Simple Constellation",
    sequential: bool = True,
) -> TaskConstellation:
    """
    Create a simple constellation from a list of task descriptions.

    Args:
        task_descriptions: List of task descriptions
        constellation_name: Name for the constellation
        sequential: Whether to make tasks sequential (True) or parallel (False)

    Returns:
        TaskConstellation instance
    """
    from .task_star_line import TaskStarLine

    constellation = TaskConstellation(name=constellation_name)

    # Create tasks
    tasks = []
    for i, description in enumerate(task_descriptions):
        task = TaskStar(
            task_id=f"task_{i+1}",
            description=description,
        )
        constellation.add_task(task)
        tasks.append(task)

    # Add dependencies if sequential
    if sequential and len(tasks) > 1:
        for i in range(len(tasks) - 1):
            dep = TaskStarLine.create_unconditional(
                tasks[i].task_id,
                tasks[i + 1].task_id,
                f"Sequential dependency: {tasks[i].task_id} -> {tasks[i + 1].task_id}",
            )
            constellation.add_dependency(dep)

    return constellation
