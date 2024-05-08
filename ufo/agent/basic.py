# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type

from ufo import utils
from ufo.llm import llm_call
from ufo.module.state import Status

# Lazy import the retriever factory to aviod long loading time.
retriever = utils.LazyImport("..rag.retriever")


@dataclass
class MemoryItem:
    """
    This data class represents a memory item of an agent at one step.
    """

    _memory_attributes = []

    def to_dict(self) -> Dict[str, str]:
        """
        Convert the MemoryItem to a dictionary.
        :return: The dictionary.
        """
        return {
            key: value
            for key, value in self.__dict__.items()
            if key in self._memory_attributes
        }

    def to_json(self) -> str:
        """
        Convert the memory item to a JSON string.
        :return: The JSON string.
        """
        return json.dumps(self.to_dict())

    def filter(self, keys: List[str] = []) -> None:
        """
        Fetch the memory item.
        :param keys: The keys to fetch.
        :return: The filtered memory item.
        """

        return {key: value for key, value in self.to_dict().items() if key in keys}

    def set_value(self, key: str, value: str) -> None:
        """
        Add a field to the memory item.
        :param key: The key of the field.
        :param value: The value of the field.
        """
        setattr(self, key, value)

        if key not in self._memory_attributes:
            self._memory_attributes.append(key)

    def set_values_from_dict(self, values: Dict[str, str]) -> None:
        """
        Add fields to the memory item.
        :param values: The values of the fields.
        """
        for key, value in values.items():
            self.set_value(key, value)

    def get_value(self, key: str) -> Optional[str]:
        """
        Get the value of the field.
        :param key: The key of the field.
        :return: The value of the field.
        """

        return getattr(self, key, None)

    def get_values(self, keys: List[str]) -> dict:
        """
        Get the values of the fields.
        :param keys: The keys of the fields.
        :return: The values of the fields.
        """
        return {key: self.get_value(key) for key in keys}

    @property
    def attributes(self) -> List[str]:
        """
        Get the attributes of the memory item.
        :return: The attributes.
        """
        return self._memory_attributes


@dataclass
class Memory:
    """
    This data class represents a memory of an agent.
    """

    _content: List[MemoryItem] = field(default_factory=list)

    def load(self, content: List[MemoryItem]) -> None:
        """
        Load the data from the memory.
        :param key: The key of the data.
        """
        self._content = content

    def filter_memory_from_steps(self, steps: List[int]) -> List[Dict[str, str]]:
        """
        Filter the memory from the steps.
        :param steps: The steps to filter.
        :return: The filtered memory.
        """
        return [item.to_dict() for item in self._content if item.step in steps]

    def filter_memory_from_keys(self, keys: List[str]) -> List[Dict[str, str]]:
        """
        Filter the memory from the keys. If an item does not have the key, the key will be ignored.
        :param keys: The keys to filter.
        :return: The filtered memory.
        """
        return [item.filter(keys) for item in self._content]

    def add_memory_item(self, memory_item: MemoryItem) -> None:
        """
        Add a memory item to the memory.
        :param memory_item: The memory item to add.
        """
        self._content.append(memory_item)

    def clear(self) -> None:
        """
        Clear the memory.
        """
        self._content = []

    @property
    def length(self) -> int:
        """
        Get the length of the memory.
        :return: The length of the memory.
        """
        return len(self._content)

    def delete_memory_item(self, step: int) -> None:
        """
        Delete a memory item from the memory.
        :param step: The step of the memory item to delete.
        """
        self._content = [item for item in self._content if item.step != step]

    def to_json(self) -> str:
        """
        Convert the memory to a JSON string.
        :return: The JSON string.
        """

        return json.dumps(
            [item.to_dict() for item in self._content if item is not None]
        )

    def get_latest_item(self) -> MemoryItem:
        """
        Get the latest memory item.
        :return: The latest memory item.
        """
        if self.length == 0:
            return None
        return self._content[-1]

    @property
    def content(self) -> List[MemoryItem]:
        """
        Get the content of the memory.
        :return: The content of the memory.
        """
        return self._content


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

    @property
    def complete(self) -> bool:
        """
        Indicates whether the current instruction execution is complete.
        :returns: complete (bool): True if execution is complete; False otherwise.
        """
        self._complete = self._status.upper() == Status.FINISH

        return self._complete

    @property
    def status(self) -> str:
        """
        Get the status of the agent.
        :return: The status of the agent.
        """
        return self._status

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

    def get_host(self):
        """
        Get the host of the agent.
        :return: The host of the agent.
        """
        return self._host

    def set_host(self, host: BasicAgent):
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
    def message_constructor(self) -> List[dict]:
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

    def update_step(self, step=1) -> None:
        """
        Update the step of the agent.
        """
        self._step += step

    def update_status(self, status: str) -> None:
        """
        Update the status of the agent.
        :param status: The status of the agent.
        """
        self._status = status

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

    def get_step(self) -> int:
        """
        Get the step of the agent.
        :return: The step of the agent.
        """
        return self._step

    def get_status(self) -> str:
        """
        Get the status of the agent.
        :return: The status of the agent.
        """
        return self._status

    def reflection(self, original_message, response, user_content) -> None:
        """
        TODO:
        Reflect on the action.
        """

        pass

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
