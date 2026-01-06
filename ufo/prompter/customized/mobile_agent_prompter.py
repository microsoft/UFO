# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from typing import Any, Dict, List

from config.config_loader import get_ufo_config
from ufo.prompter.agent_prompter import AppAgentPrompter


class MobileAgentPrompter(AppAgentPrompter):
    """
    The MobileAgentPrompter class is the prompter for the Mobile Android agent.
    """

    def __init__(
        self,
        prompt_template: str,
        example_prompt_template: str,
    ):
        """
        Initialize the MobileAgentPrompter.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        """
        super().__init__(None, prompt_template, example_prompt_template)
        self.api_prompt_template = None

    def system_prompt_construction(self, additional_examples: List[str] = []) -> str:
        """
        Construct the system prompt for mobile agent.
        :param additional_examples: The additional examples added to the prompt.
        return: The system prompt for mobile agent.
        """

        apis = self.api_prompt_helper(verbose=1)
        examples = self.examples_prompt_helper(additional_examples=additional_examples)

        return self.prompt_template["system"].format(apis=apis, examples=examples)

    def user_prompt_construction(
        self,
        prev_plan: List[str],
        user_request: str,
        installed_apps: List[Dict[str, Any]],
        current_controls: List[Dict[str, Any]],
        retrieved_docs: str = "",
        last_success_actions: List[Dict[str, Any]] = [],
    ) -> str:
        """
        Construct the user prompt for action selection.
        :param prev_plan: The previous plan.
        :param user_request: The user request.
        :param installed_apps: The list of installed apps on the device.
        :param current_controls: The list of current screen controls.
        :param retrieved_docs: The retrieved documents.
        :param last_success_actions: The list of successful actions in the last step.
        return: The prompt for action selection.
        """
        prompt = self.prompt_template["user"].format(
            prev_plan=json.dumps(prev_plan),
            user_request=user_request,
            installed_apps=json.dumps(installed_apps),
            current_controls=json.dumps(current_controls),
            retrieved_docs=retrieved_docs,
            last_success_actions=json.dumps(last_success_actions),
        )

        return prompt

    def user_content_construction(
        self,
        prev_plan: List[str],
        user_request: str,
        installed_apps: List[Dict[str, Any]],
        current_controls: List[Dict[str, Any]],
        screenshot_url: str = None,
        annotated_screenshot_url: str = None,
        retrieved_docs: str = "",
        last_success_actions: List[Dict[str, Any]] = [],
    ) -> List[Dict[str, str]]:
        """
        Construct the prompt content for LLMs with screenshots and control information.
        :param prev_plan: The previous plan.
        :param user_request: The user request.
        :param installed_apps: The list of installed apps on the device.
        :param current_controls: The list of current screen controls.
        :param screenshot_url: The clean screenshot URL (base64).
        :param annotated_screenshot_url: The annotated screenshot URL (base64).
        :param retrieved_docs: The retrieved documents.
        :param last_success_actions: The list of successful actions in the last step.
        return: The prompt content for LLMs.
        """

        user_content = []

        # Add screenshots if available
        if screenshot_url:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": screenshot_url},
                }
            )

        if annotated_screenshot_url:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": annotated_screenshot_url},
                }
            )

        # Add text prompt
        user_content.append(
            {
                "type": "text",
                "text": self.user_prompt_construction(
                    prev_plan=prev_plan,
                    user_request=user_request,
                    installed_apps=installed_apps,
                    current_controls=current_controls,
                    retrieved_docs=retrieved_docs,
                    last_success_actions=last_success_actions,
                ),
            }
        )

        return user_content

    def examples_prompt_helper(
        self,
        header: str = "## Response Examples",
        separator: str = "Example",
        additional_examples: List[Dict[str, Any]] = [],
    ) -> str:
        """
        Construct the prompt for examples.
        :param header: The header of the prompt.
        :param separator: The separator of the prompt.
        :param additional_examples: The additional examples added to the prompt.
        return: The prompt for examples.
        """

        template = """
        [User Request]:
            {request}
        [Response]:
            {response}"""

        example_dict = [
            self.example_prompt_template[key]
            for key in self.example_prompt_template.keys()
            if key.startswith("example")
        ] + additional_examples

        example_list = []

        for example in example_dict:
            example_str = template.format(
                request=example.get("Request"),
                response=json.dumps(example.get("Response")),
            )
            example_list.append(example_str)

        return self.retrieved_documents_prompt_helper(header, separator, example_list)

    def api_prompt_helper(self, verbose: int = 1) -> str:
        """
        Construct the prompt for APIs.
        :param verbose: The verbosity level.
        return: The prompt for APIs.
        """
        if self.api_prompt_template is None:
            raise ValueError(
                "API prompt template is not set. Call create_api_prompt_template first."
            )
        return self.api_prompt_template
