import base64
import copy
import io
import json
import os
import shutil
import time
from http import HTTPStatus
from typing import Any, Optional

import dashscope
from PIL import Image

from ufo.utils import print_with_color
from ufo.llm.base import BaseService


class QwenService(BaseService):
    def __init__(self, config, agent_type: str):
        self.config_llm = config[agent_type]
        self.config = config
        self.max_retry = self.config["MAX_RETRY"]
        self.timeout = self.config["TIMEOUT"]
        dashscope.api_key = self.config_llm["API_KEY"]
        self.tmp_dir = None

    def chat_completion(
        self,
        messages,
        n,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
        """
        Generates chat completions based on the given messages.
        Args:
            messages (List[str]): List of messages in the conversation.
            n (int): Number of completions to generate.
            temperature (float, optional): Controls the randomness of the output. Higher values make the output more random. Defaults to None.
            max_tokens (int, optional): Maximum number of tokens in the generated completions. Defaults to None.
            top_p (float, optional): Controls the diversity of the output. Higher values make the output more diverse. Defaults to None.
            **kwargs: Additional keyword arguments.
        Returns:
            Tuple[List[str], float]: A tuple containing a list of generated completions and the total cost.
        Raises:
            ValueError: If the API response does not contain the expected content.
            Exception: If there is an error making the API request.
        """
        temperature = (
            temperature if temperature is not None else self.config["TEMPERATURE"]
        )
        max_tokens = max_tokens if max_tokens is not None else self.config["MAX_TOKENS"]
        top_p = top_p if top_p is not None else self.config["TOP_P"] + 1e-06
        self.model = self.config_llm["API_MODEL"]

        responses = []
        cost = 0.0

        for i in range(n):
            for _ in range(self.max_retry):
                try:
                    response = dashscope.MultiModalConversation.call(
                        model=self.model,
                        messages=self.process_messages(messages),
                        top_p=top_p,
                    )
                    if response.status_code == HTTPStatus.OK:

                        usage = response.usage
                        _cost = self.get_cost_estimator(
                            self.api_type,
                            self.model,
                            self.prices,
                            usage["input_tokens"],
                            (
                                usage["output_tokens"] + usage["image_tokens"]
                                if "image_tokens" in usage
                                else usage["output_tokens"]
                            ),
                        )

                        if (
                            "Observation"
                            not in response.output.choices[0].message.content[0]["text"]
                        ):
                            raise ValueError(
                                response.output.choices[0].message.content[0]["text"]
                            )
                        else:
                            shutil.rmtree(self.tmp_dir, ignore_errors=True)
                            responses.append(
                                self.parse_qwen_response(
                                    response.output.choices[0].message.content[0][
                                        "text"
                                    ]
                                )
                            )
                            cost += _cost
                            break
                    else:
                        raise ValueError(response.message)
                except Exception as e:
                    print_with_color(f"Error making API request: {e}", "red")
                    print_with_color(str(response), "red")
                    time.sleep(3)
                    continue

        return responses, cost

    def process_messages(self, messages):
        """
        Process the given messages and save any images included in the content.
        Args:
            messages (list): A list of messages to process.
        Returns:
            list: The processed messages with images saved.
            Path: The path to the saved tmp images.
        """

        def save_image_from_base64(base64_str, path, filename):
            image_data = base64.b64decode(base64_str)
            image = Image.open(io.BytesIO(image_data))
            image_path = os.path.join(path, filename).replace(os.sep, "/")

            # resize
            orig_width, orig_height = image.size
            max_size = 512
            scale_w = min(max_size / orig_width, 1)
            scale_h = min(max_size / orig_height, 1)
            scale = min(scale_w, scale_h)
            new_width = int(orig_width * scale)
            new_height = int(orig_height * scale)
            image_resized = image.resize((new_width, new_height), Image.LANCZOS)

            image_resized.save(image_path)
            return f"file://{image_path}"

        # Create a temporary directory to store the images.
        temp_dir = os.path.join(os.path.abspath("."), "tmp")
        self.tmp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        _messages = copy.deepcopy(messages)
        # Process messages and save images if any.
        for i, message in enumerate(_messages):
            message["content"] = (
                message.get("content", [])
                if isinstance(message["content"], list)
                else [message["content"]]
            )
            for j, content in enumerate(message["content"]):
                if isinstance(content, str):
                    content = {"text": content}
                    message["content"][j] = content
                if content.get("type"):
                    _ = content.pop("type")
                if content.get("image_url"):
                    img_data = content["image_url"]["url"].split(
                        "data:image/png;base64,"
                    )[1]
                    filename = f"{i}_{j}.png"
                    content["image"] = save_image_from_base64(
                        img_data, temp_dir, filename
                    )
                    _ = content.pop("image_url")
        return _messages

    def parse_qwen_response(self, content):
        """
        Parses the qwen response and returns a JSON string.
        Args:
            content (str): The content to be parsed.
        Returns:
            str: A JSON string representing the parsed content.
        """
        dict_str = [_.strip() for _ in content.split("\n")][1:-1]
        _dict_str = {}

        def remove_quotes(s):
            if (s.startswith('"') and s.endswith('"')) or (
                s.startswith("'") and s.endswith("'")
            ):
                return s[1:-1]
            elif (s.startswith('"')) or (s.startswith("'")):
                return s[1]
            elif (s.endswith('"')) or (s.endswith("'")):
                return s[:-1]
            return s

        for _str in dict_str:
            key, value = _str.split(":")
            _dict_str[remove_quotes(key)] = value.strip()

        return json.dumps(_dict_str)
