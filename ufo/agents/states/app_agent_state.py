# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional, Type

from ufo.agents.agent.basic import BasicAgent
from ufo.agents.states.basic import AgentState, AgentStateManager
from ufo.agents.states.host_agent_state import (
    ContinueHostAgentState,
    FinishHostAgentState,
    NoneHostAgentState,
)
from ufo.module.context import Context

# Avoid circular import
if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent
    from ufo.agents.agent.host_agent import HostAgent
    from ufo.agents.states.host_agent_state import HostAgentState


class AppAgentStatus(Enum):
    """
    Store the status of the app agent.
    """

    ERROR = "ERROR"
    FINISH = "FINISH"
    CONTINUE = "CONTINUE"
    FAIL = "FAIL"
    PENDING = "PENDING"
    CONFIRM = "CONFIRM"
    SWITCH = "SWITCH"
    SCREENSHOT = "SCREENSHOT"


class AppAgentStateManager(AgentStateManager):

    _state_mapping: Dict[str, Type[AppAgentState]] = {}

    @property
    def none_state(self) -> AgentState:
        """
        The none state of the state manager.
        """
        return NoneAppAgentState()


class AppAgentState(AgentState):
    """
    The abstract class for the app agent state.
    """

    def handle(self, agent: "AppAgent", context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param context: The context for the agent and session.
        """
        pass

    @classmethod
    def agent_class(cls) -> Type[AppAgent]:
        """
        Handle the agent for the current step.
        """

        # Avoid circular import
        from ufo.agents.agent.app_agent import AppAgent

        return AppAgent

    def next_agent(self, agent: "AppAgent") -> BasicAgent:
        """
        Get the agent for the next step.
        """
        return agent

    def next_state(self, agent: "AppAgent") -> AppAgentState:
        """
        Get the next state of the agent.
        """

        status = agent.status
        state = AppAgentStateManager().get_state(status)
        return state


@AppAgentStateManager.register
class FinishAppAgentState(AppAgentState):
    """
    The class for the finish app agent state.
    """

    def next_agent(self, agent: "AppAgent") -> HostAgent:
        """
        Get the agent for the next step.
        :param context: The context for the agent and session.
        :return: The agent for the next step.
        """
        return agent.host

    def next_state(self, agent: "AppAgent") -> HostAgentState:

        return FinishHostAgentState()

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
        return AppAgentStatus.FINISH.value


@AppAgentStateManager.register
class ContinueAppAgentState(AppAgentState):
    """
    The class for the continue app agent state.
    """

    def handle(self, agent: "AppAgent", context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param context: The context for the agent and session.
        """
        agent.process(context)

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
        return AppAgentStatus.CONTINUE.value


@AppAgentStateManager.register
class ScreenshotAppAgentState(ContinueAppAgentState):
    """
    The class for the screenshot app agent state.
    """

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        """
        return AppAgentStatus.SCREENSHOT.value


@AppAgentStateManager.register
class SwitchAppAgentState(AppAgentState):
    """
    The class for the switch app agent state.
    """

    def next_state(self, agent: "AppAgent") -> HostAgentState:
        """
        The next state of the agent.
        """

        return ContinueHostAgentState()

    def next_agent(self, agent: "AppAgent") -> BasicAgent:
        """
        Get the agent for the next step.
        """
        return agent.host

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
        return AppAgentStatus.SWITCH.value


@AppAgentStateManager.register
class PendingAppAgentState(AppAgentState):
    """
    The class for the pending app agent state.
    """

    def handle(self, agent: "AppAgent", context: Optional["Context"] = None) -> None:
        """
        TODO
        Handle the agent for the current step.
        :param context: The context for the agent and session.
        """
        pass

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
        return AppAgentStatus.PENDING.value


@AppAgentStateManager.register
class ConfirmAppAgentState(AppAgentState):
    """
    The class for the confirm app agent state.
    """

    def __init__(self) -> None:
        """
        Initialize the confirm state.
        """
        self._confirm = None

    def handle(self, agent: "AppAgent", context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param context: The context for the agent and session.
        """

        self._confirm = self.user_confirm()

        if self._confirm:
            agent.process_resume()
        else:
            pass

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return False

    def user_confirm(self) -> bool:
        """
        TODO
        Handle the agent for the current step.
        :param context: The context for the agent and session.
        """
        pass

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        """
        return AppAgentStatus.CONFIRM.value


@AppAgentStateManager.register
class ErrorAppAgentState(AppAgentState):
    """
    The class for the error app agent state.
    """

    def next_agent(self, agent: "AppAgent") -> HostAgent:
        """
        Get the agent for the next step.
        :param context: The context for the agent and session.
        :return: The agent for the next step.
        """
        return agent.host

    def next_state(self, agent: "AppAgent") -> HostAgentState:
        """
        Get the next state of the agent.
        """
        return FinishHostAgentState

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
        return AppAgentStatus.ERROR.value


@AppAgentStateManager.register
class FailAppAgentState(AppAgentState):
    """
    The class for the fail app agent state.
    """

    def next_agent(self, agent: "AppAgent") -> HostAgent:
        """
        Get the agent for the next step.
        :param context: The context for the agent and session.
        :return: The agent for the next step.
        """
        return agent.host

    def next_state(self, agent: "AppAgent") -> HostAgentState:
        """
        Get the next state of the agent.
        """
        return FinishHostAgentState

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
        return AppAgentStatus.FAIL.value


@AppAgentStateManager.register
class NoneAppAgentState(AppAgentState):
    """
    The class for the none app agent state.
    """

    def next_agent(self, agent: "AppAgent") -> HostAgent:
        """
        Get the agent for the next step.
        :param context: The context for the agent and session.
        :return: The agent for the next step.
        """
        return agent.host

    def next_state(self, agent: "AppAgent") -> HostAgentState:
        """
        Get the next state of the agent.
        """
        return NoneHostAgentState

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
