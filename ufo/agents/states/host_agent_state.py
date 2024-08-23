# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional, Type

from ufo.agents.states.basic import AgentState, AgentStateManager
from ufo.config.config import Config
from ufo.module.context import Context, ContextNames

configs = Config.get_instance().config_data

if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent
    from ufo.agents.agent.host_agent import HostAgent
    from ufo.agents.states.app_agent_state import AppAgentState


class HostAgentStatus(Enum):
    """
    Store the status of the host agent.
    """

    ERROR = "ERROR"
    FINISH = "FINISH"
    CONTINUE = "CONTINUE"
    FAIL = "FAIL"
    PENDING = "PENDING"
    CONFIRM = "CONFIRM"


class HostAgentStateManager(AgentStateManager):
    """
    The class to manage the states of the host agent.
    """

    _state_mapping: Dict[str, Type[HostAgentState]] = {}

    @property
    def none_state(self) -> AgentState:
        """
        The none state of the state manager.
        """
        return NoneHostAgentState()


class HostAgentState(AgentState):
    """
    The abstract class for the host agent state.
    """

    def handle(self, agent: "HostAgent", context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent to handle.
        :param context: The context for the agent and session.
        """
        pass

    @classmethod
    def agent_class(cls) -> Type[HostAgent]:
        """
        Handle the agent for the current step.
        :param agent: The agent class of the state.
        """
        from ufo.agents.agent.host_agent import HostAgent

        return HostAgent

    def next_state(self, agent: "HostAgent") -> AgentState:
        """
        Get the next state of the agent.
        :param agent: The current agent.
        """
        status = agent.status

        state = HostAgentStateManager().get_state(status)
        return state

    def next_agent(self, agent: "HostAgent") -> HostAgent:
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """
        return agent

    def is_subtask_end(self) -> bool:
        """
        Check if the subtask ends.
        :return: True if the subtask ends, False otherwise.
        """
        return False


@HostAgentStateManager.register
class FinishHostAgentState(HostAgentState):
    """
    The class for the finish host agent state.
    """

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
        :return: The class name of the
        """
        return HostAgentStatus.FINISH.value


@HostAgentStateManager.register
class ContinueHostAgentState(HostAgentState):
    """
    The class for the continue host agent state.
    """

    def handle(self, agent: "HostAgent", context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent to handle.
        :param context: The context for the agent and session.
        """
        agent.process(context)

        self.create_app_agent(agent, context)

    def next_state(self, agent: "HostAgent") -> AppAgentState:
        """
        Get the next state of the agent.
        :param agent: The current agent.
        :return: The state for the next step.
        """

        # Transition to the app agent state.
        # Lazy import to avoid circular dependency.

        if agent.status == HostAgentStatus.CONTINUE.value:

            from ufo.agents.states.app_agent_state import ContinueAppAgentState

            return ContinueAppAgentState()

        else:
            return super().next_state(agent)

    def create_app_agent(self, agent: "HostAgent", context: Context) -> AppAgent:
        """
        Create the app agent for the host agent.
        :param agent: The host agent.
        :param context: The context for the agent and session.
        :return: The app agent.
        """

        application_window_name = context.get(ContextNames.APPLICATION_PROCESS_NAME)
        application_root_name = context.get(ContextNames.APPLICATION_ROOT_NAME)
        request = context.get(ContextNames.REQUEST)

        if context.get(ContextNames.MODE) == "normal":

            agent_name = "AppAgent/{root}/{process}".format(
                root=application_root_name, process=application_window_name
            )

            app_agent: AppAgent = agent.create_subagent(
                agent_type="app",
                agent_name=agent_name,
                process_name=application_window_name,
                app_root_name=application_root_name,
                is_visual=configs["APP_AGENT"]["VISUAL_MODE"],
                main_prompt=configs["APPAGENT_PROMPT"],
                example_prompt=configs["APPAGENT_EXAMPLE_PROMPT"],
                api_prompt=configs["API_PROMPT"],
            )

        elif context.get(ContextNames.MODE) == "follower":

            # Load additional app info prompt.
            app_info_prompt = configs.get("APP_INFO_PROMPT", None)

            agent_name = "FollowerAgent/{root}/{process}".format(
                root=application_root_name, process=application_window_name
            )

            # Create the app agent in the follower mode.
            app_agent = agent.create_subagent(
                agent_type="follower",
                agent_name=agent_name,
                process_name=application_window_name,
                app_root_name=application_root_name,
                is_visual=configs["APP_AGENT"]["VISUAL_MODE"],
                main_prompt=configs["FOLLOWERAHENT_PROMPT"],
                example_prompt=configs["APPAGENT_EXAMPLE_PROMPT"],
                api_prompt=configs["API_PROMPT"],
                app_info_prompt=app_info_prompt,
            )

        else:
            raise ValueError(
                f"The {context.get(ContextNames.MODE)} mode is not supported."
            )

        # Create the COM receiver for the app agent.
        if configs.get("USE_APIS", False):
            app_agent.Puppeteer.receiver_manager.create_api_receiver(
                application_root_name, application_window_name
            )

        # Provision the context for the app agent, including the all retrievers.
        app_agent.context_provision(request)

        return app_agent

    def next_agent(self, agent: "HostAgent") -> AppAgent:
        """
        Get the agent for the next step.
        :param agent: The agent for the current step.
        :return: The agent for the next step.
        """

        if agent.status == HostAgentStatus.CONTINUE.value:
            return agent.get_active_appagent()
        else:
            return agent

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
        :return: The class name of the state.
        """
        return HostAgentStatus.CONTINUE.value


@HostAgentStateManager.register
class PendingHostAgentState(HostAgentState):
    """
    The class for the pending host agent state.
    """

    def handle(self, agent: "HostAgent", context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param agent: The agent to handle.
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

    def next_state(self, agent: HostAgent) -> AgentState:
        """
        Get the next state of the agent.
        :param agent: The current agent.
        :return: The state for the next step.
        """
        agent.status = HostAgentStatus.CONTINUE.value
        return ContinueHostAgentState()

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        :return: The class name of the state.
        """
        return HostAgentStatus.PENDING.value


@HostAgentStateManager.register
class ErrorHostAgentState(HostAgentState):
    """
    The class for the error host agent state.
    """

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return True

    def next_state(self, agent: HostAgent) -> AgentState:
        """
        Get the next state of the agent.
        :param agent: The current agent.
        :return: The state for the next step.
        """
        return FinishHostAgentState()

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        :return: The class name of the
        """
        return HostAgentStatus.ERROR.value


@HostAgentStateManager.register
class FailHostAgentState(HostAgentState):
    """
    The class for the fail host agent state.
    """

    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        return True

    def next_state(self, agent: HostAgent) -> AgentState:
        """
        Get the next state of the agent.
        :param agent: The current agent.
        :return: The state for the next step.
        """
        return FinishHostAgentState()

    @classmethod
    def name(cls) -> str:
        """
        The class name of the state.
        :return: The class name of the
        """
        return HostAgentStatus.FAIL.value


@HostAgentStateManager.register
class NoneHostAgentState(HostAgentState):
    """
    The class for the none host agent state.
    """

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
