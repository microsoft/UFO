# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import traceback
from abc import ABC, abstractmethod
from typing import List, Union

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.automator.ui_control.inspector import ControlInspectorFacade
from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.config.config import Config
from ufo.module.context import Context, ContextNames
from ufo.agents.agent.basic import BasicAgent

configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]


class BaseProcessor(ABC):
    """
    The base processor for the session. A session consists of multiple rounds of conversation with the user, completing a task.
    At each round, the HostAgent and AppAgent interact with the user and the application with the processor.
    Each processor is responsible for processing the user request and updating the HostAgent and AppAgent at a single step in a round.
    """

    def __init__(self, agent: BasicAgent, context: Context) -> None:
        """
        Initialize the processor.
        :param context: The context of the session.
        :param agent: The agent who executes the processor.
        """

        self._context = context
        self._agent = agent

        self.photographer = PhotographerFacade()
        self.control_inspector = ControlInspectorFacade(BACKEND)

        self._prompt_message = None
        self._status = None
        self._response = None
        self._cost = 0
        self._control_label = None
        self._control_text = None
        self._response_json = {}
        self._results = None
        self._agent_status_manager = self.agent.status_manager

    def process(self) -> None:
        """
        Process a single step in a round.
        The process includes the following steps:
        1. Print the step information.
        2. Capture the screenshot.
        3. Get the control information.
        4. Get the prompt message.
        5. Get the response.
        6. Update the context.
        7. Parse the response.
        8. Execute the action.
        9. Update the memory.
        10. Update the step and status.
        """

        # Step 1: Print the step information.
        self.print_step_info()

        # Step 2: Capture the screenshot.
        self.capture_screenshot()

        # Step 3: Get the control information.
        self.get_control_info()

        # Step 4: Get the prompt message.
        self.get_prompt_message()

        # Step 5: Get the response.
        self.get_response()

        if self.is_error():
            return

        # Step 6: Update the context.
        self.update_context()

        # Step 7: Parse the response, if there is no error.
        self.parse_response()

        if self.is_error():
            return

        # Step 8: Execute the action.
        self.execute_action()

        # Step 9: Update the memory.
        self.update_memory()

        # Step 10: Update the status.
        self.update_status()

    def resume(self) -> None:
        """
        Resume the process of action execution.
        """

        self.execute_action()
        self.update_memory()

        if self.should_create_subagent():
            self.create_sub_agent()

        self.update_status()

    @abstractmethod
    def print_step_info(self) -> None:
        """
        Print the step information.
        """
        pass

    @abstractmethod
    def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """
        pass

    @abstractmethod
    def get_control_info(self) -> None:
        """
        Get the control information.
        """
        pass

    @abstractmethod
    def get_prompt_message(self) -> None:
        """
        Get the prompt message.
        """
        pass

    @abstractmethod
    def get_response(self) -> None:
        """
        Get the response from the LLM.
        """
        pass

    @abstractmethod
    def parse_response(self) -> None:
        """
        Parse the response.
        """
        pass

    @abstractmethod
    def execute_action(self) -> None:
        """
        Execute the action.
        """
        pass

    @abstractmethod
    def update_memory(self) -> None:
        """
        Update the memory of the Agent.
        """
        pass

    @abstractmethod
    def update_status(self) -> None:
        """
        Update the status of the session.
        """
        pass

    @property
    def context(self) -> Context:
        """
        Get the context.
        :return: The context.
        """
        return self._context

    def update_context(self) -> None:
        """
        Update the context.
        """

        self.round_step += 1
        self.session_step += 1

        self.round_cost += self.cost
        self.session_cost += self.cost

    @property
    def agent(self) -> BasicAgent:
        """
        Get the agent.
        :return: The agent.
        """
        return self._agent

    @property
    def application_window(self) -> UIAWrapper:
        """
        Get the active window.
        :return: The active window.
        """
        return self.context.get(ContextNames.APPLICATION_WINDOW)

    @application_window.setter
    def application_window(self, window: UIAWrapper) -> None:
        """
        Set the active window.
        :param window: The active window.
        """
        self.context.set(ContextNames.APPLICATION_WINDOW, window)

    @property
    def round_step(self) -> int:
        """
        Get the round step.
        :return: The round step.
        """
        return self.context.get(ContextNames.CURRENT_ROUND_STEP)

    @round_step.setter
    def round_step(self, step: int) -> None:
        """
        Set the round step.
        :param step: The round step.
        """
        self.context.set(ContextNames.CURRENT_ROUND_STEP, step)

    @property
    def round_cost(self) -> float:
        """
        Get the round cost.
        :return: The round cost.
        """
        return self.context.get(ContextNames.CURRENT_ROUND_COST)

    @round_cost.setter
    def round_cost(self, cost: float) -> None:
        """
        Set the round cost.
        :param cost: The round cost.
        """
        self.context.set(ContextNames.CURRENT_ROUND_COST, cost)

    @property
    def session_step(self) -> int:
        """
        Get the session step.
        :return: The session step.
        """
        return self.context.get(ContextNames.SESSION_STEP)

    @session_step.setter
    def session_step(self, step: int) -> None:
        """
        Set the session step.
        :param step: The session step.
        """
        self.context.set(ContextNames.SESSION_STEP, step)

    @property
    def session_cost(self) -> float:
        """
        Get the session cost.
        :return: The session cost.
        """
        return self.context.get(ContextNames.SESSION_COST)

    @session_cost.setter
    def session_cost(self, cost: float) -> None:
        """
        Set the session cost.
        :param cost: The session cost.
        """
        self.context.set(ContextNames.SESSION_COST, cost)

    @property
    def application_process_name(self) -> str:
        """
        Get the application process name.
        :return: The application process name.
        """
        return self.context.get(ContextNames.APPLICATION_PROCESS_NAME)

    @application_process_name.setter
    def application_process_name(self, name: str) -> None:
        """
        Set the application process name.
        :param name: The application process name.
        """
        self.context.set(ContextNames.APPLICATION_PROCESS_NAME, name)

    @property
    def app_root(self) -> str:
        """
        Get the application root.
        :return: The application root.
        """
        return self.context.get(ContextNames.APPLICATION_ROOT_NAME)

    @app_root.setter
    def app_root(self, root: str) -> None:
        """
        Set the application root.
        :param root: The application root.
        """
        self.context.set(ContextNames.APPLICATION_ROOT_NAME, root)

    @property
    def control_reannotate(self) -> List[str]:
        """
        Get the control reannotation.
        :return: The control reannotation.
        """
        return self.context.get(ContextNames.CONTROL_REANNOTATION)

    @control_reannotate.setter
    def control_reannotate(self, reannotate: List[str]) -> None:
        """
        Set the control reannotation.
        :param reannotate: The control reannotation.
        """
        self.context.set(ContextNames.CONTROL_REANNOTATION, reannotate)

    @property
    def round_num(self) -> int:
        """
        Get the round number.
        :return: The round number.
        """
        return self.context.get(ContextNames.CURRENT_ROUND_ID)

    @property
    def control_text(self) -> str:
        """
        Get the active application.
        :return: The active application.
        """
        return self._control_text

    @control_text.setter
    def control_text(self, text: str) -> None:
        """
        Set the control text.
        :param text: The control text.
        """
        self._control_text = text

    @property
    def status(self) -> str:
        """
        Get the status of the processor.
        :return: The status of the processor.
        """
        return self._status

    @property
    def log_path(self) -> str:
        """
        Get the log path.
        :return: The log path.
        """
        return self.context.get(ContextNames.LOG_PATH)

    @property
    def request(self) -> str:
        """
        Get the request.
        :return: The request.
        """
        return self.context.get(ContextNames.REQUEST)

    @property
    def request_logger(self) -> str:
        """
        Get the request logger.
        :return: The request logger.
        """
        return self.context.get(ContextNames.REQUEST_LOGGER)

    @property
    def logger(self) -> str:
        """
        Get the logger.
        :return: The logger.
        """
        return self.context.get(ContextNames.LOGGER)

    @status.setter
    def status(self, status: str) -> None:
        """
        Set the status of the processor.
        :param status: The status of the processor.
        """
        self._status = status

    @property
    def cost(self) -> float:
        """
        Get the cost of the processor.
        :return: The cost of the processor.
        """

        if self._cost is None:
            return 0
        return self._cost

    @cost.setter
    def cost(self, cost: float) -> None:
        """
        Set the cost of the processor.
        :param cost: The cost of the processor.
        """
        self._cost = cost

    def is_error(self) -> bool:
        """
        Check if the process is in error.
        :return: The boolean value indicating if the process is in error.
        """

        return self._status == self._agent_status_manager.ERROR.value

    def log(self, response_json: dict) -> None:
        """
        Set the result of the session, and log the result.
        result: The result of the session.
        response_json: The response json.
        return: The response json.
        """

        self.logger.info(json.dumps(response_json))

    def error_log(self, response_str: str, error: str) -> None:
        """
        Error handler for the session.
        """
        log = json.dumps(
            {
                "step": self.session_step,
                "status": self._agent_status_manager.ERROR.value,
                "response": response_str,
                "error": error,
            }
        )
        self.logger.info(log)

    @property
    def name(self) -> str:
        """
        Get the name of the processor.
        :return: The name of the processor.
        """
        return self.__class__.__name__

    def general_error_handler(self) -> None:
        """
        Error handler for the general error.
        """
        error_trace = traceback.format_exc()
        utils.print_with_color(f"Error Occurs at {self.name}", "red")
        utils.print_with_color(str(error_trace), "red")
        utils.print_with_color(self._response, "red")
        self.error_log(self._response, str(error_trace))
        self._status = self._agent_status_manager.ERROR.value

    def llm_error_handler(self) -> None:
        """
        Error handler for the LLM error.
        """
        error_trace = traceback.format_exc()
        log = json.dumps(
            {
                "step": self.session_step,
                "prompt": self._prompt_message,
                "status": str(error_trace),
            }
        )
        utils.print_with_color(
            "Error occurs when calling LLM: {e}".format(e=str(error_trace)), "red"
        )
        self.request_logger.info(log)
        self._status = self._agent_status_manager.ERROR.value
        return

    @staticmethod
    def string2list(string: str) -> List[str]:
        """
        Convert a string to a list of string if the input is a string.
        :param string: The string.
        :return: The list.
        """
        if isinstance(string, str):
            return [string]
        else:
            return string
