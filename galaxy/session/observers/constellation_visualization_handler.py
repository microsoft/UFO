# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation-specific visualization handler.
"""

import logging
from typing import Optional

from galaxy.visualization.dag_visualizer import DAGVisualizer

from ...constellation import TaskConstellation
from ...core.events import ConstellationEvent, EventType
from ...visualization import ConstellationDisplay, VisualizationChangeDetector


class ConstellationVisualizationHandler:
    """
    Specialized handler for constellation-related visualization events.

    This class routes constellation events to appropriate display components,
    delegating actual visualization to specialized display classes.
    """

    def __init__(
        self, visualizer: DAGVisualizer, logger: Optional[logging.Logger] = None
    ):
        """
        Initialize ConstellationVisualizationHandler.

        :param visualizer: DAGVisualizer instance for complex displays
        :param logger: Optional logger instance
        """
        self._visualizer = visualizer
        self.constellation_display = ConstellationDisplay(visualizer.console)
        self.logger = logger or logging.getLogger(__name__)

    async def handle_constellation_started(
        self, event: ConstellationEvent, constellation: Optional[TaskConstellation]
    ) -> None:
        """
        Handle constellation start visualization.

        :param event: ConstellationEvent instance
        :param constellation: TaskConstellation instance if available
        """
        if not constellation:
            return

        try:
            # Extract additional info from event
            additional_info = {}
            if event.data:
                additional_info = {k: v for k, v in event.data.items() if v is not None}

            # Use constellation display for start notification
            self.constellation_display.display_constellation_started(
                constellation, additional_info
            )

            # Show initial topology using DAGVisualizer
            self._visualizer.display_dag_topology(constellation)
        except Exception as e:
            self.logger.debug(f"Error displaying constellation start: {e}")

    async def handle_constellation_completed(
        self, event: ConstellationEvent, constellation: Optional[TaskConstellation]
    ) -> None:
        """
        Handle constellation completion visualization.

        :param event: ConstellationEvent instance
        :param constellation: TaskConstellation instance if available
        """
        if not constellation:
            return

        try:
            # Extract execution time from event
            execution_time = event.data.get("execution_time") if event.data else None
            additional_info = {}
            if event.data:
                additional_info = {
                    k: v
                    for k, v in event.data.items()
                    if k != "execution_time" and v is not None
                }

            # Use constellation display for completion notification
            self.constellation_display.display_constellation_completed(
                constellation, execution_time, additional_info
            )
        except Exception as e:
            self.logger.debug(f"Error displaying constellation completion: {e}")

    async def handle_constellation_failed(
        self, event: ConstellationEvent, constellation: Optional[TaskConstellation]
    ) -> None:
        """
        Handle constellation failure visualization.

        :param event: ConstellationEvent instance
        :param constellation: TaskConstellation instance if available
        """
        if not constellation:
            return

        try:
            # Extract error from event
            error = event.data.get("error") if event.data else None
            additional_info = {}
            if event.data:
                additional_info = {
                    k: v
                    for k, v in event.data.items()
                    if k != "error" and v is not None
                }

            # Use constellation display for failure notification
            self.constellation_display.display_constellation_failed(
                constellation, error, additional_info
            )
        except Exception as e:
            self.logger.debug(f"Error displaying constellation failure: {e}")

    async def handle_constellation_modified(
        self, event: ConstellationEvent, constellation: Optional[TaskConstellation]
    ) -> None:
        """
        Handle constellation modification visualization with enhanced display.

        :param event: ConstellationEvent instance
        :param constellation: TaskConstellation instance if available
        """
        try:
            if not constellation:
                return

            # Get old and new constellations from event data
            old_constellation = None
            new_constellation = constellation

            if event.data:
                old_constellation = event.data.get("old_constellation")
                if "new_constellation" in event.data:
                    new_constellation = event.data["new_constellation"]
                elif "updated_constellation" in event.data:
                    new_constellation = event.data["updated_constellation"]

            # Calculate changes using specialized detector
            changes = VisualizationChangeDetector.calculate_constellation_changes(
                old_constellation, new_constellation
            )

            # Extract additional info from event
            additional_info = {}
            if event.data:
                excluded_keys = {
                    "old_constellation",
                    "new_constellation",
                    "updated_constellation",
                    "processing_start_time",
                    "processing_end_time",
                    "processing_duration",
                }
                additional_info = {
                    k: v
                    for k, v in event.data.items()
                    if k not in excluded_keys and v is not None
                }

            # Use constellation display for modification notification
            self.constellation_display.display_constellation_modified(
                new_constellation, changes, additional_info
            )

            # Show updated topology using DAGVisualizer
            self._visualizer.display_dag_topology(new_constellation)

        except Exception as e:
            self.logger.debug(f"Error displaying constellation modification: {e}")

    async def handle_constellation_event(
        self, event: ConstellationEvent, constellation: Optional[TaskConstellation]
    ) -> None:
        """
        Route constellation events to appropriate handlers.

        :param event: ConstellationEvent instance
        :param constellation: TaskConstellation instance if available
        """
        if event.event_type == EventType.CONSTELLATION_STARTED:
            await self.handle_constellation_started(event, constellation)
        elif event.event_type == EventType.CONSTELLATION_COMPLETED:
            await self.handle_constellation_completed(event, constellation)
        elif event.event_type == EventType.CONSTELLATION_FAILED:
            await self.handle_constellation_failed(event, constellation)
        elif event.event_type == EventType.CONSTELLATION_MODIFIED:
            await self.handle_constellation_modified(event, constellation)
