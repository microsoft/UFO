import os
import time
from typing import Any, Dict, List, Tuple

from dataflow.config.config import Config as InstantiationConfig
from dataflow.env.env_manager import WindowsAppEnv
from dataflow.execution.agent.execute_agent import ExecuteAgent
from dataflow.execution.agent.execute_eval_agent import ExecuteEvalAgent
from ufo import utils
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.automator.app_apis.basic import WinCOMReceiverBasic
from ufo.config.config import Config as UFOConfig
from ufo.module.basic import BaseSession, Context, ContextNames
from ufo.automator.ui_control.screenshot import PhotographerDecorator

_configs = InstantiationConfig.get_instance().config_data
_ufo_configs = UFOConfig.get_instance().config_data


class ExecuteFlow(AppAgentProcessor):
    """
    ExecuteFlow class for executing the task and saving the result.
    """

    _app_execute_agent_dict: Dict[str, ExecuteAgent] = {}
    _app_eval_agent_dict: Dict[str, ExecuteEvalAgent] = {}

    def __init__(
        self, task_file_name: str, context: Context, environment: WindowsAppEnv
    ) -> None:
        """
        Initialize the execute flow for a task.
        :param task_file_name: Name of the task file being processed.
        :param context: Context object for the current session.
        :param environment: Environment object for the application being processed.
        """

        super().__init__(agent=ExecuteAgent, context=context)

        self.execution_time = None
        self.eval_time = None
        self._app_env = environment
        self._task_file_name = task_file_name
        self._app_name = self._app_env.app_name

        log_path = _configs["EXECUTE_LOG_PATH"].format(task=task_file_name)
        self._initialize_logs(log_path)

        self.application_window = self._app_env.find_matching_window(task_file_name)
        self.app_agent = self._get_or_create_execute_agent()
        self.eval_agent = self._get_or_create_evaluation_agent()

        self._matched_control = None  # Matched control for the current step.

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
        :param log_path: Path to save the logs.
        """

        os.makedirs(log_path, exist_ok=True)
        self._execute_message_logger = BaseSession.initialize_logger(
            log_path, "execute_log.json", "w", _configs
        )
        self.context.set(ContextNames.LOG_PATH, log_path)
        self.context.set(ContextNames.LOGGER, self._execute_message_logger)

    def execute(
        self, request: str, instantiated_plan: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Execute the execute flow: Execute the task and save the result.
        :param request: Original request to be executed.
        :param instantiated_plan: Instantiated plan containing steps to execute.
        :return: Tuple containing task quality flag, comment, and task type.
        """

        start_time = time.time()
        try:
            executed_plan = self.execute_plan(instantiated_plan)
        except Exception as error:
            raise RuntimeError(f"Execution failed. {error}")
        finally:
            self.execution_time = round(time.time() - start_time, 3)

        start_time = time.time()
        try:
            result, _ = self.eval_agent.evaluate(
                request=request, log_path=self.log_path
            )
            utils.print_with_color(f"Result: {result}", "green")
        except Exception as error:
            raise RuntimeError(f"Evaluation failed. {error}")
        finally:
            self.eval_time = round(time.time() - start_time, 3)

        return executed_plan, result

    def execute_plan(
        self, instantiated_plan: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get the executed result from the execute agent.
        :param instantiated_plan: Plan containing steps to execute.
        :return: List of executed steps.
        """

        # Initialize the step counter and capture the initial screenshot.
        self.session_step = 0
        try:
            time.sleep(1)
            # Initialize the API receiver
            self.app_agent.Puppeteer.receiver_manager.create_api_receiver(
                self.app_agent._app_root_name, self.app_agent._process_name
            )
            # Initialize the control receiver
            current_receiver = self.app_agent.Puppeteer.receiver_manager.receiver_list[
                -1
            ]

            if current_receiver is not None:
                self.application_window = self._app_env.find_matching_window(
                    self._task_file_name
                )
                current_receiver.com_object = (
                    current_receiver.get_object_from_process_name()
                )

            self.init_and_final_capture_screenshot()
        except Exception as error:
            raise RuntimeError(f"Execution initialization failed. {error}")

        # Initialize the success flag for each step.
        for index, step_plan in enumerate(instantiated_plan):
            instantiated_plan[index]["Success"] = None
            instantiated_plan[index]["MatchedControlText"] = None

        for index, step_plan in enumerate(instantiated_plan):
            try:
                self.session_step += 1

                # Check if the maximum steps have been exceeded.
                if self.session_step > _configs["MAX_STEPS"]:
                    raise RuntimeError("Maximum steps exceeded.")

                self._parse_step_plan(step_plan)

                try:
                    self.process()
                    instantiated_plan[index]["Success"] = True
                    instantiated_plan[index]["ControlLabel"] = self._control_label
                    instantiated_plan[index][
                        "MatchedControlText"
                    ] = self._matched_control
                except Exception as ControllerNotFoundError:
                    instantiated_plan[index]["Success"] = False
                    raise ControllerNotFoundError

            except Exception as error:
                err_info = RuntimeError(
                    f"Step {self.session_step} execution failed. {error}"
                )
                raise err_info
        # capture the final screenshot
        self.session_step += 1
        time.sleep(1)
        self.init_and_final_capture_screenshot()
        # save the final state of the app

        win_com_receiver = None
        for receiver in reversed(
            self.app_agent.Puppeteer.receiver_manager.receiver_list
        ):
            if isinstance(receiver, WinCOMReceiverBasic):
                if receiver.client is not None:
                    win_com_receiver = receiver
                    break

        if win_com_receiver is not None:
            win_com_receiver.save()
            time.sleep(1)
            win_com_receiver.client.Quit()

        print("Execution complete.")

        return instantiated_plan

    def process(self) -> None:
        """
        Process the current step.
        """

        step_start_time = time.time()
        self.print_step_info()
        self.capture_screenshot()
        self.execute_action()
        self.time_cost = round(time.time() - step_start_time, 3)
        self.log_save()

    def print_step_info(self) -> None:
        """
        Print the step information.
        """

        utils.print_with_color(
            "Step {step}: {subtask}".format(
                step=self.session_step,
                subtask=self.subtask,
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
            "Results": self._results,
            "Application": self.app_agent._app_root_name,
            "TimeCost": self.time_cost,
        }
        self._memory_data.add_values_from_dict(step_memory)
        self.log(self._memory_data.to_dict())

    def _parse_step_plan(self, step_plan: Dict[str, Any]) -> None:
        """
        Parse the response.
        :param step_plan: The step plan.
        """

        self._matched_control = None
        self.subtask = step_plan.get("Subtask", "")
        self.control_text = step_plan.get("ControlText", "")
        self._operation = step_plan.get("Function", "")
        self.question_list = step_plan.get("Questions", [])
        self._args = utils.revise_line_breaks(step_plan.get("Args", ""))

        # Compose the function call and the arguments string.
        self.action = self.app_agent.Puppeteer.get_command_string(
            self._operation, self._args
        )

        self.status = step_plan.get("Status", "")

    def init_and_final_capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """

        # Define the paths for the screenshots saved.
        screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"

        self._memory_data.add_values_from_dict(
            {
                "CleanScreenshot": screenshot_save_path,
            }
        )

        self.photographer.capture_app_window_screenshot(
            self.application_window, save_path=screenshot_save_path
        )
        # Capture the control screenshot.
        control_selected = self._app_env.app_window
        self.capture_control_screenshot(control_selected)

    def execute_action(self) -> None:
        """
        Execute the action.
        """

        control_selected = None
        # Find the matching window and control.
        self.application_window = self._app_env.find_matching_window(
            self._task_file_name
        )
        if self.control_text == "":
            control_selected = self.application_window
        else:
            self._control_label, control_selected = (
                self._app_env.find_matching_controller(
                    self.filtered_annotation_dict, self.control_text
                )
            )
            if control_selected:
                self._matched_control = control_selected.window_text()

        if not control_selected:
            # If the control is not found, raise an error.
            raise RuntimeError(f"Control with text '{self.control_text}' not found.")

        try:
            # Get the selected control item from the annotation dictionary and LLM response.
            # The LLM response is a number index corresponding to the key in the annotation dictionary.
            if control_selected:

                if _ufo_configs.get("SHOW_VISUAL_OUTLINE_ON_SCREEN", True):
                    control_selected.draw_outline(colour="red", thickness=3)
                    time.sleep(_ufo_configs.get("RECTANGLE_TIME", 0))

                control_coordinates = PhotographerDecorator.coordinate_adjusted(
                    self.application_window.rectangle(), control_selected.rectangle()
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
            self.general_error_handler()

    def general_error_handler(self) -> None:
        """
        Handle general errors.
        """

        pass
