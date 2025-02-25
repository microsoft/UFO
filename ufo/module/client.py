# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import List

from tqdm import tqdm

from ufo.config.config import Config
from ufo.module.basic import BaseSession

_configs = Config.get_instance().config_data

class UFOClientManager:
    """
    The manager for the UFO clients.
    """

    def __init__(self, session_list: List[BaseSession]) -> None:
        """
        Initialize a batch UFO client.
        """

        self._session_list = session_list

    def run_all(self) -> None:
        """
        Run the batch UFO client.
        """
        if _configs["MONITOR"]:
            send_point = _configs["SEND_POINT"].split(",")
            total = len(self.session_list)

            for idx, session in enumerate(tqdm(self.session_list), start=1):
                session.run()

                if str(idx) in send_point:
                    message = f"Ufo Execute Completed: {idx}/{total}"
                    send_message(message)
        else:
            for session in tqdm(self.session_list):
                session.run()

    @property
    def session_list(self) -> List[BaseSession]:
        """
        Get the session list.
        :return: The session list.
        """
        return self._session_list

    def add_session(self, session: BaseSession) -> None:
        """
        Add a session to the session list.
        :param session: The session to add.
        """
        self._session_list.append(session)

    def next_session(self) -> BaseSession:
        """
        Get the next session.
        :return: The next session.
        """
        return self._session_list.pop(0)
