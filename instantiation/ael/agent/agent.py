# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from ..prompter.agent_prompter import ActionPrefillPrompter, FilterPrompter
from ufo.agents.agent.basic import BasicAgent

class FilterAgent(BasicAgent):
    """
    The Agent to evaluate whether the task has been completed and whether the actions sequence has taken effects.
    """
    def __init__(self, name: str, process_name: str, is_visual: bool, main_prompt: str, example_prompt: str, api_prompt: str):
        """
        Initialize the FollowAgent.
        :agent_type: The type of the agent.
        :is_visual: The flag indicating whether the agent is visual or not.
        """
        self._step = 0
        self._complete = False
        self._name = name
        self._status = None
        self.prompter : FilterPrompter = self.get_prompter(
            is_visual, main_prompt, example_prompt, api_prompt)
        self._process_name = process_name

    def get_prompter(self, is_visual, main_prompt, example_prompt, api_prompt) -> str:
        """
        Get the prompt for the agent.
        :return: The prompt.
        """
        return FilterPrompter(is_visual, main_prompt, example_prompt, api_prompt)

    def message_constructor(self, dynamic_examples: str,
                            request: str, app:str) -> list:
        """
        Construct the prompt message for the AppAgent.
        :param dynamic_examples: The dynamic examples retrieved from the self-demonstration and human demonstration.
        :param dynamic_tips: The dynamic tips retrieved from the self-demonstration and human demonstration.
        :param image_list: The list of screenshot images.
        :param request_history: The request history.
        :param action_history: The action history.
        :param plan: The plan.
        :param request: The request.
        :return: The prompt message.
        """
        filter_agent_prompt_system_message = self.prompter.system_prompt_construction(
            dynamic_examples, app = app)
        filter_agent_prompt_user_message = self.prompter.user_content_construction(
            request)
        filter_agent_prompt_message = self.prompter.prompt_construction(
            filter_agent_prompt_system_message, filter_agent_prompt_user_message)

        return filter_agent_prompt_message
    
    def process_comfirmation(self) -> None:
        """
        Confirm the process.
        """
        pass


class ActionPrefillAgent(BasicAgent):
    """
    The Agent for task instantialization and action sequence generation.
    """

    def __init__(self, name: str, process_name: str, is_visual: bool, main_prompt: str, example_prompt: str, api_prompt: str):
        """
        Initialize the FollowAgent.
        :agent_type: The type of the agent.
        :is_visual: The flag indicating whether the agent is visual or not.
        """
        self._step = 0
        self._complete = False
        self._name = name
        self._status = None
        self.prompter:ActionPrefillPrompter = self.get_prompter(
            is_visual, main_prompt, example_prompt, api_prompt)
        self._process_name = process_name

    def get_prompter(self, is_visual, main_prompt, example_prompt, api_prompt) -> str:
        """
        Get the prompt for the agent.
        :return: The prompt.
        """
        return ActionPrefillPrompter(is_visual, main_prompt, example_prompt, api_prompt)

    def message_constructor(self, dynamic_examples: str,
                            given_task: str, 
                            reference_steps:list,
                            doc_control_state: dict,
                            log_path : str) -> list:
        """
        Construct the prompt message for the AppAgent.
        :param dynamic_examples: The dynamic examples retrieved from the self-demonstration and human demonstration.
        :param dynamic_tips: The dynamic tips retrieved from the self-demonstration and human demonstration.
        :param image_list: The list of screenshot images.
        :param request_history: The request history.
        :param action_history: The action history.
        :param plan: The plan.
        :param request: The request.
        :return: The prompt message.
        """
        action_prefill_agent_prompt_system_message = self.prompter.system_prompt_construction(
            dynamic_examples)
        action_prefill_agent_prompt_user_message = self.prompter.user_content_construction(
            given_task,reference_steps, doc_control_state, log_path)
        appagent_prompt_message = self.prompter.prompt_construction(
            action_prefill_agent_prompt_system_message, action_prefill_agent_prompt_user_message)

        return appagent_prompt_message
    
    def process_comfirmation(self) -> None:
        """
        Confirm the process.
        """
        pass