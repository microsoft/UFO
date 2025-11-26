# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base observer classes for constellation progress and session metrics.
"""

import logging
from typing import Any, Dict, Optional

from ...agents.constellation_agent import ConstellationAgent
from ...core.events import (
    ConstellationEvent,
    Event,
    EventType,
    IEventObserver,
    TaskEvent,
)
from ...visualization.change_detector import VisualizationChangeDetector


class ConstellationProgressObserver(IEventObserver):
    """
    Observer that handles constellation progress updates.

    This replaces the complex callback logic in GalaxyRound.
    """

    def __init__(self, agent: ConstellationAgent):
        """
        Initialize ConstellationProgressObserver.

        :param agent: ConstellationAgent instance for task coordination
        """
        self.agent = agent
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
            self.logger.info(
                f"Task progress: {event.task_id} -> {event.status}. Event Type: {event.event_type}"
            )

            # Store task result
            self.task_results[event.task_id] = {
                "task_id": event.task_id,
                "status": event.status,
                "result": event.result,
                "error": event.error,
                "timestamp": event.timestamp,
            }

            # Put event into agent's queue - this will wake up the Continue state
            if event.event_type in [EventType.TASK_COMPLETED, EventType.TASK_FAILED]:
                await self.agent.add_task_completion_event(event)

        except AttributeError as e:
            self.logger.error(
                f"Attribute error handling task event: {e}", exc_info=True
            )
        except KeyError as e:
            self.logger.error(f"Missing key in task event: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(
                f"Unexpected error handling task event: {e}", exc_info=True
            )

    async def _handle_constellation_event(self, event: ConstellationEvent) -> None:
        """
        Handle constellation update events - now handled by agent state machine.

        :param event: ConstellationEvent instance containing constellation updates
        """
        try:
            if event.event_type == EventType.CONSTELLATION_COMPLETED:
                await self.agent.add_constellation_completion_event(event)

        except AttributeError as e:
            self.logger.error(
                f"Attribute error handling constellation event: {e}", exc_info=True
            )
        except Exception as e:
            self.logger.error(
                f"Unexpected error handling constellation event: {e}", exc_info=True
            )


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
            "constellation_count": 0,
            "completed_constellations": 0,
            "failed_constellations": 0,
            "total_constellation_time": 0.0,
            "constellation_timings": {},
            "constellation_modifications": {},  # Track modifications per constellation
        }
        self.logger = logger or logging.getLogger(__name__)

    async def on_event(self, event: Event) -> None:
        """
        Collect metrics from events.

        :param event: Event instance for metrics collection
        """
        if isinstance(event, TaskEvent):
            await self._handle_task_event(event)
        elif isinstance(event, ConstellationEvent):
            await self._handle_constellation_event(event)

    async def _handle_task_event(self, event: TaskEvent) -> None:
        """
        Handle task-related events for metrics collection.

        :param event: TaskEvent instance
        """
        if event.event_type == EventType.TASK_STARTED:
            self._handle_task_started(event)
        elif event.event_type == EventType.TASK_COMPLETED:
            self._handle_task_completed(event)
        elif event.event_type == EventType.TASK_FAILED:
            self._handle_task_failed(event)

    async def _handle_constellation_event(self, event: ConstellationEvent) -> None:
        """
        Handle constellation-related events for metrics collection.

        :param event: ConstellationEvent instance
        """
        if event.event_type == EventType.CONSTELLATION_STARTED:
            self._handle_constellation_started(event)
        elif event.event_type == EventType.CONSTELLATION_COMPLETED:
            self._handle_constellation_completed(event)
        elif event.event_type == EventType.CONSTELLATION_MODIFIED:
            self._handle_constellation_modified(event)

    def _handle_task_started(self, event: TaskEvent) -> None:
        """
        Handle TASK_STARTED event.

        :param event: TaskEvent instance
        """
        self.metrics["task_count"] += 1
        self.metrics["task_timings"][event.task_id] = {"start": event.timestamp}

    def _handle_task_completed(self, event: TaskEvent) -> None:
        """
        Handle TASK_COMPLETED event.

        :param event: TaskEvent instance
        """
        self.metrics["completed_tasks"] += 1

        if event.task_id in self.metrics["task_timings"]:
            duration = (
                event.timestamp - self.metrics["task_timings"][event.task_id]["start"]
            )
            self.metrics["task_timings"][event.task_id]["duration"] = duration
            self.metrics["task_timings"][event.task_id]["end"] = event.timestamp
            self.metrics["total_execution_time"] += duration

    def _handle_task_failed(self, event: TaskEvent) -> None:
        """
        Handle TASK_FAILED event.

        :param event: TaskEvent instance
        """
        self.metrics["failed_tasks"] += 1
        if event.task_id in self.metrics["task_timings"]:
            duration = (
                event.timestamp - self.metrics["task_timings"][event.task_id]["start"]
            )
            self.metrics["task_timings"][event.task_id]["duration"] = duration
            self.metrics["total_execution_time"] += duration
            self.metrics["task_timings"][event.task_id]["end"] = event.timestamp

    def _handle_constellation_started(self, event: ConstellationEvent) -> None:
        """
        Handle CONSTELLATION_STARTED event.

        :param event: ConstellationEvent instance
        """
        self.metrics["constellation_count"] += 1
        constellation_id = event.constellation_id

        # Extract constellation from event data
        constellation = event.data.get("constellation")

        # Store initial constellation statistics
        self.metrics["constellation_timings"][constellation_id] = {
            "start_time": event.timestamp,
            "initial_statistics": (
                constellation.get_statistics() if constellation else {}
            ),
            "processing_start_time": event.data.get("processing_start_time"),
            "processing_end_time": event.data.get("processing_end_time"),
            "processing_duration": event.data.get("processing_duration"),
        }

    def _handle_constellation_completed(self, event: ConstellationEvent) -> None:
        """
        Handle CONSTELLATION_COMPLETED event.

        :param event: ConstellationEvent instance
        """
        self.metrics["completed_constellations"] += 1
        constellation_id = event.constellation_id
        constellation = event.data.get("constellation")

        duration = (
            event.timestamp
            - self.metrics["constellation_timings"][constellation_id]["start_time"]
            if constellation_id in self.metrics["constellation_timings"]
            else None
        )

        # Store final constellation statistics
        if constellation_id in self.metrics["constellation_timings"]:
            self.metrics["constellation_timings"][constellation_id].update(
                {
                    "end_time": event.timestamp,
                    "duration": duration,
                    "final_statistics": (
                        constellation.get_statistics() if constellation else {}
                    ),
                }
            )

    def _handle_constellation_modified(self, event: ConstellationEvent) -> None:
        """
        Handle CONSTELLATION_MODIFIED event.

        :param event: ConstellationEvent instance
        """
        constellation_id = event.constellation_id

        # Initialize modifications list for this constellation if needed
        if constellation_id not in self.metrics["constellation_modifications"]:
            self.metrics["constellation_modifications"][constellation_id] = []

        # Extract old and new constellations from event data
        if hasattr(event, "data") and event.data:
            old_constellation = event.data.get("old_constellation")
            new_constellation = event.data.get("new_constellation")

            # Calculate changes using VisualizationChangeDetector
            changes = None
            if old_constellation and new_constellation:
                changes = VisualizationChangeDetector.calculate_constellation_changes(
                    old_constellation, new_constellation
                )

            # Get new constellation statistics
            new_statistics = (
                new_constellation.get_statistics() if new_constellation else {}
            )

            # Store modification record
            modification_record = {
                "timestamp": event.timestamp,
                "modification_type": event.data.get("modification_type", "unknown"),
                "on_task_id": event.data.get("on_task_id", []),
                "changes": changes,
                "new_statistics": new_statistics,
                "processing_start_time": event.data.get("processing_start_time"),
                "processing_end_time": event.data.get("processing_end_time"),
                "processing_duration": event.data.get("processing_duration"),
            }

            self.metrics["constellation_modifications"][constellation_id].append(
                modification_record
            )

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get collected metrics with computed statistics.

        :return: Dictionary containing session metrics and computed statistics
        """
        metrics = self.metrics.copy()

        # Compute task statistics
        task_stats = self._compute_task_statistics()
        metrics["task_statistics"] = task_stats

        # Compute constellation statistics
        constellation_stats = self._compute_constellation_statistics()
        metrics["constellation_statistics"] = constellation_stats

        # Compute modification statistics
        modification_stats = self._compute_modification_statistics()
        metrics["modification_statistics"] = modification_stats

        return metrics

    def _compute_task_statistics(self) -> Dict[str, Any]:
        """
        Compute task-related statistics.

        :return: Dictionary containing computed task statistics
        """
        task_timings = self.metrics.get("task_timings", {})

        # Collect all task durations
        durations = [
            timing["duration"]
            for timing in task_timings.values()
            if "duration" in timing
        ]

        return {
            "total_tasks": self.metrics.get("task_count", 0),
            "completed_tasks": self.metrics.get("completed_tasks", 0),
            "failed_tasks": self.metrics.get("failed_tasks", 0),
            "success_rate": (
                self.metrics.get("completed_tasks", 0)
                / self.metrics.get("task_count", 1)
                if self.metrics.get("task_count", 0) > 0
                else 0.0
            ),
            "failure_rate": (
                self.metrics.get("failed_tasks", 0) / self.metrics.get("task_count", 1)
                if self.metrics.get("task_count", 0) > 0
                else 0.0
            ),
            "average_task_duration": (
                sum(durations) / len(durations) if durations else 0.0
            ),
            "min_task_duration": min(durations) if durations else 0.0,
            "max_task_duration": max(durations) if durations else 0.0,
            "total_task_execution_time": self.metrics.get("total_execution_time", 0.0),
        }

    def _compute_constellation_statistics(self) -> Dict[str, Any]:
        """
        Compute constellation-related statistics.

        :return: Dictionary containing computed constellation statistics
        """
        constellation_timings = self.metrics.get("constellation_timings", {})

        # Collect all constellation durations
        durations = [
            timing["duration"]
            for timing in constellation_timings.values()
            if "duration" in timing and timing["duration"] is not None
        ]

        # Calculate average tasks per constellation
        total_tasks_in_constellations = 0
        constellation_count = 0

        for timing in constellation_timings.values():
            initial_stats = timing.get("initial_statistics", {})
            if "total_tasks" in initial_stats:
                total_tasks_in_constellations += initial_stats["total_tasks"]
                constellation_count += 1

        return {
            "total_constellations": self.metrics.get("constellation_count", 0),
            "completed_constellations": self.metrics.get("completed_constellations", 0),
            "failed_constellations": self.metrics.get("failed_constellations", 0),
            "success_rate": (
                self.metrics.get("completed_constellations", 0)
                / self.metrics.get("constellation_count", 1)
                if self.metrics.get("constellation_count", 0) > 0
                else 0.0
            ),
            "average_constellation_duration": (
                sum(durations) / len(durations) if durations else 0.0
            ),
            "min_constellation_duration": min(durations) if durations else 0.0,
            "max_constellation_duration": max(durations) if durations else 0.0,
            "total_constellation_time": self.metrics.get(
                "total_constellation_time", 0.0
            ),
            "average_tasks_per_constellation": (
                total_tasks_in_constellations / constellation_count
                if constellation_count > 0
                else 0.0
            ),
        }

    def _compute_modification_statistics(self) -> Dict[str, Any]:
        """
        Compute constellation modification statistics.

        :return: Dictionary containing computed modification statistics
        """
        modifications = self.metrics.get("constellation_modifications", {})

        # Total modifications across all constellations
        total_modifications = sum(len(mods) for mods in modifications.values())

        # Modifications per constellation
        modifications_per_constellation = {
            const_id: len(mods) for const_id, mods in modifications.items()
        }

        # Average modifications per constellation
        avg_modifications = (
            total_modifications / len(modifications) if modifications else 0.0
        )

        # Find most modified constellation
        most_modified_constellation = None
        max_modifications = 0
        if modifications_per_constellation:
            most_modified_constellation = max(
                modifications_per_constellation.items(), key=lambda x: x[1]
            )
            max_modifications = most_modified_constellation[1]
            most_modified_constellation = most_modified_constellation[0]

        # Collect modification types
        modification_types = {}
        for const_mods in modifications.values():
            for mod in const_mods:
                mod_type = mod.get("modification_type", "unknown")
                modification_types[mod_type] = modification_types.get(mod_type, 0) + 1

        return {
            "total_modifications": total_modifications,
            "constellations_modified": len(modifications),
            "average_modifications_per_constellation": avg_modifications,
            "max_modifications_for_single_constellation": max_modifications,
            "most_modified_constellation": most_modified_constellation,
            "modifications_per_constellation": modifications_per_constellation,
            "modification_types_breakdown": modification_types,
        }
