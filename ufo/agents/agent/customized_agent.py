from ufo.agents.agent.app_agent import AppAgent
from ufo.agents.agent.basic import AgentRegistry
from ufo.agents.processors.customized_agent_processor import (
    HardwareAgentProcessor,
    CustomizedAgentProcessor,
)


@AgentRegistry.register(
    agent_name="CustomizedAgent",
    third_party=True,
    processor_cls=CustomizedAgentProcessor,
)
class CustomizedAgent(AppAgent):
    """
    An example of a customized agent that extends the AppAgent class.
    """

    pass


@AgentRegistry.register(
    agent_name="HardwareAgent", third_party=True, processor_cls=HardwareAgentProcessor
)
class HardwareAgent(AppAgent):
    """
    HardwareAgent is a specialized agent that interacts with hardware components.
    It extends the AppAgent to provide additional functionality specific to hardware.
    """

    pass
