# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from typing import Dict, List, Optional

from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.config.config import Config
from ufo.prompter.agent_prompter import APIPromptLoader
from ufo.prompter.basic import BasicPrompter


configs = Config.get_instance().config_data


class EvaluationAgentPrompter(BasicPrompter):
    """
    The HostAgentPrompter class is the prompter for the host agent.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
        api_prompt_template: str,
        root_name: Optional[str] = None,
    ):
        """
        Initialize the ApplicationAgentPrompter.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        :param api_prompt_template: The path of the api prompt template.
        """
        super().__init__(is_visual, prompt_template, example_prompt_template)
        self.root_name = root_name
        self.app_prompter = APIPromptLoader(self.root_name)
        self.api_prompt_template = self.load_prompt_template(api_prompt_template)

        self.app_api_prompt_template = None

        if configs.get("USE_APIS", False):
            self.app_api_prompt_template = self.app_prompter.load_com_api_prompt()

    def system_prompt_construction(self) -> str:
        """
        Construct the prompt for app selection.
        return: The prompt for app selection.
        """

        examples = self.examples_prompt_helper()
        apis = self.api_prompt_helper(verbose=1)

        system_key = "system"

        return self.prompt_template[system_key].format(examples=examples, apis=apis)

    def user_prompt_construction(
        self,
        request: str,
        trajectory: List[Dict[str, str]],
    ) -> str:
        """
        Construct the prompt for action selection.
        :param action_history: The action history.
        :param control_item: The control item.
        :param user_request: The user request.
        :param retrieved_docs: The retrieved documents.
        return: The prompt for action selection.
        """
        prompt = self.prompt_template["user"].format(
            request=request, trajectory=json.dumps(trajectory, indent=4, sort_keys=True)
        )

        return prompt

    def user_content_construction(
        self, log_path: str, request: str
    ) -> List[Dict[str, str]]:
        """
        Construct the prompt for the EvaluationAgent.
        :param log_path: The path of the log.
        :param request: The user request.
        return: The prompt for the EvaluationAgent.
        """

        user_content = []
        trajectory = []

        logs = self.load_logs(log_path)
        screenshots = self.load_screenshots(log_path)

        for log in logs:
            step_trajectory = {
                "Subtask": log.get("Request"),
                "Step": log.get("Step"),
                "Observation": log.get("Observation"),
                "Thought": log.get("Thought"),
                "ControlLabel": log.get("ControlLabel"),
                "ControlText": log.get("ControlText"),
                "Plan": log.get("Plan"),
                "Comment": log.get("Comment"),
                "Action": log.get("Action"),
                "Application": log.get("Application"),
                "Results": log.get("Results"),
            }

            trajectory.append(step_trajectory)

        if self.is_visual:
            screenshot_text = ["Initial Screenshot:", "Final Screenshot:"]

            for i, image in enumerate(screenshots):
                user_content.append({"type": "text", "text": screenshot_text[i]})
                user_content.append({"type": "image_url", "image_url": {"url": image}})

        user_content.append(
            {
                "type": "text",
                "text": self.user_prompt_construction(
                    request,
                    trajectory,
                ),
            }
        )

        return user_content

    @staticmethod
    def load_logs(log_path: str) -> List[Dict[str, str]]:
        """
        Load logs from the log path.
        """
        log_file_path = os.path.join(log_path, "response.log")
        with open(log_file_path, "r") as f:
            logs = f.readlines()
            logs = [json.loads(log) for log in logs]
        return logs

    @staticmethod
    def load_screenshots(log_path: str) -> List[str]:

        init_image = os.path.join(log_path, "action_step1.png")
        final_image = os.path.join(log_path, "action_step_final.png")
        init_image_url = PhotographerFacade().encode_image_from_path(init_image)
        final_image_url = PhotographerFacade().encode_image_from_path(final_image)
        images = [init_image_url, final_image_url]
        return images

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

        if isinstance(self.example_prompt_template, str):
            return self.example_prompt_template

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

        return self.retrived_documents_prompt_helper(header, separator, example_list)

    def api_prompt_helper(self, verbose: int = 1) -> str:
        """
        Construct the prompt for APIs.
        :param apis: The APIs.
        :param verbose: The verbosity level.
        return: The prompt for APIs.
        """

        # Construct the prompt for each UI control action.
        api_list = [
            "- The action types for UI elements are: {actions}.".format(
                actions=list(self.api_prompt_template.keys())
            )
        ]

        for key in self.api_prompt_template.keys():
            api = self.api_prompt_template[key]
            if verbose > 0:
                api_text = "{summary}\n{usage}".format(
                    summary=api["summary"], usage=api["usage"]
                )
            else:
                api_text = api["summary"]

            api_list.append(api_text)

        # Construct the prompt for COM APIs
        if self.app_api_prompt_template:

            api_list += [
                "- There are additional shortcut APIs for the operations: {apis}".format(
                    apis=list(self.app_api_prompt_template.keys())
                )
            ]
            for key in self.app_api_prompt_template.keys():
                api = self.app_api_prompt_template[key]
                if verbose > 0:
                    api_text = "{summary}\n{usage}".format(
                        summary=api["summary"], usage=api["usage"]
                    )
                else:
                    api_text = api["summary"]

                api_list.append(api_text)

        api_prompt = self.retrived_documents_prompt_helper("", "", api_list)

        return api_prompt
