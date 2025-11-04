# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from typing import Any, Dict, List, Optional

from config.config_loader import get_ufo_config
from aip.messages import MCPToolInfo
from ufo.prompter.basic import BasicPrompter


class HostAgentPrompter(BasicPrompter):
    """
    The HostAgentPrompter class is the prompter for the host agent.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
        api_prompt_template: str,
    ):
        """
        Initialize the ApplicationAgentPrompter.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        :param api_prompt_template: The path of the api prompt template.
        """
        super().__init__(is_visual, prompt_template, example_prompt_template)
        self.api_prompt_template = self.load_prompt_template(api_prompt_template)

    def create_api_prompt_template(self, tools: List[MCPToolInfo]):
        """
        Create the API prompt template.
        :param tools: The list of tools.
        """
        self.api_prompt_template = BasicPrompter.tools_to_llm_prompt(tools)

    def system_prompt_construction(self) -> str:
        """
        Construct the prompt for app selection.
        return: The prompt for app selection.
        """
        apis = self.api_prompt_helper(verbose=0)
        examples = self.examples_prompt_helper()

        third_party_instructions = self.third_party_agent_instruction()

        system_key = "system" if self.is_visual else "system_nonvisual"

        return self.prompt_template[system_key].format(
            apis=apis,
            examples=examples,
            third_party_instructions=third_party_instructions,
        )

    def user_prompt_construction(
        self,
        control_item: List[str],
        prev_subtask: List[Dict[str, str]],
        prev_plan: List[str],
        user_request: str,
        retrieved_docs: str = "",
    ) -> str:
        """
        Construct the prompt for action selection.
        :param control_item: The control item.
        :param prev_plan: The previous plan.
        :param prev_subtask: The previous subtask.
        :param user_request: The user request.
        :param retrieved_docs: The retrieved documents.
        return: The prompt for action selection.
        """
        prompt = self.prompt_template["user"].format(
            control_item=json.dumps(control_item),
            prev_plan=json.dumps(prev_plan),
            prev_subtask=json.dumps(prev_subtask),
            user_request=user_request,
            retrieved_docs=retrieved_docs,
        )

        return prompt

    def third_party_agent_instruction(
        self,
    ) -> str:
        """
        Construct the prompt for third party agent instruction.
        :return: The prompt for third party agent instruction.
        """
        ufo_config = get_ufo_config()
        enabled_third_party_agents = ufo_config.system.enabled_third_party_agents
        third_party_agents_configs = ufo_config.system.third_party_agent_config

        instructions = []
        for agent_name in enabled_third_party_agents:
            agent_config = third_party_agents_configs.get(agent_name, {})
            instruction = agent_config.get("INTRODUCTION", "")
            instructions.append(f"{agent_name}: {instruction}")

        return "\n".join(instructions)

    def user_content_construction(
        self,
        image_list: List[str],
        control_item: List[str],
        prev_subtask: List[Dict[str, str]],
        prev_plan: str,
        user_request: str,
        retrieved_docs: str = "",
    ) -> List[Dict[str, str]]:
        """
        Construct the prompt for LLMs.
        :param image_list: The list of images.
        :param control_item: The control item.
        :param prev_subtask: The previous subtask.
        :param prev_plan: The previous plan.
        :param user_request: The user request.
        :param retrieved_docs: The retrieved documents.
        return: The prompt for LLMs.
        """

        user_content = []

        if self.is_visual:
            screenshot_text = ["Current Screenshots:"]

            for i, image in enumerate(image_list):
                user_content.append({"type": "text", "text": screenshot_text[i]})
                user_content.append({"type": "image_url", "image_url": {"url": image}})

        user_content.append(
            {
                "type": "text",
                "text": self.user_prompt_construction(
                    control_item=control_item,
                    prev_subtask=prev_subtask,
                    prev_plan=prev_plan,
                    user_request=user_request,
                    retrieved_docs=retrieved_docs,
                ),
            }
        )

        return user_content

    def examples_prompt_helper(
        self, header: str = "## Response Examples", separator: str = "Example"
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
            {response}"""
        example_list = []

        for key, values in self.example_prompt_template.items():

            if key.startswith("example"):
                example = template.format(
                    request=values.get("Request"),
                    response=json.dumps(values.get("Response")),
                )
                example_list.append(example)

        return self.retrieved_documents_prompt_helper(header, separator, example_list)

    def api_prompt_helper(self, verbose: int = 1) -> str:
        """
        Construct the prompt for APIs.
        :param apis: The APIs.
        :param verbose: The verbosity level.
        return: The prompt for APIs.
        """
        if self.api_prompt_template is None:
            raise ValueError(
                "API prompt template is not set. Call create_api_prompt_template first."
            )
        return self.api_prompt_template


class AppAgentPrompter(BasicPrompter):
    """
    The AppAgentPrompter class is the prompter for the application agent.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
    ):
        """
        Initialize the ApplicationAgentPrompter.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        :param api_prompt_template: The path of the api prompt template.
        :param root_name: The root name of the app.
        """
        super().__init__(is_visual, prompt_template, example_prompt_template)
        self.api_prompt_template = None

    def create_api_prompt_template(self, tools: List[MCPToolInfo]):
        """
        Create the API prompt template.
        :param tools: The list of tools.
        """
        self.api_prompt_template = BasicPrompter.tools_to_llm_prompt(tools)

    def system_prompt_construction(self, additional_examples: List[str] = []) -> str:
        """
        Construct the prompt for app selection.
        :param additional_examples: The additional examples added to the prompt.
        return: The prompt for app selection.
        """

        apis = self.api_prompt_helper(verbose=1)
        examples = self.examples_prompt_helper(additional_examples=additional_examples)

        ufo_config = get_ufo_config()
        if ufo_config.system.action_sequence:
            system_key = "system_as"
        else:
            system_key = "system"
        if not self.is_visual:
            system_key += "_nonvisual"

        return self.prompt_template[system_key].format(apis=apis, examples=examples)

    def user_prompt_construction(
        self,
        control_item: List[str],
        prev_subtask: List[Dict[str, str]],
        prev_plan: List[str],
        user_request: str,
        subtask: str,
        current_application: str,
        host_message: List[str],
        retrieved_docs: str = "",
        last_success_actions: List[Dict[str, Any]] = [],
    ) -> str:
        """
        Construct the prompt for action selection.
        :param prompt_template: The template of the prompt.
        :param control_item: The control item.
        :param prev_subtask: The previous subtask.
        :param prev_plan: The previous plan.
        :param user_request: The user request.
        :param subtask: The subtask.
        :param current_application: The current application.
        :param host_message: The host message.
        :param retrieved_docs: The retrieved documents.
        :param last_success_actions: The list of successful actions in the last step.
        return: The prompt for action selection.
        """
        prompt = self.prompt_template["user"].format(
            control_item=json.dumps(control_item),
            prev_subtask=json.dumps(prev_subtask),
            prev_plan=json.dumps(prev_plan),
            user_request=user_request,
            subtask=subtask,
            current_application=current_application,
            host_message=json.dumps(host_message),
            retrieved_docs=retrieved_docs,
            last_success_actions=json.dumps(last_success_actions),
        )

        return prompt

    def user_content_construction(
        self,
        image_list: List[str],
        control_item: List[str],
        prev_subtask: List[str],
        prev_plan: List[str],
        user_request: str,
        subtask: str,
        current_application: str,
        host_message: List[str],
        retrieved_docs: str = "",
        last_success_actions: List[Dict[str, Any]] = [],
        include_last_screenshot: bool = True,
    ) -> List[Dict[str, str]]:
        """
        Construct the prompt for LLMs.
        :param image_list: The list of images.
        :param control_item: The control item.
        :param prev_subtask: The previous subtask.
        :param prev_plan: The previous plan.
        :param user_request: The user request.
        :param subtask: The subtask.
        :param current_application: The current application.
        :param host_message: The host message.
        :param retrieved_docs: The retrieved documents.
        return: The prompt for LLMs.
        """

        user_content = []

        if self.is_visual:

            screenshot_text = []
            if include_last_screenshot:
                screenshot_text += ["Screenshot for the last step:"]

            screenshot_text += ["Current Screenshots:", "Annotated Screenshot:"]

            for i, image in enumerate(image_list):
                user_content.append({"type": "text", "text": screenshot_text[i]})
                user_content.append({"type": "image_url", "image_url": {"url": image}})

        user_content.append(
            {
                "type": "text",
                "text": self.user_prompt_construction(
                    control_item=control_item,
                    prev_subtask=prev_subtask,
                    prev_plan=prev_plan,
                    user_request=user_request,
                    subtask=subtask,
                    current_application=current_application,
                    host_message=host_message,
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
        :param examples: The examples.
        :param header: The header of the prompt.
        :param separator: The separator of the prompt.
        :param additional_examples: The additional examples added to the prompt.
        return: The prompt for examples.
        """

        template = """
        [User Request]:
            {request}
        [Sub-Task]:
            {subtask}
        [Tips]:
            {tips}
        [Response]:
            {response}"""

        ufo_config = get_ufo_config()
        if ufo_config.system.action_sequence:
            for example in additional_examples:
                example["Response"] = self.action2action_sequence(
                    example.get("Response", {})
                )

        example_dict = [
            self.example_prompt_template[key]
            for key in self.example_prompt_template.keys()
            if key.startswith("example")
        ] + additional_examples

        example_list = []

        for example in example_dict:
            example_str = template.format(
                request=example.get("Request"),
                subtask=example.get("Sub-task"),
                tips=example.get("Tips"),
                response=json.dumps(example.get("Response")),
            )
            example_list.append(example_str)

        return self.retrieved_documents_prompt_helper(header, separator, example_list)

    @staticmethod
    def action2action_sequence(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete the key in the example["Response"], and replaced it with the key "ActionList".
        :param example: The action.
        return: The action sequence.
        """
        action_list = [
            {
                "function": response.get("function", ""),
                "arguments": response.get("arguments", {}),
                "status": response.get("status", "CONTINUE"),
            }
        ]

        # Delete the keys in the response
        from copy import deepcopy

        response_copy = deepcopy(response)
        for key in ["function", "arguments", "status"]:
            response_copy.pop(key, None)
        response_copy["action"] = action_list

        return response_copy

    def api_prompt_helper(self, verbose: int = 1) -> str:
        """
        Construct the prompt for APIs.
        :param apis: The APIs.
        :param verbose: The verbosity level.
        return: The prompt for APIs.
        """
        if self.api_prompt_template is None:
            raise ValueError(
                "API prompt template is not set. Call create_api_prompt_template first."
            )
        return self.api_prompt_template
