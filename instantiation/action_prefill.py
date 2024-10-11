# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import glob
import json
import os
import sys
from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Dict

from langchain_community.vectorstores import FAISS


class AppEnum(Enum):
    """
    Define the apps can be used in the instantiation.
    """

    WORD = 1, "Word", ".docx", "winword"
    EXCEL = 2, "Excel", ".xlsx", "excel"
    POWERPOINT = 3, "PowerPoint", ".pptx", "powerpnt"

    def __init__(self, id, description, file_extension, win_app):
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


class TaskObject(ABC):
    """
    Abstract class for the task object.
    All the task objects should be extended from this class.
    """

    def __init__(self):
        pass


class TaskJsonObject(TaskObject):
    """
    The task object from the json file.
    """

    def __init__(self, json_path: str) -> None:
        """
        Initialize the task object from the json file.
        :param json_path: The json file path.
        """

        # Load the json file and get the app object.
        task_json_file = json.load(open(json_path, "r"))
        self.app_object = self.get_app_from_json(task_json_file)
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

    def get_app_from_json(self, task_json_file: str) -> AppEnum:
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
        for key, value in self.__dict__.items():
            if key in self.json_fields:
                if hasattr(self, key):
                    json_data[key] = value
        return json_data

    def set_attributes(self, **kwargs) -> None:
        """
        Add all input fields as attributes.
        :param kwargs: The fields to be added.
        """

        for key, value in kwargs.items():
            setattr(self, key, value)


class TaskPathObject(TaskObject):
    """
    The path object according to the task file path.
    """

    def __init__(self, task_file: str):
        """
        Initialize the task object from the task file path.
        :param task_file: The task file path.
        :return: The created path object.
        """

        self.task_file = task_file
        # The folder name of the task, specific for one process. Example: action_prefill.
        self.task_file_dir_name = os.path.dirname(os.path.dirname(task_file))
        # The base name of the task file. Example: task_1.json.
        self.task_file_base_name = os.path.basename(task_file)
        # The task name of the task file without extension. Example: task_1.
        self.task = self.task_file_base_name.split(".")[0]


class ObjectMethodService:
    """
    The object method service.
    Provide methods related to the object, which is extended from TaskObject.
    """

    def __init__(
        self,
        task_dir_name: str,
        task_json_object: TaskObject,
        task_path_object: TaskObject,
    ):
        """
        :param task_dir_name: Folder name of the task, specific for one process.
        :param task_json_object: Json object, which is the json file of the task.
        :param task_path_object: Path object, which is related to the path of the task.
        """

        self.task_dir_name = task_dir_name
        self.task_json_object = task_json_object
        self.task_path_object = task_path_object
        self.filter_flow_app = dict()

        from instantiation.controller.env.state_manager import WindowsAppEnv
        from instantiation.controller.module.action_prefill_flow import \
            ActionPrefillFlow

        self.app_env = WindowsAppEnv(task_json_object.app_object)
        self.action_prefill_flow = ActionPrefillFlow(
            task_json_object.app_object.description.lower(),
            task_path_object.task,
            self.app_env,
        )

    def filter_task(
        self, app_name: str, request_to_filter: str
    ) -> tuple[bool, str, str]:
        """
        Filter the task by the filter flow.
        :param app_name: The name of the app. Example: "Word".
        :param request_to_filt: The request to be filtered.
        :return: The evaluation quality \ comment \ type of the task.
        """

        if app_name not in self.filter_flow_app:
            from controller.module.filter_flow import FilterFlow

            filter_flow = FilterFlow(app_name)
            self.filter_flow_app[app_name] = filter_flow
        else:
            filter_flow = self.filter_flow_app[app_name]
        try:
            is_good, comment, type = filter_flow.get_filter_res(request_to_filter)
            return is_good, comment, type
        except Exception as e:
            print(f"Error! ObjectMethodService#request_to_filter: {e}")

    def create_cache_file(
        self, copy_from_path: str, copy_to_folder_path: str, file_name: str = None
    ) -> str:
        """
        According to the original path, create a cache file.
        :param copy_from_path: The original path of the file.
        :param copy_to_folder_path: The path of the cache file.
        :param file_name: The name of the task file.
        :return: The template path string as a new created file.
        """

        # Create the folder if not exists.
        if not os.path.exists(copy_to_folder_path):
            os.makedirs(copy_to_folder_path)
        time_start = datetime.now()
        current_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
        template_extension = self.task_json_object.app_object.file_extension
        if not file_name:
            cached_template_path = os.path.join(
                current_path,
                copy_to_folder_path,
                time_start.strftime("%Y-%m-%d-%H-%M-%S") + template_extension,
            )
        else:
            cached_template_path = os.path.join(
                current_path, copy_to_folder_path, file_name + template_extension
            )
            with open(copy_from_path, "rb") as f:
                ori_content = f.read()
            with open(cached_template_path, "wb") as f:
                f.write(ori_content)
        return cached_template_path

    def get_chosen_file_path(self) -> str:
        """
        Choose the most relative template file.
        :return: The most relative template file path string.
        """

        # get the description of the templates
        templates_description_path = os.path.join(
            configs["TEMPLATE_PATH"],
            self.task_json_object.app_object.description.lower(),
            "description.json",
        )
        templates_file_description = json.load(open(templates_description_path, "r"))
        # get the chosen file path
        chosen_file_path = self.get_target_template_file(
            self.task_json_object.task, templates_file_description
        )
        return chosen_file_path

    def chose_template_and_copy(self) -> str:
        """
        Choose the template and copy it to the cache folder.
        """

        # Get the chosen template file path.
        chosen_template_file_path = self.get_chosen_file_path()
        chosen_template_full_path = os.path.join(
            configs["TEMPLATE_PATH"],
            self.task_json_object.app_object.description.lower(),
            chosen_template_file_path,
        )

        # Get the target template folder path.
        target_template_folder_path = os.path.join(
            configs["TASKS_HUB"], self.task_dir_name + "_templates"
        )

        # Copy the template to the cache folder.
        template_cached_path = self.create_cache_file(
            chosen_template_full_path,
            target_template_folder_path,
            self.task_path_object.task,
        )
        self.task_json_object.instantial_template_path = template_cached_path

        return template_cached_path

    def get_target_template_file(
        self, given_task: str, doc_files_description: Dict[str, str]
    ):
        """
        Get the target file based on the semantic similarity of given task and the template file decription.
        :param given_task: The given task.
        :param doc_files_description: The description of the template files.
        :return: The target file path.
        """

        candidates = [
            doc_file_description
            for doc, doc_file_description in doc_files_description.items()
        ]
        file_doc_descriptions = {
            doc_file_description: doc
            for doc, doc_file_description in doc_files_description.items()
        }
        # use FAISS to get the top k control items texts
        db = FAISS.from_texts(candidates, self.action_prefill_flow.embedding_model)
        doc_descriptions = db.similarity_search(given_task, k=1)
        doc_description = doc_descriptions[0].page_content
        doc = file_doc_descriptions[doc_description]
        return doc

    def get_instance_folder_path(self) -> tuple[str, str]:
        """
        Get the new folder path for the passed / failed instances without creating them.
        :return: The folder path string where passed / failed instances should be in.
        """

        new_folder_path = os.path.join(
            configs["TASKS_HUB"], self.task_dir_name + "_instantiated"
        )
        new_folder_pass_path = os.path.join(new_folder_path, "instances_pass")
        new_folder_fail_path = os.path.join(new_folder_path, "instances_fail")
        return new_folder_pass_path, new_folder_fail_path

    def get_task_filtered(self) -> None:
        """
        Evaluate the task by the filter.
        :param task_to_filter: The task to be evaluated.
        :return: The evaluation quality \ comment \ type of the task.
        """

        request_quality_is_good, request_comment, request_type = self.filter_task(
            self.task_json_object.app_object.description.lower(),
            self.task_json_object.instantiated_request,
        )
        self.task_json_object.set_attributes(
            request_quality_is_good=request_quality_is_good,
            request_comment=request_comment,
            request_type=request_type,
        )

    def get_task_instantiated(self) -> None:
        """
        Get the instantiated result and evaluate the task.
        Save the task to the pass / fail folder.
        """

        # Get the instantiated result.
        template_cached_path = self.chose_template_and_copy()
        self.app_env.start(template_cached_path)
        try:
            instantiated_request, instantiated_plan = (
                self.action_prefill_flow.get_prefill_actions(
                    self.task_json_object.task,
                    self.task_json_object.refined_steps,
                    template_cached_path,
                )
            )
        except Exception as e:
            print(f"Error! get_instantiated_result: {e}")
        finally:
            self.app_env.close()

        self.task_json_object.set_attributes(
            instantiated_request=instantiated_request,
            instantiated_plan=instantiated_plan,
        )

        self.action_prefill_flow.prefill_logger.info(
            f"Task {self.task_path_object.task_file_base_name} has been processed successfully."
        )

    def save_instantiated_task(self) -> None:
        """
        Save the instantiated task to the pass / fail folder.
        """

        # Get the folder path for classified instances.
        new_folder_pass_path, new_folder_fail_path = self.get_instance_folder_path()
        # Generate the json object of the task.
        task_json = self.task_json_object.to_json()

        # Save the task to the pass / fail folder.
        if self.task_json_object.request_quality_is_good:
            new_task_path = os.path.join(
                new_folder_pass_path, self.task_path_object.task_file_base_name
            )
        else:
            new_task_path = os.path.join(
                new_folder_fail_path, self.task_path_object.task_file_base_name
            )
        os.makedirs(os.path.dirname(new_task_path), exist_ok=True)
        open(new_task_path, "w").write(json.dumps(task_json))


class ServiceController:
    """
    Key process to instantialize the task.
    Control the process of the task.
    """

    def execute(task_service: ObjectMethodService) -> None:
        """
        Execute the process for one task.
        :param task_service: The task service object.
        The execution includes getting the instantiated result, evaluating the task and saving the instantiated task.
        """

        task_service.get_task_instantiated()
        task_service.get_task_filtered()
        task_service.save_instantiated_task()


def main():
    """
    The main function to process the tasks.
    """

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
        "--task", help="The name of the task.", type=str, default="action_prefill"
    )
    parsed_args = args.parse_args()

    # Load the configs.
    from instantiation.controller.config.config import Config

    config_path = (
        os.path.normpath(os.path.join(current_dir, "controller/config/")) + "\\"
    )
    global configs
    configs = Config(config_path).get_instance().config_data

    # Get and process all the task files.
    task_dir_name = parsed_args.task.lower()
    all_task_file_path: str = os.path.join(configs["TASKS_HUB"], task_dir_name, "*")
    all_task_files = glob.glob(all_task_file_path)

    for index, task_file in enumerate(all_task_files, start=1):
        print(f"Task starts: {index} / {len(all_task_files)}")
        try:
            task_json_object = TaskJsonObject(task_file)
            task_path_object = TaskPathObject(task_file)

            task_service = ObjectMethodService(
                task_dir_name, task_json_object, task_path_object
            )
            ServiceController.execute(task_service)
        except Exception as e:
            print(f"Error in task {index} with file {task_file}: {e}")

    print("All tasks have been processed.")


if __name__ == "__main__":
    main()
