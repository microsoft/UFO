# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC

from .state_map import AppropriateState



class SessionState(ABC):

    def handle(self, session):
        pass