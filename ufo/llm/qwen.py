import base64
import copy
import io
import os
import shutil
import time
from http import HTTPStatus
from typing import Any, Dict, List, Optional

import dashscope
from PIL import Image

from ufo.llm.base import BaseService
from ufo.utils import print_with_color


class QwenService(BaseService):
    """
    A service class for Qwen models.
    """

    def __init__(self, config, agent_type: str):
        """
        :param config: The configuration.
        :param agent_type: The agent type.
        """
        self.config_llm = config[agent_type]
        self.config = config
        self.max_retry = self.config["MAX_RETRY"]
        self.timeout = self.config["TIMEOUT"]
        self.api_type = self.config_llm["API_TYPE"].lower()
        self.prices = self.config["PRICES"]
        dashscope.api_key = self.config_llm["API_KEY"]
        self.tmp_dir = None

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        n: int = 1,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generates chat completions based on the given messages.
        :param messages: The list of messages to generate completions for.
        :param n: The number of completions to generate.
        :param temperature: Controls the randomness of the output. Higher values make the output more random. If not provided, the default value from the model configuration will be used.
        :param max_tokens: The maximum number of tokens in the generated completions. If not provided, the default value from the model configuration will be used.
        :param top_p: Controls the diversity of the output. Higher values make the output more diverse. If not provided, the default value from the model configuration will be used.
        :return: A tuple containing a list of generated completions and the total cost.
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
                                response.output.choices[0].message.content[0]["text"]
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

    def process_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Process the given messages and save any images included in the content.
        :param messages: The list of messages to process.
        :return: The processed messages with images saved.
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
