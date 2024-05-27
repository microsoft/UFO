# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Type

from ufo.agents.agent.app_agent import AppAgent
from ufo.agents.agent.host_agent import HostAgent
from ufo.agents.states.basic import AgentState, AgentStateManager
from ufo.modules.context import Context


@dataclass
class HostAgentStatus:
    """
    Store the status of the host agent.
    """

    ERROR = "ERROR"
    FINISH = "FINISH"
    CONTINUE = "CONTINUE"
    FAIL = "FAIL"
    PENDING = "PENDING"


class HostAgentStateManager(AgentStateManager):
    """
    The class to manage the states of the host agent.
    """

    @property
    def none_state(self) -> AgentState:
        """
        The none state of the state manager.
        """
        return NoneHostAgentState(self.agent)


class HostAgentState(AgentState):
    """
    The abstract class for the host agent state.
    """

    @property
    def agent(self) -> HostAgent:
        """
        The agent to be handled.
        """
        return self._agent

    @property
    def agent_class(self) -> Type[HostAgent]:
        """
        Handle the agent for the current step.
        """
        return HostAgent


@HostAgentStateManager.register
class FinishHostAgentState(HostAgentState):
    """
    The class for the finish host agent state.
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
        return self.agent

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
        return HostAgentStatus.FINISH


@HostAgentStateManager.register
class ContinueHostAgentState(HostAgentState):
    """
    The class for the continue host agent state.
    """

    def handle(self, context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param context: The context for the agent and session.
        """
        pass

    def next_agent(self, context: Optional["Context"] = None) -> AppAgent:
        """
                Get the agent for the next step.
        :param context: The context for the agent and session.
                :return: The agent for the next step.
        """
        self.agent.get_active_appagent()

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return False

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        """
        return HostAgentStatus.CONTINUE


@HostAgentStateManager.register
class PendingHostAgentState(HostAgentState):
    """
    The class for the pending host agent state.
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
        return False

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        """
        return HostAgentStatus.PENDING


@HostAgentStateManager.register
class ErrorHostAgentState(HostAgentState):
    """
    The class for the error host agent state.
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
        return False

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        """
        return HostAgentStatus.ERROR


@HostAgentStateManager.register
class FailHostAgentState(HostAgentState):
    """
    The class for the fail host agent state.
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
        return HostAgentStatus.FAIL


@HostAgentStateManager.register
class NoneHostAgentState(HostAgentState):
    """
    The class for the none host agent state.
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
        :return: The class name of the state.
        """
        return ""
