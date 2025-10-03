# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Editing mode strategies for Constellation Agent processing.

This module provides specific strategies for constellation editing mode,
implementing the abstract methods defined in the base strategies.
"""

from typing import TYPE_CHECKING, Any, Dict, List

from ufo.agents.processors.schemas.actions import (
    ActionCommandInfo,
    ListActionCommandInfo,
)
from ufo.contracts.contracts import Result
from ufo.galaxy.agents.processors.strategies.base_constellation_strategy import (
    BaseConstellationActionExecutionStrategy,
)
from ufo.galaxy.agents.schema import ConstellationAgentResponse, WeavingMode
from ufo.galaxy.constellation.task_constellation import TaskConstellation
from ufo.galaxy.core.types import ProcessingContext

if TYPE_CHECKING:
    from ufo.galaxy.agents.constellation_agent import ConstellationAgent
    from rich.console import Console


class ConstellationEditingActionExecutionStrategy(
    BaseConstellationActionExecutionStrategy
):
    """
    Action execution strategy specifically for constellation editing mode.

    This strategy handles:
    - Editing-specific action extraction
    - Existing constellation modification commands
    """

    def __init__(self, fail_fast: bool = False) -> None:
        """
        Initialize Constellation editing action execution strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(weaving_mode=WeavingMode.EDITING, fail_fast=fail_fast)

    async def _create_mode_specific_action_info(
        self, agent: "ConstellationAgent", parsed_response: ConstellationAgentResponse
    ) -> ActionCommandInfo | List[ActionCommandInfo]:
        """
        Create editing-specific action information from LLM response.
        """
        try:
            # For editing mode, we use the actions from the response
            if parsed_response.action:
                return parsed_response.action
            else:
                # No action specified, return empty list
                return []

        except Exception as e:
            self.logger.warning(f"Failed to create editing action info: {str(e)}")
            # Return basic action info on failure
            return [
                ActionCommandInfo(
                    function="no_action",
                    arguments={},
                    status=(
                        parsed_response.status if parsed_response.status else "FAILED"
                    ),
                    result=Result(status="error", result={"error": str(e)}),
                )
            ]

    def print_actions(self, actions: ListActionCommandInfo) -> None:
        """
        Print constellation editing actions in a concise and structured format.

        Displays editing operations with clear visual indicators, operation summaries,
        and status information optimized for constellation modifications.

        :param actions: List of action command information
        """
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text
        from ufo.contracts.contracts import ResultStatus

        console = Console()

        if not actions or not actions.actions:
            console.print("ℹ️  No actions to display", style="dim")
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

        console.print()
        console.print(Panel(header, border_style="cyan"))

        # Display each action in a compact format
        for idx, action in enumerate(actions.actions, 1):
            self._print_single_action(console, idx, action)

        # Display summary
        self._print_summary(console, success_count, failed_count, actions.status)
        console.print()

    def _print_single_action(
        self, console: "Console", idx: int, action: ActionCommandInfo
    ) -> None:
        """
        Print a single constellation editing action in compact format.

        :param console: Rich console instance
        :param idx: Action index
        :param action: Action command information
        """
        from rich.table import Table
        from rich.text import Text
        from ufo.contracts.contracts import ResultStatus

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
        operation = self._format_operation(action)

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

        console.print(table)

        # Show error if failed
        if action.result.status == ResultStatus.FAILURE and action.result.error:
            error_text = Text()
            error_text.append("    └─ Error: ", style="red dim")
            error_text.append(str(action.result.error)[:100], style="red")
            if len(str(action.result.error)) > 100:
                error_text.append("...", style="red dim")
            console.print(error_text)

    def _format_operation(self, action: ActionCommandInfo) -> str:
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

    def _print_summary(
        self,
        console: "Console",
        success_count: int,
        failed_count: int,
        final_status: str,
    ) -> None:
        """
        Print operation summary.

        :param console: Rich console instance
        :param success_count: Number of successful operations
        :param failed_count: Number of failed operations
        :param final_status: Final status of the action sequence
        """
        from rich.table import Table
        from rich.text import Text
        from rich.panel import Panel

        # Create summary table
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
        status_style = (
            "green" if final_status in ["CONTINUE", "COMPLETED"] else "yellow"
        )
        status_text = Text(final_status, style=f"{status_style} bold")
        summary.add_row("📊 Status:", status_text)

        console.print()
        console.print(
            Panel(summary, title="Summary", border_style="blue", padding=(0, 1))
        )

    def sync_constellation(
        self, results: List[Result], context: ProcessingContext
    ) -> None:
        """
        Synchronize the constellation state from MCP tool execution results.

        Extracts the updated constellation from the last successful result and
        updates the global context.

        :param results: List of execution results from MCP tools
        :param context: Processing context to access and update constellation state
        """
        from ufo.contracts.contracts import ResultStatus
        from ufo.module.context import ContextNames
        from ufo.galaxy.constellation.task_constellation import TaskConstellation

        if not results:
            self.logger.debug("No results to sync constellation from")
            return

        # Find the last successful result that contains constellation data
        constellation_json = None
        for result in reversed(results):
            # Check if result status is SUCCESS
            if result.status == ResultStatus.SUCCESS and result.result:
                try:
                    # Check if result contains constellation JSON
                    # MCP tools return JSON strings
                    if isinstance(result.result, str):
                        # Try to parse as constellation JSON
                        # Valid constellation JSON should contain "constellation_id"
                        if (
                            '"constellation_id"' in result.result
                            or '"tasks"' in result.result
                        ):
                            constellation_json = result.result
                            break
                    elif isinstance(result.result, dict):
                        # If result is already a dict, check for constellation fields
                        if (
                            "constellation_id" in result.result
                            or "tasks" in result.result
                        ):
                            constellation_json = result.result
                            break
                except Exception as e:
                    self.logger.warning(f"Failed to parse result as constellation: {e}")
                    continue

        # If we found constellation data, sync it to context
        if constellation_json:
            try:
                # Parse constellation from JSON
                if isinstance(constellation_json, str):
                    constellation = TaskConstellation.from_json(
                        json_data=constellation_json
                    )
                else:
                    constellation = TaskConstellation.from_dict(constellation_json)

                # Update global context
                context.global_context.set(ContextNames.CONSTELLATION, constellation)
                self.logger.info(
                    f"Successfully synced constellation from editing operation: "
                    f"constellation_id={constellation.constellation_id}"
                )
            except Exception as e:
                self.logger.error(f"Failed to sync constellation from result: {e}")
        else:
            self.logger.debug("No constellation data found in results to sync")
