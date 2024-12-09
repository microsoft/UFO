import json
import logging
import os
import time
from typing import Dict, Tuple, Any

from dataflow.config.config import Config
from dataflow.instantiation.agent.filter_agent import FilterAgent
from ufo.module.basic import BaseSession

_configs = Config.get_instance().config_data


class FilterFlow:
    """
    Class to refine the plan steps and prefill the file based on filtering criteria.
    """

    _app_filter_agent_dict: Dict[str, FilterAgent] = {}

    def __init__(self, app_name: str, task_file_name: str) -> None:
        """
        Initialize the filter flow for a task.
        :param app_name: Name of the application being processed.
        :param task_file_name: Name of the task file being processed.
        """

        self.execution_time = None
        self._app_name = app_name
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

    def execute(self, instantiated_request: str) -> Dict[str, Any]:
        """
        Execute the filter flow: Filter the task and save the result.
        :param instantiated_request: Request object to be filtered.
        :return: Tuple containing task quality flag, comment, and task type.
        """

        start_time = time.time()
        try:
            judge, thought, request_type = self._get_filtered_result(
                instantiated_request
            )
        except Exception as e:
            raise e
        finally:
            self.execution_time = round(time.time() - start_time, 3)
        return {
            "judge": judge,
            "thought": thought,
            "request_type": request_type,
        }
    
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

    def _get_filtered_result(self, instantiated_request: str) -> Tuple[bool, str, str]:
        """
        Get the filtered result from the filter agent.
        :param instantiated_request: Request object containing task details.
        :return: Tuple containing task quality flag, request comment, and request type.
        """

        # Construct the prompt message for the filter agent
        prompt_message = self._filter_agent.message_constructor(
            instantiated_request,
            self._app_name,
        )
        prompt_json = json.dumps(prompt_message, indent=4)
        self._filter_message_logger.info(prompt_json)

        # Get the response from the filter agent
        try:
            start_time = time.time()
            response_string, _ = self._filter_agent.get_response(
                prompt_message, "filter", use_backup_engine=True, configs=_configs
            )
            try:
                fixed_response_string = self._fix_json_commas(response_string)
                response_json = self._filter_agent.response_to_dict(
                    fixed_response_string
                )
            except json.JSONDecodeError as e:
                logging.error(
                    f"JSONDecodeError: {e.msg} at position {e.pos}. Response: {response_string}"
                )
                raise e

            execution_time = round(time.time() - start_time, 3)

            response_json["execution_time"] = execution_time
            self._filter_response_logger.info(json.dumps(response_json, indent=4))

            return (
                response_json["judge"],
                response_json["thought"],
                response_json["type"],
            )
        except Exception as e:
            logging.error(f"Error occurred while filtering: {e}")
            raise e

    def _fix_json_commas(self, json_string: str) -> str:
        """
        Function to add missing commas between key-value pairs in a JSON string
        and remove newline characters for proper formatting.
        :param json_string: The JSON string to be fixed.
        :return: The fixed JSON string.
        """

        # Remove newline characters
        json_string = json_string.replace("\n", "")

        return json_string