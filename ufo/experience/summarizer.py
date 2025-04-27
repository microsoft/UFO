# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import sys
from typing import Tuple

import yaml
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS

from ufo.experience.experience_parser import ExperienceLogLoader
from ufo.llm.llm_call import get_completion
from ufo.prompter.experience_prompter import ExperiencePrompter
from ufo.utils import get_hugginface_embedding, json_parser


class ExperienceSummarizer:
    """
    The ExperienceSummarizer class is the summarizer for the experience learning.
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
        self.is_visual = is_visual
        self.prompt_template = prompt_template
        self.example_prompt_template = example_prompt_template
        self.api_prompt_template = api_prompt_template

    def build_prompt(self, log_partition: dict) -> list:
        """
        Build the prompt.
        :param log_partition: The log partition.
        return: The prompt.
        """
        experience_prompter = ExperiencePrompter(
            self.is_visual,
            self.prompt_template,
            self.example_prompt_template,
            self.api_prompt_template,
        )
        experience_system_prompt = experience_prompter.system_prompt_construction()
        experience_user_prompt = experience_prompter.user_content_construction(
            log_partition
        )
        experience_prompt = experience_prompter.prompt_construction(
            experience_system_prompt, experience_user_prompt
        )

        return experience_prompt

    def get_summary(self, prompt_message: list) -> Tuple[dict, float]:
        """
        Get the summary.
        :param prompt_message: The prompt message.
        return: The summary and the cost.
        """

        # Get the completion for the prompt message
        response_string, cost = get_completion(
            prompt_message, "APPAGENT", use_backup_engine=True
        )
        try:
            response_json = json_parser(response_string)
        except:
            response_json = None

        # Restructure the response
        if response_json:
            summary = dict()
            summary["example"] = {}
            for key in [
                "Observation",
                "Thought",
                "ControlLabel",
                "ControlText",
                "Function",
                "Args",
                "Status",
                "Plan",
                "Comment",
            ]:
                summary["example"][key] = response_json.get(key, "")
            summary["Tips"] = response_json.get("Tips", "")

        return summary, cost

    def get_summary_list(self, logs: list) -> Tuple[list, float]:
        """
        Get the summary list.
        :param logs: The logs.
        return: The summary list and the total cost.
        """
        summaries = []
        total_cost = 0.0
        for log_partition in logs:
            prompt = self.build_prompt(log_partition)
            summary, cost = self.get_summary(prompt)
            summary["request"] = log_partition.get("subtask")
            summary["Sub-task"] = log_partition.get("subtask")
            summary["app_list"] = [log_partition.get("application")]
            summaries.append(summary)
            total_cost += cost

        return summaries, total_cost

    @staticmethod
    def read_logs(log_path: str) -> list:
        """
        Read the log.
        :param log_path: The path of the log file.
        """
        replay_loader = ExperienceLogLoader(log_path)
        return replay_loader.subtask_partition

    @staticmethod
    def create_or_update_yaml(summaries: list, yaml_path: str):
        """
        Create or update the YAML file.

        :param summaries: The summaries.
        :param yaml_path: The path of the YAML file.
        """

        # Check if the file exists, if not, create a new one
        if not os.path.exists(yaml_path):
            with open(yaml_path, "w"):
                pass
            print(f"Created new YAML file: {yaml_path}")

        # Read existing data from the YAML file
        with open(yaml_path, "r") as file:
            existing_data = yaml.safe_load(file)

        # Initialize index and existing_data if file is empty
        index = len(existing_data) if existing_data else 0
        existing_data = existing_data or {}

        # Update data with new summaries
        for i, summary in enumerate(summaries):
            example = {f"example{index + i}": summary}
            existing_data.update(example)

        # Write updated data back to the YAML file
        with open(yaml_path, "w") as file:
            yaml.safe_dump(
                existing_data, file, default_flow_style=False, sort_keys=False
            )

        print(f"Updated existing YAML file successfully: {yaml_path}")

    @staticmethod
    def create_or_update_vector_db(summaries: list, db_path: str):
        """
        Create or update the vector database.
        :param summaries: The summaries.
        :param db_path: The path of the vector database.
        """

        document_list = []

        for summary in summaries:
            request = summary["request"]
            document_list.append(Document(page_content=request, metadata=summary))

        db = FAISS.from_documents(document_list, get_hugginface_embedding())

        # Check if the db exists, if not, create a new one.
        if os.path.exists(db_path):
            prev_db = FAISS.load_local(
                db_path,
                get_hugginface_embedding(),
                allow_dangerous_deserialization=True,
            )
            db.merge_from(prev_db)

        db.save_local(db_path)

        print(f"Updated vector DB successfully: {db_path}")


if __name__ == "__main__":

    from ufo.config.config import Config

    configs = Config.get_instance().config_data

    # Initialize the ExperienceSummarizer

    summarizer = ExperienceSummarizer(
        configs["APP_AGENT"]["VISUAL_MODE"],
        configs["EXPERIENCE_PROMPT"],
        configs["APPAGENT_EXAMPLE_PROMPT"],
        configs["API_PROMPT"],
    )

    log_path = "logs/test_exp"

    experience = summarizer.read_logs(log_path)
    summaries, cost = summarizer.get_summary_list(experience)
    print(summaries, cost)
