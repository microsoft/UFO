# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from typing import Any, Dict, List, Optional

from ufo.config import Config
from ufo.contracts.contracts import MCPToolInfo
from ufo.galaxy.agents.schema import WeavingMode
from ufo.galaxy.constellation.task_constellation import TaskConstellation
from ufo.prompter.basic import BasicPrompter

configs = Config.get_instance().config_data


class ConstellationAgentPrompter(BasicPrompter):
    """
    The ConstellationAgentPrompter class is the prompter for the constellation agent.
    """

    def __init__(
        self,
        creation_prompt_template: str,
        editing_prompt_template: str,
        creation_example_prompt_template: str,
        editing_example_prompt_template: str,
        weaving_mode: WeavingMode,
    ):
        """
        Initialize the ApplicationAgentPrompter.
        :param creation_prompt_template: The creation prompt template.
        :param editing_prompt_template: The editing prompt template.
        :param creation_example_prompt_template: The creation example prompt template.
        :param editing_example_prompt_template: The editing example prompt template.
        :param weaving_mode: The weaving mode.
        """

        self.creation_prompt_template = self.load_prompt_template(
            creation_prompt_template
        )
        self.editing_prompt_template = self.load_prompt_template(
            editing_prompt_template
        )
        self.creation_example_prompt_template = self.load_prompt_template(
            creation_example_prompt_template
        )
        self.editing_example_prompt_template = self.load_prompt_template(
            editing_example_prompt_template
        )
        self.weaving_mode = weaving_mode

    def create_api_prompt_template(self, tools: List[MCPToolInfo]):
        """
        Create the API prompt template.
        :param tools: The list of tools.
        """
        self.api_prompt_template = BasicPrompter.tools_to_llm_prompt(tools)

    def system_prompt_construction(self) -> str:
        """
        Construct the prompt for app selection.
        :param weaving_mode: The weaving mode.
        return: The prompt for app selection.
        """

        examples = self.examples_prompt_helper()

        if self.weaving_mode == WeavingMode.CREATION:
            return self.creation_prompt_template["system"].format(
                apis=self.api_prompt_template, examples=examples
            )
        else:
            return self.editing_prompt_template["system"].format(
                apis=self.api_prompt_template, examples=examples
            )

    def user_content_construction(
        self, device_info: Dict[str, str], constellation: TaskConstellation
    ) -> str:
        """
        Construct the prompt for action selection.
        :param device_info: The device information.
        :param constellation: The task constellation.
        return: The prompt for action selection.
        """

        constellation_representation = constellation.to_dict()

        if self.weaving_mode == WeavingMode.CREATION:
            prompt_template = self.creation_prompt_template["user"]
        else:
            prompt_template = self.editing_prompt_template["user"]

        prompt = prompt_template.format(
            device_info=json.dumps(device_info),
            constellation=json.dumps(constellation_representation),
        )

        return [{"type": "text", "text": prompt}]

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
