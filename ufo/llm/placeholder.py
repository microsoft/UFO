from typing import Any, Optional

from ufo.llm.base import BaseService


class PlaceHolderService(BaseService):
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
        pass
