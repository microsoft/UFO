import json
import logging
import os
import time
from typing import Dict, Tuple

from zmq import Context

from instantiation.config.config import Config
from instantiation.controller.env.env_manager import WindowsAppEnv
from instantiation.controller.agent.agent import ExecuteAgent
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.automator import puppeteer
from ufo.module.basic import BaseSession, Context, ContextNames

_configs = Config.get_instance().config_data

class ExecuteFlow(AppAgentProcessor):
    """
    Class to refine the plan steps and prefill the file based on executeing criteria.
    """

    _app_execute_agent_dict: Dict[str, ExecuteAgent] = {}

    def __init__(self, environment: WindowsAppEnv, task_file_name: str, context: Context) -> None:
        """
        Initialize the execute flow for a task.
        :param app_object: Application object containing task details.
        :param task_file_name: Name of the task file being processed.
        """
        super().__init__(agent=ExecuteAgent, context=context)

        self.execution_time = 0
        self._app_env = environment
        self._task_file_name = task_file_name
        self._app_name = self._app_env.app_name


        # FIXME: os.makedirs() function should be invloved in the Context class
        log_path = _configs["EXECUTE_LOG_PATH"].format(task=task_file_name)
        os.makedirs(log_path, exist_ok=True)
        self.context.set(ContextNames.LOG_PATH, log_path)
        self.application_window = self._app_env.find_matching_window(task_file_name)
        # self.log_path = _configs["EXECUTE_LOG_PATH"].format(task=task_file_name)
        self.app_agent = self._get_or_create_execute_agent()
        self._initialize_logs()

    def _get_or_create_execute_agent(self) -> ExecuteAgent:
        """
        Retrieve or create a execute agent for the given application.
        :return: ExecuteAgent instance for the specified application.
        """
        if self._app_name not in ExecuteFlow._app_execute_agent_dict:
            ExecuteFlow._app_execute_agent_dict[self._app_name] = ExecuteAgent(
                "execute",
                self._app_name,
                self._app_env.app_root_name,
                is_visual=True,
                main_prompt=_configs["EXECUTE_PROMPT"],
                example_prompt="",
                api_prompt=_configs["API_PROMPT"],
            )
        return ExecuteFlow._app_execute_agent_dict[self._app_name]

    def execute(self, instantiated_request, instantiated_plan) -> Tuple[bool, str, str]:
        """
        Execute the execute flow: Execute the task and save the result.
        :param instantiated_request: Request object to be executeed.
        :return: Tuple containing task quality flag, comment, and task type.
        """
        start_time = time.time()
        is_quality_good, execute_result = self._get_executeed_result(
            instantiated_request, instantiated_plan
        )
        self.execution_time = round(time.time() - start_time, 3)
        return is_quality_good, execute_result

    def _initialize_logs(self) -> None:
        """
        Initialize logging for execute messages and responses.
        """
        os.makedirs(self.log_path, exist_ok=True)
        self._execute_message_logger = BaseSession.initialize_logger(
            self.log_path, "execute_log.json", "w", _configs
        )

    from typing import Tuple

    def _get_executeed_result(self, instantiated_request, instantiated_plan) -> Tuple[bool, str, str]:
        """
        Get the executeed result from the execute agent.
        :param instantiated_request: Request object containing task details.
        :param instantiated_plan: Plan containing steps to execute.
        :return: Tuple containing task quality flag, request comment, and request type.
        """
        execute_result_dict = {}
        print("Starting execution of instantiated plan...")
        # print("Instantiated plan:", instantiated_plan)
        # self.capture_screenshot()

        for index, step_context in enumerate(instantiated_plan):
            # step = index + 1
            # control_label = step_context["controlLabel"]
            # control_text = step_context["controlText"]
            # function_name = step_context["function"]
            # function_args = step_context["args"]
            print(f"Executing step {index + 1}: {step_context}")

            self._response = step_context
            self.parse_response()
            self.capture_screenshot()
            self.execute_action()

        print("Execution complete.")
        # print("Execueted result:", execute_result_dict)
        is_quality_good = True

        self._app_env.close()

        # Return the evaluation result (assuming it returns a tuple as specified)
        return is_quality_good, execute_result_dict  # Ensure this matches the expected Tuple[bool, str, str]


