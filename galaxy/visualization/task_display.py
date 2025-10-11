# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task-specific visualization display components.

This module provides specialized display functionality for task-related
visualizations with rich console output, including status indicators,
progress tracking, and detailed task information.
"""

from typing import Any, Dict, Optional

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from galaxy.core.types import ExecutionResult

from ..constellation.enums import TaskStatus
from ..constellation.task_star import TaskStar


class TaskDisplay:
    """
    Specialized display components for task visualization.

    Provides reusable, modular components for displaying task information
    with consistent Rich formatting across different contexts.
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize TaskDisplay.

        :param console: Optional Rich Console instance for output
        """
        self.console = console or Console()

    def display_task_started(
        self, task: TaskStar, additional_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Display task start notification with enhanced formatting.

        :param task: TaskStar instance that started
        :param additional_info: Optional additional information to display
        """
        # Create task info text
        task_info = Text()
        task_info.append("🚀 ", style="bold green")
        task_info.append(f"Task Started: ", style="bold blue")
        task_info.append(f"{task.name}", style="bold yellow")
        task_info.append(f" ({task.task_id[:8]}...)", style="dim")

        # Additional details
        details = self._format_task_details(task, additional_info)

        # Create panel
        panel = Panel(
            f"{task_info}\n\n{details}",
            title="[bold green]🎯 Task Execution Started[/bold green]",
            border_style="green",
            width=80,
        )

        self.console.print(panel)

    def display_task_completed(
        self,
        task: TaskStar,
        execution_time: Optional[float] = None,
        result: Optional[Any] = None,
        newly_ready_tasks: Optional[int] = None,
    ) -> None:
        """
        Display task completion notification with results.

        :param task: TaskStar instance that completed
        :param execution_time: Task execution duration in seconds
        :param result: Task execution result
        :param newly_ready_tasks: Number of newly ready tasks
        """
        # Create success message
        success_text = Text()
        success_text.append("✅ ", style="bold green")
        success_text.append(f"Task Completed: ", style="bold green")
        success_text.append(f"{task.name}", style="bold yellow")
        success_text.append(f" ({task.task_id[:8]}...)", style="dim")

        # Create details table
        table = Table(show_header=False, show_edge=False, padding=0)
        table.add_column("Key", style="cyan", width=15)
        table.add_column("Value", style="white")

        # Add execution details
        if execution_time is not None:
            table.add_row("⏱️ Duration:", f"{execution_time:.2f}s")
        elif hasattr(task, "execution_duration") and task.execution_duration:
            table.add_row("⏱️ Duration:", f"{task.execution_duration:.2f}s")

        if task.target_device_id:
            table.add_row("📱 Device:", task.target_device_id)

        if result is not None:
            if isinstance(result, ExecutionResult):
                result_text = result.result
                result_preview = (
                    str(result_text)[:100] + "..."
                    if len(str(result_text)) > 100
                    else str(result_text)
                )

            else:
                result_preview = (
                    str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
                )
            table.add_row("📊 Result:", result_preview)

        if newly_ready_tasks is not None and newly_ready_tasks > 0:
            table.add_row("🎯 Unlocked:", f"{newly_ready_tasks} new tasks ready")

        # Create panel with proper Rich composition
        content = Group(success_text, "", table)

        panel = Panel(
            content,
            title="[bold green]🎉 Task Execution Completed[/bold green]",
            border_style="green",
            width=80,
        )

        self.console.print(panel)

    def display_task_failed(
        self,
        task: TaskStar,
        error: Optional[Exception] = None,
        retry_info: Optional[Dict[str, int]] = None,
        newly_ready_tasks: Optional[int] = None,
    ) -> None:
        """
        Display task failure notification with error details.

        :param task: TaskStar instance that failed
        :param error: Exception that caused the failure
        :param retry_info: Dictionary with current_retry and max_retries
        :param newly_ready_tasks: Number of tasks still ready despite failure
        """
        # Create failure message
        failure_text = Text()
        failure_text.append("❌ ", style="bold red")
        failure_text.append(f"Task Failed: ", style="bold red")
        failure_text.append(f"{task.name}", style="bold yellow")
        failure_text.append(f" ({task.task_id[:8]}...)", style="dim")

        # Create details table
        table = Table(show_header=False, show_edge=False, padding=0)
        table.add_column("Key", style="cyan", width=15)
        table.add_column("Value", style="white")

        # Add task details
        if task.target_device_id:
            table.add_row("📱 Device:", task.target_device_id)

        # Retry information
        if retry_info:
            current = retry_info.get("current_retry", 0)
            maximum = retry_info.get("max_retries", 0)
            table.add_row("🔄 Retries:", f"{current}/{maximum}")
        elif hasattr(task, "current_retry") and hasattr(task, "retry_count"):
            table.add_row("🔄 Retries:", f"{task.current_retry}/{task.retry_count}")

        # Show error information
        if error:
            error_msg = (
                str(error)[:100] + "..." if len(str(error)) > 100 else str(error)
            )
            table.add_row("⚠️ Error:", error_msg)

        # Show impact on ready tasks
        if newly_ready_tasks is not None and newly_ready_tasks > 0:
            table.add_row("🎯 Still Ready:", f"{newly_ready_tasks} tasks")

        # Create panel with proper Rich composition
        content = Group(failure_text, "", table)

        panel = Panel(
            content,
            title="[bold red]💥 Task Execution Failed[/bold red]",
            border_style="red",
            width=80,
        )

        self.console.print(panel)

    def _format_task_details(
        self, task: TaskStar, additional_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format task details for display.

        :param task: TaskStar instance to format
        :param additional_info: Optional additional information
        :return: Formatted details string
        """
        details = []

        if task.target_device_id:
            details.append(f"📱 Device: {task.target_device_id}")

        if hasattr(task, "priority") and task.priority:
            priority_name = getattr(task.priority, "name", str(task.priority))
            details.append(f"⭐ Priority: {priority_name}")

        if task.description:
            description = (
                task.description[:50] + "..."
                if len(task.description) > 50
                else task.description
            )
            details.append(f"📝 {description}")

        # Add any additional information
        if additional_info:
            for key, value in additional_info.items():
                if value is not None:
                    details.append(f"ℹ️ {key}: {value}")

        return "\n".join(details) if details else "No additional details"

    def get_task_status_icon(self, status: TaskStatus) -> str:
        """
        Get status icon for a task.

        :param status: TaskStatus to get icon for
        :return: Unicode icon string
        """
        icons = {
            TaskStatus.PENDING: "⭕",
            TaskStatus.WAITING_DEPENDENCY: "⏳",
            TaskStatus.RUNNING: "🔵",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.CANCELLED: "⭕",
        }
        return icons.get(status, "❓")

    def format_task_summary(self, task: TaskStar, include_id: bool = True) -> str:
        """
        Format a brief task summary for inline display.

        :param task: TaskStar to summarize
        :param include_id: Whether to include task ID
        :return: Formatted summary string
        """
        status_icon = self.get_task_status_icon(task.status)
        name = task.name[:20] + "..." if len(task.name) > 20 else task.name

        if include_id:
            task_id_short = (
                task.task_id[:6] + "..." if len(task.task_id) > 8 else task.task_id
            )
            return f"{status_icon} {name} ({task_id_short})"
        else:
            return f"{status_icon} {name}"
