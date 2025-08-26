# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import Any, Dict, Optional, Tuple

from ufo.agents.agent.basic import BasicAgent
from ufo.agents.states.evaluaton_agent_state import EvaluatonAgentStatus
from ufo.config import Config
from ufo.prompter.eva_prompter import EvaluationAgentPrompter
from ufo.module.context import Context, ContextNames
from ufo.utils import json_parser, print_with_color


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
        self,
        log_path: str,
        request: str,
        eva_all_screenshots: bool = True,
        context: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """
        Construct the message.
        :param log_path: The path to the log file.
        :param request: The request.
        :param eva_all_screenshots: The flag indicating whether to evaluate all screenshots.
        :param context: The context.
        :return: The message.
        """

        evaagent_prompt_system_message = self.prompter.system_prompt_construction(
            context
        )

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

        message = self.message_constructor(
            log_path=log_path,
            request=request,
            eva_all_screenshots=eva_all_screenshots,
            context=context,
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

    def print_response(self, response_dict: Dict[str, Any]) -> None:
        """
        Print the response of the evaluation.
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

        sub_scores = response_dict.get("sub_scores", {})
        reason = response_dict.get("reason", "")

        print_with_color(f"Evaluation result🧐:", "magenta")
        print_with_color(f"[Sub-scores📊:]", "green")

        for sub_score in sub_scores:
            score = sub_score.get("name")
            evaluation = sub_score.get("evaluation")
            print_with_color(
                f"{score}: {emoji_map.get(evaluation, evaluation)}", "green"
            )

        print_with_color(
            "[Task is complete💯:] {complete}".format(complete=complete), "cyan"
        )

        print_with_color(f"[Reason🤔:] {reason}".format(reason=reason), "blue")


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
