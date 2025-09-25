# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Editing mode strategies for Constellation Agent processing.

This module provides specific strategies for constellation editing mode,
implementing the abstract methods defined in the base strategies.
"""

from typing import TYPE_CHECKING, Any, Dict, List

from ufo.agents.processors.schemas.actions import ActionCommandInfo
from ufo.contracts.contracts import Result
from ufo.galaxy.agents.processors.strategies.base_constellation_strategy import (
    BaseConstellationActionExecutionStrategy,
)
from ufo.galaxy.agents.schema import ConstellationAgentResponse, WeavingMode
from ufo.galaxy.constellation.task_constellation import TaskConstellation

if TYPE_CHECKING:
    from ufo.galaxy.agents.constellation_agent import ConstellationAgent


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

    def _determine_execution_status(
        self, parsed_response: ConstellationAgentResponse, execution_results: List
    ) -> str:
        """
        Determine execution status for editing mode.
        """
        # For editing mode, we prioritize the parsed response action status
        if parsed_response and parsed_response.action:
            # If there are actions, try to get status from the first action
            if isinstance(parsed_response.action, list) and parsed_response.action:
                first_action = parsed_response.action[0]
                if hasattr(first_action, "status") and first_action.status:
                    return first_action.status
            elif (
                hasattr(parsed_response.action, "status")
                and parsed_response.action.status
            ):
                return parsed_response.action.status

        # Fallback to general response status
        if parsed_response and parsed_response.status:
            return parsed_response.status

        # Final fallback to checking execution results
        if execution_results and all(
            result.status == "success" for result in execution_results
        ):
            return "CONTINUE"
        else:
            return "FAILED"
