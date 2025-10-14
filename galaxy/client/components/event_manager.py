# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Event Manager

Manages event handling and callbacks.
Single responsibility: Event coordination.
"""

import logging
from typing import Callable, List

from galaxy.core.types import ExecutionResult

from .types import AgentProfile


class EventManager:
    """
    Manages event handling and callbacks.
    Single responsibility: Event coordination.
    """

    def __init__(self):
        self._connection_handlers: List[Callable] = []
        self._disconnection_handlers: List[Callable] = []
        self._task_completion_handlers: List[Callable] = []
        self._task_failure_handlers: List[Callable] = []
        self.logger = logging.getLogger(f"{__name__}.EventManager")

    def add_connection_handler(self, handler: Callable) -> None:
        """Add a handler for device connection events"""
        self._connection_handlers.append(handler)

    def add_disconnection_handler(self, handler: Callable) -> None:
        """Add a handler for device disconnection events"""
        self._disconnection_handlers.append(handler)

    def add_task_completion_handler(self, handler: Callable) -> None:
        """Add a handler for task completion events"""
        self._task_completion_handlers.append(handler)

    def add_task_failure_handler(self, handler: Callable) -> None:
        """Add a handler for task failure events"""
        self._task_failure_handlers.append(handler)

    async def notify_device_connected(
        self, device_id: str, device_info: AgentProfile
    ) -> None:
        """Notify all handlers of device connection"""
        for handler in self._connection_handlers:
            try:
                await handler(device_id, device_info)
            except Exception as e:
                self.logger.error(f"Error in connection handler: {e}")

    async def notify_device_disconnected(self, device_id: str) -> None:
        """Notify all handlers of device disconnection"""
        for handler in self._disconnection_handlers:
            try:
                await handler(device_id)
            except Exception as e:
                self.logger.error(f"Error in disconnection handler: {e}")

    async def notify_task_completed(
        self, device_id: str, task_id: str, result: ExecutionResult
    ) -> None:
        """Notify all handlers of task completion"""
        for handler in self._task_completion_handlers:
            try:
                await handler(device_id, task_id, result)
            except Exception as e:
                self.logger.error(f"Error in task completion handler: {e}")

    async def notify_task_failed(
        self, device_id: str, task_id: str, error: str
    ) -> None:
        """Notify all handlers of task failure"""
        for handler in self._task_failure_handlers:
            try:
                await handler(device_id, task_id, error)
            except Exception as e:
                self.logger.error(f"Error in task failure handler: {e}")
