# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from ufo.utils import print_with_color
from ..config.config import load_config


configs = load_config()


def get_completion(messages, is_visual=True, agent: str='APP', backup_engine: bool=True):
    """
    Get completion for the given messages.

    Args:
        messages (list): List of messages to be used for completion.
        is_visual (bool, optional): Flag indicating whether the completion is visual or not. 
        agent (str, optional): Type of agent. Possible values are 'APP', 'ACTION' or 'BACKUP'.
        backup_engine (bool, optional): Flag indicating whether to use the backup engine or not.

    Returns:
        tuple: A tuple containing the completion response (str) and the cost (float).

    """
    if agent.lower() == "app":
        agent_type = "APP_AGENT"
    elif agent.lower() == "action":
        agent_type = "ACTION_AGENT"
    elif agent.lower() == "backup":
        agent_type = "BACKUP_AGENT"
    else:
        raise ValueError(f'Agent {agent} not supported')
    
    api_type =  configs[agent_type]['VISUAL' if is_visual else 'NON_VISUAL']['API_TYPE']
    if api_type.lower() in ['openai', 'aoai', 'azure_ad']:
        from .openai import OpenAIService
        try:
            response, cost = OpenAIService(configs, is_visual=is_visual, agent_type=agent_type).chat_completion(messages)
        except Exception as e:
            if backup_engine:
                print_with_color(f"OpenAI API request failed: {e}, try to use the backup engine", "red")
                return get_completion(messages, is_visual=is_visual, agent='backup', backup_engine=False)
            else:
                raise e
        return response, cost
    else:
        raise ValueError(f'API_TYPE {api_type} not supported')