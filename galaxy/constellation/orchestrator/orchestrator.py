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
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from galaxy.client.device_manager import ConstellationDeviceManager

if TYPE_CHECKING:
    from ...session.observers.constellation_sync_observer import (
        ConstellationModificationSynchronizer,
    )

from ...core.events import ConstellationEvent, EventType, TaskEvent, get_event_bus
from ..enums import TaskStatus
from ..task_constellation import TaskConstellation
from ..task_star import TaskStar
from .constellation_manager import ConstellationManager


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

            self._event_bus = get_event_bus()
        else:
            self._event_bus = event_bus

        # Track active execution tasks
        self._execution_tasks: Dict[str, asyncio.Task] = {}

        # Cancellation support
        self._cancellation_requested = False
        self._cancelled_constellations: Dict[str, bool] = {}

        # Modification synchronizer (will be set by session)
        self._modification_synchronizer: Optional[
            "ConstellationModificationSynchronizer"
        ] = None

    def set_device_manager(self, device_manager: ConstellationDeviceManager) -> None:
        """
        Set the device manager for device communication.

        :param device_manager: The constellation device manager instance
        """
        self._device_manager = device_manager
        self._constellation_manager.set_device_manager(device_manager)

    def set_modification_synchronizer(
        self, synchronizer: "ConstellationModificationSynchronizer"
    ) -> None:
        """
        Set the modification synchronizer for coordination.

        :param synchronizer: ConstellationModificationSynchronizer instance
        """
        self._modification_synchronizer = synchronizer
        if self._logger:
            self._logger.info("Modification synchronizer attached to orchestrator")

    async def cancel_execution(self, constellation_id: str) -> bool:
        """
        Cancel constellation execution immediately.

        Cancels all running tasks and marks the constellation for cancellation.

        :param constellation_id: ID of the constellation to cancel
        :return: True if cancellation was successful
        """
        if self._logger:
            self._logger.info(
                f"🛑 Cancelling constellation execution: {constellation_id}"
            )

        # Mark this constellation as cancelled
        self._cancellation_requested = True
        self._cancelled_constellations[constellation_id] = True

        # Cancel all running execution tasks
        if self._execution_tasks:
            cancelled_count = 0
            for task_id, task in list(self._execution_tasks.items()):
                if not task.done():
                    if self._logger:
                        self._logger.debug(f"🛑 Cancelling task {task_id}")
                    task.cancel()
                    cancelled_count += 1

            if self._logger:
                self._logger.info(f"🛑 Cancelled {cancelled_count} running tasks")

            # Wait for all cancellations to complete
            await asyncio.gather(
                *self._execution_tasks.values(), return_exceptions=True
            )
            self._execution_tasks.clear()

        if self._logger:
            self._logger.info(
                f"✅ Constellation {constellation_id} cancellation completed"
            )

        return True

    async def orchestrate_constellation(
        self,
        constellation: TaskConstellation,
        device_assignments: Optional[Dict[str, str]] = None,
        assignment_strategy: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrate DAG execution using event-driven pattern.

        This is the main entry point that coordinates the entire orchestration workflow.

        :param constellation: TaskConstellation to orchestrate
        :param device_assignments: Optional manual device assignments
        :param assignment_strategy: Device assignment strategy for auto-assignment
        :param metadata: Optional metadata for orchestration
        :return: Orchestration results and statistics
        """
        # 1. Pre-execution validation and setup
        await self._validate_and_prepare_constellation(
            constellation, device_assignments, assignment_strategy
        )

        # 2. Start execution and publish event
        start_event = await self._start_constellation_execution(
            constellation, device_assignments, assignment_strategy, metadata
        )

        try:
            # 3. Main execution loop
            await self._run_execution_loop(constellation)

            # 4. Finalize and publish completion event
            return await self._finalize_constellation_execution(
                constellation, start_event
            )

        except ValueError as e:
            await self._handle_orchestration_failure(constellation, e)
            raise
        except RuntimeError as e:
            await self._handle_orchestration_failure(constellation, e)
            raise
        except asyncio.CancelledError:
            if self._logger:
                self._logger.info(
                    f"Orchestration cancelled for constellation {constellation.constellation_id}"
                )
            raise
        except Exception as e:
            await self._handle_orchestration_failure(constellation, e)
            raise

        finally:
            # Cancel all pending tasks before cleanup
            if self._execution_tasks:
                for task_id, task in list(self._execution_tasks.items()):
                    if not task.done():
                        task.cancel()

                # Wait for all cancellations to complete with proper exception handling
                if self._execution_tasks:
                    results = await asyncio.gather(
                        *self._execution_tasks.values(), return_exceptions=True
                    )
                    # Log any unexpected exceptions (non-CancelledError)
                    for i, result in enumerate(results):
                        if isinstance(result, Exception) and not isinstance(
                            result, asyncio.CancelledError
                        ):
                            if self._logger:
                                self._logger.warning(
                                    f"Task cleanup exception: {result}"
                                )

                self._execution_tasks.clear()

            await self._cleanup_constellation(constellation)

    # ========================================
    # Private helper methods (extracted from orchestrate_constellation)
    # ========================================

    async def _validate_and_prepare_constellation(
        self,
        constellation: TaskConstellation,
        device_assignments: Optional[Dict[str, str]],
        assignment_strategy: Optional[str] = None,
    ) -> None:
        """
        Validate DAG structure and prepare device assignments.

        :param constellation: TaskConstellation to validate
        :param device_assignments: Optional manual device assignments
        :param assignment_strategy: Device assignment strategy
        :raises ValueError: If validation fails
        """
        if not self._device_manager:
            raise ValueError(
                "ConstellationDeviceManager not set. Use set_device_manager() first."
            )

        if self._logger:
            self._logger.info(
                f"Starting orchestration of constellation {constellation.constellation_id}"
            )

        # Validate DAG structure
        is_valid, errors = constellation.validate_dag()
        if not is_valid:
            raise ValueError(f"Invalid DAG: {errors}")

        # Handle device assignments
        await self._assign_devices_to_tasks(
            constellation, device_assignments, assignment_strategy
        )

        # Validate assignments
        is_valid, errors = (
            self._constellation_manager.validate_constellation_assignments(
                constellation
            )
        )
        if not is_valid:
            raise ValueError(f"Device assignment validation failed: {errors}")

    async def _assign_devices_to_tasks(
        self,
        constellation: TaskConstellation,
        device_assignments: Optional[Dict[str, str]],
        assignment_strategy: Optional[str] = None,
    ) -> None:
        """
        Assign devices to tasks either manually or automatically.

        :param constellation: TaskConstellation to assign devices to
        :param device_assignments: Optional manual device assignments
        :param assignment_strategy: Device assignment strategy for auto-assignment
        :raises ValueError: If assignment_strategy is None and tasks have no target_device_id
        """
        if device_assignments:
            # Apply manual assignments
            for task_id, device_id in device_assignments.items():
                self._constellation_manager.reassign_task_device(
                    constellation, task_id, device_id
                )
        elif assignment_strategy:
            # Auto-assign devices
            await self._constellation_manager.assign_devices_automatically(
                constellation, assignment_strategy
            )
        else:
            # No assignment strategy provided, validate that all tasks have target_device_id
            self._validate_existing_device_assignments(constellation)

    def _validate_existing_device_assignments(
        self, constellation: TaskConstellation
    ) -> None:
        """
        Validate that all tasks in constellation have target_device_id assigned.

        This is called when no device_assignments or assignment_strategy is provided,
        ensuring that tasks already have device assignments.

        :param constellation: TaskConstellation to validate
        :raises ValueError: If any task is missing target_device_id or device_id is invalid
        """
        tasks_without_device = []
        tasks_with_invalid_device = []

        # Get all registered devices from device manager
        all_devices = self._device_manager.get_all_devices()
        valid_device_ids = set(all_devices.keys())

        for task_id, task in constellation.tasks.items():
            # Check if target_device_id is None or empty string
            if not task.target_device_id:
                tasks_without_device.append(task_id)
            else:
                # Check if the device_id exists in device manager
                if task.target_device_id not in valid_device_ids:
                    tasks_with_invalid_device.append(
                        f"{task_id} (assigned to unknown device: {task.target_device_id})"
                    )

        # Build error message if there are issues
        error_parts = []
        if tasks_without_device:
            error_parts.append(
                f"Tasks without device assignment: {tasks_without_device}"
            )
        if tasks_with_invalid_device:
            error_parts.append(
                f"Tasks with invalid device IDs: {tasks_with_invalid_device}"
            )

        if error_parts:
            error_msg = (
                f"Device assignment validation failed:\n"
                + "\n".join(f"  - {part}" for part in error_parts)
                + f"\n  Available devices: {list(valid_device_ids)}"
                + "\n  Please provide either 'device_assignments' or 'assignment_strategy' parameter."
            )
            if self._logger:
                self._logger.error(error_msg)
            raise ValueError(error_msg)

        if self._logger:
            self._logger.debug(
                f"All tasks have valid device assignments. "
                f"Total tasks validated: {len(constellation.tasks)}, "
                f"Available devices: {list(valid_device_ids)}"
            )

    async def _start_constellation_execution(
        self,
        constellation: TaskConstellation,
        device_assignments: Optional[Dict[str, str]],
        assignment_strategy: str,
        metadata: Optional[Dict] = None,
    ) -> ConstellationEvent:
        """
        Start constellation execution and publish started event.

        :param constellation: TaskConstellation to start
        :param device_assignments: Device assignments used
        :param assignment_strategy: Assignment strategy used
        :param metadata: Optional metadata for orchestration
        :return: The published constellation started event
        """
        constellation.start_execution()

        # Create and publish constellation started event
        start_event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_STARTED,
            source_id=f"orchestrator_{id(self)}",
            timestamp=time.time(),
            data={
                "total_tasks": len(constellation.tasks),
                "assignment_strategy": assignment_strategy,
                "device_assignments": device_assignments or {},
                "constellation": constellation,
                **(metadata or {}),  # Unpack metadata into data
            },
            constellation_id=constellation.constellation_id,
            constellation_state="executing",
        )
        await self._event_bus.publish_event(start_event)

        return start_event

    async def _run_execution_loop(self, constellation: TaskConstellation) -> None:
        """
        Main execution loop for processing constellation tasks.

        Continuously processes ready tasks until constellation is complete.
        Handles dynamic constellation modifications via synchronizer.

        :param constellation: TaskConstellation to execute
        """
        while not constellation.is_complete():
            # Check for cancellation at the beginning of each iteration
            if self._cancellation_requested or self._cancelled_constellations.get(
                constellation.constellation_id, False
            ):
                if self._logger:
                    self._logger.info(
                        f"🛑 Execution loop cancelled for constellation {constellation.constellation_id}"
                    )
                # Mark constellation as cancelled
                from ..enums import ConstellationState

                constellation.state = ConstellationState.CANCELLED
                break

            # Wait for pending modifications and refresh constellation
            constellation = await self._sync_constellation_modifications(constellation)

            # Validate existing device assignments
            self._validate_existing_device_assignments(constellation)

            # Get ready tasks and schedule them
            ready_tasks = constellation.get_ready_tasks()
            await self._schedule_ready_tasks(ready_tasks, constellation)

            # Wait for task completion
            await self._wait_for_task_completion()

        # Wait for all remaining tasks
        await self._wait_for_all_tasks()

    async def _sync_constellation_modifications(
        self, constellation: TaskConstellation
    ) -> TaskConstellation:
        """
        Synchronize pending constellation modifications.

        Merges structural changes from agent while preserving orchestrator's
        execution state (task statuses, results) to prevent race conditions.

        :param constellation: Current orchestrator's constellation
        :return: Updated constellation with merged state
        """
        if self._logger:
            old_ready = [t.task_id for t in constellation.get_ready_tasks()]
            self._logger.debug(f"⚠️ Old Ready tasks: {old_ready}")

        if self._modification_synchronizer:
            await self._modification_synchronizer.wait_for_pending_modifications()

            constellation = (
                self._modification_synchronizer.merge_and_sync_constellation_states(
                    orchestrator_constellation=constellation,
                )
            )

        if self._logger:
            self._logger.debug(
                f"🆕 Task ID for constellation after editing: {list(constellation.tasks.keys())}"
            )
            new_ready = [t.task_id for t in constellation.get_ready_tasks()]
            self._logger.debug(f"🆕 New Ready tasks: {new_ready}")

        return constellation

    async def _schedule_ready_tasks(
        self, ready_tasks: List[TaskStar], constellation: TaskConstellation
    ) -> None:
        """
        Schedule ready tasks for execution.

        :param ready_tasks: List of tasks ready to execute
        :param constellation: Parent constellation
        """
        for task in ready_tasks:
            if task.task_id not in self._execution_tasks:
                task_future = asyncio.create_task(
                    self._execute_task_with_events(task, constellation)
                )
                self._execution_tasks[task.task_id] = task_future

    async def _wait_for_task_completion(self) -> None:
        """
        Wait for at least one task to complete and clean up.
        """
        if self._execution_tasks:
            done, _ = await asyncio.wait(
                self._execution_tasks.values(), return_when=asyncio.FIRST_COMPLETED
            )

            # Clean up completed tasks
            await self._cleanup_completed_tasks(done)
        else:
            # No running tasks, wait briefly
            await asyncio.sleep(0.1)

    async def _cleanup_completed_tasks(self, done_futures: set) -> None:
        """
        Clean up completed task futures from tracking.

        :param done_futures: Set of completed task futures
        """
        completed_task_ids = []
        for task_future in done_futures:
            for task_id, future in self._execution_tasks.items():
                if future == task_future:
                    completed_task_ids.append(task_id)
                    break

        for task_id in completed_task_ids:
            del self._execution_tasks[task_id]

    async def _wait_for_all_tasks(self) -> None:
        """Wait for all remaining tasks to complete."""
        if self._execution_tasks:
            try:
                results = await asyncio.gather(
                    *self._execution_tasks.values(), return_exceptions=True
                )
                # Log any unexpected exceptions (non-CancelledError)
                for result in results:
                    if isinstance(result, Exception) and not isinstance(
                        result, asyncio.CancelledError
                    ):
                        if self._logger:
                            self._logger.warning(f"Task wait exception: {result}")
            except asyncio.CancelledError:
                # Gracefully handle cancellation during shutdown
                if self._logger:
                    self._logger.debug("Task gathering cancelled during shutdown")
                # Re-raise to propagate cancellation
                raise
            finally:
                self._execution_tasks.clear()

    async def _finalize_constellation_execution(
        self, constellation: TaskConstellation, start_event: ConstellationEvent
    ) -> Dict[str, Any]:
        """
        Finalize constellation execution and publish completion event.

        :param constellation: Completed constellation
        :param start_event: The original start event for timing
        :return: Orchestration results and statistics
        """
        constellation.complete_execution()

        # Publish constellation completed event
        completion_event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_COMPLETED,
            source_id=f"orchestrator_{id(self)}",
            timestamp=time.time(),
            data={
                "total_tasks": len(constellation.tasks),
                "statistics": constellation.get_statistics(),
                "execution_duration": time.time() - start_event.timestamp,
                "constellation": constellation,
            },
            constellation_id=constellation.constellation_id,
            constellation_state="completed",
        )
        await self._event_bus.publish_event(completion_event)

        if self._logger:
            self._logger.info(
                f"Completed orchestration of constellation {constellation.constellation_id}"
            )

        # Note: results is initialized as {} in original code
        results = {}
        return {
            "results": results,
            "status": "completed",
            "total_tasks": len(results),
            "statistics": constellation.get_statistics(),
        }

    async def _handle_orchestration_failure(
        self, constellation: TaskConstellation, error: Exception
    ) -> None:
        """
        Handle orchestration failure.

        :param constellation: Failed constellation
        :param error: The exception that caused the failure
        """
        constellation.complete_execution()
        if self._logger:
            self._logger.error(f"Orchestration failed: {error}")

    async def _cleanup_constellation(self, constellation: TaskConstellation) -> None:
        """
        Clean up constellation resources.

        :param constellation: Constellation to clean up
        """
        self._constellation_manager.unregister_constellation(
            constellation.constellation_id
        )

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

            task.start_execution()

            # Execute the task
            result = await task.execute(self._device_manager)

            is_success = result.status == TaskStatus.COMPLETED.value

            self._logger.info(
                f"Task {task.task_id} execution result: {result}, is_success: {is_success}"
            )

            # Mark task as completed in constellation
            newly_ready = constellation.mark_task_completed(
                task.task_id, success=is_success, result=result
            )

            # Publish task completed event
            completed_event = TaskEvent(
                event_type=(
                    EventType.TASK_COMPLETED if is_success else EventType.TASK_FAILED
                ),
                source_id=f"orchestrator_{id(self)}",
                timestamp=time.time(),
                data={
                    "constellation_id": constellation.constellation_id,
                    "newly_ready_tasks": [t.task_id for t in newly_ready],
                    "constellation": constellation,
                },
                task_id=task.task_id,
                status=result.status,
                result=result,
            )
            await self._event_bus.publish_event(completed_event)

            self._logger.debug(
                f"Task {task.task_id} is marked as completed. Completed tasks ids: {[t.task_id for t in constellation.get_completed_tasks()]}"
            )

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
