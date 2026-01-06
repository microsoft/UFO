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
import platform
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, TYPE_CHECKING, Any

# Conditional import for Windows-specific packages
if TYPE_CHECKING or platform.system() == "Windows":
    from pywinauto.controls.uiawrapper import UIAWrapper
else:
    UIAWrapper = Any

from rich.console import Console

from ufo import utils
from ufo.agents.agent.basic import BasicAgent
from ufo.agents.agent.evaluation_agent import EvaluationAgent
from ufo.agents.agent.host_agent import HostAgent
from ufo.agents.states.basic import AgentState, AgentStatus
from config.config_loader import get_ufo_config
from aip.messages import Command
from ufo.experience.summarizer import ExperienceSummarizer
from ufo.module.context import Context, ContextNames
from ufo.trajectory.parser import Trajectory

ufo_config = get_ufo_config()
console = Console()


class FileWriter:
    """
    Simple file writer that bypasses global logging settings.
    Provides a unified write interface for logging to files.
    """

    def __init__(self, file_path: str, mode: str = "a"):
        """
        Initialize file writer.
        :param file_path: Path to the log file
        :param mode: File open mode (default: 'a' for append)
        """
        self.file_path = file_path
        self.mode = mode

        # Ensure directory exists (only if there's a directory part)
        dir_path = os.path.dirname(file_path)
        if dir_path:  # Only create directory if there's a directory part
            os.makedirs(dir_path, exist_ok=True)

        # Create or open the file to ensure it exists
        with open(file_path, mode, encoding="utf-8") as f:
            pass

    def write(self, message: str) -> None:
        """
        Write message to file.
        :param message: Message to write
        """
        try:
            with open(self.file_path, self.mode, encoding="utf-8") as f:
                f.write(message)
                if not message.endswith("\n"):
                    f.write("\n")
                f.flush()  # Ensure immediate write
        except Exception as e:
            # Fallback: at least try to print the error
            print(f"Failed to write to file {self.file_path}: {e}")


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
        self.logger = logging.getLogger(__name__)

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

    async def run(self) -> None:
        """
        Run the round.
        """

        while not self.is_finished():

            await self.agent.handle(self.context)

            # Take action

            self.state = self.agent.state.next_state(self.agent)
            self.agent = self.agent.state.next_agent(self.agent)

            self.logger.info(
                f"Agent {self.agent.name} transitioned to state {self.state.name()}"
            )

            self.agent.set_state(self.state)

            # If the subtask ends, capture the last snapshot of the application.
            if self.state.is_subtask_end():
                time.sleep(ufo_config.system.sleep_time)
                await self.capture_last_snapshot(sub_round_id=self.subtask_amount)
                self.subtask_amount += 1

        self.agent.blackboard.add_requests(
            {"request_{i}".format(i=self.id): self.request}
        )

        await self.capture_last_snapshot()

        if self._should_evaluate:
            self.evaluation()

        return self.context.get(ContextNames.ROUND_RESULT)

    def is_finished(self) -> bool:
        """
        Check if the round is finished.
        return: True if the round is finished, otherwise False.
        """
        return (
            self.state.is_round_end()
            or self.context.get(ContextNames.SESSION_STEP) >= ufo_config.system.max_step
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
            console.print(
                f"💰 Request total cost for current round is {formatted_cost}",
                style="yellow",
            )

    @property
    def log_path(self) -> str:
        """
        Get the log path of the round.

        return: The log path of the round.
        """
        return self._context.get(ContextNames.LOG_PATH)

    async def capture_last_snapshot(self, sub_round_id: Optional[int] = None) -> None:
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

        if (
            self.application_window is not None
            or self.application_window_info is not None
        ):

            try:

                result = await self.context.command_dispatcher.execute_commands(
                    [
                        Command(
                            tool_name="capture_window_screenshot",
                            parameters={},
                            tool_type="data_collection",
                        )
                    ]
                )

                image = result[0].result
                utils.save_image_string(image, screenshot_save_path)
                self.logger.info(
                    f"Captured application window screenshot at final: {screenshot_save_path}"
                )

            except Exception as e:
                self.logger.warning(
                    f"The last snapshot capture failed, due to the error: {e}"
                )
            if ufo_config.system.save_ui_tree:
                # Get session data manager from context

                ui_tree_path = os.path.join(self.log_path, "ui_trees")
                ui_tree_file_name = (
                    f"ui_tree_round_{self.id}_final.json"
                    if sub_round_id is None
                    else f"ui_tree_round_{self.id}_sub_round_{sub_round_id}_final.json"
                )
                ui_tree_save_path = os.path.join(ui_tree_path, ui_tree_file_name)

                await self.save_ui_tree(ui_tree_save_path)

            if ufo_config.system.save_full_screen:

                desktop_save_path = (
                    self.log_path
                    + f"desktop_round_{self.id}_sub_round_{sub_round_id}_final.png"
                )

                result = await self.context.command_dispatcher.execute_commands(
                    [
                        Command(
                            tool_name="capture_desktop_screenshot",
                            parameters={"all_screens": True},
                            tool_type="data_collection",
                        )
                    ]
                )

                desktop_screenshot_url = result[0].result
                utils.save_image_string(desktop_screenshot_url, desktop_save_path)
                self.logger.info(f"Desktop screenshot saved to {desktop_save_path}")

    async def save_ui_tree(self, save_path: str):
        """
        Save the UI tree of the current application window.
        """
        if self.application_window is not None:
            result = await self.context.command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="get_ui_tree",
                        parameters={},
                        tool_type="data_collection",
                    )
                ]
            )
            step_ui_tree = result[0].result

            if step_ui_tree:

                save_dir = os.path.dirname(save_path)
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

                with open(save_path, "w") as file:
                    json.dump(step_ui_tree, file, indent=4)
                    self.logger.info(f"UI tree saved to {save_path}")

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

    @property
    def application_window_info(self) -> Dict[str, str]:
        """
        Get the application window info of the session.
        return: The application window info of the session.
        """
        return self._context.get(ContextNames.APPLICATION_WINDOW_INFO)

    @application_window_info.setter
    def application_window_info(self, app_window_info: Dict[str, str]) -> None:
        """
        Set the application window info.
        :param app_window_info: The application window info.
        """
        self._context.set(ContextNames.APPLICATION_WINDOW_INFO, app_window_info)


class BaseSession(ABC):
    """
    A basic session in UFO. A session consists of multiple rounds of interactions and conversations.
    """

    def __init__(self, task: str, should_evaluate: bool, id: str) -> None:
        """
        Initialize a session.
        :param task: The name of current task.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The id of the session.
        """

        self._should_evaluate = should_evaluate
        self._id = id
        self.task = task

        # Logging-related properties
        self.log_path = f"logs/{task}/"
        utils.create_folder(self.log_path)

        self._rounds: Dict[int, BaseRound] = {}

        self._context = Context()
        self._init_context()
        self._finish = False
        self._results = []
        self.logger = logging.getLogger(__name__)

        # Initialize platform-specific agents
        # Subclasses should override _init_agents() to set up their agents
        self._host_agent: Optional[HostAgent] = None
        self._init_agents()

    async def run(self) -> List[Dict[str, str]]:
        """
        Run the session.
        :return: The result per session
        """

        while not self.is_finished():

            round = self.create_new_round()
            if round is None:
                break

            round_result = await round.run()

            self.results.append({"request": round.request, "result": round_result})

        await self.capture_last_snapshot()

        if self._should_evaluate and not self.is_error():
            self.evaluation()

        if ufo_config.system.log_to_markdown:

            self.save_log_to_markdown()

        self.print_cost()

        return self.results

    @abstractmethod
    def _init_agents(self) -> None:
        """
        Initialize platform-specific agents.
        Platform-specific sessions should override this to set up their agents.
        For Windows sessions, this creates a HostAgent.
        For Linux sessions, this may create different agent types or no host agent.
        """
        pass

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

    def save_log_to_markdown(self) -> None:
        """
        Save the log of the session to markdown file.
        """

        file_path = self.log_path
        trajectory = Trajectory(file_path)
        trajectory.to_markdown(file_path + "/output.md")
        self.logger.info(f"Trajectory saved to {file_path + '/output.md'}")

    def _init_context(self) -> None:
        """
        Initialize the context of the session.
        """

        # Initialize the ID
        self.context.set(ContextNames.ID, self.id)

        # Initialize the log path and create file writers
        self.context.set(ContextNames.LOG_PATH, self.log_path)

        # Create file writers that bypass global logging.disable()
        response_writer = FileWriter(
            os.path.join(self.log_path, "response.log"), mode="a"
        )
        request_writer = FileWriter(
            os.path.join(self.log_path, "request.log"), mode="a"
        )
        eval_writer = FileWriter(
            os.path.join(self.log_path, "evaluation.log"), mode="a"
        )

        self.context.set(ContextNames.LOGGER, response_writer)
        self.context.set(ContextNames.REQUEST_LOGGER, request_writer)
        self.context.set(ContextNames.EVALUATION_LOGGER, eval_writer)

        # Initialize the session cost and step
        self.context.set(ContextNames.SESSION_COST, 0)
        self.context.set(ContextNames.SESSION_STEP, 0)

    @property
    def id(self) -> str:
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
    def application_window_info(self) -> Dict[str, str]:
        """
        Get the application window info of the session.
        return: The application window info of the session.
        """
        return self.context.get(ContextNames.APPLICATION_WINDOW_INFO)

    @application_window_info.setter
    def application_window_info(self, app_window_info: Dict[str, str]) -> None:
        """
        Set the application window info.
        :param app_window_info: The application window info.
        """
        self.context.set(ContextNames.APPLICATION_WINDOW_INFO, app_window_info)

    @property
    def step(self) -> int:
        """
        Get the step of the session.
        return: The step of the session.
        """
        return self.context.get(ContextNames.SESSION_STEP)

    @property
    def evaluation_logger(self) -> FileWriter:
        """
        Get the file writer for evaluation.
        return: The file writer for evaluation.
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
    def host_agent(self) -> Optional[HostAgent]:
        """
        Get the host agent of the session.
        May return None for sessions that don't use a host agent (e.g., Linux).
        :return: The host agent of the session, or None if not applicable.
        """
        return self._host_agent

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
    def results(self) -> List[Dict[str, str]]:
        """
        Get the evaluation results of the session.
        return: The evaluation results of the session.
        """
        return self._results

    @results.setter
    def results(self, value: List[Dict[str, str]]) -> None:
        """
        Set the evaluation results of the session.
        :param value: The evaluation results of the session.
        """
        self._results = value

    def experience_saver(self) -> None:
        """
        Save the current trajectory as agent experience.
        """
        console.print(
            "📚 Summarizing and saving the execution flow as experience...",
            style="yellow",
        )

        summarizer = ExperienceSummarizer(
            ufo_config.app_agent.visual_mode,
            ufo_config.system.EXPERIENCE_PROMPT,
            ufo_config.system.APPAGENT_EXAMPLE_PROMPT,
            ufo_config.system.API_PROMPT,
        )
        experience = summarizer.read_logs(self.log_path)
        summaries, cost = summarizer.get_summary_list(experience)

        experience_path = ufo_config.system.EXPERIENCE_SAVED_PATH
        utils.create_folder(experience_path)
        summarizer.create_or_update_yaml(
            summaries, os.path.join(experience_path, "experience.yaml")
        )
        summarizer.create_or_update_vector_db(
            summaries, os.path.join(experience_path, "experience_db")
        )

        self.cost += cost
        self.logger.info(f"The experience has been saved to {experience_path}")

    def print_cost(self) -> None:
        """
        Print the total cost of the session.
        """

        if isinstance(self.cost, float) and self.cost > 0:
            formatted_cost = "${:.2f}".format(self.cost)
            console.print(
                f"💰 Total request cost of the session: {formatted_cost}",
                style="yellow",
            )
        else:
            console.print(
                f"ℹ️  Cost is not available for the model {ufo_config.host_agent.api_model} or {ufo_config.app_agent.api_model}.",
                style="yellow",
            )
            self.logger.warning("Cost information is not available.")

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
            or self.step >= ufo_config.system.max_step
            or self.total_rounds >= ufo_config.system.max_round
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

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the session to initial state.
        """
        pass

    def evaluation(self) -> None:
        """
        Evaluate the session.
        """
        console.print("📊 Evaluating the session...", style="yellow")

        is_visual = ufo_config.evaluation_agent.visual_mode

        evaluator = EvaluationAgent(
            name="eva_agent",
            is_visual=is_visual,
            main_prompt=ufo_config.system.EVALUATION_PROMPT,
            example_prompt="",
        )

        requests = self.request_to_evaluate()

        # Evaluate the session, first use the default setting, if failed, then disable the screenshot evaluation.
        try:
            result, cost = evaluator.evaluate(
                request=requests,
                log_path=self.log_path,
                eva_all_screenshots=ufo_config.system.eva_all_screenshots,
                context=self.context,
            )
        except Exception as e:
            result, cost = evaluator.evaluate(
                request=requests,
                log_path=self.log_path,
                eva_all_screenshots=False,
                context=self.context,
            )

        # Add additional information to the evaluation result.
        additional_info = {
            "level": "session",
            "request": requests,
            "type": "evaluation_result",
        }
        result.update(additional_info)

        self._results.append(result)

        self.cost += cost

        evaluator.print_response(result)

        self.evaluation_logger.write(json.dumps(result))

        self.logger.info(
            f"Evaluation result saved to {os.path.join(self.log_path, 'evaluation.log')}"
        )

    @property
    def results(self) -> List[Dict[str, str]]:
        """
        Get the evaluation results of the session.
        return: The evaluation results of the session.
        """
        return self._results

    @results.setter
    def results(self, value: List[Dict[str, str]]):
        """
        Set the evaluation results of the session.
        :param value: The evaluation results to set.
        """
        self._results = value

    @property
    def session_type(self) -> str:
        """
        Get the class name of the session.
        return: The class name of the session.
        """
        return self.__class__.__name__

    @property
    def current_agent_class(self) -> str:
        """
        Get the class name of the current agent.
        return: The class name of the current agent.
        """
        return self.current_round.agent.__class__.__name__

    async def capture_last_snapshot(self) -> None:
        """
        Capture the last snapshot of the application, including the screenshot and the XML file if configured.
        """  # Capture the final screenshot
        screenshot_save_path = self.log_path + "action_step_final.png"

        if (
            self.application_window is not None
            or self.application_window_info is not None
        ):

            await self.capture_last_screenshot(screenshot_save_path)

            if ufo_config.system.save_ui_tree:
                ui_tree_path = os.path.join(self.log_path, "ui_trees")
                ui_tree_file_name = "ui_tree_final.json"
                ui_tree_save_path = os.path.join(ui_tree_path, ui_tree_file_name)
                await self.capture_last_ui_tree(ui_tree_save_path)

            if ufo_config.system.save_full_screen:

                desktop_save_path = self.log_path + "desktop_final.png"

                await self.capture_last_screenshot(desktop_save_path, full_screen=True)

    async def capture_last_screenshot(
        self, save_path: str, full_screen: bool = False
    ) -> None:
        """
        Capture the last window screenshot.
        :param save_path: The path to save the window screenshot.
        :param full_screen: Whether to capture the full screen or just the active window.
        """

        try:
            if full_screen:
                command = Command(
                    tool_name="capture_desktop_screenshot",
                    parameters={"all_screens": True},
                    tool_type="data_collection",
                )
            else:

                command = Command(
                    tool_name="capture_window_screenshot",
                    parameters={},
                    tool_type="data_collection",
                )

            result = await self.context.command_dispatcher.execute_commands([command])
            image = result[0].result

            self.logger.info(f"Captured screenshot at final: {save_path}")
            if image:
                utils.save_image_string(image, save_path)

        except Exception as e:
            self.logger.warning(
                f"The last snapshot capture failed, due to the error: {e}"
            )

    async def capture_last_ui_tree(self, save_path: str) -> None:
        """
        Capture the last UI tree snapshot.
        :param save_path: The path to save the UI tree snapshot.
        """

        result = await self.context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="get_ui_tree",
                    parameters={},
                    tool_type="data_collection",
                )
            ]
        )

        if result and result[0].result:
            with open(save_path, "w") as file:
                json.dump(result[0].result, file, indent=4)

    @staticmethod
    def initialize_logger(log_path: str, log_filename: str, mode="a") -> logging.Logger:
        """
        Initialize logging.
        log_path: The path of the log file.
        log_filename: The name of the log file.
        return: The logger.
        """
        # Code for initializing logging
        logger = logging.Logger(log_filename)

        if not ufo_config.system.print_log:
            # Remove existing handlers if PRINT_LOG is False
            logger.handlers = []

        log_file_path = os.path.join(log_path, log_filename)
        file_handler = logging.FileHandler(log_file_path, mode=mode, encoding="utf-8")
        formatter = logging.Formatter("%(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(ufo_config.system.log_level)

        return logger
