# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from typing import Dict, List

from ufo.prompter.basic import BasicPrompter


class FilterPrompter(BasicPrompter):
    """
    Load the prompt for the FilterAgent.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
        api_prompt_template: str,
    ):
        """
        Initialize the FilterPrompter.
        :param is_visual: The flag indicating whether the prompter is visual or not.
        :param prompt_template: The prompt template.
        :param example_prompt_template: The example prompt template.
        :param api_prompt_template: The API prompt template.
        """

        super().__init__(is_visual, prompt_template, example_prompt_template)
        self.api_prompt_template = self.load_prompt_template(
            api_prompt_template, is_visual
        )

    def api_prompt_helper(self, apis: Dict = {}, verbose: int = 1) -> str:
        """
        Construct the prompt for APIs.
        :param apis: The APIs.
        :param verbose: The verbosity level.
        :return: The prompt for APIs.
        """

        # Construct the prompt for APIs
        if len(apis) == 0:
            api_list = [
                "- The action type are limited to {actions}.".format(
                    actions=list(self.api_prompt_template.keys())
                )
            ]

            # Construct the prompt for each API
            for key in self.api_prompt_template.keys():
                api = self.api_prompt_template[key]
                if verbose > 0:
                    api_text = "{summary}\n{usage}".format(
                        summary=api["summary"], usage=api["usage"]
                    )
                else:
                    api_text = api["summary"]

                api_list.append(api_text)

            api_prompt = self.retrived_documents_prompt_helper("", "", api_list)
        else:
            api_list = [
                "- The action type are limited to {actions}.".format(
                    actions=list(apis.keys())
                )
            ]

            # Construct the prompt for each API
            for key in apis.keys():
                api = apis[key]
                api_text = "{description}\n{example}".format(
                    description=api["description"], example=api["example"]
                )
                api_list.append(api_text)

            api_prompt = self.retrived_documents_prompt_helper("", "", api_list)

        return api_prompt

    def system_prompt_construction(self, app: str = "") -> str:
        """
        Construct the prompt for the system.
        :param app: The app name.
        :return: The prompt for the system.
        """

        try:
            ans = self.prompt_template["system"]
            ans = ans.format(app=app)
            return ans
        except Exception as e:
            print(e)

    def user_prompt_construction(self, request: str) -> str:
        """
        Construct the prompt for the user.
        :param request: The user request.
        :return: The prompt for the user.
        """
        prompt = self.prompt_template["user"].format(request=request)
        return prompt

    def user_content_construction(self, request: str) -> List[Dict]:
        """
        Construct the prompt for LLMs.
        :param request: The user request.
        :return: The prompt for LLMs.
        """

        user_content = []

        user_content.append(
            {"type": "text", "text": self.user_prompt_construction(request)}
        )

        return user_content

    def examples_prompt_helper(
        self,
        header: str = "## Response Examples",
        separator: str = "Example",
        additional_examples: List[str] = [],
    ) -> str:
        """
        Construct the prompt for examples.
        :param header: The header of the prompt.
        :param separator: The separator of the prompt.
        :param additional_examples: The additional examples.
        :return: The prompt for examples.
        """

        template = """
        [User Request]:
            {request}
        [Response]:
            {response}
        [Tip]
            {tip}
        """

        example_list = []

        for key in self.example_prompt_template.keys():
            if key.startswith("example"):
                example = template.format(
                    request=self.example_prompt_template[key].get("Request"),
                    response=json.dumps(
                        self.example_prompt_template[key].get("Response")
                    ),
                    tip=self.example_prompt_template[key].get("Tips", ""),
                )
                example_list.append(example)

        example_list += [json.dumps(example) for example in additional_examples]

        return self.retrived_documents_prompt_helper(header, separator, example_list)


class PrefillPrompter(BasicPrompter):
    """
    Load the prompt for the PrefillAgent.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
        api_prompt_template: str,
    ):
        """
        Initialize the PrefillPrompter.
        :param is_visual: The flag indicating whether the prompter is visual or not.
        :param prompt_template: The prompt template.
        :param example_prompt_template: The example prompt template.
        :param api_prompt_template: The API prompt template.
        """

        super().__init__(is_visual, prompt_template, example_prompt_template)
        self.api_prompt_template = self.load_prompt_template(
            api_prompt_template, is_visual
        )

    def api_prompt_helper(self, verbose: int = 1) -> str:
        """
        Construct the prompt for APIs.
        :param verbose: The verbosity level.
        :return: The prompt for APIs.
        """

        # Construct the prompt for APIs
        api_list = [
            "- The action type are limited to {actions}.".format(
                actions=list(self.api_prompt_template.keys())
            )
        ]

        # Construct the prompt for each API
        for key in self.api_prompt_template.keys():
            api = self.api_prompt_template[key]
            if verbose > 0:
                api_text = "{summary}\n{usage}".format(
                    summary=api["summary"], usage=api["usage"]
                )
            else:
                api_text = api["summary"]

            api_list.append(api_text)

        api_prompt = self.retrived_documents_prompt_helper("", "", api_list)

        return api_prompt

    def system_prompt_construction(self, additional_examples: List = []) -> str:
        """
        Construct the prompt for the system.
        :param additional_examples: The additional examples.
        :return: The prompt for the system.
        """

        examples = self.examples_prompt_helper(additional_examples=additional_examples)
        apis = self.api_prompt_helper(verbose=0)
        return self.prompt_template["system"].format(apis=apis, examples=examples)

    def user_prompt_construction(
        self, given_task: str, reference_steps: List, doc_control_state: Dict
    ) -> str:
        """
        Construct the prompt for the user.
        :param given_task: The given task.
        :param reference_steps: The reference steps.
        :param doc_control_state: The document control state.
        :return: The prompt for the user.
        """

        prompt = self.prompt_template["user"].format(
            given_task=given_task,
            reference_steps=json.dumps(reference_steps),
            doc_control_state=json.dumps(doc_control_state),
        )

        return prompt

    def load_screenshots(self, log_path: str) -> str:
        """
        Load the first and last screenshots from the log path.
        :param log_path: The path of the log.
        :return: The screenshot URL.
        """
        from ufo.prompter.eva_prompter import EvaluationAgentPrompter

        init_image = os.path.join(log_path, "screenshot.png")
        init_image_url = EvaluationAgentPrompter.load_single_screenshot(init_image)
        return init_image_url

    def user_content_construction(
        self,
        given_task: str,
        reference_steps: List,
        doc_control_state: Dict,
        log_path: str,
    ) -> List[Dict]:
        """
        Construct the prompt for LLMs.
        :param given_task: The given task.
        :param reference_steps: The reference steps.
        :param doc_control_state: The document control state.
        :param log_path: The path of the log.
        :return: The prompt for LLMs.
        """

        user_content = []
        if self.is_visual:
            screenshot = self.load_screenshots(log_path)
            screenshot_text = """You are a action prefill agent, responsible to prefill the given task.
                                This is the screenshot of the current environment, please check it and give prefilled task accodingly."""

            user_content.append({"type": "text", "text": screenshot_text})
            user_content.append({"type": "image_url", "image_url": {"url": screenshot}})

        user_content.append(
            {
                "type": "text",
                "text": self.user_prompt_construction(
                    given_task, reference_steps, doc_control_state
                ),
            }
        )

        return user_content

    def examples_prompt_helper(
        self,
        header: str = "## Response Examples",
        separator: str = "Example",
        additional_examples: List[str] = [],
    ) -> str:
        """
        Construct the prompt for examples.
        :param header: The header of the prompt.
        :param separator: The separator of the prompt.
        :param additional_examples: The additional examples.
        :return: The prompt for examples.
        """

        template = """
        [User Request]:
            {request}
        [Response]:
            {response}
        [Tip]
            {tip}
        """

        example_list = []

        for key in self.example_prompt_template.keys():
            if key.startswith("example"):
                example = template.format(
                    request=self.example_prompt_template[key].get("Request"),
                    response=json.dumps(
                        self.example_prompt_template[key].get("Response")
                    ),
                    tip=self.example_prompt_template[key].get("Tips", ""),
                )
                example_list.append(example)

        example_list += [json.dumps(example) for example in additional_examples]

        return self.retrived_documents_prompt_helper(header, separator, example_list)


class ExecutePrompter(BasicPrompter):
    """
    Load the prompt for the ExecuteAgent.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
        api_prompt_template: str,
    ):
        """
        Initialize the ExecutePrompter.
        :param is_visual: The flag indicating whether the prompter is visual or not.
        :param prompt_template: The prompt template.
        :param example_prompt_template: The example prompt template.
        :param api_prompt_template: The API prompt template.
        """

        super().__init__(is_visual, prompt_template, example_prompt_template)
        self.api_prompt_template = self.load_prompt_template(
            api_prompt_template, is_visual
        )

    def load_screenshots(self, log_path: str) -> str:
        """
        Load the first and last screenshots from the log path.
        :param log_path: The path of the log.
        :return: The screenshot URL.
        """
        from ufo.prompter.eva_prompter import EvaluationAgentPrompter

        init_image = os.path.join(log_path, "screenshot.png")
        init_image_url = EvaluationAgentPrompter.load_single_screenshot(init_image)
        return init_image_url
