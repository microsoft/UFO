# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from enum import Enum
from typing import Optional, Type

from ufo.agents.agent.evaluation_agent import EvaluationAgent
from ufo.agents.agent.host_agent import HostAgent
from ufo.agents.states.basic import AgentState, AgentStateManager
from ufo.modules.context import Context


class EvaluatonAgentStatus(Enum):
    """
    Store the status of the evaluation agent.
    """

    EVALUATION = "EVALUATION"
    FINISH = "FINISH"


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

    @property
    def agent(self) -> EvaluationAgent:
        """
        The agent to be handled.
        """
        return self._agent

    @classmethod
    def agent_class(cls) -> Type[EvaluationAgent]:
        """
        Handle the agent for the current step.
        """
        return EvaluationAgent


@EvaluationAgentStateManager.register
class EvaEvaluatonAgentState(EvaluatonAgentState):
    """
    The class for the finish evaluation agent state.
    """

    def handle(self, context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param context: The context for the agent and session.
        """
        pass

    def next_agent(self, context: Optional["Context"] = None) -> HostAgent:
        """
        Get the agent for the next step.
        :param context: The context for the agent and session.
        :return: The agent for the next step.
        """
        self.agent

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
        """
        return EvaluatonAgentStatus.EVALUATION.value


@EvaluationAgentStateManager.register
class NoneEvaluatonAgentState(EvaluatonAgentState):
    """
    The state when the evaluation agent is None.
    """

    def handle(self, context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param context: The context for the agent and session.
        """
        pass

    def next_agent(self, context: Optional["Context"] = None) -> HostAgent:
        """
        Get the agent for the next step.
        :param context: The context for the agent and session.
        :return: The agent for the next step.
        """
        self.agent

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
        """
        return ""
