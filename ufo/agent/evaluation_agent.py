# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Tuple

from ufo.agent.basic import BasicAgent
from ufo.config.config import Config

configs = Config.get_instance().config_data


class EvaluationAgent(BasicAgent):
    """
    The agent for evaluation.
    """

    def __init__(self, agent_name: str) -> None:
        """
        Initialize the agent.
        :param agent_name: The name of the agent.
        """

        super().__init__(agent_name)

    def get_prompter(self) -> None:
        """
        Run the agent.
        """

        pass

    def message_constructor(self, log_path: str) -> None:
        """
        Construct the message.
        :param log_path: The path to the log file.
        """

        pass


    def evaluate(self, log_path: str) -> Tuple[str, float]:
        """
        Evaluate the task completion.
        :param log_path: The path to the log file.
        :return: The evaluation result and the cost of LLM.
        """

        message = self.message_constructor(log_path)
        result, cost = self.get_response(message=message, namescope="app")

        return result, cost


