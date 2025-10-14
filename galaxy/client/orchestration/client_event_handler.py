# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Client Event Handler

Handles event management and callbacks for ConstellationClient.
Single responsibility: Event handling coordination.
"""

import logging
from typing import Dict, Any, Callable, List

from ..components import AgentProfile


class ClientEventHandler:
    """
    Manages client-level event handling and callbacks.
    Single responsibility: Client event coordination.
    """

    def __init__(self):
        """Initialize the client event handler."""
        self._connection_handlers: List[Callable] = []
        self._disconnection_handlers: List[Callable] = []
        self._task_completion_handlers: List[Callable] = []
        self._error_handlers: List[Callable] = []
        self.logger = logging.getLogger(f"{__name__}.ClientEventHandler")

    def add_connection_handler(self, handler: Callable) -> None:
        """
        Add a handler for device connection events.

        :param handler: Async function(device_id: str, device_info: AgentProfile) -> None
        """
        self._connection_handlers.append(handler)
        self.logger.debug(f"📝 Added connection handler: {handler.__name__}")

    def add_disconnection_handler(self, handler: Callable) -> None:
        """
        Add a handler for device disconnection events.

        :param handler: Async function(device_id: str) -> None
        """
        self._disconnection_handlers.append(handler)
        self.logger.debug(f"📝 Added disconnection handler: {handler.__name__}")

    def add_task_completion_handler(self, handler: Callable) -> None:
        """
        Add a handler for task completion events.

        :param handler: Async function(device_id: str, task_id: str, result: Dict[str, Any]) -> None
        """
        self._task_completion_handlers.append(handler)
        self.logger.debug(f"📝 Added task completion handler: {handler.__name__}")

    def add_error_handler(self, handler: Callable) -> None:
        """
        Add a handler for error events.

        :param handler: Async function(error_type: str, error_message: str, context: Dict[str, Any]) -> None
        """
        self._error_handlers.append(handler)
        self.logger.debug(f"📝 Added error handler: {handler.__name__}")

    async def handle_device_connected(
        self, device_id: str, device_info: AgentProfile
    ) -> None:
        """
        Handle device connection events.

        :param device_id: Connected device ID
        :param device_info: Device information
        """
        self.logger.info(f"🔗 Device {device_id} connected successfully")

        for handler in self._connection_handlers:
            try:
                await handler(device_id, device_info)
            except Exception as e:
                self.logger.error(
                    f"❌ Error in connection handler {handler.__name__}: {e}"
                )
                await self._notify_error_handlers(
                    "connection_handler_error",
                    str(e),
                    {"device_id": device_id, "handler": handler.__name__},
                )

    async def handle_device_disconnected(self, device_id: str) -> None:
        """
        Handle device disconnection events.

        :param device_id: Disconnected device ID
        """
        self.logger.warning(f"🔌 Device {device_id} disconnected")

        for handler in self._disconnection_handlers:
            try:
                await handler(device_id)
            except Exception as e:
                self.logger.error(
                    f"❌ Error in disconnection handler {handler.__name__}: {e}"
                )
                await self._notify_error_handlers(
                    "disconnection_handler_error",
                    str(e),
                    {"device_id": device_id, "handler": handler.__name__},
                )

    async def handle_task_completed(
        self, device_id: str, task_id: str, result: Dict[str, Any]
    ) -> None:
        """
        Handle task completion events.

        :param device_id: Device that completed the task
        :param task_id: Completed task ID
        :param result: Task result
        """
        self.logger.info(f"✅ Task {task_id} completed on device {device_id}")

        for handler in self._task_completion_handlers:
            try:
                await handler(device_id, task_id, result)
            except Exception as e:
                self.logger.error(
                    f"❌ Error in task completion handler {handler.__name__}: {e}"
                )
                await self._notify_error_handlers(
                    "task_completion_handler_error",
                    str(e),
                    {
                        "device_id": device_id,
                        "task_id": task_id,
                        "handler": handler.__name__,
                    },
                )

    async def _notify_error_handlers(
        self, error_type: str, error_message: str, context: Dict[str, Any]
    ) -> None:
        """
        Notify all error handlers of an error.

        :param error_type: Type of error
        :param error_message: Error message
        :param context: Additional error context
        """
        for handler in self._error_handlers:
            try:
                await handler(error_type, error_message, context)
            except Exception as e:
                # Avoid infinite recursion - just log error handler failures
                self.logger.error(f"❌ Error in error handler {handler.__name__}: {e}")

    def get_handler_counts(self) -> Dict[str, int]:
        """
        Get the number of registered handlers for each event type.

        :return: Dictionary with handler counts
        """
        return {
            "connection_handlers": len(self._connection_handlers),
            "disconnection_handlers": len(self._disconnection_handlers),
            "task_completion_handlers": len(self._task_completion_handlers),
            "error_handlers": len(self._error_handlers),
        }

    def clear_all_handlers(self) -> None:
        """Clear all registered event handlers."""
        self._connection_handlers.clear()
        self._disconnection_handlers.clear()
        self._task_completion_handlers.clear()
        self._error_handlers.clear()
        self.logger.info("🧹 All event handlers cleared")

    def remove_handler(self, handler: Callable, event_type: str) -> bool:
        """
        Remove a specific handler from an event type.

        :param handler: Handler function to remove
        :param event_type: Event type ("connection", "disconnection", "task_completion", "error")
        :return: True if handler was found and removed
        """
        handler_lists = {
            "connection": self._connection_handlers,
            "disconnection": self._disconnection_handlers,
            "task_completion": self._task_completion_handlers,
            "error": self._error_handlers,
        }

        if event_type not in handler_lists:
            self.logger.error(f"❌ Unknown event type: {event_type}")
            return False

        handler_list = handler_lists[event_type]
        if handler in handler_list:
            handler_list.remove(handler)
            self.logger.debug(f"🗑️ Removed {event_type} handler: {handler.__name__}")
            return True

        return False
