# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional, Type

from ufo.agents.states.basic import AgentState, AgentStateManager
from config.config_loader import get_ufo_config
from ufo.module.context import Context

# Avoid circular import
if TYPE_CHECKING:
    from ufo.agents.agent.customized_agent import MobileAgent


ufo_config = get_ufo_config()


class MobileAgentStatus(Enum):
    """
    Store the status of the mobile agent.
    """

    FINISH = "FINISH"
    CONTINUE = "CONTINUE"
    FAIL = "FAIL"


class MobileAgentStateManager(AgentStateManager):

    _state_mapping: Dict[str, Type[MobileAgentState]] = {}

    @property
    def none_state(self) -> AgentState:
        """
        The none state of the state manager.
        """
        return NoneMobileAgentState()


class MobileAgentState(AgentState):
    """
    The abstract class for the mobile agent state.
    """

    async def handle(
        self, agent: "MobileAgent", context: Optional["Context"] = None
    ) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """
        pass

    @classmethod
    def agent_class(cls) -> Type[MobileAgent]:
        """
        The agent class of the state.
        :return: The agent class.
        """

        # Avoid circular import
        from ufo.agents.agent.customized_agent import MobileAgent

        return MobileAgent

    def next_agent(self, agent: "MobileAgent") -> "MobileAgent":
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

    def next_state(self, agent: "MobileAgent") -> MobileAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """

        status = agent.status
        state = MobileAgentStateManager().get_state(status)
        return state

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return False


@MobileAgentStateManager.register
class FinishMobileAgentState(MobileAgentState):
    """
    The class for the finish mobile agent state.
    """

    def next_agent(self, agent: "MobileAgent") -> "MobileAgent":
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

    def next_state(self, agent: "MobileAgent") -> MobileAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """
        return FinishMobileAgentState()

    def is_subtask_end(self) -> bool:
        """
        Check if the subtask ends.
        :return: True if the subtask ends, False otherwise.
        """
        return True

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return True

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        :return: The name of the state.
        """
        return MobileAgentStatus.FINISH.value


@MobileAgentStateManager.register
class ContinueMobileAgentState(MobileAgentState):
    """
    The class for the continue mobile agent state.
    """

    async def handle(
        self, agent: "MobileAgent", context: Optional["Context"] = None
    ) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """

        await agent.process(context)

    def is_subtask_end(self) -> bool:
        """
        Check if the subtask ends.
        :return: True if the subtask ends, False otherwise.
        """
        return False

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        :return: The name of the state.
        """
        return MobileAgentStatus.CONTINUE.value


@MobileAgentStateManager.register
class FailMobileAgentState(MobileAgentState):
    """
    The class for the fail mobile agent state.
    """

    def next_agent(self, agent: "MobileAgent") -> "MobileAgent":
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

    def next_state(self, agent: "MobileAgent") -> MobileAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """
        return FinishMobileAgentState()

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return True

    def is_subtask_end(self) -> bool:
        """
        Check if the subtask ends.
        :return: True if the subtask ends, False otherwise.
        """
        return True

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        :return: The name of the state.
        """
        return MobileAgentStatus.FAIL.value


@MobileAgentStateManager.register
class NoneMobileAgentState(MobileAgentState):
    """
    The class for the none mobile agent state.
    """

    def next_agent(self, agent: "MobileAgent") -> "MobileAgent":
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

    def next_state(self, agent: "MobileAgent") -> MobileAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """
        return FinishMobileAgentState()

    def is_subtask_end(self) -> bool:
        """
        Check if the subtask ends.
        :return: True if the subtask ends, False otherwise.
        """
        return True

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return True

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        :return: The name of the state.
        """
        return ""
