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
    from ufo.agents.agent.customized_agent import LinuxAgent


ufo_config = get_ufo_config()


class LinuxAgentStatus(Enum):
    """
    Store the status of the linux agent.
    """

    FINISH = "FINISH"
    CONTINUE = "CONTINUE"
    FAIL = "FAIL"


class LinuxAgentStateManager(AgentStateManager):

    _state_mapping: Dict[str, Type[LinuxAgentState]] = {}

    @property
    def none_state(self) -> AgentState:
        """
        The none state of the state manager.
        """
        return NoneLinuxAgentState()


class LinuxAgentState(AgentState):
    """
    The abstract class for the linux agent state.
    """

    async def handle(
        self, agent: "LinuxAgent", context: Optional["Context"] = None
    ) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """
        pass

    @classmethod
    def agent_class(cls) -> Type[LinuxAgent]:
        """
        The agent class of the state.
        :return: The agent class.
        """

        # Avoid circular import
        from ufo.agents.agent.customized_agent import LinuxAgent

        return LinuxAgent

    def next_agent(self, agent: "LinuxAgent") -> "LinuxAgent":
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

    def next_state(self, agent: "LinuxAgent") -> LinuxAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """

        status = agent.status
        state = LinuxAgentStateManager().get_state(status)
        return state

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return False


@LinuxAgentStateManager.register
class FinishLinuxAgentState(LinuxAgentState):
    """
    The class for the finish linux agent state.
    """

    def next_agent(self, agent: "LinuxAgent") -> "LinuxAgent":
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

    def next_state(self, agent: "LinuxAgent") -> LinuxAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """
        return FinishLinuxAgentState()

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
        return LinuxAgentStatus.FINISH.value


@LinuxAgentStateManager.register
class ContinueLinuxAgentState(LinuxAgentState):
    """
    The class for the continue linux agent state.
    """

    async def handle(
        self, agent: "LinuxAgent", context: Optional["Context"] = None
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
        return LinuxAgentStatus.CONTINUE.value


@LinuxAgentStateManager.register
class FailLinuxAgentState(LinuxAgentState):
    """
    The class for the fail linux agent state.
    """

    def next_agent(self, agent: "LinuxAgent") -> "LinuxAgent":
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

    def next_state(self, agent: "LinuxAgent") -> LinuxAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """
        return FinishLinuxAgentState()

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
        return LinuxAgentStatus.FAIL.value


@LinuxAgentStateManager.register
class NoneLinuxAgentState(LinuxAgentState):
    """
    The class for the none linux agent state.
    """

    def next_agent(self, agent: "LinuxAgent") -> "LinuxAgent":
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

    def next_state(self, agent: "LinuxAgent") -> LinuxAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """
        return FinishLinuxAgentState()

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
