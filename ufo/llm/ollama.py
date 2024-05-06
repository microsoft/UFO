import base64
import copy
import io
import json
import time
from typing import Any, Optional

import requests
from PIL import Image

from ufo.utils import print_with_color

from .base import BaseService


class OllamaService(BaseService):
    def __init__(self, config, agent_type: str):
        self.config_llm = config[agent_type]
        self.config = config
        self.max_retry = self.config["MAX_RETRY"]
        self.timeout = self.config["TIMEOUT"]

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
        Generates completions for a given list of messages.

        Args:
            messages (List[str]): The list of messages to generate completions for.
            n (int): The number of completions to generate for each message.
            temperature (float, optional): Controls the randomness of the generated completions. Higher values (e.g., 0.8) make the completions more random, while lower values (e.g., 0.2) make the completions more focused and deterministic. If not provided, the default value from the model configuration will be used.
            max_tokens (int, optional): The maximum number of tokens in the generated completions. If not provided, the default value from the model configuration will be used.
            top_p (float, optional): Controls the diversity of the generated completions. Higher values (e.g., 0.8) make the completions more diverse, while lower values (e.g., 0.2) make the completions more focused. If not provided, the default value from the model configuration will be used.
            **kwargs: Additional keyword arguments to be passed to the underlying completion method.

        Returns:
            List[str], None:A list of generated completions for each message and the cost set to be None.

        Raises:
            Exception: If an error occurs while making the API request.
        """
        temperature = (
            temperature if temperature is not None else self.config["TEMPERATURE"]
        )
        max_tokens = max_tokens if max_tokens is not None else self.config["MAX_TOKENS"]
        top_p = top_p if top_p is not None else self.config["TOP_P"]

        responses = []

        for i in range(n):
            for _ in range(self.max_retry):
                try:
                    response = self._chat_completion(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        **kwargs,
                    )
                    responses.append(response)
                    break
                except Exception as e:
                    print_with_color(f"Error making API request: {e}", "red")
                    try:
                        print_with_color(response, "red")
                    except:
                        _
                    time.sleep(3)
                    continue
        return responses, None

    def _chat_completion(
        self,
        messages,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
        """
        Perform chat completion using the OpenAI API.

        Args:
            messages: A list of message objects containing 'role' and 'content' keys.
            temperature: The temperature parameter controls the randomness of the output.
            max_tokens: The maximum number of tokens to generate in the response.
            top_p: The cumulative probability of the most likely tokens to include in the response.
            **kwargs: Additional keyword arguments.

        Returns:
            The generated response as a string.

        Raises:
            Exception: If the API request fails with a non-200 status code.
        """
        api_endpoint = "/api/chat"
        payload = {
            "model": self.config_llm["API_MODEL"],
            "messages": self._process_messages(messages),
            "format": "json",
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            },
            "stream": False,
        }

        resp = self._request_api(api_endpoint, payload)
        if resp.status_code != 200:
            raise Exception(
                f"Failed to get completion with error code {resp.status_code}: {resp.text}",
            )
        response: str = resp.json()["message"]["content"]

        return response

    def resize_base64_image(self, base64_str):
        """
        Resize a base64 encoded image.

        Args:
            base64_str (str): The base64 encoded image string.

        Returns:
            str: The resized base64 encoded image string.
        """
        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))

        orig_width, orig_height = image.size
        max_size = 1024
        scale_w = min(max_size / orig_width, 1)
        scale_h = min(max_size / orig_height, 1)
        scale = min(scale_w, scale_h)
        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)
        image_resized = image.resize((new_width, new_height), Image.LANCZOS)
        buffer = io.BytesIO()
        image_resized.save(buffer, format="PNG")

        return base64.b64encode(buffer.getvalue()).decode()

    def _process_messages(self, messages):
        """
        Process the given messages and modify their content and images.

        Args:
            messages (list): A list of messages to be processed.

        Returns:
            list: The processed messages with modified content and images.
        """
        _messages = copy.deepcopy(messages)
        tmp_image_text = tmp_image = None
        for i, message in enumerate(_messages):
            if isinstance(message["content"], list):
                for j, content in enumerate(message["content"]):
                    if content["type"] == "text":
                        tmp_text = content.get("text")
                    elif content["type"] == "image_url":
                        tmp_image = content.get("image_url")["url"].split("base64,")[1]
                        tmp_image_text = tmp_text
                message["content"] = (
                    tmp_text
                    + "And the image is the screenshot from windows,"
                    + tmp_image_text[:-1]
                )
                message["images"] = [self.resize_base64_image(tmp_image)]
        return _messages

    def _request_api(self, api_path: str, payload: Any, stream: bool = False):
        """
        Sends a POST request to the specified API path with the given payload.

        Args:
            api_path (str): The path of the API endpoint.
            payload (Any): The payload to be sent with the request.
            stream (bool, optional): Whether to stream the response. Defaults to False.

        Returns:
            Response: The response object returned by the API.
        """
        url = f"{self.config_llm['API_BASE']}{api_path}"
        response = requests.post(
            url=url, json=payload, timeout=self.timeout, stream=stream
        )
        return response
