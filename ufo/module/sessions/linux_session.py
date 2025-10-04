# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Linux-specific session implementations.
This module provides session types for Linux platform that don't require a HostAgent.
"""

import logging
from typing import Optional

from fastapi import WebSocket

from ufo.agents.agent.host_agent import AgentFactory
from ufo.client.mcp.mcp_server_manager import MCPServerManager
from ufo.config import Config
from ufo.module import interactor
from ufo.module.basic import BaseRound
from ufo.module.context import ContextNames
from ufo.module.dispatcher import LocalCommandDispatcher, WebSocketCommandDispatcher
from ufo.module.sessions.platform_session import LinuxBaseSession

configs = Config.get_instance().config_data


class LinuxSession(LinuxBaseSession):
    """
    A session for UFO on Linux platform.
    Unlike Windows sessions, Linux sessions don't use a HostAgent.
    They work directly with application agents.
    """

    def __init__(
        self,
        task: str,
        should_evaluate: bool,
        id: int,
        request: str = "",
        mode: str = "normal",
        application_name: str = None,
    ) -> None:
        """
        Initialize a Linux session.
        :param task: The name of current task.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The id of the session.
        :param request: The user request of the session.
        :param mode: The mode of the task.
        :param application_name: The target application name for Linux.
        """
        self._mode = mode
        self._init_request = request
        self._application_name = application_name
        super().__init__(task, should_evaluate, id)
        self.logger = logging.getLogger(__name__)

    def _init_context(self) -> None:
        """
        Initialize the context for Linux session.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, self._mode)
        self.context.set(ContextNames.PLATFORM, "linux")

        # Initialize Linux-specific command dispatcher
        mcp_server_manager = MCPServerManager()
        command_dispatcher = LocalCommandDispatcher(self, mcp_server_manager)
        self.context.attach_command_dispatcher(command_dispatcher)

        # Set application context if provided
        if self._application_name:
            self.context.set(
                ContextNames.APPLICATION_PROCESS_NAME, self._application_name
            )
            self.context.set(ContextNames.APPLICATION_ROOT_NAME, self._application_name)

    def create_new_round(self) -> Optional[BaseRound]:
        """
        Create a new round for Linux session.
        Since there's no host agent, directly create app-level rounds.
        """
        request = self.next_request()

        if self.is_finished():
            return None

        # Create app agent directly without host agent
        app_agent = AgentFactory.create_agent(
            "app",
            name="LinuxAppAgent",
            process_name=self.context.get(ContextNames.APPLICATION_PROCESS_NAME),
            app_root_name=self.context.get(ContextNames.APPLICATION_ROOT_NAME),
            is_visual=configs["APP_AGENT"]["VISUAL_MODE"],
            main_prompt=configs["APPAGENT_PROMPT"],
            example_prompt=configs["APPAGENT_EXAMPLE_PROMPT"],
            api_prompt=configs["API_PROMPT"],
        )

        app_agent.set_state(app_agent.default_state)

        round = BaseRound(
            request=request,
            agent=app_agent,
            context=self.context,
            should_evaluate=configs.get("EVA_ROUND", False),
            id=self.total_rounds,
        )

        self.add_round(round.id, round)
        return round

    def next_request(self) -> str:
        """
        Get the request for the app agent.
        :return: The request for the app agent.
        """
        if self.total_rounds == 0:
            if self._init_request:
                return self._init_request
            else:
                return interactor.first_request()
        else:
            request, iscomplete = interactor.new_request()
            if iscomplete:
                self._finish = True
            return request

    def request_to_evaluate(self) -> str:
        """
        Get the request to evaluate.
        :return: The request(s) to evaluate.
        """
        # For Linux session, collect requests from all rounds
        if self.current_round and hasattr(self.current_round.agent, "blackboard"):
            request_memory = self.current_round.agent.blackboard.requests
            return request_memory.to_json()
        return self._init_request

    async def run(self) -> None:
        """
        Run the Linux session.
        """
        await super().run()

        # Linux-specific post-processing
        save_experience = configs.get("SAVE_EXPERIENCE", "always_not")

        if save_experience == "always":
            self.experience_saver()
        elif save_experience == "ask":
            if interactor.experience_asker():
                self.experience_saver()
        elif save_experience == "auto":
            task_completed = self.results.get("complete", "no")
            if task_completed.lower() == "yes":
                self.experience_saver()


class LinuxServiceSession(LinuxBaseSession):
    """
    A session for UFO service on Linux platform.
    Similar to Windows ServiceSession but without HostAgent - works directly with application agents.
    Communicates via WebSocket for remote control and monitoring.
    """

    def __init__(
        self,
        task: str,
        should_evaluate: bool,
        id: str = None,
        request: str = "",
        websocket: Optional[WebSocket] = None,
    ):
        """
        Initialize the Linux service session.
        :param task: The task name for the session.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The ID of the session.
        :param request: The user request for the session.
        :param websocket: WebSocket connection for service communication.
        """
        self.websocket = websocket
        self._init_request = request
        super().__init__(task=task, should_evaluate=should_evaluate, id=id)

    def _init_context(self) -> None:
        """
        Initialize the context for Linux service session.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, "service")

        # Use WebSocket command dispatcher for service mode
        command_dispatcher = WebSocketCommandDispatcher(self, self.websocket)
        self.context.attach_command_dispatcher(command_dispatcher)

    def create_new_round(self) -> Optional[BaseRound]:
        """
        Create a new round for Linux service session.
        """
        request = self.next_request()

        if self.is_finished():
            return None

        # Create app agent directly without host agent
        app_agent = AgentFactory.create_agent(
            "app",
            name="LinuxServiceAppAgent",
            process_name=self.context.get(ContextNames.APPLICATION_PROCESS_NAME),
            app_root_name=self.context.get(ContextNames.APPLICATION_ROOT_NAME),
            is_visual=configs["APP_AGENT"]["VISUAL_MODE"],
            main_prompt=configs["APPAGENT_PROMPT"],
            example_prompt=configs["APPAGENT_EXAMPLE_PROMPT"],
            api_prompt=configs["API_PROMPT"],
        )

        app_agent.set_state(app_agent.default_state)

        round = BaseRound(
            request=request,
            agent=app_agent,
            context=self.context,
            should_evaluate=configs.get("EVA_ROUND", False),
            id=self.total_rounds,
        )

        self.add_round(round.id, round)
        return round

    def next_request(self) -> str:
        """
        Get the next request for the session.
        For service mode, only process the initial request.
        :return: The next request for the session.
        """
        if self.total_rounds != 0:
            self._finish = True

        return self._init_request

    def request_to_evaluate(self) -> str:
        """
        Get the request to evaluate.
        :return: The request(s) to evaluate.
        """
        # For Linux service session, return the initial request
        if self.current_round and hasattr(self.current_round.agent, "blackboard"):
            request_memory = self.current_round.agent.blackboard.requests
            return request_memory.to_json()
        return self._init_request
