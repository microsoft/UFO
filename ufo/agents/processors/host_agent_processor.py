# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import time
from typing import TYPE_CHECKING

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agents.memory.memory import MemoryItem
from ufo.agents.processors.basic import BaseProcessor
from ufo.config.config import Config
from ufo.module.context import Context, ContextNames

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
        :param agent: The host agent to be processed.
        :param context: The context.
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

        # Get the previous plan from the memory. If the memory is empty, set the plan to an empty string.
        agent_memory = self.host_agent.memory
        if agent_memory.length > 0:
            plan = agent_memory.get_latest_item().to_dict()["Plan"]
        else:
            plan = []

        # Construct the prompt message for the host agent.
        self._prompt_message = self.host_agent.message_constructor(
            [self._desktop_screen_url],
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
            self._response, self.cost = self.host_agent.get_response(
                self._prompt_message, "HOSTAGENT", use_backup_engine=True
            )

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
        self.control_text = self._response_json.get("ControlText", "")

        # Convert the plan from a string to a list if the plan is a string.
        self._plan = self.string2list(self._response_json.get("Plan", ""))
        self._response_json["Plan"] = self._plan

        self.status = self._response_json.get("Status", "")
        self.question_list = self._response_json.get("Questions", [])

        self.app_to_open = self._response_json.get("AppsToOpen", None)

        self.host_agent.print_response(self._response_json)

    def execute_action(self) -> None:
        """
        Execute the action.
        """

        # When the required application is not opened, try to open the application and set the focus to the application window.
        if self.app_to_open is not None:
            new_app_window = self.host_agent.app_file_manager(self.app_to_open)
            self.control_text = new_app_window.window_text()
        else:
            # Get the application window
            new_app_window = self._desktop_windows_dict.get(self.control_label, None)

        if new_app_window is None:

            self.status = self._agent_status_manager.FINISH.value
            return

        # Get the root name of the application.
        self.app_root = self.control_inspector.get_application_root_name(new_app_window)

        # Check if the window interface is available for the visual element.
        if not self.is_window_interface_available(new_app_window):
            self.status = self._agent_status_manager.ERROR.value

            return

        # Switch to the new application window, if it is different from the current application window.
        self.switch_to_new_app_window(new_app_window)
        self.application_window.set_focus()
        self.application_window.draw_outline(colour="red", thickness=3)

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
                    title=self.control_text
                ),
                "red",
            )
            return False

    def switch_to_new_app_window(self, new_app_window: UIAWrapper) -> None:
        """
        Switch to the new application window if it is different from the current application window.
        :param new_app_window: The new application window.
        """

        if (
            new_app_window != self.application_window
            and self.application_window is not None
        ):
            utils.print_with_color("Switching to a new application...", "magenta")

        self.application_window = new_app_window

        self.context.set(ContextNames.APPLICATION_WINDOW, self.application_window)

        self.context.set(ContextNames.APPLICATION_ROOT_NAME, self.app_root)
        self.context.set(ContextNames.APPLICATION_PROCESS_NAME, self.control_text)

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
            "ControlLabel": self.control_text,
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

        self.host_agent.blackboard.add_trajectories(memorized_action)
