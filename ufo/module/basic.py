# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


"""
This module contains the basic classes of Round and Session for the UFO system.

A round of a session in UFO manages a single user request and consists of multiple steps. 

A session may consists of multiple rounds of interactions.

The session is the core class of UFO. It manages the state transition and handles the different states, using the state pattern.

For more details definition of the state pattern, please refer to the state.py module.
"""

import logging
import os
from abc import ABC, abstractmethod
from logging import Logger
from typing import Type

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agent.agent import AgentFactory, HostAgent
from ufo.config.config import Config
from ufo.experience.summarizer import ExperienceSummarizer
from ufo.module.processors.basic import BaseProcessor
from ufo.module.state import (
    ErrorState,
    MaxStepReachedState,
    NoneState,
    Status,
    StatusToStateMapper,
)

configs = Config.get_instance().config_data


class BaseRound(ABC):
    """
    A round of a session in UFO.
    A round manages a single user request and consists of multiple steps. A session may consists of multiple rounds of interactions.
    """

    def __init__(
        self,
        task: str,
        logger: Logger,
        request_logger: Logger,
        host_agent: HostAgent,
        request: str,
    ) -> None:
        """
        Initialize a round.
        :param task: The name of current task.
        :param logger: The logger for the response and error.
        :param request_logger: The logger for the request string.
        :param host_agent: The host agent.
        :param request: The user request at the current round.
        """
        # Step-related properties
        self._step = 0

        # Logging-related properties
        self.log_path = f"logs/{task}/"
        self.logger = logger
        self.request_logger = request_logger

        # Agent-related properties
        self.host_agent = host_agent
        self.app_agent = None

        # Status-related properties
        self._status = Status.APP_SELECTION

        # Application-related properties
        self.application = ""
        self.app_root = ""
        self.app_window = None

        # Cost and reannotate-related properties
        self._cost = 0.0
        self.control_reannotate = []

        # Request-related properties
        self.request = request

        # round_num and global step-related properties
        self.round_num = None
        self.session_step = None

    @abstractmethod
    def process_application_selection(self) -> None:
        """
        Select an application to interact with.
        """

        pass

    @abstractmethod
    def process_action_selection(self) -> None:
        """
        Select an action with the application.
        """

        pass

    @abstractmethod
    def _create_host_agent_processor(
        self, processor_class: Type["BaseProcessor"]
    ) -> BaseProcessor:
        """
        Create a host agent processor.
        :param processor_class: The processor class.
        :return: The processor instance.
        """

        pass

    @abstractmethod
    def _create_app_agent_processor(
        self, processor_class: Type["BaseProcessor"]
    ) -> BaseProcessor:
        """
        Create a host agent processor.
        :param processor_class: The processor class.
        :return: The processor instance.
        """

        pass

    def _run_step(self, processor: BaseProcessor) -> None:
        """
        Run a step.
        :param processor: The processor.
        """
        processor.process()

        self._status = processor.get_process_status()
        self._step += processor.get_process_step()
        self.update_cost(processor.get_process_cost())

    def get_status(self) -> str:
        """
        Get the status of the round.
        return: The status of the round.
        """
        return self._status

    def get_step(self) -> int:
        """
        Get the local step of the round.
        return: The step of the round.
        """
        return self._step

    def get_cost(self) -> float:
        """
        Get the cost of the round.
        return: The cost of the round.
        """
        return self._cost

    def print_cost(self) -> None:
        """
        Print the total cost of the round.
        """

        total_cost = self.get_cost()
        if isinstance(total_cost, float):
            formatted_cost = "${:.2f}".format(total_cost)
            utils.print_with_color(
                f"Request total cost for current round is {formatted_cost}", "yellow"
            )

    def get_results(self) -> str:
        """
        Get the results of the round.
        return: The results of the round.
        """

        action_history = self.host_agent.get_global_action_memory().content

        if len(action_history) > 0:
            result = action_history[-1].to_dict().get("Results")
        else:
            result = ""
        return result

    def set_index(self, index: int) -> None:
        """
        Set the round index of the round.
        """
        self.round_num = index

    def set_session_step(self, session_step: int) -> None:
        """
        Set the global step of the round.
        """
        self.session_step = session_step

    def get_application_window(self) -> UIAWrapper:
        """
        Get the application of the session.
        return: The application of the session.
        """
        return self.app_window

    def set_application_window(self, app_window: UIAWrapper) -> None:
        """
        Set the application window.
        :param app_window: The application window.
        """
        self.app_window = app_window

    def update_cost(self, cost: float) -> None:
        """
        Update the cost of the round.
        """
        if isinstance(cost, float) and isinstance(self._cost, float):
            self._cost += cost
        else:
            self._cost = None


class BaseSession(ABC):
    """
    A basic session in UFO. A session consists of multiple rounds of interactions.
    The handle function is the core function to handle the session. UFO runs with the state transition and handles the different states, using the state pattern.
    A session follows the following steps:
    1. Begins with the ''APP_SELECTION'' state for the HostAgent to select an application.
    2. After the application is selected, the session moves to the ''CONTINUE'' state for the AppAgent to select an action. This process continues until all the actions are completed.
    3. When all the actions are completed for the current user request at a round, the session moves to the ''FINISH'' state.
    4. The session will ask the user if they want to continue with another request. If the user wants to continue, the session will start a new round and move to the ''APP_SELECTION'' state.
    5. If the user does not want to continue, the session will transition to the ''COMPLETE'' state.
    6. At this point, the session will ask the user if they want to save the experience. If the user wants to save the experience, the session will save the experience and terminate.
    """

    def __init__(self, task: str) -> None:
        """
        Initialize a session.
        :param task: The name of current task.
        """

        # Task-related properties
        self.task = task
        self._step = 0
        self._round = 0

        # Logging-related properties
        self.log_path = f"logs/{self.task}/"
        utils.create_folder(self.log_path)
        self.logger = self.initialize_logger(self.log_path, "response.log")
        self.request_logger = self.initialize_logger(self.log_path, "request.log")

        # Agent-related properties
        self.host_agent = AgentFactory.create_agent(
            "host",
            "HostAgent",
            configs["HOST_AGENT"]["VISUAL_MODE"],
            configs["HOSTAGENT_PROMPT"],
            configs["HOSTAGENT_EXAMPLE_PROMPT"],
            configs["API_PROMPT"],
            configs["ALLOW_OPENAPP"],
        )
        self.app_agent = None

        # Status and state-related properties
        self._status = Status.APP_SELECTION
        self._state = StatusToStateMapper().get_appropriate_state(self._status)

        # Application-related properties
        self.application = ""
        self.app_root = ""
        self.app_window = None

        # Cost and reannotate-related properties
        self._cost = 0.0
        self.control_reannotate = []

    @abstractmethod
    def create_round(self):
        """
        Create a new round.
        """

        pass

    def experience_saver(self) -> None:
        """
        Save the current trajectory as agent experience.
        """
        utils.print_with_color(
            "Summarizing and saving the execution flow as experience...", "yellow"
        )

        summarizer = ExperienceSummarizer(
            configs["APP_AGENT"]["VISUAL_MODE"],
            configs["EXPERIENCE_PROMPT"],
            configs["APPAGENT_EXAMPLE_PROMPT"],
            configs["API_PROMPT"],
        )
        experience = summarizer.read_logs(self.log_path)
        summaries, total_cost = summarizer.get_summary_list(experience)

        experience_path = configs["EXPERIENCE_SAVED_PATH"]
        utils.create_folder(experience_path)
        summarizer.create_or_update_yaml(
            summaries, os.path.join(experience_path, "experience.yaml")
        )
        summarizer.create_or_update_vector_db(
            summaries, os.path.join(experience_path, "experience_db")
        )

        self.update_cost(cost=total_cost)
        utils.print_with_color("The experience has been saved.", "magenta")

    @abstractmethod
    def start_new_round(self) -> None:
        """
        Start a new round.
        """

        pass

    @abstractmethod
    def round_hostagent_execution(self) -> None:
        """
        Execute the host agent in the current round.
        """

        pass

    @abstractmethod
    def round_appagent_execution(self) -> None:
        """
        Execute the app agent in the current round.
        """

        pass

    def get_current_round(self) -> BaseRound:
        """
        Get the current round.
        return: The current round.
        """
        return self._current_round

    def get_round_num(self) -> int:
        """
        Get the round of the session.
        return: The round of the session.
        """
        return self._round

    def get_status(self) -> str:
        """
        Get the status of the session.
        return: The status of the session.
        """
        return self._status

    def get_state(self) -> object:
        """
        Get the state of the session.
        return: The state of the session.
        """
        return self._state

    def get_step(self) -> int:
        """
        Get the step of the session.
        return: The step of the session.
        """
        return self._step

    def get_cost(self) -> float:
        """
        Get the cost of the session.
        return: The cost of the session.
        """
        return self._cost

    def print_cost(self) -> None:
        """
        Print the total cost of the session.
        """

        total_cost = self.get_cost()
        if isinstance(total_cost, float):
            formatted_cost = "${:.2f}".format(total_cost)
            utils.print_with_color(f"Request total cost is {formatted_cost}", "yellow")

    def get_results(self) -> str:
        """
        Get the results of the session.
        return: The results of the session.
        """

        action_history = self.host_agent.get_global_action_memory().content

        if len(action_history) > 0:
            result = action_history[-1].to_dict().get("Results")
        else:
            result = ""
        return result

    def get_application_window(self) -> UIAWrapper:
        """
        Get the application of the session.
        return: The application of the session.
        """
        return self.app_window

    def set_application_window(self, app_window: UIAWrapper) -> None:
        """
        Set the application window.
        :param app_window: The application window.
        """
        self.app_window = app_window

    def update_cost(self, cost: float) -> None:
        """
        Update the cost of the session.
        """
        if isinstance(cost, float) and isinstance(self._cost, float):
            self._cost += cost
        else:
            self._cost = None

    def is_finish(self) -> bool:
        """
        Check if the session is ended.
        return: True if the session is ended, otherwise False.
        """

        # Finish the session if the state is ErrorState, MaxStepReachedState, or NoneState.
        return (
            True
            if isinstance(
                self.get_state(),
                (ErrorState, MaxStepReachedState, NoneState),
            )
            else False
        )

    def set_state(self, state) -> None:
        """
        Set the state of the session.
        """
        self._state = state

    def handle(self) -> None:
        """
        Handle the session.
        """
        self._state.handle(self)

    @property
    def session_type(self) -> str:
        """
        Get the class name of the session.
        return: The class name of the session.
        """
        return self.__class__.__name__

    @staticmethod
    def initialize_logger(log_path: str, log_filename: str) -> logging.Logger:
        """
        Initialize logging.
        log_path: The path of the log file.
        log_filename: The name of the log file.
        return: The logger.
        """
        # Code for initializing logging
        logger = logging.Logger(log_filename)

        if not configs["PRINT_LOG"]:
            # Remove existing handlers if PRINT_LOG is False
            logger.handlers = []

        log_file_path = os.path.join(log_path, log_filename)
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        formatter = logging.Formatter("%(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(configs["LOG_LEVEL"])

        return logger
