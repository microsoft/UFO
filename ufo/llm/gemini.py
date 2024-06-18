import time
from typing import Any, Optional

import google.generativeai as genai
from ufo.llm.base import BaseService
from ufo.utils import print_with_color


class GeminiService(BaseService):
    def __init__(self, config, agent_type: str):
        self.config_llm = config[agent_type]
        self.config = config
        self.model = self.config_llm["API_MODEL"]
        self.prices = self.config["PRICES"]
        self.max_retry = self.config['MAX_RETRY']
        self.api_type = self.config_llm["API_TYPE"].lower()
        genai.configure(api_key = self.config_llm["API_KEY"])

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
        top_p = top_p if top_p is not None else self.config["TOP_P"]
        max_tokens = max_tokens if max_tokens is not None else self.config["MAX_TOKENS"]
        genai_config = genai.GenerationConfig(candidate_count = n, max_output_tokens = max_tokens, temperature = temperature, \
            top_p = top_p, response_mime_type = "application/json")
        self.client = genai.GenerativeModel(self.model, generation_config=genai_config)
        
        responses = []
        cost = 0.0
        
        for _ in range(n):
            for _ in range(self.max_retry):
                try:
                    response = self.client.generate_content(
                        self.process_messages(messages),
                    )
                    responses.append(response.text)
                    prompt_tokens = response.usage_metadata.prompt_token_count
                    completion_tokens = response.usage_metadata.candidates_token_count
                    cost += self.get_cost_estimator(
                        self.api_type, self.model, self.prices, prompt_tokens, completion_tokens
                        )
                except Exception as e:
                    print_with_color(f"Error making API request: {e}", "red")
                    try:
                        print_with_color(response, "red")
                    except:
                        _
                    time.sleep(3)
                    continue

        return responses, cost

    def process_messages(self, messages):
        """
        Process the given messages and extract prompts from them.

        Args:
            messages (list or dict): The messages to process. If a dictionary is provided, it will be converted to a list.

        Returns:
            list: A list of prompts extracted from the messages.

        """
        prompt_contents = []

        if isinstance(messages, dict):
            messages = [messages]
        for message in messages:
            if message["role"] == "system":
                prompt = f"Your general instruction: {message['content']}"
                prompt_contents.append(prompt)
            else:
                for content in message["content"]:
                    if content["type"] == "text":
                        prompt = content["text"]
                        prompt_contents.append(prompt)
                    elif content["type"] == "image_url":
                        prompt = self.base64_to_image(content["image_url"]["url"])
                        prompt_contents.append(prompt)
        return prompt_contents
            
            