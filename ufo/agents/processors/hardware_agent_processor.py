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
from ufo.automator.ui_control.control_filter import ControlFilterFactory
from ufo.config import Config
from ufo.module.context import Context, ContextNames
from ufo.contracts.contracts import (
    AppWindowControlInfo,
    CaptureAppWindowScreenshotFromWebcamAction,
    CaptureAppWindowScreenshotFromWebcamParams,
    GetAppWindowControlInfoAction,
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
                params=CaptureAppWindowScreenshotFromWebcamParams(annotation_id=None)
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
        pass

        # self.session_data_manager.add_action(
        #     GetAppWindowControlInfoAction(
        #         params=GetAppWindowControlInfoParams(
        #             annotation_id=self.application_window_info.annotation_id,
        #             field_list=ControlInfoRecorder.recording_fields,
        #         )
        #     ),
        #     setter=self._get_app_window_control_info_action_callback,
        # )

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
        # screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"

        # annotated_screenshot_save_path = (
        #     self.log_path + f"action_step{self.session_step}_annotated.png"
        # )

        # self.session_data_manager.add_callback(
        #     lambda value: self._generate_annotated_image(
        #         value, screenshot_save_path, annotated_screenshot_save_path
        #     )
        # )

        # # add callback for operations when data ready
        # self.session_data_manager.add_callback(
        #     lambda value: self._capture_screen_callback(
        #         value,
        #         {
        #             "screenshot_save_path": screenshot_save_path,
        #             "annotated_screenshot_save_path": annotated_screenshot_save_path,
        #         },
        #     )
        # )

        pass

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
            image_list=self.session_data_manager.session_data.state.app_window_screen_url,
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
            image_list=self.session_data_manager.session_data.state.app_window_screen_url,
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

        self.session_data_manager.session_data.state.app_window_screen_url = []

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

        # self._generate_control_screenshot()

    def _execute_mcp_action(self) -> None:
        """
        Execute action using MCP server.
        """
        from ufo.contracts.contracts import (
            MCPToolExecutionAction,
            MCPToolExecutionParams,
        )

        app_namespace = self.app_agent._get_app_namespace()

        print(
            f"Executing MCP tool: {self._operation} with args: {self._args} for {app_namespace}"
        )

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
