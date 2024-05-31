# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional, Type

from ufo import utils
from ufo.agents.agent.app_agent import AppAgent
from ufo.agents.agent.basic import BasicAgent
from ufo.agents.states.basic import AgentState, AgentStateManager
from ufo.agents.states.host_agent_state import (
    ContinueHostAgentState,
    FinishHostAgentState,
    NoneHostAgentState,
)
from ufo.config.config import Config
from ufo.module import interactor
from ufo.module.context import Context

# Avoid circular import
if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent
    from ufo.agents.agent.host_agent import HostAgent
    from ufo.agents.states.host_agent_state import HostAgentState


configs = Config.get_instance().config_data


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
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """
        pass

    @classmethod
    def agent_class(cls) -> Type[AppAgent]:
        """
        The agent class of the state.
        :return: The agent class.
        """

        # Avoid circular import
        from ufo.agents.agent.app_agent import AppAgent

        return AppAgent

    def next_agent(self, agent: "AppAgent") -> BasicAgent:
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

    def next_state(self, agent: "AppAgent") -> AppAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
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
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent.host

    def next_state(self, agent: "AppAgent") -> HostAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """

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
        :return: The name of the state.
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
        :param agent: The agent for the current step.
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
        :return: The name of the state.
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
        :return: The name of the state.
        """
        return AppAgentStatus.SCREENSHOT.value

    def next_state(self, agent: BasicAgent) -> AgentState:

        agent_processor = agent.processor

        if agent_processor is None:

            agent.status = AppAgentStatus.CONTINUE.value
            return ContinueAppAgentState()

        control_reannotate = agent_processor.control_reannotate

        if control_reannotate is None or len(control_reannotate) == 0:
            agent.status = AppAgentStatus.CONTINUE.value
            return ContinueAppAgentState()
        else:
            return super().next_state(agent)


@AppAgentStateManager.register
class SwitchAppAgentState(AppAgentState):
    """
    The class for the switch app agent state.
    """

    def next_state(self, agent: "AppAgent") -> HostAgentState:
        """
        The next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """

        return ContinueHostAgentState()

    def next_agent(self, agent: "AppAgent") -> BasicAgent:
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
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
        :return: The name of the state.
        """
        return AppAgentStatus.SWITCH.value


@AppAgentStateManager.register
class PendingAppAgentState(AppAgentState):
    """
    The class for the pending app agent state.
    """

    def handle(self, agent: "AppAgent", context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """

        # Ask the user questions to help the agent to proceed.
        agent.process_asker()

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return False

    def next_state(self, agent: AppAgent) -> AppAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """
        agent.status = AppAgentStatus.CONTINUE.value
        return ContinueAppAgentState()

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        :return: The name of the state.
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
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """

        # If the safe guard is not enabled, the agent should resume the task.
        if not configs["SAFE_GUARD"]:
            agent.process_resume()

        agent_processor = agent.processor

        if agent_processor is None:
            utils.print_with_color("The agent processor is None.", "red")
            return

        # Get the action and control text from the agent processor to ask the user whether to proceed with the action.
        action = agent.processor.action
        control_text = agent.processor.control_text

        self._confirm = self.user_confirm(action=action, control_text=control_text)

        # If the user confirms the action, the agent should resume the task.
        if self._confirm:
            agent.process_resume()

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return False

    def next_state(self, agent: AppAgent) -> AppAgentState:

        plan = agent.processor.plan

        # If the plan is not empty and the plan contains the finish status, it means the task is finished.
        # The next state should be FinishAppAgentState.
        if len(plan) > 0 and AppAgentStatus.FINISH.value in plan[0]:
            agent.status = AppAgentStatus.FINISH.value
            return FinishAppAgentState()

        if self._confirm:
            agent.status = AppAgentStatus.CONTINUE.value
            return ContinueAppAgentState()
        else:
            agent.status = AppAgentStatus.FINISH.value
            return FinishAppAgentState()

    def user_confirm(self, action: str, control_text: str) -> bool:
        """
        Ask the user whether to proceed with the action when the status is CONFIRM.
        :param action: The action to be confirmed.
        :param control_text: The control text for the action.
        :return: True if the user confirms the action, False otherwise.
        """

        # Ask the user whether to proceed with the action when the status is PENDING.
        decision = interactor.sensitive_step_asker(action, control_text)
        if not decision:
            utils.print_with_color("The user decide to stop the task.", "magenta")
            return False

        return True

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        :return: The name of the state.
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
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent.host

    def next_state(self, agent: "AppAgent") -> HostAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
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
        :return: The name of the state.
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
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent.host

    def next_state(self, agent: "AppAgent") -> HostAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
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
        :return: The name of the state.
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
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent.host

    def next_state(self, agent: "AppAgent") -> HostAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
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
        :return: The name of the state.
        """
        return ""
