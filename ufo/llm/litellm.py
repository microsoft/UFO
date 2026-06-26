# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from ufo.llm.base import BaseService

logger = logging.getLogger(__name__)


class LiteLLMService(BaseService):
    """
    A service class for LiteLLM — access 100+ LLM providers
    (OpenAI, Anthropic, Google, Azure, Bedrock, Cohere, Mistral, etc.)
    through a single unified interface.

    Models are specified with provider-prefixed names, e.g.:
        anthropic/claude-sonnet-4-6
        openai/gpt-4o
        gemini/gemini-2.5-pro
        bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
    """

    def __init__(self, config: Dict[str, Any], agent_type: str):
        """
        Initialize the LiteLLM service.
        :param config: The configuration dictionary.
        :param agent_type: The agent type.
        """
        self.config_llm = config[agent_type]
        self.config = config
        self.model = self.config_llm["API_MODEL"]
        self.prices = self.config.get("PRICES", {})
        self.max_retry = self.config.get("MAX_RETRY", 3)
        self.api_type = self.config_llm["API_TYPE"].lower()

        self.api_key = self.config_llm.get("API_KEY", "")
        self.api_base = self.config_llm.get("API_BASE", "")

        try:
            import litellm  # noqa: F401
        except ImportError:
            raise ImportError(
                "litellm is not installed. "
                "Install with: pip install litellm>=1.80,<1.87"
            )

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        n: int = 1,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ) -> Tuple[List[str], Optional[float]]:
        """
        Generates completions using LiteLLM (100+ providers).
        :param messages: The list of messages in the conversation.
        :param n: The number of completions to generate.
        :param temperature: The temperature parameter for randomness.
        :param max_tokens: The maximum number of tokens in the response.
        :param top_p: The top-p parameter for nucleus sampling.
        :param kwargs: Additional keyword arguments.
        :return: A tuple of (list of response strings, estimated cost).
        """
        import litellm

        temperature = (
            temperature if temperature is not None else self.config.get("TEMPERATURE", 0.0)
        )
        max_tokens = (
            max_tokens if max_tokens is not None else self.config.get("MAX_TOKENS", 2000)
        )

        responses = []
        cost = 0.0

        call_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "drop_params": True,
            **kwargs,
        }
        if self.api_key:
            call_kwargs["api_key"] = self.api_key
        if self.api_base:
            call_kwargs["api_base"] = self.api_base

        for _ in range(n):
            for attempt in range(self.max_retry):
                try:
                    response = litellm.completion(**call_kwargs)
                    content = response.choices[0].message.content or ""
                    responses.append(content)

                    usage = getattr(response, "usage", None)
                    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                    completion_tokens = getattr(usage, "completion_tokens", 0) or 0

                    cost += self.get_cost_estimator(
                        self.api_type,
                        self.model,
                        self.prices,
                        prompt_tokens,
                        completion_tokens,
                    )
                    break
                except Exception as e:
                    qualname = f"{type(e).__module__}.{type(e).__name__}"
                    is_transient = qualname in {
                        "litellm.exceptions.RateLimitError",
                        "litellm.exceptions.APIConnectionError",
                        "litellm.exceptions.Timeout",
                        "litellm.exceptions.InternalServerError",
                        "litellm.exceptions.ServiceUnavailableError",
                    }
                    if not is_transient or attempt >= self.max_retry - 1:
                        logger.error(f"LiteLLM API error: {e}")
                        raise
                    logger.warning(
                        f"LiteLLM transient error (attempt {attempt + 1}/{self.max_retry}): {e}"
                    )
                    time.sleep(2**attempt)

        return responses, cost
