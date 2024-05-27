# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import os
import time
from logging import Logger
from typing import Dict, List, Optional, Tuple

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agent.agent import AppAgent, HostAgent
from ufo.agent.basic import MemoryItem
from ufo.automator.ui_control.control_filter import ControlFilterFactory
from ufo.config.config import Config
from ufo.module import interactor
from ufo.module.processors.basic import BaseProcessor
from ufo.module.state import Status

configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]


class HostAgentProcessor(BaseProcessor):
    """
    The processor for the host agent at a single step.
    """

    def __init__(
        self,
        round_num: int,
        log_path: str,
        request: str,
        request_logger: Logger,
        logger: Logger,
        host_agent: HostAgent,
        round_step: int,
        session_step: int,
        prev_status: str,
        app_window=None,
    ) -> None:
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

        super().__init__(
            round_num=round_num,
            log_path=log_path,
            request=request,
            request_logger=request_logger,
            logger=logger,
            round_step=round_step,
            session_step=session_step,
            prev_status=prev_status,
            app_window=app_window,
        )

        self.host_agent = host_agent

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
                "step": self._step,
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
        self._plan = self._response_json.get("Plan", "")
        self._status = self._response_json.get("Status", "")
        self.app_to_open = self._response_json.get("AppsToOpen", None)

        self.host_agent.print_response(self._response_json)

        if (
            Status.FINISH in self._status.upper()
            or self._control_text == ""
            and self.app_to_open is None
        ):
            self._status = Status.FINISH

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
            self._status = Status.ERROR
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
        if new_app_window is not self._app_window and self._app_window is not None:
            utils.print_with_color("Switching to a new application...", "magenta")
            self._app_window.minimize()
        self._app_window = new_app_window

    def update_memory(self) -> None:
        """
        Update the memory of the Agent.
        """

        # Create a memory item for the host agent at the current step.
        host_agent_step_memory = MemoryItem()

        # Log additional information for the host agent.
        additional_memory = {
            "Step": self.session_step,
            "RoundStep": self.get_process_step(),
            "AgentStep": self.host_agent.get_step(),
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
        self.host_agent.update_step()
        self.host_agent.update_status(self._status)

        # Wait for the application to be ready after an action is taken before proceeding to the next step.
        if self._status != Status.FINISH:
            time.sleep(configs["SLEEP_TIME"])

    def should_create_subagent(self) -> bool:
        """
        Check if the app agent should be created.
        :return: The boolean value indicating if the app agent should be created.
        """

        # Only create the app agent when the previous status is APP_SELECTION and the processor is HostAgentProcessor.
        if (
            isinstance(self, HostAgentProcessor)
            and self.prev_status == Status.APP_SELECTION
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


class AppAgentProcessor(BaseProcessor):
    """
    The processor for the app agent at a single step.
    """

    def __init__(
        self,
        round_num: int,
        log_path: str,
        request: str,
        request_logger: Logger,
        logger: Logger,
        app_agent: AppAgent,
        round_step: int,
        session_step: int,
        process_name: str,
        app_window: UIAWrapper,
        control_reannotate: Optional[list],
        prev_status: str,
    ) -> None:
        """
        Initialize the app agent processor.
        :param round_num: The total number of rounds in the session.
        :param log_path: The log path.
        :param request: The user request.
        :param request_logger: The logger for the request string.
        :param logger: The logger for the response and error.
        :param app_agent: The app agent to process the current step.
        :param round_step: The number of steps in the round.
        :param session_step: The global step of the session.
        :param process_name: The process name.
        :param app_window: The application window.
        :param control_reannotate: The list of controls to reannotate.
        :param prev_status: The previous status of the session.
        """

        super().__init__(
            round_num=round_num,
            log_path=log_path,
            request=request,
            request_logger=request_logger,
            logger=logger,
            round_step=round_step,
            session_step=session_step,
            prev_status=prev_status,
            app_window=app_window,
        )

        self.app_agent = app_agent
        self.process_name = process_name

        self._annotation_dict = None
        self._control_info = None
        self._operation = None
        self._args = None
        self._image_url = []
        self.prev_plan = []
        self._control_reannotate = control_reannotate
        self.control_filter_factory = ControlFilterFactory()
        self.filtered_annotation_dict = None

    def print_step_info(self) -> None:
        """
        Print the step information.
        """
        utils.print_with_color(
            "Round {round_num}, Step {step}: Taking an action on application {application}.".format(
                round_num=self.round_num + 1,
                step=self.round_step + 1,
                application=self.process_name,
            ),
            "magenta",
        )

    def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """

        # Define the paths for the screenshots saved.
        screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"
        annotated_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_annotated.png"
        )
        concat_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_concat.png"
        )

        # Get the control elements in the application window if the control items are not provided for reannotation.
        if type(self._control_reannotate) == list and len(self._control_reannotate) > 0:
            control_list = self._control_reannotate
        else:
            control_list = self.control_inspector.find_control_elements_in_descendants(
                self._app_window,
                control_type_list=configs["CONTROL_LIST"],
                class_name_list=configs["CONTROL_LIST"],
            )

        # Get the annotation dictionary for the control items, in a format of {control_label: control_element}.
        self._annotation_dict = self.photographer.get_annotation_dict(
            self._app_window, control_list, annotation_type="number"
        )

        self.prev_plan = self.get_prev_plan()

        # Attempt to filter out irrelevant control items based on the previous plan.
        self.filtered_annotation_dict = self.get_filtered_annotation_dict(
            self._annotation_dict
        )
        self.photographer.capture_app_window_screenshot(
            self._app_window, save_path=screenshot_save_path
        )

        # Capture the screenshot of the selected control items with annotation and save it.
        self.photographer.capture_app_window_screenshot_with_annotation_dict(
            self._app_window,
            self.filtered_annotation_dict,
            annotation_type="number",
            save_path=annotated_screenshot_save_path,
        )

        # If the configuration is set to include the last screenshot with selected controls tagged, save the last screenshot.
        if configs["INCLUDE_LAST_SCREENSHOT"]:
            last_screenshot_save_path = (
                self.log_path + f"action_step{self.session_step - 1}.png"
            )
            last_control_screenshot_save_path = (
                self.log_path
                + f"action_step{self.session_step - 1}_selected_controls.png"
            )
            self._image_url += [
                self.photographer.encode_image_from_path(
                    last_control_screenshot_save_path
                    if os.path.exists(last_control_screenshot_save_path)
                    else last_screenshot_save_path
                )
            ]

        # Whether to concatenate the screenshots of clean screenshot and annotated screenshot into one image.
        if configs["CONCAT_SCREENSHOT"]:
            self.photographer.concat_screenshots(
                screenshot_save_path,
                annotated_screenshot_save_path,
                concat_screenshot_save_path,
            )
            self._image_url += [
                self.photographer.encode_image_from_path(concat_screenshot_save_path)
            ]
        else:
            screenshot_url = self.photographer.encode_image_from_path(
                screenshot_save_path
            )
            screenshot_annotated_url = self.photographer.encode_image_from_path(
                annotated_screenshot_save_path
            )
            self._image_url += [screenshot_url, screenshot_annotated_url]

    def get_control_info(self) -> None:
        """
        Get the control information.
        """

        # Get the control information for the control items and the filtered control items, in a format of list of dictionaries.
        self._control_info = self.control_inspector.get_control_info_list_of_dict(
            self._annotation_dict,
            ["control_text", "control_type" if BACKEND == "uia" else "control_class"],
        )
        self.filtered_control_info = (
            self.control_inspector.get_control_info_list_of_dict(
                self.filtered_annotation_dict,
                [
                    "control_text",
                    "control_type" if BACKEND == "uia" else "control_class",
                ],
            )
        )

    def get_prompt_message(self) -> None:
        """
        Get the prompt message for the AppAgent.
        """

        examples, tips = self.demonstration_prompt_helper()

        # Get the external knowledge prompt for the AppAgent using the offline and online retrievers.
        external_knowledge_prompt = self.app_agent.external_knowledge_prompt_helper(
            self.request,
            configs["RAG_OFFLINE_DOCS_RETRIEVED_TOPK"],
            configs["RAG_ONLINE_RETRIEVED_TOPK"],
        )

        # Get the action history and request history of the host agent and feed them into the prompt message.
        host_agent = self.app_agent.get_host()
        action_history = host_agent.get_global_action_memory().to_json()
        request_history = host_agent.get_request_history_memory().to_json()

        # Construct the prompt message for the AppAgent.
        self._prompt_message = self.app_agent.message_constructor(
            examples,
            tips,
            external_knowledge_prompt,
            self._image_url,
            request_history,
            action_history,
            self.filtered_control_info,
            self.prev_plan,
            self.request,
            configs["INCLUDE_LAST_SCREENSHOT"],
        )

        # Log the prompt message. Only save them in debug mode.
        log = json.dumps(
            {
                "step": self.session_step,
                "prompt": self._prompt_message,
                "control_items": self._control_info,
                "filted_control_items": self.filtered_control_info,
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
            self._response, self._cost = self.app_agent.get_response(
                self._prompt_message, "APPAGENT", use_backup_engine=True
            )
        except Exception:
            self.llm_error_handler()
            return

    def parse_response(self) -> None:
        """
        Parse the response.
        """

        # Try to parse the response. If an error occurs, catch the exception and log the error.
        try:
            self._response_json = self.app_agent.response_to_dict(self._response)

        except Exception:
            self.general_error_handler()

        self._control_label = self._response_json.get("ControlLabel", "")
        self._control_text = self._response_json.get("ControlText", "")
        self._operation = self._response_json.get("Function", "")
        self._args = utils.revise_line_breaks(self._response_json.get("Args", ""))
        self._plan = self._response_json.get("Plan", "")
        self._status = self._response_json.get("Status", "")

        self.app_agent.print_response(self._response_json)

    def execute_action(self) -> None:
        """
        Execute the action.
        """

        try:
            # Get the selected control item from the annotation dictionary and LLM response. The LLm response is a number index corresponding to the key in the annotation dictionary.
            control_selected = self._annotation_dict.get(self._control_label, "")

            if control_selected:
                control_selected.draw_outline(colour="red", thickness=3)
                time.sleep(configs.get("RECTANGLE_TIME", 0))

            self.app_agent.Puppeteer.receiver_manager.create_ui_control_receiver(
                control_selected, self._app_window
            )

            # Save the screenshot of the tagged selected control.
            self.capture_control_screenshot(control_selected)

            # Compose the function call and the arguments string.
            self._action = self.app_agent.Puppeteer.get_command_string(
                self._operation, self._args
            )

            # Whether to proceed with the action.
            should_proceed = True

            # Safe guard for the action.
            if self._status.upper() == Status.PENDING and configs["SAFE_GUARD"]:
                should_proceed = self._safe_guard_judgement(
                    self._action, self._control_text
                )

            # Execute the action if the user decides to proceed or safe guard is not enabled.
            if should_proceed:
                self._results = self.app_agent.Puppeteer.execute_command(
                    self._operation, self._args
                )
                if not utils.is_json_serializable(self._results):
                    self._results = ""
            else:
                self._results = "The user decide to stop the task."

                return

            # Handle the case when the annotation is overlapped and the agent is unable to select the control items.
            self.handle_screenshot_status()

        except Exception:
            self.general_error_handler()

    def capture_control_screenshot(self, control_selected: UIAWrapper) -> None:
        """
        Capture the screenshot of the selected control.
        :param control_selected: The selected control item.
        """
        control_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_selected_controls.png"
        )
        self.photographer.capture_app_window_screenshot_with_rectangle(
            self._app_window,
            sub_control_list=[control_selected],
            save_path=control_screenshot_save_path,
        )

    def handle_screenshot_status(self) -> None:
        """
        Handle the screenshot status when the annotation is overlapped and the agent is unable to select the control items.
        """

        if self._status.upper() == Status.SCREENSHOT:
            utils.print_with_color(
                "Annotation is overlapped and the agent is unable to select the control items. New annotated screenshot is taken.",
                "magenta",
            )
            self._control_reannotate = self.app_agent.Puppeteer.execute_command(
                "annotation", self._args, self._annotation_dict
            )
            if self._control_reannotate is None or len(self._control_reannotate) == 0:
                self._status = Status.CONTINUE
        else:
            self._control_reannotate = None

    def update_memory(self) -> None:
        """
        Update the memory of the Agent.
        """
        # Create a memory item for the app agent
        app_agent_step_memory = MemoryItem()

        app_root = self.control_inspector.get_application_root_name(self._app_window)
        host_agent = self.app_agent.get_host()

        # Log additional information for the app agent.
        additional_memory = {
            "Step": self.session_step,
            "RoundStep": self.get_process_step(),
            "AgentStep": self.app_agent.get_step(),
            "Round": self.round_num,
            "Action": self._action,
            "ActionType": self.app_agent.Puppeteer.get_command_types(self._operation),
            "Request": self.request,
            "Agent": "ActAgent",
            "AgentName": self.app_agent.name,
            "Application": app_root,
            "Cost": self._cost,
            "Results": self._results,
        }
        app_agent_step_memory.set_values_from_dict(self._response_json)
        app_agent_step_memory.set_values_from_dict(additional_memory)

        self.app_agent.add_memory(app_agent_step_memory)

        # Log the memory item.
        self.log(app_agent_step_memory.to_dict())

        # Only memorize the keys in the HISTORY_KEYS list to feed into the prompt message in the future steps.
        memorized_action = {
            key: app_agent_step_memory.to_dict().get(key)
            for key in configs["HISTORY_KEYS"]
        }
        host_agent.add_global_action_memory(memorized_action)

    def update_status(self) -> None:
        """
        Update the status of the session.
        """

        self.app_agent.update_step()
        self.app_agent.update_status(self._status)

        if self._status != Status.FINISH:
            time.sleep(configs["SLEEP_TIME"])

    def _safe_guard_judgement(self, action: str, control_text: str) -> bool:
        """
        Safe guard for the session.
        action: The action to be taken.
        control_text: The text of the control item.
        return: The boolean value indicating whether to proceed or not.
        """

        # Ask the user whether to proceed with the action when the status is PENDING.
        decision = interactor.sensitive_step_asker(action, control_text)
        if not decision:
            utils.print_with_color("The user decide to stop the task.", "magenta")
            self._status = Status.FINISH
            return False

        # Handle the PENDING_AND_FINISH case
        elif len(self._plan) > 0 and Status.FINISH in self._plan[0]:
            self._status = Status.FINISH
        return True

    def get_control_reannotate(self) -> List[UIAWrapper]:
        """
        Get the control to reannotate.
        :return: The control to reannotate.
        """

        return self._control_reannotate

    def get_prev_plan(self) -> str:
        """
        Retrieves the previous plan from the agent's memory.
        :return: The previous plan, or an empty string if the agent's memory is empty.
        """
        agent_memory = self.app_agent.memory

        if agent_memory.length > 0:
            prev_plan = agent_memory.get_latest_item().to_dict()["Plan"]
        else:
            prev_plan = []

        return prev_plan

    def demonstration_prompt_helper(self) -> Tuple[List[str], List[str]]:
        """
        Get the examples and tips for the AppAgent using the demonstration retriever.
        :return: The examples and tips for the AppAgent.
        """

        # Get the examples and tips for the AppAgent using the experience and demonstration retrievers.
        if configs["RAG_EXPERIENCE"]:
            experience_examples, experience_tips = (
                self.app_agent.rag_experience_retrieve(
                    self.request, configs["RAG_EXPERIENCE_RETRIEVED_TOPK"]
                )
            )
        else:
            experience_examples = []
            experience_tips = []

        if configs["RAG_DEMONSTRATION"]:
            demonstration_examples, demonstration_tips = (
                self.app_agent.rag_demonstration_retrieve(
                    self.request, configs["RAG_DEMONSTRATION_RETRIEVED_TOPK"]
                )
            )
        else:
            demonstration_examples = []
            demonstration_tips = []

        examples = experience_examples + demonstration_examples
        tips = experience_tips + demonstration_tips

        return examples, tips

    def get_filtered_annotation_dict(
        self, annotation_dict: Dict[str, UIAWrapper]
    ) -> Dict[str, UIAWrapper]:
        """
        Get the filtered annotation dictionary.
        :param annotation_dict: The annotation dictionary.
        :return: The filtered annotation dictionary.
        """

        # Get the control filter type and top k plan from the configuration.
        control_filter_type = configs["CONTROL_FILTER_TYPE"]
        topk_plan = configs["CONTROL_FILTER_TOP_K_PLAN"]

        if len(control_filter_type) == 0 or self.prev_plan == []:
            return annotation_dict

        control_filter_type_lower = [
            control_filter_type_lower.lower()
            for control_filter_type_lower in control_filter_type
        ]

        filtered_annotation_dict = {}

        # Get the top k recent plans from the memory.
        plans = self.control_filter_factory.get_plans(self.prev_plan, topk_plan)

        # Filter the annotation dictionary based on the keywords of control text and plan.
        if "text" in control_filter_type_lower:
            model_text = self.control_filter_factory.create_control_filter("text")
            filtered_text_dict = model_text.control_filter(annotation_dict, plans)
            filtered_annotation_dict = (
                self.control_filter_factory.inplace_append_filtered_annotation_dict(
                    filtered_annotation_dict, filtered_text_dict
                )
            )

        # Filter the annotation dictionary based on the semantic similarity of the control text and plan with their embeddings.
        if "semantic" in control_filter_type_lower:
            model_semantic = self.control_filter_factory.create_control_filter(
                "semantic", configs["CONTROL_FILTER_MODEL_SEMANTIC_NAME"]
            )
            filtered_semantic_dict = model_semantic.control_filter(
                annotation_dict, plans, configs["CONTROL_FILTER_TOP_K_SEMANTIC"]
            )
            filtered_annotation_dict = (
                self.control_filter_factory.inplace_append_filtered_annotation_dict(
                    filtered_annotation_dict, filtered_semantic_dict
                )
            )

        # Filter the annotation dictionary based on the icon image icon and plan with their embeddings.
        if "icon" in control_filter_type_lower:
            model_icon = self.control_filter_factory.create_control_filter(
                "icon", configs["CONTROL_FILTER_MODEL_ICON_NAME"]
            )

            cropped_icons_dict = self.photographer.get_cropped_icons_dict(
                self._app_window, annotation_dict
            )
            filtered_icon_dict = model_icon.control_filter(
                annotation_dict,
                cropped_icons_dict,
                plans,
                configs["CONTROL_FILTER_TOP_K_ICON"],
            )
            filtered_annotation_dict = (
                self.control_filter_factory.inplace_append_filtered_annotation_dict(
                    filtered_annotation_dict, filtered_icon_dict
                )
            )

        return filtered_annotation_dict
