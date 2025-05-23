import functools
import base64
import re
import time
import random
from typing import Any, Dict, List, Optional

from google import genai
from google.genai.types import GenerateContentConfig, Part, GenerateContentResponse

from ufo.llm.base import BaseService
from ufo.utils import print_with_color


class GeminiService(BaseService):
    """
    A service class for Gemini models.
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
        self.client = GeminiService.get_gemini_client(
            api_key=self.config_llm["API_KEY"],
        )

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
        :return: A list of generated completions for each message and the estimated cost.
        """

        temperature = (
            temperature if temperature is not None else self.config["TEMPERATURE"]
        )
        top_p = top_p if top_p is not None else self.config["TOP_P"]
        max_tokens = max_tokens if max_tokens is not None else self.config["MAX_TOKENS"]
        genai_config = GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            response_mime_type='application/json',
        )

        processed_messages = self.process_messages(messages)

        # Default parameters from OpenAI
        # Ref: _calculate_retry_timeout from https://github.com/openai/openai-python/blob/main/src/openai/_base_client.pys
        initial_delay = 0.5
        max_delay = 8.0
        jitter_factor = 0.25

        for attempt in range(self.max_retry):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=processed_messages,
                    config=genai_config,
                )
                prompt_tokens = response.usage_metadata.prompt_token_count
                completion_tokens = response.usage_metadata.candidates_token_count
                cost = self.get_cost_estimator(
                    self.api_type,
                    self.model,
                    self.prices,
                    prompt_tokens,
                    completion_tokens,
                )
                break
            except Exception as e:
                # Calculate backoff with jitter
                delay = min(initial_delay * (2 ** attempt), max_delay)
                jitter = random.uniform(-jitter_factor * delay, 0)
                sleep_time = delay + jitter
                print_with_color(
                    f"Error during Gemini API request, attempt {attempt+1}/{self.max_retry}: {e}. "
                    f"Retrying in {sleep_time:.2f}s...", 
                    "yellow"
                )
                time.sleep(sleep_time)

        return self.get_text_from_all_candidates(response), cost

    def process_messages(self, messages: List[Dict[str, str]]) -> List[str]:
        """
        Process the given messages and extract prompts from them.
        :param messages: The messages to process.
        :return: A list of prompts extracted from the messages.
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
                        prompt = self.base64_to_blob(content["image_url"]["url"])
                        prompt_contents.append(Part.from_bytes(data=prompt["data"], mime_type=prompt["mime_type"]))
        return prompt_contents

    def base64_to_blob(self, base64_str: str) -> Dict[str, str]:
        """
        Converts a base64 encoded image string to MIME type and binary data.
        :param base64_str: The base64 encoded image string.
        :return: A dictionary containing the MIME type and binary data.
        """

        match = re.match(r'data:(?P<mime_type>image/.+?);base64,(?P<base64_string>.+)', base64_str)

        if match:
            mime_type = match.group('mime_type')
            base64_string = match.group('base64_string')
        else:
            print("Error: Could not parse the data URL.")
            raise ValueError("Invalid data URL format.")

        return {
            "mime_type": mime_type,
            "data": base64.b64decode(base64_string)
        }

    def get_text_from_all_candidates(self, response: GenerateContentResponse) -> List[Optional[str]]:
        """
        Extracts the concatenated text content from each candidate in the response.

        Args:
            response: The GenerateContentResponse object from the Gemini API call.

        Returns:
            A list where each element is the concatenated text from a candidate,
            or None if a candidate has no text parts.
        """
        all_texts = []
        if (
            not response
            or not response.candidates
        ):
            print("Warning: Response object does not contain candidates.")
            return all_texts

        for i, candidate in enumerate(response.candidates):
            candidate_text: str = ''
            any_text_part_found: bool = False
            non_text_parts_found: List[str] = []

            if (
                not candidate
                or not candidate.content
                or not candidate.content.parts
            ):
                # Handle cases where a candidate might be empty (e.g., safety blocked)
                print(f"Warning: Candidate {i} has no content or parts. Finish Reason: {getattr(candidate, 'finish_reason', 'N/A')}")
                all_texts.append(None)
                continue

            for part in candidate.content.parts:
                # Check for non-text parts (similar to _get_text logic)
                for field_name, field_value in part.model_dump(exclude={'text', 'thought'}).items():
                    if field_value is not None:
                        if field_name not in non_text_parts_found: # Avoid duplicates
                            non_text_parts_found.append(field_name)

                # Check if the part has text and it's not just internal 'thought'
                if isinstance(part.text, str):
                    # Skip parts marked as internal 'thought' if the attribute exists
                    if isinstance(part.thought, bool) and part.thought:
                        continue
                    any_text_part_found = True
                    candidate_text += part.text

            if non_text_parts_found:
                print(
                    f'Warning: Candidate {i}: Contains non-text parts: {non_text_parts_found}. '
                    'Returning concatenated text from text parts only for this candidate.'
                )

            all_texts.append(candidate_text if any_text_part_found else None)

        return all_texts

    @functools.lru_cache()
    @staticmethod
    def get_gemini_client(api_key: str) -> genai.Client:
        """
        Create a Gemini client using the provided API key.
        :param api_key: The API key for authentication.
        :return: A Gemini client instance.
        """
        return genai.Client(
            api_key=api_key
        )
