# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
ConstellationExecutor - Execution engine for TaskConstellation.

This module provides the execution engine that accepts TaskConstellation objects,
analyzes the DAG structure, and coordinates async task execution across devices.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Callable, Awaitable

from .enums import TaskStatus, ConstellationState
from .task_star import TaskStar
from .task_constellation import TaskConstellation


class ConstellationExecutor:
    """
    Executes TaskConstellation objects by coordinating task execution across devices.

    Provides:
    - Async task execution coordination
    - Device assignment and load balancing
    - Result collection and dependency resolution
    - Error handling and retry logic
    """

    def __init__(
        self,
        client_interface: Optional[Callable[[TaskStar], Awaitable[Any]]] = None,
        max_concurrent_tasks: int = 10,
        enable_logging: bool = True,
    ):
        """
        Initialize the ConstellationExecutor.

        Args:
            client_interface: Async function to execute tasks on devices
            max_concurrent_tasks: Maximum number of concurrent tasks
            enable_logging: Whether to enable detailed logging
        """
        self._client_interface = client_interface
        self._max_concurrent_tasks = max_concurrent_tasks
        self._enable_logging = enable_logging

        # Execution state
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._device_assignments: Dict[str, str] = {}  # task_id -> device_id
        self._execution_semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # Logging
        self._logger = logging.getLogger(__name__) if enable_logging else None

        # Statistics
        self._stats = {
            "tasks_executed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
        }

    @property
    def stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return self._stats.copy()

    def set_client_interface(
        self, client_interface: Callable[[TaskStar], Awaitable[Any]]
    ) -> None:
        """
        Set the client interface for task execution.

        Args:
            client_interface: Async function to execute tasks
        """
        self._client_interface = client_interface

    async def execute_constellation(
        self,
        constellation: TaskConstellation,
        device_client_map: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str, TaskStatus, Any], None]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a complete TaskConstellation.

        Args:
            constellation: TaskConstellation to execute
            device_client_map: Map of device_id -> client_instance
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with execution results and statistics
        """
        if not self._client_interface:
            raise ValueError(
                "Client interface not set. Use set_client_interface() first."
            )

        if self._logger:
            self._logger.info(
                f"Starting execution of constellation {constellation.constellation_id}"
            )

        # Validate the constellation
        is_valid, errors = constellation.validate_dag()
        if not is_valid:
            raise ValueError(f"Invalid constellation DAG: {errors}")

        # Start execution
        constellation.start_execution()

        try:
            results = await self._execute_dag(
                constellation, device_client_map, progress_callback
            )
            constellation.complete_execution()

            if self._logger:
                self._logger.info(
                    f"Completed execution of constellation {constellation.constellation_id}"
                )

            return {
                "constellation_id": constellation.constellation_id,
                "status": "completed",
                "results": results,
                "statistics": constellation.get_statistics(),
                "execution_stats": self._stats.copy(),
            }

        except Exception as e:
            constellation.complete_execution()

            if self._logger:
                self._logger.error(
                    f"Failed to execute constellation {constellation.constellation_id}: {e}"
                )

            return {
                "constellation_id": constellation.constellation_id,
                "status": "failed",
                "error": str(e),
                "statistics": constellation.get_statistics(),
                "execution_stats": self._stats.copy(),
            }

    async def _execute_dag(
        self,
        constellation: TaskConstellation,
        device_client_map: Optional[Dict[str, Any]],
        progress_callback: Optional[Callable[[str, TaskStatus, Any], None]],
    ) -> Dict[str, Any]:
        """Execute the DAG by coordinating task execution."""
        results = {}

        while not constellation.is_complete():
            # Get ready tasks
            ready_tasks = constellation.get_ready_tasks()

            if not ready_tasks and not self._running_tasks:
                # No ready tasks and nothing running - check for deadlock
                pending_tasks = constellation.get_pending_tasks()
                if pending_tasks:
                    raise RuntimeError(
                        "Execution deadlock detected: pending tasks with unsatisfied dependencies"
                    )
                break

            # Start execution of ready tasks
            for task in ready_tasks:
                if len(self._running_tasks) >= self._max_concurrent_tasks:
                    break

                # Assign device if needed
                if not task.target_device_id:
                    task.target_device_id = self._assign_device(task, device_client_map)

                # Start task execution
                asyncio_task = asyncio.create_task(
                    self._execute_task(task, constellation, progress_callback)
                )
                self._running_tasks[task.task_id] = asyncio_task

                if self._logger:
                    self._logger.info(f"Started execution of task {task.task_id}")

            # Wait for at least one task to complete
            if self._running_tasks:
                done, pending = await asyncio.wait(
                    self._running_tasks.values(), return_when=asyncio.FIRST_COMPLETED
                )

                # Process completed tasks
                for completed_task in done:
                    task_id = None
                    for tid, t in self._running_tasks.items():
                        if t == completed_task:
                            task_id = tid
                            break

                    if task_id:
                        del self._running_tasks[task_id]

                        try:
                            result = await completed_task
                            results[task_id] = result
                        except Exception as e:
                            results[task_id] = {"error": str(e)}

            # Small delay to prevent tight loop
            await asyncio.sleep(0.1)

        # Wait for any remaining tasks
        if self._running_tasks:
            await asyncio.gather(*self._running_tasks.values(), return_exceptions=True)

        return results

    async def _execute_task(
        self,
        task: TaskStar,
        constellation: TaskConstellation,
        progress_callback: Optional[Callable[[str, TaskStatus, Any], None]],
    ) -> Any:
        """Execute a single task."""
        async with self._execution_semaphore:
            start_time = datetime.now(timezone.utc)

            try:
                # Mark task as started
                task.start_execution()

                if progress_callback:
                    progress_callback(task.task_id, TaskStatus.RUNNING, None)

                # Execute the task using client interface
                result = await self._client_interface(task)

                # Mark task as completed
                task.complete_with_success(result)
                newly_ready = constellation.mark_task_completed(
                    task.task_id, True, result
                )

                # Update statistics
                execution_time = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds()
                self._stats["tasks_executed"] += 1
                self._stats["total_execution_time"] += execution_time

                if progress_callback:
                    progress_callback(task.task_id, TaskStatus.COMPLETED, result)

                if self._logger:
                    self._logger.info(
                        f"Task {task.task_id} completed successfully in {execution_time:.2f}s"
                    )

                return result

            except Exception as e:
                # Mark task as failed
                task.complete_with_failure(e)
                constellation.mark_task_completed(task.task_id, False, error=e)

                # Update statistics
                self._stats["tasks_failed"] += 1

                if progress_callback:
                    progress_callback(task.task_id, TaskStatus.FAILED, e)

                if self._logger:
                    self._logger.error(f"Task {task.task_id} failed: {e}")

                # Check if task should be retried
                if task.should_retry():
                    if self._logger:
                        self._logger.info(
                            f"Retrying task {task.task_id} (attempt {task._current_retry + 1})"
                        )

                    task.retry()
                    # Re-add to constellation for retry
                    return await self._execute_task(
                        task, constellation, progress_callback
                    )

                raise e

    def _assign_device(
        self,
        task: TaskStar,
        device_client_map: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """
        Assign a device to a task based on device type and availability.

        Args:
            task: TaskStar to assign device to
            device_client_map: Available devices

        Returns:
            Device ID or None if no suitable device found
        """
        if not device_client_map:
            return None

        # Simple assignment based on device type
        if task.device_type:
            for device_id, client in device_client_map.items():
                # This is a simplified assignment - in practice, you'd check
                # device capabilities, load, etc.
                if (
                    hasattr(client, "device_type")
                    and client.device_type == task.device_type
                ):
                    return device_id

        # Fall back to first available device
        return next(iter(device_client_map.keys())) if device_client_map else None

    async def execute_single_task(
        self,
        task: TaskStar,
        device_client: Optional[Any] = None,
    ) -> Any:
        """
        Execute a single task without DAG coordination.

        Args:
            task: TaskStar to execute
            device_client: Optional specific device client

        Returns:
            Task execution result
        """
        if not self._client_interface:
            raise ValueError("Client interface not set")

        if self._logger:
            self._logger.info(f"Executing single task {task.task_id}")

        try:
            task.start_execution()
            result = await self._client_interface(task)
            task.complete_with_success(result)

            if self._logger:
                self._logger.info(f"Single task {task.task_id} completed successfully")

            return result

        except Exception as e:
            task.complete_with_failure(e)

            if self._logger:
                self._logger.error(f"Single task {task.task_id} failed: {e}")

            raise e

    def get_running_task_count(self) -> int:
        """Get the number of currently running tasks."""
        return len(self._running_tasks)

    def cancel_all_tasks(self) -> None:
        """Cancel all running tasks."""
        for task in self._running_tasks.values():
            task.cancel()
        self._running_tasks.clear()

    async def wait_for_completion(self) -> None:
        """Wait for all running tasks to complete."""
        if self._running_tasks:
            await asyncio.gather(*self._running_tasks.values(), return_exceptions=True)
            self._running_tasks.clear()

    def reset_stats(self) -> None:
        """Reset execution statistics."""
        self._stats = {
            "tasks_executed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
        }
