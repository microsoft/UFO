from ufo.agents.agent.app_agent import AppAgent
from ufo.agents.agent.basic import AgentRegistry
from ufo.agents.processors.customized.customized_agent_processor import (
    CustomizedProcessor,
    HardwareAgentProcessor,
)


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
