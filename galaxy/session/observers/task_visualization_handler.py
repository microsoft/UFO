# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task-specific visualization handler.
"""

import logging
from typing import Optional

from galaxy.visualization import DAGVisualizer, TaskDisplay

from ...constellation import TaskConstellation
from ...core.events import EventType, TaskEvent


class TaskVisualizationHandler:
    """
    Specialized handler for task-related visualization events.

    This class routes task events to appropriate display components,
    delegating actual visualization to specialized display classes.
    """

    def __init__(
        self, visualizer: DAGVisualizer, logger: Optional[logging.Logger] = None
    ):
        """
        Initialize TaskVisualizationHandler.

        :param visualizer: DAGVisualizer instance for complex displays
        :param logger: Optional logger instance
        """
        self._visualizer = visualizer
        self.task_display = TaskDisplay(visualizer.console)
        self.logger = logger or logging.getLogger(__name__)

    async def handle_task_started(
        self, event: TaskEvent, constellation: TaskConstellation
    ) -> None:
        """
        Handle task started visualization.

        :param event: TaskEvent instance
        :param constellation: TaskConstellation containing the task
        """
        try:
            # Get task info
            task_id = event.task_id
            task = constellation.get_task(task_id) if task_id else None

            if task:
                # Extract additional info from event
                additional_info = {}
                if event.data:
                    additional_info = {
                        k: v for k, v in event.data.items() if v is not None
                    }

                # Use task display for start notification
                self.task_display.display_task_started(task, additional_info)

            # Show topology for smaller constellations
            # if constellation.task_count <= 10:
            #     self._visualizer.display_dag_topology(constellation)

        except Exception as e:
            self.logger.debug(f"Error displaying task start: {e}")

    async def handle_task_completed(
        self, event: TaskEvent, constellation: TaskConstellation
    ) -> None:
        """
        Handle task completion visualization.

        :param event: TaskEvent instance
        :param constellation: TaskConstellation containing the task
        """
        try:
            # Get task info
            task_id = event.task_id
            task = constellation.get_task(task_id) if task_id else None

            if task:
                # Extract execution details from event
                execution_time = (
                    event.data.get("execution_time") if event.data else None
                )
                result = getattr(event, "result", None) or (
                    event.data.get("result") if event.data else None
                )
                newly_ready_count = (
                    len(event.data.get("newly_ready_tasks", [])) if event.data else None
                )

                # Use task display for completion notification
                self.task_display.display_task_completed(
                    task, execution_time, result, newly_ready_count
                )

            # Show execution progress for smaller constellations
            if constellation.task_count <= 10:
                self._visualizer.display_execution_flow(constellation)

        except Exception as e:
            self.logger.debug(f"Error displaying task completion: {e}")

    async def handle_task_failed(
        self, event: TaskEvent, constellation: TaskConstellation
    ) -> None:
        """
        Handle task failure visualization.

        :param event: TaskEvent instance
        :param constellation: TaskConstellation containing the task
        """
        try:
            # Get task info
            task_id = event.task_id
            task = constellation.get_task(task_id) if task_id else None

            if task:
                # Extract error details from event
                error = getattr(event, "error", None) or (
                    event.data.get("error") if event.data else None
                )

                # Extract retry information
                retry_info = None
                if event.data:
                    if "current_retry" in event.data and "max_retries" in event.data:
                        retry_info = {
                            "current_retry": event.data["current_retry"],
                            "max_retries": event.data["max_retries"],
                        }

                newly_ready_count = (
                    len(event.data.get("newly_ready_tasks", [])) if event.data else None
                )

                # Use task display for failure notification
                self.task_display.display_task_failed(
                    task, error, retry_info, newly_ready_count
                )

            # Always show failure status regardless of constellation size
            # self._visualizer.display_execution_flow(constellation)

        except Exception as e:
            self.logger.debug(f"Error displaying task failure: {e}")

    async def handle_task_event(
        self, event: TaskEvent, constellation: TaskConstellation
    ) -> None:
        """
        Route task events to appropriate handlers.

        :param event: TaskEvent instance
        :param constellation: TaskConstellation containing the task
        """
        if event.event_type == EventType.TASK_STARTED:
            await self.handle_task_started(event, constellation)
        elif event.event_type == EventType.TASK_COMPLETED:
            await self.handle_task_completed(event, constellation)
        elif event.event_type == EventType.TASK_FAILED:
            await self.handle_task_failed(event, constellation)
