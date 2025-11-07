# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation result formatter for beautiful and structured display.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import box
from rich.text import Text


class ConstellationFormatter:
    """Formatter for displaying constellation execution results in a structured way."""

    def __init__(self):
        self.console = Console()

    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable format."""
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.2f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.2f}s"

    def format_timestamp(self, timestamp: str) -> str:
        """Format ISO timestamp to readable format."""
        try:
            dt = datetime.fromisoformat(timestamp.replace("+00:00", ""))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return timestamp

    def create_overview_table(self, data: Dict[str, Any]) -> Table:
        """Create overview information table."""
        table = Table(
            title="📊 Constellation Overview",
            box=box.ROUNDED,
            show_header=False,
            title_style="bold cyan",
        )

        table.add_column("Property", style="bold yellow", width=25)
        table.add_column("Value", style="green")

        # Basic info
        table.add_row("ID", data.get("id", "N/A"))
        table.add_row("Name", data.get("name", "N/A"))
        table.add_row(
            "State", f"[bold green]✅ {data.get('state', 'N/A').upper()}[/bold green]"
        )

        # Timeline
        if "created" in data:
            table.add_row("Created", data["created"])
        if "started" in data:
            table.add_row("Started", data["started"])
        if "ended" in data:
            table.add_row("Ended", data["ended"])

        # Task info
        table.add_row("Total Tasks", str(data.get("total_tasks", 0)))
        table.add_row(
            "Execution Duration",
            self.format_duration(data.get("execution_duration", 0)),
        )

        return table

    def create_statistics_table(self, stats: Dict[str, Any]) -> Table:
        """Create detailed statistics table."""
        table = Table(
            title="📈 Performance Metrics", box=box.ROUNDED, title_style="bold magenta"
        )

        table.add_column("Metric", style="bold cyan", width=30)
        table.add_column("Value", style="yellow", justify="right")

        # Task statistics
        if "total_tasks" in stats:
            table.add_row("Total Tasks", str(stats["total_tasks"]))

        if "total_dependencies" in stats:
            table.add_row("Total Dependencies", str(stats["total_dependencies"]))

        # Task status breakdown
        if "task_status_counts" in stats:
            status_counts = stats["task_status_counts"]
            for status, count in status_counts.items():
                table.add_row(f"  • {status.capitalize()}", str(count))

        # Performance metrics
        if "critical_path_length" in stats:
            table.add_row(
                "Critical Path Length",
                self.format_duration(stats["critical_path_length"]),
            )

        if "total_work" in stats:
            table.add_row("Total Work Time", self.format_duration(stats["total_work"]))

        if "parallelism_ratio" in stats:
            table.add_row("Parallelism Ratio", f"{stats['parallelism_ratio']:.2f}x")

        if "execution_duration" in stats:
            table.add_row(
                "Execution Duration", self.format_duration(stats["execution_duration"])
            )

        # Path metrics
        if "longest_path_length" in stats:
            table.add_row("Longest Path Length", str(stats["longest_path_length"]))

        if "max_width" in stats:
            table.add_row("Max Width (Parallelism)", str(stats["max_width"]))

        return table

    def create_critical_path_panel(self, stats: Dict[str, Any]) -> Optional[Panel]:
        """Create critical path information panel."""
        critical_tasks = stats.get("critical_path_tasks", [])

        if not critical_tasks:
            return None

        content = Text()
        content.append("🎯 Critical Path Tasks:\n", style="bold")
        for task in critical_tasks:
            content.append(f"  • {task}\n", style="cyan")

        return Panel(
            content,
            title="Critical Path Analysis",
            border_style="yellow",
            box=box.ROUNDED,
        )

    def display_constellation_result(self, constellation_data: Dict[str, Any]):
        """
        Display constellation execution result in a beautiful structured format.

        Args:
            constellation_data: Dictionary containing constellation execution data
        """
        self.console.print("\n")

        # Header
        header = Panel(
            Text(
                "✅ Constellation Execution Completed",
                justify="center",
                style="bold green",
            ),
            box=box.DOUBLE,
            style="green",
        )
        self.console.print(header)

        # Overview table
        overview = self.create_overview_table(constellation_data)
        self.console.print(overview)
        self.console.print()

        # Statistics table
        if "statistics" in constellation_data:
            stats_table = self.create_statistics_table(constellation_data["statistics"])
            self.console.print(stats_table)
            self.console.print()

            # Critical path panel
            critical_panel = self.create_critical_path_panel(
                constellation_data["statistics"]
            )
            if critical_panel:
                self.console.print(critical_panel)
                self.console.print()

        # Constellation summary
        if "constellation" in constellation_data:
            summary = Panel(
                Text(constellation_data["constellation"], style="cyan"),
                title="📦 Constellation Summary",
                border_style="blue",
                box=box.ROUNDED,
            )
            self.console.print(summary)

        self.console.print("\n")


def format_constellation_result(result_data: Dict[str, Any]):
    """
    Utility function to format and display constellation result.

    Args:
        result_data: Dictionary containing constellation execution data

    Example usage:
        >>> data = {
        ...     'id': 'constellation_8a657000_20251107_225225',
        ...     'name': 'constellation_8a657000_20251107_225225',
        ...     'state': 'completed',
        ...     'created': '14:52:25',
        ...     'started': '14:52:26',
        ...     'ended': '14:52:51',
        ...     'total_tasks': 3,
        ...     'execution_duration': 24.953522,
        ...     'statistics': {...}
        ... }
        >>> format_constellation_result(data)
    """
    formatter = ConstellationFormatter()
    formatter.display_constellation_result(result_data)


if __name__ == "__main__":
    # Example data
    example_data = {
        "id": "constellation_8a657000_20251107_225225",
        "name": "constellation_8a657000_20251107_225225",
        "state": "completed",
        "created": "14:52:25",
        "started": "14:52:26",
        "ended": "14:52:51",
        "total_tasks": 3,
        "execution_duration": 24.953522,
        "statistics": {
            "constellation_id": "constellation_8a657000_20251107_225225",
            "name": "constellation_8a657000_20251107_225225",
            "state": "completed",
            "total_tasks": 3,
            "total_dependencies": 0,
            "task_status_counts": {"completed": 3},
            "longest_path_length": 1,
            "longest_path_tasks": [],
            "max_width": 3,
            "critical_path_length": 7.643585,
            "total_work": 21.733924,
            "parallelism_ratio": 2.84342020138456,
            "parallelism_calculation_mode": "actual_time",
            "critical_path_tasks": ["task-2"],
            "execution_duration": 24.953522,
            "created_at": "2025-11-07T14:52:25.985927+00:00",
            "updated_at": "2025-11-07T14:52:51.071804+00:00",
        },
        "constellation": "TaskConstellation(id=constellation_8a657000_20251107_225225, tasks=3, state=completed)",
    }

    format_constellation_result(example_data)
