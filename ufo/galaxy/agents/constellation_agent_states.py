# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Agent State Machine

This module implements the state machine for Constellation to handle
constellation orchestration with proper synchronization between task completion
events and agent updates.
"""

import asyncio
from enum import Enum
from typing import TYPE_CHECKING, Dict, Type

from ufo.agents.states.basic import AgentState, AgentStateManager


if TYPE_CHECKING:
    from ufo.galaxy.agents.constellation_agent import ConstellationAgent


class ConstellationAgentStatus(Enum):
    """Galaxy Agent states"""

    START = "START"
    CONTINUE = "CONTINUE"
    FINISH = "FINISH"
    FAIL = "FAIL"


class ConstellationAgentStateManager(AgentStateManager):
    """State manager for Galaxy Agent"""

    _state_mapping: Dict[str, Type[AgentState]] = {}

    @property
    def none_state(self) -> AgentState:
        return StartConstellationAgentState()


class ConstellationAgentState(AgentState):
    """Base state for Galaxy Agent"""

    @classmethod
    def agent_class(cls):
        from .constellation_agent import ConstellationAgent

        return ConstellationAgent

    def next_state(self, agent: "ConstellationAgent") -> AgentState:
        """
        Get the next state of the agent.
        :param agent: The current agent.
        """
        status = agent.status

        state = ConstellationAgentStateManager().get_state(status)
        return state


@ConstellationAgentStateManager.register
class StartConstellationAgentState(ConstellationAgentState):
    """Start state - create and execute constellation"""

    async def handle(self, agent: "ConstellationAgent", context=None) -> None:
        try:
            agent.logger.info("Starting constellation orchestration")

            if agent.status in ["FINISH", "FAIL"]:
                return

            # Create constellation if not exists
            if not agent.current_constellation:
                agent._current_constellation = await agent.process_creation(
                    agent.current_request, context
                )

            # Start orchestration
            if agent.current_constellation:
                # Start orchestration in background (non-blocking)

                asyncio.create_task(
                    agent.orchestrator.orchestrate_constellation(
                        agent.current_constellation
                    )
                )

                agent.logger.info(
                    f"Started orchestration for constellation {agent.current_constellation.constellation_id}"
                )
            else:
                agent.status = "FAIL"
                agent.logger.error("Failed to create constellation")

        except Exception as e:
            agent.logger.error(f"Error in start state: {e}")
            agent.status = "FAIL"

    def next_agent(self, agent):
        return agent

    def is_round_end(self) -> bool:
        return False

    def is_subtask_end(self) -> bool:
        return False

    @classmethod
    def name(cls) -> str:
        return ConstellationAgentStatus.START.value


@ConstellationAgentStateManager.register
class ContinueConstellationAgentState(ConstellationAgentState):
    """Continue state - wait for task completion events"""

    async def handle(self, agent: "ConstellationAgent", context=None) -> None:
        try:

            # Wait for task completion event - NO timeout here
            # The timeout is handled at task execution level
            agent.logger.debug("Continue waiting for task completion events...")

            task_event = await agent.task_completion_queue.get()

            agent.logger.info(
                f"Received task completion: {task_event.task_id} -> {task_event.status}"
            )

            # Update constellation based on task completion
            constellation = await agent.process_editing(context=context)
            if constellation.is_complete():
                agent.logger.info(
                    f"The old constellation {constellation.constellation_id} is completed."
                )
                # IMPORTANT: Restart the constellation orchestration when there is new update.
                if agent.status == "CONTINUE":
                    agent.logger.info(
                        f"New update to the constellation {constellation.constellation_id} needed, restart the orchestration"
                    )
                    agent.status = "START"

        except Exception as e:
            agent.logger.error(f"Error in continue state: {e}")
            agent._status = "FAIL"

    def next_agent(self, agent):
        return agent

    def is_round_end(self) -> bool:
        return False

    def is_subtask_end(self) -> bool:
        return False

    @classmethod
    def name(cls) -> str:
        return ConstellationAgentStatus.CONTINUE.value


@ConstellationAgentStateManager.register
class FinishConstellationAgentState(ConstellationAgentState):
    """Finish state - task completed successfully"""

    async def handle(self, agent: "ConstellationAgent", context=None) -> None:
        agent.logger.info("Galaxy task completed successfully")
        agent._status = "FINISH"

    def next_state(self, agent: "ConstellationAgent") -> AgentState:
        return self  # Terminal state

    def next_agent(self, agent: "ConstellationAgent"):
        return agent

    def is_round_end(self) -> bool:
        return True

    def is_subtask_end(self) -> bool:
        return True

    @classmethod
    def name(cls) -> str:
        return ConstellationAgentStatus.FINISH.value


@ConstellationAgentStateManager.register
class FailConstellationAgentState(ConstellationAgentState):
    """Fail state - task failed"""

    async def handle(self, agent: "ConstellationAgent", context=None) -> None:
        agent.logger.error("Galaxy task failed")
        agent._status = "FAIL"

    def next_state(self, agent: "ConstellationAgent") -> AgentState:
        return self  # Terminal state

    def next_agent(self, agent: "ConstellationAgent"):
        return agent

    def is_round_end(self) -> bool:
        return True

    def is_subtask_end(self) -> bool:
        return True

    @classmethod
    def name(cls) -> str:
        return ConstellationAgentStatus.FAIL.value
