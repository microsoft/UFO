from ufo.agents.agent.basic import BasicAgent

from ufo.agents.agent.app_agent import AppAgent
from ufo.config import Config
from ufo.module import interactor
from ufo.module.context import Context, ContextNames
from ufo.prompter.agent_prompter import AppAgentPrompter
from typing import Any, Dict, List, Optional, Tuple, Union

from ufo.cs.contracts import MCPGetInstructionsAction, MCPGetInstructionsParams
from ufo.llm import AgentType


from ufo.agents.processors.app_agent_action_seq_processor import (
    HardwareAgentActionSequenceProcessor,
)
from ufo.agents.processors.app_agent_processor import AppAgentProcessor

configs = Config.get_instance().config_data


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
        if configs.get("ACTION_SEQUENCE", False):
            self.processor = HardwareAgentActionSequenceProcessor(
                agent=self, context=context
            )
        else:
            self.processor = HardwareAgentProcessor(agent=self, context=context)
        self.processor.process()
        self.status = self.processor.status
