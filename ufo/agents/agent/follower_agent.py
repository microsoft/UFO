# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from __future__ import annotations

from typing import List, Dict

from ufo.agents.agent.app_agent import AppAgent
from ufo.agents.processors.follower_agent_processor import FollowerAppAgentProcessor
from ufo.module.context import Context
from ufo.prompter.agent_prompter import FollowerAgentPrompter


class FollowerAgent(AppAgent):
    """
    The FollowerAgent class the manager of a FollowedAgent that follows the step-by-step instructions for action execution within an application.
    It is a subclass of the AppAgent, which completes the action execution within the application.
    """

    def __init__(
        self,
        name: str,
        process_name: str,
        app_root_name: str,
        is_visual: bool,
        main_prompt: str,
        example_prompt: str,
        api_prompt: str,
        app_info_prompt: str,
    ):
        """
        Initialize the FollowAgent.
        :param name: The name of the agent.
        :param process_name: The process name of the app.
        :param app_root_name: The root name of the app.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :param app_info_prompt: The app information prompt file path.
        """
        super().__init__(
            name=name,
            process_name=process_name,
            app_root_name=app_root_name,
            is_visual=is_visual,
            main_prompt=main_prompt,
            example_prompt=example_prompt,
            api_prompt=api_prompt,
            skip_prompter=True,
        )

        self.prompter = self.get_prompter(
            is_visual,
            main_prompt,
            example_prompt,
            api_prompt,
            app_info_prompt,
            app_root_name,
        )

    def get_prompter(
        self,
        is_visual: str,
        main_prompt: str,
        example_prompt: str,
        api_prompt: str,
        app_info_prompt: str,
        app_root_name: str = "",
    ) -> FollowerAgentPrompter:
        """
        Get the prompter for the follower agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :param app_info_prompt: The app information prompt file path.
        :param app_root_name: The root name of the app.
        :return: The prompter instance.
        """
        return FollowerAgentPrompter(
            is_visual,
            main_prompt,
            example_prompt,
            api_prompt,
            app_info_prompt,
            app_root_name,
        )

    def message_constructor(
        self,
        dynamic_examples: str,
        dynamic_knowledge: str,
        image_list: List[str],
        control_info: str,
        prev_subtask: List[str],
        plan: List[str],
        request: str,
        subtask: str,
        host_message: List[str],
        current_state: Dict[str, str],
        state_diff: Dict[str, str],
        blackboard_prompt: List[Dict[str, str]],
        include_last_screenshot: bool,
    ) -> List[Dict[str, str]]:
        """
        Construct the prompt message for the FollowAgent.
        :param dynamic_examples: The dynamic examples retrieved from the self-demonstration and human demonstration.
        :param dynamic_knowledge: The dynamic knowledge retrieved from the self-demonstration and human demonstration.
        :param image_list: The list of screenshot images.
        :param control_info: The control information.
        :param prev_subtask: The previous subtask.
        :param plan: The plan.
        :param request: The request.
        :param subtask: The subtask.
        :param host_message: The host message.
        :param current_state: The current state of the app.
        :param state_diff: The state difference between the current state and the previous state.
        :param blackboard_prompt: The blackboard prompt.
        :param include_last_screenshot: The flag indicating whether the last screenshot should be included.
        :return: The prompt message.
        """
        followagent_prompt_system_message = self.prompter.system_prompt_construction(
            dynamic_examples
        )
        followagent_prompt_user_message = self.prompter.user_content_construction(
            image_list=image_list,
            control_item=control_info,
            prev_subtask=prev_subtask,
            prev_plan=plan,
            user_request=request,
            subtask=subtask,
            current_application=self._process_name,
            host_message=host_message,
            retrieved_docs=dynamic_knowledge,
            current_state=current_state,
            state_diff=state_diff,
            include_last_screenshot=include_last_screenshot,
        )

        followagent_prompt_message = self.prompter.prompt_construction(
            followagent_prompt_system_message, followagent_prompt_user_message
        )

        return followagent_prompt_message

    def process(self, context: Context) -> None:

        self.processor = FollowerAppAgentProcessor(agent=self, context=context)
        self.processor.process()
        self.status = self.processor.status
