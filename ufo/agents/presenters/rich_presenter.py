# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Rich Console Presenter

This module implements the Rich-based presenter for beautiful console output.
All agents' print_response logic is centralized here for maintainability.
"""

import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .base_presenter import BasePresenter

# Import response types for type hints
if TYPE_CHECKING:
    from ufo.agents.processors.schemas.response_schema import (
        AppAgentResponse,
        HostAgentResponse,
        EvaluationAgentResponse,
    )
    from galaxy.agents.schema import ConstellationAgentResponse


class RichPresenter(BasePresenter):
    """
    Rich-based presenter for beautiful console output.

    This presenter uses the Rich library to create visually appealing
    console output with colors, panels, and tables.
    """

    # Style configuration - centralized for easy maintenance
    STYLES = {
        "thought": {"title": "💡 Thoughts", "style": "green"},
        "observation": {"title": "👀 Observations", "style": "bright_cyan"},
        "action": {"title": "⚒️ Actions", "style": "blue"},
        "action_applied": {"title": "⚒️ Action applied", "style": "blue"},
        "plan": {"title": "📚 Plans", "style": "cyan"},
        "next_plan": {"title": "📚 Next Plan", "style": "cyan"},
        "comment": {"title": "💬 Agent Comment", "style": "yellow"},
        "message": {"title": "📩 Messages to AppAgent", "style": "cyan"},
        "results": {"title": "📊 Current Task Results", "style": "bright_magenta"},
        "constellation_info": {
            "title": "🌌 Constellation Information",
            "style": "cyan",
        },
        "task_details": {"title": "📋 Task Details", "style": "yellow"},
        "dependencies": {"title": "🔗 Dependencies", "style": "blue"},
        "notice": {"title": "Notice", "style": "yellow"},
        "next_application": {
            "title": "📲 Next Selected Application/Agent",
            "style": "yellow",
        },
        "status_default": {"title": "📊 Status", "style": "blue"},
        "status_processing": {"title": "📊 Processing Status", "style": "blue"},
        "final_status": {"title": "📊 Final Status", "style": "yellow"},
        "status": {
            "FINISH": {"style": "green", "emoji": "✅"},
            "FAIL": {"style": "red", "emoji": "❌"},
            "CONTINUE": {"style": "yellow", "emoji": "🔄"},
            "START": {"style": "blue", "emoji": "🚀"},
        },
        # Evaluation-specific styles
        "evaluation": {
            "sub_scores": {"title": "📊 Sub-scores", "style": "green"},
            "task_complete": {"title": "💯 Task is complete", "style": "cyan"},
            "reason": {"title": "🤔 Reason", "style": "blue"},
        },
        # Response separator styles
        "separator": {
            "start": {"char": "═", "style": "bright_blue bold"},
            "end": {"char": "─", "style": "dim"},
        },
    }

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the Rich presenter.

        :param console: Optional Rich Console instance. If not provided, a new one is created.
        """
        self.console = console or Console()

    def present_response(self, response: Any, **kwargs) -> None:
        """
        Present the complete agent response.
        Delegates to specific methods based on response type.

        :param response: The response object to present
        :param kwargs: Additional options like print_action, etc.
        """
        # This is a generic method that will be overridden by specific presenter methods
        # or can delegate to type-specific presentation methods
        pass

    def present_thought(self, thought: str) -> None:
        """
        Present agent's thought/reasoning.

        :param thought: The thought text to display
        """
        if thought:
            self.console.print(
                Panel(
                    thought,
                    title=self.STYLES["thought"]["title"],
                    style=self.STYLES["thought"]["style"],
                )
            )

    def present_observation(self, observation: str) -> None:
        """
        Present agent's observation.

        :param observation: The observation text to display
        """
        if observation:
            self.console.print(
                Panel(
                    observation,
                    title=self.STYLES["observation"]["title"],
                    style=self.STYLES["observation"]["style"],
                )
            )

    def present_status(self, status: str, **kwargs) -> None:
        """
        Present agent's status.

        :param status: The status string
        :param kwargs: Optional 'title_style' to choose between different title styles
        """
        status_upper = status.upper()
        style_config = self.STYLES["status"].get(status_upper, {})
        emoji = style_config.get("emoji", "📊")
        style = style_config.get("style", "blue")

        title_style = kwargs.get("title_style", "processing")
        if title_style == "default":
            title = self.STYLES["status_default"]["title"]
        elif title_style == "final":
            title = self.STYLES["final_status"]["title"]
        else:
            title = (
                f"{emoji} {self.STYLES['status_processing']['title'].split(' ', 1)[-1]}"
            )

        self.console.print(
            Panel(
                status_upper,
                title=title,
                style=style,
            )
        )

    def present_actions(self, actions: Any, **kwargs) -> None:
        """
        Present agent's planned actions.

        :param actions: The actions to display
        :param kwargs: Display options like 'format' (table/list)
        """
        # This will be implemented by specific action presentation methods
        pass

    def present_plan(self, plan: List[str]) -> None:
        """
        Present agent's plan.

        :param plan: List of plan items
        """
        if plan:
            plan_str = "\n".join(plan) if isinstance(plan, list) else str(plan)
            self.console.print(
                Panel(
                    plan_str,
                    title=self.STYLES["next_plan"]["title"],
                    style=self.STYLES["next_plan"]["style"],
                )
            )

    def present_comment(self, comment: Optional[str]) -> None:
        """
        Present agent's comment/message.

        :param comment: The comment text to display
        """
        if comment:
            self._display_agent_comment(comment)

    def present_results(self, results: Any) -> None:
        """
        Present execution results.

        :param results: The results to display
        """
        if results:
            results_content = str(results)
            if len(results_content) > 500:
                results_content = results_content[:497] + "..."

            self.console.print(
                Panel(
                    results_content,
                    title=self.STYLES["results"]["title"],
                    style=self.STYLES["results"]["style"],
                )
            )

    # ============================================================================
    # Helper methods for visual separation
    # ============================================================================

    def _print_response_header(self, agent_type: str) -> None:
        """
        Print response header separator.

        :param agent_type: Agent type name (e.g., "AppAgent", "HostAgent")
        """
        from rich.rule import Rule

        self.console.print()
        self.console.print(
            Rule(
                f"🤖 {agent_type} Response",
                style=self.STYLES["separator"]["start"]["style"],
                characters=self.STYLES["separator"]["start"]["char"],
            )
        )

    def _print_response_footer(self) -> None:
        """
        Print response footer separator.
        """
        from rich.rule import Rule

        self.console.print(
            Rule(
                style=self.STYLES["separator"]["end"]["style"],
                characters=self.STYLES["separator"]["end"]["char"],
            )
        )
        self.console.print()

    # ============================================================================
    # AppAgent-specific presentation methods
    # ============================================================================

    def present_app_agent_response(
        self, response: "AppAgentResponse", print_action: bool = True
    ) -> None:
        """
        Present AppAgent response - matches original AppAgent.print_response logic.

        :param response: AppAgentResponse object
        :param print_action: Whether to print actions
        """
        from ufo.agents.processors.schemas.actions import ActionCommandInfo

        # Print response header
        self._print_response_header("AppAgent")

        actions = response.action
        if isinstance(actions, ActionCommandInfo):
            actions = [actions]

        observation = response.observation
        thought = response.thought
        plan = response.plan if isinstance(response.plan, list) else [response.plan]
        comment = response.comment
        result = response.result

        # Observations
        self.present_observation(observation)

        # Thoughts
        self.present_thought(thought)

        # Actions as table
        if print_action and actions:
            self._present_actions_as_table(actions)

        # Next Plan
        self.present_plan(plan)

        # Comment
        self.present_comment(comment)

        # Screenshot saving
        screenshot_saving = response.save_screenshot
        if screenshot_saving.get("save", False):
            reason = screenshot_saving.get("reason")
            self.console.print(
                Panel(
                    f"📸 Screenshot saved to the blackboard.\nReason: {reason}",
                    title=self.STYLES["notice"]["title"],
                    style=self.STYLES["notice"]["style"],
                )
            )
        # Results
        if result:
            self.present_results(result)

        # Print response footer
        self._print_response_footer()

    def _present_actions_as_table(self, actions: List[Any]) -> None:
        """
        Present actions as a Rich table (AppAgent style).

        :param actions: List of ActionCommandInfo objects
        """
        table = Table(
            title=self.STYLES["action"]["title"], show_lines=True, style="blue"
        )
        table.add_column("Step", style="cyan", no_wrap=True)
        table.add_column("Function", style="yellow")
        table.add_column("Arguments", style="magenta")
        table.add_column("Status", style="red")

        for i, action in enumerate(actions):
            args = action.arguments
            if isinstance(args, dict):
                args_str = str(args)
            else:
                args_str = str(json.loads(args))

            table.add_row(
                f"{i+1}",
                str(action.function),
                args_str,
                str(action.status),
            )

        self.console.print(table)

    # ============================================================================
    # HostAgent-specific presentation methods
    # ============================================================================

    def present_host_agent_response(
        self, response: "HostAgentResponse", action_str: Optional[str] = None
    ) -> None:
        """
        Present HostAgent response - matches original HostAgent.print_response logic.

        :param response: HostAgentResponse object
        :param action_str: Pre-formatted action string (optional)
        """
        # Print response header
        self._print_response_header("HostAgent")

        function = response.function
        arguments = response.arguments
        observation = response.observation
        thought = response.thought
        subtask = response.current_subtask
        result = response.result
        message = "\n".join(response.message) if response.message else ""
        plan = [subtask] + list(response.plan)
        plan_str = "\n".join([f"({i+1}) {str(item)}" for i, item in enumerate(plan)])
        status = response.status
        comment = response.comment

        application = (
            arguments.get("name") if function == "select_application_window" else None
        )

        # Observations
        self.present_observation(observation)

        # Thoughts
        self.present_thought(thought)

        # Action - use pre-formatted action string if provided, otherwise format it
        if function:
            if not action_str:
                action_str = self._format_action_string(function, arguments)

            self.console.print(
                Panel(
                    action_str,
                    title=self.STYLES["action_applied"]["title"],
                    style=self.STYLES["action_applied"]["style"],
                )
            )

        # Plan
        self.console.print(
            Panel(
                plan_str,
                title=self.STYLES["plan"]["title"],
                style=self.STYLES["plan"]["style"],
            )
        )

        # Next selected application
        if application:
            self.console.print(
                Panel(
                    application,
                    title=self.STYLES["next_application"]["title"],
                    style=self.STYLES["next_application"]["style"],
                )
            )

        # Messages
        if message:
            self.console.print(
                Panel(
                    message,
                    title=self.STYLES["message"]["title"],
                    style=self.STYLES["message"]["style"],
                )
            )

        # Status
        self.console.print(
            Panel(
                status,
                title=self.STYLES["status_default"]["title"],
                style=self.STYLES["status_default"]["style"],
            )
        )

        # Comment
        self.present_comment(comment)

        # Results
        if result:
            self.present_results(result)

        # Print response footer
        self._print_response_footer()

    def _format_action_string(self, function: str, arguments: Dict[str, Any]) -> str:
        """
        Format action string for display.

        :param function: Function name
        :param arguments: Function arguments
        :return: Formatted action string
        """
        # Basic formatting - can be enhanced based on HostAgent.get_command_string
        args_str = ", ".join([f"{k}={v}" for k, v in arguments.items()])
        return f"{function}({args_str})"

    # ============================================================================
    # ConstellationAgent-specific presentation methods
    # ============================================================================

    def present_constellation_agent_response(
        self, response: "ConstellationAgentResponse", print_action: bool = False
    ) -> None:
        """
        Present ConstellationAgent response - matches original ConstellationAgent.print_response logic.

        :param response: ConstellationAgentResponse object
        :param print_action: Whether to print actions
        """
        # Print response header
        self._print_response_header("ConstellationAgent")

        # Agent thoughts
        if response.thought:
            self.console.print(
                Panel(
                    response.thought,
                    title="🧠 Constellation Agent Thoughts",
                    style="green",
                )
            )

        # Status display with appropriate styling
        status_style = "blue"
        status_emoji = "📊"
        if response.status.upper() == "FINISH":
            status_style = "green"
            status_emoji = "✅"
        elif response.status.upper() == "FAIL":
            status_style = "red"
            status_emoji = "❌"
        elif response.status.upper() == "CONTINUE":
            status_style = "yellow"
            status_emoji = "🔄"

        self.console.print(
            Panel(
                response.status.upper(),
                title=f"{status_emoji} Processing Status",
                style=status_style,
            )
        )

        # Constellation (if available)
        if response.constellation:
            self._present_constellation_info(response.constellation)

        # Actions (if available)
        if response.action and print_action:
            if isinstance(response.action, list) and len(response.action) > 0:
                actions_text = Text()
                for i, action in enumerate(response.action):
                    action_str = action.to_string(action.function, action.arguments)
                    actions_text.append(f"{i+1}. ", style="bold cyan")
                    actions_text.append(f"{action_str}\n", style="white")

                self.console.print(
                    Panel(
                        actions_text,
                        title="⚒️ Planned Actions",
                        style="blue",
                    )
                )

        # Results (if available)
        if response.results:
            self.present_results(response.results)

        # Print response footer
        self._print_response_footer()

    def _present_constellation_info(self, constellation: Any) -> None:
        """
        Present constellation information.

        :param constellation: TaskConstellation object
        """
        constellation_name = (
            constellation.name or f"Constellation {constellation.constellation_id}"
        )
        task_count = len(constellation.tasks)
        dependency_count = len(constellation.dependencies)
        constellation_state = constellation.state

        constellation_info = Text()
        constellation_info.append(f"🆔 ID: ", style="bold cyan")
        constellation_info.append(f"{constellation.constellation_id}\n", style="white")
        constellation_info.append(f"🌟 Name: ", style="bold cyan")
        constellation_info.append(f"{constellation_name}\n", style="white")
        constellation_info.append(f"📊 State: ", style="bold cyan")
        constellation_info.append(f"{constellation_state}\n", style="white")
        constellation_info.append(f"📋 Tasks: ", style="bold cyan")
        constellation_info.append(f"{task_count}\n", style="white")
        constellation_info.append(f"🔗 Dependencies: ", style="bold cyan")
        constellation_info.append(f"{dependency_count}", style="white")

        self.console.print(
            Panel(
                constellation_info,
                title=self.STYLES["constellation_info"]["title"],
                style=self.STYLES["constellation_info"]["style"],
            )
        )

        # Display task details if available
        if constellation.tasks:
            tasks_text = Text()
            for task_id, task in constellation.tasks.items():
                task_name = task.name
                target_device = task.target_device_id or "Unknown"
                tasks_text.append(f"• Task: {task_name} ", style="bold yellow")
                tasks_text.append(f"→ Device: {target_device}\n", style="white")

                # Show description if available
                if task.description:
                    tasks_text.append(
                        f"  Description: {task.description}\n", style="cyan"
                    )

                # Show tips if available
                if task.tips:
                    for tip in task.tips:
                        tasks_text.append(f"  💡 {tip}\n", style="green")

            self.console.print(
                Panel(
                    tasks_text,
                    title=self.STYLES["task_details"]["title"],
                    style=self.STYLES["task_details"]["style"],
                )
            )

        # Display dependency details if available
        if constellation.dependencies:
            deps_text = Text()
            for line_id, dependency in constellation.dependencies.items():
                deps_text.append(f"• {dependency.from_task_id} ", style="bold blue")
                deps_text.append(f"→ {dependency.to_task_id}\n", style="bold blue")
                if dependency.condition_description:
                    deps_text.append(
                        f"  Condition: {dependency.condition_description}\n",
                        style="cyan",
                    )

            self.console.print(
                Panel(
                    deps_text,
                    title=self.STYLES["dependencies"]["title"],
                    style=self.STYLES["dependencies"]["style"],
                )
            )

    # ============================================================================
    # Action presentation methods (for strategies)
    # ============================================================================

    def present_action_list(self, actions: Any, success_only: bool = False) -> None:
        """
        Present action list with enhanced visual formatting.

        :param actions: ListActionCommandInfo object
        :param success_only: Whether to print only successful actions
        """
        from rich.rule import Rule
        from aip.messages import ResultStatus

        if not actions or not actions.actions:
            self.console.print("ℹ️  No actions to display", style="dim")
            return

        # Filter actions based on success_only
        filtered_actions = [
            action
            for action in actions.actions
            if not success_only or action.result.status == ResultStatus.SUCCESS
        ]

        if not filtered_actions:
            self.console.print("ℹ️  No actions to display", style="dim")
            return

        # Count successful and failed actions
        success_count = sum(
            1 for a in actions.actions if a.result.status == ResultStatus.SUCCESS
        )
        failed_count = len(actions.actions) - success_count

        # Print header
        self.console.print()
        header_text = f"⚒️  Action Execution Results ({len(filtered_actions)} action{'s' if len(filtered_actions) != 1 else ''})"
        self.console.print(
            Rule(
                header_text,
                style="bright_blue bold",
                characters="═",
            )
        )

        # Display each action with enhanced formatting
        for idx, action in enumerate(filtered_actions, 1):
            self._print_single_action(idx, action)

        # Display summary
        self._print_action_summary(success_count, failed_count, actions.status)

        # Print footer
        self.console.print(
            Rule(
                style="dim",
                characters="─",
            )
        )
        self.console.print()

    def present_constellation_editing_actions(self, actions: Any) -> None:
        """
        Present constellation editing actions - matches ConstellationEditingActionExecutionStrategy.print_actions logic.

        :param actions: ListActionCommandInfo object
        """
        from aip.messages import ResultStatus

        if not actions or not actions.actions:
            self.console.print("ℹ️  No actions to display", style="dim")
            return

        # Count successful and failed actions
        success_count = sum(
            1 for a in actions.actions if a.result.status == ResultStatus.SUCCESS
        )
        failed_count = len(actions.actions) - success_count

        # Create header
        header = Text()
        header.append("🔧 Constellation Editing Operations", style="bold cyan")
        header.append(
            f" ({len(actions.actions)} action{'s' if len(actions.actions) > 1 else ''})",
            style="dim",
        )

        self.console.print()
        self.console.print(Panel(header, border_style="cyan"))

        # Display each action in a compact format
        for idx, action in enumerate(actions.actions, 1):
            self._print_single_constellation_action(idx, action)

        # Display summary
        self._print_constellation_summary(success_count, failed_count, actions.status)
        self.console.print()

    def _print_single_constellation_action(self, idx: int, action: Any) -> None:
        """Print a single constellation editing action in compact format."""
        from rich.table import Table
        from rich.text import Text
        from aip.messages import ResultStatus

        # Determine status icon and color
        if action.result.status == ResultStatus.SUCCESS:
            status_icon = "✅"
            status_color = "green"
        elif action.result.status == ResultStatus.FAILURE:
            status_icon = "❌"
            status_color = "red"
        else:
            status_icon = "⏸️"
            status_color = "yellow"

        # Extract operation details
        operation = self._format_constellation_operation(action)

        # Create compact table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Icon", style=status_color, width=3)
        table.add_column("Index", style="dim", width=4)
        table.add_column("Operation", style="bold")
        table.add_column("Status", style=status_color, width=12)

        # Format status
        status_text = (
            action.result.status.value
            if hasattr(action.result.status, "value")
            else str(action.result.status)
        )

        table.add_row(status_icon, f"#{idx}", operation, status_text.upper())

        self.console.print(table)

        # Show error if failed
        if action.result.status == ResultStatus.FAILURE and action.result.error:
            error_text = Text()
            error_text.append("    └─ Error: ", style="red dim")
            error_text.append(str(action.result.error)[:100], style="red")
            if len(str(action.result.error)) > 100:
                error_text.append("...", style="red dim")
            self.console.print(error_text)

    def _format_constellation_operation(self, action: Any) -> str:
        """
        Format constellation operation into human-readable text.

        :param action: Action command information
        :return: Formatted operation description
        """
        function = action.function
        args = action.arguments

        # Format different types of operations
        if function == "add_task":
            task_id = args.get("task_id", "?")
            name = args.get("name", "")
            return (
                f"Add Task: '{task_id}' ({name})" if name else f"Add Task: '{task_id}'"
            )

        elif function == "remove_task":
            task_id = args.get("task_id", "?")
            return f"Remove Task: '{task_id}'"

        elif function == "update_task":
            task_id = args.get("task_id", "?")
            # Show which fields are being updated
            update_fields = [
                k for k in args.keys() if k != "task_id" and args[k] is not None
            ]
            fields_str = ", ".join(update_fields) if update_fields else "fields"
            return f"Update Task: '{task_id}' ({fields_str})"

        elif function == "add_dependency":
            dep_id = args.get("dependency_id", "?")
            from_task = args.get("from_task_id", "?")
            to_task = args.get("to_task_id", "?")
            return f"Add Dependency (ID {dep_id}): {from_task} → {to_task}"

        elif function == "remove_dependency":
            dep_id = args.get("dependency_id", "?")
            return f"Remove Dependency: '{dep_id}'"

        elif function == "update_dependency":
            dep_id = args.get("dependency_id", "?")
            return f"Update Dependency: '{dep_id}'"

        elif function == "build_constellation":
            config = args.get("config", {})
            if isinstance(config, dict):
                task_count = len(config.get("tasks", []))
                dep_count = len(config.get("dependencies", []))
                return f"Build Constellation ({task_count} tasks, {dep_count} dependencies)"
            return "Build Constellation"

        elif function == "clear_constellation":
            return "Clear Constellation (remove all tasks)"

        elif function == "load_constellation":
            file_path = args.get("file_path", "?")
            import os

            filename = os.path.basename(file_path) if file_path else "?"
            return f"Load Constellation from '{filename}'"

        elif function == "save_constellation":
            file_path = args.get("file_path", "?")
            import os

            filename = os.path.basename(file_path) if file_path else "?"
            return f"Save Constellation to '{filename}'"

        else:
            # Fallback for unknown operations
            return f"{function}({', '.join(f'{k}={v}' for k, v in list(args.items())[:2])})"

    def _print_constellation_summary(
        self, success_count: int, failed_count: int, status: str
    ) -> None:
        """Print summary of constellation editing actions."""
        from rich.panel import Panel

        summary = Table(show_header=False, box=None, padding=(0, 2))
        summary.add_column("Label", style="bold")
        summary.add_column("Value")

        # Success count
        success_text = Text()
        success_text.append(str(success_count), style="green bold")
        success_text.append(" succeeded", style="green")
        summary.add_row("✅ Successful:", success_text)

        # Failed count
        if failed_count > 0:
            failed_text = Text()
            failed_text.append(str(failed_count), style="red bold")
            failed_text.append(" failed", style="red")
            summary.add_row("❌ Failed:", failed_text)

        # Final status
        status_style = "green" if status in ["CONTINUE", "COMPLETED"] else "yellow"
        status_text = Text(status, style=f"{status_style} bold")
        summary.add_row("📊 Status:", status_text)

        self.console.print()
        self.console.print(
            Panel(summary, title="Summary", border_style="blue", padding=(0, 1))
        )

    # ============================================================================
    # Helper methods
    # ============================================================================

    def _display_agent_comment(self, comment: str) -> None:
        """
        Display agent comment with enhanced formatting.

        :param comment: Comment text to display
        """
        if comment:
            self.console.print(
                Panel(
                    comment,
                    title=self.STYLES["comment"]["title"],
                    style=self.STYLES["comment"]["style"],
                )
            )

    def _print_single_action(self, idx: int, action: Any) -> None:
        """
        Print a single action with detailed information and visual formatting.

        :param idx: Action index number
        :param action: ActionCommandInfo object
        """
        from rich.text import Text
        from aip.messages import ResultStatus

        # Determine status icon and color
        if action.result.status == ResultStatus.SUCCESS:
            status_icon = "✅"
            status_color = "green"
            border_style = "green"
        elif action.result.status == ResultStatus.FAILURE:
            status_icon = "❌"
            status_color = "red"
            border_style = "red"
        else:
            status_icon = "⏸️"
            status_color = "yellow"
            border_style = "yellow"

        # Build content with proper formatting
        content = Text()

        # Function
        content.append("Function: ", style="cyan bold")
        content.append(
            f"{action.function}\n" if action.function else "[dim]None[/dim]\n",
            style="white",
        )

        # Arguments
        if action.arguments:
            args_str = ", ".join([f"{k}={v}" for k, v in action.arguments.items()])
            if len(args_str) > 100:
                args_str = args_str[:97] + "..."
            content.append("Arguments: ", style="cyan bold")
            content.append(f"{args_str}\n", style="white")

        # Target information
        if action.target:
            target_name = action.target.name or action.target.id or "Unknown"
            target_type = action.target.type or "Unknown"
            content.append("Target: ", style="cyan bold")
            content.append(f"{target_name} ", style="white")
            content.append(f"({target_type})\n", style="dim")

        # Status
        status_text = (
            action.result.status.value
            if hasattr(action.result.status, "value")
            else str(action.result.status)
        )
        content.append("Status: ", style="cyan bold")
        content.append(f"{status_icon} {status_text.upper()}", style=status_color)

        # Create panel for this action
        panel_title = f"[bold]Action #{idx}[/bold]"
        self.console.print(
            Panel(
                content,
                title=panel_title,
                border_style=border_style,
                padding=(0, 1),
            )
        )

        # Show result details if available
        if action.result.result and str(action.result.result).strip():
            result_text = Text()
            result_text.append("    └─ Result: ", style="dim")
            result_str = str(action.result.result)
            if len(result_str) > 500:
                result_str = result_str[:497] + "..."
            result_text.append(result_str, style="bright_black")
            self.console.print(result_text)

        # Show error if failed
        if action.result.status == ResultStatus.FAILURE and action.result.error:
            error_text = Text()
            error_text.append("    └─ Error: ", style="red dim")
            error_str = str(action.result.error)
            if len(error_str) > 100:
                error_str = error_str[:97] + "..."
            error_text.append(error_str, style="red")
            self.console.print(error_text)

    def _print_action_summary(
        self, success_count: int, failed_count: int, status: str
    ) -> None:
        """
        Print summary of action execution results.

        :param success_count: Number of successful actions
        :param failed_count: Number of failed actions
        :param status: Overall execution status
        """
        from rich.panel import Panel

        summary = Table(show_header=False, box=None, padding=(0, 2))
        summary.add_column("Label", style="bold")
        summary.add_column("Value")

        # Success count
        if success_count > 0:
            success_text = Text()
            success_text.append(str(success_count), style="green bold")
            success_text.append(" succeeded", style="green")
            summary.add_row("✅ Successful:", success_text)

        # Failed count
        if failed_count > 0:
            failed_text = Text()
            failed_text.append(str(failed_count), style="red bold")
            failed_text.append(" failed", style="red")
            summary.add_row("❌ Failed:", failed_text)

        # Final status
        status_style = "green" if status in ["FINISH", "COMPLETED"] else "yellow"
        status_emoji = "🏁" if status == "FINISH" else "🔄"
        status_text = Text(f"{status_emoji} {status}", style=f"{status_style} bold")
        summary.add_row("📊 Status:", status_text)

        self.console.print()
        self.console.print(
            Panel(summary, title="Summary", border_style="blue", padding=(0, 1))
        )

    # ============================================================================
    # EvaluationAgent-specific presentation methods
    # ============================================================================

    def present_evaluation_agent_response(
        self, response: "EvaluationAgentResponse"
    ) -> None:
        """
        Present EvaluationAgent response - matches original EvaluationAgent.print_response logic.

        :param response: EvaluationAgentResponse object
        """
        from rich.rule import Rule

        # Print response header
        self._print_response_header("EvaluationAgent")

        emoji_map = {
            "yes": "✅",
            "no": "❌",
            "unsure": "❓",
        }

        complete = emoji_map.get(response.complete, response.complete)
        sub_scores = response.sub_scores or []
        reason = response.reason

        # Sub-scores table
        if sub_scores:
            table = Table(
                title=self.STYLES["evaluation"]["sub_scores"]["title"],
                show_lines=True,
                style=self.STYLES["evaluation"]["sub_scores"]["style"],
            )
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Evaluation", style="green")
            for sub_score in sub_scores:
                score = sub_score.get("name")
                evaluation = sub_score.get("evaluation")
                table.add_row(str(score), str(emoji_map.get(evaluation, evaluation)))
            self.console.print(table)

        # Task complete
        self.console.print(
            Panel(
                f"{complete}",
                title=self.STYLES["evaluation"]["task_complete"]["title"],
                style=self.STYLES["evaluation"]["task_complete"]["style"],
            )
        )

        # Reason
        if reason:
            self.console.print(
                Panel(
                    reason,
                    title=self.STYLES["evaluation"]["reason"]["title"],
                    style=self.STYLES["evaluation"]["reason"]["style"],
                )
            )

        # Print response footer
        self._print_response_footer()
