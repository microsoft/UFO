# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Mobile Android-specific session implementations.
This module provides session types for Android mobile platform that don't require a HostAgent.
"""

import logging
from typing import Optional, TYPE_CHECKING

from ufo.client.mcp.mcp_server_manager import MCPServerManager
from config.config_loader import get_ufo_config
from ufo.module import interactor
from ufo.module.basic import BaseRound
from ufo.module.context import ContextNames
from ufo.module.dispatcher import LocalCommandDispatcher, WebSocketCommandDispatcher
from ufo.module.sessions.platform_session import MobileBaseSession

if TYPE_CHECKING:
    from aip.protocol.task_execution import TaskExecutionProtocol

ufo_config = get_ufo_config()


class MobileSession(MobileBaseSession):
    """
    A session for UFO on Android mobile platform.
    Unlike Windows sessions, Mobile sessions don't use a HostAgent.
    They work directly with MobileAgent for device control.
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
        Initialize a Mobile session.
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
        Initialize the context for Mobile session.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, self._mode)

        # Initialize Mobile-specific command dispatcher
        mcp_server_manager = MCPServerManager()
        command_dispatcher = LocalCommandDispatcher(self, mcp_server_manager)
        self.context.attach_command_dispatcher(command_dispatcher)

    def create_new_round(self) -> Optional[BaseRound]:
        """
        Create a new round for Mobile session.
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
        Get the request for the mobile agent.
        :return: The request for the mobile agent.
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
        # For Mobile session, collect requests from all rounds
        if self.current_round and hasattr(self.current_round.agent, "blackboard"):
            request_memory = self.current_round.agent.blackboard.requests
            return request_memory.to_json()
        return self._init_request


class MobileServiceSession(MobileSession):
    """
    A session for UFO service on Android mobile platform.
    Similar to Windows ServiceSession but without HostAgent - works directly with MobileAgent.
    Communicates via AIP protocols for remote control and monitoring.
    This enables server-client architecture for mobile device control.
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
        Initialize the Mobile service session.
        :param task: The task name for the session.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The ID of the session.
        :param request: The user request for the session.
        :param task_protocol: AIP TaskExecutionProtocol instance for remote communication.
        """
        self.task_protocol = task_protocol
        super().__init__(
            task=task, should_evaluate=should_evaluate, id=id, request=request
        )

    def _init_context(self) -> None:
        """
        Initialize the context for Mobile service session.
        Uses WebSocket-based dispatcher for remote communication.
        """
        super()._init_context()

        # Use WebSocket dispatcher for service mode (server-client communication)
        command_dispatcher = WebSocketCommandDispatcher(
            self, protocol=self.task_protocol
        )
        self.context.attach_command_dispatcher(command_dispatcher)
