# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.box import DOUBLE


from ufo.agents.agent.app_agent import AppAgent, OpenAIOperatorAgent
from ufo.agents.agent.basic import AgentRegistry, BasicAgent
from ufo.agents.memory.blackboard import Blackboard
from ufo.agents.processors.host_agent_processor import HostAgentProcessor
from ufo.agents.processors.schemas.response_schema import HostAgentResponse
from ufo.agents.states.host_agent_state import ContinueHostAgentState, HostAgentStatus
from config.config_loader import get_ufo_config
from aip.messages import Command, MCPToolInfo
from ufo.llm import AgentType
from ufo.module.context import Context, ContextNames
from ufo.prompter.agent_prompter import HostAgentPrompter

console = Console()

ufo_config = get_ufo_config()


class RunningMode(str, Enum):
    NORMAL = "normal"
    BATCH_NORMAL = "batch_normal"
    FOLLOWER = "follower"
    NORMAL_OPERATOR = "normal_operator"
    BATCH_OPERATOR = "batch_normal_operator"


class AgentConfigResolver:
    """Resolve configuration for creating agents."""

    @staticmethod
    def resolve_app_agent_config(
        root: str, process: str, mode: RunningMode
    ) -> Dict[str, Any]:
        """Return configuration dict for standard app agents."""

        ufo_config = get_ufo_config()

        example_prompt = (
            ufo_config.system.appagent_example_prompt_as
            if ufo_config.system.action_sequence
            else ufo_config.system.appagent_example_prompt
        )

        if mode == RunningMode.NORMAL:
            agent_name = f"AppAgent/{root}/{process}"
        elif mode in {RunningMode.BATCH_NORMAL, RunningMode.FOLLOWER}:
            agent_name = f"BatchAgent/{root}/{process}"
        else:
            raise ValueError(f"Unsupported mode for AppAgent: {mode}")

        return dict(
            agent_type="app",
            name=agent_name,
            process_name=process,
            app_root_name=root,
            is_visual=ufo_config.app_agent.visual_mode,
            main_prompt=ufo_config.system.appagent_prompt,
            example_prompt=example_prompt,
            mode=mode.value,
        )

    @staticmethod
    def resolve_operator_agent_config(
        root: str, process: str, mode: RunningMode
    ) -> Dict[str, Any]:
        """Return configuration dict for operator agents."""
        if mode == RunningMode.NORMAL_OPERATOR:
            agent_name = f"OpenAIOperator/{root}/{process}"
        elif mode == RunningMode.BATCH_OPERATOR:
            agent_name = f"BatchOpenAIOperator/{root}/{process}"
        else:
            raise ValueError(f"Unsupported mode for OperatorAgent: {mode}")

        return dict(
            agent_type="operator",
            name=agent_name,
            process_name=process,
            app_root_name=root,
        )

    @staticmethod
    def resolve_third_party_config(
        agent_name: str, mode: RunningMode
    ) -> Dict[str, Any]:
        """Return configuration dict for third-party agents."""
        ufo_config = get_ufo_config()
        cfg = ufo_config.system.third_party_agent_config.get(agent_name, {})
        return dict(
            agent_type=agent_name,
            name=agent_name,
            process_name=agent_name,
            app_root_name=agent_name,
            is_visual=cfg.get("VISUAL_MODE", True),
            main_prompt=cfg["APPAGENT_PROMPT"],
            example_prompt=cfg["APPAGENT_EXAMPLE_PROMPT"],
            mode=mode.value,
        )


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
        elif agent_type == "batch_normal":
            return AppAgent(*args, **kwargs)
        elif agent_type == "operator":
            return OpenAIOperatorAgent(*args, **kwargs)
        elif agent_type in AgentRegistry.list_agents():
            return AgentRegistry.get(agent_type)(*args, **kwargs)
        else:
            raise ValueError("Invalid agent type: {}".format(agent_type))


@AgentRegistry.register(agent_name="hostagent")
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

        self._context_provision_executed = False

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

    async def process(self, context: Context) -> None:
        """
        Process the agent.
        :param context: The context.
        """
        # from ufo.agents.processors.host_agent_processor import HostAgentProcessor

        if not self._context_provision_executed:
            await self.context_provision(context=context)
            self._context_provision_executed = True
        self.processor = HostAgentProcessor(agent=self, global_context=context)
        # self.processor = HostAgentProcessor(agent=self, context=context)
        await self.processor.process()

        # Sync the status with the processor.
        # self.status = self.processor.status
        self.status = self.processor.processing_context.get_local("status")
        self.logger.info(f"Host agent status updated to: {self.status}")

    async def context_provision(self, context: Context) -> None:
        """
        Provide the context for the agent.
        :param context: The context for the agent.
        """
        await self._load_mcp_context(context)

    async def _load_mcp_context(self, context: Context) -> None:
        """
        Load MCP context information for the current application.
        """

        self.logger.info("Loading MCP tool information...")
        result = await context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="list_tools",
                    parameters={
                        "tool_type": "action",
                    },
                    tool_type="action",
                )
            ]
        )

        tool_list = result[0].result if result else None

        tool_name_list = (
            [tool.get("tool_name") for tool in tool_list] if tool_list else []
        )

        self.logger.info(f"Loaded tool list: {tool_name_list} for the HostAgent.")

        tools_info = [MCPToolInfo(**tool) for tool in tool_list]

        self.prompter.create_api_prompt_template(tools=tools_info)

    def create_subagent(self, context: Optional["Context"] = None) -> None:
        """
        Orchestrate creation of the appropriate sub-agent.
        Decides between third-party agent and built-in app/operator agent.
        :param context: The context for the agent and session.
        """
        mode = RunningMode(context.get(ContextNames.MODE))

        assigned_third_party_agent = self.processor.processing_context.get_local(
            "assigned_third_party_agent"
        )
        # if self.processor.assigned_third_party_agent:
        if assigned_third_party_agent:
            config = AgentConfigResolver.resolve_third_party_config(
                assigned_third_party_agent, mode
            )
        else:
            window_name = context.get(ContextNames.APPLICATION_PROCESS_NAME)
            root_name = context.get(ContextNames.APPLICATION_ROOT_NAME)

            if mode in {
                RunningMode.NORMAL,
                RunningMode.BATCH_NORMAL,
                RunningMode.FOLLOWER,
            }:
                config = AgentConfigResolver.resolve_app_agent_config(
                    root_name, window_name, mode
                )
            elif mode in {RunningMode.NORMAL_OPERATOR, RunningMode.BATCH_OPERATOR}:
                config = AgentConfigResolver.resolve_operator_agent_config(
                    root_name, window_name, mode
                )
            else:
                raise ValueError(f"Unsupported mode: {mode}")

        agent_name = config.get("name")
        agent_type = config.get("agent_type")
        process_name = config.get("process_name")

        self.logger.info(f"Creating sub agent with config: {config}")

        app_agent = self.agent_factory.create_agent(**config)
        self.appagent_dict[agent_name] = app_agent
        app_agent.host = self
        self._active_appagent = app_agent

        self.logger.info(
            f"Created sub agent: {agent_name} with type {agent_type} and process name {process_name}, class {app_agent.__class__.__name__}"
        )

        return app_agent

    def process_confirmation(self) -> None:
        """
        TODO: Process the confirmation.
        """
        pass

    def _display_agent_comment(self, comment: str) -> None:
        """
        Display agent comment with enhanced UX for agent-user dialogue.

        :param comment: The comment text from the agent
        """
        if not comment:
            return

        # Create a conversation-style comment display
        comment_text = Text()

        # Add agent identifier
        comment_text.append("🤖 UFO Agent", style="bold blue")
        comment_text.append(" says:\n\n", style="dim blue")

        # Add the actual comment with proper formatting
        comment_lines = comment.split("\n")
        for i, line in enumerate(comment_lines):
            if line.strip():
                # Add bullet point for multiple lines
                if len(comment_lines) > 1 and line.strip():
                    comment_text.append("💭 ", style="cyan")
                comment_text.append(line.strip(), style="white")
                if i < len(comment_lines) - 1:
                    comment_text.append("\n")

        # Create enhanced panel with conversation styling
        comment_panel = Panel(
            Align.left(comment_text),
            title="💬 [bold yellow]Agent Dialogue[/bold yellow]",
            title_align="left",
            border_style="yellow",
            box=DOUBLE,
            padding=(1, 2),
            width=80,
        )

        # Add some visual spacing and emphasis
        console.print()  # Empty line before
        console.print("─" * 80, style="dim yellow")  # Separator line
        console.print(comment_panel)
        console.print("─" * 80, style="dim yellow")  # Separator line
        console.print()  # Empty line after

    def print_response(self, response: HostAgentResponse) -> None:
        """
        Print the response using the presenter.
        :param response: The response object to print.
        """
        # Format the action string using get_command_string and pass to presenter
        function = response.function
        arguments = response.arguments

        action_str = None
        if function:
            action_str = self.get_command_string(function, arguments)

        # Pass formatted action string as parameter instead of modifying response
        self.presenter.present_host_agent_response(response, action_str=action_str)

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

    # if __name__ == "__main__":
    #     # Example usage of the HostAgent


# host_agent = HostAgent(
#     name="HostAgent",
#     is_visual=True,
#     main_prompt="./ufo/prompts/share/base/host_agent.yaml",
#     example_prompt="./ufo/prompts/examples/visual/host_agent_example.yaml",
#     api_prompt="./ufo/prompts/share/base/api.yaml",
# )
# print("HostAgent created with name:", host_agent.name)

# host_agent.create_third_party_app_agent(
#     agent_name="HardwareAgent",
#     request="Please interact with the hardware.",
#     mode="normal",
#     context=Context(),
# )
# print("Third-party app agent created successfully.")
