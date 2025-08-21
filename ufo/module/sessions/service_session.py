from typing import Optional

from fastapi import WebSocket

from ufo.agents.states.host_agent_state import ContinueHostAgentState
from ufo.config import Config
from ufo.module.basic import BaseRound, BaseSession
from ufo.module.context import ContextNames

configs = Config.get_instance().config_data


class ServiceSession(BaseSession):
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
        :param host_agent: The host agent.
        :param app_agent: The app agent.
        :param request: The request for the session.
        """

        super().__init__(task=task, should_evaluate=should_evaluate, id=id)

        self._init_request = request
        self.context.attach_message_bus(self, websocket)

    def _init_context(self) -> None:
        """
        Initialize the context.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, "normal")

    def create_new_round(self) -> Optional[BaseRound]:
        """
        Create a new round.
        """

        # Get a request for the new round.
        request = self.next_request()

        # Create a new round and return None if the session is finished.

        if self.is_finished():
            return None

        self._host_agent.set_state(ContinueHostAgentState())

        round = BaseRound(
            request=request,
            agent=self._host_agent,
            context=self.context,
            should_evaluate=configs.get("EVA_ROUND", False),
            id=self.total_rounds,
        )

        self.add_round(round.id, round)

        return round

    def next_request(self) -> str:
        """
        Get the next request for the session.
        :return: The next request for the session.
        """

        if self.total_rounds != 0:
            self._finish = True

        return self._init_request

    def request_to_evaluate(self) -> bool:
        """
        Check if the session should be evaluated.
        :return: True if the session should be evaluated, False otherwise.
        """
        request_memory = self._host_agent.blackboard.requests
        return request_memory.to_json()
