# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from PIL import Image
from pywinauto.controls.uiawrapper import UIAWrapper
from ufo import utils
from ufo.agents.processors.actions import ActionSequence, OneStepAction
from ufo.agents.processors.basic import BaseProcessor
from ufo.agents.processors.app_agent_processor import (
    AppAgentProcessor,
    AppAgentAdditionalMemory,
    AppAgentRequestLog,
)
from ufo.automator.ui_control import ui_tree
from ufo.config.config import Config
from ufo.module.context import Context, ContextNames

if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import OpenAIOperatorAgent

configs = Config.get_instance().config_data

if configs is not None:
    CONTROL_BACKEND = configs.get("CONTROL_BACKEND", ["uia"])
    BACKEND = "win32" if "win32" in CONTROL_BACKEND else "uia"


@dataclass
class AppAgentAdditionalMemory:
    """
    The additional memory data for the AppAgent.
    """

    Step: int
    RoundStep: int
    AgentStep: int
    Round: int
    Subtask: str
    SubtaskIndex: int
    FunctionCall: List[str]
    Action: List[Dict[str, Any]]
    ActionSuccess: List[Dict[str, Any]]
    ActionType: List[str]
    Request: str
    Agent: str
    AgentName: str
    Application: str
    Cost: float
    Results: str
    error: str
    time_cost: Dict[str, float]
    ControlLog: Dict[str, Any]
    UserConfirm: Optional[str] = None


@dataclass
class OpenAIOperatorRequestLog:
    """
    The request log data for the OpenAIOperatorAgent.
    """

    step: int
    image_list: str
    subtask: str
    current_application: str
    host_message: List[str]
    prompt: Dict[str, Any]
    response_id: str
    is_first_step: bool


class OpenAIOperatorProcessor(AppAgentProcessor):
    """
    The processor for the app agent at a single step.
    """

    def __init__(self, agent: "OpenAIOperatorAgent", context: Context) -> None:
        """
        Initialize the app agent processor.
        :param agent: The app agent who executes the processor.
        :param context: The context of the session.
        """

        super().__init__(agent=agent, context=context)

        self.app_agent: "OpenAIOperatorAgent" = agent
        self.host_agent = agent.host

        self._operation = None
        self._args = None
        self._image_url = []
        self.screenshot_save_path = None
        self.width = None
        self.height = None

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """

        # Define the paths for the screenshots saved.
        screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"
        self.screenshot_save_path = screenshot_save_path

        self._memory_data.add_values_from_dict(
            {
                "CleanScreenshot": screenshot_save_path,
                "AnnotatedScreenshot": screenshot_save_path,
                "ConcatScreenshot": screenshot_save_path,
            }
        )

        screenshot: Image = self.photographer.capture_app_window_screenshot(
            self.application_window, save_path=screenshot_save_path
        )
        self.width, self.height = screenshot.size

        self._image_url = self.photographer.encode_image_from_path(screenshot_save_path)

        if configs.get("SAVE_UI_TREE", False):
            if self.application_window is not None:
                step_ui_tree = ui_tree.UITree(self.application_window)
                step_ui_tree.save_ui_tree_to_json(
                    os.path.join(
                        self.ui_tree_path, f"ui_tree_step{self.session_step}.json"
                    )
                )

        if configs.get("SAVE_FULL_SCREEN", False):

            desktop_save_path = (
                self.log_path + f"desktop_action_step{self.session_step}.png"
            )

            self._memory_data.add_values_from_dict(
                {"DesktopCleanScreenshot": desktop_save_path}
            )

            # Capture the desktop screenshot for all screens.
            self.photographer.capture_desktop_screen_screenshot(
                all_screens=True, save_path=desktop_save_path
            )

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def get_control_info(self) -> None:
        """
        Get the control information.
        """
        pass

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def get_prompt_message(self) -> None:
        """
        Get the prompt message for the AppAgent.
        """

        # Check if the current step is the first step.
        is_first_step = self.agent.step == 0

        tools = self.get_tools_info()

        # Construct the prompt message for the OpenAIOperatorAgent.
        self._prompt_message = self.app_agent.message_constructor(
            subtask=self.subtask,
            tools=tools,
            image=self._image_url,
            host_message=self.host_message,
            response_id=self.agent.response_id,
            is_first_step=is_first_step,
        )

        # Log the prompt message. Only save them in debug mode.
        request_data = OpenAIOperatorRequestLog(
            step=self.session_step,
            image_list=self._image_url,
            subtask=self.subtask,
            current_application=self.application_process_name,
            response_id=self.app_agent.response_id,
            is_first_step=is_first_step,
            host_message=self.host_message,
            prompt=self._prompt_message,
        )

        request_log_str = json.dumps(asdict(request_data), ensure_ascii=False)
        self.request_logger.debug(request_log_str)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def get_response(self) -> None:
        """
        Get the response from the LLM.
        """

        print(f"Prompt message: {self._prompt_message}")
        self._response, self.cost = self.app_agent.get_response(
            self._prompt_message, "OPERATOR", use_backup_engine=False
        )
        print(f"Response: {self._response}")

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def parse_response(self) -> None:
        """
        Parse the response.
        """

        self._response_json: Dict[str, Any] = self._response

        action_dict = self._response_json.get("action", {})

        self._operation = action_dict.get("type", "")
        self._args = {k: v for k, v in action_dict.items() if k != "type"}

        output_type = self._response_json.get("output_type", "")

        if output_type != self.agent._continue_type:
            self.status = self._agent_status_manager.FINISH.value

            # Get the message from the Agent.
            if output_type == self.agent._message_type:
                message = ""
                for content in self._response_json.get("content", []):
                    if content.get("type") == "output_text":
                        if content.get("type") == "output_text":
                            message += content.get("text", "")
                self.agent.message = message
        else:
            self.status = self._agent_status_manager.CONTINUE.value

        self.app_agent.print_response(
            response_dict=self._response_json, print_action=True
        )

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def execute_action(self) -> None:
        """
        Execute the action.
        """

        action = OneStepAction(
            function=self._operation,
            args=self._args,
            control_label=self._control_label,
            control_text=self.control_text,
            after_status=self.status,
        )

        # Save the screenshot of the tagged selected control.
        self.capture_control_screenshot(None)

        self.actions: ActionSequence = ActionSequence(actions=[action])
        self.actions.execute_all(
            puppeteer=self.app_agent.Puppeteer,
            control_dict=self._annotation_dict,
            application_window=self.application_window,
        )

        if self.is_application_closed():
            utils.print_with_color("Warning: The application is closed.", "yellow")
            self.status = "FINISH"

    def capture_control_screenshot(
        self, control_selected: Union[UIAWrapper, List[UIAWrapper]]
    ) -> None:
        """
        Capture the screenshot of the selected control.
        :param control_selected: The selected control item or a list of selected control items.
        """
        control_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_selected_controls.png"
        )

        self._memory_data.add_values_from_dict(
            {"SelectedControlScreenshot": control_screenshot_save_path}
        )

        sub_control_list = (
            control_selected
            if isinstance(control_selected, list)
            else [control_selected]
        )

        self.photographer.capture_app_window_screenshot_with_rectangle(
            self.application_window,
            sub_control_list=sub_control_list,
            save_path=control_screenshot_save_path,
            background_screenshot_path=self.screenshot_save_path,
        )

    def handle_screenshot_status(self) -> None:
        """
        Handle the screenshot status when the annotation is overlapped and the agent is unable to select the control items.
        """

        utils.print_with_color(
            "Annotation is overlapped and the agent is unable to select the control items. New annotated screenshot is taken.",
            "magenta",
        )
        self.control_reannotate = self.app_agent.Puppeteer.execute_command(
            "annotation", self._args, self._annotation_dict
        )

    def sync_memory(self):
        """
        Sync the memory of the AppAgent.
        """

        app_root = self.control_inspector.get_application_root_name(
            self.application_window
        )

        action_type = [
            self.app_agent.Puppeteer.get_command_types(action.function)
            for action in self.actions.actions
        ]

        all_previous_success_actions = self.get_all_success_actions()

        action_success = self.actions.to_list_of_dicts(
            success_only=True, previous_actions=all_previous_success_actions
        )

        # Create the additional memory data for the log.
        additional_memory = AppAgentAdditionalMemory(
            Step=self.session_step,
            RoundStep=self.round_step,
            AgentStep=self.app_agent.step,
            Round=self.round_num,
            Subtask=self.subtask,
            SubtaskIndex=self.round_subtask_amount,
            FunctionCall=self.actions.get_function_calls(),
            Action=self.actions.to_list_of_dicts(
                previous_actions=all_previous_success_actions
            ),
            ActionSuccess=action_success,
            ActionType=action_type,
            Request=self.request,
            Agent="AppAgent",
            AgentName=self.app_agent.name,
            Application=app_root,
            Cost=self._cost,
            Results=self.actions.get_results(),
            error=self._exeception_traceback,
            time_cost=self._time_cost,
            ControlLog=self.actions.get_control_logs(),
            UserConfirm=(
                "Yes"
                if self.status.upper()
                == self._agent_status_manager.CONFIRM.value.upper()
                else None
            ),
        )

        # Log the original response from the LLM.
        self.add_to_memory(self._response_json)

        # Log the additional memory data for the AppAgent.
        self.add_to_memory(asdict(additional_memory))

    def update_memory(self) -> None:
        """
        Update the memory of the Agent.
        """

        # Sync the memory of the AppAgent.
        self.sync_memory()

        self.app_agent.add_memory(self._memory_data)

        # Log the memory item.
        self.context.add_to_structural_logs(self._memory_data.to_dict())
        # self.log(self._memory_data.to_dict())

        # Only memorize the keys in the HISTORY_KEYS list to feed into the prompt message in the future steps.
        memorized_action = {
            key: self._memory_data.to_dict().get(key)
            for key in configs.get("HISTORY_KEYS", [])
        }

        if self.is_confirm():

            if self._is_resumed:
                self._memory_data.add_values_from_dict({"UserConfirm": "Yes"})
                memorized_action["UserConfirm"] = "Yes"
            else:
                self._memory_data.add_values_from_dict({"UserConfirm": "No"})
                memorized_action["UserConfirm"] = "No"

        # Save the screenshot to the blackboard if the SaveScreenshot flag is set to True by the AppAgent.
        self._update_image_blackboard()
        self.app_agent.blackboard.add_trajectories(memorized_action)

    def _update_image_blackboard(self) -> None:
        """
        Save the screenshot to the blackboard if the SaveScreenshot flag is set to True by the AppAgent.
        """
        screenshot_saving = self._response_json.get("SaveScreenshot", {})

        if screenshot_saving.get("save", False):

            screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"
            metadata = {
                "screenshot application": self.context.get(
                    ContextNames.APPLICATION_PROCESS_NAME
                ),
                "saving reason": screenshot_saving.get("reason", ""),
            }
            self.app_agent.blackboard.add_image(screenshot_save_path, metadata)

    def _save_to_xml(self) -> None:
        """
        Save the XML file for the current state. Only work for COM objects.
        """
        log_abs_path = os.path.abspath(self.log_path)
        xml_save_path = os.path.join(
            log_abs_path, f"xml/action_step{self.session_step}.xml"
        )
        self.app_agent.Puppeteer.save_to_xml(xml_save_path)

    def get_tools_info(self) -> List[Dict[str, Any]]:
        """
        Get the tools information.
        """

        tools = [
            {
                "type": "computer-preview",
                "display_width": self.width,
                "display_height": self.height,
                "environment": "windows",
            }
        ]

        return tools
