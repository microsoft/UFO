import json
import os
from typing import Dict, Tuple

from instantiation.config.config import Config
from instantiation.controller.agent.agent import FilterAgent
from ufo.module.basic import BaseSession

configs = Config.get_instance().config_data


class FilterFlow:
    """
    The class to refine the plan steps and prefill the file.
    """

    # A dictionary to store filter agents for each app.
    app_filter_agent_dict: Dict[str, FilterAgent] = dict()

    def __init__(self, task_object: object) -> None:
        """
        Initialize the filter flow for a task.
        :param task_object: The task object containing task details.
        """
        self.task_object = task_object
        self.app_name = self.task_object.app_object.description.lower()

        # If no filter agent exists for the app, create one and store it in the dictionary.
        if FilterFlow.app_filter_agent_dict.get(self.app_name) is None:
            FilterFlow.app_filter_agent_dict[self.app_name] = FilterAgent(
                "filter",
                self.app_name,
                is_visual=True,
                main_prompt=configs["FILTER_PROMPT"],
                example_prompt="",
                api_prompt=configs["API_PROMPT"],
            )
        self.filter_agent = FilterFlow.app_filter_agent_dict[self.app_name]

        # Set up log paths and create directories if necessary.
        self.log_path_configs = configs["FILTER_LOG_PATH"].format(
            task=self.task_object.task_file_name
        )
        os.makedirs(self.log_path_configs, exist_ok=True)

        # Initialize loggers for request messages and responses.
        self.filter_message_logger = BaseSession.initialize_logger(
            self.log_path_configs, "filter_messages.json", "w", configs
        )
        self.filter_response_logger = BaseSession.initialize_logger(
            self.log_path_configs, "filter_responses.json", "w", configs
        )

    def execute(self) -> None:
        """
        Execute the filter flow: Filter the task and save the result.
        """

        self.get_task_filtered()
        self.save_instantiated_task()

    def get_filter_res(self) -> Tuple[bool, str, str]:
        """
        Get the filtered result from the filter agent.
        :return: A tuple containing whether the request is good, the request comment, and the request type.
        """
        # app_name = self.task_object.app_object.app_name
        prompt_message = self.filter_agent.message_constructor(
            self.task_object.instantiated_request,
            self.task_object.app_object.description.lower(),
        )
        try:
            # Log the prompt message
            self.filter_message_logger.info(prompt_message)

            response_string, cost = self.filter_agent.get_response(
                prompt_message, "filter", use_backup_engine=True, configs=configs
            )
            # Log the response string
            self.filter_response_logger.info(response_string)

            # Convert the response to a dictionary and extract information.
            response_json = self.filter_agent.response_to_dict(response_string)
            request_quality_is_good = response_json["judge"]
            request_comment = response_json["thought"]
            request_type = response_json["type"]

            print("Comment for the instantiation: ", request_comment)
            return request_quality_is_good, request_comment, request_type

        except Exception as e:
            self.status = "ERROR"
            print(f"Error: {e}")
            return None

    def filter_task(self) -> Tuple[bool, str, str]:
        """
        Filter the task by sending the request to the filter agent.
        :return: A tuple containing whether the request is good, the request comment, and the request type.
        """

        try:
            return self.get_filter_res()
        except Exception as e:
            print(f"Error in filter_task: {e}")
            return False, "", ""

    def get_instance_folder_path(self) -> Tuple[str, str]:
        """
        Get the folder paths for passing and failing instances.
        :return: A tuple containing the pass and fail folder paths.
        """

        new_folder_path = os.path.join(
            configs["TASKS_HUB"], self.task_object.task_dir_name + "_instantiated"
        )
        new_folder_pass_path = os.path.join(new_folder_path, "instances_pass")
        new_folder_fail_path = os.path.join(new_folder_path, "instances_fail")
        return new_folder_pass_path, new_folder_fail_path

    def get_task_filtered(self) -> None:
        """
        Filter the task and set the corresponding attributes in the task object.
        """

        request_quality_is_good, request_comment, request_type = self.filter_task()
        self.task_object.set_attributes(
            request_quality_is_good=request_quality_is_good,
            request_comment=request_comment,
            request_type=request_type,
        )

    def save_instantiated_task(self) -> None:
        """
        Save the instantiated task to the pass / fail folder.
        """

        # Get the folder path for classified instances.
        new_folder_pass_path, new_folder_fail_path = self.get_instance_folder_path()
        # Generate the json object of the task.
        task_json = self.task_object.to_json()

        # Save the task to the pass / fail folder.
        if self.task_object.request_quality_is_good:
            new_task_path = os.path.join(
                new_folder_pass_path, self.task_object.task_file_base_name
            )
        else:
            new_task_path = os.path.join(
                new_folder_fail_path, self.task_object.task_file_base_name
            )
        os.makedirs(os.path.dirname(new_task_path), exist_ok=True)
        open(new_task_path, "w").write(json.dumps(task_json))
