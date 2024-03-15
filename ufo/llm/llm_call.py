# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from ..config.config import load_llm_config


configs = load_llm_config()


def get_completion(messages, is_visual=True, index=1):
    api_type =  configs['VISUAL' if is_visual else 'NON_VISUAL'][index]['API_TYPE']
    if api_type.lower() in ['openai', 'aoai', 'azure_ad']:
        from .openai import OpenAIService
        return OpenAIService(configs, is_visual=is_visual, index=index).chat_completion(messages)
    else:
        raise ValueError(f'API_TYPE {api_type} not supported')