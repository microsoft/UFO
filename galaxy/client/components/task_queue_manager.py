# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task Queue Manager

Manages task queuing and scheduling for devices.
Ensures tasks are queued when devices are busy.
"""

import asyncio
import logging
from collections import deque
from typing import Dict, List, Optional

from .types import TaskRequest


class TaskQueueManager:
    """
    Manages task queuing and scheduling for devices.
    Single responsibility: Task queue management and scheduling.
    """

    def __init__(self):
        # Task queues per device
        self._task_queues: Dict[str, deque[TaskRequest]] = {}

        # Pending task futures for awaiting results
        self._pending_tasks: Dict[str, Dict[str, asyncio.Future]] = {}

        self.logger = logging.getLogger(f"{__name__}.TaskQueueManager")

    def enqueue_task(self, device_id: str, task_request: TaskRequest) -> asyncio.Future:
        """
        Enqueue a task for a device.

        :param device_id: Target device ID
        :param task_request: Task to enqueue
        :return: Future that will contain the task result
        """
        # Initialize queue if needed
        if device_id not in self._task_queues:
            self._task_queues[device_id] = deque()

        # Initialize pending tasks dict if needed
        if device_id not in self._pending_tasks:
            self._pending_tasks[device_id] = {}

        # Create future for this task
        future = asyncio.Future()
        self._pending_tasks[device_id][task_request.task_id] = future

        # Add task to queue
        self._task_queues[device_id].append(task_request)

        queue_size = len(self._task_queues[device_id])
        self.logger.info(
            f"📥 Task {task_request.task_id} enqueued for device {device_id} "
            f"(Queue size: {queue_size})"
        )

        return future

    def dequeue_task(self, device_id: str) -> Optional[TaskRequest]:
        """
        Dequeue the next task for a device.

        :param device_id: Device ID
        :return: Next task or None if queue is empty
        """
        if device_id not in self._task_queues or not self._task_queues[device_id]:
            return None

        task = self._task_queues[device_id].popleft()
        self.logger.info(
            f"📤 Task {task.task_id} dequeued for device {device_id} "
            f"(Remaining: {len(self._task_queues[device_id])})"
        )
        return task

    def peek_next_task(self, device_id: str) -> Optional[TaskRequest]:
        """
        Peek at the next task without removing it.

        :param device_id: Device ID
        :return: Next task or None if queue is empty
        """
        if device_id not in self._task_queues or not self._task_queues[device_id]:
            return None
        return self._task_queues[device_id][0]

    def get_queue_size(self, device_id: str) -> int:
        """Get the number of queued tasks for a device"""
        if device_id not in self._task_queues:
            return 0
        return len(self._task_queues[device_id])

    def has_queued_tasks(self, device_id: str) -> bool:
        """Check if device has queued tasks"""
        return self.get_queue_size(device_id) > 0

    def complete_task(self, device_id: str, task_id: str, result: any) -> None:
        """
        Mark a task as completed and set its result.

        :param device_id: Device ID
        :param task_id: Task ID
        :param result: Task execution result
        """
        if (
            device_id in self._pending_tasks
            and task_id in self._pending_tasks[device_id]
        ):
            future = self._pending_tasks[device_id][task_id]
            if not future.done():
                future.set_result(result)
            del self._pending_tasks[device_id][task_id]
            self.logger.info(f"✅ Task {task_id} completed on device {device_id}")

    def fail_task(self, device_id: str, task_id: str, exception: Exception) -> None:
        """
        Mark a task as failed.

        :param device_id: Device ID
        :param task_id: Task ID
        :param exception: Exception that caused the failure
        """
        if (
            device_id in self._pending_tasks
            and task_id in self._pending_tasks[device_id]
        ):
            future = self._pending_tasks[device_id][task_id]
            if not future.done():
                future.set_exception(exception)
            del self._pending_tasks[device_id][task_id]
            self.logger.error(
                f"❌ Task {task_id} failed on device {device_id}: {exception}"
            )

    def cancel_all_tasks(self, device_id: str) -> None:
        """
        Cancel all pending tasks for a device.

        :param device_id: Device ID
        """
        # Cancel all queued tasks
        if device_id in self._task_queues:
            queue_size = len(self._task_queues[device_id])
            self._task_queues[device_id].clear()
            self.logger.info(
                f"🗑️  Cancelled {queue_size} queued tasks for device {device_id}"
            )

        # Cancel all pending futures
        if device_id in self._pending_tasks:
            for task_id, future in self._pending_tasks[device_id].items():
                if not future.done():
                    future.cancel()
            self._pending_tasks[device_id].clear()

    def get_pending_task_ids(self, device_id: str) -> List[str]:
        """Get list of pending task IDs for a device"""
        if device_id not in self._pending_tasks:
            return []
        return list(self._pending_tasks[device_id].keys())

    def get_queued_task_ids(self, device_id: str) -> List[str]:
        """Get list of queued task IDs for a device"""
        if device_id not in self._task_queues:
            return []
        return [task.task_id for task in self._task_queues[device_id]]
