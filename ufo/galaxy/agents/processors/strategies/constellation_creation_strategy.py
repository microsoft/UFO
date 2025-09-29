# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Creation mode strategies for Constellation Agent processing.

This module provides specific strategies for constellation creation mode,
implementing the abstract methods defined in the base strategies.
"""

from typing import TYPE_CHECKING, List

from ufo.agents.processors.context.processing_context import ProcessingContext
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
from ufo.module.context import ContextNames


if TYPE_CHECKING:
    from ufo.galaxy.agents.constellation_agent import ConstellationAgent


class ConstellationCreationActionExecutionStrategy(
    BaseConstellationActionExecutionStrategy
):
    """
    Action execution strategy specifically for constellation creation mode.

    This strategy handles:
    - Creation-specific action generation
    - New constellation building commands
    """

    def __init__(self, fail_fast: bool = False) -> None:
        """
        Initialize Constellation creation action execution strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(weaving_mode=WeavingMode.CREATION, fail_fast=fail_fast)

    async def _create_mode_specific_action_info(
        self, agent: "ConstellationAgent", parsed_response: ConstellationAgentResponse
    ) -> List[ActionCommandInfo]:
        """
        Create creation-specific action information for constellation building.
        """
        if not parsed_response.constellation:
            self.logger.warning("No valid constellation found in response.")
            return []

        try:
            # For creation mode, we create a constellation building action
            action_info = [
                ActionCommandInfo(
                    function=agent._constellation_creation_tool_name,
                    arguments={"config": parsed_response.constellation},
                )
            ]

            return action_info

        except Exception as e:
            self.logger.warning(f"Failed to create creation action info: {str(e)}")
            # Return basic action info on failure
            return [
                ActionCommandInfo(
                    function=agent._constellation_creation_tool_name,
                    arguments={
                        "config": (
                            parsed_response.constellation
                            if parsed_response.constellation
                            else "{}"
                        )
                    },
                    status=(
                        parsed_response.status if parsed_response.status else "FAILED"
                    ),
                )
            ]

    def _determine_execution_status(
        self, parsed_response: ConstellationAgentResponse, execution_results: List
    ) -> str:
        """
        Determine execution status for creation mode.
        """
        # For creation mode, status typically comes from the response
        if parsed_response and parsed_response.status:
            return parsed_response.status

        # Fallback to checking execution results
        if execution_results and all(
            result.status == "success" for result in execution_results
        ):
            return "CONTINUE"
        else:
            return "FAILED"

    def print_actions(self, actions: ListActionCommandInfo) -> None:
        """
        Printing the action result.
        :param actions: List of action command information. Do nothing for creation mode
        """
        pass

    def sync_constellation(
        self, results: List[Result], context: ProcessingContext
    ) -> None:
        """
        Synchronize the constellation state. Do nothing for editing mode.
        :param results: List of execution results
        :param context: Processing context to access and update constellation state
        """
        constellation_json = results[0].result if results else None
        if constellation_json:
            constellation = TaskConstellation.from_json(constellation_json)
            context.global_context.set(ContextNames.CONSTELLATION, constellation)
