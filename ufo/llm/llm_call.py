# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from ufo.utils import print_with_color
from ..config.config import load_config
from typing import Tuple

from .openai import OpenAIService
from .qwen import QwenService
from .ollama import OllamaService
from .cogagent import CogagentService
from .llava import LlavaService


configs = load_config()
host_service_map = {
    'openai': OpenAIService,
    'aoai': OpenAIService,
    'azure_ad': OpenAIService,
    'qwen': QwenService,
    'ollama': OllamaService,
}
customized_service_map = {
    'llava': LlavaService,
    'cogagent': CogagentService,
}

def get_completion(messages, agent: str='APP', use_backup_engine: bool=True) -> Tuple[str, float]:
    """
    Get completion for the given messages.

    Args:
        messages (list): List of messages to be used for completion.
        agent (str, optional): Type of agent. Possible values are 'hostagent', 'appagent' or 'BACKUP'.
        use_backup_engine (bool, optional): Flag indicating whether to use the backup engine or not.
        
    Returns:
        tuple: A tuple containing the completion response (str) and the cost (float).

    """
    
    responses, cost = get_completions(messages, agent=agent, use_backup_engine=use_backup_engine, n=1)
    return responses[0], cost

def customized_check(model_name):
    """
    Customized check function to determine the type of model based on the given model name.

    Args:
        model_name (str): The name of the model.

    Returns:
        str: The type of the model. If the model name contains 'llava', it returns 'llava'.
             If the model name contains 'cogagent', it returns 'cogagent'.
             Otherwise, it returns the original model name.
    """
    model_name = model_name.lower()
    if 'llava' in model_name:
        return 'llava'
    elif 'cogagent' in model_name:
        return 'cogagent'
    else:
        return model_name
    
def get_completions(messages, agent: str='APP', use_backup_engine: bool=True, n: int=1) -> Tuple[list, float]:
    """
    Get completions for the given messages.

    Args:
        messages (list): List of messages to be used for completion.
        agent (str, optional): Type of agent. Possible values are 'hostagent', 'appagent' or 'backup'.
        use_backup_engine (bool, optional): Flag indicating whether to use the backup engine or not.
        n (int, optional): Number of completions to generate.

    Returns:
        tuple: A tuple containing the completion responses (list of str) and the cost (float).

    """
    if agent.lower() in ["host", "hostagent"]:
        agent_type = "HOST_AGENT"
    elif agent.lower() in ["app", "appagent"]:
        agent_type = "APP_AGENT"
    elif agent.lower() == "backup":
        agent_type = "BACKUP_AGENT"
    else:
        raise ValueError(f'Agent {agent} not supported')
    api_type =  configs[agent_type]['API_TYPE']
    try:
        api_type_lower = api_type.lower()
        if api_type_lower in host_service_map:
            service = host_service_map[api_type_lower]
            response, cost = service(configs, agent_type=agent_type).chat_completion(messages)
            return response, cost
        elif api_type_lower == 'customized':
            service = customized_service_map[customized_check(configs[agent_type]['API_MODEL'])]
            response, cost = service(configs, agent_type=agent_type).chat_completion(messages)
            return response, cost
        else:
            raise ValueError(f'API_TYPE {api_type} not supported')
    except Exception as e:
        if use_backup_engine:
            print_with_color(f"The API request of {agent_type} failed: {e}.", "red")
            print_with_color(f"Switching to use the backup engine...", "yellow")
            return get_completion(messages, agent='backup', use_backup_engine=False, n=n)
        else:
            raise e