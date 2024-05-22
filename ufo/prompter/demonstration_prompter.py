# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from typing import Dict, List

from record_processor.parser.demonstration_record import DemonstrationRecord
from ufo.prompter.basic import BasicPrompter


class DemonstrationPrompter(BasicPrompter):
    """
    The DemonstrationPrompter class is the prompter for the user demonstration learning.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
        api_prompt_template: str,
    ):
        """
        Initialize the DemonstrationPrompter.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        :param api_prompt_template: The path of the api prompt template.
        """
        super().__init__(is_visual, prompt_template, example_prompt_template)
        self.api_prompt_template = self.load_prompt_template(api_prompt_template)

    def system_prompt_construction(self) -> str:
        """
        Construct the system prompt.
        return: The system prompt.
        """
        apis = self.api_prompt_helper(verbose=1)
        examples = self.examples_prompt_helper()

        system_key = "system" if self.is_visual else "system_nonvisual"

        return self.prompt_template[system_key].format(apis=apis, examples=examples)

    def user_prompt_construction(self, user_request: str) -> str:
        """
        Construct the user prompt.
        :param user_request: The user request.
        return: The user prompt.
        """
        prompt = self.prompt_template["user"].format(user_request=user_request)

        return prompt

    def user_content_construction(
        self, demo_record: DemonstrationRecord
    ) -> List[Dict[str, str]]:
        """
        Construct the prompt for the user demonstration record with following contents:
        1. Initial Application Screenshot if it is visual mode
        2. Agent Trajectory.
        3. User Request.
        :param demo_record: The demonstration record.
        return: The prompt for the user demonstration record.
        """

        user_content = []

        # Add the initial application screenshot if it is visual mode.
        if self.is_visual:
            user_content.append(
                {"type": "text", "text": "[Initial Application Screenshot]:"}
            )
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": demo_record.__getattribute__("step_0")["screenshot"]
                    },
                }
            )

        # Get the total steps of the demonstration record. And construct the agent trajectory.
        step_num = demo_record.get_step_num()

        user_content.append({"type": "text", "text": "[Agent Trajectory]:"})

        for num in range(step_num):
            step = demo_record.__getattribute__("step_{num}".format(num=num))
            step_content = {
                "application": step["application"],
                "description": step["description"],
                "action": step["action"],
            }
            if step["comment"]:
                step_content["comment"] = step["comment"]

            user_content.append({"type": "text", "text": json.dumps(step_content)})

        # Add the user request.
        user_content.append(
            {
                "type": "text",
                "text": self.user_prompt_construction(demo_record.get_request()),
            }
        )

        return user_content

    def api_prompt_helper(self, verbose: int = 1) -> str:
        """
        Construct the prompt for APIs.
        :param verbose: The verbosity level.
        return: The prompt for APIs.
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

    def examples_prompt_helper(
        self, header: str = "## Summarization Examples", separator: str = "Example"
    ) -> str:
        """
        Construct the prompt for examples.
        :param examples: The examples.
        :param header: The header of the prompt.
        :param separator: The separator of the prompt.
        return: The prompt for examples.
        """

        template = """
        [User Request]:
            {request}
        [Response]:
            {response}
        """
        example_list = []

        for key in self.example_prompt_template.keys():
            if key.startswith("example"):
                response = self.example_prompt_template[key].get("Response")
                response["Tips"] = self.example_prompt_template[key].get("Tips")
                example = template.format(
                    request=self.example_prompt_template[key].get("Request"),
                    response=response,
                )
                example_list.append(example)

        return self.retrived_documents_prompt_helper(header, separator, example_list)
