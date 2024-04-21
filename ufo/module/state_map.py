# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from .state import AllFinishState, AppSelectionState, ErrorState, FinishState, ActionSelectionState, MaxStepReachedState, SessionState

STATE_MAPPING = {  
    "FINISH": FinishState,  
    "ERROR": ErrorState,  
    "APP_SELECTION": AppSelectionState,  
    "ACTION_SELECTION": ActionSelectionState,  
    "ALLFINISH": AllFinishState,  
    "MAX_STEP_REACHED": MaxStepReachedState  
}


def AppropriateState(status: str) -> SessionState:
    """
    """
    return STATE_MAPPING.get(status, None)