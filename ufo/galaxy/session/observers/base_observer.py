# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base observer classes for constellation progress and session metrics.
"""

import logging
from typing import Any, Dict, Optional

from ...core.events import (
    Event,
    EventType,
    TaskEvent,
    ConstellationEvent,
    IEventObserver,
)
from ...agents.constellation_agent import ConstellationAgent
from ufo.module.context import Context


class ConstellationProgressObserver(IEventObserver):
    """
    Observer that handles constellation progress updates.

    This replaces the complex callback logic in GalaxyRound.
    """

    def __init__(self, agent: ConstellationAgent, context: Context):
        """
        Initialize ConstellationProgressObserver.

        :param agent: ConstellationAgent instance for task coordination
        :param context: Context object for the session
        """
        self.agent = agent
        self.context = context
        self.task_results: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)

    async def on_event(self, event: Event) -> None:
        """
        Handle constellation-related events.

        :param event: Event instance to handle (TaskEvent or ConstellationEvent)
        """
        if isinstance(event, TaskEvent):
            await self._handle_task_event(event)
        elif isinstance(event, ConstellationEvent):
            await self._handle_constellation_event(event)

    async def _handle_task_event(self, event: TaskEvent) -> None:
        """
        Handle task progress events and queue them for agent processing.

        :param event: TaskEvent instance containing task status updates
        """
        try:
            self.logger.info(f"Task progress: {event.task_id} -> {event.status}")

            # Store task result
            self.task_results[event.task_id] = {
                "task_id": event.task_id,
                "status": event.status,
                "result": event.result,
                "error": event.error,
                "timestamp": event.timestamp,
            }

            # Put event into agent's queue - this will wake up the Continue state
            await self.agent.task_completion_queue.put(event)

            self.logger.info(
                f"Queued task completion: {event.task_id} -> {event.status}"
            )

        except Exception as e:
            self.logger.error(f"Error handling task event: {e}")

    async def _handle_constellation_event(self, event: ConstellationEvent) -> None:
        """
        Handle constellation update events - now handled by agent state machine.

        :param event: ConstellationEvent instance containing constellation updates
        """
        try:
            if (
                event.event_type == EventType.CONSTELLATION_MODIFIED
            ):  # Changed from NEW_TASKS_READY to DAG_MODIFIED
                self.logger.info(
                    f"Constellation modified, new ready tasks: {event.new_ready_tasks}"
                )
                # The orchestration will automatically pick up new ready tasks

        except Exception as e:
            self.logger.error(f"Error handling constellation event: {e}")


class SessionMetricsObserver(IEventObserver):
    """
    Observer that collects session metrics and statistics.
    """

    def __init__(self, session_id: str, logger: Optional[logging.Logger] = None):
        """
        Initialize SessionMetricsObserver.

        :param session_id: Unique session identifier for metrics tracking
        :param logger: Optional logger instance (creates default if None)
        """
        self.metrics: Dict[str, Any] = {
            "session_id": session_id,
            "task_count": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_execution_time": 0.0,
            "task_timings": {},
        }
        self.logger = logger or logging.getLogger(__name__)

    async def on_event(self, event: Event) -> None:
        """
        Collect metrics from events.

        :param event: Event instance for metrics collection
        """
        if isinstance(event, TaskEvent):
            if event.event_type == EventType.TASK_STARTED:
                self.metrics["task_count"] += 1
                self.metrics["task_timings"][event.task_id] = {"start": event.timestamp}

            elif event.event_type == EventType.TASK_COMPLETED:
                self.metrics["completed_tasks"] += 1
                if event.task_id in self.metrics["task_timings"]:
                    duration = (
                        event.timestamp
                        - self.metrics["task_timings"][event.task_id]["start"]
                    )
                    self.metrics["task_timings"][event.task_id]["duration"] = duration
                    self.metrics["total_execution_time"] += duration

            elif event.event_type == EventType.TASK_FAILED:
                self.metrics["failed_tasks"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get collected metrics.

        :return: Dictionary containing session metrics and statistics
        """
        return self.metrics.copy()
