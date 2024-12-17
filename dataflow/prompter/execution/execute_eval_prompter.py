# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from typing import Dict, List, Optional

from ufo.prompter.basic import BasicPrompter
from ufo.prompter.eva_prompter import EvaluationAgentPrompter

class ExecuteEvalAgentPrompter(EvaluationAgentPrompter):
    """
    Execute the prompt for the ExecuteEvalAgent.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
        api_prompt_template: str,
        root_name: Optional[str] = None,
    ):
        """
        Initialize the CustomEvaluationAgentPrompter.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        :param api_prompt_template: The path of the api prompt template.
        :param root_name: The name of the root application.
        """

        super().__init__(
            is_visual,
            prompt_template,
            example_prompt_template,
            api_prompt_template,
            root_name,
        )

    @staticmethod
    def load_logs(log_path: str) -> List[Dict[str, str]]:
        """
        Load logs from the log path.
        :param log_path: The path of the log.
        """

        log_file_path = os.path.join(log_path, "execute_log.json")
        with open(log_file_path, "r") as f:
            logs = f.readlines()
            logs = [json.loads(log) for log in logs]
        return logs
