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
from ufo.config.config import Config
from ufo.module.context import Context, ContextNames

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

    def archive_subtask(self, context: "Context") -> None:
        """
        Update the subtask of the agent.
        :param context: The context for the agent and session.
        """

        subtask = context.get(ContextNames.SUBTASK)
        previous_subtasks = context.get(ContextNames.PREVIOUS_SUBTASKS)

        if subtask:
            subtask_info = {"subtask": subtask, "status": self.name()}
            previous_subtasks.append(subtask_info)
            context.set(ContextNames.PREVIOUS_SUBTASKS, previous_subtasks)

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return False


@AppAgentStateManager.register
class FinishAppAgentState(AppAgentState):
    """
    The class for the finish app agent state.
    """

    def handle(self, agent: "AppAgent", context: Optional["Context"] = None) -> None:
        """
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """

        self.archive_subtask(context)

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

        if agent.mode == "follower":
            return FinishHostAgentState()
        else:
            return ContinueHostAgentState()

        # from ufo.agents.agent.app_agent import AppAgent
        # from ufo.agents.agent.follower_agent import FollowerAgent

        # if type(agent) == AppAgent:
        #     return ContinueHostAgentState()
        # elif type(agent) == FollowerAgent:
        #     return FinishHostAgentState()
        # else:
        #     return FinishHostAgentState()

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

    def is_subtask_end(self) -> bool:
        """
        Check if the subtask ends.
        :return: True if the subtask ends, False otherwise.
        """
        return False


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
        agent.process_asker(ask_user=configs.get("ASK_QUESTION", False))

    def next_state(self, agent: AppAgent) -> AppAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """
        agent.status = AppAgentStatus.CONTINUE.value
        return ContinueAppAgentState()

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
            self._confirm = True

            return

        self._confirm = agent.process_comfirmation()
        # If the user confirms the action, the agent should resume the task.
        if self._confirm:
            agent.process_resume()

    def next_state(self, agent: AppAgent) -> AppAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """

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
            return FinishHostAgentState()

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
        return AppAgentStatus.CONFIRM.value


@AppAgentStateManager.register
class ErrorAppAgentState(AppAgentState):
    """
    The class for the error app agent state.
    """

    def handle(self, agent: "AppAgent", context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """

        self.archive_subtask(context)

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
        return AppAgentStatus.ERROR.value


@AppAgentStateManager.register
class FailAppAgentState(AppAgentState):
    """
    The class for the fail app agent state.
    """

    def handle(self, agent: "AppAgent", context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """

        self.archive_subtask(context)

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
        return NoneHostAgentState()

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
        return ""
