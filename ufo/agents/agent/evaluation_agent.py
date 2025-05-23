# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import Any, Dict, Optional, Tuple

from ufo.agents.agent.basic import BasicAgent
from ufo.agents.states.evaluaton_agent_state import EvaluatonAgentStatus
from ufo.config.config import Config
from ufo.prompter.eva_prompter import EvaluationAgentPrompter
from ufo.utils import json_parser, print_with_color


configs = Config.get_instance().config_data


class EvaluationAgent(BasicAgent):
    """
    The agent for evaluation.
    """

    def __init__(
        self,
        name: str,
        app_root_name: str,
        is_visual: bool,
        main_prompt: str,
        example_prompt: str,
        api_prompt: str,
    ):
        """
        Initialize the FollowAgent.
        :agent_type: The type of the agent.
        :is_visual: The flag indicating whether the agent is visual or not.
        """

        super().__init__(name=name)

        self._app_root_name = app_root_name
        self.prompter = self.get_prompter(
            is_visual,
            main_prompt,
            example_prompt,
            api_prompt,
            app_root_name,
        )

    def get_prompter(
        self,
        is_visual,
        prompt_template: str,
        example_prompt_template: str,
        api_prompt_template: str,
        root_name: Optional[str] = None,
    ) -> EvaluationAgentPrompter:
        """
        Get the prompter for the agent.
        """

        return EvaluationAgentPrompter(
            is_visual=is_visual,
            prompt_template=prompt_template,
            example_prompt_template=example_prompt_template,
            api_prompt_template=api_prompt_template,
            root_name=root_name,
        )

    def message_constructor(
        self, log_path: str, request: str, eva_all_screenshots: bool = True
    ) -> Dict[str, Any]:
        """
        Construct the message.
        :param log_path: The path to the log file.
        :param request: The request.
        :param eva_all_screenshots: The flag indicating whether to evaluate all screenshots.
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

    def evaluate(
        self, request: str, log_path: str, eva_all_screenshots: bool = True
    ) -> Tuple[Dict[str, str], float]:
        """
        Evaluate the task completion.
        :param log_path: The path to the log file.
        :return: The evaluation result and the cost of LLM.
        """

        message = self.message_constructor(
            log_path=log_path, request=request, eva_all_screenshots=eva_all_screenshots
        )
        result, cost = self.get_response(
            message=message, namescope="eva", use_backup_engine=True
        )

        result = json_parser(result)

        return result, cost

    def process_comfirmation(self) -> None:
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

        for score, evaluation in sub_scores.items():
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
        app_root_name="WINWORD.EXE",
        is_visual=True,
        main_prompt=configs["EVALUATION_PROMPT"],
        example_prompt="",
        api_prompt=configs["API_PROMPT"],
    )

    request = "Can you open paint and draw a circle of radius 200px?"
    log_path = "./logs/test_paint5"
    results = eva_agent.evaluate(
        request=request, log_path=log_path, eva_all_screenshots=True
    )

    print(results)
