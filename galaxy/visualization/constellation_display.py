# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation-specific visualization display components.

This module provides specialized display functionality for constellation-related
visualizations with rich console output, including structure changes,
statistics, and state transitions.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from ..constellation.task_constellation import TaskConstellation

from ..constellation.enums import ConstellationState


class ConstellationDisplay:
    """
    Specialized display components for constellation visualization.

    Provides reusable, modular components for displaying constellation information
    with consistent Rich formatting across different contexts.
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize ConstellationDisplay.

        :param console: Optional Rich Console instance for output
        """
        self.console = console or Console()

    def display_constellation_started(
        self,
        constellation: "TaskConstellation",
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Display constellation start notification.

        :param constellation: TaskConstellation that started
        :param additional_info: Optional additional information
        """
        # Create constellation info
        info_panel = self._create_basic_info_panel(
            constellation, "🚀 Constellation Started", additional_info
        )

        # Create basic stats
        stats_panel = self._create_basic_stats_panel(constellation)

        # Display side by side
        self.console.print()
        self.console.rule("[bold cyan]🚀 Constellation Started[/bold cyan]")
        self.console.print(Columns([info_panel, stats_panel], equal=True))

    def display_constellation_completed(
        self,
        constellation: "TaskConstellation",
        execution_time: Optional[float] = None,
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Display constellation completion notification with enhanced formatting.

        :param constellation: TaskConstellation that completed
        :param execution_time: Total execution time in seconds
        :param additional_info: Optional additional information
        """
        from .constellation_formatter import ConstellationFormatter

        # Prepare data for the formatter
        stats = (
            constellation.get_statistics()
            if hasattr(constellation, "get_statistics")
            else {}
        )

        constellation_data = {
            "id": constellation.constellation_id,
            "name": constellation.name or constellation.constellation_id,
            "state": (
                constellation.state.value
                if hasattr(constellation.state, "value")
                else str(constellation.state)
            ),
            "total_tasks": (
                len(constellation.tasks) if hasattr(constellation, "tasks") else 0
            ),
            "execution_duration": execution_time or 0,
            "statistics": stats,
            "constellation": str(constellation),
        }

        # Add timing information if available
        if hasattr(constellation, "created_at") and constellation.created_at:
            constellation_data["created"] = constellation.created_at.strftime(
                "%H:%M:%S"
            )

        if (
            hasattr(constellation, "execution_start_time")
            and constellation.execution_start_time
        ):
            constellation_data["started"] = constellation.execution_start_time.strftime(
                "%H:%M:%S"
            )

        if (
            hasattr(constellation, "execution_end_time")
            and constellation.execution_end_time
        ):
            constellation_data["ended"] = constellation.execution_end_time.strftime(
                "%H:%M:%S"
            )

        # Merge additional info
        if additional_info:
            constellation_data.update(additional_info)

        # Use the new formatter to display
        formatter = ConstellationFormatter()
        formatter.display_constellation_result(constellation_data)

    def display_constellation_failed(
        self,
        constellation: "TaskConstellation",
        error: Optional[Exception] = None,
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Display constellation failure notification.

        :param constellation: TaskConstellation that failed
        :param error: Exception that caused the failure
        :param additional_info: Optional additional information
        """
        # Enhance additional info with error
        enhanced_info = additional_info.copy() if additional_info else {}
        if error:
            enhanced_info["error"] = str(error)[:100]

        # Create failure info
        info_panel = self._create_basic_info_panel(
            constellation, "❌ Constellation Failed", enhanced_info
        )

        # Create stats with failure emphasis
        stats_panel = self._create_basic_stats_panel(constellation)

        # Display with error styling
        self.console.print()
        self.console.rule("[bold red]❌ Constellation Failed[/bold red]")
        self.console.print(Columns([info_panel, stats_panel], equal=True))

    def display_constellation_modified(
        self,
        constellation: "TaskConstellation",
        changes: Dict[str, Any],
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Display constellation modification notification with change details.

        :param constellation: Modified TaskConstellation
        :param changes: Dictionary containing detected changes
        :param additional_info: Optional additional information
        """
        # Create modification message
        mod_text = Text()
        mod_text.append("🔄 ", style="bold blue")
        mod_text.append(f"Constellation Modified: ", style="bold blue")
        mod_text.append(f"{constellation.name}", style="bold yellow")
        mod_text.append(f" ({constellation.constellation_id[:8]}...)", style="dim")

        # Create details table for changes
        table = Table(show_header=False, show_edge=False, padding=0)
        table.add_column("Key", style="cyan", width=20)
        table.add_column(
            "Value", width=50
        )  # Remove default white style to allow individual coloring

        # Add calculated modification details
        if changes.get("modification_type"):
            mod_type = changes["modification_type"].replace("_", " ").title()
            table.add_row("🔧 Change Type:", f"[bold blue]{mod_type}[/bold blue]")

        self._add_change_details_to_table(table, changes)
        self._add_constellation_stats_to_table(table, constellation)

        # Add additional info if provided
        if additional_info:
            for key, value in additional_info.items():
                if value is not None:
                    table.add_row(f"ℹ️ {key.title()}:", f"[cyan]{value}[/cyan]")

        # Create panel with proper Rich composition
        content = Group(mod_text, "", table)

        panel = Panel(
            content,
            title="[bold blue]⚙️ Constellation Structure Updated[/bold blue]",
            border_style="blue",
            width=80,
        )

        self.console.print(panel)

    def _create_basic_info_panel(
        self,
        constellation: "TaskConstellation",
        title: str,
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> Panel:
        """
        Create basic constellation information panel.

        :param constellation: TaskConstellation to display info for
        :param title: Panel title
        :param additional_info: Optional additional information
        :return: Rich Panel with constellation information
        """
        info_lines = [
            f"[bold]ID:[/bold] {constellation.constellation_id[:12]}...",
            f"[bold]Name:[/bold] {constellation.name or 'Unnamed'}",
            f"[bold]State:[/bold] {self._get_state_text(constellation.state)}",
        ]

        # Add timing information if available
        if hasattr(constellation, "created_at") and constellation.created_at:
            info_lines.append(
                f"[bold]Created:[/bold] {constellation.created_at.strftime('%H:%M:%S')}"
            )

        if (
            hasattr(constellation, "execution_start_time")
            and constellation.execution_start_time
        ):
            info_lines.append(
                f"[bold]Started:[/bold] {constellation.execution_start_time.strftime('%H:%M:%S')}"
            )

        if (
            hasattr(constellation, "execution_end_time")
            and constellation.execution_end_time
        ):
            info_lines.append(
                f"[bold]Ended:[/bold] {constellation.execution_end_time.strftime('%H:%M:%S')}"
            )

        # Add additional info if provided
        if additional_info:
            for key, value in additional_info.items():
                if value is not None:
                    formatted_key = key.replace("_", " ").title()
                    info_lines.append(f"[bold]{formatted_key}:[/bold] {value}")

        return Panel("\n".join(info_lines), title=f"📊 {title}", border_style="cyan")

    def _create_basic_stats_panel(self, constellation: "TaskConstellation") -> Panel:
        """
        Create basic constellation statistics panel.

        :param constellation: TaskConstellation to extract statistics from
        :return: Rich Panel with constellation statistics
        """
        stats = self._get_constellation_statistics(constellation)

        stats_lines = [
            f"[bold]Total Tasks:[/bold] {stats['total_tasks']}",
            f"[bold]Dependencies:[/bold] {stats['total_dependencies']}",
            f"[green]✅ Completed:[/green] {stats['completed_tasks']}",
            f"[blue]🔵 Running:[/blue] {stats['running_tasks']}",
            f"[yellow]🟡 Ready:[/yellow] {stats['ready_tasks']}",
            f"[red]❌ Failed:[/red] {stats['failed_tasks']}",
        ]

        if stats.get("success_rate") is not None:
            stats_lines.append(
                f"[bold]Success Rate:[/bold] {stats['success_rate']:.1%}"
            )

        return Panel(
            "\n".join(stats_lines), title="📈 Statistics", border_style="green"
        )

    def _add_change_details_to_table(
        self, table: Table, changes: Dict[str, Any]
    ) -> None:
        """
        Add change details to a Rich table.

        :param table: Rich Table instance to add rows to
        :param changes: Dictionary containing detected changes
        """
        if changes.get("added_tasks"):
            count = len(changes["added_tasks"])
            table.add_row("➕ Tasks Added:", f"[green]{count} new tasks[/green]")
            # Show task names if not too many
            if count <= 3:
                task_names = ", ".join(
                    [
                        t[:10] + "..." if len(t) > 10 else t
                        for t in changes["added_tasks"]
                    ]
                )
                table.add_row("", f"[dim]({task_names})[/dim]")

        if changes.get("removed_tasks"):
            count = len(changes["removed_tasks"])
            table.add_row("➖ Tasks Removed:", f"[red]{count} tasks[/red]")
            # Show task names if not too many
            if count <= 3:
                task_names = ", ".join(
                    [
                        t[:10] + "..." if len(t) > 10 else t
                        for t in changes["removed_tasks"]
                    ]
                )
                table.add_row("", f"[dim]({task_names})[/dim]")

        if changes.get("added_dependencies"):
            table.add_row(
                "🔗 Deps Added:",
                f"[green]{len(changes['added_dependencies'])} links[/green]",
            )

        if changes.get("removed_dependencies"):
            table.add_row(
                "🔗 Deps Removed:",
                f"[red]{len(changes['removed_dependencies'])} links[/red]",
            )

        if changes.get("modified_tasks"):
            table.add_row(
                "📝 Tasks Modified:",
                f"[yellow]{len(changes['modified_tasks'])} tasks updated[/yellow]",
            )

    def _add_constellation_stats_to_table(
        self, table: Table, constellation: "TaskConstellation"
    ) -> None:
        """
        Add constellation statistics to the details table.

        :param table: Rich Table instance to add rows to
        :param constellation: TaskConstellation instance for statistics
        """
        stats = self._get_constellation_statistics(constellation)

        table.add_row(
            "📊 Total Tasks:", f"[bold white]{stats['total_tasks']}[/bold white]"
        )
        table.add_row(
            "🔗 Total Deps:", f"[bold white]{stats['total_dependencies']}[/bold white]"
        )

        # Task status breakdown
        status_summary = []
        if stats["completed_tasks"] > 0:
            status_summary.append(f"[green]✅ {stats['completed_tasks']}[/green]")
        if stats["running_tasks"] > 0:
            status_summary.append(f"[blue]🔵 {stats['running_tasks']}[/blue]")
        if stats["ready_tasks"] > 0:
            status_summary.append(f"[yellow]🟡 {stats['ready_tasks']}[/yellow]")
        if stats["failed_tasks"] > 0:
            status_summary.append(f"[red]❌ {stats['failed_tasks']}[/red]")

        if status_summary:
            table.add_row("📈 Task Status:", " | ".join(status_summary))

    def _get_constellation_statistics(
        self, constellation: "TaskConstellation"
    ) -> Dict[str, Any]:
        """
        Extract and normalize constellation statistics.

        :param constellation: TaskConstellation to extract statistics from
        :return: Normalized statistics dictionary
        """
        # Try to get statistics from constellation
        if hasattr(constellation, "get_statistics"):
            stats = constellation.get_statistics()

            # Handle different statistics formats
            if "task_status_counts" in stats:
                # Format from real TaskConstellation
                status_counts = stats["task_status_counts"]
                return {
                    "total_tasks": stats["total_tasks"],
                    "total_dependencies": stats["total_dependencies"],
                    "completed_tasks": status_counts.get("completed", 0),
                    "failed_tasks": status_counts.get("failed", 0),
                    "running_tasks": status_counts.get("running", 0),
                    "ready_tasks": self._get_ready_task_count(constellation),
                    "success_rate": self._calculate_success_rate(status_counts),
                }
            else:
                # Format from simple test constellation
                return {
                    "total_tasks": stats.get("total_tasks", 0),
                    "total_dependencies": stats.get("total_dependencies", 0),
                    "completed_tasks": stats.get("completed_tasks", 0),
                    "failed_tasks": stats.get("failed_tasks", 0),
                    "running_tasks": stats.get("running_tasks", 0),
                    "ready_tasks": stats.get("ready_tasks", 0),
                    "success_rate": stats.get("success_rate"),
                }
        else:
            # Fallback: calculate from constellation directly
            return self._calculate_basic_statistics(constellation)

    def _get_ready_task_count(self, constellation: "TaskConstellation") -> int:
        """
        Get count of ready tasks.

        :param constellation: TaskConstellation to check
        :return: Number of ready tasks
        """
        try:
            return len(constellation.get_ready_tasks())
        except AttributeError:
            return 0

    def _calculate_success_rate(self, status_counts: Dict[str, int]) -> Optional[float]:
        """
        Calculate success rate from status counts.

        :param status_counts: Dictionary of task status counts
        :return: Success rate as float or None if no terminal tasks
        """
        completed = status_counts.get("completed", 0)
        failed = status_counts.get("failed", 0)
        total_terminal = completed + failed

        return completed / total_terminal if total_terminal > 0 else None

    def _calculate_basic_statistics(
        self, constellation: "TaskConstellation"
    ) -> Dict[str, Any]:
        """
        Calculate basic statistics directly from constellation.

        :param constellation: TaskConstellation to analyze
        :return: Basic statistics dictionary
        """
        # This is a fallback method for constellations without get_statistics
        tasks = getattr(constellation, "tasks", {})
        dependencies = getattr(constellation, "dependencies", {})

        return {
            "total_tasks": len(tasks),
            "total_dependencies": len(dependencies),
            "completed_tasks": 0,
            "failed_tasks": 0,
            "running_tasks": 0,
            "ready_tasks": 0,
            "success_rate": None,
        }

    def _get_state_text(self, state: ConstellationState) -> str:
        """
        Get formatted constellation state text.

        :param state: ConstellationState to format
        :return: Formatted state text with color
        """
        state_colors = {
            ConstellationState.CREATED: "yellow",
            ConstellationState.READY: "blue",
            ConstellationState.EXECUTING: "blue",
            ConstellationState.COMPLETED: "green",
            ConstellationState.FAILED: "red",
            ConstellationState.PARTIALLY_FAILED: "orange1",
        }
        color = state_colors.get(state, "white")
        return f"[{color}]{state.value.upper()}[/]"
