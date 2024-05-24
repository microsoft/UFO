# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Type

from ufo.agent.agent import AppAgent, HostAgent
from ufo.agent.states.basic import AgentState, AgentStateManager
from ufo.modules.context import Context


@dataclass
class AppAgentStatus:
    """
    Store the status of the app agent.
    """

    ERROR = "ERROR"
    FINISH = "FINISH"
    SWITCH = "SWITCH"
    CONTINUE = "CONTINUE"
    FAIL = "FAIL"
    PENDING = "PENDING"
    CONFIRM = "CONFIRM"
    SCREENSHOT = "SCREENSHOT"


class AppAgentStateManager(AgentStateManager):

    @property
    def none_state(self) -> AgentState:
        """
        The none state of the state manager.
        """
        return NoneAppAgentState(self.agent)


class AppAgentState(AgentState):
    """
    The abstract class for the app agent state.
    """

    @property
    def agent(self) -> AppAgent:
        """
        The agent to be handled.
        """
        return self._agent

    @property
    def agent_class(self) -> Type[AppAgent]:
        """
        Handle the agent for the current step.
        """
        return AppAgent


@AppAgentStateManager.register
class FinishAppAgentState(AppAgentState):
    """
    The class for the finish app agent state.
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
        self.agent.host

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
        return AppAgentStatus.FINISH


@AppAgentStateManager.register
class ContinueAppAgentState(AppAgentState):
    """
    The class for the continue app agent state.
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
        return AppAgentStatus.CONTINUE


@AppAgentStateManager.register
class ScreenshotAppAgentState(AppAgentState):
    """
    The class for the screenshot app agent state.
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
        return AppAgentStatus.SCREENSHOT


@AppAgentStateManager.register
class SwitchAppAgentState(AppAgentState):
    """
    The class for the switch app agent state.
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
        self.agent.host

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
        return AppAgentStatus.SWITCH


@AppAgentStateManager.register
class PendingAppAgentState(AppAgentState):
    """
    The class for the pending app agent state.
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
        return AppAgentStatus.PENDING


@AppAgentStateManager.register
class ConfirmAppAgentState(AppAgentState):
    """
    The class for the confirm app agent state.
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
        return AppAgentStatus.CONFIRM


@AppAgentStateManager.register
class ErrorAppAgentState(AppAgentState):
    """
    The class for the error app agent state.
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
        self.agent.host

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
        return AppAgentStatus.ERROR


@AppAgentStateManager.register
class FailAppAgentState(AppAgentState):
    """
    The class for the fail app agent state.
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
        return AppAgentStatus.FAIL


@AppAgentStateManager.register
class NoneAppAgentState(AppAgentState):
    """
    The class for the none app agent state.
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
