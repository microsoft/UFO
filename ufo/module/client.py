# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import List

from ufo.module.basic import BaseSession


class UFOClientManager:
    """
    The manager for the UFO clients.
    """

    def __init__(self, session_list: List[BaseSession]) -> None:
        """
        Initialize a batch UFO client.
        """

        self.session_list = session_list

    def run_all(self) -> None:
        """
        Run the batch UFO client.
        """

        for session in self.session_list:
            session.run()
