from ufo.agents.agent.basic import BasicAgent

from ufo.agents.agent.app_agent import AppAgent
from ufo.config import Config
from ufo.module import interactor
from ufo.module.context import Context, ContextNames
from ufo.prompter.agent_prompter import AppAgentPrompter
from typing import Any, Dict, List, Optional, Tuple, Union

from ufo.cs.contracts import MCPGetInstructionsAction, MCPGetInstructionsParams
from ufo.llm import AgentType

from ufo.agents.processors.hardware_agent_processor import HardwareAgentProcessor


configs = Config.get_instance().config_data


class HardwareAgent(AppAgent):
    """
    HardwareAgent is a specialized agent that interacts with hardware components.
    It extends the BasicAgent to provide additional functionality specific to hardware.
    """

    def __init__(
        self,
        name: str,
        is_visual: bool,
        main_prompt: str,
        example_prompt: str,
        api_prompt: str,
        skip_prompter: bool = False,
        mode: str = "normal",
    ):
        """
        Initialize the HardwareAgent.
        :param name: The name of the agent.
        """
        super().__init__(
            name=name,
            process_name="hardware",
            app_root_name="hardware",
            is_visual=is_visual,
            main_prompt=main_prompt,
            example_prompt=example_prompt,
            api_prompt=api_prompt,
            skip_prompter=skip_prompter,
            mode=mode,
        )

    def process(self, context: Context) -> None:
        """
        Process the agent.
        :param context: The context.
        """
        self.processor = HardwareAgentProcessor(agent=self, context=context)
        self.processor.process()
        self.status = self.processor.status
