# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from datetime import datetime
import json,glob
import argparse
import sys
from abc import ABC, abstractmethod
from enum import Enum


class AppEnum(Enum):
    """
    Define the apps can be used in the instantiation.
    """

    WORD = 1, 'Word', '.docx'
    EXCEL = 2, 'Excel', '.xlsx'
    POWERPOINT = 3, 'PowerPoint', '.pptx'

    def __init__(self, id, description, file_extension):
        self.id = id
        self.description = description
        self.file_extension = file_extension
        self.root_name = description + '.Application'

class TaskObject(ABC):
    """
    Abstract class for the task object.
    """

    @abstractmethod
    def __init__(self):
        pass

    def set_attributes(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


class TaskJsonObject(TaskObject):
    def __init__(self, json_path):
        """
        Initialize the task object from the json file.
        :param json_path: The json file path.
        :return: The created json object.
        """
        task_json_file = json.load(open(json_path, "r"))
        self.app_object = self.get_app_from_json(task_json_file)
        for key, value in task_json_file.items():
            setattr(self, key.lower().replace(" ", "_"), value)

    def get_app_from_json(self, task_json_file):
        for app in AppEnum:
            app_name = app.description.lower()
            json_app_name = task_json_file["app"].lower()
            if app_name == json_app_name:
                return app
        raise ValueError('Not a correct App')
    
    def to_json(self):
        fields = ['unique_id', 'instantiated_request', 'instantiated_plan', 'instantial_template_path', 'request_comment']
        data = {}
        for key, value in self.__dict__.items():
            if key in fields:
                if hasattr(self, key):
                    data[key] = value
        return data

class TaskPathObject(TaskObject):
    def __init__(self, task_file):
        """
        Initialize the task object from the task file path.
        :param task_file: The task file path.
        :return: The created path object.
        """

        self.task_file = task_file
        self.task_file_dir_name = os.path.dirname(os.path.dirname(task_file))
        self.task_file_base_name = os.path.basename(task_file)
        self.task=self.task_file_base_name.split('.')[0]

class TaskConfigObject(TaskObject):
    def __init__(self, configs):
        """
        Initialize the task object from the config dictionary.
        :param configs: The config dictionary.
        :return: The created config object.
        """

        for key, value in configs.items():
            setattr(self, key.lower().replace(" ", "_"), value)

class ObjectMethodService():
    """
    The object method service.
    Provide methods related to the object, which is extended from TaskObject.
    """
    def __init__(self, task_dir_name : str, task_config_object : TaskObject, task_json_object : TaskObject, task_path_object : TaskObject) -> None:
        """
        :param task_dir_name: Folder name of the task, specific for one process.
        :param task_config_object: Config object, which is singleton for one process.
        :param task_json_object: Json object, which is the json file of the task.
        :param task_path_object: Path object, which is related to the path of the task.
        """

        self.task_dir_name : str = task_dir_name
        self.task_config_object : TaskObject = task_config_object
        self.task_json_object : TaskObject = task_json_object
        self.task_path_object : TaskObject = task_path_object
    
    @classmethod
    def format_action_plans(self, action_plans : str) -> list[str]:
        if isinstance(action_plans, str):
            return action_plans.split("\n")
        elif isinstance(action_plans, list):
            return action_plans
        else:
            return []
    
    @classmethod
    def filter_task(self, app_name : str, request_to_filt : str):
        from ael.module.filter_flow import FilterFlow
        try:
            filter_flow = FilterFlow(app_name)
        except Exception as e:
            print(f"Error! ObjectMethodService#filter_task: {e}")
        else:
            try:
                is_good, comment, type = filter_flow.get_filter_res(
                    request_to_filt
                )
                return is_good, comment, type
            except Exception as e:
                print(f"Error! ObjectMethodService#filter_task: {e}")
    
    def create_cache_file(self, ori_path: str, doc_path: str, file_name: str = None) -> str:
        """
        According to the original path, create a cache file.
        :param ori_path: The original path of the file.
        :param doc_path: The path of the cache file.
        :return: The template path string as a new created file.
        """

        if not os.path.exists(doc_path):
            os.makedirs(doc_path)
        time_start = datetime.now()
        current_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
        template_extension = self.task_json_object.app_object.file_extension
        if not file_name:
            seed = os.path.join(current_path, doc_path,
                                time_start.strftime('%Y-%m-%d-%H-%M-%S') + template_extension)
        else:
            seed = os.path.join(current_path, doc_path, file_name + template_extension)
            with open(ori_path, 'rb') as f:
                ori_content = f.read()
            with open(seed, 'wb') as f:
                f.write(ori_content)
        return seed
    
    def get_choose_file(self, action_prefill_flow) -> str:
        """
        Choose the most relative template file.
        :param action_prefill_flow: The action prefill flow object.
        :return: The most relative template file path string.
        """
        templates_description_path = self.get_description_path()
        templates_file_description = json.load(open(templates_description_path, "r"))
        choose_file = action_prefill_flow.get_target_file(self.task_json_object.task, templates_file_description)
        return choose_file

    def get_description_path(self) -> str:
        return os.path.join(self.task_config_object.template_path, self.task_json_object.app_object.description.lower(), "description.json")

    def get_ori_path(self, action_prefill_flow) -> str:
        choose_file = self.get_choose_file(action_prefill_flow)
        return os.path.join(self.task_config_object.template_path, self.task_json_object.app_object.description.lower(), choose_file)
    
    def get_doc_path(self) -> str:
        return os.path.join(self.task_config_object.tasks_hub, self.task_dir_name + '_files')
    
    def get_and_save_seed_path(self, action_prefill_flow) -> str:
        seed = self.create_cache_file(self.get_ori_path(action_prefill_flow), self.get_doc_path(), self.task_path_object.task)
        self.task_json_object.instantial_template_path = seed
        return seed
    
    def get_instance_folder_path(self) -> tuple[str, str]:
        """
        Get the new folder path for the good and bad instances without creating them.
        :return: The folder path string where good / bad instances should be in.
        """

        new_folder_path = os.path.join(self.task_config_object.tasks_hub, self.task_dir_name + "_new")
        new_folder_good_path = os.path.join(new_folder_path, "good_instances")
        new_folder_bad_path = os.path.join(new_folder_path, "bad_instances")
        return new_folder_good_path, new_folder_bad_path


class ProcessProducer():
    """
    Key process to instantialize the task.
    Provide workflow to initialize and evaluate the task.
    """

    def __init__(self, task_dir_name : str, 
                 task_config_object : TaskObject, 
                 task_json_object : TaskObject,
                 task_path_object : TaskObject):
        """
        :param task_dir_name: Folder name of the task, specific for one process.
        :param task_config_object: Config object, which is singleton for one process.
        :param task_json_object: Json object, which is the json file of the task.
        :param task_path_object: Path object, which is related to the path of the task.
        """

        from instantiation.ael.module.action_prefill_flow import ActionPrefillFlow
        from instantiation.ael.env.state_manager import WindowsAppEnv

        self.task_object = ObjectMethodService(task_dir_name, task_config_object, task_json_object, task_path_object)
        self.app_env = WindowsAppEnv(task_json_object.app_object.root_name, task_json_object.app_object.description)

        self.action_prefill_flow = ActionPrefillFlow(task_json_object.app_object.description.lower(), self.app_env)
        self.action_prefill_flow.init_flow(task_path_object.task)
    
    def get_instantiated_result(self) -> tuple[str, str]:
        """
        Get the instantiated result of the task.
        :return: The instantiated request and plan string.
        """

        seed = self.task_object.get_and_save_seed_path(self.action_prefill_flow)
        try:
            self.app_env.start(seed)
            instantiated_request, instantiated_plan = self.action_prefill_flow.get_prefill_actions(
                self.task_object.task_json_object.task, self.task_object.task_json_object.refined_steps, seed)
        except Exception as e:
            print(f"Error! ProcessProducer#get_instantiated_result: {e}")
        finally:
            self.app_env.close()
        return instantiated_request, instantiated_plan
    
    
    def get_task_filtered(self, task_to_filter : str) -> tuple[bool, str, str]:
        """
        Evaluate the task by the filter.
        :param task_to_filter: The task to be evaluated.
        :return: The evaluation quality \ comment \ type of the task.
        """

        request_quality_is_good, request_comment, request_type = \
            ObjectMethodService.filter_task(self.task_object.task_json_object.app_object.description.lower(), task_to_filter)
        
        return request_quality_is_good, request_comment, request_type

    def get_task_instantiated_and_filted(self) -> None:
        """
        Get the instantiated result and evaluate the task.
        Save the task to the good / bad folder.
        """

        try:
            instantiated_request, instantiated_plan = self.get_instantiated_result()
            instantiated_plan = ObjectMethodService.format_action_plans(instantiated_plan)
            self.task_object.task_json_object.set_attributes(instantiated_request = instantiated_request, instantiated_plan=instantiated_plan)
            
            request_quality_is_good, request_comment, request_type = self.get_task_filtered(instantiated_request)
            self.task_object.task_json_object.set_attributes(request_quality_is_good=request_quality_is_good, request_comment=request_comment, request_type=request_type)
            
            self.action_prefill_flow.execute_logger.info(f"Task {self.task_object.task_path_object.task_file_base_name} has been processed successfully.")
        except Exception as e:
            print(f"Error! ProcessProducer#get_task_instantiated_and_filted: {e}")
            self.action_prefill_flow.execute_logger.info(f"Error:{e}")
    
    def save_instantiated_task(self) -> None:
        """
        Save the instantiated task to the good / bad folder.
        """
        
        new_folder_good_path, new_folder_bad_path = self.task_object.get_instance_folder_path()
        task_json = self.task_object.task_json_object.to_json()

        if self.task_object.task_json_object.request_quality_is_good:
            new_task_path = os.path.join(new_folder_good_path, self.task_object.task_path_object.task_file_base_name)
        else:
            new_task_path = os.path.join(new_folder_bad_path, self.task_object.task_path_object.task_file_base_name)
        os.makedirs(os.path.dirname(new_task_path), exist_ok=True)
        open(new_task_path,"w").write(json.dumps(task_json))

def main():
    """
    The main function to process the tasks.
    """
    from instantiation.ael.config.config import Config

    config_path = os.path.normpath(os.path.join(current_dir, 'ael/config/')) + '\\'
    configs : dict[str, str] = Config(config_path).get_instance().config_data
    task_config_object : TaskObject = TaskConfigObject(configs)

    task_dir_name = parsed_args.task.lower()
    all_task_file_path : str = os.path.join(task_config_object.tasks_hub, task_dir_name, "*")
    all_task_files = glob.glob(all_task_file_path)

    try:
        for index, task_file in enumerate(all_task_files, start = 1):
            task_json_object = TaskJsonObject(task_file)
            task_path_object = TaskPathObject(task_file)
            
            process = ProcessProducer(task_dir_name, task_config_object, task_json_object, task_path_object)
            process.get_task_instantiated_and_filted()
            process.save_instantiated_task()
            
    except Exception as e:
        print(f"Error! main: {e}")


if __name__ == "__main__":

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    
    if project_root not in sys.path:
        sys.path.append(project_root)

    os.environ["RUN_CONFIGS"] = "false"

    args = argparse.ArgumentParser()
    args.add_argument("--task", help="The name of the task.", type=str, default="action_prefill")
    parsed_args = args.parse_args()

    main()