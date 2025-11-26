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

from galaxy.agents.schema import WeavingMode
from ufo.agents.states.basic import AgentState, AgentStateManager
from ufo.module.context import Context, ContextNames

if TYPE_CHECKING:
    from galaxy.agents.constellation_agent import ConstellationAgent


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

    async def handle(self, agent: "ConstellationAgent", context: Context) -> None:
        try:
            agent.logger.info("Starting constellation orchestration")

            if agent.status in [
                ConstellationAgentStatus.FINISH.value,
                ConstellationAgentStatus.FAIL.value,
            ]:
                return

            # Initialize timing_info to avoid UnboundLocalError
            timing_info = {}

            # Create constellation if not exists
            if not agent.current_constellation:
                context.set(ContextNames.WEAVING_MODE, WeavingMode.CREATION)

                agent._current_constellation, timing_info = (
                    await agent.process_creation(context)
                )

            # Start orchestration in background (non-blocking)
            if agent.current_constellation:

                asyncio.create_task(
                    agent.orchestrator.orchestrate_constellation(
                        agent.current_constellation, metadata=timing_info
                    )
                )

                agent.logger.info(
                    f"Started orchestration for constellation {agent.current_constellation.constellation_id}"
                )
                agent.status = ConstellationAgentStatus.CONTINUE.value
            elif agent.status == ConstellationAgentStatus.CONTINUE.value:
                agent.status = ConstellationAgentStatus.FAIL.value
                agent.logger.error("Failed to create constellation")

        except AttributeError as e:
            import traceback

            agent.logger.error(
                f"Attribute error in start state: {traceback.format_exc()}",
                exc_info=True,
            )
            agent.status = ConstellationAgentStatus.FAIL.value
        except KeyError as e:
            import traceback

            agent.logger.error(
                f"Missing key in start state: {traceback.format_exc()}", exc_info=True
            )
            agent.status = ConstellationAgentStatus.FAIL.value
        except Exception as e:
            import traceback

            agent.logger.error(
                f"Unexpected error in start state: {traceback.format_exc()}",
                exc_info=True,
            )
            agent.status = ConstellationAgentStatus.FAIL.value

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

    async def _get_merged_constellation(
        self, agent: "ConstellationAgent", orchestrator_constellation
    ):
        """
        Get real-time merged constellation from synchronizer.

        This ensures that the agent always processes with the most up-to-date
        constellation state, including any structural modifications from previous
        editing sessions that may have completed while this task was running.

        :param agent: The ConstellationAgent instance
        :param orchestrator_constellation: The constellation from orchestrator's event
        :return: Merged constellation with latest agent modifications + orchestrator state
        """
        synchronizer = agent.orchestrator._modification_synchronizer

        if not synchronizer:
            agent.logger.debug(
                "No modification synchronizer available, using orchestrator constellation"
            )
            return orchestrator_constellation

        # Get real-time merged constellation from synchronizer
        merged_constellation = synchronizer.merge_and_sync_constellation_states(
            orchestrator_constellation=orchestrator_constellation
        )

        agent.logger.info(
            f"🔄 Real-time merged constellation for editing. "
            f"Tasks before: {len(orchestrator_constellation.tasks)}, "
            f"Tasks after merge: {len(merged_constellation.tasks)}"
        )

        return merged_constellation

    async def handle(self, agent: "ConstellationAgent", context=None) -> None:
        try:

            # Wait for task completion event - NO timeout here
            # The timeout is handled at task execution level
            agent.logger.info("Continue monitoring for task completion events...")
            context.set(ContextNames.WEAVING_MODE, WeavingMode.EDITING)

            # Collect all pending task completion events in queue
            completed_task_events = []

            # Wait for at least one event (blocking)
            first_event = await agent.task_completion_queue.get()
            completed_task_events.append(first_event)

            # Collect any other pending events (non-blocking)
            while not agent.task_completion_queue.empty():
                try:
                    event = agent.task_completion_queue.get_nowait()
                    completed_task_events.append(event)
                except asyncio.QueueEmpty:
                    break

            # Log collected events
            task_ids = [event.task_id for event in completed_task_events]
            agent.logger.info(
                f"Collected {len(completed_task_events)} task completion event(s): {task_ids}"
            )

            # Get the latest constellation from the last event
            # (orchestrator updates the same constellation object)
            latest_constellation = completed_task_events[-1].data.get("constellation")

            # ⭐ NEW: Get real-time merged constellation before processing
            # This ensures task_2 editing sees task_1's modifications even if
            # task_1 editing completed while task_2 was running
            merged_constellation = await self._get_merged_constellation(
                agent, latest_constellation
            )

            # Update constellation based on task completion
            await agent.process_editing(
                context=context,
                task_ids=task_ids,  # Pass all collected task IDs
                before_constellation=merged_constellation,  # Use merged version
            )

            # Sleep for waiting
            await asyncio.sleep(0.5)

        except Exception as e:
            agent.logger.error(f"Error in continue state: {e}")
            agent.status = ConstellationAgentStatus.FAIL.value

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
        agent._status = ConstellationAgentStatus.FINISH.value

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
        agent._status = ConstellationAgentStatus.FAIL.value

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
