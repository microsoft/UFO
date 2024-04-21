# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC

from .state_map import AppropriateState



class SessionState(ABC):

    def handle(self, session):
        pass


class RoundFinishState(SessionState):

    def handle(self, session):
        pass


class ErrorState(SessionState):

    def handle(self, session):
        pass


class AppSelectionState(SessionState):

    def handle(self, session):
        pass


class ActionSelectionState(SessionState):

    def handle(self, session):
        pass


class SessionFinishState(SessionState):

    def handle(self, session):
        pass


class AnnotationState(SessionState):

    def handle(self, session):
        pass


class MaxStepReachedState(SessionState):

    def handle(self, session):
        pass