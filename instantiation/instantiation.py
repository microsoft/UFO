# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import glob
import json
import os
import sys
from enum import Enum

# Add the project root to the system path.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

if project_root not in sys.path:
    sys.path.append(project_root)

# Set the environment variable.
os.environ["RUN_CONFIGS"] = "false"

# Parse the arguments.
args = argparse.ArgumentParser()
args.add_argument(
    "--task", help="The name of the task.", type=str, default="prefill"
)
parsed_args = args.parse_args()

class AppEnum(Enum):
    """
    Define the apps can be used in the instantiation.
    """

    WORD = 1, "Word", ".docx", "winword"
    EXCEL = 2, "Excel", ".xlsx", "excel"
    POWERPOINT = 3, "PowerPoint", ".pptx", "powerpnt"

    def __init__(self, id : int, description : str, file_extension : str, win_app : str):
        """
        :param id: The unique id of the app.
        :param description: The description of the app. Example: Word, Excel, PowerPoint.
        :param file_extension: The file extension of the app. Example: .docx, .xlsx, .pptx.
        :param win_app: The windows app name of the app. Example: winword, excel, powerpnt.
        """

        self.id = id
        self.description = description
        self.file_extension = file_extension
        self.win_app = win_app
        # The root name of the app to be used in opening and closing app window.
        self.app_root_name = win_app.upper() + ".EXE"


class TaskObject():
    """
    The task object from the json file.
    """

    def __init__(self, task_dir_name : str, task_file: str) -> None:
        """
        Initialize the task object from the json file.
        :param task_file: The task file to load from.
        """

        self.task_dir_name = task_dir_name
        self.task_file = task_file
        # The folder name of the task, specific for one process. Example: prefill.
        self.task_file_dir_name = os.path.dirname(os.path.dirname(task_file))
        # The base name of the task file. Example: task_1.json.
        self.task_file_base_name = os.path.basename(task_file)
        # The task name of the task file without extension. Example: task_1.
        self.task_file_name = self.task_file_base_name.split(".")[0]
        
        # Load the json file and get the app object.
        with open(task_file, "r") as f:
            task_json_file = json.load(f)
        self.app_object = self.choose_app_from_json(task_json_file)

        for key, value in task_json_file.items():
            setattr(self, key.lower().replace(" ", "_"), value)

        # The fields to be saved in the json file.
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
            app_name = app.description.lower()
            json_app_name = task_json_file["app"].lower()
            if app_name == json_app_name:
                return app
        raise ValueError("Not a correct App")


    def to_json(self) -> dict:
        """
        Convert the object to a JSON object.
        :return: The JSON object.
        """
        json_data = {}
        for key in self.json_fields:
            if hasattr(self, key):
                json_data[key] = getattr(self, key)
        return json_data

    def set_attributes(self, **kwargs) -> None:
        """
        Add all input fields as attributes.
        :param kwargs: The fields to be added.
        """

        for key, value in kwargs.items():
            setattr(self, key, value)


class InstantiationProcess:
    """
    Key process to instantialize the task.
    Control the process of the task.
    """    

    def instantiate_files(self, task_dir_name: str) -> None:
        """
        """

        all_task_file_path: str = os.path.join(configs["TASKS_HUB"], task_dir_name, "*")
        all_task_files = glob.glob(all_task_file_path)

        for index, task_file in enumerate(all_task_files, start=1):
            print(f"Task starts: {index} / {len(all_task_files)}")
            try:

                task_object = TaskObject(task_dir_name, task_file)
                self.instantiate_single_file(task_object)
            except Exception as e:
                print(f"Error in task {index} with file {task_file}: {e}")

        print("All tasks have been processed.")

    def instantiate_single_file(self, task_object : TaskObject) -> None:
        """
        Execute the process for one task.
        :param task_object: The TaskObject containing task details.
        The execution includes getting the instantiated result, evaluating the task and saving the instantiated task.
        """

        from instantiation.controller.workflow.choose_template_flow import ChooseTemplateFlow
        from instantiation.controller.workflow.prefill_flow import PrefillFlow
        from instantiation.controller.workflow.filter_flow import FilterFlow

        ChooseTemplateFlow(task_object).execute()
        PrefillFlow(task_object).execute()
        FilterFlow(task_object).execute()



def main():
    """
    The main function to process the tasks.
    """

    # Load the configs.
    from instantiation.config.config import Config

    config_path = (
        os.path.normpath(os.path.join(current_dir, "config/")) + "\\"
    )
    global configs
    configs = Config(config_path).get_instance().config_data

    task_dir_name = parsed_args.task.lower()
    
    InstantiationProcess().instantiate_files(task_dir_name)

if __name__ == "__main__":
    main()