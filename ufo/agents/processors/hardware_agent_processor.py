# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional

from ufo import utils
from ufo.utils import collector
from PIL import Image
from ufo.agents.processors.action_contracts import BaseControlLog, OneStepAction
from ufo.agents.processors.basic import BaseProcessor
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.cs.service.control_filter import ControlFilterFactory
from ufo.config import Config
from ufo.module.context import Context, ContextNames
from ufo.cs.contracts import (
    AppWindowControlInfo,
    CaptureAppWindowScreenshotFromWebcamAction,
    CaptureDesktopScreenshotAction,
    ControlInfo,
    GetAppWindowControlInfoAction,
    GetUITreeAction,
    GetUITreeParams,
    OperationCommand,
    OperationSequenceAction,
)
from ufo.cs.contracts import (
    CaptureAppWindowScreenshotParams,
    CaptureDesktopScreenshotParams,
    GetAppWindowControlInfoParams,
)


from ufo.llm import AgentType

if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent

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
class AppAgentControlLog(BaseControlLog):
    """
    The control log data for the AppAgent.
    """

    control_friendly_class_name: str = ""
    control_coordinates: Dict[str, int] = field(default_factory=dict)


@dataclass
class ControlInfoRecorder:
    """
    The control meta information recorder for the current application window.
    """

    recording_fields: ClassVar[List[str]] = [
        "control_text",
        "control_type" if BACKEND == "uia" else "control_class",
        "control_rect",
        "source",
    ]

    application_windows_info: Dict[str, Any] = field(default_factory=dict)
    uia_controls_info: List[Dict[str, Any]] = field(default_factory=dict)
    grounding_controls_info: List[Dict[str, Any]] = field(default_factory=dict)
    merged_controls_info: List[Dict[str, Any]] = field(default_factory=dict)


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


class HardwareAgentProcessor(AppAgentProcessor):
    """
    The processor for the app agent at a single step.
    """

    def __init__(self, agent: "AppAgent", context: Context) -> None:
        """
        Initialize the app agent processor.
        :param agent: The app agent who executes the processor.
        :param context: The context of the session.
        """

        super().__init__(agent=agent, context=context)

        self.mcp_enabled = configs.get("USE_MCP", False)

        self.app_agent = agent
        self.host_agent = agent.host

        # self._annotation_dict = None
        # self._control_info = None
        self._operation = ""
        self._args = {}
        # self._image_url = []
        # self.session_data_manager.session_data.state.app_winddow_screen_url = []
        self.control_filter_factory = ControlFilterFactory()
        self.control_recorder = ControlInfoRecorder()
        # self.filtered_annotation_dict = None
        self.screenshot_save_path = None
        self._mcp_execution_result = None

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

        self.session_data_manager.add_action(
            CaptureAppWindowScreenshotFromWebcamAction(
                params=CaptureAppWindowScreenshotParams(annotation_id=None)
            ),
            setter=self._get_app_window_screenshot_action_callback,
        )

        # removed control_recorder as it is not used in the code
        # moved annotated image generation to process_collected_info

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def get_control_info(self) -> None:
        """
        Get the control information.
        """

        self.session_data_manager.add_action(
            GetAppWindowControlInfoAction(
                params=GetAppWindowControlInfoParams(
                    annotation_id=self.application_window_info.annotation_id,
                    field_list=ControlInfoRecorder.recording_fields,
                )
            ),
            setter=self._get_app_window_control_info_action_callback,
        )

    def _get_app_window_control_info_action_callback(self, value):
        if isinstance(value, AppWindowControlInfo):
            model = value
        elif isinstance(value, dict):
            model = AppWindowControlInfo(**value)
        else:
            raise ValueError(
                f"Expected AppWindowControlInfo or dict, got {type(value)}"
            )
        self.session_data_manager.session_data.state.app_window_control_info = model

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def process_collected_info(self) -> None:
        screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"

        annotated_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_annotated.png"
        )

        self.session_data_manager.add_callback(
            lambda value: self._generate_annotated_image(
                value, screenshot_save_path, annotated_screenshot_save_path
            )
        )

        # add callback for operations when data ready
        self.session_data_manager.add_callback(
            lambda value: self._capture_screen_callback(
                value,
                {
                    "screenshot_save_path": screenshot_save_path,
                    "annotated_screenshot_save_path": annotated_screenshot_save_path,
                },
            )
        )

    def _generate_annotated_image(
        self, value, screenshot_save_path, annotated_screenshot_save_path
    ):
        """
        Helper method to generate annotated image.

        Args:
            value: The result returned from the action
        """
        self.session_data_manager.session_data.state._annotation_dict = {
            control.annotation_id: control
            for control in self.session_data_manager.session_data.state.app_window_control_info.controls
        }

        self.session_data_manager.session_data.state.filtered_annotation_dict = (
            self.get_filtered_annotation_dict(
                self.session_data_manager.session_data.state._annotation_dict
            )
        )

        if BACKEND == "uia":
            self.session_data_manager.session_data.state._control_info = [
                dict(
                    label=item[0],
                    control_text=item[1].name,
                    control_type=item[1].control_type,
                )
                for item in self.session_data_manager.session_data.state._annotation_dict.items()
            ]

            self.session_data_manager.session_data.state.filtered_control_info = [
                dict(
                    label=item[0],
                    control_text=item[1].name,
                    control_type=item[1].control_type,
                )
                for item in self.session_data_manager.session_data.state.filtered_annotation_dict.items()
            ]
        else:
            self._control_info = [
                dict(
                    label=item[0],
                    control_class=item[1].class_name,
                )
                for item in self.session_data_manager.session_data.state._annotation_dict.items()
            ]

            self.session_data_manager.session_data.state.filtered_control_info = [
                dict(
                    label=item[0],
                    control_class=item[1].class_name,
                )
                for item in self.session_data_manager.session_data.state.filtered_annotation_dict.items()
            ]

        image = Image.open(screenshot_save_path)

        annotated_image: Image.Image = collector.annotate_app_window_image(
            image,
            self.session_data_manager.session_data.state.app_window_control_info.window_info,
            self.session_data_manager.session_data.state.app_window_control_info.controls,
        )

        if annotated_image:
            os.makedirs(os.path.dirname(annotated_screenshot_save_path), exist_ok=True)

            with open(annotated_screenshot_save_path, "wb") as f:
                annotated_image.save(f, format="PNG")

    def _capture_all_desktop_screenshot_action_callback(self, value, path):
        """
        Helper method to save desktop screenshot data and save to file.

        Args:
            value: The result returned from the action
            path: Path to save the screenshot
        """

        if (
            value
            and isinstance(value, str)
            and value.startswith("data:image/png;base64,")
        ):
            try:
                img_data = utils.decode_base64_image(value)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    f.write(img_data)
            except Exception as e:
                print(f"Error saving image: {e}")

    def _capture_screen_callback(self, value, params: Dict[str, str]):
        """
        Helper method to save screenshot data.

        Args:
            value: The result returned from the action
            params: The parameters for the action
        """
        if params:
            screenshot_save_path = params.get("screenshot_save_path")
            annotated_screenshot_save_path = params.get(
                "annotated_screenshot_save_path"
            )
            concat_screenshot_save_path = params.get("concat_screenshot_save_path")

        if configs.get("INCLUDE_LAST_SCREENSHOT", True):
            last_screenshot_save_path = (
                self.log_path + f"action_step{self.session_step - 1}.png"
            )
            last_control_screenshot_save_path = (
                self.log_path
                + f"action_step{self.session_step - 1}_selected_controls.png"
            )

            image_path = (
                last_control_screenshot_save_path
                if os.path.exists(last_control_screenshot_save_path)
                else last_screenshot_save_path
            )
            # self._image_url += [utils.encode_image_from_path(image_path)]
            self.session_data_manager.session_data.state.app_winddow_screen_url += [
                utils.encode_image_from_path(image_path)
            ]

        # Whether to concatenate the screenshots of clean screenshot and annotated screenshot into one image.
        if configs.get("CONCAT_SCREENSHOT", False):
            collector.concat_screenshots(
                screenshot_save_path,
                annotated_screenshot_save_path,
                concat_screenshot_save_path,
            )
            # self._image_url += [
            #     utils.encode_image_from_path(concat_screenshot_save_path)
            # ]
            self.session_data_manager.session_data.state.app_winddow_screen_url += [
                utils.encode_image_from_path(concat_screenshot_save_path)
            ]
        else:
            screenshot_url = utils.encode_image_from_path(screenshot_save_path)
            screenshot_annotated_url = utils.encode_image_from_path(
                annotated_screenshot_save_path
            )
            # self._image_url += [screenshot_url, screenshot_annotated_url]
            self.session_data_manager.session_data.state.app_winddow_screen_url += [
                screenshot_url,
                screenshot_annotated_url,
            ]

        # Save the XML file for the current state.
        if configs.get("LOG_XML", False):
            self._save_to_xml()

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def get_prompt_message(self) -> None:
        """
        Get the prompt message for the AppAgent.
        """

        experience_results, demonstration_results = (
            self.app_agent.demonstration_prompt_helper(request=self.subtask)
        )

        retrieved_results = experience_results + demonstration_results

        # Get the external knowledge prompt for the AppAgent using the offline and online retrievers.

        offline_docs, online_docs = self.app_agent.external_knowledge_prompt_helper(
            self.subtask,
            configs.get("RAG_OFFLINE_DOCS_RETRIEVED_TOPK", 0),
            configs.get("RAG_ONLINE_RETRIEVED_TOPK", 0),
        )

        # print(offline_docs, online_docs)

        external_knowledge_prompt = offline_docs + online_docs

        if not self.app_agent.blackboard.is_empty():
            blackboard_prompt = self.app_agent.blackboard.blackboard_to_prompt()
        else:
            blackboard_prompt = []

        # Get the last successful actions of the AppAgent.
        last_success_actions = self.get_last_success_actions()

        action_keys = ["Function", "Args", "ControlText", "Results", "RepeatTimes"]

        filtered_last_success_actions = [
            {key: action.get(key, "") for key in action_keys}
            for action in last_success_actions
        ]

        # Construct the prompt message for the AppAgent.
        self._prompt_message = self.app_agent.message_constructor(
            dynamic_examples=retrieved_results,
            dynamic_knowledge=external_knowledge_prompt,
            image_list=self.session_data_manager.session_data.state.app_winddow_screen_url,
            control_info=self.session_data_manager.session_data.state.filtered_control_info,
            prev_subtask=self.previous_subtasks,
            plan=self.prev_plan,
            request=self.request,
            subtask=self.subtask,
            current_application=self.application_process_name,
            host_message=self.host_message,
            blackboard_prompt=blackboard_prompt,
            last_success_actions=filtered_last_success_actions,
            include_last_screenshot=configs.get("INCLUDE_LAST_SCREENSHOT", True),
        )

        # Log the prompt message. Only save them in debug mode.
        request_data = AppAgentRequestLog(
            step=self.session_step,
            experience_examples=experience_results,
            demonstration_examples=demonstration_results,
            dynamic_examples=retrieved_results,
            offline_docs=offline_docs,
            online_docs=online_docs,
            dynamic_knowledge=external_knowledge_prompt,
            image_list=self.session_data_manager.session_data.state.app_winddow_screen_url,
            prev_subtask=self.previous_subtasks,
            plan=self.prev_plan,
            request=self.request,
            control_info=self.session_data_manager.session_data.state.filtered_control_info,
            subtask=self.subtask,
            current_application=self.application_process_name,
            host_message=self.host_message,
            blackboard_prompt=blackboard_prompt,
            last_success_actions=filtered_last_success_actions,
            include_last_screenshot=configs.get("INCLUDE_LAST_SCREENSHOT", True),
            prompt=self._prompt_message,
            control_info_recording=asdict(self.control_recorder),
        )

        self.session_data_manager.session_data.state.app_winddow_screen_url = []

        request_log_str = json.dumps(asdict(request_data), ensure_ascii=False)
        self.request_logger.debug(request_log_str)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def get_response(self) -> None:
        """
        Get the response from the LLM.
        """

        retry = 0
        while retry < configs.get("JSON_PARSING_RETRY", 3):
            # Try to get the response from the LLM. If an error occurs, catch the exception and log the error.
            self._response, self.cost = self.app_agent.get_response(
                self._prompt_message, AgentType.APP, use_backup_engine=True
            )

            try:
                self.app_agent.response_to_dict(self._response)
                break
            except Exception as e:
                print("Error in parsing response: ", e)
                retry += 1

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
        if configs.get(AgentType.APP).get("JSON_SCHEMA", False):
            self._args = utils.revise_line_breaks(
                json.loads(self._response_json.get("Args", ""))
            )
        else:
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

        self._execute_mcp_action()

        self._generate_control_screenshot()

    def _execute_mcp_action(self) -> None:
        """
        Execute action using MCP server.
        """
        from ufo.cs.contracts import MCPToolExecutionAction, MCPToolExecutionParams

        app_namespace = self.app_agent._get_app_namespace()

        # Create the MCP tool execution action
        mcp_action = MCPToolExecutionAction(
            params=MCPToolExecutionParams(
                app_namespace=app_namespace,
                tool_name=self._operation,
                tool_args=self._args,
            )
        )

        # Add action to session with callback for result handling
        self.session_data_manager.add_action(
            mcp_action,
            setter=lambda result: self._handle_mcp_execution_callback(result),
        )

        utils.print_with_color(
            f"Added MCP tool execution to session: {self._operation} for {app_namespace}",
            "blue",
        )

    def _handle_mcp_execution_callback(self, result: Any) -> None:
        """
        Callback to handle MCP tool execution result.
        :param result: The result from the MCP tool execution
        """
        try:
            if result and isinstance(result, dict):
                success = result.get("success", False)
                if success:
                    utils.print_with_color(
                        f"MCP tool execution successful: {result.get('tool_name', 'unknown')}",
                        "green",
                    )
                    # Store the result for memory and logging
                    self._mcp_execution_result = result
                else:
                    error_msg = result.get("error", "Unknown error")
                    utils.print_with_color(
                        f"MCP tool execution failed: {error_msg}", "red"
                    )
                    # Could fallback to UI automation here if needed
                    self._mcp_execution_result = result
            else:
                utils.print_with_color(
                    f"Received unexpected MCP execution result type: {type(result)}",
                    "yellow",
                )
        except Exception as e:
            utils.print_with_color(
                f"Error handling MCP execution callback: {str(e)}", "red"
            )

    def sync_memory(self):
        """
        Sync the memory of the AppAgent.
        """

        app_root = self.app_root
        # app_root is set in the selecte_app and launch_app actions
        # and should not change as app agent is for a single app
        # app_root = self.application_window_info.process_name
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
