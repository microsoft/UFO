# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Observer classes for constellation events.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from ..core.events import (
    Event,
    EventType,
    TaskEvent,
    ConstellationEvent,
    IEventObserver,
)
from ..constellation import TaskConstellation, TaskStatus
from ..agents.galaxy_agent import GalaxyWeaverAgent
from ufo.module.context import Context


class ConstellationProgressObserver(IEventObserver):
    """
    Observer that handles constellation progress updates.

    This replaces the complex callback logic in GalaxyRound.
    """

    def __init__(self, agent: GalaxyWeaverAgent, context: Context):
        self.agent = agent
        self.context = context
        self.task_results: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)

    async def on_event(self, event: Event) -> None:
        """Handle constellation-related events."""
        if isinstance(event, TaskEvent):
            await self._handle_task_event(event)
        elif isinstance(event, ConstellationEvent):
            await self._handle_constellation_event(event)

    async def _handle_task_event(self, event: TaskEvent) -> None:
        """Handle task progress events."""
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

            # Task events are sufficient for constellation state tracking
            # No need to publish additional constellation events

        except Exception as e:
            self.logger.error(f"Error handling task event: {e}")

    async def _handle_constellation_event(self, event: ConstellationEvent) -> None:
        """Handle constellation update events."""
        try:
            if event.event_type == EventType.NEW_TASKS_READY:
                self.logger.info(f"New ready tasks detected: {event.new_ready_tasks}")
                # The orchestration will automatically pick up new ready tasks

        except Exception as e:
            self.logger.error(f"Error handling constellation event: {e}")


class SessionMetricsObserver(IEventObserver):
    """
    Observer that collects session metrics and statistics.
    """

    def __init__(self, session_id: str, logger: Optional[logging.Logger] = None):
        self.session_id = session_id
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
        """Collect metrics from events."""
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
        """Get collected metrics."""
        return self.metrics.copy()


class DAGVisualizationObserver(IEventObserver):
    """
    Observer that handles DAG visualization for constellation events.

    This observer replaces all scattered visualization logic throughout the codebase
    with a centralized event-driven approach. It responds to constellation state
    changes, task completions, and structure modifications.
    """

    def __init__(self, enable_visualization: bool = True, console=None):
        """
        Initialize the DAG visualization observer.

        :param enable_visualization: Whether to enable visualization
        :param console: Optional rich console for output
        """
        self.enable_visualization = enable_visualization
        self.logger = logging.getLogger(__name__)
        self._visualizer = None
        self._console = console

        # Track constellations for visualization
        self._constellations: Dict[str, TaskConstellation] = {}

        # Initialize visualizer if enabled
        if self.enable_visualization:
            self._init_visualizer()

    def _init_visualizer(self) -> None:
        """Initialize the DAG visualizer."""
        try:
            from ..visualization.dag_visualizer import DAGVisualizer

            self._visualizer = DAGVisualizer(console=self._console)
        except ImportError as e:
            self.logger.warning(f"Failed to import DAGVisualizer: {e}")
            self.enable_visualization = False

    async def on_event(self, event: Event) -> None:
        """Handle visualization events."""
        if not self.enable_visualization or not self._visualizer:
            return

        try:
            if isinstance(event, ConstellationEvent):
                await self._handle_constellation_event(event)
            elif isinstance(event, TaskEvent):
                await self._handle_task_event(event)
        except Exception as e:
            self.logger.debug(f"Visualization error: {e}")

    async def _handle_constellation_event(self, event: ConstellationEvent) -> None:
        """Handle constellation-related visualization events."""
        constellation_id = event.constellation_id

        # Get constellation from event data if available
        constellation = None
        if hasattr(event, "data") and isinstance(event.data, dict):
            constellation = event.data.get("constellation")
            if not constellation and "updated_constellation" in event.data:
                constellation = event.data["updated_constellation"]

        # Store constellation reference for future use
        if constellation:
            self._constellations[constellation_id] = constellation

        # Handle different constellation events
        if event.event_type == EventType.CONSTELLATION_STARTED:
            await self._handle_constellation_started(event, constellation)
        elif event.event_type == EventType.CONSTELLATION_COMPLETED:
            await self._handle_constellation_completed(event, constellation)
        elif event.event_type == EventType.CONSTELLATION_FAILED:
            await self._handle_constellation_failed(event, constellation)

    async def _handle_task_event(self, event: TaskEvent) -> None:
        """Handle task-related visualization events."""
        constellation_id = event.data.get("constellation_id") if event.data else None
        if not constellation_id:
            return

        # Get constellation for this task
        constellation = self._constellations.get(constellation_id)
        if not constellation:
            return

        # Handle task progress visualization
        if event.event_type == EventType.TASK_STARTED:
            await self._handle_task_started(event, constellation)
        elif event.event_type == EventType.TASK_COMPLETED:
            await self._handle_task_completed(event, constellation)
        elif event.event_type == EventType.TASK_FAILED:
            await self._handle_task_failed(event, constellation)

    async def _handle_constellation_started(
        self, event: ConstellationEvent, constellation: Optional[TaskConstellation]
    ) -> None:
        """Handle constellation start visualization and auto-registration."""
        if not constellation:
            return

        try:
            # Auto-register the constellation for future visualization
            self._constellations[event.constellation_id] = constellation

            # Display constellation started overview
            self._visualizer.display_constellation_overview(
                constellation, "🚀 Constellation Started"
            )
        except Exception as e:
            self.logger.debug(f"Error displaying constellation start: {e}")

    async def _handle_constellation_completed(
        self, event: ConstellationEvent, constellation: Optional[TaskConstellation]
    ) -> None:
        """Handle constellation completion visualization."""
        if not constellation:
            return

        try:
            # Display final constellation status
            execution_time = event.data.get("execution_time") if event.data else None
            status_msg = "✅ Constellation Completed"
            if execution_time:
                status_msg += f" (in {execution_time:.2f}s)"

            self._visualizer.display_constellation_overview(constellation, status_msg)
        except Exception as e:
            self.logger.debug(f"Error displaying constellation completion: {e}")

    async def _handle_constellation_failed(
        self, event: ConstellationEvent, constellation: Optional[TaskConstellation]
    ) -> None:
        """Handle constellation failure visualization."""
        if not constellation:
            return

        try:
            # Display failure status
            self._visualizer.display_constellation_overview(
                constellation, "❌ Constellation Failed"
            )
        except Exception as e:
            self.logger.debug(f"Error displaying constellation failure: {e}")

    async def _handle_task_started(
        self, event: TaskEvent, constellation: TaskConstellation
    ) -> None:
        """Handle task started visualization."""
        try:
            # Limit task-level visualization to avoid spam
            if constellation.task_count <= 10:
                self._visualizer.display_dag_topology(constellation)
        except Exception as e:
            self.logger.debug(f"Error displaying task start: {e}")

    async def _handle_task_completed(
        self, event: TaskEvent, constellation: TaskConstellation
    ) -> None:
        """Handle task completion visualization."""
        try:
            # Show execution progress for smaller constellations
            if constellation.task_count <= 10:
                self._visualizer.display_execution_flow(constellation)
        except Exception as e:
            self.logger.debug(f"Error displaying task completion: {e}")

    async def _handle_task_failed(
        self, event: TaskEvent, constellation: TaskConstellation
    ) -> None:
        """Handle task failure visualization."""
        try:
            # Always show failure status regardless of constellation size
            self._visualizer.display_execution_flow(constellation)
        except Exception as e:
            self.logger.debug(f"Error displaying task failure: {e}")

    def set_visualization_enabled(self, enabled: bool) -> None:
        """
        Enable or disable visualization.

        :param enabled: Whether to enable visualization
        """
        self.enable_visualization = enabled
        if enabled and not self._visualizer:
            self._init_visualizer()
