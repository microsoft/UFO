# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from ..config.config import load_llm_config


configs = load_llm_config()


def get_gptv_completion(messages, is_visual=True):
    from .openai import OpenAIService
    return OpenAIService(configs, is_visual=is_visual).chat_completion(messages)
