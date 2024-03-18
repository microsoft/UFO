# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from .parser import LogLoader
from ..prompter.experience_prompter import ExperiencePrompter
from ..llm.llm_call import get_gptv_completion


class ExperienceSummarizer:
    """
    The ExperienceSummarizer class is the summarizer for the experience learning.
    """

    def __init__(self, is_visual: bool, prompt_template: str, example_prompt_template: str, api_prompt_template: str):
        """
        Initialize the ApplicationAgentPrompter.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        :param api_prompt_template: The path of the api prompt template.
        """
        self.is_visual = is_visual
        self.prompt_template = prompt_template
        self.example_prompt_template = example_prompt_template
        self.api_prompt_template = api_prompt_template


    def read_log(self, log_path: str) -> list:
        """
        Read the log.
        :param log_path: The path of the log file.
        """
        replay_loader = LogLoader(log_path)
        logs = replay_loader.create_logs()
        return logs
    
    
    def build_prompt(self, logs: list) -> list:
        """
        Build the prompt.
        :param logs: The logs.
        :param user_request: The user request.
        """
        experience_prompter = ExperiencePrompter(self.is_visual, self.prompt_template, self.example_prompt_template, self.api_prompt_template)
        experience_system_prompt = experience_prompter.system_prompt_construction()
        experience_user_prompt = experience_prompter.user_content_construction(logs)
        experience_prompt = experience_prompter.prompt_construction(experience_system_prompt, experience_user_prompt)
        
        return experience_prompt
    

    def get_summary(self, prompt: str) -> str:
        """
        """
        response = get_gptv_completion(prompt, self.is_visual)

        return prompt