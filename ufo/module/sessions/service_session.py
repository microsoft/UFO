from ufo.agents.states.host_agent_state import ContinueHostAgentState
from ufo.config.config import Config
from ufo.module import interactor
from ufo.module.basic import BaseRound, BaseSession
from ufo.module.sessions.plan_reader import PlanReader
from ufo.module.context import ContextNames

configs = Config.get_instance().config_data

class ServiceSession(BaseSession):
    """
    A session for UFO service.
    """

    def run(self) -> None:
        """
        Run the session.
        """

        #while not self.is_finished():

        round = self.create_new_round()
        if round is not None:
            round.run()

        # if self.application_window is not None:
        #     self.capture_last_snapshot()

        # if self._should_evaluate and not self.is_error():
        #     self.evaluation()

        compeleted_message = "Session completed successfully."
        if isinstance(self.cost, float) and self.cost > 0:
            formatted_cost = "${:.2f}".format(self.cost)
            compeleted_message += f" The cost of the session is {formatted_cost}."

        #get_events_listner().on_task_completed(compeleted_message)

        self.print_cost()

    def _init_context(self) -> None:
        """
        Initialize the context.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, "normal")

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
        return self._request

    def request_to_evaluate(self) -> bool:
        """
        Check if the session should be evaluated.
        :return: True if the session should be evaluated, False otherwise.
        """
        request_memory = self._host_agent.blackboard.requests
        return request_memory.to_json()
