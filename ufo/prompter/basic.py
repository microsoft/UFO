# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import yaml

from aip.messages import MCPToolInfo

logger = logging.getLogger(__name__)


class BasicPrompter(ABC):
    """
    The BasicPrompter class is the abstract class for the prompter.
    """

    def __init__(
        self, is_visual: bool, prompt_template: str, example_prompt_template: str
    ):
        """
        Initialize the BasicPrompter.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        """
        self.is_visual = is_visual
        if prompt_template:
            self.prompt_template = self.load_prompt_template(prompt_template, is_visual)
        else:
            self.prompt_template = ""
        if example_prompt_template:
            self.example_prompt_template = self.load_prompt_template(
                example_prompt_template, is_visual
            )
        else:
            self.example_prompt_template = ""

        self.logger = logging.getLogger(__name__)

    @staticmethod
    def load_prompt_template(template_path: str, is_visual=None) -> Dict[str, str]:
        """
        Load the prompt template.
        :return: The prompt template.
        """

        if is_visual == None:
            path = template_path
        else:
            path = template_path.format(
                mode="visual" if is_visual == True else "nonvisual"
            )

        if not path:
            return {}

        if os.path.exists(path):
            try:
                prompt = yaml.safe_load(open(path, "r", encoding="utf-8"))
            except yaml.YAMLError as exc:
                logger.warning(f"Error loading prompt template: {exc}")
        else:
            raise FileNotFoundError(f"Prompt template not found at {path}")

        return prompt

    @staticmethod
    def prompt_construction(
        system_prompt: str, user_content: List[Dict[str, str]]
    ) -> List:
        """
        Construct the prompt for summarizing the experience into an example.
        :param user_content: The user content.
        return: The prompt for summarizing the experience into an example.
        """

        system_message = {"role": "system", "content": system_prompt}

        user_message = {"role": "user", "content": user_content}

        prompt_message = [system_message, user_message]

        return prompt_message

    @staticmethod
    def retrieved_documents_prompt_helper(
        header: str, separator: str, documents: List[str]
    ) -> str:
        """
        Construct the prompt for retrieved documents.
        :param header: The header of the prompt.
        :param separator: The separator of the prompt.
        :param documents: The retrieved documents.
        return: The prompt for retrieved documents.
        """

        if header:
            prompt = "\n<{header}:>\n".format(header=header)
        else:
            prompt = ""
        for i, document in enumerate(documents):
            if separator:
                prompt += "[{separator} {i}:]".format(separator=separator, i=i + 1)
                prompt += "\n"
            prompt += document
            prompt += "\n\n"
        return prompt

    @staticmethod
    def tool_to_llm_prompt(
        tool_info: MCPToolInfo, generate_example: bool = True
    ) -> str:
        """
        Convert tool information to a formatted string for LLM.
        :param tool_info: The tool information dictionary.
        :param generate_example: Whether to generate example usage.
        :return: A formatted string representing the tool information.
        """
        name = tool_info.tool_name
        desc = (tool_info.description or "").strip()
        in_props = (tool_info.input_schema or {}).get("properties", {})
        params = "\n".join(
            f"- {k} ({v.get('type', 'unknown')}, "
            f"{'optional' if 'default' in v else 'required'}): "
            f"{v.get('description', '')} "
            f"Default: {v.get('default', 'N/A')}"
            for k, v in in_props.items()
        )
        output_desc = (tool_info.output_schema or {}).get("description", "")
        example_args = ", ".join(
            f"{k}={repr(v.get('default', ''))}" for k, v in in_props.items()
        )

        formated_string = f"""\
        Tool name: {name}
        Description: {desc}

        Parameters:
        {params}

        Returns: {output_desc}
        """

        if generate_example:
            formated_string += f"""
        Example usage:
        {name}({example_args})
        """

        return formated_string

    @staticmethod
    def tools_to_llm_prompt(
        tools: List[MCPToolInfo], generate_example: bool = True
    ) -> str:
        """
        Convert a list of tool information to a formatted string for LLM.
        :param tools: A list of tool information dictionaries.
        :param generate_example: Whether to generate example usage for each tool.
        :return: A formatted string representing all tools.
        """
        return "\n\n---\n\n".join(
            BasicPrompter.tool_to_llm_prompt(tool, generate_example=generate_example)
            for tool in tools
        )

    @abstractmethod
    def system_prompt_construction(self) -> str:
        """
        Construct the system prompt for LLM.
        """

        pass

    @abstractmethod
    def user_prompt_construction(self) -> str:
        """
        Construct the textual user prompt for LLM based on the `user` field in the prompt template.
        """

        pass

    @abstractmethod
    def user_content_construction(self) -> str:
        """
        Construct the full user content for LLM, including the user prompt and images.
        """

        pass

    def examples_prompt_helper(self) -> str:
        """
        A helper function to construct the examples prompt for in-context learning.
        """

        pass

    def api_prompt_helper(self) -> str:
        """
        A helper function to construct the API list and descriptions for the prompt.
        """

        pass
