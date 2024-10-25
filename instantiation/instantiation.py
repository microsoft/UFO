# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import glob
import json
import logging
import os
import sys
import time
import traceback
from enum import Enum
from typing import Any, Dict, Tuple

from instantiation.config.config import Config
from ufo.module.basic import BaseSession

# Add the project root to the system path.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

if project_root not in sys.path:
    sys.path.append(project_root)

# Set the environment variable.
os.environ["RUN_CONFIGS"] = "false"

# Parse the arguments.
args = argparse.ArgumentParser()
args.add_argument("--task", help="The name of the task.", type=str, default="prefill")
parsed_args = args.parse_args()

_configs = Config.get_instance().config_data

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
    Control the process of the task.
    """
    def instantiate_files(self, task_dir_name: str) -> None:
        """
        Instantiate all the task files.
        :param task_dir_name: The name of the task directory.
        """
        all_task_file_path: str = os.path.join(_configs["TASKS_HUB"], task_dir_name, "*")
        all_task_files = glob.glob(all_task_file_path)

        for index, task_file in enumerate(all_task_files, start=1):
            print(f"Task starts: {index} / {len(all_task_files)}")
            try:
                task_object = TaskObject(task_dir_name, task_file)
                self.instantiate_single_file(task_object)
            except Exception as e:
                logging.exception(f"Error in task {index}: {str(e)}")
                self._handle_error(task_object.task_file_base_name, e)

        print("All tasks have been processed.")


    def instantiate_single_file(self, task_object: TaskObject) -> None:
        """
        Execute the process for one task.
        :param task_object: The TaskObject containing task details.
        """
        from instantiation.controller.workflow.choose_template_flow import ChooseTemplateFlow
        from instantiation.controller.workflow.filter_flow import FilterFlow
        from instantiation.controller.workflow.prefill_flow import PrefillFlow

        # Extract relevant task details from the TaskObject
        app_object = task_object.app_object
        task_file_name = task_object.task_file_name

        try:
            # Record the start time to measure execution duration
            start_time = time.time()
            
            # Initialize the template flow and execute it to copy the template
            choose_template_flow = ChooseTemplateFlow(app_object, task_file_name)
            template_copied_path = choose_template_flow.execute()

            # Initialize the prefill flow and execute it with the copied template and task details
            prefill_flow = PrefillFlow(app_object, task_file_name)
            instantiated_request, instantiated_plan = prefill_flow.execute(
                template_copied_path, task_object.task, task_object.refined_steps
            )

            # Initialize the filter flow to evaluate the instantiated request
            filter_flow = FilterFlow(app_object, task_file_name)
            is_quality_good, filter_result, request_type = filter_flow.execute(
                instantiated_request
            )

            # Calculate total execution time for the process
            total_execution_time = round(time.time() - start_time, 3)

            # Prepare a dictionary to store the execution time for each stage
            execution_time = {
                "choose_template": choose_template_flow.execution_time,
                "prefill": prefill_flow.execution_time,
                "filter": filter_flow.execution_time,
                "total": total_execution_time,
            }

            # Prepare the result structure to capture the filter result
            result = {
                "filter": filter_result
            }

            # Create a summary of the instantiated task information
            instantiated_task_info = {
                "unique_id": task_object.unique_id,
                "original_task": task_object.task,
                "original_steps": task_object.refined_steps,
                "instantiated_request": instantiated_request,
                "instantiated_plan": instantiated_plan,
                "result": result,
                "execution_time": execution_time,
            }

            # Save the instantiated task information using the designated method
            self._save_instantiated_task(
                instantiated_task_info, task_object.task_file_base_name, is_quality_good
            )

        except Exception as e:
            # Handle any errors encountered during the instantiation process
            logging.exception(f"Error processing task: {str(e)}")
            raise


    def _handle_error(self, task_file_base_name: str, error: Exception) -> None:
        """
        Handle error logging for task processing.
        :param task_file_base_name: The base name of the task file.
        :param error: The exception raised during processing.
        """
        error_folder = os.path.join(_configs["TASKS_HUB"], "prefill_instantiated", "instances_error")
        os.makedirs(error_folder, exist_ok=True)

        err_logger = BaseSession.initialize_logger(error_folder, task_file_base_name, "w", _configs)

        # Use splitlines to keep the original line breaks in traceback
        formatted_traceback = traceback.format_exc()

        error_log = {
            "error_message": str(error),
            "traceback": formatted_traceback,  # Keep original traceback line breaks
        }

        err_logger.error(json.dumps(error_log, ensure_ascii=False, indent=4))

    def _save_instantiated_task(
        self,
        instantiated_task_info: Dict[str, Any],
        task_file_base_name: str,
        is_quality_good: bool,
    ) -> None:
        """
        Save the instantiated task information to a JSON file.
        :param instantiated_task_info: A dictionary containing instantiated task details.
        :param task_file_base_name: The base name of the task file.
        :param is_quality_good: Indicates whether the quality of the task is good.
        """
        # Convert the dictionary to a JSON string
        task_json = json.dumps(instantiated_task_info, ensure_ascii=False, indent=4)

        # Define folder paths for passing and failing instances
        instance_folder = os.path.join(_configs["TASKS_HUB"], "prefill_instantiated")
        pass_folder = os.path.join(instance_folder, "instances_pass")
        fail_folder = os.path.join(instance_folder, "instances_fail")
        target_folder = pass_folder if is_quality_good else fail_folder

        new_task_path = os.path.join(target_folder, task_file_base_name)
        os.makedirs(os.path.dirname(new_task_path), exist_ok=True)

        with open(new_task_path, "w", encoding="utf-8") as f:
            f.write(task_json)

        print(f"Task saved to {new_task_path}")


def main():
    """
    The main function to process the tasks.
    """
    task_dir_name = parsed_args.task.lower()
    InstantiationProcess().instantiate_files(task_dir_name)


if __name__ == "__main__":
    main()
