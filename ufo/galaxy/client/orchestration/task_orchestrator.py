# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task Orchestrator

Handles single task execution, task ID generation, and task lifecycle management.
Single responsibility: Individual task coordination.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Callable

from ..device_manager import ConstellationDeviceManager


class TaskOrchestrator:
    """
    Manages individual task execution and lifecycle.
    Single responsibility: Task execution coordination.
    """

    def __init__(self, device_manager: ConstellationDeviceManager):
        """
        Initialize the task orchestrator.

        :param device_manager: Device manager for task execution
        """
        self.device_manager = device_manager
        self._task_counter = 0
        self._task_callbacks: Dict[str, Callable] = {}
        self.logger = logging.getLogger(f"{__name__}.TaskOrchestrator")

    def generate_task_id(self) -> str:
        """Generate a unique task ID"""
        self._task_counter += 1
        return f"task_{self._task_counter}_{uuid.uuid4().hex[:8]}"

    def register_task_callback(self, task_id: str, callback: Callable) -> None:
        """Register a callback for task completion"""
        self._task_callbacks[task_id] = callback

    async def execute_task(
        self,
        request: str,
        device_id: str,
        target_client_id: Optional[str] = None,
        task_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: float = 300.0,
        callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute a single task on a specific device.

        :param request: Task request description
        :param device_id: Target device ID
        :param target_client_id: Specific local client ID (optional)
        :param task_name: Task name
        :param metadata: Additional task metadata
        :param timeout: Task timeout in seconds
        :param callback: Completion callback function
        :return: Task execution result
        """
        # Generate task ID
        task_id = self.generate_task_id()

        if not task_name:
            task_name = f"constellation_task_{self._task_counter}"

        # Validate device is connected
        if device_id not in self.device_manager.get_connected_devices():
            raise ValueError(f"Device {device_id} is not connected")

        # Register callback if provided
        if callback:
            self.register_task_callback(task_id, callback)

        try:
            # Execute task via device manager
            result = await self.device_manager.assign_task_to_device(
                task_id=task_id,
                device_id=device_id,
                target_client_id=target_client_id,
                task_description=request,
                task_data=metadata or {},
                timeout=timeout,
            )

            self.logger.info(
                f"✅ Task {task_id} completed successfully on device {device_id}"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ Task {task_id} failed on device {device_id}: {e}")
            # Clean up callback
            self._task_callbacks.pop(task_id, None)
            raise

    async def handle_task_completion(
        self, task_id: str, device_id: str, result: Dict[str, Any]
    ) -> None:
        """
        Handle task completion and execute callbacks.

        :param task_id: Completed task ID
        :param device_id: Device that completed the task
        :param result: Task result
        """
        if task_id in self._task_callbacks:
            try:
                callback = self._task_callbacks[task_id]
                await callback(task_id, device_id, result)
            except Exception as e:
                self.logger.error(f"Error in task callback for {task_id}: {e}")
            finally:
                del self._task_callbacks[task_id]

    def get_pending_callbacks(self) -> List[str]:
        """Get list of task IDs with pending callbacks"""
        return list(self._task_callbacks.keys())

    def cleanup_callbacks(self) -> None:
        """Clean up all pending callbacks"""
        self._task_callbacks.clear()
        self.logger.info("🧹 All task callbacks cleaned up")
