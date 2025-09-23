# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation-specific visualization handler.
"""

import logging
from typing import Optional

from ...core.events import ConstellationEvent, EventType
from ...constellation import TaskConstellation
from .visualization_change_detector import VisualizationChangeDetector


class ConstellationVisualizationHandler:
    """
    Specialized handler for constellation-related visualization events.

    This class encapsulates all constellation visualization logic, including
    constellation start, completion, failure, and modification displays.
    """

    def __init__(self, visualizer, logger: Optional[logging.Logger] = None):
        """
        Initialize ConstellationVisualizationHandler.

        :param visualizer: DAGVisualizer instance for rendering
        :param logger: Optional logger instance
        """
        self._visualizer = visualizer
        self.logger = logger or logging.getLogger(__name__)

    async def handle_constellation_started(
        self, event: ConstellationEvent, constellation: Optional[TaskConstellation]
    ) -> None:
        """
        Handle constellation start visualization and auto-registration.

        :param event: ConstellationEvent instance
        :param constellation: TaskConstellation instance if available
        """
        if not constellation:
            return

        try:
            # Display constellation started overview
            self._visualizer.display_constellation_overview(
                constellation, "🚀 Constellation Started"
            )
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
            # Display final constellation status
            execution_time = event.data.get("execution_time") if event.data else None
            status_msg = "✅ Constellation Completed"
            if execution_time:
                status_msg += f" (in {execution_time:.2f}s)"

            self._visualizer.display_constellation_overview(constellation, status_msg)
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
            # Display failure status
            self._visualizer.display_constellation_overview(
                constellation, "❌ Constellation Failed"
            )
        except Exception as e:
            self.logger.debug(f"Error displaying constellation failure: {e}")

    async def handle_constellation_modified(
        self, event: ConstellationEvent, constellation: Optional[TaskConstellation]
    ) -> None:
        """
        Handle constellation modification visualization with enhanced display.
        Automatically compares old and new constellation to detect changes.

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

            # Calculate changes by comparing old and new constellations
            changes = VisualizationChangeDetector.calculate_constellation_changes(
                old_constellation, new_constellation
            )

            # Create and display modification panel
            self._create_modification_panel(new_constellation, changes)

            # Show updated topology
            self._visualizer.display_dag_topology(new_constellation)

        except Exception as e:
            self.logger.debug(f"Error displaying constellation modification: {e}")

    def _create_modification_panel(
        self, constellation: TaskConstellation, changes: dict
    ) -> None:
        """
        Create and display a Rich panel for constellation modifications.

        :param constellation: Current constellation state
        :param changes: Dictionary containing detected changes
        """
        from rich.panel import Panel
        from rich.text import Text
        from rich.table import Table
        from rich.console import Group

        # Create modification message
        mod_text = Text()
        mod_text.append("🔄 ", style="bold blue")
        mod_text.append(f"Constellation Modified: ", style="bold blue")
        mod_text.append(f"{constellation.name}", style="bold yellow")
        mod_text.append(f" ({constellation.constellation_id})", style="dim")

        # Create details table
        table = Table(show_header=False, show_edge=False, padding=0)
        table.add_column("Key", style="cyan", width=20)
        table.add_column("Value", style="white", width=50)

        # Add calculated modification details
        if changes["modification_type"]:
            table.add_row("🔧 Change Type:", changes["modification_type"])

        if changes["added_tasks"]:
            table.add_row("➕ Tasks Added:", f"{len(changes['added_tasks'])} new tasks")
            # Show task names if not too many
            if len(changes["added_tasks"]) <= 3:
                task_names = ", ".join(
                    [
                        t[:10] + "..." if len(t) > 10 else t
                        for t in changes["added_tasks"]
                    ]
                )
                table.add_row("", f"({task_names})")

        if changes["removed_tasks"]:
            table.add_row("➖ Tasks Removed:", f"{len(changes['removed_tasks'])} tasks")
            # Show task names if not too many
            if len(changes["removed_tasks"]) <= 3:
                task_names = ", ".join(
                    [
                        t[:10] + "..." if len(t) > 10 else t
                        for t in changes["removed_tasks"]
                    ]
                )
                table.add_row("", f"({task_names})")

        if changes["added_dependencies"]:
            table.add_row(
                "🔗 Deps Added:", f"{len(changes['added_dependencies'])} links"
            )

        if changes["removed_dependencies"]:
            table.add_row(
                "🔗 Deps Removed:", f"{len(changes['removed_dependencies'])} links"
            )

        if changes["modified_tasks"]:
            table.add_row(
                "📝 Tasks Modified:", f"{len(changes['modified_tasks'])} tasks updated"
            )

        # Add current constellation stats
        self._add_constellation_stats_to_table(table, constellation)

        # Create panel with proper Rich composition
        content = Group(mod_text, "", table)

        panel = Panel(
            content,
            title="[bold blue]⚙️ Constellation Structure Updated[/bold blue]",
            border_style="blue",
            width=80,
        )

        self._visualizer.console.print(panel)

    def _add_constellation_stats_to_table(
        self, table, constellation: TaskConstellation
    ) -> None:
        """
        Add constellation statistics to the details table.

        :param table: Rich Table instance to add rows to
        :param constellation: TaskConstellation instance for statistics
        """
        stats = (
            constellation.get_statistics()
            if hasattr(constellation, "get_statistics")
            else {}
        )

        if stats:
            table.add_row(
                "📊 Total Tasks:",
                str(stats.get("total_tasks", len(constellation.tasks))),
            )
            table.add_row(
                "🔗 Total Deps:",
                str(stats.get("total_dependencies", len(constellation.dependencies))),
            )

            # Task status breakdown
            status_counts = stats.get("task_status_counts", {})
            if status_counts:
                status_summary = []
                for status, count in status_counts.items():
                    if count > 0:
                        icon = {
                            "completed": "✅",
                            "running": "🔵",
                            "pending": "⭕",
                            "failed": "❌",
                        }.get(status, "⚪")
                        status_summary.append(f"{icon} {count}")
                if status_summary:
                    table.add_row("📈 Task Status:", " | ".join(status_summary))

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
