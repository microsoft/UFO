# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from ufo.utils import print_with_color
from ..config.config import load_config


configs = load_config()


def get_completion(messages, agent: str='APP', use_backup_engine: bool=True):
    """
    Get completion for the given messages.

    Args:
        messages (list): List of messages to be used for completion.
        agent (str, optional): Type of agent. Possible values are 'APP', 'ACTION' or 'BACKUP'.
        use_backup_engine (bool, optional): Flag indicating whether to use the backup engine or not.

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
    
    api_type =  configs[agent_type]['API_TYPE']
    try:
        if api_type.lower() in ['openai', 'aoai', 'azure_ad']:
            from .openai import OpenAIService
            response, cost = OpenAIService(configs, agent_type=agent_type).chat_completion(messages)
            return response, cost
        else:
            raise ValueError(f'API_TYPE {api_type} not supported')
    except Exception as e:
        if use_backup_engine:
            print_with_color(f"The API request of {agent_type} failed: {e}, try to use the backup engine", "red")
            return get_completion(messages, agent='backup', use_backup_engine=False)
        else:
            raise e