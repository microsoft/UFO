# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


"""
This module contains the basic classes of Round and Session for the UFO system.

A round of a session in UFO manages a single user request and consists of multiple steps. 

A session may consists of multiple rounds of interactions.

The session is the core class of UFO. It manages the state transition and handles the different states, using the state pattern.

For more details definition of the state pattern, please refer to the state.py module.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Optional

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agents.agent.basic import BasicAgent
from ufo.agents.agent.evaluation_agent import EvaluationAgent
from ufo.agents.agent.host_agent import AgentFactory, HostAgent
from ufo.agents.states.basic import AgentState
from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.config.config import Config
from ufo.experience.summarizer import ExperienceSummarizer
from ufo.modules.context import Context, ContextNames

configs = Config.get_instance().config_data


class BaseRound(ABC):
    """
    A round of a session in UFO.
    A round manages a single user request and consists of multiple steps. A session may consists of multiple rounds of interactions.
    """

    def __init__(
        self,
        request: str,
        agent: BasicAgent,
        context: Context,
        should_evaluate: bool,
        id: int,
    ) -> None:
        """
        Initialize a round.
        :param request: The request of the round.
        :param agent: The initial agent of the round.
        :param context: The shared context of the round.
        :param should_evaluate: Whether to evaluate the round.
        :param id: The id of the round.
        """

        self._request = request
        self._context = context
        self._agent = agent
        self._state = agent.state
        self._id = id
        self._should_evaluate = should_evaluate

        self._init_context()

    def _init_context(self) -> None:
        """
        Update the context of the round.
        """

        # Initialize the round step
        round_step = {self.id: self.step}
        self.context.update_dict(ContextNames.ROUND_STEP, round_step)

        # Initialize the round cost
        round_cost = {self.id: self.cost}
        self.context.update_dict(ContextNames.ROUND_COST, round_cost)

        # Initialize the round request and the current round id
        self.context.set(ContextNames.REQUEST, self.request)
        self.context.set(ContextNames.CURRENT_ROUND_ID, self.id)

    def run(self) -> None:
        """
        Run the round.
        """
        while not self.is_finished():
            print(self.state.name())
            self._agent.handle(self._context)
            self._agent = self._agent.state.next_agent(self._agent)
            self._state = self._agent.state.next_state(self._agent)
            self._agent.set_state(self._state)

        if self._should_evaluate:
            self.evaluation()

    def is_finished(self) -> bool:
        """
        Check if the round is finished.
        return: True if the round is finished, otherwise False.
        """
        self._state.is_round_end()

    @property
    def state(self) -> AgentState:
        """
        Get the status of the round.
        return: The status of the round.
        """
        return self._state

    @property
    def step(self) -> int:
        """
        Get the local step of the round.
        return: The step of the round.
        """
        return self._context.get(ContextNames.ROUND_STEP).get(self.id, 0)

    @property
    def cost(self) -> float:
        """
        Get the cost of the round.
        return: The cost of the round.
        """
        return self._context.get(ContextNames.ROUND_COST).get(self.id, 0)

    @property
    def request(self) -> str:
        """
        Get the request of the round.
        return: The request of the round.
        """
        return self._request

    @property
    def id(self) -> int:
        """
        Get the id of the round.
        return: The id of the round.
        """
        return self._id

    @property
    def context(self) -> Context:
        """
        Get the context of the round.
        return: The context of the round.
        """
        return self._context

    def print_cost(self) -> None:
        """
        Print the total cost of the round.
        """

        total_cost = self.cost
        if isinstance(total_cost, float):
            formatted_cost = "${:.2f}".format(total_cost)
            utils.print_with_color(
                f"Request total cost for current round is {formatted_cost}", "yellow"
            )

    def evaluation(self) -> None:
        """
        TODO: Evaluate the round.
        """
        pass

    @property
    def application_window(self) -> UIAWrapper:
        """
        Get the application of the session.
        return: The application of the session.
        """
        return self._context.get(ContextNames.APPLICATION_WINDOW)

    @application_window.setter
    def application_window(self, app_window: UIAWrapper) -> None:
        """
        Set the application window.
        :param app_window: The application window.
        """
        self._context.set(ContextNames.APPLICATION_WINDOW, app_window)


class BaseSession(ABC):
    """
    A basic session in UFO. A session consists of multiple rounds of interactions.
    The handle function is the core function to handle the session. UFO runs with the state transition and handles the different states, using the state pattern.
    A session follows the following steps:
    1. Begins with the ''CONTINUE'' state for the HostAgent to select an application.
    2. After the application is selected, the session moves to the ''CONTINUE'' state for the AppAgent to select an action. This process continues until all the actions are completed.
    3. When all the actions are completed for the current user request at a round, the session moves to the ''FINISH'' state.
    4. The session will ask the user if they want to continue with another request. If the user wants to continue, the session will start a new round and move to the ''SWITCH'' state.
    5. If the user does not want to continue, the session will transition to the ''COMPLETE'' state.
    6. At this point, the session will ask the user if they want to save the experience. If the user wants to save the experience, the session will save the experience and terminate.
    """

    def __init__(self, task: str, should_evaluate: bool) -> None:
        """
        Initialize a session.
        :param task: The name of current task.
        :param should_evaluate: Whether to evaluate the session.
        """

        self._should_evaluate = should_evaluate

        # Logging-related properties
        self.log_path = f"logs/{task}/"
        utils.create_folder(self.log_path)

        self._rounds: Dict[int, BaseRound] = {}

        self._context = Context()
        self._init_context()
        self._finish = False

        self._host_agent: HostAgent = AgentFactory.create_agent(
            "host",
            "HostAgent",
            configs["HOST_AGENT"]["VISUAL_MODE"],
            configs["HOSTAGENT_PROMPT"],
            configs["HOSTAGENT_EXAMPLE_PROMPT"],
            configs["API_PROMPT"],
            configs["ALLOW_OPENAPP"],
        )

    def run(self) -> None:
        """
        Run the session.
        """
        while not self.is_finished():

            round = self.create_new_round()
            if round is None:
                break
            round.run()

        self.capture_last_snapshot()

        if self._should_evaluate:
            self.evaluation()

    @abstractmethod
    def create_new_round(self) -> Optional[BaseRound]:
        """
        Create a new round.
        """
        pass

    @abstractmethod
    def get_request(self) -> str:
        """
        Get the request of the session.
        return: The request of the session.
        """
        pass

    def create_following_round(self) -> BaseRound:
        """
        Create a following round.
        return: The following round.
        """
        pass

    def add_round(self, id: int, round: BaseRound) -> None:
        """
        Add a round to the session.
        :param id: The id of the round.
        :param round: The round to be added.
        """
        self._rounds[id] = round

    def _init_context(self) -> None:
        """
        Initialize the context of the session.
        """

        # Initialize the logger
        logger = self.initialize_logger(self.log_path, "response.log")
        request_logger = self.initialize_logger(self.log_path, "request.log")

        self.context.set(ContextNames.LOGGER, logger)
        self.context.set(ContextNames.REQUEST_LOGGER, request_logger)

        # Initialize the session cost and step
        self.context.set(ContextNames.SESSION_COST, 0)
        self.context.set(ContextNames.SESSION_STEP, 0)

    @property
    def context(self) -> Context:
        """
        Get the context of the session.
        return: The context of the session.
        """
        return self._context

    @property
    def cost(self) -> float:
        """
        Get the cost of the session.
        return: The cost of the session.
        """
        return self.context.get(ContextNames.SESSION_COST)

    @property
    def step(self) -> int:
        """
        Get the step of the session.
        return: The step of the session.
        """
        return self.context.get(ContextNames.SESSION_STEP)

    @property
    def total_rounds(self) -> int:
        """
        Get the total number of rounds in the session.
        return: The total number of rounds in the session.
        """
        return len(self._rounds)

    @property
    def rounds(self) -> Dict[int, BaseRound]:
        """
        Get the rounds of the session.
        return: The rounds of the session.
        """
        return self._rounds

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

    def print_cost(self) -> None:
        """
        Print the total cost of the session.
        """

        if isinstance(self.cost, float):
            formatted_cost = "${:.2f}".format(self.cost)
            utils.print_with_color(f"Request total cost is {formatted_cost}", "yellow")

    @property
    def application_window(self) -> UIAWrapper:
        """
        Get the application of the session.
        return: The application of the session.
        """
        return self._context.get(ContextNames.APPLICATION_WINDOW)

    @application_window.setter
    def application_window(self, app_window: UIAWrapper) -> None:
        """
        Set the application window.
        :param app_window: The application window.
        """
        self._context.set(ContextNames.APPLICATION_WINDOW, app_window)

    def is_finished(self) -> bool:
        """
        Check if the session is ended.
        return: True if the session is ended, otherwise False.
        """
        if self._finish or self.step >= configs["MAX_STEP"]:
            return True
        return False

    @abstractmethod
    def request_to_evaluate(self) -> str:
        """
        Get the request to evaluate.
        return: The request(s) to evaluate.
        """
        pass

    def evaluation(self) -> None:
        """
        Evaluate the session.
        """
        utils.print_with_color("Evaluating the session...", "yellow")
        evaluator = EvaluationAgent(
            name="eva_agent",
            app_root_name=self.context.get(ContextNames.APPLICATION_ROOT_NAME),
            is_visual=configs["APP_AGENT"]["VISUAL_MODE"],
            main_prompt=configs["EVALUATION_PROMPT"],
            example_prompt="",
            api_prompt=configs["API_PROMPT"],
        )

        requests = self.request_to_evaluate()
        result, cost = evaluator.evaluate(request=requests, log_path=self.log_path)
        self.context.add_value(ContextNames.SESSION_COST, cost)

        evaluator.print_response(result)

        logger = self.context.get(ContextNames.LOGGER)
        logger.info(json.dumps(result))

    @property
    def session_type(self) -> str:
        """
        Get the class name of the session.
        return: The class name of the session.
        """
        return self.__class__.__name__

    def capture_last_snapshot(self) -> None:
        """
        Capture the last snapshot of the application, including the screenshot and the XML file if configured.
        """

        # Capture the final screenshot
        screenshot_save_path = self.log_path + f"action_step_final.png"

        PhotographerFacade().capture_app_window_screenshot(
            self.application_window, save_path=screenshot_save_path
        )

        # Save the final XML file
        if configs["LOG_XML"]:
            log_abs_path = os.path.abspath(self.log_path)
            xml_save_path = os.path.join(log_abs_path, f"xml/action_step_final.xml")

            app_agent = self._host_agent.get_active_appagent()
            if app_agent is not None:
                app_agent.Puppeteer.save_to_xml(xml_save_path)

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
