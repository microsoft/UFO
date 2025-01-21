# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import mimetypes
import os
from typing import Dict, List, cast, Optional

from ufo.prompter.basic import BasicPrompter


class TemplatePrompter(BasicPrompter):
    """
    Load the prompt for the TemplateAgent.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
    ):
        """
        Initialize the FilterPrompter.
        :param is_visual: The flag indicating whether the prompter is visual or not.
        :param prompt_template: The prompt template.
        """

        super().__init__(is_visual, prompt_template, example_prompt_template)

    def encode_image(self, image_path: str) -> str:
        """
        Encode the image.
        :param image_path: The image path.
        :return: The encoded image.
        """
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("ascii")

        mime_type = "image/png"

        image_url = f"data:{mime_type};base64," + encoded_image
        return image_url

    def file_prompt_helper(self, path) -> str:
        """
        Construct the prompt for files.
        :return: The prompt for files.
        """
        image_path = os.path.join(path, "images")
        image_urls = []
        user_content = []
        for file in os.listdir(image_path):
            if file.endswith(".png"):
                image_urls.append(self.encode_image(os.path.join(image_path, file)))

        for i in range(len(image_urls)):
            user_content.append(
                {
                    "type": "text",
                    "text": "This is the screenshot of " + str(i + 1) + ".docx",
                },
            )
            user_content.append(
                {"type": "image_url", "image_url": {"url": image_urls[i]}},
            )
        return user_content

    def system_prompt_construction(self, descriptions: str = "") -> str:
        """
        Construct the prompt for the system.
        :param app: The app name.
        :return: The prompt for the system.
        """

        try:
            ans = self.prompt_template["system"]
            ans = ans.format(descriptions=descriptions)
            return ans
        except Exception as e:
            print(e)

    def user_prompt_construction(self, request: str) -> str:
        """
        Construct the prompt for the user.
        :param request: The user request.
        :return: The prompt for the user.
        """

        prompt = self.prompt_template["user"].format(given_task=request)
        return prompt

    def user_content_construction(self, path: str, request: str) -> List[Dict]:
        """
        Construct the prompt for LLMs.
        :param path: The path of the template.
        :param request: The user request.
        :return: The prompt for LLMs.
        """

        user_content = self.file_prompt_helper(path)

        user_content.append(
            {"type": "text", "text": self.user_prompt_construction(request)}
        )

        return user_content
