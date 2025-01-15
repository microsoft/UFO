# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from typing import Tuple

import yaml
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS

from record_processor.parser.demonstration_record import DemonstrationRecord
from record_processor.utils import json_parser
from ufo.llm.llm_call import get_completions
from ufo.prompter.demonstration_prompter import DemonstrationPrompter
from ufo.utils import get_hugginface_embedding


class DemonstrationSummarizer:
    """
    The DemonstrationSummarizer class is the summarizer for the demonstration learning.
    It summarizes the demonstration record to a list of summaries,
    and save the summaries to the YAML file and the vector database.
    A sample of the summary is as follows:
    {
        "example": {
            "Observation": "Word.exe is opened.",
            "Thought": "The user is trying to create a new file.",
            "ControlLabel": "1",
            "ControlText": "Sample Control Text",
            "Function": "CreateFile",
            "Args": "filename='new_file.txt'",
            "Status": "Success",
            "Plan": "Create a new file named 'new_file.txt'.",
            "Comment": "The user successfully created a new file."
        },
        "Tips": "You can use the 'CreateFile' function to create a new file."
    }
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        demonstration_prompt_template: str,
        api_prompt_template: str,
        completion_num: int = 1,
    ):
        """
        Initialize the DemonstrationSummarizer.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param demonstration_prompt_template: The path of the example prompt template for demonstration.
        :param api_prompt_template: The path of the api prompt template.
        """
        self.is_visual = is_visual
        self.prompt_template = prompt_template
        self.demonstration_prompt_template = demonstration_prompt_template
        self.api_prompt_template = api_prompt_template
        self.completion_num = completion_num

    def get_summary_list(self, record: DemonstrationRecord) -> Tuple[list, float]:
        """
        Get the summary list for a record
        :param record: The demonstration record.
        return: The summary list for the user defined completion number and the cost
        """

        prompt = self.__build_prompt(record)
        response_string_list, cost = get_completions(
            prompt, "APPAGENT", use_backup_engine=True, n=self.completion_num
        )
        summaries = []
        for response_string in response_string_list:
            summary = self.__parse_response(response_string)
            if summary:
                summary["request"] = record.get_request()
                summary["app_list"] = record.get_applications()
                summaries.append(summary)

        return summaries, cost

    def __build_prompt(self, demo_record: DemonstrationRecord) -> list:
        """
        Build the prompt by the user demonstration record.
        :param demo_record: The user demonstration record.
        return: The prompt.
        """
        demonstration_prompter = DemonstrationPrompter(
            self.is_visual,
            self.prompt_template,
            self.demonstration_prompt_template,
            self.api_prompt_template,
        )
        demonstration_system_prompt = (
            demonstration_prompter.system_prompt_construction()
        )
        demonstration_user_prompt = demonstration_prompter.user_content_construction(
            demo_record
        )
        demonstration_prompt = demonstration_prompter.prompt_construction(
            demonstration_system_prompt, demonstration_user_prompt
        )

        return demonstration_prompt

    def __parse_response(self, response_string: str) -> dict:
        """
        Parse the response string to a dict of summary.
        :param response_string: The response string.
        return: The summary dict.
        """
        try:
            response_json = json_parser(response_string)
        except:
            response_json = None

        # Restructure the response, in case any of the keys are missing, set them to empty string.
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

            return summary

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
