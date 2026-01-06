# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import logging
import os
import platform
import time
from typing import Optional, TYPE_CHECKING

import psutil

# Conditional import for Windows-specific packages
if TYPE_CHECKING or platform.system() == "Windows":
    import win32com.client
else:
    win32com = None

from rich.console import Console

from ufo import utils
from ufo.agents.agent.app_agent import OpenAIOperatorAgent
from ufo.agents.agent.host_agent import AgentFactory
from ufo.agents.states.app_agent_state import ContinueAppAgentState
from ufo.agents.states.host_agent_state import ContinueHostAgentState
from ufo.client.mcp.mcp_server_manager import MCPServerManager
from config.config_loader import get_ufo_config
from aip.messages import Command
from ufo.module import interactor
from ufo.module.basic import BaseRound
from ufo.module.context import ContextNames
from ufo.module.dispatcher import LocalCommandDispatcher
from ufo.module.sessions.plan_reader import PlanReader
from ufo.module.sessions.platform_session import WindowsBaseSession
from ufo.trajectory.parser import Trajectory

ufo_config = get_ufo_config()
console = Console()


class Session(WindowsBaseSession):
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
        self.logger = logging.getLogger(__name__)

    async def run(self) -> None:
        """
        Run the session.
        """
        await super().run()
        # Save the experience if the user asks so.

        save_experience = ufo_config.system.save_experience

        self.logger.info(f"Save experience setting: {save_experience}")

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
        mcp_server_manager = MCPServerManager()
        command_dispatcher = LocalCommandDispatcher(self, mcp_server_manager)
        self.context.attach_command_dispatcher(command_dispatcher)

    def create_new_round(self) -> Optional[BaseRound]:
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
            should_evaluate=ufo_config.system.eva_round,
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
            # Otherwise, ask the user to input the request with enhanced UX.
            else:
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


class FollowerSession(WindowsBaseSession):
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
        mcp_server_manager = MCPServerManager()
        command_dispatcher = LocalCommandDispatcher(self, mcp_server_manager)
        self.context.attach_command_dispatcher(command_dispatcher)

    def create_new_round(self) -> None:
        """
        Create a new round.
        """
        from ufo.agents.agent.host_agent import HostAgent

        # Get a request for the new round.
        request = self.next_request()

        # Create a new round and return None if the session is finished.
        if self.is_finished():
            return None

        if self.total_rounds == 0:
            console.print("Complete the following request:", style="yellow")
            console.print(self.plan_reader.get_initial_request(), style="cyan")
            agent: HostAgent = self._host_agent
        else:
            host_agent: HostAgent = self._host_agent
            self.context.set(ContextNames.SUBTASK, request)
            agent = host_agent.create_subagent(context=self.context)

            # Clear the memory and set the state to continue the app agent.
            agent.clear_memory()
            agent.blackboard.requests.clear()

            agent.set_state(ContinueAppAgentState())

        round = BaseRound(
            request=request,
            agent=agent,
            context=self.context,
            should_evaluate=ufo_config.system.eva_round,
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


class FromFileSession(WindowsBaseSession):
    """
    A session for UFO from files on Windows.
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
            should_evaluate=ufo_config.system.eva_round,
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
            console.print(self.plan_reader.get_host_request(), style="cyan")
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
        is_record = ufo_config.system.task_status
        if is_record:
            file_path = ufo_config.system.get(
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

        # Initialize application_window as None, will be set via action callback
        self.application_window = None

        application_process_name = "Desktop"
        application_root_name = "Desktop"

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

    async def run(self) -> None:
        """
        Run the session.
        """
        while not self.is_finished():

            round = self.create_new_round()

            if round is None:
                break
            round.run()

        await self.capture_last_snapshot()

        if self._should_evaluate and not self.is_error():
            self.evaluation()

        if ufo_config.system.log_to_markdown:

            file_path = self.log_path
            trajectory = Trajectory(file_path)
            trajectory.to_markdown(file_path + "output.md")

        self.print_cost()

    async def capture_last_screenshot(
        self, save_path: str, full_screen: bool = False
    ) -> None:
        """
        Capture the last window screenshot.
        :param save_path: The path to save the window screenshot.
        :param full_screen: Whether to capture the full screen or just the active window.
        """

        try:
            if full_screen:
                command = Command(
                    tool_name="capture_desktop_screenshot",
                    parameters={"all_screens": True},
                    tool_type="data_collection",
                )
            else:

                command = Command(
                    tool_name="capture_desktop_screenshot",
                    parameters={"all_screens": False},
                    tool_type="data_collection",
                )

            result = await self.context.command_dispatcher.execute_commands([command])
            image = result[0].result

            self.logger.info(f"Captured screenshot at final: {save_path}")
            if image:
                utils.save_image_string(image, save_path)

        except Exception as e:
            self.logger.warning(
                f"The last snapshot capture failed, due to the error: {e}"
            )
