# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Optional, Type

from ufo.agents.agent.host_agent import HostAgent
from ufo.agents.states.basic import AgentState, AgentStateManager
from ufo.module.context import Context

if TYPE_CHECKING:
    from ufo.agents.agent.evaluation_agent import EvaluationAgent


class EvaluatonAgentStatus(Enum):
    """
    Store the status of the evaluation agent.
    """

    FINISH = "FINISH"
    CONTINUE = "CONTINUE"


class EvaluationAgentStateManager(AgentStateManager):

    @property
    def none_state(self) -> AgentState:
        """
        The none state of the state manager.
        """
        return NoneEvaluatonAgentState(self.agent)


class EvaluatonAgentState(AgentState):
    """
    The abstract class for the evaluation agent state.
    """

    @classmethod
    def agent_class(cls) -> Type[EvaluationAgent]:
        """
        Handle the agent for the current step.
        """
        return EvaluationAgent


@EvaluationAgentStateManager.register
class ContinueEvaluatonAgentState(EvaluatonAgentState):
    """
    The class for the finish evaluation agent state.
    """

    def handle(
        self, agent: EvaluationAgent, context: Optional["Context"] = None
    ) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent to handle.
        :param context: The context for the agent and session.
        """
        pass

    def next_agent(self, agent: EvaluationAgent) -> HostAgent:
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return True

    @property
    def none_state(self) -> AgentState:
        """
        The none state of the state manager.
        :return: The none state of the state manager.
        """
        return NoneEvaluatonAgentState()

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        :return: The class name of the state.
        """
        return EvaluatonAgentStatus.CONTINUE.value


@EvaluationAgentStateManager.register
class NoneEvaluatonAgentState(EvaluatonAgentState):
    """
    The state when the evaluation agent is None.
    """

    def handle(
        self, agent: EvaluationAgent, context: Optional["Context"] = None
    ) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent to handle.
        :param context: The context for the agent and session.
        """
        pass

    def next_agent(self, agent: EvaluationAgent) -> HostAgent:
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

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
        :return: The class name of the state.
        """
        return ""
