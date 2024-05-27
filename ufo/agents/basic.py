# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Type, Union

from ufo import utils
from ufo.agents.memory import Memory, MemoryItem
from ufo.agents.states.basic import AgentState, AgentStateManager
from ufo.automator import puppeteer
from ufo.llm import llm_call

# Lazy import the retriever factory to aviod long loading time.
retriever = utils.LazyImport("..rag.retriever")

# To avoid circular import
if TYPE_CHECKING:
    from ufo.agents.blackboard import Blackboard


class BasicAgent(ABC):
    """
    The BasicAgent class is the abstract class for the agent.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize the BasicAgent.
        :param name: The name of the agent.
        """
        self._step = 0
        self._complete = False
        self._name = name
        self._status = None
        self._register_self()
        self.retriever_factory = retriever.RetrieverFactory()
        self._memory = Memory()
        self._host = None
        self._state_mamager = self.state_manager_class(self)

    @property
    def status(self) -> str:
        """
        Get the status of the agent.
        :return: The status of the agent.
        """
        return self._status

    @status.setter
    def status(self, status: str) -> None:
        """
        Set the status of the agent.
        :param status: The status of the agent.
        """
        self._status = status

    @property
    def state(self) -> AgentState:
        """
        Get the state of the agent.
        :return: The state of the agent.
        """
        return self.state_manager.get_state(self.status)

    @state.setter
    def state(self, state: AgentState) -> None:
        """
        Set the state of the agent.
        :param state: The state of the agent.
        """
        self.state_manager.set_state(state)

    @property
    def memory(self) -> Memory:
        """
        Get the memory of the agent.
        :return: The memory of the agent.
        """
        return self._memory

    @property
    def name(self) -> str:
        """
        Get the name of the agent.
        :return: The name of the agent.
        """
        return self._name

    @property
    def blackboard(self) -> Blackboard:
        """
        Get the blackboard.
        :return: The blackboard.
        """
        return self.host.blackboard

    def create_puppteer_interface(self) -> puppeteer.AppPuppeteer:
        """
        Create the puppeteer interface.
        """
        pass

    @property
    def host(self) -> BasicAgent:
        """
        Get the host of the agent.
        :return: The host of the agent.
        """
        return self._host

    @host.setter
    def host(self, host: BasicAgent) -> None:
        """
        Set the host of the agent.
        :param host: The host of the agent.
        """
        self._host = host

    @abstractmethod
    def get_prompter(self) -> str:
        """
        Get the prompt for the agent.
        :return: The prompt.
        """
        pass

    @abstractmethod
    def message_constructor(self) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Construct the message.
        :return: The message.
        """
        pass

    @classmethod
    def get_response(
        cls, message: List[dict], namescope: str, use_backup_engine: bool
    ) -> str:
        """
        Get the response for the prompt.
        :param prompt: The prompt.
        :return: The response.
        """
        response_string, cost = llm_call.get_completion(
            message, namescope, use_backup_engine=use_backup_engine
        )
        return response_string, cost

    @staticmethod
    def response_to_dict(response: str) -> Dict[str, str]:
        """
        Convert the response to a dictionary.
        :param response: The response.
        :return: The dictionary.
        """
        return utils.json_parser(response)

    @property
    def step(self) -> int:
        """
        Get the step of the agent.
        :return: The step of the agent.
        """
        return self._step

    @step.setter
    def step(self, step: int) -> None:
        """
        Set the step of the agent.
        :param step: The step of the agent.
        """
        self._step = step

    def add_memory(self, memory_item: MemoryItem) -> None:
        """
        Update the memory of the agent.
        :param memory_item: The memory item to add.
        """
        self._memory.add_memory_item(memory_item)

    def delete_memory(self, step: int) -> None:
        """
        Delete the memory of the agent.
        :param step: The step of the memory item to delete.
        """
        self._memory.delete_memory_item(step)

    def clear_memory(self) -> None:
        """
        Clear the memory of the agent.
        """
        self._memory.clear()

    def reflection(self) -> None:
        """
        TODO:
        Reflect on the action.
        """
        pass

    @property
    def state_manager_class(self) -> Type["AgentStateManager"]:
        """
        Get the state manager class.
        :return: The state manager class.
        """
        return AgentStateManager

    @property
    def state_manager(self) -> AgentStateManager:
        """
        Get the state manager.
        :return: The state manager.
        """
        return self._state_mamager

    def build_offline_docs_retriever(self) -> None:
        """
        Build the offline docs retriever.
        """
        pass

    def build_online_search_retriever(self) -> None:
        """
        Build the online search retriever.
        """
        pass

    def build_experience_retriever(self) -> None:
        """
        Build the experience retriever.
        """
        pass

    def build_human_demonstration_retriever(self) -> None:
        """
        Build the human demonstration retriever.
        """
        pass

    def print_response(self) -> None:
        """
        Print the response.
        :param response: The response.
        """
        pass

    @classmethod
    def _register_self(self):
        """
        Register the subclass upon instantiation.
        """
        cls = type(self)
        if cls.__name__ not in AgentRegistry._registry:
            AgentRegistry.register(cls.__name__, cls)

    @classmethod
    def get_cls(cls, name: str) -> Type["BasicAgent"]:
        """
        Retrieves an agent class from the registry.
        :param name: The name of the agent class.
        :return: The agent class.
        """
        return AgentRegistry().get_cls(name)


class AgentRegistry:
    """
    The registry for the agent.
    """

    _registry: Dict[str, Type["BasicAgent"]] = {}

    @classmethod
    def register(cls, name: str, agent_cls: Type["BasicAgent"]) -> None:
        """
        Register an agent class.
        :param name: The name of the agent class.
        :param agent_cls: The agent class.
        """
        if name in cls._registry:
            raise ValueError(f"Agent class already registered under '{name}'.")
        cls._registry[name] = agent_cls

    @classmethod
    def get_cls(cls, name: str) -> Type["BasicAgent"]:
        """
        Get an agent class from the registry.
        :param name: The name of the agent class.
        :return: The agent class.
        """
        if name not in cls._registry:
            raise ValueError(f"No agent class registered under '{name}'.")
        return cls._registry[name]
