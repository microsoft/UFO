from typing import Any, Dict, List, Optional

from ufo.llm.base import BaseService


class PlaceHolderService(BaseService):
    """
    A placeholder service class.
    """

    def __init__(self, config: Dict[str, Any], agent_type: str):
        """
        Initialize the placeholder service.
        :param config: The configuration.
        :param agent_type: The agent type.
        """
        self.config_llm = config[agent_type]
        self.config = config
        self.max_retry = self.config["MAX_RETRY"]
        self.timeout = self.config["TIMEOUT"]

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        n: int = 1,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
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
        pass
