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
    from ufo.agents.agent.app_agent import OpenAIOperatorAgent
    from ufo.agents.agent.host_agent import HostAgent
    from ufo.agents.states.host_agent_state import HostAgentState


configs = Config.get_instance().config_data


class OpenAIOperatorStatus(Enum):
    """
    Store the status of the app agent.
    """

    ERROR = "ERROR"
    FINISH = "FINISH"
    CONTINUE = "CONTINUE"
    PENDING = "PENDING"
    CONFIRM = "CONFIRM"
    ALLFINISH = "ALLFINISH"


class OpenAIOperatorStateManager(AgentStateManager):

    _state_mapping: Dict[str, Type[OpenAIOperatorState]] = {}

    @property
    def none_state(self) -> AgentState:
        """
        The none state of the state manager.
        """
        return NoneOpenAIOperatorState()


class OpenAIOperatorState(AgentState):
    """
    The abstract class for the app agent state.
    """

    def handle(
        self, agent: "OpenAIOperatorAgent", context: Optional["Context"] = None
    ) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """
        pass

    @classmethod
    def agent_class(cls) -> Type[OpenAIOperatorAgent]:
        """
        The agent class of the state.
        :return: The agent class.
        """

        # Avoid circular import
        from ufo.agents.agent.app_agent import OpenAIOperatorAgent

        return OpenAIOperatorAgent

    def next_agent(self, agent: "OpenAIOperatorAgent") -> BasicAgent:
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

    def next_state(self, agent: "OpenAIOperatorAgent") -> OpenAIOperatorState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """

        status = agent.status
        state = OpenAIOperatorStateManager().get_state(status)
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


@OpenAIOperatorStateManager.register
class AllFinishOpenAIOperatorState(OpenAIOperatorState):
    """
    The class for the all finish app agent state.
    """

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
        return OpenAIOperatorStatus.ALLFINISH.value


@OpenAIOperatorStateManager.register
class FinishOpenAIOperatorState(OpenAIOperatorState):
    """
    The class for the finish app agent state.
    """

    def handle(
        self, agent: "OpenAIOperatorAgent", context: Optional["Context"] = None
    ) -> None:
        """
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """

        self.archive_subtask(context)

    def next_agent(self, agent: "OpenAIOperatorAgent") -> HostAgent:
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent.host if agent.host else agent

    def next_state(self, agent: "OpenAIOperatorAgent") -> HostAgentState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """

        from ufo.agents.agent.host_agent import HostAgent

        if type(agent.host) == HostAgent:
            return ContinueHostAgentState()
        else:
            return AllFinishOpenAIOperatorState()

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
        return OpenAIOperatorStatus.FINISH.value


@OpenAIOperatorStateManager.register
class ContinueOpenAIOperatorState(OpenAIOperatorState):
    """
    The class for the continue app agent state.
    """

    def handle(
        self, agent: "OpenAIOperatorAgent", context: Optional["Context"] = None
    ) -> None:
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
        return OpenAIOperatorStatus.CONTINUE.value


@OpenAIOperatorStateManager.register
class PendingOpenAIOperatorState(OpenAIOperatorState):
    """
    The class for the pending app agent state.
    """

    def handle(
        self, agent: "OpenAIOperatorAgent", context: Optional["Context"] = None
    ) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """

        # Ask the user questions to help the agent to proceed.
        agent.process_asker(ask_user=configs.get("ASK_QUESTION", False))

    def next_state(self, agent: OpenAIOperatorAgent) -> OpenAIOperatorState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """
        agent.status = OpenAIOperatorStatus.CONTINUE.value
        return ContinueOpenAIOperatorState()

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
        return OpenAIOperatorStatus.PENDING.value


@OpenAIOperatorStateManager.register
class ConfirmOpenAIOperatorState(OpenAIOperatorState):
    """
    The class for the confirm app agent state.
    """

    def __init__(self) -> None:
        """
        Initialize the confirm state.
        """
        self._confirm = None

    def handle(
        self, agent: "OpenAIOperatorAgent", context: Optional["Context"] = None
    ) -> None:
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

    def next_state(self, agent: OpenAIOperatorAgent) -> OpenAIOperatorState:
        """
        Get the next state of the agent.
        :param agent: The agent for the current step.
        :return: The state for the next step.
        """

        plan = agent.processor.plan

        # If the plan is not empty and the plan contains the finish status, it means the task is finished.
        # The next state should be FinishOpenAIOperatorState.
        if len(plan) > 0 and OpenAIOperatorStatus.FINISH.value in plan[0]:
            agent.status = OpenAIOperatorStatus.FINISH.value
            return FinishOpenAIOperatorState()

        if self._confirm:
            agent.status = OpenAIOperatorStatus.CONTINUE.value
            return ContinueOpenAIOperatorState()
        else:
            agent.status = OpenAIOperatorStatus.FINISH.value
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
        return OpenAIOperatorStatus.CONFIRM.value


@OpenAIOperatorStateManager.register
class ErrorOpenAIOperatorState(OpenAIOperatorState):
    """
    The class for the error app agent state.
    """

    def handle(
        self, agent: "OpenAIOperatorAgent", context: Optional["Context"] = None
    ) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent for the current step.
        :param context: The context for the agent and session.
        """

        self.archive_subtask(context)

    def next_agent(self, agent: "OpenAIOperatorAgent") -> HostAgent:
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent.host

    def next_state(self, agent: "OpenAIOperatorAgent") -> HostAgentState:
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
        return OpenAIOperatorStatus.ERROR.value


@OpenAIOperatorStateManager.register
class NoneOpenAIOperatorState(OpenAIOperatorState):
    """
    The class for the none app agent state.
    """

    def next_agent(self, agent: "OpenAIOperatorAgent") -> HostAgent:
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent.host

    def next_state(self, agent: "OpenAIOperatorAgent") -> HostAgentState:
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
