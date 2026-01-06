# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import logging
import os
import platform
from typing import List, Optional, TYPE_CHECKING

from config.config_loader import get_ufo_config
from ufo.module.basic import BaseSession
from ufo.module.sessions.session import (
    FollowerSession,
    FromFileSession,
    OpenAIOperatorSession,
    Session,
)
from ufo.module.sessions.service_session import ServiceSession

if TYPE_CHECKING:
    from aip.protocol.task_execution import TaskExecutionProtocol
from ufo.module.sessions.linux_session import LinuxSession, LinuxServiceSession
from ufo.module.sessions.mobile_session import MobileSession, MobileServiceSession

ufo_config = get_ufo_config()


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
    Supports both Windows and Linux platforms with different session types.
    """

    logger = logging.getLogger(__name__)

    def create_session(
        self,
        task: str,
        mode: str,
        plan: str,
        request: str = "",
        platform_override: Optional[str] = None,
        **kwargs,
    ) -> List[BaseSession]:
        """
        Create a session based on platform and mode.
        :param task: The name of current task.
        :param mode: The mode of the task.
        :param plan: The plan file or folder path (for follower/batch modes).
        :param request: The user request.
        :param platform_override: Override platform detection ('windows', 'linux', or 'mobile').
        :param kwargs: Additional platform-specific parameters:
            - application_name: Target application (for Linux sessions)
            - websocket: WebSocket connection (for service sessions)
        :return: The created session list.
        """
        current_platform = platform_override or platform.system().lower()

        if current_platform == "windows":
            return self._create_windows_session(task, mode, plan, request, **kwargs)
        elif current_platform == "linux":
            return self._create_linux_session(task, mode, plan, request, **kwargs)
        elif current_platform == "mobile":
            return self._create_mobile_session(task, mode, plan, request, **kwargs)
        else:
            raise NotImplementedError(
                f"Platform {current_platform} is not supported yet."
            )

    def _create_windows_session(
        self, task: str, mode: str, plan: str, request: str = "", **kwargs
    ) -> List[BaseSession]:
        """
        Create Windows-specific sessions.
        :param task: The name of current task.
        :param mode: The mode of the task.
        :param plan: The plan file or folder path.
        :param request: The user request.
        :param kwargs: Additional parameters.
        :return: The created Windows session list.
        """
        if mode in ["normal", "normal_operator"]:
            self.logger.info(f"Creating a normal Windows session for mode: {mode}")
            return [
                Session(
                    task,
                    ufo_config.system.eva_session,
                    id=kwargs.get("id", 0),
                    request=request,
                    mode=mode,
                )
            ]
        elif mode == "service":
            self.logger.info(f"Creating a Windows service session for mode: {mode}")
            return [
                ServiceSession(
                    task=task,
                    should_evaluate=ufo_config.system.eva_session,
                    id=kwargs.get("id", 0),
                    request=request,
                    task_protocol=kwargs.get("task_protocol"),
                )
            ]
        elif mode == "follower":
            # If the plan is a folder, create a follower session for each plan file in the folder.

            self.logger.info(f"Creating a Windows follower session for mode: {mode}")
            if self.is_folder(plan):
                self.logger.info(f"Got a folder for plan, creating sessions in batch.")
                return self.create_follower_session_in_batch(task, plan)
            else:
                return [
                    FollowerSession(task, plan, ufo_config.system.eva_session, id=0)
                ]
        elif mode == "batch_normal":
            self.logger.info(
                f"Creating a batch normal Windows session for mode: {mode}"
            )
            if self.is_folder(plan):
                self.logger.info(f"Got a folder for plan, creating sessions in batch.")
                return self.create_sessions_in_batch(task, plan)
            else:
                return [
                    FromFileSession(task, plan, ufo_config.system.eva_session, id=0)
                ]
        elif mode == "operator":
            self.logger.info(f"Creating a Windows operator session for mode: {mode}")
            return [
                OpenAIOperatorSession(
                    task, ufo_config.system.eva_session, id=0, request=request
                )
            ]
        else:
            raise ValueError(f"The {mode} mode is not supported on Windows.")

    def _create_linux_session(
        self, task: str, mode: str, plan: str, request: str = "", **kwargs
    ) -> List[BaseSession]:
        """
        Create Linux-specific sessions.
        :param task: The name of current task.
        :param mode: The mode of the task.
        :param plan: The plan file or folder path (not used for normal/service modes).
        :param request: The user request.
        :param kwargs: Additional parameters:
            - application_name: Target application name
            - task_protocol: AIP TaskExecutionProtocol instance (for service mode)
        :return: The created Linux session list.
        """
        if mode in ["normal", "normal_operator"]:
            self.logger.info(f"Creating a normal Linux session for mode: {mode}")
            return [
                LinuxSession(
                    task=task,
                    should_evaluate=ufo_config.system.eva_session,
                    id=0,
                    request=request,
                    mode=mode,
                    application_name=kwargs.get("application_name"),
                )
            ]
        elif mode == "service":
            self.logger.info(f"Creating a Linux service session for mode: {mode}")
            return [
                LinuxServiceSession(
                    task=task,
                    should_evaluate=ufo_config.system.eva_session,
                    id=0,
                    request=request,
                    task_protocol=kwargs.get("task_protocol"),
                )
            ]
        # TODO: Add Linux follower and batch modes if needed
        # elif mode == "follower":
        #     return self._create_linux_follower_session(...)
        else:
            raise ValueError(
                f"The {mode} mode is not supported on Linux yet. "
                f"Supported modes: normal, normal_operator, service"
            )

    def _create_mobile_session(
        self, task: str, mode: str, plan: str, request: str = "", **kwargs
    ) -> List[BaseSession]:
        """
        Create Mobile Android-specific sessions.
        :param task: The name of current task.
        :param mode: The mode of the task.
        :param plan: The plan file or folder path (not used for normal/service modes).
        :param request: The user request.
        :param kwargs: Additional parameters:
            - task_protocol: AIP TaskExecutionProtocol instance (for service mode)
        :return: The created Mobile session list.
        """
        if mode in ["normal", "normal_operator"]:
            self.logger.info(f"Creating a normal Mobile session for mode: {mode}")
            return [
                MobileSession(
                    task=task,
                    should_evaluate=ufo_config.system.eva_session,
                    id=0,
                    request=request,
                    mode=mode,
                )
            ]
        elif mode == "service":
            self.logger.info(f"Creating a Mobile service session for mode: {mode}")
            return [
                MobileServiceSession(
                    task=task,
                    should_evaluate=ufo_config.system.eva_session,
                    id=0,
                    request=request,
                    task_protocol=kwargs.get("task_protocol"),
                )
            ]
        # TODO: Add Mobile follower and batch modes if needed
        # elif mode == "follower":
        #     return self._create_mobile_follower_session(...)
        else:
            raise ValueError(
                f"The {mode} mode is not supported on Mobile yet. "
                f"Supported modes: normal, normal_operator, service"
            )

    def create_service_session(
        self,
        task: str,
        should_evaluate: bool,
        id: str,
        request: str,
        task_protocol: Optional["TaskExecutionProtocol"] = None,
        platform_override: Optional[str] = None,
    ) -> BaseSession:
        """
        Convenient method to create a service session for any platform.
        :param task: Task name.
        :param should_evaluate: Whether to evaluate.
        :param id: Session ID.
        :param request: User request.
        :param task_protocol: AIP TaskExecutionProtocol instance.
        :param platform_override: Override platform detection ('windows', 'linux', or 'mobile').
        :return: Platform-specific service session.
        """
        current_platform = platform_override or platform.system().lower()

        if current_platform == "windows":
            self.logger.info("Creating Windows service session")
            return ServiceSession(
                task=task,
                should_evaluate=should_evaluate,
                id=id,
                request=request,
                task_protocol=task_protocol,
            )
        elif current_platform == "linux":
            self.logger.info("Creating Linux service session")
            return LinuxServiceSession(
                task=task,
                should_evaluate=should_evaluate,
                id=id,
                request=request,
                task_protocol=task_protocol,
            )
        elif current_platform == "mobile":
            self.logger.info("Creating Mobile service session")
            return MobileServiceSession(
                task=task,
                should_evaluate=should_evaluate,
                id=id,
                request=request,
                task_protocol=task_protocol,
            )
        else:
            raise NotImplementedError(
                f"Service session not supported on {current_platform}"
            )

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
                ufo_config.system.eva_session,
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
        is_record = ufo_config.system.task_status
        plan_files = self.get_plan_files(plan)
        file_names = [self.get_file_name_without_extension(f) for f in plan_files]
        is_done_files = []
        if is_record:
            file_path = ufo_config.system.task_status_file or os.path.join(
                os.path.dirname(plan), "tasks_status.json"
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
                ufo_config.system.eva_session,
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
