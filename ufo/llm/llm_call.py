# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Any, Dict, List, Tuple

from ufo.utils import print_with_color

from ..config.config import Config
from .base import BaseService

configs = Config.get_instance().config_data


def get_completion(
    messages, agent: str = "APP", use_backup_engine: bool = True, configs=configs
) -> Tuple[str, float]:
    """
    Get completion for the given messages.
    :param messages: List of messages to be used for completion.
    :param agent: Type of agent. Possible values are 'hostagent', 'appagent' or 'backup'.
    :param use_backup_engine: Flag indicating whether to use the backup engine or not.
    :return: A tuple containing the completion response and the cost.
    """

    responses, cost = get_completions(
        messages, agent=agent, use_backup_engine=use_backup_engine, n=1, configs=configs
    )
    return responses[0], cost


def get_completions(
    messages,
    agent: str = "APP",
    use_backup_engine: bool = True,
    n: int = 1,
    configs=configs,
) -> Tuple[list, float]:
    """
    Get completions for the given messages.
    :param messages: List of messages to be used for completion.
    :param agent: Type of agent. Possible values are 'hostagent', 'appagent' or 'backup'.
    :param use_backup_engine: Flag indicating whether to use the backup engine or not.
    :param n: Number of completions to generate.
    :return: A tuple containing the completion responses and the cost.
    """

    if agent.lower() in ["host", "hostagent"]:
        agent_type = "HOST_AGENT"
    elif agent.lower() in ["app", "appagent"]:
        agent_type = "APP_AGENT"
    elif agent.lower() in ["eva", "evaluation", "evaluationagent"]:
        # If evaluation agent is not in configs, use APP_AGENT as default.
        if "EVALUATION_AGENT" not in configs:
            agent_type = "APP_AGENT"
        else:
            agent_type = "EVALUATION_AGENT"
    elif agent.lower() in ["openaioperator", "openai_operator", "operator"]:
        agent_type = "OPERATOR"
    elif agent.lower() == "prefill":
        agent_type = "PREFILL_AGENT"
    elif agent.lower() == "filter":
        agent_type = "FILTER_AGENT"
    elif agent.lower() == "backup":
        agent_type = "BACKUP_AGENT"
    else:
        raise ValueError(f"Agent {agent} not supported")

    api_type = configs[agent_type]["API_TYPE"]
    try:
        api_type_lower = api_type.lower()
        service = BaseService.get_service(
            api_type_lower, configs[agent_type]["API_MODEL"].lower()
        )
        if service:
            response, cost = service(configs, agent_type=agent_type).chat_completion(
                messages, n
            )
            return response, cost
        else:
            raise ValueError(f"API_TYPE {api_type} not supported")
    except Exception as e:
        if use_backup_engine:
            print_with_color(f"The API request of {agent_type} failed: {e}.", "red")
            print_with_color(f"Switching to use the backup engine...", "yellow")
            return get_completions(
                messages, agent="backup", use_backup_engine=False, n=n
            )
        else:
            raise e
