# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Dict, List

from dataflow.prompter.instantiation.template_prompter import TemplatePrompter

from ufo.agents.agent.basic import BasicAgent


class TemplateAgent(BasicAgent):
    """
    The Agent for choosing template.
    """

    def __init__(
        self,
        name: str,
        is_visual: bool,
        main_prompt: str,
        template_prompt: str = "",
    ):
        """
        Initialize the TemplateAgent.
        :param name: The name of the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt.
        :param template_prompt: The description of the file.
        """

        self._step = 0
        self._complete = False
        self._name = name
        self._status = None
        self.prompter: TemplatePrompter = self.get_prompter(
            is_visual, main_prompt, template_prompt
        )

    def get_prompter(
        self,
        is_visual: bool,
        main_prompt: str,
        template_prompt: str = "",
    ) -> str:
        """
        Get the prompt for the agent.
        This is the abstract method from BasicAgent that needs to be implemented.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt.
        :param template_prompt: The description of the file.
        :return: The prompt string.
        """

        return TemplatePrompter(is_visual, main_prompt, template_prompt)

    def message_constructor(
        self,
        descriptions: Dict,
        request: str,
        path: str = r"dataflow\templates\word",
    ) -> List[str]:
        """
        Construct the prompt message for the PrefillAgent.

        :return: The prompt message.
        """

        template_agent_prompt_system_message = self.prompter.system_prompt_construction(
            descriptions
        )
        template_agent_prompt_user_message = self.prompter.user_content_construction(
            path=path, request=request
        )
        appagent_prompt_message = self.prompter.prompt_construction(
            template_agent_prompt_system_message,
            template_agent_prompt_user_message,
        )

        return appagent_prompt_message

    def process_comfirmation(self) -> None:
        """
        Confirm the process.
        This is the abstract method from BasicAgent that needs to be implemented.
        """

        pass
