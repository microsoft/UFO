# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Optional

from dataflow.prompter.execution.execute_eval_prompter import ExecuteEvalAgentPrompter
from ufo.agents.agent.evaluation_agent import EvaluationAgent

class ExecuteEvalAgent(EvaluationAgent):
    """
    The Agent for task execution evaluation.
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
        Initialize the ExecuteEvalAgent.
        :param name: The name of the agent.
        :param app_root_name: The name of the app root.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt.
        :param example_prompt: The example prompt.
        :param api_prompt: The API prompt.
        """

        super().__init__(
            name=name,
            app_root_name=app_root_name,
            is_visual=is_visual,
            main_prompt=main_prompt,
            example_prompt=example_prompt,
            api_prompt=api_prompt,
        )

    def get_prompter(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
        api_prompt_template: str,
        root_name: Optional[str] = None,
    ) -> ExecuteEvalAgentPrompter:
        """
        Get the prompter for the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param prompt_template: The prompt template.
        :param example_prompt_template: The example prompt template.
        :param api_prompt_template: The API prompt template.
        :param root_name: The name of the root.
        :return: The prompter.
        """

        return ExecuteEvalAgentPrompter(
            is_visual=is_visual,
            prompt_template=prompt_template,
            example_prompt_template=example_prompt_template,
            api_prompt_template=api_prompt_template,
            root_name=root_name,
        )