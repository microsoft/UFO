# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task-specific visualization handler.
"""

import logging
from typing import Optional

from ...core.events import TaskEvent, EventType
from ...constellation import TaskConstellation


class TaskVisualizationHandler:
    """
    Specialized handler for task-related visualization events.

    This class encapsulates all task visualization logic, including
    task start, completion, and failure displays with Rich formatting.
    """

    def __init__(self, visualizer, logger: Optional[logging.Logger] = None):
        """
        Initialize TaskVisualizationHandler.

        :param visualizer: DAGVisualizer instance for rendering
        :param logger: Optional logger instance
        """
        self._visualizer = visualizer
        self.logger = logger or logging.getLogger(__name__)

    async def handle_task_started(
        self, event: TaskEvent, constellation: TaskConstellation
    ) -> None:
        """
        Handle task started visualization with enhanced display.

        :param event: TaskEvent instance
        :param constellation: TaskConstellation containing the task
        """
        try:
            # Get task info
            task_id = event.task_id
            task = constellation.get_task(task_id) if task_id else None

            if task:
                # Beautiful task started display
                from rich.panel import Panel
                from rich.text import Text

                # Create task info text
                task_info = Text()
                task_info.append("🚀 ", style="bold green")
                task_info.append(f"Task Started: ", style="bold blue")
                task_info.append(f"{task.name}", style="bold yellow")
                task_info.append(f" ({task_id})", style="dim")

                # Additional details
                details = []
                if task.target_device_id:
                    details.append(f"📱 Device: {task.target_device_id}")
                if task.priority:
                    details.append(f"⭐ Priority: {task.priority.name}")
                if task.description:
                    details.append(f"📝 {task.description[:50]}...")

                detail_text = "\n".join(details) if details else "No additional details"

                # Create panel
                panel = Panel(
                    f"{task_info}\n\n{detail_text}",
                    title="[bold green]🎯 Task Execution Started[/bold green]",
                    border_style="green",
                    width=80,
                )

                self._visualizer.console.print(panel)

            # Show topology for smaller constellations
            if constellation.task_count <= 10:
                self._visualizer.display_dag_topology(constellation)

        except Exception as e:
            self.logger.debug(f"Error displaying task start: {e}")

    async def handle_task_completed(
        self, event: TaskEvent, constellation: TaskConstellation
    ) -> None:
        """
        Handle task completion visualization with enhanced display.

        :param event: TaskEvent instance
        :param constellation: TaskConstellation containing the task
        """
        try:
            # Get task info
            task_id = event.task_id
            task = constellation.get_task(task_id) if task_id else None

            if task:
                # Beautiful task completion display
                from rich.panel import Panel
                from rich.text import Text
                from rich.table import Table
                from rich.console import Group

                # Create success message
                success_text = Text()
                success_text.append("✅ ", style="bold green")
                success_text.append(f"Task Completed: ", style="bold green")
                success_text.append(f"{task.name}", style="bold yellow")
                success_text.append(f" ({task_id})", style="dim")

                # Create details table
                table = Table(show_header=False, show_edge=False, padding=0)
                table.add_column("Key", style="cyan", width=15)
                table.add_column("Value", style="white")

                # Add task details
                if task.execution_duration:
                    table.add_row("⏱️ Duration:", f"{task.execution_duration:.2f}s")
                if task.target_device_id:
                    table.add_row("📱 Device:", task.target_device_id)
                if hasattr(event, "result") and event.result:
                    result_preview = (
                        str(event.result)[:50] + "..."
                        if len(str(event.result)) > 50
                        else str(event.result)
                    )
                    table.add_row("📊 Result:", result_preview)

                # Show newly ready tasks
                newly_ready = (
                    event.data.get("newly_ready_tasks", []) if event.data else []
                )
                if newly_ready:
                    table.add_row("🎯 Unlocked:", f"{len(newly_ready)} new tasks ready")

                # Create panel with proper Rich composition
                content = Group(success_text, "", table)

                panel = Panel(
                    content,
                    title="[bold green]🎉 Task Execution Completed[/bold green]",
                    border_style="green",
                    width=80,
                )

                self._visualizer.console.print(panel)

            # Show execution progress for smaller constellations
            if constellation.task_count <= 10:
                self._visualizer.display_execution_flow(constellation)

        except Exception as e:
            self.logger.debug(f"Error displaying task completion: {e}")

    async def handle_task_failed(
        self, event: TaskEvent, constellation: TaskConstellation
    ) -> None:
        """
        Handle task failure visualization with enhanced display.

        :param event: TaskEvent instance
        :param constellation: TaskConstellation containing the task
        """
        try:
            # Get task info
            task_id = event.task_id
            task = constellation.get_task(task_id) if task_id else None

            if task:
                # Beautiful task failure display
                from rich.panel import Panel
                from rich.text import Text
                from rich.table import Table
                from rich.console import Group

                # Create failure message
                failure_text = Text()
                failure_text.append("❌ ", style="bold red")
                failure_text.append(f"Task Failed: ", style="bold red")
                failure_text.append(f"{task.name}", style="bold yellow")
                failure_text.append(f" ({task_id})", style="dim")

                # Create details table
                table = Table(show_header=False, show_edge=False, padding=0)
                table.add_column("Key", style="cyan", width=15)
                table.add_column("Value", style="white")

                # Add task details
                if task.target_device_id:
                    table.add_row("📱 Device:", task.target_device_id)
                if task.retry_count and task.current_retry:
                    table.add_row(
                        "🔄 Retries:", f"{task.current_retry}/{task.retry_count}"
                    )

                # Show error information
                if hasattr(event, "error") and event.error:
                    error_msg = (
                        str(event.error)[:100] + "..."
                        if len(str(event.error)) > 100
                        else str(event.error)
                    )
                    table.add_row("⚠️ Error:", error_msg)

                # Show impact on ready tasks
                newly_ready = (
                    event.data.get("newly_ready_tasks", []) if event.data else []
                )
                if newly_ready:
                    table.add_row(
                        "🎯 Unlocked:", f"{len(newly_ready)} tasks still ready"
                    )

                # Create panel with proper Rich composition
                content = Group(failure_text, "", table)

                panel = Panel(
                    content,
                    title="[bold red]💥 Task Execution Failed[/bold red]",
                    border_style="red",
                    width=80,
                )

                self._visualizer.console.print(panel)

            # Always show failure status regardless of constellation size
            self._visualizer.display_execution_flow(constellation)

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
