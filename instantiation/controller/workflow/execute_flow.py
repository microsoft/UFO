import json
import logging
import os
from textwrap import indent
import time
from typing import Dict, Tuple, Any
    
from docx import Document
from zmq import Context

from instantiation.config.config import Config
from instantiation.controller.env.env_manager import WindowsAppEnv
from instantiation.controller.agent.agent import ExecuteAgent
from ufo import utils
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.automator import puppeteer
from ufo.module.basic import BaseSession, Context, ContextNames
from ufo.automator.ui_control.screenshot import PhotographerDecorator
from ufo.agents.memory.memory import Memory

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

        log_path = _configs["EXECUTE_LOG_PATH"].format(task=task_file_name)
        os.makedirs(log_path, exist_ok=True)
        self._initialize_logs()

        self.context.set(ContextNames.LOG_PATH, log_path)
        self.application_window = self._app_env.find_matching_window(task_file_name)
        self.app_agent = self._get_or_create_execute_agent()

        self.save_pass_folder, self.save_error_folder = self._init_save_folders()

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

    def execute(self, instantiated_plan) -> Tuple[bool, str, str]:
        """
        Execute the execute flow: Execute the task and save the result.
        :param instantiated_request: Request object to be executeed.
        :return: Tuple containing task quality flag, comment, and task type.
        """
        start_time = time.time()
        is_quality_good = self._get_executeed_result(
            instantiated_plan
        )
        self.execution_time = round(time.time() - start_time, 3)
        return is_quality_good

    def _initialize_logs(self) -> None:
        """
        Initialize logging for execute messages and responses.
        """
        os.makedirs(self.log_path, exist_ok=True)
        self._execute_message_logger = BaseSession.initialize_logger(
            self.log_path, "execute_log.json", "w", _configs
        )


    def _get_executeed_result(self, instantiated_plan) -> Tuple[bool, str, str]:
        """
        Get the executed result from the execute agent.
        :param instantiated_plan: Plan containing steps to execute.
        :return: Tuple containing task quality flag, request comment, and request type.
        """
        print("Starting execution of instantiated plan...")

        self.step_index = 0
        is_quality_good = True  # Initialize as True

        try:
            # Initialize the API receiver
            self.app_agent.Puppeteer.receiver_manager.create_api_receiver(
                self.app_agent._app_root_name, self.app_agent._process_name
            )
            
            # Get the filtered annotation dictionary for the control items.
            self.filtered_annotation_dict = self.get_filtered_control_dict()
            
            for _, step_plan in enumerate(instantiated_plan):
                try:
                    self.capture_screenshot()
                    self.step_index += 1
                    print(f"Executing step {self.step_index}: {step_plan}")

                    # Parse the step plan
                    self._parse_step_plan(step_plan)
                    
                    # Get the filtered annotation dictionary for the control items
                    control_selected = self.get_selected_controller()
                    self.capture_control_screenshot(control_selected)
                    self.execute_action(control_selected)
                    self._log_step_message()
                    self._execute_message_logger.info(json.dumps(self.app_agent.memory.to_json(), indent=4))

                except Exception as step_error:
                    # Handle errors specific to the step execution
                    logging.exception(f"Error while executing step {self.step_index}: {step_error}")
                    self._execute_message_logger.error(f"Step {self.step_index} failed: {step_error}")
                    
                    # Mark quality as false due to failure
                    is_quality_good = False
                    continue  # Continue with the next step

            print("Execution complete.")

            self._app_env.close()
            # Return the evaluation result
            if is_quality_good:
                return "Execution completed successfully."
            else:
                return "Execution completed with errors."

        except Exception as e:
            # Log and handle unexpected errors during the entire process
            logging.exception(f"Unexpected error during execution: {e}")
            self._execute_message_logger.error(f"Execution failed: {e}")
            return False, f"Execution failed: {str(e)}", "Error"

    def _parse_step_plan(self, step_plan) -> None:
        """
        Parse the response.
        """
        self.control_text = step_plan.get("controlText", "")
        self._operation = step_plan.get("function", "")
        self.question_list = step_plan.get("questions", [])
        self._args = utils.revise_line_breaks(step_plan.get("args", ""))
        
        # Convert the plan from a string to a list if the plan is a string.
        step_plan_key = "step "+str(self.step_index)
        self.plan = self.string2list(step_plan.get(step_plan_key, ""))

        # Compose the function call and the arguments string.
        self.action = self.app_agent.Puppeteer.get_command_string(
            self._operation, self._args
        )

        self.status = step_plan.get("status", "")

    def execute_action(self, control_selected) -> None:
        """
        Execute the action.
        """
        try:

            if self._operation:

                if _configs.get("SHOW_VISUAL_OUTLINE_ON_SCREEN", True):
                    control_selected.draw_outline(colour="red", thickness=3)
                    time.sleep(_configs.get("RECTANGLE_TIME", 0))

                if control_selected:
                    control_coordinates = PhotographerDecorator.coordinate_adjusted(
                        self.application_window.rectangle(),
                        control_selected.rectangle(),
                    )
                    self._control_log = {
                        "control_class": control_selected.element_info.class_name,
                        "control_type": control_selected.element_info.control_type,
                        "control_automation_id": control_selected.element_info.automation_id,
                        "control_friendly_class_name": control_selected.friendly_class_name(),
                        "control_coordinates": {
                            "left": control_coordinates[0],
                            "top": control_coordinates[1],
                            "right": control_coordinates[2],
                            "bottom": control_coordinates[3],
                        },
                    }
                else:
                    self._control_log = {}

                self.app_agent.Puppeteer.receiver_manager.create_ui_control_receiver(
                    control_selected, self.application_window
                )

                # Save the screenshot of the tagged selected control.
                self.capture_control_screenshot(control_selected)

                self._results = self.app_agent.Puppeteer.execute_command(
                    self._operation, self._args
                )
                self.control_reannotate = None
                if not utils.is_json_serializable(self._results):
                    self._results = ""

                    return

        except Exception:
            logging.exception("Failed to execute the action.")
            raise


    def get_filtered_control_dict(self):
        # Get the control elements in the application window if the control items are not provided for reannotation.
        if type(self.control_reannotate) == list and len(self.control_reannotate) > 0:
            control_list = self.control_reannotate
        else:
            control_list = self.control_inspector.find_control_elements_in_descendants(
                self.application_window,
                control_type_list=_configs["CONTROL_LIST"],
                class_name_list=_configs["CONTROL_LIST"],
            )

        # Get the annotation dictionary for the control items, in a format of {control_label: control_element}.
        self._annotation_dict = self.photographer.get_annotation_dict(
            self.application_window, control_list, annotation_type="number"
        )

        # Attempt to filter out irrelevant control items based on the previous plan.
        filtered_annotation_dict = self.get_filtered_annotation_dict(
            self._annotation_dict
        )
        return filtered_annotation_dict

    def get_selected_controller(self) -> Any:
        """
        Find keys in a dictionary where the associated value has a control_text attribute.
        
        :param annotation_dict: Dictionary with keys as strings and values as UIAWrapper objects.
        :return: A dictionary containing the keys and their corresponding control_text.
        """
        if self.control_text == "":
            return self.application_window
        for key, control in self.filtered_annotation_dict.items():
            if self._app_env.is_matched_controller(control, self.control_text):
                self._control_label = key
                return control
        return None
    

    def _log_step_message(self) -> None:
        """
        Log the constructed prompt message for the PrefillAgent.

        :param step_execution_result: The execution result of the current step.
        """
        step_memory = {
            "Step": self.step_index, 
            "Subtask": self.subtask,  
            "Action": self.action,  
            "ActionType": self.app_agent.Puppeteer.get_command_types(self._operation),  # 操作类型
            "Application": self.app_agent._app_root_name,
            "Results": self._results, 
            "TimeCost": self._time_cost,  
        }
        self._memory_data.set_values_from_dict(step_memory)

        self.app_agent.add_memory(self._memory_data)


    def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """

        # Define the paths for the screenshots saved.
        screenshot_save_path = self.log_path + f"action_step{self.step_index}.png"
        annotated_screenshot_save_path = (
            self.log_path + f"action_step{self.step_index}_annotated.png"
        )
        concat_screenshot_save_path = (
            self.log_path + f"action_step{self.step_index}_concat.png"
        )
        self._memory_data.set_values_from_dict(
            {
                "CleanScreenshot": screenshot_save_path,
                "AnnotatedScreenshot": annotated_screenshot_save_path,
                "ConcatScreenshot": concat_screenshot_save_path,
            }
        )

        self.photographer.capture_app_window_screenshot(
            self.application_window, save_path=screenshot_save_path
        )

        # Capture the screenshot of the selected control items with annotation and save it.
        self.photographer.capture_app_window_screenshot_with_annotation_dict(
            self.application_window,
            self.filtered_annotation_dict,
            annotation_type="number",
            save_path=annotated_screenshot_save_path,
        )

        # If the configuration is set to include the last screenshot with selected controls tagged, save the last screenshot.
        if _configs["INCLUDE_LAST_SCREENSHOT"] and self.step_index > 0:
            last_screenshot_save_path = (
                self.log_path + f"action_step{self.step_index - 1}.png"
            )
            last_control_screenshot_save_path = (
                self.log_path
                + f"action_step{self.step_index - 1}_selected_controls.png"
            )
            self._image_url += [
                self.photographer.encode_image_from_path(
                    last_control_screenshot_save_path
                    if os.path.exists(last_control_screenshot_save_path)
                    else last_screenshot_save_path
                )
            ]

        # Whether to concatenate the screenshots of clean screenshot and annotated screenshot into one image.
        if _configs["CONCAT_SCREENSHOT"]:
            self.photographer.concat_screenshots(
                screenshot_save_path,
                annotated_screenshot_save_path,
                concat_screenshot_save_path,
            )
            self._image_url += [
                self.photographer.encode_image_from_path(concat_screenshot_save_path)
            ]
        else:
            screenshot_url = self.photographer.encode_image_from_path(
                screenshot_save_path
            )
            screenshot_annotated_url = self.photographer.encode_image_from_path(
                annotated_screenshot_save_path
            )
            self._image_url += [screenshot_url, screenshot_annotated_url]

    
    def _init_save_folders(self):
        """
        Initialize the folders for saving the execution results.
        """
        instance_folder = os.path.join(_configs["TASKS_HUB"], "execute_result")
        pass_folder = os.path.join(instance_folder, "execute_pass")
        fail_folder = os.path.join(instance_folder, "execute_fail")
        os.makedirs(pass_folder, exist_ok=True)
        os.makedirs(fail_folder, exist_ok=True)
        return pass_folder, fail_folder