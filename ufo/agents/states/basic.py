# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Optional, Type

from ufo.modules.context import Context

# Avoid circular import
if TYPE_CHECKING:
    from ufo.agents.agent.basic import BasicAgent


class SingletonMeta(type):
    """
    A metaclass to create singleton classes.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class AgentStateManager(ABC, metaclass=SingletonMeta):
    """
    A abstract class to manage the states of the agent.
    """

    _state_mapping: Dict[str, Type[AgentState]] = {}

    def __init__(self):
        """
        Initialize the state manager.
        :param agent: The agent to be handled.
        """

        self._state_instance_mapping: Dict[str, AgentState] = {}

    def get_state(self, status: str) -> AgentState:
        """
        Get the state for the status.
        :param status: The status string.
        :return: The state object.
        """
        state = self._state_instance_mapping.get(status, self.none_state)

        return state

    def add_state(self, status: str, state: AgentState) -> None:
        """
        Add a new state to the state mapping.
        :param status: The status string.
        :param state: The state object.
        """
        self.state_map[status] = state

    @property
    def agent(self) -> BasicAgent:
        """
        The agent to be handled.
        """
        return self._agent

    @property
    def state_map(self) -> Dict[str, AgentState]:
        """
        The state mapping of status to state.
        :return: The state mapping.
        """
        return self._state_instance_mapping

    @classmethod
    def register(cls, state_class: Type[AgentState]) -> Type[AgentState]:
        """
        Decorator to register the state class to the state manager.
        :param state_class: The state class to be registered.
        """
        cls._state_mapping[state_class.name()] = state_class
        return state_class

    @property
    @abstractmethod
    def none_state(self) -> AgentState:
        """
        The none state of the state manager.
        """
        pass


class AgentState(ABC):
    """
    The abstract class for the agent state.
    """

    def __init__(self, agent: BasicAgent) -> None:
        """
        Initialize the agent state.
        :param agent: The agent to be handled.
        """
        self._agent = agent
        self._state_manager = self.create_state_manager()

    @abstractmethod
    def create_state_manager(self) -> AgentStateManager:
        return AgentStateManager()

    @property
    def state_manager(self) -> AgentStateManager:
        return self._state_manager

    @abstractmethod
    def handle(self, agent: BasicAgent, context: Optional["Context"] = None) -> None:
        """
        Handle the agent for the current step.
        :param context: The context for the agent and session.
        """
        pass

    @abstractmethod
    def next_agent(self, agent: BasicAgent) -> BasicAgent:
        """
        Get the agent for the next step.
        :param context: The context for the agent and session.
        :return: The agent for the next step.
        """
        return self.next_state().agent

    @abstractmethod
    def next_state(self, agent: BasicAgent) -> AgentState:
        """
        Get the state for the next step.
        :return: The state for the next step.
        """
        pass

    @abstractmethod
    def is_round_end(self) -> bool:
        """
        Check if the round ends.
        :return: True if the round ends, False otherwise.
        """
        pass

    @classmethod
    @abstractmethod
    def agent_class(cls) -> Type[BasicAgent]:
        """
        The class of the agent.
        """
        pass

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """
        The class name of the state.
        """
        return ""
