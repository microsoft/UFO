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
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agents.agent.app_agent import AppAgent
from ufo.agents.agent.basic import BasicAgent
from ufo.agents.agent.evaluation_agent import EvaluationAgent
from ufo.agents.agent.host_agent import AgentFactory, HostAgent
from ufo.agents.states.basic import AgentState, AgentStatus
from ufo.automator.ui_control import ui_tree
from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.config.config import Config
from ufo.experience.summarizer import ExperienceSummarizer
from ufo.module.context import Context, ContextNames
from ufo.trajectory.parser import Trajectory

configs = Config.get_instance().config_data


class BaseRound(ABC):
    """
    A round of a session in UFO.
    A round manages a single user request and consists of multiple steps.
    A session may consists of multiple rounds of interactions.
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
        round_step = {self.id: 0}
        self.context.update_dict(ContextNames.ROUND_STEP, round_step)

        # Initialize the round cost
        round_cost = {self.id: 0}
        self.context.update_dict(ContextNames.ROUND_COST, round_cost)

        # Initialize the round subtask amount
        round_subtask_amount = {self.id: 0}
        self.context.update_dict(
            ContextNames.ROUND_SUBTASK_AMOUNT, round_subtask_amount
        )

        # Initialize the round request and the current round id
        self.context.set(ContextNames.REQUEST, self.request)

        self.context.set(ContextNames.CURRENT_ROUND_ID, self.id)

    def run(self) -> None:
        """
        Run the round.
        """

        while not self.is_finished():

            self.agent.handle(self.context)

            self.state = self.agent.state.next_state(self.agent)
            self.agent = self.agent.state.next_agent(self.agent)

            self.agent.set_state(self.state)

            # If the subtask ends, capture the last snapshot of the application.
            if self.state.is_subtask_end():
                time.sleep(configs["SLEEP_TIME"])
                self.capture_last_snapshot(sub_round_id=self.subtask_amount)
                self.subtask_amount += 1

        self.agent.blackboard.add_requests(
            {"request_{i}".format(i=self.id): self.request}
        )

        if self.application_window is not None:
            self.capture_last_snapshot()

        if self._should_evaluate:
            self.evaluation()

    def is_finished(self) -> bool:
        """
        Check if the round is finished.
        return: True if the round is finished, otherwise False.
        """
        return (
            self.state.is_round_end()
            or self.context.get(ContextNames.SESSION_STEP) >= configs["MAX_STEP"]
        )

    @property
    def agent(self) -> BasicAgent:
        """
        Get the agent of the round.
        return: The agent of the round.
        """
        return self._agent

    @agent.setter
    def agent(self, agent: BasicAgent) -> None:
        """
        Set the agent of the round.
        :param agent: The agent of the round.
        """
        self._agent = agent

    @property
    def state(self) -> AgentState:
        """
        Get the status of the round.
        return: The status of the round.
        """
        return self._state

    @state.setter
    def state(self, state: AgentState) -> None:
        """
        Set the status of the round.
        :param state: The status of the round.
        """
        self._state = state

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
    def subtask_amount(self) -> int:
        """
        Get the subtask amount of the round.
        return: The subtask amount of the round.
        """
        return self._context.get(ContextNames.ROUND_SUBTASK_AMOUNT).get(self.id, 0)

    @subtask_amount.setter
    def subtask_amount(self, value: int) -> None:
        """
        Set the subtask amount of the round.
        :param value: The value to set.
        """
        self._context.current_round_subtask_amount = value

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

    @property
    def log_path(self) -> str:
        """
        Get the log path of the round.

        return: The log path of the round.
        """
        return self._context.get(ContextNames.LOG_PATH)

    def capture_last_snapshot(self, sub_round_id: Optional[int] = None) -> None:
        """
        Capture the last snapshot of the application, including the screenshot and the XML file if configured.
        :param sub_round_id: The id of the sub-round, default is None.
        """

        # Capture the final screenshot
        if sub_round_id is None:
            screenshot_save_path = self.log_path + f"action_round_{self.id}_final.png"
        else:
            screenshot_save_path = (
                self.log_path
                + f"action_round_{self.id}_sub_round_{sub_round_id}_final.png"
            )

        if self.application_window is not None:

            try:
                PhotographerFacade().capture_app_window_screenshot(
                    self.application_window, save_path=screenshot_save_path
                )

            except Exception as e:
                utils.print_with_color(
                    f"Warning: The last snapshot capture failed, due to the error: {e}",
                    "yellow",
                )

            if configs.get("SAVE_UI_TREE", False):
                step_ui_tree = ui_tree.UITree(self.application_window)

                ui_tree_path = os.path.join(self.log_path, "ui_trees")

                ui_tree_file_name = (
                    f"ui_tree_round_{self.id}_final.json"
                    if sub_round_id is None
                    else f"ui_tree_round_{self.id}_sub_round_{sub_round_id}_final.json"
                )

                step_ui_tree.save_ui_tree_to_json(
                    os.path.join(
                        ui_tree_path,
                        ui_tree_file_name,
                    )
                )

            if configs.get("SAVE_FULL_SCREEN", False):

                desktop_save_path = (
                    self.log_path
                    + f"desktop_round_{self.id}_sub_round_{sub_round_id}_final.png"
                )

                # Capture the desktop screenshot for all screens.
                PhotographerFacade().capture_desktop_screen_screenshot(
                    all_screens=True, save_path=desktop_save_path
                )

            # Save the final XML file
            if configs["LOG_XML"]:
                log_abs_path = os.path.abspath(self.log_path)
                xml_save_path = os.path.join(
                    log_abs_path,
                    (
                        f"xml/action_round_{self.id}_final.xml"
                        if sub_round_id is None
                        else f"xml/action_round_{self.id}_sub_round_{sub_round_id}_final.xml"
                    ),
                )

                if issubclass(type(self.agent), HostAgent):

                    app_agent: AppAgent = self.agent.get_active_appagent()
                    app_agent.Puppeteer.save_to_xml(xml_save_path)
                elif issubclass(type(self.agent), AppAgent):
                    app_agent: AppAgent = self.agent
                    app_agent.Puppeteer.save_to_xml(xml_save_path)

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
    A basic session in UFO. A session consists of multiple rounds of interactions and conversations.
    """

    def __init__(self, task: str, should_evaluate: bool, id: int) -> None:
        """
        Initialize a session.
        :param task: The name of current task.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The id of the session.
        """

        self._should_evaluate = should_evaluate
        self._id = id

        # Logging-related properties
        self.log_path = f"logs/{task}/"
        utils.create_folder(self.log_path)

        self._rounds: Dict[int, BaseRound] = {}

        self._context = Context()
        self._init_context()
        self._finish = False
        self._results = {}

        self._host_agent: HostAgent = AgentFactory.create_agent(
            "host",
            "HostAgent",
            configs["HOST_AGENT"]["VISUAL_MODE"],
            configs["HOSTAGENT_PROMPT"],
            configs["HOSTAGENT_EXAMPLE_PROMPT"],
            configs["API_PROMPT"],
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

        if self.application_window is not None:
            self.capture_last_snapshot()

        if self._should_evaluate and not self.is_error():
            self.evaluation()

        if configs.get("LOG_TO_MARKDOWN", True):

            file_path = self.log_path
            trajectory = Trajectory(file_path)
            trajectory.to_markdown(file_path + "/output.md")

        self.print_cost()

    @abstractmethod
    def create_new_round(self) -> Optional[BaseRound]:
        """
        Create a new round.
        """
        pass

    @abstractmethod
    def next_request(self) -> str:
        """
        Get the next request of the session.
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

        # Initialize the ID
        self.context.set(ContextNames.ID, self.id)

        # Initialize the log path and the logger
        logger = self.initialize_logger(self.log_path, "response.log")
        request_logger = self.initialize_logger(self.log_path, "request.log")
        eval_logger = self.initialize_logger(self.log_path, "evaluation.log")

        self.context.set(ContextNames.LOG_PATH, self.log_path)

        self.context.set(ContextNames.LOGGER, logger)
        self.context.set(ContextNames.REQUEST_LOGGER, request_logger)
        self.context.set(ContextNames.EVALUATION_LOGGER, eval_logger)

        # Initialize the session cost and step
        self.context.set(ContextNames.SESSION_COST, 0)
        self.context.set(ContextNames.SESSION_STEP, 0)

    @property
    def id(self) -> int:
        """
        Get the id of the session.
        return: The id of the session.
        """
        return self._id

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

    @cost.setter
    def cost(self, cost: float) -> None:
        """
        Update the cost of the session.
        :param cost: The cost to be updated.
        """
        self.context.set(ContextNames.SESSION_COST, cost)

    @property
    def application_window(self) -> UIAWrapper:
        """
        Get the application of the session.
        return: The application of the session.
        """
        return self.context.get(ContextNames.APPLICATION_WINDOW)

    @application_window.setter
    def application_window(self, app_window: UIAWrapper) -> None:
        """
        Set the application window.
        :param app_window: The application window.
        """
        self.context.set(ContextNames.APPLICATION_WINDOW, app_window)

    @property
    def step(self) -> int:
        """
        Get the step of the session.
        return: The step of the session.
        """
        return self.context.get(ContextNames.SESSION_STEP)

    @property
    def evaluation_logger(self) -> logging.Logger:
        """
        Get the logger for evaluation.
        return: The logger for evaluation.
        """
        return self.context.get(ContextNames.EVALUATION_LOGGER)

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

    @property
    def current_round(self) -> BaseRound:
        """
        Get the current round of the session.
        return: The current round of the session.
        """
        if self.total_rounds == 0:
            return None
        else:
            return self._rounds[self.total_rounds - 1]

    @property
    def results(self) -> Dict[str, str]:
        """
        Get the evaluation results of the session.
        return: The evaluation results of the session.
        """
        return self._results

    @results.setter
    def results(self, value: Dict[str, str]) -> None:
        """
        Set the evaluation results of the session.
        :param value: The evaluation results of the session.
        """
        self._results = value

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
        summaries, cost = summarizer.get_summary_list(experience)

        experience_path = configs["EXPERIENCE_SAVED_PATH"]
        utils.create_folder(experience_path)
        summarizer.create_or_update_yaml(
            summaries, os.path.join(experience_path, "experience.yaml")
        )
        summarizer.create_or_update_vector_db(
            summaries, os.path.join(experience_path, "experience_db")
        )

        self.cost += cost
        utils.print_with_color("The experience has been saved.", "magenta")

    def print_cost(self) -> None:
        """
        Print the total cost of the session.
        """

        if isinstance(self.cost, float) and self.cost > 0:
            formatted_cost = "${:.2f}".format(self.cost)
            utils.print_with_color(
                f"Total request cost of the session: {formatted_cost}$", "yellow"
            )
        else:
            utils.print_with_color(
                "Cost is not available for the model {host_model} or {app_model}.".format(
                    host_model=configs["HOST_AGENT"]["API_MODEL"],
                    app_model=configs["APP_AGENT"]["API_MODEL"],
                ),
                "yellow",
            )

    def is_error(self):
        """
        Check if the session is in error state.
        return: True if the session is in error state, otherwise False.
        """
        if self.current_round is not None:
            return self.current_round.state.name() == AgentStatus.ERROR.value
        return False

    def is_finished(self) -> bool:
        """
        Check if the session is ended.
        return: True if the session is ended, otherwise False.
        """
        if (
            self._finish
            or self.step >= configs["MAX_STEP"]
            or self.total_rounds >= configs["MAX_ROUND"]
        ):
            return True

        if self.is_error():
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

        is_visual = configs.get("EVALUATION_AGENT", {}).get("VISUAL_MODE", True)

        evaluator = EvaluationAgent(
            name="eva_agent",
            app_root_name=self.context.get(ContextNames.APPLICATION_ROOT_NAME),
            is_visual=is_visual,
            main_prompt=configs["EVALUATION_PROMPT"],
            example_prompt="",
            api_prompt=configs["API_PROMPT"],
        )

        requests = self.request_to_evaluate()

        # Evaluate the session, first use the default setting, if failed, then disable the screenshot evaluation.
        try:
            result, cost = evaluator.evaluate(
                request=requests,
                log_path=self.log_path,
                eva_all_screenshots=configs.get("EVA_ALL_SCREENSHOTS", True),
            )
        except Exception as e:
            result, cost = evaluator.evaluate(
                request=requests,
                log_path=self.log_path,
                eva_all_screenshots=False,
            )

        # Add additional information to the evaluation result.
        additional_info = {"level": "session", "request": requests, "id": 0}
        result.update(additional_info)

        self.results = result

        self.cost += cost

        evaluator.print_response(result)

        self.evaluation_logger.info(json.dumps(result))

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

        if self.application_window is not None:

            try:
                PhotographerFacade().capture_app_window_screenshot(
                    self.application_window, save_path=screenshot_save_path
                )

            except Exception as e:
                utils.print_with_color(
                    f"Warning: The last snapshot capture failed, due to the error: {e}",
                    "yellow",
                )

            if configs.get("SAVE_UI_TREE", False):
                step_ui_tree = ui_tree.UITree(self.application_window)

                ui_tree_path = os.path.join(self.log_path, "ui_trees")

                ui_tree_file_name = "ui_tree_final.json"

                step_ui_tree.save_ui_tree_to_json(
                    os.path.join(
                        ui_tree_path,
                        ui_tree_file_name,
                    )
                )

            if configs.get("SAVE_FULL_SCREEN", False):

                desktop_save_path = self.log_path + f"desktop_final.png"

                # Capture the desktop screenshot for all screens.
                PhotographerFacade().capture_desktop_screen_screenshot(
                    all_screens=True, save_path=desktop_save_path
                )

            # Save the final XML file
            if configs["LOG_XML"]:
                log_abs_path = os.path.abspath(self.log_path)
                xml_save_path = os.path.join(log_abs_path, f"xml/action_step_final.xml")

                app_agent = self._host_agent.get_active_appagent()
                if app_agent is not None:
                    app_agent.Puppeteer.save_to_xml(xml_save_path)

    @staticmethod
    def initialize_logger(
        log_path: str, log_filename: str, mode="a", configs=configs
    ) -> logging.Logger:
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
        file_handler = logging.FileHandler(log_file_path, mode=mode, encoding="utf-8")
        formatter = logging.Formatter("%(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(configs["LOG_LEVEL"])

        return logger
