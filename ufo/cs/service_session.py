
from ufo.agents.states.host_agent_state import ContinueHostAgentState
from ufo.config.config import Config
from ufo.cs.contracts import ActionBase
from ufo.cs.session_data import SessionDataManager
from ufo.module.basic import BaseRound, BaseSession
from ufo.module.context import ContextNames


configs = Config.get_instance().config_data

class ServiceSession(BaseSession):
    """
    A session for UFO service.
    """
    def __init__(self, task: str, should_evaluate: bool, id: str = None):
        """
        Initialize the session.
        :param host_agent: The host agent.
        :param app_agent: The app agent.
        :param request: The request for the session.
        """
        
        super().__init__(task=task, should_evaluate=should_evaluate, id=id)

    def init(self, request):
        self._host_agent.set_state(ContinueHostAgentState())

        round = BaseRound(
            request=request,
            agent=self._host_agent,
            context=self.context,
            should_evaluate=configs.get("EVA_ROUND", False),
            id=self.total_rounds,
        )

        self.add_round(round.id, round)

    def step_forward(self):
        self.current_round.step_forward()
        # if isinstance(self.current_round.agent, HostAgent) and self.current_round.agent.state.name() == HostAgentStatus.ASSIGN.value:
        #     self.current_round.step_forward()
        # elif isinstance(self.current_round.agent, AppAgent) and self.current_round.agent.state.name() == AppAgentStatus.FINISH.value:
        #     self.current_round.step_forward()

    def _init_context(self) -> None:
        """
        Initialize the context.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, "normal")
        self.context.set(ContextNames.SESSION_DATA_MANAGER, SessionDataManager(self.id))

    def create_new_round(self) -> BaseRound:
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
        self._finish = True
        return self._request
    
    def is_finished(self) -> bool:
        """
        Check if the session is ended.
        return: True if the session is ended, otherwise False.
        """
        if (
            self.current_round.is_finished()
            or self.step >= configs["MAX_STEP"]
            or self.total_rounds >= configs["MAX_ROUND"]
        ):
            return True

        if self.is_error():
            return True

        return False

    def request_to_evaluate(self) -> bool:
        """
        Check if the session should be evaluated.
        :return: True if the session should be evaluated, False otherwise.
        """
        request_memory = self._host_agent.blackboard.requests
        return request_memory.to_json()
    
    def get_actions(self) -> list[ActionBase]:
        session_data_manager: SessionDataManager = self.context.get(ContextNames.SESSION_DATA_MANAGER)
        return session_data_manager.session_data.actions_to_run
    
    def update_session_state_from_action_results(self, action_results: dict[str, any]) -> None:
        session_data_manager: SessionDataManager = self.context.get(ContextNames.SESSION_DATA_MANAGER)
        session_data_manager.update_session_state_from_action_results(action_results)
        session_data_manager.clear_roundtrip_data()

    