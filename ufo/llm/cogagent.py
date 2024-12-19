import time
from typing import Any, Optional

import requests

from ufo.utils import print_with_color
from .base import BaseService


class CogAgentService(BaseService):
    def __init__(self, config, agent_type: str):
        self.config_llm = config[agent_type]
        self.config = config
        self.max_retry = self.config["MAX_RETRY"]
        self.timeout = self.config["TIMEOUT"]
        self.max_tokens = 2048  # default max tokens for cogagent for now

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
        Generate chat completions based on given messages.
        Args:
            messages (list): A list of messages.
            n (int): The number of completions to generate.
            temperature (float, optional): The temperature for sampling. Defaults to None.
            max_tokens (int, optional): The maximum number of tokens in the completion. Defaults to None.
            top_p (float, optional): The cumulative probability for top-p sampling. Defaults to None.
            **kwargs: Additional keyword arguments.
        Returns:
            tuple: A tuple containing the generated texts and None.
        """

        temperature = (
            temperature if temperature is not None else self.config["TEMPERATURE"]
        )
        max_tokens = max_tokens if max_tokens is not None else self.config["MAX_TOKENS"]
        top_p = top_p if top_p is not None else self.config["TOP_P"]

        texts = []
        for i in range(n):
            image_base64 = None
            if self.config_llm["VISUAL_MODE"]:
                image_base64 = messages[1]["content"][-2]["image_url"]["url"].split(
                    "base64,"
                )[1]
            prompt = messages[0]["content"] + messages[1]["content"][-1]["text"]

            payload = {
                "model": self.config_llm["API_MODEL"],
                "prompt": prompt,
                "temperature": temperature,
                "top_p": top_p,
                "max_new_tokens": self.max_tokens,
                "image": image_base64,
            }

            for _ in range(self.max_retry):
                try:
                    response = requests.post(
                        self.config_llm["API_BASE"] + "/chat/completions", json=payload
                    )
                    if response.status_code == 200:
                        response = response.json()
                        text = response["text"]
                        texts.append(text)
                        break
                    else:
                        raise Exception(
                            f"Failed to get completion with error code {response.status_code}: {response.text}",
                        )
                except Exception as e:
                    print_with_color(f"Error making API request: {e}", "red")
                    try:
                        print_with_color(response, "red")
                    except:
                        _
                    time.sleep(3)
                    continue
        return texts, None
