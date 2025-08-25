# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import logging
import os
from typing import List

from ufo.config import Config
from ufo.module.basic import BaseSession
from ufo.module.sessions.session import (
    FollowerSession,
    FromFileSession,
    OpenAIOperatorSession,
    Session,
)

configs = Config.get_instance().config_data


class SessionPool:
    """
    The manager for the UFO clients.
    """

    def __init__(self, session_list: List[BaseSession]) -> None:
        """
        Initialize a batch UFO client.
        """

        self._session_list = session_list

    async def run_all(self) -> None:
        """
        Run the batch UFO client.
        """

        for session in self.session_list:
            await session.run()

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


class SessionFactory:
    """
    The factory class to create a session.
    """

    logger = logging.getLogger(__name__)

    def create_session(
        self, task: str, mode: str, plan: str, request: str = ""
    ) -> List[BaseSession]:
        """
        Create a session.
        :param task: The name of current task.
        :param mode: The mode of the task.
        :return: The created session.
        """
        if mode in ["normal", "normal_operator"]:
            self.logger.info(f"Creating a normal session for mode: {mode}")
            return [
                Session(
                    task,
                    configs.get("EVA_SESSION", False),
                    id=0,
                    request=request,
                    mode=mode,
                )
            ]
        elif mode == "follower":
            # If the plan is a folder, create a follower session for each plan file in the folder.

            self.logger.info(f"Creating a follower session for mode: {mode}")
            if self.is_folder(plan):
                self.logger.info(f"Got a folder for plan, creating sessions in batch.")
                return self.create_follower_session_in_batch(task, plan)
            else:
                return [
                    FollowerSession(task, plan, configs.get("EVA_SESSION", False), id=0)
                ]
        elif mode == "batch_normal":
            self.logger.info(f"Creating a batch normal session for mode: {mode}")
            if self.is_folder(plan):
                self.logger.info(f"Got a folder for plan, creating sessions in batch.")
                return self.create_sessions_in_batch(task, plan)
            else:
                return [
                    FromFileSession(task, plan, configs.get("EVA_SESSION", False), id=0)
                ]
        elif mode == "operator":
            self.logger.info(f"Creating an operator session for mode: {mode}")
            return [
                OpenAIOperatorSession(
                    task, configs.get("EVA_SESSION", False), id=0, request=request
                )
            ]
        else:
            raise ValueError(f"The {mode} mode is not supported.")

    def create_follower_session_in_batch(
        self, task: str, plan: str
    ) -> List[BaseSession]:
        """
        Create a follower session.
        :param task: The name of current task.
        :param plan: The path folder of all plan files.
        :return: The list of created follower sessions.
        """
        plan_files = self.get_plan_files(plan)
        file_names = [self.get_file_name_without_extension(f) for f in plan_files]
        sessions = [
            FollowerSession(
                f"{task}/{file_name}",
                plan_file,
                configs.get("EVA_SESSION", False),
                id=i,
            )
            for i, (file_name, plan_file) in enumerate(zip(file_names, plan_files))
        ]

        return sessions

    def create_sessions_in_batch(self, task: str, plan: str) -> List[BaseSession]:
        """
        Create a follower session.
        :param task: The name of current task.
        :param plan: The path folder of all plan files.
        :return: The list of created follower sessions.
        """
        is_record = configs.get("TASK_STATUS", True)
        plan_files = self.get_plan_files(plan)
        file_names = [self.get_file_name_without_extension(f) for f in plan_files]
        is_done_files = []
        if is_record:
            file_path = configs.get(
                "TASK_STATUS_FILE",
                os.path.join(os.path.dirname(plan), "tasks_status.json"),
            )
            if not os.path.exists(file_path):
                self.task_done = {f: False for f in file_names}
                json.dump(
                    self.task_done,
                    open(file_path, "w"),
                    indent=4,
                )
            else:
                self.task_done = json.load(open(file_path, "r"))
                is_done_files = [f for f in file_names if self.task_done.get(f, False)]

        sessions = [
            FromFileSession(
                f"{task}/{file_name}",
                plan_file,
                configs.get("EVA_SESSION", False),
                id=i,
            )
            for i, (file_name, plan_file) in enumerate(zip(file_names, plan_files))
            if file_name not in is_done_files
        ]

        return sessions

    @staticmethod
    def is_folder(path: str) -> bool:
        """
        Check if the path is a folder.
        :param path: The path to check.
        :return: True if the path is a folder, False otherwise.
        """
        return os.path.isdir(path)

    @staticmethod
    def get_plan_files(path: str) -> List[str]:
        """
        Get the plan files in the folder. The plan file should have the extension ".json".
        :param path: The path of the folder.
        :return: The plan files in the folder.
        """
        return [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".json")]

    def get_file_name_without_extension(self, file_path: str) -> str:
        """
        Get the file name without extension.
        :param file_path: The path of the file.
        :return: The file name without extension.
        """
        return os.path.splitext(os.path.basename(file_path))[0]
