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
import textwrap
from enum import Enum
from typing import Tuple

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

logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
        self.task_file_dir_name = os.path.dirname(os.path.dirname(task_file))
        self.task_file_base_name = os.path.basename(task_file)
        self.task_file_name = self.task_file_base_name.split(".")[0]

        with open(task_file, "r") as f:
            task_json_file = json.load(f)
        self.app_object = self.choose_app_from_json(task_json_file)

        for key, value in task_json_file.items():
            setattr(self, key.lower().replace(" ", "_"), value)

        self.json_fields = [
            "unique_id",
            "instantiated_request",
            "instantiated_plan",
            "instantial_template_path",
            "request_comment",
        ]

    def choose_app_from_json(self, task_json_file: dict) -> AppEnum:
        """
        Generate an app object by traversing AppEnum based on the app specified in the JSON.
        :param task_json_file: The JSON file of the task.
        :return: The app object.
        """
        for app in AppEnum:
            if app.description.lower() == task_json_file["app"].lower():
                return app
        raise ValueError("Not a correct App")

    def to_json(self) -> dict:
        """
        Convert the object to a JSON object.
        :return: The JSON object.
        """
        return {
            key: getattr(self, key) for key in self.json_fields if hasattr(self, key)
        }

    def set_attributes(self, **kwargs) -> None:
        """
        Add all input fields as attributes.
        :param kwargs: The fields to be added.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)


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
        all_task_file_path: str = os.path.join(configs["TASKS_HUB"], task_dir_name, "*")
        all_task_files = glob.glob(all_task_file_path)

        for index, task_file in enumerate(all_task_files, start=1):
            print(f"Task starts: {index} / {len(all_task_files)}")
            try:
                task_object = TaskObject(task_dir_name, task_file)
                self.instantiate_single_file(task_object)
            except Exception as e:
                logging.exception(f"Error in task {index}: {str(e)}")
                traceback.print_exc()

        print("All tasks have been processed.")

    def instantiate_single_file(self, task_object: TaskObject) -> None:
        """
        Execute the process for one task.
        :param task_object: The TaskObject containing task details.
        """
        from instantiation.controller.workflow.choose_template_flow import (
            ChooseTemplateFlow,
        )
        from instantiation.controller.workflow.filter_flow import FilterFlow
        from instantiation.controller.workflow.prefill_flow import PrefillFlow

        try:
            start_time = time.time()

            # Measure time for ChooseTemplateFlow
            start_choose_template_time = time.time()
            template_copied_path = ChooseTemplateFlow(task_object).execute()
            choose_template_duration = time.time() - start_choose_template_time

            # Measure time for PrefillFlow
            start_prefill_time = time.time()
            instantiated_task = PrefillFlow(task_object).execute(template_copied_path)
            prefill_duration = time.time() - start_prefill_time

            # Measure time for FilterFlow
            start_filter_time = time.time()
            is_quality_good = FilterFlow(task_object).execute(instantiated_task)
            filter_duration = time.time() - start_filter_time

            # Calculate total duration
            total_duration = time.time() - start_time

            durations = {
                "choose_template": choose_template_duration,
                "prefill": prefill_duration,
                "filter": filter_duration,
                "total": total_duration,
            }

            self._save_instantiated_task(task_object, is_quality_good, durations)

        except Exception as e:
            logging.exception(f"Error processing task: {str(e)}")
            self.log_error(task_object.task_file_base_name, str(e))
            raise
    

    def _save_instantiated_task(
        self, task_object: TaskObject, is_quality_good: bool, durations: dict
    ) -> None:
        """
        Save the instantiated task along with duration information to the pass/fail folder.
        :param task_object: The task object to save.
        :param is_quality_good: Indicator of whether the task quality is good.
        :param durations: A dictionary containing duration information for each flow.
        """
        pass_path, fail_path = self._get_instance_folder_path()
        task_json = task_object.to_json()
        task_json["duration_sec"] = durations

        target_folder = pass_path if is_quality_good else fail_path
        new_task_path = os.path.join(target_folder, task_object.task_file_base_name)

        os.makedirs(os.path.dirname(new_task_path), exist_ok=True)

        with open(new_task_path, "w", encoding="utf-8") as f:
            json.dump(task_json, f, ensure_ascii=False)

    def _get_instance_folder_path(self) -> Tuple[str, str]:
        """
        Get the folder paths for passing and failing instances.
        :return: A tuple containing the pass and fail folder paths.
        """
        instance_folder = os.path.join(configs["TASKS_HUB"], "prefill_instantiated")
        pass_folder = os.path.join(instance_folder, "instances_pass")
        fail_folder = os.path.join(instance_folder, "instances_fail")
        return pass_folder, fail_folder

    def log_error(self, task_file_base_name: str, message: str) -> None:
        """
        Log the error message with traceback to a specified file in JSON format.
        :param task_file_base_name: The name of the task for the log filename.
        :param message: The error message to log.
        """
        error_folder = os.path.join(
            configs["TASKS_HUB"], "prefill_instantiated", "instances_error"
        )
        os.makedirs(error_folder, exist_ok=True)
        
        # Ensure the file name has the .json extension
        error_file_path = os.path.join(error_folder, task_file_base_name)

        # Use splitlines to keep the original line breaks in traceback
        formatted_traceback = traceback.format_exc().splitlines()
        formatted_traceback = "\n".join(formatted_traceback)

        error_log = {
            "error_message": message,
            "traceback": formatted_traceback  # Keep original traceback line breaks
        }

        with open(error_file_path, "w", encoding="utf-8") as f:
            json.dump(error_log, f, indent=4, ensure_ascii=False)



def main():
    """
    The main function to process the tasks.
    """
    from instantiation.config.config import Config

    config_path = os.path.normpath(os.path.join(current_dir, "config/")) + "\\"
    global configs
    configs = Config(config_path).get_instance().config_data

    task_dir_name = parsed_args.task.lower()
    InstantiationProcess().instantiate_files(task_dir_name)


if __name__ == "__main__":
    main()
