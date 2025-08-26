from ufo.agents.agent.basic import AgentRegistry

from ufo.agents.agent.app_agent import AppAgent
from ufo.config import Config

from ufo.agents.processors.hardware_agent_processor import HardwareAgentProcessor


configs = Config.get_instance().config_data


@AgentRegistry.register(
    agent_name="HardwareAgent", third_party=True, processor_cls=HardwareAgentProcessor
)
class HardwareAgent(AppAgent):
    """
    HardwareAgent is a specialized agent that interacts with hardware components.
    It extends the BasicAgent to provide additional functionality specific to hardware.
    """

    pass
