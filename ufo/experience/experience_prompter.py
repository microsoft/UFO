# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import List
import json
import yaml

VISUAL_PROMPT = "ufo/prompts/experience/visual_experience_prompt.yaml"
NON_VISUAL_PROMPT = "ufo/prompts/experience/nonvisual_experience_prompt.yaml"

VISUAL_EXAMPLE_PROMPT = "ufo/prompts/experience/visual_experience_example_prompt.yaml"
NON_VISUAL_EXAMPLE_PROMPT = "ufo/prompts/experience/nonvisual_experience_example_prompt.yaml"

EXAMPLE_SAVED_PATH = "ufo/experience/replay/"



class ExperiencePrompter:

    def __init__(self, is_visual: bool):
        """
        Initialize the ExperiencePrompter.
        :param is_visual: Whether the request is for visual model.
        """
        self.is_visual = is_visual
        self.prompt_template = self.load_prompt_template()
        self.example_prompt_template = self.load_example_prompt_template()

        self.system_prompt = self.system_prompt_construction()


    def load_prompt_template(self):
        """
        Load the prompt template.
        :return: The prompt template.
        """

        if self.is_visual:
            path = VISUAL_PROMPT
        else:
            path = NON_VISUAL_PROMPT

        prompt = yaml.safe_load(open(path, "r", encoding="utf-8"))

        return prompt
    

    def load_example_prompt_template(self):
        """
        Load the example prompt template.
        :return: The example prompt template.
        """
        if self.is_visual:
            path = VISUAL_EXAMPLE_PROMPT
        else:
            path = NON_VISUAL_EXAMPLE_PROMPT

        prompt = yaml.safe_load(open(path, "r", encoding="utf-8"))

        return prompt
    

    def system_prompt_construction(self) -> str:

        example_prompt = ""
        system_prompt = self.prompt_template["system"].format(examples=example_prompt)

        return system_prompt
    


    def user_prompt_construction(self, log_partition: list) -> str:
        pass


    def prompt_construction(self, user_content:list) -> list[dict]:
        """
        Construct the prompt for summarizing the experience into an example.
        :param user_content: The user content.
        return: The prompt for summarizing the experience into an example.
        """
    
        system_message = {
            "role": "system",
            "content": self.system_prompt
        }

        user_message = {
            "role": "user", 
            "content": user_content
            }
        
        prompt_message = [system_message, user_message]

        return prompt_message
    

    def examples_prompt_helper(self) -> list[str]:
        """
        Construct the prompt for examples.
        :param examples: The examples.
        :param header: The header of the prompt.
        :param separator: The separator of the prompt.
        return: The prompt for examples.
        """

        pass