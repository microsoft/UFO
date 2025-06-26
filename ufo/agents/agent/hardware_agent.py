from ufo.agents.agent.basic import AgentRegistry

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


@AgentRegistry.register(agent_name="HardwareAgent", third_party=True)
class HardwareAgent(AppAgent):
    """
    HardwareAgent is a specialized agent that interacts with hardware components.
    It extends the BasicAgent to provide additional functionality specific to hardware.
    """

    def process(self, context: Context) -> None:
        """
        Process the agent.
        :param context: The context.
        """
        self.processor = HardwareAgentProcessor(agent=self, context=context)
        self.processor.process()
        self.status = self.processor.status
