# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import os
from typing import Any, Dict, List

from config.config_loader import get_ufo_config
from ufo.prompter.basic import BasicPrompter
from ufo.trajectory import parser
import ufo.utils


class EvaluationAgentPrompter(BasicPrompter):
    """
    The HostAgentPrompter class is the prompter for the host agent.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
    ):
        """
        Initialize the ApplicationAgentPrompter.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        """
        super().__init__(is_visual, prompt_template, example_prompt_template)

        self.api_prompt_template = None

    def system_prompt_construction(self) -> str:
        """
        Construct the prompt for app selection.
        return: The prompt for app selection.
        """

        examples = self.examples_prompt_helper()
        apis = self.api_prompt_helper()

        ufo_config = get_ufo_config()
        system_key = "system"
        screenshot_key = (
            "screenshots_all"
            if ufo_config.system.eva_all_screenshots
            else "screenshots_head_tail"
        )

        screenshots_description = self.prompt_template[screenshot_key]

        return self.prompt_template[system_key].format(
            examples=examples, apis=apis, screenshots=screenshots_description
        )

    def user_prompt_construction(
        self,
        request: str,
        trajectory: List[Dict[str, str]],
    ) -> str:
        """
        Construct the prompt for action selection.
        :request: The user request(s) to be evaluated.
        :trajectory: The trajectory of the user action.
        return: The prompt for action selection.
        """
        prompt = self.prompt_template["user"].format(
            request=request, trajectory=json.dumps(trajectory, indent=4, sort_keys=True)
        )

        return prompt

    def user_content_construction(
        self, log_path: str, request: str, eva_all_screenshots: bool = True
    ) -> List[Dict[str, str]]:
        """
        Construct the prompt for the EvaluationAgent.
        :param log_path: The path of the log.
        :param request: The user request.
        return: The prompt for the EvaluationAgent.
        """

        if eva_all_screenshots:
            return self.user_content_construction_all(log_path, request)
        else:
            return self.user_content_construction_head_tail(log_path, request)

    def user_content_construction_head_tail(
        self, log_path: str, request: str
    ) -> List[Dict[str, str]]:
        """
        Construct the prompt for the EvaluationAgent with head and tail screenshots.
        :param log_path: The path of the log.
        :param request: The user request.
        return: The prompt for the EvaluationAgent.
        """

        user_content = []
        log_eva = []

        trajectory = self.load_logs(log_path)

        if len(trajectory.app_agent_log) >= 0:
            first_screenshot_str = ufo.utils.encode_image(
                trajectory.app_agent_log[0]
                .get("ScreenshotImages")
                .get("clean_screenshot_path")
            )
        else:
            first_screenshot_str = ""

        last_screenshot_str = ufo.utils.encode_image(trajectory.final_screenshot_image)

        head_tail_screenshots = [first_screenshot_str, last_screenshot_str]

        for log in trajectory.app_agent_log:
            step_trajectory = self.get_step_trajectory(log)

            log_eva.append(step_trajectory)

        if self.is_visual:
            screenshot_text = ["Initial Screenshot:", "Final Screenshot:"]

            for i, image in enumerate(head_tail_screenshots):
                user_content.append({"type": "text", "text": screenshot_text[i]})
                user_content.append({"type": "image_url", "image_url": {"url": image}})

        user_content.append(
            {
                "type": "text",
                "text": self.user_prompt_construction(
                    request,
                    log_eva,
                ),
            }
        )

        return user_content

    def user_content_construction_all(
        self, log_path: str, request: str
    ) -> List[Dict[str, str]]:
        """
        Construct the prompt for the EvaluationAgent with all screenshots.
        :param log_path: The path of the log.
        :param request: The user request.
        return: The prompt for the EvaluationAgent.
        """

        user_content = []
        user_content.append(
            {
                "type": "text",
                "text": "<Original Request:> {request}".format(request=request),
            }
        )

        trajectory = self.load_logs(log_path)

        for log in trajectory.app_agent_log:

            step = log.get("session_step")

            if step is None:
                continue

            if self.is_visual:

                screenshot_image = log.get("ScreenshotImages").get(
                    "selected_control_screenshot_path"
                )
                screenshot_str = ufo.utils.encode_image(screenshot_image)

                user_content.append(
                    {"type": "image_url", "image_url": {"url": screenshot_str}}
                )

            step_trajectory = self.get_step_trajectory(log)

            user_content.append({"type": "text", "text": json.dumps(step_trajectory)})

        if self.is_visual:

            user_content.append({"type": "text", "text": "<Final Screenshot:>"})
            screenshot_str = ufo.utils.encode_image(trajectory.final_screenshot_image)

            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": screenshot_str},
                }
            )

        user_content.append(
            {
                "type": "text",
                "text": "<Your response:>",
            }
        )

        return user_content

    def get_step_trajectory(self, log: Dict[str, str]) -> Dict[str, str]:
        """
        Get the step trajectory from the log path.
        :param log: The log.
        """
        step_trajectory = {
            "Subtask": log.get("subtask"),
            "Step": log.get("session_step"),
            "Observation": log.get("observation"),
            "Thought": log.get("thought"),
            "Plan": log.get("plan"),
            "Comment": log.get("comment"),
            "Action": log.get("action"),
            "Application": log.get("application_process_name"),
            # "Results": log.get("Results"),
        }

        return step_trajectory

    @staticmethod
    def load_logs(log_path: str) -> parser.Trajectory:
        """
        Load logs from the log path.
        """

        return parser.Trajectory(log_path)

    def load_screenshots(self, log_path: str) -> List[str]:
        """
        Load the first and last screenshots from the log path.
        :param log_path: The path of the log.
        """

        init_image = os.path.join(log_path, "action_step1.png")
        final_image = os.path.join(log_path, "action_step_final.png")
        init_image_url = self.load_single_screenshot(init_image)
        final_image_url = self.load_single_screenshot(final_image)
        images = [init_image_url, final_image_url]
        return images

    @staticmethod
    def load_single_screenshot(screenshot_path: str) -> str:
        """
        Load a single screenshot from the log path.
        :param screenshot_path: The path of the screenshot.
        :return: The URL of the screenshot.
        """

        return ufo.utils.encode_image_from_path(screenshot_path)

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

        return self.retrieved_documents_prompt_helper(header, separator, example_list)

    def create_api_prompt_template(self, tool_info_dict: Dict[str, Any]) -> None:
        """
        Create the API prompt template.
        :param tool_info_dict: The tool information dictionary.
        """

        api_list = []

        for agent_name in tool_info_dict:
            tool_info = tool_info_dict[agent_name]
            tool_info_prompt = BasicPrompter.tools_to_llm_prompt(tool_info)
            api_list.append(f"Tool Info for Agent {agent_name}: {tool_info_prompt}")

        api_prompt = self.retrieved_documents_prompt_helper("", "", api_list)

        self.api_prompt_template = api_prompt

    def api_prompt_helper(self) -> str:
        """
        Construct the API prompt.
        """
        if self.api_prompt_template is None:
            raise ValueError(
                "API prompt template is not set. Call create_api_prompt_template first."
            )
        return self.api_prompt_template


if __name__ == "__main__":

    ufo_config = get_ufo_config()
    eva_prompter = EvaluationAgentPrompter(
        is_visual=True,
        prompt_template=ufo_config.system.evaluation_prompt,
        example_prompt_template="",
    )
