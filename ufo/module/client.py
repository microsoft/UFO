# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import List

from ufo.module.basic import BaseSession


class UFOClient:
    """
    A UFO client to run the UFO system for a single session.
    """

    def __init__(self, session: BaseSession) -> None:
        """
        Initialize a UFO client.
        """

        self.session = session

    def run(self) -> None:
        """
        Run the UFO client.
        """

        while not self.session.is_finish():
            self.session.handle()

        self.session.print_cost()


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
            client = UFOClient(session)
            client.run()
