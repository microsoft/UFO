# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Platform-specific base session classes.
This module provides base classes for Windows and Linux platforms,
allowing for platform-specific agent initialization and behavior.
"""

from typing import Optional

from ufo.agents.agent.customized_agent import LinuxAgent
from ufo.agents.agent.host_agent import AgentFactory, HostAgent
from ufo.config import Config
from ufo.module.basic import BaseRound, BaseSession

configs = Config.get_instance().config_data


class WindowsBaseSession(BaseSession):
    """
    Base class for all Windows-based sessions.
    Provides Windows-specific functionality like HostAgent initialization.
    Windows sessions use a two-tier architecture: HostAgent -> AppAgent.
    """

    def _init_agents(self) -> None:
        """
        Initialize Windows-specific agents, including the HostAgent.
        The HostAgent is responsible for task planning and coordination in Windows sessions.
        """
        self._host_agent: HostAgent = AgentFactory.create_agent(
            "host",
            "HostAgent",
            configs["HOST_AGENT"]["VISUAL_MODE"],
            configs["HOSTAGENT_PROMPT"],
            configs["HOSTAGENT_EXAMPLE_PROMPT"],
            configs["API_PROMPT"],
        )


class LinuxBaseSession(BaseSession):
    """
    Base class for all Linux-based sessions.
    Linux sessions don't use a HostAgent, working directly with application agents.
    This provides a simpler, single-tier architecture for Linux environments.
    """

    def _init_agents(self) -> None:
        """
        Initialize Linux-specific agents.
        Linux sessions don't require a HostAgent - they work directly with AppAgents.
        This method intentionally leaves _host_agent as None.
        """
        # No host agent for Linux
        self._host_agent = None
        # Linux-specific agent initialization can be added here if needed
        self._agent: LinuxAgent = AgentFactory.create_agent(
            "LinuxAgent",
            "LinuxAgent",
            configs["THIRD_PARTY_AGENT_CONFIG"]["LinuxAgent"]["APPAGENT_PROMPT"],
            configs["THIRD_PARTY_AGENT_CONFIG"]["LinuxAgent"][
                "APPAGENT_EXAMPLE_PROMPT"
            ],
        )
