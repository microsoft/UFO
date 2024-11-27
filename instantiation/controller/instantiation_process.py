import glob
import json
import os
import time
import traceback
from contextlib import contextmanager
from enum import Enum
from typing import Any, Dict

from instantiation.config.config import Config
from ufo.module.context import Context

# Set the environment variable for the run configuration.
os.environ["RUN_CONFIGS"] = "True"

# Load configuration data.
_configs = Config.get_instance().config_data


@contextmanager
def stage_context(stage_name):
    try:
        yield stage_name
    except Exception as e:
        raise e


class AppEnum(Enum):
    """
    Define the apps that can be used in the instantiation.
    """

    WORD = 1, "Word", ".docx", "winword"
    EXCEL = 2, "Excel", ".xlsx", "excel"
    POWERPOINT = 3, "PowerPoint", ".pptx", "powerpnt"

    def __init__(self, id: int, description: str, file_extension: str, win_app: str):
        """
        :param id: The unique id of the app.
        :param description: The description of the app.
        :param file_extension: The file extension of the app.
        :param win_app: The windows app name of the app.
        """

        self.id = id
        self.description = description
        self.file_extension = file_extension
        self.win_app = win_app
        self.app_root_name = win_app.upper() + ".EXE"


class TaskObject:
    """
    The task object from the json file.
    """

    def __init__(self, task_dir_name: str, task_file: str) -> None:
        """
        Initialize the task object from the json file.
        :param task_dir_name: The name of the directory containing the task.
        :param task_file: The task file to load from.
        """

        self.task_dir_name = task_dir_name
        self.task_file = task_file
        self.task_file_base_name = os.path.basename(task_file)
        self.task_file_name = self.task_file_base_name.split(".")[0]

        with open(task_file, "r") as f:
            task_json_file = json.load(f)
        self.app_object = self._choose_app_from_json(task_json_file)

        for key, value in task_json_file.items():
            setattr(self, key.lower().replace(" ", "_"), value)

    def _choose_app_from_json(self, task_json_file: dict) -> AppEnum:
        """
        Generate an app object by traversing AppEnum based on the app specified in the JSON.
        :param task_json_file: The JSON file of the task.
        :return: The app object.
        """

        for app in AppEnum:
            if app.description.lower() == task_json_file["app"].lower():
                return app
        raise ValueError("Not a correct App")


class InstantiationProcess:
    """
    Key process to instantiate the task.
    Control the overall process.
    """

    def instantiate_files(self, task_dir_name: str) -> None:
        """
        Instantiate all the task files.
        :param task_dir_name: The name of the task directory.
        """

        all_task_file_path: str = os.path.join(
            _configs["TASKS_HUB"], task_dir_name, "*"
        )
        all_task_files = glob.glob(all_task_file_path)
        for index, task_file in enumerate(all_task_files, start=1):
            print(f"Task starts: {index} / {len(all_task_files)}")
            task_object = TaskObject(task_dir_name, task_file)
            self.instantiate_single_file(task_object)

        print("All tasks have been processed.")

    def instantiate_single_file(self, task_object: TaskObject) -> None:
        """
        Execute the process for one task.
        :param task_object: The TaskObject containing task details.
        """

        from instantiation.controller.env.env_manager import WindowsAppEnv
        from instantiation.controller.workflow.choose_template_flow import \
            ChooseTemplateFlow
        from instantiation.controller.workflow.execute_flow import ExecuteFlow
        from instantiation.controller.workflow.filter_flow import FilterFlow
        from instantiation.controller.workflow.prefill_flow import PrefillFlow

        # Initialize the app environment and the task file name.
        app_object = task_object.app_object
        app_name = app_object.description.lower()
        app_env = WindowsAppEnv(app_object)
        task_file_name = task_object.task_file_name

        stage = None  # To store which stage the error occurred at
        is_quality_good = False
        is_completed = ""
        instantiated_task_info = {
            "unique_id": task_object.unique_id,
            "original_task": task_object.task,
            "original_steps": task_object.refined_steps,
            "instantiated_request": None,
            "instantiated_plan": None,
            "result": {},
            "time_cost": {},
        }  # Initialize with a basic structure to avoid "used before assignment" error

        try:
            start_time = time.time()

            # Initialize the template flow and execute it to copy the template
            with stage_context("choose_template") as stage:
                choose_template_flow = ChooseTemplateFlow(
                    app_name, app_object.file_extension, task_file_name
                )
                template_copied_path = choose_template_flow.execute()
                instantiated_task_info["time_cost"]["choose_template"] = choose_template_flow.execution_time

            # Initialize the prefill flow and execute it with the copied template and task details
            with stage_context("prefill") as stage:
                prefill_flow = PrefillFlow(app_env, task_file_name)
                instantiated_request, instantiated_plan = prefill_flow.execute(
                    template_copied_path, task_object.task, task_object.refined_steps
                )
                instantiated_task_info["instantiated_request"] = instantiated_request
                instantiated_task_info["instantiated_plan"] = instantiated_plan
                instantiated_task_info["time_cost"]["prefill"] = prefill_flow.execution_time

            # Initialize the filter flow to evaluate the instantiated request
            with stage_context("filter") as stage:
                filter_flow = FilterFlow(app_name, task_file_name)
                is_quality_good, filter_result, request_type = filter_flow.execute(
                    instantiated_request
                )
                instantiated_task_info["result"]["filter"] = filter_result
                instantiated_task_info["time_cost"]["filter"] = filter_flow.execution_time

            # Initialize the execute flow and execute it with the instantiated plan
            with stage_context("execute") as stage:
                context = Context()
                execute_flow = ExecuteFlow(app_env, task_file_name, context)
                execute_result, _ = execute_flow.execute(
                    task_object.task, instantiated_plan
                )
                is_completed = execute_result["complete"]
                instantiated_task_info["result"]["execute"] = execute_result
                instantiated_task_info["time_cost"]["execute"] = execute_flow.execution_time

            # Calculate total execution time for the process
            instantiation_time = round(time.time() - start_time, 3)
            instantiated_task_info["time_cost"]["total"] = instantiation_time

        except Exception as e:
            instantiated_task_info["error"] = {
                "stage": stage,
                "type": str(e.__class__),
                "error_message": str(e),
                "traceback": traceback.format_exc(),
            }

        finally:
            app_env.close()
            self._save_instantiated_task(
                instantiated_task_info,
                task_object.task_file_base_name,
                is_quality_good,
                is_completed,
            )

    def _save_instantiated_task(
        self,
        instantiated_task_info: Dict[str, Any],
        task_file_base_name: str,
        is_quality_good: bool,
        is_completed: str,
    ) -> None:
        """
        Save the instantiated task information to a JSON file.
        :param instantiated_task_info: A dictionary containing instantiated task details.
        :param task_file_base_name: The base name of the task file.
        :param is_quality_good: Indicates whether the quality of the task is good.
        :param is_completed: Indicates whether the task is completed.
        """
        
        # Convert the dictionary to a JSON string
        task_json = json.dumps(instantiated_task_info, ensure_ascii=False, indent=4)

        # Define folder paths for passing and failing instances
        instance_folder = os.path.join(_configs["TASKS_HUB"], "instantiated_results")
        pass_folder = os.path.join(instance_folder, "instances_pass")
        fail_folder = os.path.join(instance_folder, "instances_fail")
        unsure_folder = os.path.join(instance_folder, "instances_unsure")

        if is_completed == "unsure":
            target_folder = unsure_folder
        elif is_completed == "yes" and is_quality_good:
            target_folder = pass_folder
        else:
            target_folder = fail_folder

        new_task_path = os.path.join(target_folder, task_file_base_name)
        os.makedirs(os.path.dirname(new_task_path), exist_ok=True)

        with open(new_task_path, "w", encoding="utf-8") as f:
            f.write(task_json)

        print(f"Task saved to {new_task_path}")
