
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from typing import List, Dict, Type
from dataclasses import dataclass


class BasicAgent(ABC):
    """
    The BasicAgent class is the abstract class for the agent.
    """

    _registry: Dict[str, Type['BasicAgent']] = {}

    def __init__(self, agent_type: str):
        """
        Initialize the BasicAgent.
        :param agent_type: The type of the agent.
        :param memory: The memory of the agent.
        """
        self.agent_type = agent_type



    @abstractmethod
    def get_prompter(self) -> str:
        """
        Get the prompt for the agent.
        :return: The prompt.
        """
        pass


    def get_response(self, prompt: str) -> str:
        """
        Get the response for the prompt.
        :param prompt: The prompt.
        :return: The response.
        """
        pass


    def print_response(self, response: str) -> None:
        """
        Print the response.
        :param response: The response.
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


    def get_memory(self):
        """
        Get the memory of the agent.
        :return: The memory of the agent.
        """
        return self.__memory
    

    @classmethod
    def register(cls, name: str, agent_cls: Type['BasicAgent']):
        """
        Registers an agent class in the registry.

        Parameters:
        - name (str): The name to register the class under.
        - agent_cls (Type['Agent']): The class to register.
        """
        if name in cls._registry:
            raise ValueError(f"Agent class already registered under '{name}'.")
        cls._registry[name] = agent_cls


    @classmethod
    def get_cls(cls, name: str) -> Type['BasicAgent']:
        """
        Retrieves an agent class from the registry.

        Parameters:
        - name (str): The name of the class to retrieve

        Returns:
        - agent_cls (Type['Agent']): The class registered under the specified name.
        """
        if name not in cls._registry:
            raise ValueError(f"No agent class registered under '{name}'.")
        return cls._registry[name]

    

    
@dataclass
class MemoryItem:
    step: int
    thought: str
    action: str

    
@dataclass
class BasicMemory(ABC):
    """
    This data class represents a memory of an agent.
    """

    content: str
    # TODO: add more fields as needed

    @abstractmethod
    def save(self, data: dict) -> None:
        """
        Save the data to the memory.
        :param data: The data to save.
        """
        pass

    @abstractmethod
    def load(self, key: str) -> dict:
        """
        Load the data from the memory.
        :param key: The key of the data.
        :return: The data.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Delete the data from the memory.
        :param key: The key of the data.
        """
        pass


    @abstractmethod
    def clear(self) -> None:
        """
        Clear the memory.
        """
        pass