# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from .parser import LogLoader
from ..prompter.experience_prompter import ExperiencePrompter
from ..llm.llm_call import get_completion


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
        response = get_completion(prompt, self.is_visual)

        return response
    

    def get_summary_list(self, logs: list) -> list:
        """
        """
        summaries = []
        for log in logs:
            prompt = self.build_prompt(log)
            summary = self.get_summary(prompt)
            summaries.append(summary)

        self.update_ymal(summaries, "path")
        self.update_verctor_db(summaries, "path")
        return summaries
    

    @staticmethod
    def update_ymal(summaries: list, yaml_path: str):
        """
        """
        pass


    @staticmethod
    def update_verctor_db(summaries: list, db_path: str):
        """
        """
        pass