# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from typing import List

from ufo import utils
from ufo.agents.states.app_agent_state import ContinueAppAgentState
from ufo.agents.states.host_agent_state import ContinueHostAgentState
from ufo.config.config import Config
from ufo.module import interactor
from ufo.modules.basic import BaseRound, BaseSession
from ufo.modules.sessions.plan_reader import PlanReader

configs = Config.get_instance().config_data


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
            return [Session(task, configs.get("EVA_SESSION", False))]
        elif mode == "follower":
            # If the plan is a folder, create a follower session for each plan file in the folder.
            if self.is_folder(plan):
                return self.create_follower_session_in_batch(task, plan)
            else:
                return [FollowerSession(task, plan, configs.get("EVA_SESSION", False))]
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
                f"{task}/{file_name}", plan_file, configs.get("EVA_SESSION", False)
            )
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

    def run(self) -> None:
        """
        Run the session.
        """
        super().run()
        # Save the experience if the user asks so.
        if interactor.experience_asker():
            self.experience_saver()

    def create_new_round(self) -> None:
        """
        Create a new round.
        """

        # Get a request for the new round.
        request = self.get_request()

        # Create a new round and return None if the session is finished.

        if self.is_finished():
            return None

        self._host_agent.set_state(ContinueHostAgentState())
        round = BaseRound(
            request=request,
            agent=self._host_agent,
            context=self.context,
            should_evaluate=configs.get("EVA_ROUND", False),
            id=self.total_rounds,
        )

        self.add_round(round.id, round)

        return round

    def get_request(self) -> str:
        """
        Get the request for the host agent.
        :return: The request for the host agent.
        """

        if self.total_rounds == 0:
            utils.print_with_color(interactor.WELCOME_TEXT, "cyan")
            return interactor.first_request()
        else:
            request, iscomplete = interactor.new_request()
            if iscomplete:
                self._finish = True
            return request

    def request_to_evaluate(self) -> bool:
        """
        Check if the session should be evaluated.
        :return: True if the session should be evaluated, False otherwise.
        """
        request_memory = self._host_agent.get_request_history_memory()
        return request_memory.to_json()


class FollowerSession(BaseSession):
    """
    A session for following a list of plan for action taken.
    This session is used for the follower agent, which accepts a plan file to follow using the PlanReader.
    """

    def __init__(self, task: str, plan_file: str, should_evaluate: bool) -> None:
        """
        Initialize a session.
        :param task: The name of current task.
        :param plan_dir: The path of the plan file to follow.
        :param should_evaluate: Whether to evaluate the session.
        """

        super(Session, self).__init__(task, should_evaluate)

        self.plan_reader = PlanReader(plan_file)

    def create_new_round(self) -> None:
        """
        Create a new round.
        """

        # Get a request for the new round.
        request = self.get_request()

        # Create a new round and return None if the session is finished.
        if self.is_finished:
            return None

        if self.total_rounds == 0:
            utils.print_with_color("Complete the following request:", "yellow")
            utils.print_with_color(self.plan_reader.get_initial_request(), "cyan")
            agent = self._host_agent
        else:
            agent = self._host_agent.get_active_appagent()
            agent.clear_memory()
            agent.set_state(ContinueAppAgentState)

            self._host_agent.add_request_memory(request)

            utils.print_with_color(
                "Starting step {round}:".format(round=self.total_rounds), "yellow"
            )
            utils.print_with_color(self.request, "cyan")

        round = BaseRound(
            request=request,
            agent=agent,
            context=self.context,
            should_evaluate=configs.get("EVA_ROUND", False),
            id=self.total_rounds,
        )

        self.add_round(round.id, round)

        return round

    def get_request(self) -> str:
        """
        Get the request for the new round.
        """

        # If the task is finished, return an empty string.
        if self.plan_reader.task_finished():
            self._finish = True
            return ""

        # Get the request from the plan reader.
        if self.total_rounds == 0:
            return self.plan_reader.get_host_agent_request()
        else:
            return self.plan_reader.next_step()

    def request_to_evaluate(self) -> bool:
        """
        Check if the session should be evaluated.
        :return: True if the session should be evaluated, False otherwise.
        """

        return self.plan_reader.get_task()
