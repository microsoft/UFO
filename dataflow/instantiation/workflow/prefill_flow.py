import json
import logging
import os
import time
from typing import Any, Dict, List, Tuple

from dataflow.config.config import Config
from dataflow.instantiation.agent.prefill_agent import PrefillAgent
from dataflow.env.env_manager import WindowsAppEnv
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.automator.ui_control.inspector import ControlInspectorFacade
from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.module.basic import BaseSession
from ufo.config.config import Config as UFOConfig

_configs = Config.get_instance().config_data
_ufo_configs = UFOConfig.get_instance().config_data
_BACKEND = "uia"


class PrefillFlow(AppAgentProcessor):
    """
    Class to manage the prefill process by refining planning steps and automating UI interactions
    """

    _app_prefill_agent_dict: Dict[str, PrefillAgent] = {}

    def __init__(
        self,
        app_name: str,
        task_file_name: str,
        environment: WindowsAppEnv,
    ) -> None:
        """
        Initialize the prefill flow with the application context.
        :param app_name: The name of the application.
        :param task_file_name: The name of the task file for logging and tracking.
        :param environment: The environment of the app.
        """

        self.execution_time = None
        self._app_name = app_name
        self._task_file_name = task_file_name
        self._app_env = environment
        # Create or reuse a PrefillAgent for the app
        if self._app_name not in PrefillFlow._app_prefill_agent_dict:
            PrefillFlow._app_prefill_agent_dict[self._app_name] = PrefillAgent(
                "prefill",
                self._app_name,
                is_visual=True,
                main_prompt=_configs["PREFILL_PROMPT"],
                example_prompt=_configs["PREFILL_EXAMPLE_PROMPT"],
                api_prompt=_configs["API_PROMPT"],
            )
        self._prefill_agent = PrefillFlow._app_prefill_agent_dict[self._app_name]

        # Initialize execution step and UI control tools
        self._execute_step = 0
        self._control_inspector = ControlInspectorFacade(_BACKEND)
        self._photographer = PhotographerFacade()

        # Set default states
        self._status = ""

        # Initialize loggers for messages and responses
        self._log_path_configs = _configs["PREFILL_LOG_PATH"].format(
            task=self._task_file_name
        )
        os.makedirs(self._log_path_configs, exist_ok=True)

        # Set up loggers
        self._message_logger = BaseSession.initialize_logger(
            self._log_path_configs, "prefill_messages.json", "w", _configs
        )
        self._response_logger = BaseSession.initialize_logger(
            self._log_path_configs, "prefill_responses.json", "w", _configs
        )

    def execute(
        self, template_copied_path: str, original_task: str, refined_steps: List[str]
    ) -> Dict[str, Any]:
        """
        Start the execution by retrieving the instantiated result.
        :param template_copied_path: The path of the copied template to use.
        :param original_task: The original task to refine.
        :param refined_steps: The steps to guide the refinement process.
        :return: The refined task and corresponding action plans.
        """

        start_time = time.time()
        try:
            instantiated_request, instantiated_plan = self._instantiate_task(
                template_copied_path, original_task, refined_steps
            )
        except Exception as e:
            raise e
        finally:
            self.execution_time = round(time.time() - start_time, 3)

        return {
            "instantiated_request": instantiated_request,
            "instantiated_plan": instantiated_plan,
        }

    def _instantiate_task(
        self, template_copied_path: str, original_task: str, refined_steps: List[str]
    ) -> Tuple[str, List[str]]:
        """
        Retrieve and process the instantiated result for the task.
        Interacts with the PrefillAgent to refine the task and generate action plans.
        :param template_copied_path: The path of the copied template to use.
        :param original_task: The original task to refine.
        :param refined_steps: The steps to guide the refinement process.
        :return: The refined task and corresponding action plans.
        """

        try:
            # Retrieve prefill actions and task plan
            instantiated_request, instantiated_plan = self._get_prefill_actions(
                original_task,
                refined_steps,
                template_copied_path,
            )

            print(f"Original Task: {original_task}")
            print(f"Prefilled Task: {instantiated_request}")

        except Exception as e:
            logging.exception(f"Error in prefilling task: {e}")
            raise e

        return instantiated_request, instantiated_plan

    def _update_state(self, file_path: str) -> None:
        """
        Update the current state of the app by inspecting UI elements.
        :param file_path: Path of the app file to inspect.
        """

        print(f"Updating the app state using the file: {file_path}")

        # Retrieve control elements in the app window
        control_list = self._control_inspector.find_control_elements_in_descendants(
            self._app_env.app_window,
            control_type_list=_ufo_configs["CONTROL_LIST"],
            class_name_list=_ufo_configs["CONTROL_LIST"],
        )

        # Capture UI control annotations
        self._annotation_dict = self._photographer.get_annotation_dict(
            self._app_env.app_window, control_list, annotation_type="number"
        )

        # Filter out irrelevant control elements
        self._filtered_annotation_dict = self.get_filtered_annotation_dict(
            self._annotation_dict, configs=_configs
        )

        # Gather control info for both full and filtered lists
        self._control_info = self._control_inspector.get_control_info_list_of_dict(
            self._annotation_dict,
            ["control_text", "control_type" if _BACKEND == "uia" else "control_class"],
        )
        self._filtered_control_info = (
            self._control_inspector.get_control_info_list_of_dict(
                self._filtered_annotation_dict,
                [
                    "control_text",
                    "control_type" if _BACKEND == "uia" else "control_class",
                ],
            )
        )

    def _get_prefill_actions(
        self, given_task: str, reference_steps: List[str], file_path: str
    ) -> Tuple[str, List[str]]:
        """
        Generate refined tasks and action plans using the PrefillAgent.
        :param given_task: The task to refine.
        :param reference_steps: Reference steps for the task.
        :param file_path: Path to the task template.
        :return: The refined task and corresponding action plans.
        """

        self._update_state(file_path)
        execution_time = 0
        # Save a screenshot of the app state
        screenshot_path = os.path.join(self._log_path_configs, "screenshot.png")
        self._save_screenshot(self._task_file_name, screenshot_path)

        # Construct prompt message for the PrefillAgent
        prompt_message = self._prefill_agent.message_constructor(
            "",
            given_task,
            reference_steps,
            self._log_path_configs,
        )

        # Log the constructed message
        self._log_message(prompt_message)

        try:
            # Record start time and get PrefillAgent response
            start_time = time.time()
            response_string, _ = self._prefill_agent.get_response(
                prompt_message, "prefill", use_backup_engine=True, configs=_configs
            )
            execution_time = round(time.time() - start_time, 3)

            # Parse and log the response
            response_json = self._prefill_agent.response_to_dict(response_string)
            instantiated_request = response_json["New_task"]
            instantiated_plan = response_json["Actions_plan"]

        except Exception as e:
            self._status = "ERROR"
            logging.exception(f"Error in prefilling task: {e}")
            raise e
        finally:
            # Log the response and execution time
            self._log_response(response_json, execution_time)

        return instantiated_request, instantiated_plan

    def _log_message(self, prompt_message: str) -> None:
        """
        Log the constructed prompt message for the PrefillAgent.
        :param prompt_message: The message constructed for PrefillAgent.
        """

        messages_log_entry = {
            "step": self._execute_step,
            "messages": prompt_message,
            "error": "",
        }
        self._message_logger.info(json.dumps(messages_log_entry, indent=4))

    def _log_response(
        self, response_json: Dict[str, Any], execution_time: float
    ) -> None:
        """
        Log the response received from PrefillAgent along with execution time.
        :param response_json: Response data from PrefillAgent.
        :param execution_time: Time taken for the PrefillAgent call.
        """

        response_log_entry = {
            "step": self._execute_step,
            "execution_time": execution_time,
            "agent_response": response_json,
            "error": "",
        }
        self._response_logger.info(json.dumps(response_log_entry, indent=4))

    def _save_screenshot(self, doc_name: str, save_path: str) -> None:
        """
        Captures a screenshot of the current window or the full screen if the window is not found.
        :param doc_name: The name or description of the document to match the window.
        :param save_path: The path where the screenshot will be saved.
        """

        try:
            # Find the window matching the document name
            matched_window = self._app_env.find_matching_window(doc_name)
            if matched_window:
                screenshot = self._photographer.capture_app_window_screenshot(
                    matched_window
                )
            else:
                logging.warning("Window not found, taking a full-screen screenshot.")
                screenshot = self._photographer.capture_desktop_screen_screenshot()

            screenshot.save(save_path)
            print(f"Screenshot saved to {save_path}")
        except Exception as e:
            logging.exception(f"Failed to save screenshot: {e}")
            raise e
