# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import os
import time
from typing import TYPE_CHECKING

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agents.agent.app_agent import AppAgent
from ufo.agents.memory.memory import MemoryItem
from ufo.agents.processors.basic import BaseProcessor
from ufo.config.config import Config
from ufo.modules.context import Context, ContextNames

configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]

if TYPE_CHECKING:
    from ufo.agents.agent.host_agent import HostAgent


class HostAgentProcessor(BaseProcessor):
    """
    The processor for the host agent at a single step.
    """

    def __init__(self, agent: "HostAgent", context: Context) -> None:
        """
        Initialize the host agent processor.
        :param round_num: The total number of rounds in the session.
        :param log_path: The log path.
        :param request: The user request.
        :param request_logger: The logger for the request string.
        :param logger: The logger for the response and error.
        :param host_agent: The host agent to process the session.
        :param round_step: The number of steps in the round.
        :param session_step: The global step of the session.
        :param prev_status: The previous status of the session.
        :param app_window: The application window.
        """

        super().__init__(agent=agent, context=context)

        self.host_agent = agent

        self._desktop_screen_url = None
        self._desktop_windows_dict = None
        self._desktop_windows_info = None
        self.app_to_open = None

    def print_step_info(self) -> None:
        """
        Print the step information.
        """
        utils.print_with_color(
            "Round {round_num}, Step {step}: Selecting an application.".format(
                round_num=self.round_num + 1, step=self.round_step + 1
            ),
            "magenta",
        )

    def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """

        desktop_save_path = self.log_path + f"action_step{self.session_step}.png"

        # Capture the desktop screenshot for all screens.
        self.photographer.capture_desktop_screen_screenshot(
            all_screens=True, save_path=desktop_save_path
        )

        # Encode the desktop screenshot into base64 format as required by the LLM.
        self._desktop_screen_url = self.photographer.encode_image_from_path(
            desktop_save_path
        )

    def get_control_info(self) -> None:
        """
        Get the control information.
        """

        # Get all available windows on the desktop, into a dictionary with format {index: application object}.
        self._desktop_windows_dict = self.control_inspector.get_desktop_app_dict(
            remove_empty=True
        )

        # Get the textual information of all windows.
        self._desktop_windows_info = self.control_inspector.get_desktop_app_info(
            self._desktop_windows_dict
        )

    def get_prompt_message(self) -> None:
        """
        Get the prompt message.
        """

        # Get the request and action history of the host agent.
        request_history = self.host_agent.get_request_history_memory().to_json()
        action_history = self.host_agent.get_global_action_memory().to_json()

        # Get the previous plan from the memory. If the memory is empty, set the plan to an empty string.
        agent_memory = self.host_agent.memory
        if agent_memory.length > 0:
            plan = agent_memory.get_latest_item().to_dict()["Plan"]
        else:
            plan = []

        # Construct the prompt message for the host agent.
        self._prompt_message = self.host_agent.message_constructor(
            [self._desktop_screen_url],
            request_history,
            action_history,
            self._desktop_windows_info,
            plan,
            self.request,
        )

        # Log the prompt message. Only save them in debug mode.
        log = json.dumps(
            {
                "step": self.session_step,
                "prompt": self._prompt_message,
                "control_items": self._desktop_windows_info,
                "filted_control_items": self._desktop_windows_info,
                "status": "",
            }
        )
        self.request_logger.debug(log)

    def get_response(self) -> None:
        """
        Get the response from the LLM.
        """

        # Try to get the response from the LLM. If an error occurs, catch the exception and log the error.
        try:
            self._response, self._cost = self.host_agent.get_response(
                self._prompt_message, "HOSTAGENT", use_backup_engine=True
            )
            self._update_context()
        except Exception:
            self.llm_error_handler()

    def parse_response(self) -> None:
        """
        Parse the response.
        """

        # Try to parse the response. If an error occurs, catch the exception and log the error.
        try:
            self._response_json = self.host_agent.response_to_dict(self._response)

        except Exception:
            self.general_error_handler()

        self.control_label = self._response_json.get("ControlLabel", "")
        self._control_text = self._response_json.get("ControlText", "")

        # Convert the plan from a string to a list if the plan is a string.
        self._plan = self.string2list(self._response_json.get("Plan", ""))
        self._response_json["Plan"] = self._plan

        self._status = self._response_json.get("Status", "")
        self.app_to_open = self._response_json.get("AppsToOpen", None)

        self.host_agent.print_response(self._response_json)

        if (
            self._agent_status_manager.FINISH.value in self._status.upper()
            or self._control_text == ""
        ):
            self._status = self._agent_status_manager.FINISH.value

    def execute_action(self) -> None:
        """
        Execute the action.
        """

        # When the required application is not opened, try to open the application and set the focus to the application window.
        if self.app_to_open is not None:
            new_app_window = self.host_agent.app_file_manager(self.app_to_open)
            self._control_text = new_app_window.window_text()
        else:
            # Get the application window
            new_app_window = self._desktop_windows_dict.get(self.control_label, None)

        if new_app_window is None:
            return

        # Get the root name of the application.
        self.app_root = self.control_inspector.get_application_root_name(new_app_window)

        # Check if the window interface is available for the visual element.
        if not self.is_window_interface_available(new_app_window):
            self._status = self._agent_status_manager.ERROR.value
            return

        # Switch to the new application window, if it is different from the current application window.
        self.switch_to_new_app_window(new_app_window)
        self._app_window.set_focus()
        self._app_window.draw_outline(colour="red", thickness=3)

    def is_window_interface_available(self, new_app_window: UIAWrapper) -> bool:
        """
        Check if the window interface is available for the visual element.
        :param new_app_window: The new application window.
        :return: True if the window interface is available, False otherwise.
        """
        try:
            new_app_window.is_normal()
            return True
        except Exception:
            utils.print_with_color(
                "Window interface {title} not available for the visual element.".format(
                    title=self._control_text
                ),
                "red",
            )
            return False

    def switch_to_new_app_window(self, new_app_window: UIAWrapper) -> None:
        """
        Switch to the new application window if it is different from the current application window.
        :param new_app_window: The new application window.
        """

        if new_app_window != self._app_window and self._app_window is not None:
            utils.print_with_color("Switching to a new application...", "magenta")

        self._app_window = new_app_window

        self.context.set(ContextNames.APPLICATION_WINDOW, self._app_window)

        self.context.set(ContextNames.APPLICATION_ROOT_NAME, self.app_root)
        self.context.set(ContextNames.APPLICATION_PROCESS_NAME, self._control_text)

    def update_memory(self) -> None:
        """
        Update the memory of the Agent.
        """

        # Create a memory item for the host agent at the current step.
        host_agent_step_memory = MemoryItem()

        # Log additional information for the host agent.
        additional_memory = {
            "Step": self.session_step,
            "RoundStep": self.round_step,
            "AgentStep": self.host_agent.step,
            "Round": self.round_num,
            "ControlLabel": self._control_text,
            "Action": "set_focus()",
            "ActionType": "UIControl",
            "Request": self.request,
            "Agent": "HostAgent",
            "AgentName": self.host_agent.name,
            "Application": self.app_root,
            "Cost": self._cost,
            "Results": "",
        }

        host_agent_step_memory.set_values_from_dict(self._response_json)
        host_agent_step_memory.set_values_from_dict(additional_memory)
        self.host_agent.add_memory(host_agent_step_memory)

        # Log the memory item.
        self.log(host_agent_step_memory.to_dict())

        # Only memorize the keys in the HISTORY_KEYS list to feed into the prompt message in the future steps.
        memorized_action = {
            key: host_agent_step_memory.to_dict().get(key)
            for key in configs["HISTORY_KEYS"]
        }
        self.host_agent.add_global_action_memory(memorized_action)

    def update_status(self) -> None:
        """
        Update the status of the session.
        """
        self.host_agent.step += 1
        self.host_agent.status = self._status

        # Wait for the application to be ready after an action is taken before proceeding to the next step.
        if self._status != self._agent_status_manager.FINISH.value:
            time.sleep(configs["SLEEP_TIME"])

    def should_create_subagent(self) -> bool:
        """
        Check if the app agent should be created.
        :return: The boolean value indicating if the app agent should be created.
        """

        # Only create the app agent when the previous status is CONTINUE and the processor is HostAgentProcessor.
        if (
            isinstance(self, HostAgentProcessor)
            and self.agent.state.name() == self._agent_status_manager.CONTINUE.value
        ):
            return True
        else:
            return False

    def create_sub_agent(self) -> AppAgent:
        """
        Create the app agent.
        :return: The app agent.
        """

        # Create the app agent.
        app_agent = self.host_agent.create_subagent(
            "app",
            "AppAgent/{root}/{process}".format(
                root=self.app_root, process=self._control_text
            ),
            self._control_text,
            self.app_root,
            configs["APP_AGENT"]["VISUAL_MODE"],
            configs["APPAGENT_PROMPT"],
            configs["APPAGENT_EXAMPLE_PROMPT"],
            configs["API_PROMPT"],
        )

        # Create the COM receiver for the app agent.
        if configs.get("USE_APIS", False):
            app_agent.Puppeteer.receiver_manager.create_com_receiver(
                self.app_root, self._control_text
            )

        # Provision the context for the app agent, including the all retrievers.
        self.app_agent_context_provision(app_agent)

        return app_agent

    def app_agent_context_provision(self, app_agent: AppAgent) -> None:
        """
        Provision the context for the app agent.
        :param app_agent: The app agent to provision the context.
        """

        # Load the offline document indexer for the app agent if available.
        if configs["RAG_OFFLINE_DOCS"]:
            utils.print_with_color(
                "Loading offline document indexer for {app}...".format(
                    app=self._control_text
                ),
                "magenta",
            )
            app_agent.build_offline_docs_retriever()

        # Load the online search indexer for the app agent if available.
        if configs["RAG_ONLINE_SEARCH"]:
            utils.print_with_color("Creating a Bing search indexer...", "magenta")
            app_agent.build_online_search_retriever(
                self.request, configs["RAG_ONLINE_SEARCH_TOPK"]
            )

        # Load the experience indexer for the app agent if available.
        if configs["RAG_EXPERIENCE"]:
            utils.print_with_color("Creating an experience indexer...", "magenta")
            experience_path = configs["EXPERIENCE_SAVED_PATH"]
            db_path = os.path.join(experience_path, "experience_db")
            app_agent.build_experience_retriever(db_path)

        # Load the demonstration indexer for the app agent if available.
        if configs["RAG_DEMONSTRATION"]:
            utils.print_with_color("Creating an demonstration indexer...", "magenta")
            demonstration_path = configs["DEMONSTRATION_SAVED_PATH"]
            db_path = os.path.join(demonstration_path, "demonstration_db")
            app_agent.build_human_demonstration_retriever(db_path)
