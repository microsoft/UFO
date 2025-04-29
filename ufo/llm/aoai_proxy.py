# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Any, Callable, Literal, Optional, List, Dict

import openai
import aiohttp
import requests

from ufo.llm.base import BaseService


class AOAIProxyService(BaseService):
    """
    The AOAI Proxy service class to interact with the AOAI Proxy API.
    """

    def __init__(self, config: Dict[str, Any], agent_type: str) -> None:
        """
        Create a AOAI Proxy service instance.
        :param config: The configuration for the AOAI Proxy service.
        :param agent_type: The type of the agent.
        """
        self.config_llm = config[agent_type]
        self.config = config
        self.api_type = self.config_llm["API_TYPE"].lower()
        self.max_retry = self.config["MAX_RETRY"]
        self.prices = self.config.get("PRICES", {})
        assert self.api_type in ["aoai_proxy"], "Invalid API type"
        self.base_url = self.config_llm.get("API_BASE_URL", "http://localhost:8000")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        n: int,
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
        """
        Generates completions for a given conversation using the OpenAI Chat API.
        :param messages: The list of messages in the conversation.
        :param n: The number of completions to generate.
        :param stream: Whether to stream the API response.
        :param temperature: The temperature parameter for randomness in the output.
        :param max_tokens: The maximum number of tokens in the generated completion.
        :param top_p: The top-p parameter for nucleus sampling.
        :param kwargs: Additional keyword arguments to pass to the OpenAI API.
        :return: A tuple containing a list of generated completions and the estimated cost.
        :raises: Exception if there is an error in the OpenAI API request
        """
        model = self.config_llm["API_MODEL"]
        temperature = temperature if temperature is not None else self.config["TEMPERATURE"]
        max_tokens = max_tokens if max_tokens is not None else self.config["MAX_TOKENS"]
        top_p = top_p if top_p is not None else self.config["TOP_P"]

        try:
            payload = {
                "model": model,
                "messages": messages,
                "n": n,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "stream": stream,
                **kwargs,
            }

            response: Any = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )          

            if response.status_code != 200:
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")
            
            result = response.json()

            usage = result['usage']
            prompt_tokens = usage['prompt_tokens']
            completion_tokens = usage['completion_tokens']

            cost = self.get_cost_estimator(
                self.api_type, model, self.prices, prompt_tokens, completion_tokens
            )

            return [result['choices'][i]['message']['content'] for i in range(n)], cost

        except requests.RequestException as e:
            raise Exception(f"Failed to connect to AOAI Proxy: {str(e)}")
        except Exception as e:
            raise Exception(f"Error in AOAI Proxy request: {str(e)}")

    

