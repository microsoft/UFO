# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import logging
from ufo.llm import AgentType
from typing import Tuple

from .base import BaseService
from .config_helper import get_agent_config

logger = logging.getLogger(__name__)


def get_completion(
    messages,
    agent: str = AgentType.APP,
    use_backup_engine: bool = True,
    configs: dict = {},
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
    agent: str = AgentType.APP,
    use_backup_engine: bool = True,
    n: int = 1,
    configs: dict = {},
) -> Tuple[list, float]:
    """
    Get completions for the given messages.
    :param messages: List of messages to be used for completion.
    :param agent: Type of agent. Possible values are 'hostagent', 'appagent' or 'backup'.
    :param use_backup_engine: Flag indicating whether to use the backup engine or not.
    :param n: Number of completions to generate.
    :param configs: (Deprecated) Legacy configs dict. If empty, will use new config system.
    :return: A tuple containing the completion responses and the cost.
    """

    if agent in [
        AgentType.HOST,
        AgentType.APP,
        AgentType.OPERATOR,
        AgentType.BACKUP,
        AgentType.CONSTELLATION,
    ]:
        agent_type = agent
    elif agent == AgentType.EVALUATION:
        # If evaluation agent is not in configs, use APP_AGENT as default.
        # Support both legacy configs dict and new config system
        if configs and AgentType.EVALUATION not in configs:
            agent_type = AgentType.APP
        elif not configs:
            # New config system - check if evaluation agent exists
            try:
                get_agent_config(AgentType.EVALUATION)
                agent_type = AgentType.EVALUATION
            except (ValueError, AttributeError):
                agent_type = AgentType.APP
        else:
            agent_type = AgentType.EVALUATION
    elif agent.lower() == "prefill":
        agent_type = AgentType.PREFILL
    elif agent.lower() == "filter":
        agent_type = AgentType.FILTER
    else:
        raise ValueError(f"Agent {agent} not supported")

    # Use new config system if configs parameter is empty (default behavior)
    # Otherwise use legacy configs for backward compatibility
    if not configs:
        agent_config = get_agent_config(agent_type)
        api_type = agent_config["API_TYPE"]
        api_model = agent_config["API_MODEL"]
    else:
        # Legacy mode - use provided configs dict
        api_type = configs[agent_type]["API_TYPE"]
        api_model = configs[agent_type]["API_MODEL"]

    try:
        api_type_lower = api_type.lower()
        service = BaseService.get_service(api_type_lower, agent_type, api_model.lower())
        if service:
            response, cost = service.chat_completion(messages, n)
            return response, cost
        else:
            raise ValueError(f"API_TYPE {api_type} not supported")
    except Exception as e:
        if use_backup_engine:
            logger.error(f"The API request of {agent_type} failed: {e}.")
            logger.warning(f"Switching to use the backup engine...")
            return get_completions(
                messages,
                agent=AgentType.BACKUP,
                use_backup_engine=False,
                n=n,
                configs=configs,
            )
        else:
            raise e
