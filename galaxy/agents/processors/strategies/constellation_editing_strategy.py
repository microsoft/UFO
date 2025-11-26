# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Editing mode strategies for Constellation Agent processing.

This module provides specific strategies for constellation editing mode,
implementing the abstract methods defined in the base strategies.
"""

import time
from typing import TYPE_CHECKING, List

from galaxy.agents.processors.strategies.base_constellation_strategy import (
    BaseConstellationActionExecutionStrategy,
)
from galaxy.agents.schema import ConstellationAgentResponse, WeavingMode
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.core.events import AgentEvent, EventType, get_event_bus
from galaxy.core.types import ProcessingContext
from ufo.agents.processors.schemas.actions import (
    ActionCommandInfo,
    ListActionCommandInfo,
)
from aip.messages import Result, ResultStatus
from ufo.module.context import ContextNames

if TYPE_CHECKING:
    from galaxy.agents.constellation_agent import ConstellationAgent


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

    async def publish_actions(
        self, agent: "ConstellationAgent", actions: ListActionCommandInfo
    ) -> None:
        """
        Publish constellation editing actions as events.

        :param agent: The constellation agent
        :param actions: List of action command information
        """
        # Publish agent action event
        event = AgentEvent(
            event_type=EventType.AGENT_ACTION,
            source_id=agent.name,
            timestamp=time.time(),
            data={},
            agent_name=agent.name,
            agent_type="constellation",
            output_type="action",
            output_data={
                "action_type": "constellation_editing",
                "actions": [action.model_dump() for action in actions.actions],
            },
        )

        # Publish event asynchronously
        await get_event_bus().publish_event(event)

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
