import re
import time
from typing import Any, Dict, List, Optional, Tuple

import anthropic
from PIL import Image

from ufo.llm.base import BaseService
from ufo.utils import print_with_color


class ClaudeService(BaseService):
    """
    A service class for Claude models.
    """

    def __init__(self, config: Dict[str, Any], agent_type: str):
        """
        Initialize the Gemini service.
        :param config: The configuration.
        :param agent_type: The agent type.
        """
        self.config_llm = config[agent_type]
        self.config = config
        self.model = self.config_llm["API_MODEL"]
        self.prices = self.config["PRICES"]
        self.max_retry = self.config["MAX_RETRY"]
        self.api_type = self.config_llm["API_TYPE"].lower()
        self.client = anthropic.Anthropic(api_key=self.config_llm["API_KEY"])

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
        Generates completions for a given list of messages.
        :param messages: The list of messages to generate completions for.
        :param n: The number of completions to generate for each message.
        :param temperature: Controls the randomness of the generated completions. Higher values (e.g., 0.8) make the completions more random, while lower values (e.g., 0.2) make the completions more focused and deterministic. If not provided, the default value from the model configuration will be used.
        :param max_tokens: The maximum number of tokens in the generated completions. If not provided, the default value from the model configuration will be used.
        :param top_p: Controls the diversity of the generated completions. Higher values (e.g., 0.8) make the completions more diverse, while lower values (e.g., 0.2) make the completions more focused. If not provided, the default value from the model configuration will be used.
        :param kwargs: Additional keyword arguments to be passed to the underlying completion method.
        :return: A list of generated completions for each message and the cost set to be None.
        """

        temperature = (
            temperature if temperature is not None else self.config["TEMPERATURE"]
        )
        top_p = top_p if top_p is not None else self.config["TOP_P"]
        max_tokens = max_tokens if max_tokens is not None else self.config["MAX_TOKENS"]

        responses = []
        cost = 0.0
        system_prompt, user_prompt = self.process_messages(messages)

        for _ in range(n):
            for _ in range(self.max_retry):
                try:
                    response = self.client.messages.create(
                        max_tokens=max_tokens,
                        model=self.model,
                        system=system_prompt,
                        messages=user_prompt,
                    )
                    responses.append(response.content[0].text)
                    prompt_tokens = response.usage.input_tokens
                    completion_tokens = response.usage.output_tokens
                    cost += self.get_cost_estimator(
                        self.api_type,
                        self.model,
                        self.prices,
                        prompt_tokens,
                        completion_tokens,
                    )
                except Exception as e:
                    import traceback

                    error_trace = traceback.format_exc()
                    print_with_color(
                        f"Error when making API request: {error_trace}", "red"
                    )
                    try:
                        print_with_color(response, "red")
                    except:
                        _
                    time.sleep(3)
                    continue

        return responses, cost

    def process_messages(
        self, messages: List[Dict[str, str]]
    ) -> Tuple[str, list[Dict]]:
        """
        Processes the messages to generate the system and user prompts.
        :param messages: A list of message dictionaries.
        :return: A tuple containing the system prompt (str) and the user prompt (list).
        """

        system_prompt = ""
        user_prompt = {"role": "user", "content": []}
        if isinstance(messages, dict):
            messages = [messages]
        for message in messages:
            if message["role"] == "system":
                system_prompt = message["content"]
            else:
                for content in message["content"]:
                    if content["type"] == "text":
                        user_prompt["content"].append(content)
                    elif content["type"] == "image_url":
                        data_url = content["image_url"]["url"]
                        match = re.match(r"data:(.*?);base64,(.*)", data_url)
                        if match:
                            media_type = match.group(1)
                            base64_data = match.group(2)
                            user_prompt["content"].append(
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": base64_data,
                                    },
                                }
                            )
                        else:
                            raise ValueError("Invalid image URL")
        return system_prompt, [user_prompt]
