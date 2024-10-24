import json
import logging
import os
import time
from typing import Dict, Tuple

from instantiation.config.config import Config
from instantiation.controller.agent.agent import FilterAgent
from instantiation.instantiation import AppEnum
from ufo.module.basic import BaseSession

_configs = Config.get_instance().config_data


class FilterFlow:
    """
    Class to refine the plan steps and prefill the file based on filtering criteria.
    """

    _app_filter_agent_dict: Dict[str, FilterAgent] = {}

    def __init__(self, app_object: AppEnum, task_file_name: str) -> None:
        """
        Initialize the filter flow for a task.
        :param app_object: Application object containing task details.
        :param task_file_name: Name of the task file being processed.
        """
        self.execution_time = 0
        self._app_name = app_object.description.lower()
        self._log_path_configs = _configs["FILTER_LOG_PATH"].format(task=task_file_name)
        self._filter_agent = self._get_or_create_filter_agent()
        self._initialize_logs()

    def _get_or_create_filter_agent(self) -> FilterAgent:
        """
        Retrieve or create a filter agent for the given application.
        :return: FilterAgent instance for the specified application.
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

    def execute(self, instantiated_request) -> Tuple[bool, str, str]:
        """
        Execute the filter flow: Filter the task and save the result.
        :param instantiated_request: Request object to be filtered.
        :return: Tuple containing task quality flag, comment, and task type.
        """
        start_time = time.time()
        is_quality_good, request_comment, request_type = self._get_filtered_result(
            instantiated_request
        )
        self.execution_time = round(time.time() - start_time, 3)
        return is_quality_good, request_comment, request_type

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

    def _get_filtered_result(self, instantiated_request) -> Tuple[bool, str, str]:
        """
        Get the filtered result from the filter agent.
        :param instantiated_request: Request object containing task details.
        :return: Tuple containing task quality flag, request comment, and request type.
        """
        prompt_message = self._filter_agent.message_constructor(
            instantiated_request,
            self._app_name,
        )
        prompt_json = json.dumps(prompt_message, indent=4)
        self._filter_message_logger.info(prompt_json)

        try:
            start_time = time.time()
            response_string, _ = self._filter_agent.get_response(
                prompt_message, "filter", use_backup_engine=True, configs=_configs
            )
            response_json = self._filter_agent.response_to_dict(response_string)
            execution_time = round(time.time() - start_time, 3)

            response_json["execution_time"] = execution_time
            self._filter_response_logger.info(json.dumps(response_json, indent=4))

            return (
                response_json["judge"],
                response_json["thought"],
                response_json["type"],
            )

        except Exception as e:
            logging.exception(
                f"Error in _get_filtered_result: {str(e)} - Prompt: {prompt_message}",
                exc_info=True,
            )
            raise
