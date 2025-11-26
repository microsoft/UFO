# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Platform-specific base session classes.
This module provides base classes for Windows and Linux platforms,
allowing for platform-specific agent initialization and behavior.
"""

from typing import Optional

from ufo.agents.agent.customized_agent import LinuxAgent, MobileAgent
from ufo.agents.agent.host_agent import AgentFactory, HostAgent
from config.config_loader import get_ufo_config
from ufo.module.basic import BaseRound, BaseSession

ufo_config = get_ufo_config()


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
            ufo_config.host_agent.visual_mode,
            ufo_config.system.HOSTAGENT_PROMPT,
            ufo_config.system.HOSTAGENT_EXAMPLE_PROMPT,
            ufo_config.system.API_PROMPT,
        )

    def reset(self):
        """
        Reset the session state for a new session.
        This includes resetting the host agent and any other session-specific state.
        """
        self._host_agent.set_state(self._host_agent.default_state)


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
            ufo_config.system.third_party_agent_config["LinuxAgent"]["APPAGENT_PROMPT"],
            ufo_config.system.third_party_agent_config["LinuxAgent"][
                "APPAGENT_EXAMPLE_PROMPT"
            ],
        )

    def evaluation(self) -> None:
        """
        Evaluation logic for Linux sessions.
        """
        # Implement evaluation logic specific to Linux sessions
        self.logger.warning("Evaluation not yet implemented for Linux sessions.")
        pass

    def save_log_to_markdown(self) -> None:
        """
        Save the log of the session to markdown file.
        """
        # Implement markdown logging specific to Linux sessions
        self.logger.warning("Markdown logging not yet implemented for Linux sessions.")
        pass

    def reset(self) -> None:
        """
        Reset the session state for a new session.
        This includes resetting any Linux-specific agents and session state.
        """
        self._agent.set_state(self._agent.default_state)


class MobileBaseSession(BaseSession):
    """
    Base class for all Android mobile-based sessions.
    Mobile sessions don't use a HostAgent, working directly with MobileAgent.
    This provides a simpler, single-tier architecture for mobile device control.
    """

    def _init_agents(self) -> None:
        """
        Initialize Mobile-specific agents.
        Mobile sessions don't require a HostAgent - they work directly with MobileAgent.
        This method intentionally leaves _host_agent as None.
        """
        # No host agent for Mobile
        self._host_agent = None
        # Mobile-specific agent initialization
        self._agent: MobileAgent = AgentFactory.create_agent(
            "MobileAgent",
            "MobileAgent",
            ufo_config.system.third_party_agent_config["MobileAgent"][
                "APPAGENT_PROMPT"
            ],
            ufo_config.system.third_party_agent_config["MobileAgent"][
                "APPAGENT_EXAMPLE_PROMPT"
            ],
        )

    def evaluation(self) -> None:
        """
        Evaluation logic for Mobile sessions.
        """
        # Implement evaluation logic specific to Mobile sessions
        self.logger.warning("Evaluation not yet implemented for Mobile sessions.")
        pass

    def save_log_to_markdown(self) -> None:
        """
        Save the log of the session to markdown file.
        """
        # Implement markdown logging specific to Mobile sessions
        self.logger.warning("Markdown logging not yet implemented for Mobile sessions.")
        pass

    def reset(self) -> None:
        """
        Reset the session state for a new session.
        This includes resetting any Mobile-specific agents and session state.
        """
        self._agent.set_state(self._agent.default_state)
