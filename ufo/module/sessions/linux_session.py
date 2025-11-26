# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Linux-specific session implementations.
This module provides session types for Linux platform that don't require a HostAgent.
"""

import logging
from typing import Optional, TYPE_CHECKING

from ufo.client.mcp.mcp_server_manager import MCPServerManager
from config.config_loader import get_ufo_config
from ufo.module import interactor
from ufo.module.basic import BaseRound
from ufo.module.context import ContextNames
from ufo.module.dispatcher import LocalCommandDispatcher, WebSocketCommandDispatcher
from ufo.module.sessions.platform_session import LinuxBaseSession

if TYPE_CHECKING:
    from aip.protocol.task_execution import TaskExecutionProtocol

ufo_config = get_ufo_config()


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
    ) -> None:
        """
        Initialize a Linux session.
        :param task: The name of current task.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The id of the session.
        :param request: The user request of the session.
        :param mode: The mode of the task.
        """
        self._mode = mode
        self._init_request = request
        super().__init__(task, should_evaluate, id)
        self.logger = logging.getLogger(__name__)

    def _init_context(self) -> None:
        """
        Initialize the context for Linux session.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, self._mode)

        # Initialize Linux-specific command dispatcher
        mcp_server_manager = MCPServerManager()
        command_dispatcher = LocalCommandDispatcher(self, mcp_server_manager)
        self.context.attach_command_dispatcher(command_dispatcher)

    def create_new_round(self) -> Optional[BaseRound]:
        """
        Create a new round for Linux session.
        Since there's no host agent, directly create app-level rounds.
        """
        request = self.next_request()

        if self.is_finished():
            return None

        round = BaseRound(
            request=request,
            agent=self._agent,
            context=self.context,
            should_evaluate=ufo_config.system.eva_round,
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


class LinuxServiceSession(LinuxSession):
    """
    A session for UFO service on Linux platform.
    Similar to Windows ServiceSession but without HostAgent - works directly with application agents.
    Communicates via AIP protocols for remote control and monitoring.
    """

    def __init__(
        self,
        task: str,
        should_evaluate: bool,
        id: str = None,
        request: str = "",
        task_protocol: Optional["TaskExecutionProtocol"] = None,
    ):
        """
        Initialize the Linux service session.
        :param task: The task name for the session.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The ID of the session.
        :param request: The user request for the session.
        :param task_protocol: AIP TaskExecutionProtocol instance.
        """
        self.task_protocol = task_protocol
        super().__init__(
            task=task, should_evaluate=should_evaluate, id=id, request=request
        )

    def _init_context(self) -> None:
        """
        Initialize the context for Linux service session.
        """
        super()._init_context()

        command_dispatcher = WebSocketCommandDispatcher(
            self, protocol=self.task_protocol
        )
        self.context.attach_command_dispatcher(command_dispatcher)
