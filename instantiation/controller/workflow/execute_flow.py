import os
import time
from typing import Dict, Tuple, Any, List
    
from instantiation.config.config import Config as InstantiationConfig
from instantiation.controller.env.env_manager import WindowsAppEnv
from instantiation.controller.agent.agent import ExecuteAgent, ExecuteEvalAgent
from ufo import utils
from ufo.config.config import Config as UFOConfig
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.module.basic import BaseSession, Context, ContextNames

_configs = InstantiationConfig.get_instance().config_data
_ufo_configs = UFOConfig.get_instance().config_data
if _configs is not None:
    BACKEND = _configs["CONTROL_BACKEND"]

class ExecuteFlow(AppAgentProcessor):
    """
    ExecuteFlow class for executing the task and saving the result.
    """

    _app_execute_agent_dict: Dict[str, ExecuteAgent] = {}
    _app_eval_agent_dict: Dict[str, ExecuteEvalAgent] = {}

    def __init__(self, environment: WindowsAppEnv, task_file_name: str, context: Context) -> None:
        """
        Initialize the execute flow for a task.
        :param environment: Environment object for the application being processed.
        :param task_file_name: Name of the task file being processed.
        :param context: Context object for the current session.
        """
        super().__init__(agent=ExecuteAgent, context=context)

        self.execution_time = 0
        self._app_env = environment
        self._task_file_name = task_file_name
        self._app_name = self._app_env.app_name

        log_path = _configs["EXECUTE_LOG_PATH"].format(task=task_file_name)
        self._initialize_logs(log_path)

        self.application_window = self._app_env.find_matching_window(task_file_name)
        self.app_agent = self._get_or_create_execute_agent()
        self.eval_agent = self._get_or_create_evaluation_agent()

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
            )
        return ExecuteFlow._app_execute_agent_dict[self._app_name]
    
    def _get_or_create_evaluation_agent(self) -> ExecuteEvalAgent:
        """
        Retrieve or create an evaluation agent for the given application.
        :return: ExecuteEvalAgent instance for the specified application.
        """
        if self._app_name not in ExecuteFlow._app_eval_agent_dict:
            ExecuteFlow._app_eval_agent_dict[self._app_name] = ExecuteEvalAgent(
                "evaluation",
                self._app_env.app_root_name,
                is_visual=True,
                main_prompt=_ufo_configs["EVALUATION_PROMPT"],
                example_prompt="",
                api_prompt=_ufo_configs["API_PROMPT"],
            )
        return ExecuteFlow._app_eval_agent_dict[self._app_name]
    
    def _initialize_logs(self, log_path: str) -> None:
        """
        Initialize logging for execute messages and responses.
        """
        os.makedirs(log_path, exist_ok=True)
        self._execute_message_logger = BaseSession.initialize_logger(
            log_path, "execute_log.json", "w", _configs
        )
        self.context.set(ContextNames.LOG_PATH, log_path)
        self.context.set(ContextNames.LOGGER, self._execute_message_logger)

    def execute(self, request: str, instantiated_plan: List[str]) -> Tuple[Dict[str, str], float]:
        """
        Execute the execute flow: Execute the task and save the result.
        :param request: Original request to be executed.
        :param instantiated_plan: Instantiated plan containing steps to execute.
        :return: Tuple containing task quality flag, comment, and task type.
        """
        start_time = time.time()
        execute_result, execute_cost = self._get_executed_result(
            request, instantiated_plan
        )
        self.execution_time = round(time.time() - start_time, 3)
        return execute_result, execute_cost 

    def _get_executed_result(self, request, instantiated_plan) -> Tuple[Dict[str, str], float]:
        """
        Get the executed result from the execute agent.
        :param request: Original request to be executed.
        :param instantiated_plan: Plan containing steps to execute.
        :return: Tuple containing task quality flag, request comment, and request type.
        """
        utils.print_with_color("Starting execution of instantiated plan...", "yellow")
        # Initialize the step counter and capture the initial screenshot.
        self.session_step = 0
        self.capture_screenshot()
        # Initialize the API receiver
        self.app_agent.Puppeteer.receiver_manager.create_api_receiver(
            self.app_agent._app_root_name, self.app_agent._process_name
        )
        for _, step_plan in enumerate(instantiated_plan):
            try:
                self.session_step += 1

                # Check if the maximum steps have been exceeded.
                if self.session_step > _configs["MAX_STEPS"]:
                    raise RuntimeError(
                        "Maximum steps exceeded."
                    )
                
                self._parse_step_plan(step_plan)

                try:
                    self.process()
                except Exception as ControllerNotFound:
                    raise ControllerNotFound
                
            except Exception as error:
                err_info = RuntimeError(f"Step {self.session_step} execution failed. {error}")
                utils.print_with_color(f"{err_info}", "red")
                raise err_info

        print("Execution complete.")

        utils.print_with_color("Evaluating the session...", "yellow")
        result, cost = self.eval_agent.evaluate(request=request, \
                                                log_path=self.log_path)

        print(result)

        return result, cost

    def process(self) -> None:
        """
        Process the current step.
        """
        step_start_time = time.time()
        self.print_step_info()
        self.capture_screenshot()
        self.select_controller()
        self.execute_action()
        self.time_cost = round(time.time() - step_start_time, 3)
        self.log_save()


    def print_step_info(self) -> None:
        """
        Print the step information.
        """
        utils.print_with_color(
            "Step {step}: {step_plan}".format(
                step=self.session_step,
                step_plan=self.plan,
            ),
            "magenta",
        )

    def log_save(self) -> None:
        """
        Log the constructed prompt message for the PrefillAgent.
        """
        step_memory = {
            "Step": self.session_step, 
            "Subtask": self.subtask,  
            "ControlLabel": self._control_label,
            "ControlText": self.control_text,
            "Action": self.action,  
            "ActionType": self.app_agent.Puppeteer.get_command_types(self._operation), 
            "Plan": self.plan,
            "Results": self._results, 
            "Application": self.app_agent._app_root_name,
            "TimeCost": self.time_cost,  
        }
        self._memory_data.set_values_from_dict(step_memory)
        self.log(self._memory_data.to_dict())

    def _parse_step_plan(self, step_plan: Dict[str, Any]) -> None:
        """
        Parse the response.
        """
        self.control_text = step_plan.get("ControlText", "")
        self._operation = step_plan.get("Function", "")
        self.question_list = step_plan.get("Questions", [])
        self._args = utils.revise_line_breaks(step_plan.get("Args", ""))
        
        # Convert the plan from a string to a list if the plan is a string.
        step_plan_key = "Step "+str(self.session_step)
        self.plan = step_plan.get(step_plan_key, "")

        # Compose the function call and the arguments string.
        self.action = self.app_agent.Puppeteer.get_command_string(
            self._operation, self._args
        )

        self.status = step_plan.get("Status", "")

    def select_controller(self) -> None:
        """
        Select the controller.        
        """
        if self.control_text == "":
            return 
        for key, control in self.filtered_annotation_dict.items():
            if self._app_env.is_matched_controller(control, self.control_text):
                self._control_label = key
                return
        raise RuntimeError(
            f"Control with text '{self.control_text}' not found."
        )
    
    def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """

        # Define the paths for the screenshots saved.
        screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"
        annotated_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_annotated.png"
        )
        concat_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_concat.png"
        )

        self._memory_data.set_values_from_dict(
            {
                "CleanScreenshot": screenshot_save_path,
                "AnnotatedScreenshot": annotated_screenshot_save_path,
                "ConcatScreenshot": concat_screenshot_save_path,
            }
        )

        # Get the control elements in the application window if the control items are not provided for reannotation.
        if type(self.control_reannotate) == list and len(self.control_reannotate) > 0:
            control_list = self.control_reannotate
        else:
            control_list = self.control_inspector.find_control_elements_in_descendants(
                self.application_window,
                control_type_list=_ufo_configs["CONTROL_LIST"],
                class_name_list=_ufo_configs["CONTROL_LIST"],
            )

        # Get the annotation dictionary for the control items, in a format of {control_label: control_element}.
        self._annotation_dict = self.photographer.get_annotation_dict(
            self.application_window, control_list, annotation_type="number"
        )

        # Attempt to filter out irrelevant control items based on the previous plan.
        self.filtered_annotation_dict = self.get_filtered_annotation_dict(
            self._annotation_dict
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
        if _ufo_configs["INCLUDE_LAST_SCREENSHOT"] and self.session_step > 1:
            last_screenshot_save_path = (
                self.log_path + f"action_step{self.session_step - 1}.png"
            )
            last_control_screenshot_save_path = (
                self.log_path
                + f"action_step{self.session_step - 1}_selected_controls.png"
            )
            self._image_url += [
                self.photographer.encode_image_from_path(
                    last_control_screenshot_save_path
                    if os.path.exists(last_control_screenshot_save_path)
                    else last_screenshot_save_path
                )
            ]

        # Whether to concatenate the screenshots of clean screenshot and annotated screenshot into one image.
        if _ufo_configs["CONCAT_SCREENSHOT"]:
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

        # Save the XML file for the current state.
        if _ufo_configs["LOG_XML"]:

            self._save_to_xml()
    
    def general_error_handler(self) -> None:
        """
        Handle general errors.
        """
        pass
