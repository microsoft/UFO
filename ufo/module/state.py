# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC

from .state_map import AppropriateState



class SessionState(ABC):

    def __init__(self, session):
        self.session = session


    def handle(self):
        pass


class AllFinishState(SessionState):
    def handle(self):
        pass


class MaxStepReachedState(SessionState):
    def handle(self):
        pass


class FinishState(SessionState):  
    def handle(self):  
        self.session.set_new_round()  
        status = self.session.get_status()  
        if status == "ALLFINISH":  
            if self.session.experience_asker():  
                self.session.experience_saver()  
            self.session.set_state(AllFinishState())  
        else:  
            if status == "APP_SELECTION":  
                self.session.set_state(AppSelectionState())  
            elif status == "ERROR":  
                self.session.set_state(ErrorState())


  
class ErrorState(SessionState):  
    def handle(self):  
        # Handle the error state logic here  
        pass  


class AppSelectionState(SessionState):  
    def handle(self):  
        self.session.process_application_selection()  
        step = self.session.get_step()  
        status = self.session.get_status()  
  
        if status == "FINISH":  
            self.session.set_state(FinishState())  
        elif status == "ERROR":  
            self.session.set_state(ErrorState())


  
class ActionSelectionState(SessionState):  
    def handle(self):  
        self.session.process_action_selection()  
        status = self.session.get_status()  
        step = self.session.get_step()  
  
        if status == "APP_SELECTION":  
            self.session.set_state(AppSelectionState())  
        elif status == "FINISH":  
            self.session.set_state(FinishState())  
        elif status == "ERROR":  
            self.session.set_state(ErrorState())