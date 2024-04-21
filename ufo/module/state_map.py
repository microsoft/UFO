# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from . import state

STATE_MAPPING = {  
    "FINISH": state.RoundFinishState,  
    "ERROR": state.ErrorState,  
    "APP_SELECTION": state.AppSelectionState,  
    "ACTION_SELECTION": state.ActionSelectionState,  
    "COMPLETE": state.SessionFinishState,
    "SCREENSHOT": state.AnnotationState,  
    "MAX_STEP_REACHED": state.MaxStepReachedState  
}


def AppropriateState(status: str) -> state.SessionState:
    """
    """
    return STATE_MAPPING.get(status, None)