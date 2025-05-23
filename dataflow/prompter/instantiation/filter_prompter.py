# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
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
        [Tips]:
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
