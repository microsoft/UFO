from typing import Optional, TYPE_CHECKING

from config.config_loader import get_ufo_config
from ufo.module.sessions.platform_session import WindowsBaseSession
from ufo.module.context import ContextNames
from ufo.module.dispatcher import WebSocketCommandDispatcher
from ufo.module.sessions.session import Session

if TYPE_CHECKING:
    from aip.protocol.task_execution import TaskExecutionProtocol


ufo_config = get_ufo_config()


class ServiceSession(Session):
    """
    A session for UFO service on Windows platform.
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
        Initialize the session.
        :param task: The task name for the session.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The ID of the session.
        :param request: The user request for the session.
        :param task_protocol: AIP TaskExecutionProtocol instance.
        """

        self.task_protocol = task_protocol
        super().__init__(task=task, should_evaluate=should_evaluate, id=id)

        self._init_request = request

    def _init_context(self) -> None:
        """
        Initialize the context.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, "normal")
        command_dispatcher = WebSocketCommandDispatcher(
            self, protocol=self.task_protocol
        )
        self.context.attach_command_dispatcher(command_dispatcher)

    def next_request(self) -> str:
        """
        Get the next request for the session.
        :return: The next request for the session.
        """

        if self.total_rounds != 0:
            self._finish = True

        return self._init_request
