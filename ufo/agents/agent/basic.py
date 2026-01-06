# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple, Type, Union

from ufo import utils
from ufo.agents.memory.memory import Memory, MemoryItem
from ufo.agents.processors.core.processor_framework import ProcessorTemplate
from ufo.agents.states.basic import AgentState, AgentStatus
from config.config_loader import get_ufo_config
from ufo.llm import llm_call
from ufo.module.context import Context
from ufo.module.interactor import question_asker
from rich.console import Console

# Lazy import the retriever factory to aviod long loading time.
retriever = utils.LazyImport("..rag.retriever")

# To avoid circular import
if TYPE_CHECKING:
    from ufo.agents.agent.host_agent import HostAgent
    from ufo.agents.memory.blackboard import Blackboard


ufo_config = get_ufo_config()
console = Console()


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
        self._processor: Optional[ProcessorTemplate] = None
        self._state = None
        self.logger = logging.getLogger(__name__)

        # Initialize presenter for output formatting
        from ufo.agents.presenters import PresenterFactory

        ufo_config = get_ufo_config()
        presenter_type = ufo_config.system.output_presenter
        self.presenter = PresenterFactory.create_presenter(presenter_type)

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

    @abstractmethod
    async def context_provision(self) -> None:
        """
        Provide the context for the agent.
        """
        pass

    @classmethod
    def get_response(
        cls,
        message: List[dict],
        namescope: str,
        use_backup_engine: bool,
    ) -> Tuple[str, float]:
        """
        Get the response for the prompt.
        :param message: The message for LLMs.
        :param namescope: The namescope for the LLMs.
        :param use_backup_engine: Whether to use the backup engine.
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

    async def handle(self, context: Context) -> None:
        """
        Handle the agent.
        :param context: The context for the agent.
        """
        await self.state.handle(self, context)

    async def process(self, context: Context) -> None:
        """
        Process the agent.
        """
        pass

    async def process_resume(self) -> None:
        """
        Resume the process.
        """
        pass

    def process_asker(self, ask_user: bool = True) -> None:
        """
        Ask for the process.
        :param ask_user: Whether to ask the user for the questions.
        """

        _ask_message = "Could you please answer the following questions to help me understand your needs and complete the task?"
        _none_answer_message = "The answer for the question is not available, please proceed with your own knowledge or experience, or leave it as a placeholder. Do not ask the same question again."

        if self.processor:
            question_list = self.processor.processing_context.get_local("questions", [])

            if ask_user:
                console.print(
                    f"❓ {_ask_message}",
                    style="yellow",
                )

            for index, question in enumerate(question_list):
                if ask_user:
                    answer = question_asker(question, index + 1)
                    if not answer.strip():
                        continue
                    qa_pair = {"question": question, "answer": answer}

                    ufo_config = get_ufo_config()
                    utils.append_string_to_file(
                        ufo_config.system.qa_pair_file, json.dumps(qa_pair)
                    )

                else:
                    qa_pair = {
                        "question": question,
                        "answer": _none_answer_message,
                    }

                self.blackboard.add_questions(qa_pair)

    @abstractmethod
    def process_confirmation(self) -> None:
        """
        Confirm the process.
        """
        pass

    @property
    def processor(self) -> ProcessorTemplate:
        """
        Get the processor.
        :return: The processor.
        """
        return self._processor

    @processor.setter
    def processor(self, processor: ProcessorTemplate) -> None:
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

    @staticmethod
    def get_command_string(command_name: str, params: Dict[str, str]) -> str:
        """
        Generate a function call string.
        :param command_name: The function name.
        :param params: The arguments as a dictionary.
        :return: The function call string.
        """
        # Format the arguments
        args_str = ", ".join(f"{k}={v!r}" for k, v in params.items())

        # Return the function call string
        return f"{command_name}({args_str})"


class AgentRegistry:
    """
    The registry for agent classes.
    """

    _registry: Dict[str, Type["BasicAgent"]] = {}
    logger = logging.getLogger(__name__)
    logger.propagate = True

    @classmethod
    def register(
        cls,
        agent_name: str,
        third_party: Optional[bool] = False,
        processor_cls: Optional[Type["ProcessorTemplate"]] = None,
    ) -> Callable[[Type["BasicAgent"]], Type["BasicAgent"]]:
        """
        Decorator to register an agent class.
        :param name: The name to register the agent class under.
        :return: The class itself (unchanged).
        """

        def decorator(agent_cls: Type["BasicAgent"]) -> Type["BasicAgent"]:

            cls.logger.info(
                f"[AgentRegistry] Registering agent class '{agent_name}': {agent_cls.__name__}"
            )

            if third_party:
                ufo_config = get_ufo_config()
                enabled = ufo_config.system.enabled_third_party_agents
                if agent_name not in enabled:
                    cls.logger.warning(
                        f"[AgentRegistry] Skipping third-party agent '{agent_name}' (not in config)."
                    )
                    return agent_cls

            # if agent_name in cls._registry:
            #     raise ValueError(
            #         f"Agent class already registered under '{agent_name}'."
            #     )
            if processor_cls:
                setattr(agent_cls, "_processor_cls", processor_cls)

                cls.logger.info(
                    f"[AgentRegistry] Registered processor for agent '{agent_name}': {processor_cls.__name__}"
                )
            cls._registry[agent_name] = agent_cls
            return agent_cls

        return decorator

    @classmethod
    def get(cls, agent_name: str) -> Type["BasicAgent"]:
        """
        Retrieve an agent class by name.
        """
        if agent_name not in cls._registry:
            raise ValueError(f"No agent class registered under '{agent_name}'.")
        return cls._registry[agent_name]

    @classmethod
    def list_agents(cls) -> Dict[str, Type["BasicAgent"]]:
        """
        List all registered agent classes.
        """
        return dict(cls._registry)
