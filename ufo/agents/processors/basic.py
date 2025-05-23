# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import os
import time
import traceback
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Dict, List

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agents.agent.basic import BasicAgent
from ufo.agents.memory.memory import MemoryItem
from ufo.agents.processors.actions import ActionSequence
from ufo.automator.ui_control.inspector import ControlInspectorFacade
from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.config.config import Config
from ufo.module.context import Context, ContextNames

configs = Config.get_instance().config_data

if configs is not None:
    CONTROL_BACKEND = configs.get("CONTROL_BACKEND", ["uia"])
    BACKEND = "win32" if "win32" in CONTROL_BACKEND else "uia"


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
        self._memory_data = MemoryItem()
        self._question_list = []
        self._agent_status_manager = self.agent.status_manager
        self._is_resumed = False
        self._plan = None

        self._total_time_cost = 0
        self._time_cost = {}
        self._exeception_traceback = {}
        self._actions = ActionSequence()

    def process(self) -> None:
        """
        Process a single step in a round.
        The process includes the following steps:
        1. Print the step information.
        2. Capture the screenshot.
        3. Get the control information.
        4. Get the prompt message.
        5. Get the response.
        6. Update the cost.
        7. Parse the response.
        8. Execute the action.
        9. Update the memory.
        10. Update the step and status.
        11. Save the log.
        """

        start_time = time.time()

        try:
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

            # Step 6: Update the context.
            self.update_cost()

            # Step 7: Parse the response, if there is no error.
            self.parse_response()

            if self.is_pending() or self.is_paused():
                # If the session is pending, update the step and memory, and return.
                if self.is_pending():
                    self.update_status()
                    self.update_memory()

                return

            # Step 8: Execute the action.
            self.execute_action()

            # Step 9: Update the memory.
            self.update_memory()

            # Step 10: Update the status.
            self.update_status()

            self._total_time_cost = time.time() - start_time

            # Step 11: Save the log.
            self.log_save()

        except StopIteration:
            # Error was handled and logged in the exception capture decorator.
            # Simply return here to stop the process early.

            return

    def resume(self) -> None:
        """
        Resume the process of action execution after the session is paused.
        """

        self._is_resumed = True

        try:
            # Step 1: Execute the action.
            self.execute_action()

            # Step 2: Update the memory.
            self.update_memory()

            # Step 3: Update the status.
            self.update_status()

        except StopIteration:
            # Error was handled and logged in the exception capture decorator.
            # Simply return here to stop the process early.
            pass

        finally:
            self._is_resumed = False

    @classmethod
    def method_timer(cls, func):
        """
        Decorator to calculate the time cost of the method.
        :param func: The method to be decorated.
        :return: The decorated method.
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            result = func(self, *args, **kwargs)
            end_time = time.time()
            self._time_cost[func.__name__] = end_time - start_time
            return result

        return wrapper

    @classmethod
    def exception_capture(cls, func):
        """
        Decorator to capture the exception of the method.
        :param func: The method to be decorated.
        :return: The decorated method.
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except Exception as e:
                self._exeception_traceback[func.__name__] = {
                    "type": str(type(e).__name__),
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                }

                utils.print_with_color(f"Error Occurs at {func.__name__}", "red")
                utils.print_with_color(
                    self._exeception_traceback[func.__name__]["traceback"], "red"
                )
                if self._response is not None:
                    utils.print_with_color("Response: ", "red")
                    utils.print_with_color(self._response, "red")
                self._status = self._agent_status_manager.ERROR.value
                self.sync_memory()
                self.add_to_memory({"error": self._exeception_traceback})
                self.add_to_memory({"Status": self._status})
                self.log_save()

                raise StopIteration("Error occurred during step.")

        return wrapper

    @abstractmethod
    def sync_memory(self) -> None:
        """
        Sync the memory of the Agent.
        """
        pass

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

    def update_status(self) -> None:
        """
        Update the status of the session.
        """
        self.agent.step += 1
        self.agent.status = self.status

        if self.status != self._agent_status_manager.FINISH.value:
            time.sleep(configs["SLEEP_TIME"])

        self.round_step += 1
        self.session_step += 1

    def add_to_memory(self, data_dict: Dict[str, Any]) -> None:
        """
        Add the data to the memory.
        :param data_dict: The data dictionary to be added to the memory.
        """
        self._memory_data.add_values_from_dict(data_dict)

    def log_save(self) -> None:
        """
        Save the log.
        """

        self._memory_data.add_values_from_dict(
            {"total_time_cost": self._total_time_cost}
        )
        self.log(self._memory_data.to_dict())

    @property
    def context(self) -> Context:
        """
        Get the context.
        :return: The context.
        """
        return self._context

    def update_cost(self) -> None:
        """
        Update the cost.
        """

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
    def prev_plan(self) -> List[str]:
        """
        Get the previous plan.
        :return: The previous plan of the agent.
        """
        agent_memory = self.agent.memory

        if agent_memory.length > 0:
            prev_plan = agent_memory.get_latest_item().to_dict().get("Plan", [])
        else:
            prev_plan = []

        return prev_plan

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
    def round_subtask_amount(self) -> int:
        """
        Get the round subtask amount.
        :return: The round subtask amount.
        """
        return self.context.get(ContextNames.CURRENT_ROUND_SUBTASK_AMOUNT)

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
    def control_label(self) -> str:
        """
        Get the control label.
        :return: The control label.
        """
        return self._control_label

    @control_label.setter
    def control_label(self, label: str) -> None:
        """
        Set the control label.
        :param label: The control label.
        """
        self._control_label = label

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
    def actions(self) -> ActionSequence:
        """
        Get the actions.
        :return: The actions.
        """
        return self._actions

    @actions.setter
    def actions(self, actions: ActionSequence) -> None:
        """
        Set the actions.
        :param actions: The actions to be executed.
        """
        self._actions = actions

    @property
    def plan(self) -> str:
        """
        Get the plan of the agent.
        :return: The plan.
        """
        return self._plan

    @plan.setter
    def plan(self, plan: str) -> None:
        """
        Set the plan of the agent.
        :param plan: The plan.
        """
        self._plan = plan

    @property
    def log_path(self) -> str:
        """
        Get the log path.
        :return: The log path.
        """
        return self.context.get(ContextNames.LOG_PATH)

    @property
    def ui_tree_path(self) -> str:
        """
        Get the UI tree path.
        :return: The UI tree path.
        """
        return os.path.join(self.log_path, "ui_trees")

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

    @property
    def subtask(self) -> str:
        """
        Get the subtask.
        :return: The subtask.
        """
        return self.context.get(ContextNames.SUBTASK)

    @subtask.setter
    def subtask(self, subtask: str) -> None:
        """
        Set the subtask.
        :param subtask: The subtask.
        """
        self.context.set(ContextNames.SUBTASK, subtask)

    @property
    def host_message(self) -> List[str]:
        """
        Get the host message.
        :return: The host message.
        """
        return self.context.get(ContextNames.HOST_MESSAGE)

    @host_message.setter
    def host_message(self, message: List[str]) -> None:
        """
        Set the host message.
        :param message: The host message.
        """
        self.context.set(ContextNames.HOST_MESSAGE, message)

    @property
    def previous_subtasks(self) -> List[str]:
        """
        Get the previous subtasks.
        :return: The previous subtasks.
        """
        return self.context.get(ContextNames.PREVIOUS_SUBTASKS)

    @previous_subtasks.setter
    def previous_subtasks(self, subtasks: List[str]) -> None:
        """
        Set the previous subtasks.
        :param subtasks: The previous subtasks.
        """
        self.context.set(ContextNames.PREVIOUS_SUBTASKS, subtasks)

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

    @property
    def question_list(self) -> List[str]:
        """
        Get the question list.
        :return: The question list.
        """

        if type(self._question_list) == str:
            self._question_list = [self._question_list]

        return self._question_list

    @question_list.setter
    def question_list(self, question_list: List[str]) -> None:
        """
        Set the question list.
        :param question_list: The question list.
        """
        self._question_list = question_list

    def is_error(self) -> bool:
        """
        Check if the process is in error.
        :return: The boolean value indicating if the process is in error.
        """

        self.agent.status = self.status
        return self.status == self._agent_status_manager.ERROR.value

    def is_paused(self) -> bool:
        """
        Check if the process is paused.
        :return: The boolean value indicating if the process is paused.
        """

        self.agent.status = self.status

        return (
            self.status == self._agent_status_manager.PENDING.value
            or self.status == self._agent_status_manager.CONFIRM.value
        )

    def is_pending(self) -> bool:
        """
        Check if the process is pending.
        :return: The boolean value indicating if the process is pending.
        """

        self.agent.status = self.status

        return self.status == self._agent_status_manager.PENDING.value

    def is_confirm(self) -> bool:
        """
        Check if the process is confirm.
        :return: The boolean value indicating if the process is confirm.
        """

        self.agent.status = self.status

        return self.status == self._agent_status_manager.CONFIRM.value

    def is_application_closed(self) -> bool:
        """
        Check if the application is closed.
        :return: The boolean value indicating if the application is closed.
        """

        if self.application_window is None:

            return True

        try:
            self.application_window.is_enabled()
            return False
        except:
            return True

    def log(self, response_json: Dict[str, Any]) -> None:
        """
        Set the result of the session, and log the result.
        result: The result of the session.
        response_json: The response json.
        return: The response json.
        """

        self.logger.info(json.dumps(response_json))

    @property
    def name(self) -> str:
        """
        Get the name of the processor.
        :return: The name of the processor.
        """
        return self.__class__.__name__

    @staticmethod
    def string2list(string: Any) -> List[str]:
        """
        Convert a string to a list of string if the input is a string.
        :param string: The string.
        :return: The list.
        """
        if isinstance(string, str):
            return [string]
        else:
            return string
