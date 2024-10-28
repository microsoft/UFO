# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import abc
from importlib import import_module
from typing import Dict


class BaseService(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def chat_completion(self, *args, **kwargs):
        pass

    @staticmethod
    def get_service(name: str) -> "BaseService":
        """
        Get the service class based on the name.
        :param name: The name of the service.
        :return: The service class.
        """
        service_map = {
            "openai": "OpenAIService",
            "aoai": "OpenAIService",
            "azure_ad": "OpenAIService",
            "qwen": "QwenService",
            "ollama": "OllamaService",
            "gemini": "GeminiService",
            "placeholder": "PlaceHolderService",
        }
        service_name = service_map.get(name, None)
        if service_name:
            if name in ["aoai", "azure_ad"]:
                module = import_module(".openai", package="ufo.llm")
            else:
                module = import_module("." + name.lower(), package="ufo.llm")
        else:
            raise ValueError(f"Service {name} not found.")
        return getattr(module, service_name)

    def get_cost_estimator(
        self,
        api_type: str,
        model: str,
        prices: Dict[str, float],
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Calculates the cost estimate for using a specific model based on the number of prompt tokens and completion tokens.
        :param api_type: The type of api used.
        :param model: The name of the model.
        :param prices: A dictionary containing the prices for different models.
        :param prompt_tokens: The number of prompt tokens used.
        :param completion_tokens: The number of completion tokens used.
        :return: The estimated cost for using the model.
        """

        if api_type.lower() == "openai":
            name = str(api_type + "/" + model)
        elif api_type.lower() in ["aoai", "azure_ad"]:
            name = str("azure/" + model)
        elif api_type.lower() == "qwen":
            name = str("qwen/" + model)
        elif api_type.lower() == "gemini":
            name = str("gemini/" + model)

        if name in prices:
            cost = (
                prompt_tokens * prices[name]["input"] / 1000
                + completion_tokens * prices[name]["output"] / 1000
            )
        else:
            return 0
        return cost
