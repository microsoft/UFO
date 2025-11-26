import logging
from typing import Any, Dict, List, Union
from ufo.agents.agent.app_agent import AppAgent
from ufo.agents.agent.basic import AgentRegistry
from ufo.agents.memory.blackboard import Blackboard
from ufo.agents.processors.customized.customized_agent_processor import (
    CustomizedProcessor,
    HardwareAgentProcessor,
    LinuxAgentProcessor,
    MobileAgentProcessor,
)
from ufo.agents.states.linux_agent_state import ContinueLinuxAgentState
from ufo.agents.states.mobile_agent_state import ContinueMobileAgentState
from ufo.prompter.customized.linux_agent_prompter import LinuxAgentPrompter
from ufo.prompter.customized.mobile_agent_prompter import MobileAgentPrompter


@AgentRegistry.register(
    agent_name="CustomizedAgent",
    third_party=True,
    processor_cls=CustomizedProcessor,
)
class CustomizedAgent(AppAgent):
    """
    An example of a customized agent that extends the AppAgent class.
    """

    pass


@AgentRegistry.register(
    agent_name="HardwareAgent", third_party=True, processor_cls=HardwareAgentProcessor
)
class HardwareAgent(CustomizedAgent):
    """
    HardwareAgent is a specialized agent that interacts with hardware components.
    It extends the AppAgent to provide additional functionality specific to hardware.
    """

    pass


@AgentRegistry.register(
    agent_name="LinuxAgent", third_party=True, processor_cls=LinuxAgentProcessor
)
class LinuxAgent(CustomizedAgent):
    """
    LinuxAgent is a specialized agent that interacts with Linux systems.
    """

    def __init__(
        self,
        name: str,
        main_prompt: str,
        example_prompt: str,
    ) -> None:
        """
        Initialize the LinuxAgent.
        :param name: The name of the agent.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        """
        super().__init__(
            name=name,
            main_prompt=main_prompt,
            example_prompt=example_prompt,
            process_name=None,
            app_root_name=None,
            is_visual=None,
        )
        self._blackboard = Blackboard()
        self.set_state(self.default_state)

        self._context_provision_executed = False
        self.logger = logging.getLogger(__name__)

        self.logger.info(
            f"Main prompt: {main_prompt}, Example prompt: {example_prompt}"
        )

    def get_prompter(
        self, is_visual: bool, main_prompt: str, example_prompt: str
    ) -> LinuxAgentPrompter:
        """
        Get the prompt for the agent.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param is_visual: Whether the agent is visual or not. (Not enabled for LinuxAgent)
        :return: The prompter instance.
        """
        return LinuxAgentPrompter(main_prompt, example_prompt)

    @property
    def default_state(self) -> ContinueLinuxAgentState:
        """
        Get the default state.
        """
        return ContinueLinuxAgentState()

    def message_constructor(
        self,
        dynamic_examples: List[str],
        dynamic_knowledge: str,
        plan: List[str],
        request: str,
        blackboard_prompt: List[Dict[str, str]],
        last_success_actions: List[Dict[str, Any]],
    ) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Construct the prompt message for the AppAgent.
        :param dynamic_examples: The dynamic examples retrieved from the self-demonstration and human demonstration.
        :param dynamic_knowledge: The dynamic knowledge retrieved from the external knowledge base.
        :param plan: The plan list.
        :param request: The overall user request.
        :param blackboard_prompt: The prompt message from the blackboard.
        :param last_success_actions: The list of successful actions in the last step.
        :return: The prompt message.
        """
        appagent_prompt_system_message = self.prompter.system_prompt_construction(
            dynamic_examples
        )

        appagent_prompt_user_message = self.prompter.user_content_construction(
            prev_plan=plan,
            user_request=request,
            retrieved_docs=dynamic_knowledge,
            last_success_actions=last_success_actions,
        )

        if blackboard_prompt:
            appagent_prompt_user_message = (
                blackboard_prompt + appagent_prompt_user_message
            )

        appagent_prompt_message = self.prompter.prompt_construction(
            appagent_prompt_system_message, appagent_prompt_user_message
        )

        return appagent_prompt_message

    @property
    def blackboard(self) -> Blackboard:
        """
        Get the blackboard.
        :return: The blackboard.
        """
        return self._blackboard


@AgentRegistry.register(
    agent_name="MobileAgent", third_party=True, processor_cls=MobileAgentProcessor
)
class MobileAgent(CustomizedAgent):
    """
    MobileAgent is a specialized agent that interacts with Android mobile devices.
    """

    def __init__(
        self,
        name: str,
        main_prompt: str,
        example_prompt: str,
    ) -> None:
        """
        Initialize the MobileAgent.
        :param name: The name of the agent.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        """
        super().__init__(
            name=name,
            main_prompt=main_prompt,
            example_prompt=example_prompt,
            process_name=None,
            app_root_name=None,
            is_visual=None,
        )
        self._blackboard = Blackboard()
        self.set_state(self.default_state)

        self._context_provision_executed = False
        self.logger = logging.getLogger(__name__)

        self.logger.info(
            f"Main prompt: {main_prompt}, Example prompt: {example_prompt}"
        )

    def get_prompter(
        self, is_visual: bool, main_prompt: str, example_prompt: str
    ) -> MobileAgentPrompter:
        """
        Get the prompt for the agent.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param is_visual: Whether the agent is visual or not. (Enabled for MobileAgent)
        :return: The prompter instance.
        """
        return MobileAgentPrompter(main_prompt, example_prompt)

    @property
    def default_state(self) -> ContinueMobileAgentState:
        """
        Get the default state.
        """
        return ContinueMobileAgentState()

    def message_constructor(
        self,
        dynamic_examples: List[str],
        dynamic_knowledge: str,
        plan: List[str],
        request: str,
        installed_apps: List[Dict[str, Any]],
        current_controls: List[Dict[str, Any]],
        screenshot_url: str = None,
        annotated_screenshot_url: str = None,
        blackboard_prompt: List[Dict[str, str]] = None,
        last_success_actions: List[Dict[str, Any]] = None,
    ) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Construct the prompt message for the MobileAgent.
        :param dynamic_examples: The dynamic examples retrieved from demonstrations.
        :param dynamic_knowledge: The dynamic knowledge retrieved from knowledge base.
        :param plan: The plan list.
        :param request: The overall user request.
        :param installed_apps: The list of installed apps on the device.
        :param current_controls: The list of current screen controls.
        :param screenshot_url: The clean screenshot URL (base64).
        :param annotated_screenshot_url: The annotated screenshot URL (base64).
        :param blackboard_prompt: The prompt message from the blackboard.
        :param last_success_actions: The list of successful actions in the last step.
        :return: The prompt message.
        """
        if blackboard_prompt is None:
            blackboard_prompt = []
        if last_success_actions is None:
            last_success_actions = []

        mobile_agent_prompt_system_message = self.prompter.system_prompt_construction(
            dynamic_examples
        )

        mobile_agent_prompt_user_message = self.prompter.user_content_construction(
            prev_plan=plan,
            user_request=request,
            installed_apps=installed_apps,
            current_controls=current_controls,
            screenshot_url=screenshot_url,
            annotated_screenshot_url=annotated_screenshot_url,
            retrieved_docs=dynamic_knowledge,
            last_success_actions=last_success_actions,
        )

        if blackboard_prompt:
            mobile_agent_prompt_user_message = (
                blackboard_prompt + mobile_agent_prompt_user_message
            )

        mobile_agent_prompt_message = self.prompter.prompt_construction(
            mobile_agent_prompt_system_message, mobile_agent_prompt_user_message
        )

        return mobile_agent_prompt_message

    @property
    def blackboard(self) -> Blackboard:
        """
        Get the blackboard.
        :return: The blackboard.
        """
        return self._blackboard
