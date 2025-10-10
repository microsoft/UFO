# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Main DAG visualization observer with delegated handlers.
"""

import logging
from typing import Dict, Optional

from galaxy.visualization.dag_visualizer import DAGVisualizer

from ...constellation import TaskConstellation
from ...core.events import ConstellationEvent, Event, IEventObserver, TaskEvent
from .constellation_visualization_handler import ConstellationVisualizationHandler
from .task_visualization_handler import TaskVisualizationHandler


class DAGVisualizationObserver(IEventObserver):
    """
    Main observer that handles DAG visualization for constellation events.

    This observer coordinates between specialized handlers for different types
    of visualization events. It maintains constellation references and delegates
    specific visualization tasks to appropriate handlers.
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

        # Initialize specialized handlers
        self._task_handler = None
        self._constellation_handler = None

        # Initialize visualizer if enabled
        if self.enable_visualization:
            self._init_visualizer()

    def _init_visualizer(self) -> None:
        """
        Initialize the DAG visualizer and handlers.

        Attempts to import and create DAGVisualizer instance,
        disables visualization if import fails.
        """
        try:

            self._visualizer = DAGVisualizer(console=self._console)

            # Initialize specialized handlers
            self._task_handler = TaskVisualizationHandler(self._visualizer, self.logger)
            self._constellation_handler = ConstellationVisualizationHandler(
                self._visualizer, self.logger
            )

        except ImportError as e:
            self.logger.warning(f"Failed to import DAGVisualizer: {e}")
            self.enable_visualization = False

    async def on_event(self, event: Event) -> None:
        """
        Handle visualization events by delegating to appropriate handlers.

        :param event: Event instance for visualization processing
        """
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
        """
        Handle constellation-related visualization events.

        :param event: ConstellationEvent instance for visualization updates
        """
        constellation_id = event.constellation_id

        # Get constellation from event data if available
        constellation = self._extract_constellation_from_event(event)

        # Store constellation reference for future use
        if constellation:
            self._constellations[constellation_id] = constellation

        # Delegate to constellation handler
        if self._constellation_handler:
            await self._constellation_handler.handle_constellation_event(
                event, constellation
            )

    async def _handle_task_event(self, event: TaskEvent) -> None:
        """
        Handle task-related visualization events.

        :param event: TaskEvent instance for task visualization updates
        """
        constellation_id = event.data.get("constellation_id") if event.data else None
        if not constellation_id:
            return

        # Get constellation for this task
        constellation = self._constellations.get(constellation_id)
        if not constellation:
            return

        # Delegate to task handler
        if self._task_handler:
            await self._task_handler.handle_task_event(event, constellation)

    def _extract_constellation_from_event(
        self, event: ConstellationEvent
    ) -> Optional[TaskConstellation]:
        """
        Extract constellation from event data.

        :param event: ConstellationEvent instance
        :return: TaskConstellation instance if found, None otherwise
        """
        constellation = None
        if isinstance(event.data, dict):
            constellation = event.data.get("constellation")
            if not constellation and "updated_constellation" in event.data:
                constellation = event.data["updated_constellation"]
            if not constellation and "new_constellation" in event.data:
                constellation = event.data["new_constellation"]

        return constellation

    def set_visualization_enabled(self, enabled: bool) -> None:
        """
        Enable or disable visualization.

        :param enabled: Whether to enable visualization
        """
        self.enable_visualization = enabled
        if enabled and not self._visualizer:
            self._init_visualizer()

    def get_constellation(self, constellation_id: str) -> Optional[TaskConstellation]:
        """
        Get stored constellation by ID.

        :param constellation_id: Constellation identifier
        :return: TaskConstellation instance if found, None otherwise
        """
        return self._constellations.get(constellation_id)

    def register_constellation(
        self, constellation_id: str, constellation: TaskConstellation
    ) -> None:
        """
        Manually register a constellation for visualization.

        :param constellation_id: Constellation identifier
        :param constellation: TaskConstellation instance
        """
        self._constellations[constellation_id] = constellation

    def clear_constellations(self) -> None:
        """
        Clear all stored constellation references.
        """
        self._constellations.clear()
