# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from PIL import Image
from pywinauto.controls.uiawrapper import UIAWrapper
from ufo import utils
from ufo.agents.processors.actions import ActionSequence, OneStepAction
from ufo.agents.processors.basic import BaseProcessor
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
class AppAgentRequestLog:
    """
    The request log data for the AppAgent.
    """

    step: int
    dynamic_examples: List[str]
    experience_examples: List[str]
    demonstration_examples: List[str]
    offline_docs: str
    online_docs: str
    dynamic_knowledge: str
    image_list: List[str]
    prev_subtask: List[str]
    plan: List[str]
    request: str
    control_info: List[Dict[str, str]]
    subtask: str
    current_application: str
    host_message: str
    blackboard_prompt: List[str]
    last_success_actions: List[Dict[str, Any]]
    include_last_screenshot: bool
    prompt: Dict[str, Any]
    control_info_recording: Dict[str, Any]


class OpenAIOperatorProcessor(BaseProcessor):
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

        self.app_agent = agent
        self.host_agent = agent.host

        self._operation = None
        self._args = None
        self._image_url = []
        self.screenshot_save_path = None
        self.width = None
        self.height = None

    def print_step_info(self) -> None:
        """
        Print the step information.
        """
        utils.print_with_color(
            "Round {round_num}, Step {step}, AppAgent: Completing the subtask [{subtask}] on application [{application}].".format(
                round_num=self.round_num + 1,
                step=self.round_step + 1,
                subtask=self.subtask,
                application=self.application_process_name,
            ),
            "magenta",
        )

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """

        # Define the paths for the screenshots saved.
        screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"
        self.screenshot_save_path = screenshot_save_path

        annotated_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_annotated.png"
        )
        concat_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_concat.png"
        )

        self._memory_data.add_values_from_dict(
            {
                "CleanScreenshot": screenshot_save_path,
                "AnnotatedScreenshot": annotated_screenshot_save_path,
                "ConcatScreenshot": concat_screenshot_save_path,
            }
        )

        screenshot: Image = self.photographer.capture_app_window_screenshot(
            self.application_window, save_path=screenshot_save_path
        )
        self.width, self.height = screenshot.size

        # Capture the screenshot of the selected control items with annotation and save it.
        self.photographer.capture_app_window_screenshot_with_annotation_dict(
            self.application_window,
            [],
            annotation_type="number",
            save_path=annotated_screenshot_save_path,
        )

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

        if self.round_step == 0:
            self._prompt_message = self.subtask

        else:
            self._prompt_message = [
                {
                    "type": "computer_call_output",
                    "call_id": self.previous_computer_id,
                    "output": {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{self._image_url}",
                    },
                }
            ]

        # Construct the prompt message for the AppAgent.
        self._prompt_message = self.app_agent.message_constructor(
            image_list=self._image_url,
            subtask=self.subtask,
        )

        # Log the prompt message. Only save them in debug mode.
        request_data = AppAgentRequestLog(
            step=self.session_step,
            image_list=self._image_url,
            subtask=self.subtask,
            current_application=self.application_process_name,
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

        self._response, self.cost = self.app_agent.get_response(
            self._prompt_message, "APPAGENT", use_backup_engine=True
        )

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def parse_response(self) -> None:
        """
        Parse the response.
        """

        self._response_json = self.app_agent.response_to_dict(self._response)

        self.control_label = self._response_json.get("ControlLabel", "")
        self.control_text = self._response_json.get("ControlText", "")
        self._operation = self._response_json.get("Function", "")
        self.question_list = self._response_json.get("Questions", [])
        self._args = utils.revise_line_breaks(self._response_json.get("Args", ""))

        # Convert the plan from a string to a list if the plan is a string.
        self.plan = self.string2list(self._response_json.get("Plan", ""))
        self._response_json["Plan"] = self.plan

        self.status = self._response_json.get("Status", "")
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
        control_selected = self._annotation_dict.get(self._control_label, None)

        # Save the screenshot of the tagged selected control.
        self.capture_control_screenshot(control_selected)

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
        self.host_agent.blackboard.add_trajectories(memorized_action)

    def get_all_success_actions(self) -> List[Dict[str, Any]]:
        """
        Get the previous action.
        :return: The previous action of the agent.
        """
        agent_memory = self.app_agent.memory

        if agent_memory.length > 0:
            success_action_memory = agent_memory.filter_memory_from_keys(
                ["ActionSuccess"]
            )
            success_actions = []
            for success_action in success_action_memory:
                success_actions += success_action.get("ActionSuccess", [])

        else:
            success_actions = []

        return success_actions

    def get_last_success_actions(self) -> List[Dict[str, Any]]:
        """
        Get the previous action.
        :return: The previous action of the agent.
        """
        agent_memory = self.app_agent.memory

        if agent_memory.length > 0:
            last_success_actions = (
                agent_memory.get_latest_item().to_dict().get("ActionSuccess", [])
            )

        else:
            last_success_actions = []

        return last_success_actions

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
