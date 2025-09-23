# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Observer classes for constellation events.
"""

import logging
from typing import Any, Dict,  Optional

from ..core.events import (
    Event,
    EventType,
    TaskEvent,
    ConstellationEvent,
    IEventObserver,
)
from ..constellation import TaskConstellation
from ..constellation.task_star_line import TaskStarLine
from ..agents.constellation_agent import ConstellationAgent
from ufo.module.context import Context


class ConstellationProgressObserver(IEventObserver):
    """
    Observer that handles constellation progress updates.

    This replaces the complex callback logic in GalaxyRound.
    """

    def __init__(self, agent: ConstellationAgent, context: Context):
        """
        Initialize ConstellationProgressObserver.

        :param agent: ConstellationAgent instance for task coordination
        :param context: Context object for the session
        """
        self.agent = agent
        self.context = context
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
            self.logger.info(f"Task progress: {event.task_id} -> {event.status}")

            # Store task result
            self.task_results[event.task_id] = {
                "task_id": event.task_id,
                "status": event.status,
                "result": event.result,
                "error": event.error,
                "timestamp": event.timestamp,
            }

            # Put event into agent's queue - this will wake up the Continue state
            await self.agent.task_completion_queue.put(event)

            self.logger.info(
                f"Queued task completion: {event.task_id} -> {event.status}"
            )

        except Exception as e:
            self.logger.error(f"Error handling task event: {e}")

    async def _handle_constellation_event(self, event: ConstellationEvent) -> None:
        """
        Handle constellation update events - now handled by agent state machine.

        :param event: ConstellationEvent instance containing constellation updates
        """
        try:
            if (
                event.event_type == EventType.CONSTELLATION_MODIFIED
            ):  # Changed from NEW_TASKS_READY to DAG_MODIFIED
                self.logger.info(
                    f"Constellation modified, new ready tasks: {event.new_ready_tasks}"
                )
                # The orchestration will automatically pick up new ready tasks

        except Exception as e:
            self.logger.error(f"Error handling constellation event: {e}")


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
        }
        self.logger = logger or logging.getLogger(__name__)

    async def on_event(self, event: Event) -> None:
        """
        Collect metrics from events.

        :param event: Event instance for metrics collection
        """
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
        """
        Get collected metrics.

        :return: Dictionary containing session metrics and statistics
        """
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
        """
        Initialize the DAG visualizer.

        Attempts to import and create DAGVisualizer instance,
        disables visualization if import fails.
        """
        try:
            from ..visualization.dag_visualizer import DAGVisualizer

            self._visualizer = DAGVisualizer(console=self._console)
        except ImportError as e:
            self.logger.warning(f"Failed to import DAGVisualizer: {e}")
            self.enable_visualization = False

    async def on_event(self, event: Event) -> None:
        """
        Handle visualization events.

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
        constellation = None
        if hasattr(event, "data") and isinstance(event.data, dict):
            constellation = event.data.get("constellation")
            if not constellation and "updated_constellation" in event.data:
                constellation = event.data["updated_constellation"]
            if not constellation and "new_constellation" in event.data:
                constellation = event.data["new_constellation"]

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
        elif event.event_type == EventType.CONSTELLATION_MODIFIED:
            await self._handle_constellation_modified(event, constellation)


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
        """
        Handle constellation start visualization and auto-registration.

        :param event: ConstellationEvent instance
        :param constellation: TaskConstellation instance if available
        """
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

    async def _handle_constellation_failed(
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

    async def _handle_task_started(
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
                from rich.columns import Columns

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

    async def _handle_task_completed(
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
                from rich.console import Group

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

    async def _handle_task_failed(
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
                from rich.console import Group

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

    async def _handle_constellation_modified(
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
            changes = self._calculate_constellation_changes(old_constellation, new_constellation)

            # Beautiful constellation modification display
            from rich.panel import Panel
            from rich.text import Text
            from rich.table import Table

            # Create modification message
            mod_text = Text()
            mod_text.append("🔄 ", style="bold blue")
            mod_text.append(f"Constellation Modified: ", style="bold blue")
            mod_text.append(f"{new_constellation.name}", style="bold yellow")
            mod_text.append(f" ({new_constellation.constellation_id})", style="dim")

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
                    task_names = ", ".join([t[:10] + "..." if len(t) > 10 else t for t in changes["added_tasks"]])
                    table.add_row("", f"({task_names})")

            if changes["removed_tasks"]:
                table.add_row("➖ Tasks Removed:", f"{len(changes['removed_tasks'])} tasks")
                # Show task names if not too many
                if len(changes["removed_tasks"]) <= 3:
                    task_names = ", ".join([t[:10] + "..." if len(t) > 10 else t for t in changes["removed_tasks"]])
                    table.add_row("", f"({task_names})")

            if changes["added_dependencies"]:
                table.add_row("🔗 Deps Added:", f"{len(changes['added_dependencies'])} links")

            if changes["removed_dependencies"]:
                table.add_row("🔗 Deps Removed:", f"{len(changes['removed_dependencies'])} links")

            if changes["modified_tasks"]:
                table.add_row("� Tasks Modified:", f"{len(changes['modified_tasks'])} tasks updated")

            # Add current constellation stats
            stats = (
                new_constellation.get_statistics()
                if hasattr(new_constellation, "get_statistics")
                else {}
            )
            if stats:
                table.add_row(
                    "📊 Total Tasks:",
                    str(stats.get("total_tasks", len(new_constellation.tasks))),
                )
                table.add_row(
                    "🔗 Total Deps:",
                    str(
                        stats.get("total_dependencies", len(new_constellation.dependencies))
                    ),
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

            # Create panel with proper Rich composition
            from rich.console import Group

            content = Group(mod_text, "", table)

            panel = Panel(
                content,
                title="[bold blue]⚙️ Constellation Structure Updated[/bold blue]",
                border_style="blue",
                width=80,
            )

            self._visualizer.console.print(panel)

            # Show updated topology
            self._visualizer.display_dag_topology(new_constellation)

        except Exception as e:
            self.logger.debug(f"Error displaying constellation modification: {e}")

    def _calculate_constellation_changes(
        self, old_constellation: Optional[TaskConstellation], new_constellation: TaskConstellation
    ) -> Dict[str, Any]:
        """
        Calculate changes between old and new constellation by comparing their structure.

        :param old_constellation: Previous constellation state (can be None for new constellation)
        :param new_constellation: Current constellation state
        :return: Dictionary containing detailed changes
        """
        changes = {
            "modification_type": "constellation_created",
            "added_tasks": [],
            "removed_tasks": [],
            "modified_tasks": [],
            "added_dependencies": [],
            "removed_dependencies": [],
            "modified_dependencies": [],
        }

        if not old_constellation:
            # New constellation - all tasks and dependencies are "added"
            changes["modification_type"] = "constellation_created"
            changes["added_tasks"] = [task.task_id for task in new_constellation.tasks.values()]
            changes["added_dependencies"] = [
                f"{dep.from_task_id}->{dep.to_task_id}" 
                for dep in new_constellation.dependencies.values()
            ]
            return changes

        # Get task IDs for comparison
        old_task_ids = set(old_constellation.tasks.keys())
        new_task_ids = set(new_constellation.tasks.keys())

        # Calculate task changes
        changes["added_tasks"] = list(new_task_ids - old_task_ids)
        changes["removed_tasks"] = list(old_task_ids - new_task_ids)

        # Find modified tasks (same ID but different properties)
        common_task_ids = old_task_ids & new_task_ids
        for task_id in common_task_ids:
            old_task = old_constellation.tasks[task_id]
            new_task = new_constellation.tasks[task_id]
            
            # Check if task properties have changed
            if self._task_properties_changed(old_task, new_task):
                changes["modified_tasks"].append(task_id)

        # Calculate dependency changes
        old_deps = set()
        new_deps = set()
        old_dep_details = {}  # Store full dependency details for comparison
        new_dep_details = {}
        
        for dep in old_constellation.dependencies.values():
            dep_key = (dep.from_task_id, dep.to_task_id)
            old_deps.add(dep_key)
            old_dep_details[dep_key] = dep
        
        for dep in new_constellation.dependencies.values():
            dep_key = (dep.from_task_id, dep.to_task_id)
            new_deps.add(dep_key)
            new_dep_details[dep_key] = dep

        added_dep_tuples = new_deps - old_deps
        removed_dep_tuples = old_deps - new_deps

        changes["added_dependencies"] = [f"{from_id}->{to_id}" for from_id, to_id in added_dep_tuples]
        changes["removed_dependencies"] = [f"{from_id}->{to_id}" for from_id, to_id in removed_dep_tuples]

        # Find modified dependencies (same from->to but different properties)
        common_deps = old_deps & new_deps
        for dep_key in common_deps:
            old_dep = old_dep_details[dep_key]
            new_dep = new_dep_details[dep_key]
            
            # Check if dependency properties have changed
            if self._dependency_properties_changed(old_dep, new_dep):
                changes["modified_dependencies"].append(f"{dep_key[0]}->{dep_key[1]}")

        # Determine overall modification type
        if changes["added_tasks"] and changes["removed_tasks"]:
            changes["modification_type"] = "tasks_added_and_removed"
        elif changes["added_tasks"]:
            changes["modification_type"] = "tasks_added"
        elif changes["removed_tasks"]:
            changes["modification_type"] = "tasks_removed"
        elif changes["added_dependencies"] and changes["removed_dependencies"]:
            changes["modification_type"] = "dependencies_modified"
        elif changes["added_dependencies"]:
            changes["modification_type"] = "dependencies_added"
        elif changes["removed_dependencies"]:
            changes["modification_type"] = "dependencies_removed"
        elif changes["modified_dependencies"]:
            changes["modification_type"] = "dependency_properties_updated"
        elif changes["modified_tasks"]:
            changes["modification_type"] = "task_properties_updated"
        else:
            changes["modification_type"] = "constellation_updated"

        return changes

    def _task_properties_changed(self, old_task, new_task) -> bool:
        """
        Check if task properties have changed between old and new versions.

        :param old_task: Previous task state
        :param new_task: Current task state
        :return: True if properties have changed
        """
        # Compare key properties that would indicate a modification
        properties_to_check = [
            'name', 'description', 'status', 'priority', 'target_device_id',
            'timeout', 'retry_count', 'tips'
        ]
        
        for prop in properties_to_check:
            old_value = getattr(old_task, prop, None)
            new_value = getattr(new_task, prop, None)
            
            if old_value != new_value:
                return True
        
        # Check task_data if it exists
        if hasattr(old_task, 'task_data') and hasattr(new_task, 'task_data'):
            if old_task.task_data != new_task.task_data:
                return True
                
        return False

    def _dependency_properties_changed(self, old_dep: TaskStarLine, new_dep: TaskStarLine) -> bool:
        """
        Check if dependency properties have changed between old and new versions.

        :param old_dep: Previous dependency state
        :param new_dep: Current dependency state
        :return: True if properties have changed
        """
        # Compare key properties that would indicate a modification
        properties_to_check = [
            'trigger_action', 'trigger_actor', 'condition', 'keyword', 
            'description', 'priority'
        ]
        
        for prop in properties_to_check:
            old_value = getattr(old_dep, prop, None)
            new_value = getattr(new_dep, prop, None)
            
            if old_value != new_value:
                return True
                
        return False

    def set_visualization_enabled(self, enabled: bool) -> None:
        """
        Enable or disable visualization.

        :param enabled: Whether to enable visualization
        """
        self.enable_visualization = enabled
        if enabled and not self._visualizer:
            self._init_visualizer()
