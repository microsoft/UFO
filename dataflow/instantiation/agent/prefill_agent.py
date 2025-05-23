# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Dict, List

from dataflow.prompter.instantiation.prefill_prompter import PrefillPrompter

from ufo.agents.agent.basic import BasicAgent


class PrefillAgent(BasicAgent):
    """
    The Agent for task instantialization and action sequence generation.
    """

    def __init__(
        self,
        name: str,
        process_name: str,
        is_visual: bool,
        main_prompt: str,
        example_prompt: str,
        api_prompt: str,
    ):
        """
        Initialize the PrefillAgent.
        :param name: The name of the agent.
        :param process_name: The name of the process.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt.
        :param example_prompt: The example prompt.
        :param api_prompt: The API prompt.
        """

        self._step = 0
        self._complete = False
        self._name = name
        self._status = None
        self.prompter: PrefillPrompter = self.get_prompter(
            is_visual, main_prompt, example_prompt, api_prompt
        )
        self._process_name = process_name

    def get_prompter(self, is_visual: bool, main_prompt: str, example_prompt: str, api_prompt: str) -> str:
        """
        Get the prompt for the agent.
        This is the abstract method from BasicAgent that needs to be implemented.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt.
        :param example_prompt: The example prompt.
        :param api_prompt: The API prompt.
        :return: The prompt string.
        """

        return PrefillPrompter(is_visual, main_prompt, example_prompt, api_prompt)

    def message_constructor(
        self,
        dynamic_examples: str,
        given_task: str,
        reference_steps: List[str],
        log_path: str,
    ) -> List[str]:
        """
        Construct the prompt message for the PrefillAgent.
        :param dynamic_examples: The dynamic examples retrieved from the self-demonstration and human demonstration.
        :param given_task: The given task.
        :param reference_steps: The reference steps.
        :param log_path: The path of the log.
        :return: The prompt message.
        """

        prefill_agent_prompt_system_message = self.prompter.system_prompt_construction(
            dynamic_examples
        )
        prefill_agent_prompt_user_message = self.prompter.user_content_construction(
            given_task, reference_steps, log_path
        )
        appagent_prompt_message = self.prompter.prompt_construction(
            prefill_agent_prompt_system_message,
            prefill_agent_prompt_user_message,
        )

        return appagent_prompt_message

    def process_comfirmation(self) -> None:
        """
        Confirm the process.
        This is the abstract method from BasicAgent that needs to be implemented.
        """

        pass