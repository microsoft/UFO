import base64
import copy
import io

import time
from typing import Any, Optional, Dict, List

import requests
from PIL import Image

from ufo.utils import print_with_color

from .openai import BaseOpenAIService


class OllamaService(BaseOpenAIService):
    """
    A service class for Ollama models.
    """

    def __init__(self, config, agent_type: str):
        """
        Initialize the Ollama service.
        :param config: The configuration.
        :param agent_type: The agent type.
        """
        base_url = config[agent_type]["API_BASE"]
        config[agent_type]["API_KEY"] = "ollama"
        super().__init__(config, agent_type, "openai", f"{base_url}/v1")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        n: int = 1,
        stream: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generates completions for a given conversation using the Ollama API.
        :param messages: The list of messages in the conversation.
        :param n: The number of completions to generate.
        :param stream: Whether to stream the API response.
        :param temperature: The temperature parameter for randomness in the output.
        :param max_tokens: The maximum number of tokens in the generated completion.
        :param top_p: The top-p parameter for nucleus sampling.
        :param kwargs: Additional keyword arguments to pass to the OpenAI API.
        :return: A tuple containing a list of generated completions and the estimated cost.
        """
        return super()._chat_completion(
            messages,
            False,
            temperature,
            max_tokens,
            top_p,
            response_format={"type": "json_object"},
            **kwargs,
        )
