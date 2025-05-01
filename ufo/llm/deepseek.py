from typing import Any, Dict, List, Optional, Tuple

from ufo.llm.openai import BaseOpenAIService
from ufo.utils import print_with_color


class DeepSeekService(BaseOpenAIService):
    """
    A service class for DeepSeek models.
    """

    def __init__(self, config, agent_type: str):
        """
        :param config: The configuration.
        :param agent_type: The agent type.
        """
        super().__init__(config, agent_type, "openai", "https://api.deepseek.com/v1")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        n: int,
        stream: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ) -> Tuple[Dict[str, Any], Optional[float]]:
        """
        Generates completions for a given conversation using the Qwen thru OpenAI Chat API.
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

        return super()._chat_completion(
            messages,
            False,
            temperature,
            max_tokens,
            top_p,
            response_format={"type": "json_object"},
            **kwargs,
        )
