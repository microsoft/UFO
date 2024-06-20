# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from __future__ import annotations

import time
from typing import Dict, List, Union

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agents.agent.app_agent import AppAgent
from ufo.agents.agent.basic import BasicAgent
from ufo.agents.agent.follower_agent import FollowerAgent
from ufo.agents.memory.blackboard import Blackboard
from ufo.agents.processors.host_agent_processor import HostAgentProcessor
from ufo.agents.states.host_agent_state import ContinueHostAgentState, HostAgentStatus
from ufo.automator.ui_control import openfile
from ufo.automator.ui_control.inspector import ControlInspectorFacade
from ufo.config.config import Config
from ufo.module.context import Context
from ufo.prompter.agent_prompter import HostAgentPrompter

configs = Config.get_instance().config_data


class AgentFactory:
    """
    Factory class to create agents.
    """

    @staticmethod
    def create_agent(agent_type: str, *args, **kwargs) -> BasicAgent:
        """
        Create an agent based on the given type.
        :param agent_type: The type of agent to create.
        :return: The created agent.
        """
        if agent_type == "host":
            return HostAgent(*args, **kwargs)
        elif agent_type == "app":
            return AppAgent(*args, **kwargs)
        elif agent_type == "follower":
            return FollowerAgent(*args, **kwargs)
        else:
            raise ValueError("Invalid agent type: {}".format(agent_type))


class HostAgent(BasicAgent):
    """
    The HostAgent class the manager of AppAgents.
    """

    def __init__(
        self,
        name: str,
        is_visual: bool,
        main_prompt: str,
        example_prompt: str,
        api_prompt: str,
        allow_openapp=False,
    ) -> None:
        """
        Initialize the HostAgent.
        :name: The name of the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        """
        super().__init__(name=name)
        self.prompter = self.get_prompter(
            is_visual, main_prompt, example_prompt, api_prompt, allow_openapp
        )
        self.offline_doc_retriever = None
        self.online_doc_retriever = None
        self.experience_retriever = None
        self.human_demonstration_retriever = None
        self.agent_factory = AgentFactory()
        self.appagent_dict = {}
        self._active_appagent = None
        self._blackboard = Blackboard()
        self.set_state(ContinueHostAgentState())

    def get_prompter(
        self,
        is_visual: bool,
        main_prompt: str,
        example_prompt: str,
        api_prompt: str,
        allow_openapp=False,
    ) -> HostAgentPrompter:
        """
        Get the prompt for the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :return: The prompter instance.
        """
        return HostAgentPrompter(
            is_visual, main_prompt, example_prompt, api_prompt, allow_openapp
        )

    def create_subagent(
        self,
        agent_type: str,
        agent_name: str,
        process_name: str,
        app_root_name: str,
        is_visual: bool,
        main_prompt: str,
        example_prompt: str,
        api_prompt: str,
        *args,
        **kwargs,
    ) -> BasicAgent:
        """
        Create an SubAgent hosted by the HostAgent.
        :param agent_type: The type of the agent to create.
        :param agent_name: The name of the SubAgent.
        :param process_name: The process name of the app.
        :param app_root_name: The root name of the app.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :return: The created SubAgent.
        """
        app_agent = self.agent_factory.create_agent(
            agent_type,
            agent_name,
            process_name,
            app_root_name,
            is_visual,
            main_prompt,
            example_prompt,
            api_prompt,
            *args,
            **kwargs,
        )
        self.appagent_dict[agent_name] = app_agent
        app_agent.host = self
        self._active_appagent = app_agent

        return app_agent

    @property
    def sub_agent_amount(self) -> int:
        """
        Get the amount of sub agents.
        :return: The amount of sub agents.
        """
        return len(self.appagent_dict)

    def get_active_appagent(self) -> AppAgent:
        """
        Get the active app agent.
        :return: The active app agent.
        """
        return self._active_appagent

    @property
    def blackboard(self):
        """
        Get the blackboard.
        """
        return self._blackboard

    def message_constructor(
        self,
        image_list: List[str],
        os_info: str,
        plan: List[str],
        prev_subtask: List[Dict[str, str]],
        request: str,
    ) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Construct the message.
        :param image_list: The list of screenshot images.
        :param os_info: The OS information.
        :param prev_subtask: The previous subtask.
        :param plan: The plan.
        :param request: The request.
        :return: The message.
        """
        hostagent_prompt_system_message = self.prompter.system_prompt_construction()
        hostagent_prompt_user_message = self.prompter.user_content_construction(
            image_list=image_list,
            control_item=os_info,
            prev_subtask=prev_subtask,
            prev_plan=plan,
            user_request=request,
        )

        if not self.blackboard.is_empty():
            blackboard_prompt = self.blackboard.blackboard_to_prompt()
            hostagent_prompt_user_message = (
                blackboard_prompt + hostagent_prompt_user_message
            )

        hostagent_prompt_message = self.prompter.prompt_construction(
            hostagent_prompt_system_message, hostagent_prompt_user_message
        )

        return hostagent_prompt_message

    def app_file_manager(self, app_file_info: Dict[str, str]) -> UIAWrapper:
        """
        Open the application or file for the user.
        :param app_file_info: The information of the application or file. {'APP': name of app, 'file_path': path}
        :return: The window of the application.
        """

        utils.print_with_color("Opening the required application or file...", "yellow")
        file_manager = openfile.FileController()
        results = file_manager.execute_code(app_file_info)
        time.sleep(configs.get("SLEEP_TIME", 5))
        desktop_windows_dict = ControlInspectorFacade(
            configs["CONTROL_BACKEND"]
        ).get_desktop_app_dict(remove_empty=True)
        if not results:
            self.status = "ERROR in openning the application or file."
            return None
        app_window = file_manager.find_window_by_app_name(desktop_windows_dict)
        app_name = app_window.window_text()

        utils.print_with_color(
            f"The application {app_name} has been opened successfully.", "green"
        )

        return app_window

    def process(self, context: Context) -> None:
        """
        Process the agent.
        :param context: The context.
        """
        self.processor = HostAgentProcessor(agent=self, context=context)
        self.processor.process()
        self.status = self.processor.status

    def print_response(self, response_dict: Dict) -> None:
        """
        Print the response.
        :param response: The response.
        """

        application = response_dict.get("ControlText")
        if not application:
            application = "[The required application needs to be opened.]"
        observation = response_dict.get("Observation")
        thought = response_dict.get("Thought")
        subtask = response_dict.get("CurrentSubtask")

        # Convert the message from a list to a string.
        message = list(response_dict.get("Message"))
        message = "\n".join(message)

        # Concatenate the subtask with the plan and convert the plan from a list to a string.
        plan = list(response_dict.get("Plan"))
        plan = [subtask] + plan
        plan = "\n".join(plan)

        status = response_dict.get("Status")
        comment = response_dict.get("Comment")

        utils.print_with_color(
            "Observations👀: {observation}".format(observation=observation), "cyan"
        )
        utils.print_with_color("Thoughts💡: {thought}".format(thought=thought), "green")
        utils.print_with_color(
            "Plans📚: {plan}".format(plan=plan),
            "cyan",
        )
        utils.print_with_color(
            "Next Selected application📲: {application}".format(
                application=application
            ),
            "yellow",
        )
        utils.print_with_color(
            "Messages to AppAgent📩: {message}".format(message=message), "cyan"
        )
        utils.print_with_color("Status📊: {status}".format(status=status), "blue")

        utils.print_with_color("Comment💬: {comment}".format(comment=comment), "green")

    @property
    def status_manager(self) -> HostAgentStatus:
        """
        Get the status manager.
        """
        return HostAgentStatus
