from typing import Optional

from fastapi import WebSocket

from ufo.config import Config
from ufo.module.sessions.session import Session
from ufo.module.context import ContextNames
from ufo.module.message import WebSocketMessageBus


configs = Config.get_instance().config_data


class ServiceSession(Session):
    """
    A session for UFO service.
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
        Initialize the session.
        :param task: The task name for the session.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The ID of the session.
        :param request: The user request for the session.
        """

        super().__init__(task=task, should_evaluate=should_evaluate, id=id)

        self._init_request = request
        self.websocket = websocket

    def _init_context(self) -> None:
        """
        Initialize the context.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, "normal")
        message_bus = WebSocketMessageBus(self, self.websocket)
        self.context.attach_message_bus(self, message_bus)

    def next_request(self) -> str:
        """
        Get the next request for the session.
        :return: The next request for the session.
        """

        if self.total_rounds != 0:
            self._finish = True

        return self._init_request
