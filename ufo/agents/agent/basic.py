# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional, Type, Union

from ufo import utils
from ufo.agents.memory.memory import Memory, MemoryItem

from ufo.agents.states.basic import AgentState, AgentStatus
from ufo.automator import puppeteer
from ufo.config.config import Config
from ufo.llm import llm_call
from ufo.module.context import Context
from ufo.module.interactor import question_asker

# Lazy import the retriever factory to aviod long loading time.
retriever = utils.LazyImport("..rag.retriever")

# To avoid circular import
if TYPE_CHECKING:
    from ufo.agents.agent.host_agent import HostAgent
    from ufo.agents.processors.basic import BaseProcessor
    from ufo.agents.memory.blackboard import Blackboard

configs = Config.get_instance().config_data


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
        self._status = self.status_manager.CONTINUE.value
        self._register_self()
        self.retriever_factory = retriever.RetrieverFactory()
        self._memory = Memory()
        self._host = None
        self._processor: Optional[BaseProcessor] = None
        self._state = None
        self.Puppeteer: puppeteer.AppPuppeteer = None

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
        return self._state

    @property
    def memory(self) -> Memory:
        """
        Get the memory of the agent.
        :return: The memory of the agent.
        """
        return self._memory

    @memory.setter
    def memory(self, memory: Memory) -> None:
        """
        Set the memory of the agent.
        :param memory: The memory of the agent.
        """
        self._memory = memory

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

    def create_puppeteer_interface(self) -> puppeteer.AppPuppeteer:
        """
        Create the puppeteer interface.
        """
        pass

    @property
    def host(self) -> HostAgent:
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
        cls,
        message: List[dict],
        namescope: str,
        use_backup_engine: bool,
        configs=configs,
    ) -> str:
        """
        Get the response for the prompt.
        :param message: The message for LLMs.
        :param namescope: The namescope for the LLMs.
        :param use_backup_engine: Whether to use the backup engine.
        :param configs: The configurations.
        :return: The response.
        """
        response_string, cost = llm_call.get_completion(
            message, namescope, use_backup_engine=use_backup_engine, configs=configs
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

    def set_memory_from_list_of_dicts(self, data: List[Dict[str, str]]) -> None:
        """
        Set the memory from the list of dictionaries.
        :param data: The list of dictionaries.
        """

        assert isinstance(data, list), "The data should be a list of dictionaries."

        self._memory.from_list_of_dicts(data)

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

    def set_state(self, state: AgentState) -> None:
        """
        Set the state of the agent.
        :param state: The state of the agent.
        """

        assert issubclass(
            type(self), state.agent_class()
        ), f"The state is only for agent type of {state.agent_class()}, but the current agent is {type(self)}."

        self._state = state

    def handle(self, context: Context) -> None:
        """
        Handle the agent.
        :param context: The context for the agent.
        """
        self.state.handle(self, context)

    def process(self, context: Context) -> None:
        """
        Process the agent.
        """
        pass

    def create_puppeteer_interface(self) -> puppeteer.AppPuppeteer:
        """
        Create the puppeteer interface.
        """
        pass

    def process_resume(self) -> None:
        """
        Resume the process.
        """
        if self.processor:
            self.processor.resume()

    def process_asker(self, ask_user: bool = True) -> None:
        """
        Ask for the process.
        :param ask_user: Whether to ask the user for the questions.
        """

        _ask_message = "Could you please answer the following questions to help me understand your needs and complete the task?"
        _none_answer_message = "The answer for the question is not available, please proceed with your own knowledge or experience, or leave it as a placeholder. Do not ask the same question again."

        if self.processor:
            question_list = self.processor.question_list

            if ask_user:
                utils.print_with_color(
                    _ask_message,
                    "yellow",
                )

            for index, question in enumerate(question_list):
                if ask_user:
                    answer = question_asker(question, index + 1)
                    if not answer.strip():
                        continue
                    qa_pair = {"question": question, "answer": answer}

                    utils.append_string_to_file(
                        configs["QA_PAIR_FILE"], json.dumps(qa_pair)
                    )

                else:
                    qa_pair = {
                        "question": question,
                        "answer": _none_answer_message,
                    }

                self.blackboard.add_questions(qa_pair)

    @abstractmethod
    def process_comfirmation(self) -> None:
        """
        Confirm the process.
        """
        pass

    @property
    def processor(self) -> BaseProcessor:
        """
        Get the processor.
        :return: The processor.
        """
        return self._processor

    @processor.setter
    def processor(self, processor: BaseProcessor) -> None:
        """
        Set the processor.
        :param processor: The processor.
        """
        self._processor = processor

    @property
    def status_manager(self) -> AgentStatus:
        """
        Get the status manager.
        :return: The status manager.
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

    @property
    def default_state(self) -> AgentState:
        """
        Get the default state of the agent.
        :return: The default state of the agent.
        """
        pass


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
