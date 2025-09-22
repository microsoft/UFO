# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Agent State Machine

This module implements the state machine for GalaxyWeaverAgent to handle
constellation orchestration with proper synchronization between task completion
events and agent updates.
"""

import asyncio
from enum import Enum
from typing import TYPE_CHECKING, Dict, Type

from ufo.agents.states.basic import AgentState, AgentStateManager
from ufo.galaxy.constellation import ConstellationState

if TYPE_CHECKING:
    from ufo.galaxy.agents.galaxy_agent import GalaxyWeaverAgent


class GalaxyAgentStatus(Enum):
    """Galaxy Agent states"""

    START = "START"
    MONITOR = "MONITOR"
    FINISH = "FINISH"
    FAIL = "FAIL"


class GalaxyAgentStateManager(AgentStateManager):
    """State manager for Galaxy Agent"""

    _state_mapping: Dict[str, Type[AgentState]] = {}

    # Add CONTINUE attribute for compatibility with BasicAgent
    class Status:
        CONTINUE = type("Status", (), {"value": "continue"})()

    CONTINUE = Status.CONTINUE

    @property
    def none_state(self) -> AgentState:
        return StartGalaxyAgentState()


class GalaxyAgentState(AgentState):
    """Base state for Galaxy Agent"""

    @classmethod
    def agent_class(cls):
        from .galaxy_agent import GalaxyWeaverAgent

        return GalaxyWeaverAgent


@GalaxyAgentStateManager.register
class StartGalaxyAgentState(GalaxyAgentState):
    """Start state - create and execute constellation"""

    async def handle(self, agent: "GalaxyWeaverAgent", context=None) -> None:
        try:
            agent.logger.info("Starting constellation orchestration")

            # Create constellation if not exists
            if not agent.current_constellation:
                agent._current_constellation = await agent.process_initial_request(
                    agent.current_request, context
                )

            # Start orchestration
            if agent.current_constellation:
                # Start orchestration in background (non-blocking)

                agent._orchestration_task = asyncio.create_task(
                    agent.orchestrator.orchestrate_constellation(
                        agent.current_constellation
                    )
                )
                agent._status = "executing"
                agent.logger.info(
                    f"Started orchestration for constellation {agent.current_constellation.constellation_id}"
                )
            else:
                agent._status = "failed"
                agent.logger.error("Failed to create constellation")

        except Exception as e:
            agent.logger.error(f"Error in start state: {e}")
            agent._status = "failed"

    def next_state(self, agent) -> AgentState:
        if agent._status == "failed":
            return FailGalaxyAgentState()
        elif agent._status == "finished":
            return FinishGalaxyAgentState()
        else:
            return MonitorGalaxyAgentState()

    def next_agent(self, agent):
        return agent

    def is_round_end(self) -> bool:
        return False

    def is_subtask_end(self) -> bool:
        return False

    @classmethod
    def name(cls) -> str:
        return GalaxyAgentStatus.START.value


@GalaxyAgentStateManager.register
class MonitorGalaxyAgentState(GalaxyAgentState):
    """Monitor state - wait for task completion events"""

    async def handle(self, agent: "GalaxyWeaverAgent", context=None) -> None:
        try:

            # Wait for task completion event - NO timeout here
            # The timeout is handled at task execution level
            agent.logger.debug("Monitor waiting for task completion events...")

            task_event = await agent.task_completion_queue.get()

            agent.logger.info(
                f"Received task completion: {task_event.task_id} -> {task_event.status}"
            )

            # Update constellation based on task completion
            await agent.update_constellation_with_lock(
                task_result={
                    "task_id": task_event.task_id,
                    "status": task_event.status,
                    "result": task_event.result,
                    "error": task_event.error,
                    "timestamp": task_event.timestamp,
                },
                context=context,
            )

            # Check agent decision after update
            should_continue = await agent.should_continue(
                agent.current_constellation, context
            )

            if not should_continue:
                if agent.current_constellation.state == ConstellationState.COMPLETED:
                    agent._status = "finished"
                    agent.logger.info("Agent decided task is finished")
                else:
                    agent._status = "failed"
                    agent.logger.info("Agent decided task failed")
            elif agent.current_constellation.state in [
                ConstellationState.COMPLETED,
                ConstellationState.FAILED,
            ]:
                # Constellation finished but agent wants to continue - restart
                agent._status = "continue"
                agent.logger.info(
                    "Constellation finished, but agent wants to continue - restarting"
                )
            else:
                # Continue monitoring
                agent.logger.debug("Continue monitoring for more task events")

        except Exception as e:
            agent.logger.error(f"Error in monitor state: {e}")
            agent._status = "failed"

    def next_state(self, agent) -> AgentState:
        if agent._status == "failed":
            return FailGalaxyAgentState()
        elif agent._status == "finished":
            return FinishGalaxyAgentState()
        elif agent._status == "continue":
            return StartGalaxyAgentState()  # Restart orchestration
        else:
            return MonitorGalaxyAgentState()  # Continue monitoring

    def next_agent(self, agent):
        return agent

    def is_round_end(self) -> bool:
        return False

    def is_subtask_end(self) -> bool:
        return False

    @classmethod
    def name(cls) -> str:
        return GalaxyAgentStatus.MONITOR.value


@GalaxyAgentStateManager.register
class FinishGalaxyAgentState(GalaxyAgentState):
    """Finish state - task completed successfully"""

    async def handle(self, agent: "GalaxyWeaverAgent", context=None) -> None:
        agent.logger.info("Galaxy task completed successfully")
        agent._status = "finished"

        # Clean up orchestration task if still running
        if agent._orchestration_task and not agent._orchestration_task.done():
            agent._orchestration_task.cancel()

    def next_state(self, agent: "GalaxyWeaverAgent") -> AgentState:
        return self  # Terminal state

    def next_agent(self, agent: "GalaxyWeaverAgent"):
        return agent

    def is_round_end(self) -> bool:
        return True

    def is_subtask_end(self) -> bool:
        return True

    @classmethod
    def name(cls) -> str:
        return GalaxyAgentStatus.FINISH.value


@GalaxyAgentStateManager.register
class FailGalaxyAgentState(GalaxyAgentState):
    """Fail state - task failed"""

    async def handle(self, agent: "GalaxyWeaverAgent", context=None) -> None:
        agent.logger.error("Galaxy task failed")
        agent._status = "failed"

        # Clean up orchestration task if still running
        if agent._orchestration_task and not agent._orchestration_task.done():
            agent._orchestration_task.cancel()

    def next_state(self, agent: "GalaxyWeaverAgent") -> AgentState:
        return self  # Terminal state

    def next_agent(self, agent: "GalaxyWeaverAgent"):
        return agent

    def is_round_end(self) -> bool:
        return True

    def is_subtask_end(self) -> bool:
        return True

    @classmethod
    def name(cls) -> str:
        return GalaxyAgentStatus.FAIL.value
