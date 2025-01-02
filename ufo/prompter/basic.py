# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from abc import ABC, abstractmethod
from typing import Dict, List

import yaml

from ufo.utils import print_with_color


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
                print_with_color(f"Error loading prompt template: {exc}", "yellow")
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
    def retrived_documents_prompt_helper(
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
