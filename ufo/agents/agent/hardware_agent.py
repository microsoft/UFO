from ufo.agents.agent.basic import AgentRegistry

from ufo.agents.agent.app_agent import AppAgent
from ufo.config import Config
from ufo.module.context import Context

from ufo.agents.processors.hardware_agent_processor import HardwareAgentProcessor


configs = Config.get_instance().config_data


@AgentRegistry.register(agent_name="HardwareAgent", third_party=True)
class HardwareAgent(AppAgent):
    """
    HardwareAgent is a specialized agent that interacts with hardware components.
    It extends the BasicAgent to provide additional functionality specific to hardware.
    """

    async def process(self, context: Context) -> None:
        """
        Process the agent.
        :param context: The context.
        """
        if not self._context_provision_executed:
            await self.context_provision(context=context)
            self._context_provision_executed = True

        self.processor = HardwareAgentProcessor(agent=self, context=context)
        await self.processor.process()
        self.status = self.processor.status
