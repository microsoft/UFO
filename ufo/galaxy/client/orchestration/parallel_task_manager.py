# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Parallel Task Manager

Handles parallel execution of multiple tasks with concurrency control.
Single responsibility: Multi-task parallel coordination.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any

from .task_orchestrator import TaskOrchestrator
from .device_selector import DeviceSelector


class ParallelTaskManager:
    """
    Manages parallel execution of multiple tasks.
    Single responsibility: Parallel task coordination.
    """

    def __init__(
        self,
        task_orchestrator: TaskOrchestrator,
        device_selector: DeviceSelector,
        max_concurrent_tasks: int = 10,
    ):
        """
        Initialize the parallel task manager.

        :param task_orchestrator: Task orchestrator for individual tasks
        :param device_selector: Device selector for task routing
        :param max_concurrent_tasks: Maximum concurrent tasks
        """
        self.task_orchestrator = task_orchestrator
        self.device_selector = device_selector
        self.max_concurrent_tasks = max_concurrent_tasks
        self.logger = logging.getLogger(f"{__name__}.ParallelTaskManager")

    async def execute_tasks_parallel(
        self,
        tasks: List[Dict[str, Any]],
        max_concurrent: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute multiple tasks in parallel across devices.

        :param tasks: List of task dictionaries with keys: request, device_id (optional), etc.
        :param max_concurrent: Maximum concurrent tasks (uses instance default if None)
        :return: Dictionary mapping task IDs to results
        """
        if max_concurrent is None:
            max_concurrent = self.max_concurrent_tasks

        self.logger.info(
            f"🚀 Starting parallel execution of {len(tasks)} tasks with max_concurrent={max_concurrent}"
        )

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single_task(task_config: Dict[str, Any]) -> tuple:
            """Execute a single task with semaphore control"""
            async with semaphore:
                task_id = f"parallel_task_{len(results)}_{uuid.uuid4().hex[:8]}"
                try:
                    # Auto-select device if not specified
                    device_id = task_config.get("device_id")
                    if not device_id:
                        capabilities_required = task_config.get("capabilities_required")
                        device_id = await self.device_selector.select_best_device(
                            capabilities_required
                        )
                        if not device_id:
                            raise ValueError(
                                "No suitable device available for task execution"
                            )

                    # Execute task via orchestrator
                    result = await self.task_orchestrator.execute_task(
                        request=task_config["request"],
                        device_id=device_id,
                        target_client_id=task_config.get("target_client_id"),
                        task_name=task_config.get("task_name"),
                        metadata=task_config.get("metadata"),
                        timeout=task_config.get("timeout", 300.0),
                        callback=task_config.get("callback"),
                    )

                    return task_id, {"success": True, "result": result}

                except Exception as e:
                    self.logger.error(f"❌ Parallel task {task_id} failed: {e}")
                    return task_id, {"success": False, "error": str(e)}

        # Execute tasks concurrently
        results = {}
        task_futures = [execute_single_task(task) for task in tasks]

        completed_tasks = await asyncio.gather(*task_futures, return_exceptions=True)

        for task_result in completed_tasks:
            if isinstance(task_result, tuple):
                task_id, result = task_result
                results[task_id] = result
            else:
                # Handle exceptions
                error_task_id = f"error_task_{len(results)}"
                results[error_task_id] = {"success": False, "error": str(task_result)}

        self.logger.info(
            f"✅ Parallel execution completed. {len(results)} tasks processed"
        )
        return results

    async def execute_tasks_with_dependencies(
        self,
        task_dag: Dict[str, Dict[str, Any]],
        max_concurrent: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute tasks with dependency resolution (DAG execution).

        :param task_dag: Dictionary with task_id -> {task_config, dependencies: [task_ids]}
        :param max_concurrent: Maximum concurrent tasks
        :return: Dictionary mapping task IDs to results
        """
        if max_concurrent is None:
            max_concurrent = self.max_concurrent_tasks

        self.logger.info(f"🏗️ Starting DAG execution with {len(task_dag)} tasks")

        # Track completion status
        completed = {}
        results = {}
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_task_when_ready(
            task_id: str, task_config: Dict[str, Any]
        ) -> None:
            """Execute task when all dependencies are satisfied"""
            dependencies = task_config.get("dependencies", [])

            # Wait for all dependencies to complete
            while dependencies:
                await asyncio.sleep(0.1)  # Short polling interval
                dependencies = [dep for dep in dependencies if dep not in completed]

            # Execute task with semaphore control
            async with semaphore:
                try:
                    # Auto-select device if not specified
                    device_id = task_config.get("device_id")
                    if not device_id:
                        capabilities_required = task_config.get("capabilities_required")
                        device_id = await self.device_selector.select_best_device(
                            capabilities_required
                        )
                        if not device_id:
                            raise ValueError(
                                "No suitable device available for task execution"
                            )

                    # Execute task
                    result = await self.task_orchestrator.execute_task(
                        request=task_config["request"],
                        device_id=device_id,
                        target_client_id=task_config.get("target_client_id"),
                        task_name=task_config.get("task_name"),
                        metadata=task_config.get("metadata"),
                        timeout=task_config.get("timeout", 300.0),
                    )

                    results[task_id] = {"success": True, "result": result}

                except Exception as e:
                    self.logger.error(f"❌ DAG task {task_id} failed: {e}")
                    results[task_id] = {"success": False, "error": str(e)}

                finally:
                    completed[task_id] = True

        # Start all tasks (they will wait for dependencies internally)
        task_futures = [
            asyncio.create_task(execute_task_when_ready(task_id, task_config))
            for task_id, task_config in task_dag.items()
        ]

        # Wait for all tasks to complete
        await asyncio.gather(*task_futures, return_exceptions=True)

        self.logger.info(f"✅ DAG execution completed. {len(results)} tasks processed")
        return results
