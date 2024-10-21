import json
import os
import time
from typing import Dict, Tuple
from venv import logger

from instantiation.config.config import Config
from instantiation.controller.agent.agent import FilterAgent
from ufo.module.basic import BaseSession

_configs = Config.get_instance().config_data


class FilterFlow:
    """
    The class to refine the plan steps and prefill the file.
    """

    _app_filter_agent_dict: Dict[str, FilterAgent] = dict()

    def __init__(self, task_object: object) -> None:
        """
        Initialize the filter flow for a task.
        :param task_object: The task object containing task details.
        """
        self.task_object = task_object
        self._app_name = task_object.app_object.description.lower()
        self._log_path_configs = _configs["FILTER_LOG_PATH"].format(
            task=self.task_object.task_file_name
        )
        self._filter_agent = self._get_or_create_filter_agent()
        self._initialize_logs()

    def _get_or_create_filter_agent(self) -> FilterAgent:
        """
        Retrieve or create a filter agent for the application.
        :return: The filter agent for the application.
        """
        if self._app_name not in FilterFlow._app_filter_agent_dict:
            FilterFlow._app_filter_agent_dict[self._app_name] = FilterAgent(
                "filter",
                self._app_name,
                is_visual=True,
                main_prompt=_configs["FILTER_PROMPT"],
                example_prompt="",
                api_prompt=_configs["API_PROMPT"],
            )
        return FilterFlow._app_filter_agent_dict[self._app_name]

    def execute(self, task_object: object = None) -> bool:
        """
        Execute the filter flow: Filter the task and save the result.
        :param task_object: Optional task object, used for external task flow passing.
        :return: True if the task quality is good, False otherwise.
        """
        if task_object:
            self.task_object = task_object

        filtered_task_attributes = self._get_task_filtered()
        return filtered_task_attributes["is_quality_good"]

    def _initialize_logs(self) -> None:
        """
        Initialize logging for filter messages and responses.
        """
        os.makedirs(self._log_path_configs, exist_ok=True)
        self._filter_message_logger = BaseSession.initialize_logger(
            self._log_path_configs, "filter_messages.json", "w", _configs
        )
        self._filter_response_logger = BaseSession.initialize_logger(
            self._log_path_configs, "filter_responses.json", "w", _configs
        )

    def _get_filter_res(self) -> Tuple[bool, str, str]:
        """
        Get the filtered result from the filter agent.
        :return: A tuple containing whether the request is good, the request comment, and the request type.
        """
        prompt_message = self._filter_agent.message_constructor(
            self.task_object.instantiated_request,
            self.task_object.app_object.description.lower(),
        )
        prompt_json = json.dumps(prompt_message, indent=4)
        self._filter_message_logger.info(prompt_json)

        try:
            start_time = time.time()
            response_string, _ = self._filter_agent.get_response(
                prompt_message, "filter", use_backup_engine=True, configs=_configs
            )
            response_json = self._filter_agent.response_to_dict(response_string)
            duration = round(time.time() - start_time, 3)

            response_json["duration_sec"] = duration
            self._filter_response_logger.info(json.dumps(response_json, indent=4))

            return (
                response_json["judge"],
                response_json["thought"],
                response_json["type"],
            )

        except Exception as e:
            logger.exception(
                f"Error in _get_filter_res: {str(e)} - Prompt: {prompt_message}",
                exc_info=True,
            )
            raise

    def _get_task_filtered(self) -> Dict[str, str]:
        """
        Filter the task and return the corresponding attributes.
        :return: A dictionary containing filtered task attributes.
        """
        request_quality_is_good, request_comment, request_type = self._get_filter_res()
        filtered_task_attributes = {
            "is_quality_good": request_quality_is_good,
            "request_comment": request_comment,
            "request_type": request_type,
        }
        return filtered_task_attributes
