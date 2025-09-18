# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ufo.agents.agent.basic import BasicAgent
from ufo.agents.states.evaluaton_agent_state import EvaluatonAgentStatus
from ufo.config import Config
from ufo.contracts.contracts import MCPToolInfo
from ufo.module.context import Context, ContextNames
from ufo.prompter.eva_prompter import EvaluationAgentPrompter
from ufo.utils import json_parser, print_with_color

console = Console()

configs = Config.get_instance().config_data


class EvaluationAgent(BasicAgent):
    """
    The agent for evaluation.
    """

    def __init__(
        self,
        name: str,
        is_visual: bool,
        main_prompt: str,
        example_prompt: str,
    ):
        """
        Initialize the FollowAgent.
        :agent_type: The type of the agent.
        :is_visual: The flag indicating whether the agent is visual or not.
        """

        super().__init__(name=name)

        self.prompter = self.get_prompter(
            is_visual,
            main_prompt,
            example_prompt,
        )

    def get_prompter(
        self,
        is_visual,
        prompt_template: str,
        example_prompt_template: str,
    ) -> EvaluationAgentPrompter:
        """
        Get the prompter for the agent.
        """

        return EvaluationAgentPrompter(
            is_visual=is_visual,
            prompt_template=prompt_template,
            example_prompt_template=example_prompt_template,
        )

    def message_constructor(
        self, log_path: str, request: str, eva_all_screenshots: bool = True
    ) -> Dict[str, Any]:
        """
        Construct the message.
        :param log_path: The path to the log file.
        :param request: The request.
        :param eva_all_screenshots: The flag indicating whether to evaluate all screenshots.
        :param context: The context.
        :return: The message.
        """

        evaagent_prompt_system_message = self.prompter.system_prompt_construction()

        evaagent_prompt_user_message = self.prompter.user_content_construction(
            log_path=log_path, request=request, eva_all_screenshots=eva_all_screenshots
        )

        evaagent_prompt_message = self.prompter.prompt_construction(
            evaagent_prompt_system_message, evaagent_prompt_user_message
        )

        return evaagent_prompt_message

    @property
    def status_manager(self) -> EvaluatonAgentStatus:
        """
        Get the status manager.
        """

        return EvaluatonAgentStatus

    def context_provision(self, context: Context) -> None:

        self.logger.info("Loading MCP tool information...")

        tool_info_dict = context.get(ContextNames.TOOL_INFO)

        for agent_name in tool_info_dict:
            tool_list: List[MCPToolInfo] = tool_info_dict[agent_name]

            tool_name_list = [tool.tool_name for tool in tool_list] if tool_list else []

            self.logger.info(
                f"Loaded tool list: {tool_name_list} for the agent {agent_name}."
            )

        self.prompter.create_api_prompt_template(tool_info_dict)

    def evaluate(
        self,
        request: str,
        log_path: str,
        eva_all_screenshots: bool = True,
        context: Optional[Context] = None,
    ) -> Tuple[Dict[str, str], float]:
        """
        Evaluate the task completion.
        :param log_path: The path to the log file.
        :return: The evaluation result and the cost of LLM.
        """

        self.context_provision(context)

        message = self.message_constructor(
            log_path=log_path, request=request, eva_all_screenshots=eva_all_screenshots
        )
        result, cost = self.get_response(
            message=message, namescope="EVALUATION_AGENT", use_backup_engine=True
        )

        result = json_parser(result)

        return result, cost

    def process_confirmation(self) -> None:
        """
        Comfirmation, currently do nothing.
        """
        pass

    def print_response(self, response_dict: Dict[str, str]) -> None:
        """
        Pretty-print the evaluation response using Rich.
        :param response_dict: The response dictionary.
        """
        emoji_map = {
            "yes": "✅",
            "no": "❌",
            "maybe": "❓",
        }

        complete = emoji_map.get(
            response_dict.get("complete"), response_dict.get("complete")
        )
        sub_scores = response_dict.get("sub_scores", [])
        reason = response_dict.get("reason", "")

        # Evaluation result title
        console.print(
            Panel(
                "",
                title="[bold magenta]Evaluation result🧐[/bold magenta]",
                expand=False,
            )
        )

        # Sub-scores table
        if sub_scores:
            table = Table(
                title="[bold green]Sub-scores📊[/bold green]", show_lines=True
            )
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Evaluation", style="green")
            for sub_score in sub_scores:
                score = sub_score.get("name")
                evaluation = sub_score.get("evaluation")
                table.add_row(str(score), str(emoji_map.get(evaluation, evaluation)))
            console.print(table)

        # Task complete
        console.print(
            Panel(
                f"{complete}",
                title="[bold cyan]Task is complete💯[/bold cyan]",
                expand=False,
                style="cyan",
            )
        )

        # Reason
        if reason:
            console.print(
                Panel(
                    reason,
                    title="[bold blue]Reason🤔[/bold blue]",
                    expand=False,
                    style="blue",
                )
            )


# The following code is used for testing the agent.
if __name__ == "__main__":

    eva_agent = EvaluationAgent(
        name="eva_agent",
        is_visual=True,
        main_prompt=configs["EVALUATION_PROMPT"],
        example_prompt="",
    )

    request = "Can you open paint and draw a circle of radius 200px?"
    log_path = "./logs/test_paint5"
    results = eva_agent.evaluate(
        request=request, log_path=log_path, eva_all_screenshots=True
    )

    print(results)
