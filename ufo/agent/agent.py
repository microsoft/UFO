# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from typing import List, Dict, Type
from dataclasses import dataclass


class BasicAgent(ABC):
    """
    The BasicAgent class is the abstract class for the agent.
    """

    def __init__(self, agent_type: str, memory: Type['BasicMemory']):
        """
        Initialize the BasicAgent.
        :param agent_type: The type of the agent.
        :param memory: The memory of the agent.
        """
        self.agent_type = agent_type
        self.memory = memory



    @abstractmethod
    def get_prompt(self) -> str:
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

    

    

@dataclass
class BasicMemory(ABC):
    """
    This data class represents a memory of an agent.
    """

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