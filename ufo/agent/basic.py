
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from typing import List, Dict, Type
from dataclasses import dataclass, field
from ..llm import llm_call
from .. import utils
import json


@dataclass
class MemoryItem:
    """
    This data class represents a memory item of an agent at one step.
    """

    _memory_attributes = []

    def to_dict(self) -> dict:
        """
        Convert the MemoryItem to a dictionary.
        :return: The dictionary.
        """
        return {key: value for key, value in self.__dict__.items() if key in self._memory_attributes}
    

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

    
    def set_values_from_dict(self, values: dict) -> None:
        """
        Add fields to the memory item.
        :param values: The values of the fields.
        """
        for key, value in values.items():
            self.set_value(key, value)


    def get_value(self, key: str) -> object:
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
class Memory():
    """
    This data class represents a memory of an agent.
    """

    _content: List[MemoryItem] = field(default_factory=list)

    
    def load(self, content: List[MemoryItem]) -> dict:
        """
        Load the data from the memory.
        :param key: The key of the data.
        """
        self._content = content
        

    def filter_memory_from_steps(self, steps: List[int]) -> List[dict]:
        """
        Filter the memory from the steps.
        :param steps: The steps to filter.
        :return: The filtered memory.
        """
        return [item.to_dict() for item in self._content if item.step in steps]
    
    
    def filter_memory_from_keys(self, keys: List[str]) -> List[dict]:
        """
        Filter the memory from the keys.
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

        return json.dumps([item.to_dict() for item in self._content])




class BasicAgent(ABC):
    """
    The BasicAgent class is the abstract class for the agent.
    """

    _registry: Dict[str, Type['BasicAgent']] = {}

    def __init__(self, name: str):
        """
        Initialize the BasicAgent.
        :param agent_type: The type of the agent.
         :param memory: The memory of the agent.
        :param memory: The memory of the agent.
        """
        self._step = 0
        self._complete = False
        self._name = name
        self._status = None
        

    @property
    def complete(self) -> bool:
        """
        Indicates whether the current instruction execution is complete.

        :returns: complete (bool): True if execution is complete; False otherwise.
        """
        self._complete = self._status.lower() == "finish"

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
    def get_response(cls, message: List[dict], namescope, use_backup_engine) -> str:
        """
        Get the response for the prompt.
        :param prompt: The prompt.
        :return: The response.
        """
        response_string, cost = llm_call.get_completion(message, namescope, use_backup_engine=use_backup_engine)
        return response_string, cost
    

    @staticmethod
    def response_to_dict(response: str) -> dict:
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


    def update_memory(self, memory_item: MemoryItem) -> None:
        """
        Update the memory of the agent.
        :param memory_item: The memory item to add.
        """
        self._memory.add_memory_item(memory_item)



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
    def register(cls, name: str, agent_cls: Type['BasicAgent']) -> None:
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