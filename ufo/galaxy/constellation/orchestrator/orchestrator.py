# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task Execution Orchestrator for TaskConstellation.

This module provides the execution orchestrator for TaskConstellation,
focused purely on execution flow control and coordination.
Delegates device/state management to ConstellationManager.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from ufo.galaxy.client.device_manager import ConstellationDeviceManager

from ...core.events import (
    ConstellationEvent,
    Event,
    EventType,
    TaskEvent,
    get_event_bus,
)
from ...core.types import ProcessingContext
from .constellation_manager import ConstellationManager
from ..enums import DeviceType, TaskStatus
from ..task_constellation import TaskConstellation
from ..task_star import TaskStar


class TaskConstellationOrchestrator:
    """
    Task execution orchestrator focused on flow control and coordination.

    This class provides execution orchestration for TaskConstellation using
    event-driven patterns. It delegates device/state management to
    ConstellationManager.
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
        is_valid, errors = constellation.validate_dag()

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

        # Publish constellation started event
        constellation_started_event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_STARTED,
            source_id=f"orchestrator_{id(self)}",
            timestamp=time.time(),
            data={
                "total_tasks": len(constellation.tasks),
                "assignment_strategy": assignment_strategy,
                "device_assignments": device_assignments or {},
            },
            constellation_id=constellation_id,
            constellation_state="executing",
        )
        await self._event_bus.publish_event(constellation_started_event)

        try:
            # Main execution loop - continue until all tasks complete
            while not constellation.is_complete():
                ready_tasks = constellation.get_ready_tasks()

                # Create execution tasks for ready tasks in parallel
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

            # Publish constellation completed event
            constellation_completed_event = ConstellationEvent(
                event_type=EventType.CONSTELLATION_COMPLETED,
                source_id=f"orchestrator_{id(self)}",
                timestamp=time.time(),
                data={
                    "total_tasks": len(constellation.tasks),
                    "statistics": constellation.get_statistics(),
                    "execution_duration": time.time()
                    - constellation_started_event.timestamp,
                },
                constellation_id=constellation_id,
                constellation_state="completed",
            )
            await self._event_bus.publish_event(constellation_completed_event)

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
