# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
DAG Visualization Module for Galaxy Framework

This module provides DAG topology visualization capabilities for TaskConstellation
with rich console output, focusing on structure, dependencies, and topology analysis.
"""

from collections import defaultdict
from typing import TYPE_CHECKING, List, Optional

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from rich.tree import Tree

if TYPE_CHECKING:
    from ..constellation.task_constellation import TaskConstellation

from ..constellation.enums import DependencyType, TaskStatus
from ..constellation.task_star import TaskStar
from .constellation_display import ConstellationDisplay
from .task_display import TaskDisplay


class DAGVisualizer:
    """
    DAG topology visualization for TaskConstellation.

    Focuses specifically on DAG structure, topology analysis, and dependency
    visualization. Event-specific displays are handled by separate display classes.
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the visualizer with optional console.

        :param console: Optional Rich Console instance for output
        """
        self.console = console or Console()
        self.task_display = TaskDisplay(console)
        self.constellation_display = ConstellationDisplay(console)

        # Status color mapping
        self.status_colors = {
            TaskStatus.PENDING: "yellow",
            TaskStatus.WAITING_DEPENDENCY: "orange1",
            TaskStatus.RUNNING: "blue",
            TaskStatus.COMPLETED: "green",
            TaskStatus.FAILED: "red",
            TaskStatus.CANCELLED: "dim",
        }

        # Dependency type symbols
        self.dependency_symbols = {
            DependencyType.UNCONDITIONAL: "→",
            DependencyType.SUCCESS_ONLY: "⇒",
            DependencyType.CONDITIONAL: "⇝",
            DependencyType.COMPLETION_ONLY: "⟶",
        }

    def display_constellation_overview(
        self,
        constellation: "TaskConstellation",
        title: str = "Task Constellation Overview",
    ) -> None:
        """
        Display comprehensive constellation overview using specialized display components.

        :param constellation: The TaskConstellation to visualize
        :param title: Custom title for the display
        """
        self.console.print()
        self.console.rule(f"[bold cyan]{title}[/bold cyan]")

        # Use constellation display for basic info and stats
        info_panel = self.constellation_display._create_basic_info_panel(
            constellation, title
        )
        stats_panel = self.constellation_display._create_basic_stats_panel(
            constellation
        )

        # Display side by side
        self.console.print(Columns([info_panel, stats_panel], equal=True))

        # DAG topology
        self.display_dag_topology(constellation)

        # Task details if not too many
        if constellation.task_count <= 20:
            self.display_task_details(constellation)

        # Dependency summary
        self.display_dependency_summary(constellation)

        self.console.print()

    def display_dag_topology(self, constellation: "TaskConstellation") -> None:
        """
        Display DAG topology in a visual tree structure.

        :param constellation: The TaskConstellation to visualize
        """
        self.console.print()
        self.console.print("[bold blue]📊 DAG Topology[/bold blue]")

        if constellation.task_count == 0:
            self.console.print("[dim]No tasks in constellation[/dim]")
            return

        # Build topology layers
        layers = self._build_topology_layers(constellation)

        if not layers:
            self.console.print(
                "[yellow]⚠️ No clear topology structure (possible cycles)[/yellow]"
            )
            return

        # Create tree visualization
        tree = Tree("🌌 [bold cyan]Task Constellation[/bold cyan]")

        for layer_idx, layer_tasks in enumerate(layers):
            layer_branch = tree.add(f"[dim]Layer {layer_idx + 1}[/dim]")

            for task in layer_tasks:
                task_text = self._format_task_for_tree(task)
                task_branch = layer_branch.add(task_text)

                # Add dependencies as sub-branches
                deps = constellation.get_task_dependencies(task.task_id)
                if deps:
                    dep_branch = task_branch.add("[dim]Dependencies:[/dim]")
                    for dep in deps:
                        dep_task = constellation.get_task(dep.from_task_id)
                        if dep_task:
                            # Only show task ID for dependencies
                            task_id_short = (
                                dep_task.task_id[:8] + "..."
                                if len(dep_task.task_id) > 8
                                else dep_task.task_id
                            )
                            status_icon = self.task_display.get_task_status_icon(
                                dep_task.status
                            )

                            # Add condition description if available
                            dep_text = f"⬅️ {status_icon} [cyan]{task_id_short}: [/cyan]"
                            if dep.condition_description:
                                condition_short = self._truncate_name(
                                    dep.condition_description, 50
                                )
                                dep_text += f" [dim]{condition_short}[/dim]"

                            dep_branch.add(dep_text)

        self.console.print(tree)

    def display_task_details(self, constellation: "TaskConstellation") -> None:
        """
        Display detailed task information in a table.

        :param constellation: The TaskConstellation to visualize
        """
        self.console.print()
        self.console.print("[bold blue]📋 Task Details[/bold blue]")

        table = Table(title="Task Information", box=box.ROUNDED)
        table.add_column("ID", style="cyan", no_wrap=True, width=12)
        table.add_column("Name", style="white", width=25)
        table.add_column("Status", justify="center", width=12)
        table.add_column("Priority", justify="center", width=8)
        table.add_column("Dependencies", style="yellow", width=15)
        table.add_column("Progress", justify="center", width=10)

        tasks = list(constellation.get_all_tasks())
        tasks.sort(key=lambda t: (t.status.value, t.task_id))

        for task in tasks:
            # Format task ID (show first 8 chars)
            task_id_short = (
                task.task_id[:8] + "..." if len(task.task_id) > 8 else task.task_id
            )

            # Task name with truncation
            task_name = task.name
            if len(task_name) > 22:
                task_name = task_name[:19] + "..."

            # Status with color and icon
            status_text = self._get_status_text(task.status)

            # Priority
            priority_value = (
                task.priority.value
                if hasattr(task.priority, "value")
                else task.priority
            )
            priority_text = (
                f"[{self._get_priority_color(task.priority)}]{priority_value}[/]"
            )

            # Dependencies count
            deps = constellation.get_task_dependencies(task.task_id)
            dep_count = len(deps) if deps else 0
            dep_text = f"{dep_count} deps" if dep_count > 0 else "[dim]none[/dim]"

            # Progress (if available)
            progress = "N/A"
            if hasattr(task, "progress") and task.progress is not None:
                progress = f"{task.progress:.0%}"
            elif task.status == TaskStatus.COMPLETED:
                progress = "100%"
            elif task.status == TaskStatus.RUNNING:
                progress = "..."

            table.add_row(
                task_id_short, task_name, status_text, priority_text, dep_text, progress
            )

        self.console.print(table)

    def display_dependency_summary(self, constellation: "TaskConstellation") -> None:
        """
        Display dependency relationships summary.

        :param constellation: The TaskConstellation to visualize
        """
        self.console.print()
        self.console.print("[bold blue]🔗 Dependency Relationships[/bold blue]")

        dependencies = constellation.get_all_dependencies()
        if not dependencies:
            self.console.print("[dim]No dependencies defined[/dim]")
            return

        # Group by dependency type
        dep_by_type = defaultdict(list)
        for dep in dependencies:
            dep_by_type[dep.dependency_type].append(dep)

        for dep_type, deps in dep_by_type.items():
            symbol = self.dependency_symbols.get(dep_type, "→")
            type_name = dep_type.value.replace("_", " ").title()

            panel_content = []
            for dep in deps[:10]:  # Limit to first 10 for readability
                from_task = constellation.get_task(dep.from_task_id)
                to_task = constellation.get_task(dep.to_task_id)

                if from_task and to_task:
                    from_name = self._truncate_name(from_task.name, 15)
                    to_name = self._truncate_name(to_task.name, 15)

                    # Status indicators
                    from_status = self._get_status_icon(from_task.status)
                    to_status = self._get_status_icon(to_task.status)

                    # Satisfaction status
                    satisfied = "✅" if dep.is_satisfied else "❌"

                    line = f"{from_status} {from_name} {symbol} {to_status} {to_name} {satisfied}"
                    panel_content.append(line)

            if len(deps) > 10:
                panel_content.append(f"[dim]... and {len(deps) - 10} more[/dim]")

            if panel_content:
                content = "\n".join(panel_content)
                panel = Panel(
                    content,
                    title=f"{symbol} {type_name} ({len(deps)})",
                    border_style="blue",
                    expand=False,
                )
                self.console.print(panel)

    def display_execution_flow(self, constellation: "TaskConstellation") -> None:
        """
        Display execution flow and ready tasks.

        :param constellation: The TaskConstellation to visualize
        """
        self.console.print()
        self.console.print("[bold blue]⚡ Execution Flow[/bold blue]")

        # Ready tasks
        ready_tasks = constellation.get_ready_tasks()
        running_tasks = constellation.get_running_tasks()
        completed_tasks = constellation.get_completed_tasks()
        failed_tasks = constellation.get_failed_tasks()

        # Create columns for different states
        columns = []

        if ready_tasks:
            ready_content = []
            for task in ready_tasks[:5]:  # Limit display
                ready_content.append(f"🟡 {self._truncate_name(task.name, 20)}")
            if len(ready_tasks) > 5:
                ready_content.append(f"[dim]... and {len(ready_tasks) - 5} more[/dim]")

            ready_panel = Panel(
                "\n".join(ready_content),
                title=f"Ready ({len(ready_tasks)})",
                border_style="yellow",
            )
            columns.append(ready_panel)

        if running_tasks:
            running_content = []
            for task in running_tasks:
                running_content.append(f"🔵 {self._truncate_name(task.name, 20)}")

            running_panel = Panel(
                "\n".join(running_content),
                title=f"Running ({len(running_tasks)})",
                border_style="blue",
            )
            columns.append(running_panel)

        if completed_tasks:
            completed_panel = Panel(
                f"✅ {len(completed_tasks)} tasks completed",
                title="Completed",
                border_style="green",
            )
            columns.append(completed_panel)

        if failed_tasks:
            failed_content = []
            for task in failed_tasks[:3]:  # Show first few failed tasks
                failed_content.append(f"❌ {self._truncate_name(task.name, 20)}")
            if len(failed_tasks) > 3:
                failed_content.append(
                    f"[dim]... and {len(failed_tasks) - 3} more[/dim]"
                )

            failed_panel = Panel(
                "\n".join(failed_content),
                title=f"Failed ({len(failed_tasks)})",
                border_style="red",
            )
            columns.append(failed_panel)

        if columns:
            self.console.print(Columns(columns, equal=True))
        else:
            self.console.print("[dim]No tasks in active execution states[/dim]")

    def _format_task_for_tree(self, task: TaskStar, compact: bool = False) -> str:
        """
        Format task for tree display.

        :param task: The TaskStar to format
        :param compact: Whether to use compact formatting
        :return: Formatted task string for tree display
        """
        name = self._truncate_name(task.name, 15 if compact else 50)
        status_icon = self.task_display.get_task_status_icon(task.status)
        priority_color = self._get_priority_color(task.priority)

        if compact:
            return f"{status_icon} [{priority_color}]{name}[/]"
        else:
            task_id_short = (
                task.task_id[:6] + "..." if len(task.task_id) > 8 else task.task_id
            )
            return f"{status_icon} [{priority_color}]{name}[/] [dim]({task_id_short})[/dim]"

    def _build_topology_layers(
        self, constellation: "TaskConstellation"
    ) -> List[List[TaskStar]]:
        """
        Build topology layers using topological sort.

        :param constellation: The TaskConstellation to build layers from
        :return: List of task layers in topological order
        """
        tasks = {task.task_id: task for task in constellation.get_all_tasks()}
        dependencies = constellation.get_all_dependencies()

        # Build adjacency list (reverse: dependents -> dependencies)
        graph = defaultdict(set)
        in_degree = defaultdict(int)

        # Initialize all tasks
        for task_id in tasks:
            in_degree[task_id] = 0

        # Build graph
        for dep in dependencies:
            graph[dep.from_task_id].add(dep.to_task_id)
            in_degree[dep.to_task_id] += 1

        # Topological sort with layers
        layers = []
        remaining_tasks = set(tasks.keys())

        while remaining_tasks:
            # Find tasks with no dependencies in current iteration
            current_layer = []
            for task_id in remaining_tasks:
                if in_degree[task_id] == 0:
                    current_layer.append(tasks[task_id])

            if not current_layer:
                # Cycle detected or no progress possible
                break

            layers.append(current_layer)

            # Remove current layer tasks and update in_degrees
            for task in current_layer:
                remaining_tasks.remove(task.task_id)
                for dependent_id in graph[task.task_id]:
                    in_degree[dependent_id] -= 1

        return layers

    def _get_status_text(self, status: TaskStatus) -> str:
        """
        Get formatted status text with color and icon.

        :param status: The TaskStatus to format
        :return: Formatted status text with color and icon
        """
        icon = self.task_display.get_task_status_icon(status)
        color = self.status_colors.get(status, "white")
        return f"[{color}]{icon} {status.value}[/]"

    def _get_priority_color(self, priority) -> str:
        """
        Get color for task priority.

        :param priority: The task priority value
        :return: Color string for the priority
        """
        # Assuming priority has a value attribute
        if hasattr(priority, "value"):
            if priority.value >= 8:
                return "red"
            elif priority.value >= 5:
                return "yellow"
            else:
                return "green"
        return "white"

    def _truncate_name(self, name: str, max_length: int) -> str:
        """
        Truncate name to max length.

        :param name: The name string to truncate
        :param max_length: Maximum length for the name
        :return: Truncated name string with ellipsis if needed
        """
        if len(name) <= max_length:
            return name
        return name[: max_length - 3] + "..."


def display_constellation_creation(
    constellation: "TaskConstellation", console: Optional[Console] = None
) -> None:
    """
    Display constellation when first created.

    :param constellation: Newly created TaskConstellation
    :param console: Optional console for output
    """
    display = ConstellationDisplay(console)
    display.display_constellation_started(
        constellation, {"status": "New constellation created"}
    )


def display_constellation_update(
    constellation: "TaskConstellation",
    change_description: str = "",
    console: Optional[Console] = None,
) -> None:
    """
    Display constellation after updates/modifications.

    :param constellation: Updated TaskConstellation
    :param change_description: Description of what changed
    :param console: Optional console for output
    """
    # For updates, we use the DAGVisualizer for full overview
    visualizer = DAGVisualizer(console)

    title = "🔄 Task Constellation Updated"
    if change_description:
        title += f" - {change_description}"

    visualizer.display_constellation_overview(constellation, title)


def display_execution_progress(
    constellation: "TaskConstellation", console: Optional[Console] = None
) -> None:
    """
    Display constellation execution progress.

    :param constellation: TaskConstellation in execution
    :param console: Optional console for output
    """
    visualizer = DAGVisualizer(console)
    visualizer.display_execution_flow(constellation)


# Convenience function for quick visualization
def visualize_dag(
    constellation: "TaskConstellation",
    mode: str = "overview",
    console: Optional[Console] = None,
) -> None:
    """
    Quick visualization of DAG.

    :param constellation: TaskConstellation to visualize
    :param mode: Visualization mode ('overview', 'topology', 'details', 'execution')
    :param console: Optional console for output
    """
    visualizer = DAGVisualizer(console)

    if mode == "overview":
        visualizer.display_constellation_overview(constellation)
    elif mode == "topology":
        visualizer.display_dag_topology(constellation)
    elif mode == "details":
        visualizer.display_task_details(constellation)
    elif mode == "execution":
        visualizer.display_execution_flow(constellation)
    else:
        visualizer.display_constellation_overview(constellation)
