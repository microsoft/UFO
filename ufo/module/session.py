# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from typing import List, Optional

from ufo import utils
from ufo.config.config import Config
from ufo.module import interactor, round
from ufo.module.basic import BaseSession
from ufo.module.state import Status

configs = Config.get_instance().config_data


class PlanReader:
    """
    The reader for a plan file.
    """

    def __init__(self, plan_file: str):
        """
        Initialize a plan reader.
        :param plan_file: The path of the plan file.
        """

        with open(plan_file, "r") as f:
            self.plan = json.load(f)
        self.remaining_steps = self.get_steps()

    def get_task(self) -> str:
        """
        Get the task name.
        :return: The task name.
        """

        return self.plan.get("task", "")

    def get_steps(self) -> List[str]:
        """
        Get the steps in the plan.
        :return: The steps in the plan.
        """

        return self.plan.get("steps", [])

    def get_operation_object(self) -> str:
        """
        Get the operation object in the step.
        :return: The operation object.
        """

        return self.plan.get("object", [])

    def get_initial_request(self) -> str:
        """
        Get the initial request in the plan.
        :return: The initial request.
        """

        task = self.get_task()
        object_name = self.get_operation_object()

        request = f"{task} in {object_name}"

        return request

    def get_host_agent_request(self) -> str:
        """
        Get the request for the host agent.
        :return: The request for the host agent.
        """

        object_name = self.get_operation_object()

        request = f"Open and select the application of {object_name}, and output the FINISH status immediately."

        return request

    def next_step(self) -> Optional[str]:
        """
        Get the next step in the plan.
        :return: The next step.
        """

        if self.remaining_steps:
            step = self.remaining_steps.pop(0)
            return step

        return None

    def task_finished(self) -> bool:
        """
        Check if the task is finished.
        :return: True if the task is finished, False otherwise.
        """

        return not self.remaining_steps


class SessionFactory:
    """
    The factory class to create a session.
    """

    def create_session(self, task: str, mode: str, plan: str) -> BaseSession:
        """
        Create a session.
        :param task: The name of current task.
        :param mode: The mode of the task.
        :return: The created session.
        """
        if mode == "normal":
            return [Session(task)]
        elif mode == "follower":
            # If the plan is a folder, create a follower session for each plan file in the folder.
            if self.is_folder(plan):
                return self.create_follower_session_in_batch(task, plan)
            else:
                return [FollowerSession(task, plan)]
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
            FollowerSession(f"{task}/{file_name}", plan_file)
            for file_name, plan_file in zip(file_names, plan_files)
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


class Session(BaseSession):
    """
    A session for UFO.
    """

    def __init__(self, task: str):
        """
        Initialize a session.
        :param task: The name of current task.
        """

        super(Session, self).__init__(task)

        # Initial setup and welcome message
        utils.print_with_color(interactor.WELCOME_TEXT, "cyan")

        self.request = interactor.first_request()

        # Round-related properties
        self.round_list = []
        self._current_round = self.create_round()

    def create_round(self) -> round.Round:
        """
        Create a new round.
        """

        new_round = round.Round(
            task=self.task,
            logger=self.logger,
            request_logger=self.request_logger,
            host_agent=self.host_agent,
            request=self.request,
        )
        new_round.set_index(self.get_round_num())
        new_round.set_session_step(self.get_step())

        self.round_list.append(new_round)

        return new_round

    def round_hostagent_execution(self) -> None:
        """
        Execute the host agent in the current round.
        """

        current_round = self.get_current_round()
        current_round.set_session_step(self.get_step())
        current_round.process_application_selection()

        self._status = current_round.get_status()
        self._step += 1

        self.app_window = current_round.get_application_window()
        self.application = self.app_window.window_text()
        self.app_agent = self.host_agent.get_active_appagent()

    def round_appagent_execution(self) -> None:
        """
        Execute the app agent in the current round.
        """

        current_round = self.get_current_round()
        current_round.set_session_step(self.get_step())
        current_round.process_action_selection()

        self._status = current_round.get_status()
        self._step += 1

    def start_new_round(self) -> None:
        """
        Start a new round.
        """

        self.host_agent.add_request_memory(self.request)
        self._round += 1

        self.request, iscomplete = interactor.new_request()

        if iscomplete:
            self._status = Status.COMPLETE
        else:
            self._current_round = self.create_round()
            self._status = Status.APP_SELECTION


class FollowerSession(Session):
    """
    A session for following a list of plan for action taken.
    This session is used for the follower agent, which accepts a plan file to follow using the PlanReader.
    """

    def __init__(self, task: str, plan_file: str) -> None:
        """
        Initialize a session.
        :param task: The name of current task.
        :param plan_dir: The path of the plan file to follow.
        """

        super(Session, self).__init__(task)

        self.plan_reader = PlanReader(plan_file)
        self.request = self.plan_reader.get_host_agent_request()
        utils.print_with_color("Complete the following request:", "yellow")
        utils.print_with_color(self.plan_reader.get_initial_request(), "cyan")

        # Round-related properties
        self.round_list = []
        self._current_round = self.create_round()

    def create_round(self) -> round.FollowerRound:
        """
        Create a new round.
        """

        new_round = round.FollowerRound(
            task=self.task,
            logger=self.logger,
            request_logger=self.request_logger,
            host_agent=self.host_agent,
            app_agent=self.app_agent,
            app_window=self.app_window,
            application=self.application,
            request=self.request,
        )
        new_round.set_index(self.get_round_num())
        new_round.set_session_step(self.get_step())

        self.round_list.append(new_round)

        return new_round

    def start_new_round(self) -> None:
        """
        Start a new round.
        """

        # Add the request to the memory, but not for the first round.
        if self._round > 0:
            self.host_agent.add_request_memory(self.request)

        # Clear the memory of the app agent to avoid any misinterpretation.
        if self.app_agent is not None:
            self.app_agent.clear_memory()

        self._round += 1

        if self.plan_reader.task_finished():
            self._status = Status.COMPLETE
        else:
            self.request = self.plan_reader.next_step()
            utils.print_with_color(
                "Starting step {round}:".format(round=self._round), "yellow"
            )
            utils.print_with_color(self.request, "cyan")

            # Create a new round.
            self._current_round = self.create_round()
            self._current_round.set_application_window(self.app_window)
            self._status = Status.CONTINUE
