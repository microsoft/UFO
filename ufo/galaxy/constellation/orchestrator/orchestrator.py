# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task Execution Orchestrator for TaskConstellation V2.

This module provides the execution orchestrator for TaskConstellation,
focused purely on execution flow control and coordination.
Delegates constellation creation/parsing to ConstellationParser and
device/state management to ConstellationManager.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from ufo.galaxy.client.device_manager import ConstellationDeviceManager

from ...core.events import EventBus, EventType, TaskEvent, get_event_bus
from ...core.types import ProcessingContext
from .constellation_manager import ConstellationManager
from ..parsers.constellation_parser import ConstellationParser
from ..enums import DeviceType, TaskStatus
from ..task_constellation import TaskConstellation
from ..task_star import TaskStar


class TaskConstellationOrchestrator:
    """
    Task execution orchestrator focused on flow control and coordination.

    This class provides execution orchestration for TaskConstellation using
    event-driven patterns. It delegates constellation creation/parsing to
    ConstellationParser and device/state management to ConstellationManager.
    """

    def __init__(
        self,
        device_manager: Optional[ConstellationDeviceManager] = None,
        enable_logging: bool = True,
        event_bus=None,
    ):
        """
        Initialize the TaskConstellationOrchestrator.

        :param device_manager: Instance of ConstellationDeviceManager
        :param enable_logging: Whether to enable logging
        :param event_bus: Event bus for publishing events
        """
        self._device_manager = device_manager
        self._constellation_parser = ConstellationParser(enable_logging)
        self._constellation_manager = ConstellationManager(
            device_manager, enable_logging
        )
        self._logger = logging.getLogger(__name__) if enable_logging else None

        # Initialize event bus for publishing events
        if event_bus is None:
            from ...core.events import get_event_bus

            self._event_bus = get_event_bus()
        else:
            self._event_bus = event_bus

        # Track active execution tasks
        self._execution_tasks: Dict[str, asyncio.Task] = {}

    def set_device_manager(self, device_manager: ConstellationDeviceManager) -> None:
        """
        Set the device manager for device communication.

        :param device_manager: The constellation device manager instance
        """
        self._device_manager = device_manager
        self._constellation_manager.set_device_manager(device_manager)

    async def create_constellation_from_llm(
        self,
        llm_output: str,
        constellation_name: Optional[str] = None,
    ) -> TaskConstellation:
        """
        Create a TaskConstellation from LLM output using ConstellationParser.

        :param llm_output: Raw LLM output describing tasks and dependencies
        :param constellation_name: Optional name for the constellation
        :return: TaskConstellation instance
        """
        if self._logger:
            self._logger.info(
                f"Creating constellation from LLM output: {constellation_name}"
            )

        constellation = await self._constellation_parser.create_from_llm(
            llm_output, constellation_name
        )

        # Register with constellation manager
        self._constellation_manager.register_constellation(constellation)

        if self._logger:
            self._logger.info(
                f"Created constellation with {constellation.task_count} tasks "
                f"and {constellation.dependency_count} dependencies"
            )

        return constellation

    async def create_constellation_from_json(
        self,
        json_data: str,
        constellation_name: Optional[str] = None,
    ) -> TaskConstellation:
        """
        Create a TaskConstellation from JSON data using ConstellationParser.

        :param json_data: JSON string representing constellation
        :param constellation_name: Optional name for the constellation
        :return: TaskConstellation instance
        """
        constellation = self._constellation_parser.create_from_json(
            json_data, constellation_name
        )

        # Register with constellation manager
        self._constellation_manager.register_constellation(constellation)

        return constellation

    async def create_simple_constellation(
        self,
        task_descriptions: List[str],
        constellation_name: str = "Simple Constellation",
        sequential: bool = True,
    ) -> TaskConstellation:
        """
        Create a simple constellation using ConstellationParser.

        :param task_descriptions: List of task descriptions
        :param constellation_name: Name for the constellation
        :param sequential: Whether to make tasks sequential (True) or parallel (False)
        :return: TaskConstellation instance
        """
        if sequential:
            constellation = self._constellation_parser.create_simple_sequential(
                task_descriptions, constellation_name
            )
        else:
            constellation = self._constellation_parser.create_simple_parallel(
                task_descriptions, constellation_name
            )

        # Register with constellation manager
        self._constellation_manager.register_constellation(constellation)

        return constellation

    async def orchestrate_constellation(
        self,
        constellation: TaskConstellation,
        device_assignments: Optional[Dict[str, str]] = None,
        assignment_strategy: str = "round_robin",
    ) -> Dict[str, Any]:
        """
        Orchestrate DAG execution using event-driven pattern.

        :param constellation: TaskConstellation to orchestrate
        :param device_assignments: Optional manual device assignments
        :param assignment_strategy: Device assignment strategy for auto-assignment
        :return: Orchestration results and statistics
        """
        if not self._device_manager:
            raise ValueError(
                "ConstellationDeviceManager not set. Use set_device_manager() first."
            )

        constellation_id = constellation.constellation_id

        if self._logger:
            self._logger.info(
                f"Starting orchestration of constellation {constellation_id}"
            )

        # Validate DAG structure using constellation parser
        is_valid, errors = self._constellation_parser.validate_constellation(
            constellation
        )
        if not is_valid:
            raise ValueError(f"Invalid DAG: {errors}")

        # Handle device assignments
        if device_assignments:
            # Apply manual assignments
            for task_id, device_id in device_assignments.items():
                self._constellation_manager.reassign_task_device(
                    constellation, task_id, device_id
                )
        else:
            # Auto-assign devices using constellation manager
            await self._constellation_manager.assign_devices_automatically(
                constellation, assignment_strategy
            )

        # Validate all tasks have device assignments
        is_valid, errors = (
            self._constellation_manager.validate_constellation_assignments(
                constellation
            )
        )
        if not is_valid:
            raise ValueError(f"Device assignment validation failed: {errors}")

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
                "statistics": constellation.get_statistics(),
            }

        except Exception as e:
            constellation.complete_execution()
            if self._logger:
                self._logger.error(f"Orchestration failed: {e}")
            raise

        finally:
            # Unregister constellation from manager
            self._constellation_manager.unregister_constellation(constellation_id)

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
            # Use constellation manager to auto-assign device
            available_devices = (
                await self._constellation_manager.get_available_devices()
            )
            if not available_devices:
                raise ValueError("No available devices for task execution")
            task.target_device_id = available_devices[0]["device_id"]

        # Execute task directly using TaskStar.execute
        result = await task.execute(self._device_manager)
        return result.result

    async def modify_constellation_with_llm(
        self,
        constellation: TaskConstellation,
        modification_request: str,
    ) -> TaskConstellation:
        """
        Modify an existing constellation using LLM via ConstellationParser.

        :param constellation: Existing TaskConstellation
        :param modification_request: LLM request for modifications
        :return: Modified TaskConstellation
        """
        return self._constellation_parser.update_from_llm(
            constellation, modification_request
        )

    async def get_constellation_status(
        self, constellation: TaskConstellation
    ) -> Dict[str, Any]:
        """
        Get detailed status of a constellation using ConstellationManager.

        :param constellation: TaskConstellation to check
        :return: Status information
        """
        return await self._constellation_manager.get_constellation_status(
            constellation.constellation_id
        )

    async def get_available_devices(self) -> List[Dict[str, Any]]:
        """
        Get list of available devices from ConstellationManager.

        :return: List of available device information
        """
        return await self._constellation_manager.get_available_devices()

    async def assign_devices_automatically(
        self,
        constellation: TaskConstellation,
        strategy: str = "round_robin",
        device_preferences: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Automatically assign devices to tasks using ConstellationManager.

        :param constellation: TaskConstellation to assign devices to
        :param strategy: Assignment strategy
        :param device_preferences: Optional device preferences by task ID
        :return: Dictionary mapping task IDs to assigned device IDs
        """
        return await self._constellation_manager.assign_devices_automatically(
            constellation, strategy, device_preferences
        )

    def export_constellation(
        self,
        constellation: TaskConstellation,
        format: str = "json",
    ) -> str:
        """
        Export constellation using ConstellationParser.

        :param constellation: TaskConstellation to export
        :param format: Export format ("json", "yaml", "llm")
        :return: Exported string representation
        """
        return self._constellation_parser.export_constellation(constellation, format)

    async def import_constellation(
        self,
        data: str,
        format: str = "json",
    ) -> TaskConstellation:
        """
        Import constellation using ConstellationParser.

        :param data: String data to import
        :param format: Import format ("json", "llm")
        :return: TaskConstellation instance
        """
        if format.lower() == "json":
            return self._constellation_parser.create_from_json(data)
        elif format.lower() == "llm":
            return await self._constellation_parser.create_from_llm(data)
        else:
            raise ValueError(f"Unsupported import format: {format}")

    def add_task_to_constellation(
        self,
        constellation: TaskConstellation,
        task: TaskStar,
        dependencies: Optional[List[str]] = None,
    ) -> bool:
        """
        Add a task to constellation using ConstellationParser.

        :param constellation: Target constellation
        :param task: TaskStar to add
        :param dependencies: Optional list of task IDs that this task depends on
        :return: True if added successfully
        """
        return self._constellation_parser.add_task_to_constellation(
            constellation, task, dependencies
        )

    def remove_task_from_constellation(
        self,
        constellation: TaskConstellation,
        task_id: str,
    ) -> bool:
        """
        Remove a task from constellation using ConstellationParser.

        :param constellation: Target constellation
        :param task_id: ID of task to remove
        :return: True if removed successfully
        """
        return self._constellation_parser.remove_task_from_constellation(
            constellation, task_id
        )

    def clone_constellation(
        self,
        constellation: TaskConstellation,
        new_name: Optional[str] = None,
    ) -> TaskConstellation:
        """
        Clone a constellation using ConstellationParser.

        :param constellation: Constellation to clone
        :param new_name: Optional new name for the cloned constellation
        :return: Cloned TaskConstellation
        """
        cloned = self._constellation_parser.clone_constellation(constellation, new_name)

        # Register cloned constellation with manager
        self._constellation_manager.register_constellation(cloned)

        return cloned

    def merge_constellations(
        self,
        constellation1: TaskConstellation,
        constellation2: TaskConstellation,
        merged_name: Optional[str] = None,
    ) -> TaskConstellation:
        """
        Merge two constellations using ConstellationParser.

        :param constellation1: First constellation
        :param constellation2: Second constellation
        :param merged_name: Optional name for merged constellation
        :return: Merged TaskConstellation
        """
        return self._constellation_parser.merge_constellations(
            constellation1, constellation2, merged_name
        )


# Convenience functions for easier usage
async def create_and_orchestrate_from_llm(
    llm_output: str,
    device_manager: ConstellationDeviceManager,
    constellation_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to create and orchestrate a constellation from LLM output.

    :param llm_output: LLM output describing tasks
    :param device_manager: ConstellationDeviceManager instance
    :param constellation_name: Optional constellation name
    :return: Orchestration results
    """
    orchestrator = TaskConstellationOrchestrator(device_manager)

    # Create constellation from LLM
    constellation = await orchestrator.create_constellation_from_llm(
        llm_output, constellation_name
    )

    # Assign devices automatically
    await orchestrator.assign_devices_automatically(constellation)

    # Orchestrate constellation
    return await orchestrator.orchestrate_constellation(constellation)


def create_simple_constellation_standalone(
    task_descriptions: List[str],
    constellation_name: str = "Simple Constellation",
    sequential: bool = True,
) -> TaskConstellation:
    """
    Create a simple constellation from a list of task descriptions without orchestrator.

    :param task_descriptions: List of task descriptions
    :param constellation_name: Name for the constellation
    :param sequential: Whether to make tasks sequential (True) or parallel (False)
    :return: TaskConstellation instance
    """
    from ..task_star_line import TaskStarLine

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
