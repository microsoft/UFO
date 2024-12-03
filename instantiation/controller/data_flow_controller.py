import os
import time
import traceback
from enum import Enum
from typing import Any, Dict
from jsonschema import validate, ValidationError

from instantiation.controller.env.env_manager import WindowsAppEnv
from instantiation.controller.workflow.choose_template_flow import ChooseTemplateFlow
from instantiation.controller.workflow.execute_flow import ExecuteFlow
from instantiation.controller.workflow.filter_flow import FilterFlow
from instantiation.controller.workflow.prefill_flow import PrefillFlow
from instantiation.config.config import Config

from ufo.utils import print_with_color
from learner.utils import load_json_file, save_json_file

from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.module.context import Context

# Set the environment variable for the run configuration.
os.environ["RUN_CONFIGS"] = "True"

# Load configuration data.
_configs = Config.get_instance().config_data

INSTANTIATION_RESULT_MAP = {
    True: "instantiation_pass",
    False: "instantiation_fail"
}

EXECUTION_RESULT_MAP = {
    "pass": "execution_pass",
    "fail": "execution_fail",
    "unsure": "execution_unsure"
}

class AppEnum(Enum):
    """
    Enum class for applications.
    """

    WORD = 1, "Word", ".docx", "winword"
    EXCEL = 2, "Excel", ".xlsx", "excel"
    POWERPOINT = 3, "PowerPoint", ".pptx", "powerpnt"

    def __init__(self, id: int, description: str, file_extension: str, win_app: str):
        """
        Initialize the application enum.
        :param id: The ID of the application.
        :param description: The description of the application.
        :param file_extension: The file extension of the application.
        :param win_app: The Windows application name.
        """

        self.id = id
        self.description = description
        self.file_extension = file_extension
        self.win_app = win_app
        self.app_root_name = win_app.upper() + ".EXE"


class TaskObject:
    def __init__(self, task_file_path: str, mode: str) -> None:
        """
        Initialize the task object.
        :param task_file_path: The path to the task file.
        :param mode: The mode of the task object (dataflow, instantiation, or execution).
        """

        self.task_file_path = task_file_path
        self.task_file_base_name = os.path.basename(task_file_path)
        self.task_file_name = self.task_file_base_name.split(".")[0]

        task_json_file = load_json_file(task_file_path)
        self.app_object = self._choose_app_from_json(task_json_file["app"])
        # Initialize the task attributes based on the mode
        self._init_attr(mode, task_json_file)

    def _choose_app_from_json(self, task_app: str) -> AppEnum:
        """
        Choose the app from the task json file.
        :param task_app: The app from the task json file.
        :return: The app enum.
        """

        for app in AppEnum:
            if app.description.lower() == task_app.lower():
                return app
        raise ValueError("Not a correct App") 
    
    def _init_attr(self, mode:str, task_json_file:Dict[str, Any]) -> None:
        """
        Initialize the attributes of the task object.
        :param mode: The mode of the task object (dataflow, instantiation, or execution).
        :param task_json_file: The task JSON file.
        """

        if mode == "dataflow" or mode == "instantiation":
            for key, value in task_json_file.items():
                setattr(self, key.lower().replace(" ", "_"), value)
        elif mode == "execution":
            self.app = task_json_file.get("app")
            self.unique_id = task_json_file.get("unique_id")
            original = task_json_file.get("original", {})
            self.task = original.get("original_task", None) 
            self.refined_steps = original.get("original_steps", None)
        else:
            raise ValueError(f"Unsupported mode: {mode}")

class DataFlowController:
    """
    Flow controller class to manage the instantiation and execution process.
    """

    def __init__(self, task_path: str, mode: str) -> None:
        """
        Initialize the flow controller.
        :param task_path: The path to the task file.
        :param mode: The mode of the flow controller (instantiation, execution, or dataflow).
        """

        self.task_object = TaskObject(task_path, mode)
        self.app_env = None
        self.app_name = self.task_object.app_object.description.lower()
        self.task_file_name = self.task_object.task_file_name

        self.schema = load_json_file(Config.get_instance().config_data["RESULT_SCHEMA"])
        
        self.mode = mode
        self.task_info = self.init_task_info()
        self.result_hub = _configs["RESULT_HUB"].format(mode=mode)

    def init_task_info(self) -> dict: 
        """
        Initialize the task information.
        :return: The initialized task information.
        """
        init_task_info = None
        if self.mode == "execution":
            # read from the instantiated task file
            init_task_info = load_json_file(self.task_object.task_file_path)
        else:
            init_task_info = {
                "unique_id": self.task_object.unique_id,
                "app": self.app_name,
                "original": {
                    "original_task": self.task_object.task,
                    "original_steps": self.task_object.refined_steps,
                },
                "execution_result": {"result": None, "error": None},
                "instantiation_result": {
                    "choose_template": {"result": None, "error": None},
                    "prefill": {"result": None, "error": None},
                    "instantiation_evaluation": {"result": None, "error": None},
                },
                "time_cost": {},
            }
        return init_task_info


    def execute_instantiation(self):
        """
        Execute the instantiation process.
        """

        print_with_color(f"Instantiating task {self.task_object.task_file_name}...", "blue")

        template_copied_path = self.instantiation_single_flow(
            ChooseTemplateFlow, "choose_template", 
            init_params=[self.task_object.app_object.file_extension],
            execute_params=[]
        )

        if template_copied_path:
            self.app_env.start(template_copied_path)

            prefill_result = self.instantiation_single_flow(
                PrefillFlow, "prefill", 
                init_params=[self.app_env],
                execute_params=[template_copied_path, self.task_object.task, self.task_object.refined_steps]
            )

            if prefill_result:
                self.instantiation_single_flow(
                    FilterFlow, "instantiation_evaluation",
                    init_params=[],
                    execute_params=[prefill_result["instantiated_request"]]
                )
                return prefill_result["instantiated_plan"]

    def execute_execution(self, request: str, plan: dict) -> None:
        """
        Execute the execution process.
        :param request: The task request to be executed.
        :param plan: The execution plan containing detailed steps.
        """

        print_with_color("Executing the execution process...", "blue")
        execute_flow = None

        try:
            # Start the application and open the copied template
            self.app_env.start(self.template_copied_path)

            # Initialize the execution context and flow
            context = Context()
            execute_flow = ExecuteFlow(self.task_file_name, context, self.app_env)
            
            # Execute the plan
            executed_plan, execute_result = execute_flow.execute(request, plan)
            
            # Update the instantiated plan
            self.instantiated_plan = executed_plan
            # Record execution results and time metrics
            self.task_info["execution_result"]["result"] = execute_result
            self.task_info["time_cost"]["execute"] = execute_flow.execution_time
            self.task_info["time_cost"]["execute_eval"] = execute_flow.eval_time

        except Exception as e:
            # Handle and log any exceptions that occur during execution
            error_traceback = traceback.format_exc()
            self.task_info["execution_result"]["error"] = {
                "type": str(type(e).__name__),
                "message": str(e),
                "traceback": error_traceback,
            }
            print_with_color(f"Error in Execution: {e}", "red")
        finally:
            # Record the total time cost of the execution process
            if execute_flow and hasattr(execute_flow, "execution_time"):
                self.task_info["time_cost"]["execute"] = execute_flow.execution_time
            else:
                self.task_info["time_cost"]["execute"] = None
            if execute_flow and hasattr(execute_flow, "eval_time"):
                self.task_info["time_cost"]["execute_eval"] = execute_flow.eval_time
            else:
                self.task_info["time_cost"]["execute_eval"] = None


    def instantiation_single_flow(
            self, 
            flow_class: AppAgentProcessor, 
            flow_type: str, 
            init_params=None, 
            execute_params=None
        ) -> Any:
        """
        Execute a single flow process in the instantiation phase.
        :param flow_class: The flow class to instantiate.
        :param flow_type: The type of the flow.
        :param init_params: The initialization parameters for the flow.
        :param execute_params: The execution parameters for the flow.
        :return: The result of the flow process.
        """
        
        flow_instance = None
        try:
            flow_instance = flow_class(self.app_name, self.task_file_name, *init_params)
            result = flow_instance.execute(*execute_params)
            self.task_info["instantiation_result"][flow_type]["result"] = result
            return result
        except Exception as e:
            self.task_info["instantiation_result"][flow_type]["error"] = {
                "type": str(e.__class__),
                "error_message": str(e),
                "traceback": traceback.format_exc(),
            }
            print_with_color(f"Error in {flow_type}: {e} {traceback.format_exc()}")
        finally:
            if flow_instance and hasattr(flow_instance, "execution_time"):
                self.task_info["time_cost"][flow_type] = flow_instance.execution_time
            else:
                self.task_info["time_cost"][flow_type] = None
    
    def save_result(self) -> None:
        """
        Validate and save the instantiated task result.
        """

        validation_error = None

        # Validate the result against the schema
        try:
            validate(instance=self.task_info, schema=self.schema)
        except ValidationError as e:
            # Record the validation error but allow the process to continue
            validation_error = str(e.message)
            print_with_color(f"Warning: Schema Validation Warning: {validation_error}", "yellow")

        # Determine the target directory based on mode and quality/completeness
        target_file = None

        if self.mode == "instantiation":
            # Determine the quality of the instantiation
            if not self.task_info["instantiation_result"]["instantiation_evaluation"]["result"]:
                target_file = INSTANTIATION_RESULT_MAP[False]
            else:
                is_quality_good = self.task_info["instantiation_result"]["instantiation_evaluation"]["result"]["judge"]
                target_file = INSTANTIATION_RESULT_MAP.get(is_quality_good, INSTANTIATION_RESULT_MAP[False])

        else:
            # Determine the completion status of the execution
            if not self.task_info["execution_result"]["result"]:
                target_file = EXECUTION_RESULT_MAP["fail"]
            else:
                is_completed = self.task_info["execution_result"]["result"]["complete"]
                target_file = EXECUTION_RESULT_MAP.get(is_completed, EXECUTION_RESULT_MAP["fail"])

        # Construct the full path to save the result
        new_task_path = os.path.join(self.result_hub, target_file, self.task_object.task_file_base_name)
        os.makedirs(os.path.dirname(new_task_path), exist_ok=True)
        save_json_file(new_task_path, self.task_info)

        print(f"Task saved to {new_task_path}")

        # If validation failed, indicate that the saved result may need further inspection
        if validation_error:
            print("The saved task result does not conform to the expected schema and may require review.")
    
    @property
    def template_copied_path(self) -> str:
        """
        Get the copied template path from the task information.
        :return: The copied template path.
        """

        return self.task_info["instantiation_result"]["choose_template"]["result"]
    
    @property
    def instantiated_plan(self) -> list[dict[str, Any]]:
        """
        Get the instantiated plan from the task information.
        :return: The instantiated plan.
        """

        return self.task_info["instantiation_result"]["prefill"]["result"]["instantiated_plan"]

    @instantiated_plan.setter
    def instantiated_plan(self, value: list[dict[str, Any]]) -> None:
        """
        Set the instantiated plan in the task information.
        :param value: New value for the instantiated plan.
        """

        self.task_info.setdefault("instantiation_result", {}).setdefault("prefill", {}).setdefault("result", {})
        self.task_info["instantiation_result"]["prefill"]["result"]["instantiated_plan"] = value

    def run(self) -> None:
        """
        Run the instantiation and execution process.
        """

        start_time = time.time()

        try:
            self.app_env = WindowsAppEnv(self.task_object.app_object)

            if self.mode == "dataflow":
                plan = self.execute_instantiation()
                self.execute_execution(self.task_object.task, plan)
            elif self.mode == "instantiation":
                self.execute_instantiation()
            elif self.mode == "execution":
                plan = self.instantiated_plan
                self.execute_execution(self.task_object.task, plan)
            else:
                raise ValueError(f"Unsupported mode: {self.mode}")
        except Exception as e:
            raise e

        finally:
            if self.app_env:
                self.app_env.close()
            # Update or record the total time cost of the process
            total_time = round(time.time() - start_time, 3)
            new_total_time = self.task_info.get("time_cost", {}).get("total", 0) + total_time
            self.task_info["time_cost"]["total"] = round(new_total_time, 3)

            self.save_result()