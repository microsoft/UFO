# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import time
from typing import List

import psutil
import win32com.client
from ufo import utils
from ufo.agents.agent.app_agent import OpenAIOperatorAgent
from ufo.agents.agent.host_agent import AgentFactory
from ufo.agents.states.app_agent_state import ContinueAppAgentState
from ufo.agents.states.host_agent_state import ContinueHostAgentState
from ufo.config.config import Config
from ufo.module import interactor
from ufo.module.basic import BaseRound, BaseSession
from ufo.module.context import ContextNames
from ufo.module.sessions.plan_reader import PlanReader
from ufo.trajectory.parser import Trajectory
from ufo.automator.ui_control.inspector import ControlInspectorFacade

configs = Config.get_instance().config_data


class SessionFactory:
    """
    The factory class to create a session.
    """

    def create_session(
        self, task: str, mode: str, plan: str, request: str = ""
    ) -> BaseSession:
        """
        Create a session.
        :param task: The name of current task.
        :param mode: The mode of the task.
        :return: The created session.
        """
        if mode in ["normal", "normal_operator"]:
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
            if self.is_folder(plan):
                return self.create_follower_session_in_batch(task, plan)
            else:
                return [
                    FollowerSession(task, plan, configs.get("EVA_SESSION", False), id=0)
                ]
        elif mode == "batch_normal":
            if self.is_folder(plan):
                return self.create_sessions_in_batch(task, plan)
            else:
                return [
                    FromFileSession(task, plan, configs.get("EVA_SESSION", False), id=0)
                ]
        elif mode == "operator":
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


class Session(BaseSession):
    """
    A session for UFO.
    """

    def __init__(
        self,
        task: str,
        should_evaluate: bool,
        id: int,
        request: str = "",
        mode: str = "normal",
    ) -> None:
        """
        Initialize a session.
        :param task: The name of current task.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The id of the session.
        :param request: The user request of the session, optional. If not provided, UFO will ask the user to input the request.
        :param mode: The mode of the task.
        """

        self._mode = mode
        super().__init__(task, should_evaluate, id)

        self._init_request = request

    def run(self) -> None:
        """
        Run the session.
        """
        super().run()
        # Save the experience if the user asks so.

        save_experience = configs.get("SAVE_EXPERIENCE", "always_not")

        if save_experience == "always":
            self.experience_saver()
        elif save_experience == "ask":
            if interactor.experience_asker():
                self.experience_saver()

        elif save_experience == "auto":
            task_completed = self.results.get("complete", "no")
            if task_completed.lower() == "yes":
                self.experience_saver()

        elif save_experience == "always_not":
            pass

    def _init_context(self) -> None:
        """
        Initialize the context.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, self._mode)

    def create_new_round(self) -> None:
        """
        Create a new round.
        """

        # Get a request for the new round.
        request = self.next_request()

        # Create a new round and return None if the session is finished.

        if self.is_finished():
            return None

        self._host_agent.set_state(self._host_agent.default_state)

        round = BaseRound(
            request=request,
            agent=self._host_agent,
            context=self.context,
            should_evaluate=configs.get("EVA_ROUND", False),
            id=self.total_rounds,
        )

        self.add_round(round.id, round)

        return round

    def next_request(self) -> str:
        """
        Get the request for the host agent.
        :return: The request for the host agent.
        """
        if self.total_rounds == 0:

            # If the request is provided via command line, use it directly.
            if self._init_request:
                return self._init_request
            # Otherwise, ask the user to input the request.
            else:
                utils.print_with_color(interactor.WELCOME_TEXT, "cyan")
                return interactor.first_request()
        else:
            request, iscomplete = interactor.new_request()
            if iscomplete:
                self._finish = True
            return request

    def request_to_evaluate(self) -> str:
        """
        Get the request to evaluate.
        return: The request(s) to evaluate.
        """
        request_memory = self._host_agent.blackboard.requests
        return request_memory.to_json()


class FollowerSession(BaseSession):
    """
    A session for following a list of plan for action taken.
    This session is used for the follower agent, which accepts a plan file to follow using the PlanReader.
    """

    def __init__(
        self, task: str, plan_file: str, should_evaluate: bool, id: int
    ) -> None:
        """
        Initialize a session.
        :param task: The name of current task.
        :param plan_file: The path of the plan file to follow.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The id of the session.
        """

        super().__init__(task, should_evaluate, id)

        self.plan_reader = PlanReader(plan_file)

    def _init_context(self) -> None:
        """
        Initialize the context.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, "follower")

    def create_new_round(self) -> None:
        """
        Create a new round.
        """

        # Get a request for the new round.
        request = self.next_request()

        # Create a new round and return None if the session is finished.
        if self.is_finished():
            return None

        if self.total_rounds == 0:
            utils.print_with_color("Complete the following request:", "yellow")
            utils.print_with_color(self.plan_reader.get_initial_request(), "cyan")
            agent = self._host_agent
        else:
            self.context.set(ContextNames.SUBTASK, request)
            agent = self._host_agent.create_app_agent(
                application_window_name=self.context.get(
                    ContextNames.APPLICATION_PROCESS_NAME
                ),
                application_root_name=self.context.get(
                    ContextNames.APPLICATION_ROOT_NAME
                ),
                request=request,
                mode=self.context.get(ContextNames.MODE),
            )

            # Clear the memory and set the state to continue the app agent.
            agent.clear_memory()
            agent.blackboard.requests.clear()

            agent.set_state(ContinueAppAgentState())

        round = BaseRound(
            request=request,
            agent=agent,
            context=self.context,
            should_evaluate=configs.get("EVA_ROUND", False),
            id=self.total_rounds,
        )

        self.add_round(round.id, round)

        return round

    def next_request(self) -> str:
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

    def request_to_evaluate(self) -> str:
        """
        Get the request to evaluate.
        return: The request(s) to evaluate.
        """

        return self.plan_reader.get_task()


class FromFileSession(BaseSession):
    """
    A session for UFO from files.
    """

    def __init__(
        self, task: str, plan_file: str, should_evaluate: bool, id: int
    ) -> None:
        """
        Initialize a session.
        :param task: The name of current task.
        :param plan_file: The path of the plan file to follow.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The id of the session.
        """

        super().__init__(task, should_evaluate, id)
        self.plan_file = plan_file
        self.plan_reader = PlanReader(plan_file)
        self.support_apps = self.plan_reader.get_support_apps()
        self.close = self.plan_reader.get_close()
        self.task_name = task.split("/")[1]
        self.object_name = ""

    def _init_context(self) -> None:
        """
        Initialize the context.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, "batch_normal")

    def create_new_round(self) -> None:
        """
        Create a new round.
        """

        # Get a request for the new round.
        request = self.next_request()

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

    def next_request(self) -> str:
        """
        Get the request for the host agent.
        :return: The request for the host agent.
        """

        if self.total_rounds == 0:
            utils.print_with_color(self.plan_reader.get_host_request(), "cyan")
            return self.plan_reader.get_host_request()
        else:
            self._finish = True
            return

    def get_app_name(self, object_name: str) -> str:
        """
        Get the application name based on the object name.
        :param object_name: The name of the object.
        :return: The application name.
        """
        application_mapping = {
            ".docx": "WINWORD.EXE",
            ".xlsx": "EXCEL.EXE",
            ".pptx": "POWERPNT.EXE",
            # "outlook": "olk.exe",
            # "onenote": "ONENOTE.EXE",
        }
        self.app_name = application_mapping.get(object_name)
        return self.app_name

    def get_app_com(self, object_name: str) -> str:
        """
        Get the COM object name based on the object name.
        :param object_name: The name of the object.
        :return: The COM object name.
        """
        application_mapping = {
            ".docx": "Word.Application",
            ".xlsx": "Excel.Application",
            ".pptx": "PowerPoint.Application",
        }
        self.app_name = application_mapping.get(object_name)
        return self.app_name

    def run(self) -> None:
        """
        Run the session.
        """
        self.setup_application_environment()
        try:
            super().run()
            self.record_task_done()
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"An error occurred: {e}")
        # Close the APP if the user ask so.
        self.terminate_application_processes()

    def terminate_application_processes(self):
        """
        Terminates specific application processes based on the provided conditions.
        """
        if self.close:
            if self.object_name:
                for process in psutil.process_iter(["name"]):
                    if process.info["name"] == self.app_name:
                        os.system(f"taskkill /f /im {self.app_name}")
                        time.sleep(1)
            else:
                app_names = ["WINWORD.EXE", "EXCEL.EXE", "POWERPNT.EXE"]
                for process in psutil.process_iter(["name"]):
                    if process.info["name"] in app_names:
                        os.system(f"taskkill /f /im {process.info['name']}")
                        time.sleep(1)

    def setup_application_environment(self):
        """
        Sets up the application environment by determining the application name and
        command based on the operation object, and then launching the application.

        Raises:
            Exception: If an error occurs during the execution of the command or
                       while interacting with the application via COM.
        """
        self.object_name = self.plan_reader.get_operation_object()
        if self.object_name:
            suffix = os.path.splitext(self.object_name)[1]
            self.app_name = self.get_app_name(suffix)
            print("app_name:", self.app_name)
            if self.app_name not in self.support_apps:
                print(f"The app {self.app_name} is not supported.")
                return  # The app is not supported, so we don't need to setup the environment.
            file = self.plan_reader.get_file_path()
            code_snippet = f"import os\nos.system('start {self.app_name} \"{file}\"')"
            code_snippet = code_snippet.replace("\\", "\\\\")  # escape backslashes
            try:
                exec(code_snippet, globals())
                app_com = self.get_app_com(suffix)
                time.sleep(2)  # wait for the app to boot
                word_app = win32com.client.Dispatch(app_com)
                word_app.WindowState = 1  # wdWindowStateMaximize
            except Exception as e:
                print(f"An error occurred: {e}")

    def request_to_evaluate(self) -> str:
        """
        Get the request to evaluate.
        return: The request(s) to evaluate.
        """
        return self.plan_reader.get_task()

    def record_task_done(self) -> None:
        """
        Record the task done.
        """
        is_record = configs.get("TASK_STATUS", True)
        if is_record:
            file_path = configs.get(
                "TASK_STATUS_FILE",
                os.path.join(self.plan_file, "../..", "tasks_status.json"),
            )
            task_done = json.load(open(file_path, "r"))
            task_done[self.task_name] = True
            json.dump(
                task_done,
                open(file_path, "w"),
                indent=4,
            )


class OpenAIOperatorSession(Session):
    """
    A session for OpenAI Operator.
    """

    def __init__(
        self, task: str, should_evaluate: bool, id: int, request: str = ""
    ) -> None:
        """
        Initialize a session.
        :param task: The name of current task.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The id of the session.
        :param request: The user request of the session, optional. If not provided, UFO will ask the user to input the request.
        """

        super().__init__(task, should_evaluate, id, request)

        inspector = ControlInspectorFacade()

        self.application_window = inspector.desktop

        application_process_name = self.application_window.element_info.name
        application_root_name = inspector.get_application_root_name(
            self.application_window
        )

        self._init_request = self.refine_request(request)

        self.context.set(ContextNames.APPLICATION_ROOT_NAME, application_root_name)
        self.context.set(
            ContextNames.APPLICATION_PROCESS_NAME, application_process_name
        )

        self._host_agent: OpenAIOperatorAgent = AgentFactory.create_agent(
            "operator",
            name="OpenAIOperatorAgent",
            process_name=application_process_name,
            app_root_name=application_root_name,
        )

    def refine_request(self, request: str) -> str:
        """
        Refine the request.
        :param request: The request to refine.
        :return: The refined request.
        """

        additional_guidance = "Please do not ask for consent to perform the task, just execute the action."
        new_request = f"{request} \n {additional_guidance}"

        return new_request

    def run(self) -> None:
        """
        Run the session.
        """

        while not self.is_finished():

            round = self.create_new_round()
            self.application_window = ControlInspectorFacade().desktop

            if round is None:
                break
            round.run()

        self.capture_last_snapshot()

        if self._should_evaluate and not self.is_error():
            self.evaluation()

        if configs.get("LOG_TO_MARKDOWN", True):

            file_path = self.log_path
            trajectory = Trajectory(file_path)
            trajectory.to_markdown(file_path + "/output.md")

        self.print_cost()
