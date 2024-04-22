# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC
from typing import Dict, Type

from ..config.config import Config
from ..utils import print_with_color
from .interactor import experience_asker

configs = Config.get_instance().config_data


class StatusToStateMapper(ABC):  
    """  
    A class to map the status to the appropriate state.  
    """  
  
    @staticmethod  
    def create_state_mapping() -> Dict[str, Type[object]]:  
        return {  
            "FINISH": RoundFinishState,  
            "ERROR": ErrorState,  
            "APP_SELECTION": AppSelectionState,  
            "CONTINUE": ContinueState,  
            "COMPLETE": SessionFinishState,  
            "SCREENSHOT": AnnotationState,  
            "MAX_STEP_REACHED": MaxStepReachedState  
        }  
  
    def __init__(self):  
        self.STATE_MAPPING = self.create_state_mapping()  
  
    def get_appropriate_state(self, status: str) -> Type[object]:  
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
    def handle(self, session):
        """
        Handle the session.
        :param session: The session.
        """
        pass
    


class NoneState(SessionState):
    """
    The state when the session is None.
    """

    def handle(self, session):
        """
        Handle the session. Do nothing.
        :param session: The session.
        """
        pass


class RoundFinishState(SessionState):
    """
    The state when a single round is finished.
    """

    def handle(self, session):
        """
        Handle the session. Either start a new round or finish the session.
        :param session: The session.
        """

        result = session.get_results()  
        round = session.get_round()  
  
        # Print the result  
        if result != "":  
            print_with_color("Result for round {round}:".format(  
                round=round), "magenta")  
            print_with_color("{result}".format(result=result), "yellow")

        session.set_new_round()
        status = session.get_status()
 
        session.set_state(StatusToStateMapper().get_appropriate_state(status))



class SessionFinishState(SessionState):
    """
    The state when the entire session is finished.
    """

    def handle(self, session):
        """
        Handle the session. Finish the entire session, and save the experience if needed.
        :param session: The session.
        """

        if experience_asker():
            session.experience_saver()



class ErrorState(SessionState):
    """
    The state when an error occurs.
    """

    def handle(self, session):
        """
        Handle the session. Do nothing.
        :param session: The session.
        """
        pass


class AppSelectionState(SessionState):
    """
    The state when the application selection is needed by a HostAgent.
    """

    def handle(self, session):
        """
        Handle the session. Process the application selection.
        :param session: The session.
        """

        round = session.get_round()
        step = session.get_step()

        if round >= 1:
            print_with_color(  
                "Step {step}: Switching to New Application".format(step=step), "magenta")  
            app_window = session.get_application_window()  
            app_window.minimize()

        session.process_application_selection()  
        step = session.get_step()  
        status = session.get_status()  
  
        if step > configs["MAX_STEP"]:  
            session.set_state(MaxStepReachedState())  
            return
        

        session.set_state(StatusToStateMapper().get_appropriate_state(status))



class ContinueState(SessionState):
    """
    The state when the session needs to continue by the AppAgent.
    """

    def handle(self, session):
        """
        Handle the session. Process the action selection.
        :param session: The session.
        """

        session.process_action_selection()  
        status = session.get_status()  
        step = session.get_step()  
  
        if step > configs["MAX_STEP"]:  
            session.set_state(MaxStepReachedState())  
            return
  
        session.set_state(StatusToStateMapper().get_appropriate_state(status))  



class AnnotationState(ContinueState):
    """
    The state when the session needs to re-nnotate the screenshot.
    """

    def handle(self, session):
        """
        Handle the session. Process the action selection with the re-annotation screenshot.
        :param session: The session.
        """
        super().handle(session)



class MaxStepReachedState(SessionState):
    """
    The state when the maximum step is reached.
    """

    def handle(self, session):
        """
        Handle the session. Finish the session when the maximum step is reached.
        :param session: The session.
        """
        pass



