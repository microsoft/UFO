# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
This module contains the state classes for the UFO system.

The state classes are used to handle the session based on the status of the session, using the State pattern.
"""


from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Dict, Type

from ufo.config.config import Config
from ufo.module.interactor import experience_asker
from ufo.utils import print_with_color


configs = Config.get_instance().config_data


# To avoid circular import
if TYPE_CHECKING:
    from .session import Session


class Status:
    ERROR = "ERROR"
    FINISH = "FINISH"
    APP_SELECTION = "APP_SELECTION"
    CONTINUE = "CONTINUE"
    COMPLETE = "COMPLETE"
    SCREENSHOT = "SCREENSHOT"
    MAX_STEP_REACHED = "MAX_STEP_REACHED"
    PENDING = "PENDING"
    EVALUATION = "EVALUATION"


class StatusToStateMapper:
    """
    A class to map the status to the appropriate state.
    """

    # Singleton instance
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.STATE_MAPPING = StatusToStateMapper.create_state_mapping()

    @staticmethod
    def create_state_mapping() -> Dict[str, Type[SessionState]]:
        return {
            Status.FINISH: RoundFinishState,
            Status.ERROR: ErrorState,
            Status.APP_SELECTION: AppSelectionState,
            Status.CONTINUE: ContinueState,
            Status.COMPLETE: SessionFinishState,
            Status.SCREENSHOT: AnnotationState,
            Status.MAX_STEP_REACHED: MaxStepReachedState,
            Status.EVALUATION: EvaluationState,
        }

    def get_appropriate_state(self, status: str) -> Type[SessionState]:
        """
        Get the appropriate state based on the status.
        :param status: The status string.
        :return: The appropriate state.
        """
        state = self.STATE_MAPPING.get(status, NoneState)
        return state()


class SessionState(ABC):
    """
    The base class for session state.
    """

    def __init__(self):
        """
        Initialize the state.
        """
        self.state_mapping = StatusToStateMapper()

    def handle(self, session: "Session") -> None:
        """
        Handle the session.
        :param session: The session.
        """
        pass

    def get_state(self, status: str):
        """
        Get the current state.
        :return: The current state.
        """
        return self.state_mapping.get_appropriate_state(status)


class NoneState(SessionState):
    """
    The state when the session is None.
    """

    def handle(self, session: "Session") -> None:
        """
        Handle the session. Do nothing.
        :param session: The session.
        """
        pass


class RoundFinishState(SessionState):
    """
    The state when a single round is finished.
    """

    def handle(self, session: "Session") -> None:
        """
        Handle the session. Either start a new round or finish the session.
        :param session: The session.
        """

        result = session.get_results()
        round_num = session.get_round_num()

        round_cost = session.get_current_round().get_cost()
        session.update_cost(round_cost)

        # Print the result
        if result != "":
            print_with_color(
                "Result for round {round_num}:".format(round_num=round_num), "magenta"
            )
            print_with_color("{result}".format(result=result), "yellow")

        session.start_new_round()
        status = session.get_status()

        state = self.get_state(status)

        session.set_state(state)


class SessionFinishState(SessionState):
    """
    The state when the entire session is finished.
    """

    def handle(self, session: "Session") -> None:
        """
        Handle the session. Finish the entire session, and save the experience if needed.
        :param session: The session.
        """

        # Save the experience if needed, only for the normal session.
        if session.session_type == "Session":
            if experience_asker():
                session.experience_saver()

        session.set_state(NoneState())


class ErrorState(SessionState):
    """
    The state when an error occurs.
    """

    def handle(self, session: "Session") -> None:
        """
        Handle the session. Do nothing.
        :param session: The session.
        """
        pass


class AppSelectionState(SessionState):
    """
    The state when the application selection is needed by a HostAgent.
    """

    def handle(self, session: "Session") -> None:
        """
        Handle the session. Process the application selection.
        :param session: The session.
        """

        session.round_hostagent_execution()
        step = session.get_step()
        status = session.get_status()

        if step > configs["MAX_STEP"]:
            session.set_state(MaxStepReachedState())
            return

        state = self.get_state(status)

        session.set_state(state)


class ContinueState(SessionState):
    """
    The state when the session needs to continue by the AppAgent.
    """

    def handle(self, session: "Session") -> None:
        """
        Handle the session. Process the action selection.
        :param session: The session.
        """

        session.round_appagent_execution()
        status = session.get_status()
        step = session.get_step()

        if step > configs["MAX_STEP"]:
            session.set_state(MaxStepReachedState())
            return

        state = self.get_state(status)

        session.set_state(state)


class AnnotationState(ContinueState):
    """
    The state when the session needs to re-nnotate the screenshot.
    """

    def handle(self, session: "Session") -> None:
        """
        Handle the session. Process the action selection with the re-annotation screenshot. Same as ContinueState.
        :param session: The session.
        """
        super().handle(session)


class MaxStepReachedState(SessionState):
    """
    The state when the maximum step is reached.
    """

    def handle(self, session: "Session") -> None:
        """
        Handle the session. Finish the session when the maximum step is reached.
        :param session: The session.
        """
        pass


class EvaluationState(SessionState):
    """
    The state when the session needs to be evaluated.
    """

    def handle(self, session: "Session") -> None:
        """
        Handle the session. Process the evaluation.
        :param session: The session.
        """
        pass
