import json
import os
from typing import Any, Dict, List, Tuple

from instantiation.config.config import Config
from instantiation.controller.agent.agent import PrefillAgent
from instantiation.controller.env.env_manager import WindowsAppEnv
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.automator.ui_control.inspector import ControlInspectorFacade
from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.module.basic import BaseSession

configs = Config.get_instance().config_data
if configs is not None:
    BACKEND = configs["CONTROL_BACKEND"]


class PrefillFlow(AppAgentProcessor):
    """
    The class to refine the plan steps and prefill the file.
    """

    app_prefill_agent_dict: Dict = dict()

    def __init__(self, task_object, environment: WindowsAppEnv = None) -> None:
        """
        Initialize the follow flow.
        :param task_object: The object containing task details (should have app_object and task_file_name).
        :param environment: The environment of the app (optional).
        """

        self.task_object = task_object
        self.app_name = task_object.app_object.description.lower()
        self.task_file_name = task_object.task_file_name

        if environment is None:
            from instantiation.controller.env.env_manager import WindowsAppEnv

            self.app_env = WindowsAppEnv(task_object.app_object)
        else:
            self.app_env = environment

        # Create the action prefill agent
        if self.app_name not in PrefillFlow.app_prefill_agent_dict:
            self.app_prefill_agent_dict[self.app_name] = PrefillAgent(
                "prefill",
                self.app_name,
                is_visual=True,
                main_prompt=configs["PREFILL_PROMPT"],
                example_prompt=configs["PREFILL_EXAMPLE_PROMPT"],
                api_prompt=configs["API_PROMPT"],
            )
        self.prefill_agent = PrefillFlow.app_prefill_agent_dict[self.app_name]

        self.file_path = ""

        self.execute_step = 0
        self.control_inspector = ControlInspectorFacade(BACKEND)
        self.photographer = PhotographerFacade()

        self.control_state = None
        self.custom_doc = None
        self.status = ""
        self.file_path = ""
        self.control_annotation = None

        # Initialize loggers for messages and responses
        self.log_path_configs = configs["PREFILL_LOG_PATH"].format(
            task=self.task_file_name
        )
        os.makedirs(self.log_path_configs, exist_ok=True)

        self.message_logger = BaseSession.initialize_logger(
            self.log_path_configs, "prefill_messages.json", "w", configs
        )
        self.response_logger = BaseSession.initialize_logger(
            self.log_path_configs, "prefill_responses.json", "w", configs
        )

    def execute(self) -> None:
        """
        Execute the prefill flow by retrieving the instantiated result.
        """

        self.get_instantiated_result()

    def get_instantiated_result(self) -> None:
        """
        Get the instantiated result for the task.

        This method interacts with the PrefillAgent to get the refined task and action plans.
        """
        template_cached_path = self.task_object.instantial_template_path
        self.app_env.start(template_cached_path)
        try:
            instantiated_request, instantiated_plan = self.get_prefill_actions(
                self.task_object.task,
                self.task_object.refined_steps,
                template_cached_path,
            )

            print(f"Original Task: {self.task_object.task}")
            print(f"Prefilled Task: {instantiated_request}")
            self.task_object.set_attributes(
                instantiated_request=instantiated_request,
                instantiated_plan=instantiated_plan,
            )

        except Exception as e:
            print(f"Error! get_instantiated_result: {e}")
        finally:
            self.app_env.close()

    def update_state(self, file_path: str) -> None:
        """
        Get current states of app with pywinauto、win32com

        :param file_path: The file path of the app.
        """
        print(f"updating the state of app file: {file_path}")

        control_list = self.control_inspector.find_control_elements_in_descendants(
            self.app_env.app_window,
            control_type_list=configs["CONTROL_LIST"],
            class_name_list=configs["CONTROL_LIST"],
        )
        self._annotation_dict = self.photographer.get_annotation_dict(
            self.app_env.app_window, control_list, annotation_type="number"
        )

        # Filter out irrelevant control items based on the previous plan.
        self.filtered_annotation_dict = self.get_filtered_annotation_dict(
            self._annotation_dict, configs=configs
        )

        self._control_info = self.control_inspector.get_control_info_list_of_dict(
            self._annotation_dict,
            ["control_text", "control_type" if BACKEND == "uia" else "control_class"],
        )
        self.filtered_control_info = (
            self.control_inspector.get_control_info_list_of_dict(
                self.filtered_annotation_dict,
                [
                    "control_text",
                    "control_type" if BACKEND == "uia" else "control_class",
                ],
            )
        )


    def log_prefill_agent_info(
        self,
        messages: List[Dict[str, Any]],
        agent_response: Dict[str, Any],
        error: str = "",
    ) -> None:
        """
        Record the prefill information.

        :param messages: The messages of the conversation.
        :param agent_response: The response of the agent.
        :param error: The error message.
        """

        # Log message
        messages_log_entry = {
            "step": self.execute_step,
            "messages": messages,
            "error": error,
        }
        self.message_logger.info(json.dumps(messages_log_entry))

        # Log response
        response_log_entry = {
            "step": self.execute_step,
            "agent_response": agent_response,
            "error": error,
        }
        self.response_logger.info(json.dumps(response_log_entry))

    def get_prefill_actions(
        self, given_task: str, reference_steps: List[str], file_path: str
    ) -> Tuple[str, List[str]]:
        """
        Call the PlanRefine Agent to select files

        :param given_task: The given task.
        :param reference_steps: The reference steps.
        :param file_path: The file path.
        :return: The prefilled task and the action plans.
        """

        error_msg = ""
        self.update_state(file_path)

        # Save the screenshot
        screenshot_path = self.log_path_configs + "screenshot.png"
        self.app_env.save_screenshot(screenshot_path)

        # filter the controls
        filter_control_state = self.filtered_control_info
        # filter the apis
        prompt_message = self.prefill_agent.message_constructor(
            "", given_task, reference_steps, filter_control_state, self.log_path_configs
        )
        try:
            response_string, cost = self.prefill_agent.get_response(
                prompt_message,
                "prefill",
                use_backup_engine=True,
                configs=configs,
            )
            response_json = self.prefill_agent.response_to_dict(response_string)
            new_task = response_json["new_task"]
            action_plans = response_json["actions_plan"]

        except Exception as e:
            self.status = "ERROR"
            error_msg = str(e)
            self.log_prefill_agent_info(
                prompt_message, {"PrefillAgent": response_json}, error_msg
            )

            return None, None
        else:
            self.log_prefill_agent_info(
                prompt_message, {"PrefillAgent": response_json}, error_msg
            )

        return new_task, action_plans
