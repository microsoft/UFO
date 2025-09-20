# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task Orchestration Bridge for TaskConstellation V2.

This module provides the simplified orchestration bridge between the TaskConstellation
orchestration system and the ConstellationDeviceManager device management infrastructure.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union

from ufo.galaxy.client.device_manager import ConstellationDeviceManager

from ..core.events import EventBus, EventType, TaskEvent, get_event_bus
from ..core.types import ProcessingContext
from .enums import DeviceType, TaskStatus
from .parser import LLMParser
from .task_constellation import TaskConstellation
from .task_star import TaskStar


class TaskOrchestration:
    """
    Simplified DAG orchestrator with direct device communication.

    This class provides direct interface for managing TaskConstellation execution
    using the device management infrastructure without unnecessary intermediate layers.
    """

    def __init__(
        self,
        device_manager: Optional[ConstellationDeviceManager] = None,
        enable_logging: bool = True,
        event_bus=None,
    ):
        """
        Initialize the TaskOrchestration.

        :param device_manager: Instance of ConstellationDeviceManager
        :param enable_logging: Whether to enable logging
        :param event_bus: Event bus for publishing events
        """
        self._device_manager = device_manager
        self._parser = LLMParser()
        self._logger = logging.getLogger(__name__) if enable_logging else None

        # Initialize event bus for publishing events
        if event_bus is None:
            from ..core.events import get_event_bus

            self._event_bus = get_event_bus()
        else:
            self._event_bus = event_bus

        # Track active constellations and their execution tasks
        self._active_constellations: Dict[str, TaskConstellation] = {}
        self._execution_tasks: Dict[str, asyncio.Task] = {}

    def set_device_manager(self, device_manager: ConstellationDeviceManager) -> None:
        """
        Set the device manager for device communication.

        :param device_manager: The constellation device manager instance
        """
        self._device_manager = device_manager

    async def create_constellation_from_llm(
        self,
        llm_output: str,
        constellation_name: Optional[str] = None,
    ) -> TaskConstellation:
        """
        Create a TaskConstellation from LLM output.

        :param llm_output: Raw LLM output describing tasks and dependencies
        :param constellation_name: Optional name for the constellation
        :return: TaskConstellation instance
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
    ) -> Dict[str, Any]:
        """
        Orchestrate DAG execution using event-driven pattern.

        :param constellation: TaskConstellation to orchestrate
        :param device_assignments: Optional manual device assignments
        :return: Orchestration results and statistics
        """
        if not self._device_manager:
            raise ValueError(
                "ConstellationDeviceManager not set. Use set_device_manager() first."
            )

        constellation_id = constellation.constellation_id
        self._active_constellations[constellation_id] = constellation

        if self._logger:
            self._logger.info(
                f"Starting orchestration of constellation {constellation_id}"
            )

        # Validate DAG structure
        is_valid, errors = constellation.validate_dag()
        if not is_valid:
            raise ValueError(f"Invalid DAG: {errors}")

        # Apply device assignments if provided
        if device_assignments:
            self._apply_device_assignments(constellation, device_assignments)

        # Execute DAG with event-driven approach
        results = {}
        constellation.start_execution()

        try:
            # Main execution loop - continue until all tasks complete
            while not constellation.is_complete():
                ready_tasks = constellation.get_ready_tasks()

                # Create execution tasks for ready tasks
                for task in ready_tasks:
                    if task.task_id not in self._execution_tasks:
                        # Auto-assign device if not already assigned
                        if not task.target_device_id:
                            task.target_device_id = await self._auto_assign_device(task)

                        # Create task execution future
                        task_future = asyncio.create_task(
                            self._execute_task_with_events(task, constellation)
                        )
                        self._execution_tasks[task.task_id] = task_future

                # Wait for at least one task to complete
                if self._execution_tasks:
                    done, pending = await asyncio.wait(
                        self._execution_tasks.values(),
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=1.0,  # Periodically check for new tasks
                    )

                    # Clean up completed tasks
                    completed_task_ids = []
                    for task_future in done:
                        for task_id, future in self._execution_tasks.items():
                            if future == task_future:
                                completed_task_ids.append(task_id)
                                break

                    for task_id in completed_task_ids:
                        del self._execution_tasks[task_id]
                else:
                    # No running tasks, wait briefly
                    await asyncio.sleep(0.1)

            # Wait for all remaining tasks to complete
            if self._execution_tasks:
                await asyncio.gather(
                    *self._execution_tasks.values(), return_exceptions=True
                )
                self._execution_tasks.clear()

            constellation.complete_execution()

            if self._logger:
                self._logger.info(
                    f"Completed orchestration of constellation {constellation_id}"
                )

            return {
                "results": results,
                "status": "completed",
                "total_tasks": len(results),
            }

        except Exception as e:
            constellation.complete_execution()
            if self._logger:
                self._logger.error(f"Orchestration failed: {e}")
            raise

        finally:
            # Cleanup resources
            if constellation_id in self._active_constellations:
                del self._active_constellations[constellation_id]

    async def _execute_task_with_events(
        self,
        task: TaskStar,
        constellation: TaskConstellation,
    ) -> None:
        """
        Execute a single task and publish events.

        :param task: The TaskStar to execute
        :param constellation: The parent TaskConstellation
        :return: Task execution result
        """
        try:
            # Import event classes

            # Publish task started event
            start_event = TaskEvent(
                event_type=EventType.TASK_STARTED,
                source_id=f"orchestrator_{id(self)}",
                timestamp=time.time(),
                data={"constellation_id": constellation.constellation_id},
                task_id=task.task_id,
                status=TaskStatus.RUNNING.value,
            )
            await self._event_bus.publish_event(start_event)

            # Execute the task
            result = await task.execute(self._device_manager)

            # Mark task as completed in constellation
            newly_ready = constellation.mark_task_completed(
                task.task_id, success=True, result=result
            )

            # Publish task completed event
            completed_event = TaskEvent(
                event_type=EventType.TASK_COMPLETED,
                source_id=f"orchestrator_{id(self)}",
                timestamp=time.time(),
                data={
                    "constellation_id": constellation.constellation_id,
                    "newly_ready_tasks": [t.task_id for t in newly_ready],
                },
                task_id=task.task_id,
                status=TaskStatus.COMPLETED.value,
                result=result,
            )
            await self._event_bus.publish_event(completed_event)

            if self._logger:
                self._logger.info(f"Task {task.task_id} completed successfully")

        except Exception as e:
            # Mark task as failed in constellation
            newly_ready = constellation.mark_task_completed(
                task.task_id, success=False, error=e
            )

            # Publish task failed event

            failed_event = TaskEvent(
                event_type=EventType.TASK_FAILED,
                source_id=f"orchestrator_{id(self)}",
                timestamp=time.time(),
                data={
                    "constellation_id": constellation.constellation_id,
                    "newly_ready_tasks": [t.task_id for t in newly_ready],
                },
                task_id=task.task_id,
                status=TaskStatus.FAILED.value,
                error=e,
            )
            await self._event_bus.publish_event(failed_event)

            if self._logger:
                self._logger.error(f"Task {task.task_id} failed: {e}")
            if self._logger:
                self._logger.error(f"Orchestration failed: {e}")
            raise

        return result

    async def execute_single_task(
        self,
        task: TaskStar,
        target_device_id: Optional[str] = None,
    ) -> Any:
        """
        Execute a single task on a specific device.

        :param task: TaskStar to execute
        :param target_device_id: Optional target device ID
        :return: Task execution result
        """
        if target_device_id:
            task.target_device_id = target_device_id

        if not task.target_device_id:
            task.target_device_id = await self._auto_assign_device(task)

        # Execute task directly using TaskStar.execute
        result = await task.execute(self._device_manager)
        return result.result

    async def modify_constellation_with_llm(
        self,
        constellation: TaskConstellation,
        modification_request: str,
    ) -> TaskConstellation:
        """
        Modify an existing constellation using LLM.

        :param constellation: Existing TaskConstellation
        :param modification_request: LLM request for modifications
        :return: Modified TaskConstellation
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

        :param constellation: TaskConstellation to check
        :return: Status information
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
        }

    async def get_available_devices(self) -> List[Dict[str, Any]]:
        """
        Get list of available devices from device manager.

        :return: List of available device information
        """
        if not self._device_manager:
            return []

        try:
            # Get connected devices
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

    async def assign_devices_automatically(
        self,
        constellation: TaskConstellation,
        device_preferences: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Automatically assign devices to tasks based on capabilities and preferences.

        :param constellation: TaskConstellation to assign devices to
        :param device_preferences: Optional device preferences by task ID
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

        :param constellation: TaskConstellation to export
        :param format: Export format ("json", "yaml", "llm")
        :return: Exported string representation
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

        :param data: String data to import
        :param format: Import format ("json", "llm")
        :return: TaskConstellation instance
        """
        if format.lower() == "json":
            return TaskConstellation.from_json(data)
        elif format.lower() == "llm":
            return self._parser.parse_from_string(data)
        else:
            raise ValueError(f"Unsupported import format: {format}")

    async def _auto_assign_device(self, task: TaskStar) -> str:
        """
        Automatically assign a device to the task.

        :param task: TaskStar that needs device assignment
        :return: Device ID for the assigned device
        """
        if not self._device_manager:
            raise ValueError("Device manager not available for auto-assignment")

        # Get connected devices
        connected_devices = self._device_manager.get_connected_devices()
        if not connected_devices:
            raise ValueError("No connected devices available")

        # Simple strategy: choose the first available device
        # More complex strategies can be based on task requirements and device capabilities
        return connected_devices[0]

    async def _get_available_devices(self) -> Dict[str, Any]:
        """
        Get available devices as a map for the executor.

        :return: Dictionary mapping device IDs to device information
        """
        if not self._device_manager:
            return {}

        try:
            # Get connected devices
            connected_device_ids = self._device_manager.get_connected_devices()
            device_map = {}

            for device_id in connected_device_ids:
                device_info = self._device_manager.device_registry.get_device_info(
                    device_id
                )
                if device_info:
                    device_map[device_id] = {
                        "device_id": device_id,
                        "device_type": getattr(device_info, "device_type", "unknown"),
                        "capabilities": getattr(device_info, "capabilities", []),
                        "status": "connected",
                        "metadata": getattr(device_info, "metadata", {}),
                    }

            return device_map
        except Exception:
            return {}

    def _apply_device_assignments(
        self,
        constellation: TaskConstellation,
        assignments: Dict[str, str],
    ) -> None:
        """
        Apply manual device assignments to tasks.

        :param constellation: TaskConstellation containing the tasks
        :param assignments: Dictionary mapping task IDs to device IDs
        """
        for task_id, device_id in assignments.items():
            task = constellation.get_task(task_id)
            if task:
                task.target_device_id = device_id


# Convenience functions for easier usage
async def create_and_orchestrate_from_llm(
    llm_output: str,
    modular_client: Any,
    constellation_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to create and orchestrate a constellation from LLM output.

    :param llm_output: LLM output describing tasks
    :param modular_client: ConstellationClient instance
    :param constellation_name: Optional constellation name
    :return: Orchestration results
    """
    orchestrator = TaskOrchestration(modular_client)

    # Create constellation from LLM
    constellation = await orchestrator.create_constellation_from_llm(
        llm_output, constellation_name
    )

    # Assign devices automatically
    await orchestrator.assign_devices_automatically(constellation)

    # Orchestrate constellation
    return await orchestrator.orchestrate_constellation(constellation)


def create_simple_constellation(
    task_descriptions: List[str],
    constellation_name: str = "Simple Constellation",
    sequential: bool = True,
) -> TaskConstellation:
    """
    Create a simple constellation from a list of task descriptions.

    :param task_descriptions: List of task descriptions
    :param constellation_name: Name for the constellation
    :param sequential: Whether to make tasks sequential (True) or parallel (False)
    :return: TaskConstellation instance
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
