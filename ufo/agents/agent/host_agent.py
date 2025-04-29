# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from __future__ import annotations

from typing import Dict, List, Union

from ufo import utils
from ufo.agents.agent.app_agent import AppAgent, OpenAIOperatorAgent
from ufo.agents.agent.basic import BasicAgent
from ufo.agents.agent.follower_agent import FollowerAgent
from ufo.agents.memory.blackboard import Blackboard
from ufo.agents.processors.host_agent_processor import HostAgentProcessor
from ufo.agents.states.host_agent_state import ContinueHostAgentState, HostAgentStatus
from ufo.automator import puppeteer
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
        elif agent_type == "batch_normal":
            return AppAgent(*args, **kwargs)
        elif agent_type == "operator":
            return OpenAIOperatorAgent(*args, **kwargs)
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
            is_visual, main_prompt, example_prompt, api_prompt
        )
        self.offline_doc_retriever = None
        self.online_doc_retriever = None
        self.experience_retriever = None
        self.human_demonstration_retriever = None
        self.agent_factory = AgentFactory()
        self.appagent_dict = {}
        self._active_appagent = None
        self._blackboard = Blackboard()
        self.set_state(self.default_state)
        self.Puppeteer = self.create_puppeteer_interface()

    def get_prompter(
        self,
        is_visual: bool,
        main_prompt: str,
        example_prompt: str,
        api_prompt: str,
    ) -> HostAgentPrompter:
        """
        Get the prompt for the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :return: The prompter instance.
        """
        return HostAgentPrompter(is_visual, main_prompt, example_prompt, api_prompt)

    def create_subagent(
        self,
        agent_type: str,
        agent_name: str,
        process_name: str,
        app_root_name: str,
        *args,
        **kwargs,
    ) -> BasicAgent:
        """
        Create an SubAgent hosted by the HostAgent.
        :param agent_type: The type of the agent to create.
        :param agent_name: The name of the SubAgent.
        :param process_name: The process name of the app.
        :param app_root_name: The root name of the app.
        :return: The created SubAgent.
        """
        app_agent = self.agent_factory.create_agent(
            agent_type,
            agent_name,
            process_name,
            app_root_name,
            # is_visual,
            # main_prompt,
            # example_prompt,
            # api_prompt,
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
    def blackboard(self) -> Blackboard:
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
        blackboard_prompt: List[Dict[str, str]],
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

        if blackboard_prompt:
            hostagent_prompt_user_message = (
                blackboard_prompt + hostagent_prompt_user_message
            )

        hostagent_prompt_message = self.prompter.prompt_construction(
            hostagent_prompt_system_message, hostagent_prompt_user_message
        )

        return hostagent_prompt_message

    def process(self, context: Context) -> None:
        """
        Process the agent.
        :param context: The context.
        """
        self.processor = HostAgentProcessor(agent=self, context=context)
        self.processor.process()

        # Sync the status with the processor.
        self.status = self.processor.status

    def create_puppeteer_interface(self) -> puppeteer.AppPuppeteer:
        """
        Create the Puppeteer interface to automate the app.
        :return: The Puppeteer interface.
        """
        return puppeteer.AppPuppeteer("", "")

    def create_app_agent(
        self,
        application_window_name: str,
        application_root_name: str,
        request: str,
        mode: str,
    ) -> AppAgent:
        """
        Create the app agent for the host agent.
        :param application_window_name: The name of the application window.
        :param application_root_name: The name of the application root.
        :param request: The user request.
        :param mode: The mode of the session.
        :return: The app agent.
        """

        if configs.get("ACTION_SEQUENCE", False):
            example_prompt = configs["APPAGENT_EXAMPLE_PROMPT_AS"]
        else:
            example_prompt = configs["APPAGENT_EXAMPLE_PROMPT"]

        if mode in ["normal", "batch_normal", "follower"]:

            agent_name = (
                "AppAgent/{root}/{process}".format(
                    root=application_root_name, process=application_window_name
                )
                if mode == "normal"
                else "BatchAgent/{root}/{process}".format(
                    root=application_root_name, process=application_window_name
                )
            )

            app_agent: AppAgent = self.create_subagent(
                agent_type="app",
                agent_name=agent_name,
                process_name=application_window_name,
                app_root_name=application_root_name,
                is_visual=configs["APP_AGENT"]["VISUAL_MODE"],
                main_prompt=configs["APPAGENT_PROMPT"],
                example_prompt=example_prompt,
                api_prompt=configs["API_PROMPT"],
                mode=mode,
            )

        elif mode in ["normal_operator", "batch_normal_operator"]:

            agent_name = (
                "OpenAIOperator/{root}/{process}".format(
                    root=application_root_name, process=application_window_name
                )
                if mode == "normal_operator"
                else "BatchOpenAIOperator/{root}/{process}".format(
                    root=application_root_name, process=application_window_name
                )
            )

            app_agent: OpenAIOperatorAgent = self.create_subagent(
                "operator",
                agent_name=agent_name,
                process_name=application_window_name,
                app_root_name=application_root_name,
            )

        else:
            raise ValueError(f"The {mode} mode is not supported.")

        # Create the COM receiver for the app agent.
        if configs.get("USE_APIS", False):
            app_agent.Puppeteer.receiver_manager.create_api_receiver(
                application_root_name, application_window_name
            )

        # Provision the context for the app agent, including the all retrievers.
        app_agent.context_provision(request)

        return app_agent

    def process_comfirmation(self) -> None:
        """
        TODO: Process the confirmation.
        """
        pass

    def print_response(self, response_dict: Dict) -> None:
        """
        Print the response.
        :param response_dict: The response dictionary to print.
        """

        application = response_dict.get("ControlText")
        if not application:
            application = "[The required application needs to be opened.]"
        observation = response_dict.get("Observation")
        thought = response_dict.get("Thought")
        bash_command = response_dict.get("Bash", None)
        subtask = response_dict.get("CurrentSubtask")

        # Convert the message from a list to a string.
        message = list(response_dict.get("Message", ""))
        message = "\n".join(message)

        # Concatenate the subtask with the plan and convert the plan from a list to a string.
        plan = list(response_dict.get("Plan"))
        plan = [subtask] + plan
        plan = "\n".join([f"({i+1}) " + str(item) for i, item in enumerate(plan)])

        status = response_dict.get("Status")
        comment = response_dict.get("Comment")

        utils.print_with_color(
            "Observations👀: {observation}".format(observation=observation), "cyan"
        )
        utils.print_with_color("Thoughts💡: {thought}".format(thought=thought), "green")
        if bash_command:
            utils.print_with_color(
                "Running Bash Command🔧: {bash}".format(bash=bash_command), "yellow"
            )
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

    @property
    def default_state(self) -> ContinueHostAgentState:
        """
        Get the default state.
        """
        return ContinueHostAgentState()
