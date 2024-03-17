# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
import yaml


class BasicPrompter(ABC):

    def __init__(self, is_visual: bool, prompt_template: str, example_prompt_template: str):
        """
        Initialize the BasicPrompter.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        """
        self.is_visual = is_visual
        self.prompt_template = self.load_prompt_template(prompt_template)
        self.example_prompt_template = self.load_prompt_template(example_prompt_template)


    def load_prompt_template(self, template_path: str) -> str:
        """
        Load the prompt template.
        :return: The prompt template.
        """

        path = template_path.format(mode = "visual" if self.is_visual else "nonvisual")
        prompt = yaml.safe_load(open(path, "r", encoding="utf-8"))
        
        return prompt
    

    def prompt_construction(self, system_prompt:str, user_content:list) -> list[dict]:
        """
        Construct the prompt for summarizing the experience into an example.
        :param user_content: The user content.
        return: The prompt for summarizing the experience into an example.
        """
    
        system_message = {
            "role": "system",
            "content": system_prompt
        }

        user_message = {
            "role": "user", 
            "content": user_content
            }
        
        prompt_message = [system_message, user_message]

        return prompt_message
    
    
    @abstractmethod
    def system_prompt_construction(self) -> str:

        pass
    

    @abstractmethod
    def user_prompt_construction(self) -> str:

        pass


    @abstractmethod
    def user_content_construction(self) -> str:

        pass


    def examples_prompt_helper(self) -> str:
        
        pass


    def api_prompt_helper(self) -> str:
        
        pass

    def retrived_documents_prompt_helper(self) -> str:
        
        pass