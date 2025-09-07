# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional

from pywinauto.controls.uiawrapper import UIAWrapper
from ufo.agents.processors.target import TargetKind, TargetRegistry
from ufo import utils
from ufo.agents.processors.actions import BaseControlLog, ActionCommandInfo
from ufo.agents.processors.basic import BaseProcessor
from ufo.automator.ui_control.control_filter import ControlFilterFactory
from ufo.automator.ui_control.grounding.basic import BasicGrounding
from ufo.automator.ui_control.inspector import ControlInspectorFacade
from ufo.config import Config
from ufo.contracts.contracts import Command
from ufo.llm import AgentType
from ufo.module.context import Context, ContextNames

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
    control_info_recording: Optional[Dict[str, Any]] = None


@dataclass
class AppAgentResponse:
    """
    The response data for the AppAgent.
    """

    observation: str
    thought: str
    status: str
    plan: Optional[List[str]] = None
    comment: Optional[str] = None
    function: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    save_screenshot: Optional[Dict[str, Any]] = None


class AppAgentProcessor(BaseProcessor):
    """
    The processor for the app agent at a single step.
    """

    def __init__(
        self,
        agent: "AppAgent",
        context: Context,
        ground_service=Optional[BasicGrounding],
    ) -> None:
        """
        Initialize the app agent processor.
        :param agent: The app agent who executes the processor.
        :param context: The context of the session.
        """

        super().__init__(agent=agent, context=context)

        self.app_agent = agent
        self.host_agent = agent.host

        self._image_url = []
        self.control_filter_factory = ControlFilterFactory()
        self.control_recorder = ControlInfoRecorder()
        self.screenshot_save_path = None
        self.control_inspector = ControlInspectorFacade()
        self.grounding_service = ground_service

        self.target_registry = TargetRegistry()

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
        self.logger.info(
            "Round {round_num}, Step {step}, AppAgent: Completing the subtask [{subtask}] on application [{application}].".format(
                round_num=self.round_num + 1,
                step=self.round_step + 1,
                subtask=self.subtask,
                application=self.application_process_name,
            )
        )

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def capture_screenshot(self) -> None:
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

        # Save the screenshot and get the current application window information and set the windows state.
        await self.save_application_window_screenshot(screenshot_save_path)

        control_list = await self.collect_window_control_info(screenshot_save_path)

        self._annotation_dict = self.photographer.get_annotation_dict(
            self.application_window, control_list, annotation_type="number"
        )

        # Attempt to filter out irrelevant control items based on the previous plan.
        self.filtered_annotation_dict = self.get_filtered_annotation_dict(
            self._annotation_dict
        )

        # Capture the screenshot of the selected control items with annotation and save it.
        self.photographer.capture_app_window_screenshot_with_annotation_dict(
            self.application_window,
            self.filtered_annotation_dict,
            annotation_type="number",
            save_path=annotated_screenshot_save_path,
            path=screenshot_save_path,
            highlight_bbox=configs.get("HIGHLIGHT_BBOX", False),
        )

        if configs.get("SAVE_UI_TREE", False):
            await self.save_ui_tree()

        if configs.get("SAVE_FULL_SCREEN", False):

            await self.save_desktop_screenshot()

        # If the configuration is set to include the last screenshot with selected controls tagged, save the last screenshot.
        if configs.get("INCLUDE_LAST_SCREENSHOT", True):
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
        if configs.get("CONCAT_SCREENSHOT", False):
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

    async def save_application_window_screenshot(
        self, screenshot_save_path: str
    ) -> None:
        """
        Get the current application window information and set the windows state.
        :param screenshot_save_path: The file path to save the screenshot.
        """

        result = await self.context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="capture_window_screenshot",
                    parameters={},
                    tool_type="data_collection",
                )
            ]
        )

        clean_screenshot_url = result[0].result
        utils.save_image_string(clean_screenshot_url, screenshot_save_path)
        self.logger.info(f"Clean screenshot saved to {screenshot_save_path}")

        result = await self.context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="get_app_window_info",
                    parameters={"field_list": ControlInfoRecorder.recording_fields},
                    tool_type="data_collection",
                )
            ]
        )

        self.control_recorder.application_windows_info = result[0].result

        self.logger.info(
            f"Application window information: {self.control_recorder.application_windows_info}"
        )

        # Convert the application window information to a virtual UIA representation.
        self.application_window = self.convert_controls_info_to_uia(
            [self.control_recorder.application_windows_info]
        )[0]

    async def save_ui_tree(self):
        """
        Save the UI tree of the current application window.
        """
        if self.application_window is not None:
            result = await self.context.command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="get_ui_tree",
                        parameters={},
                        tool_type="data_collection",
                    )
                ]
            )
            step_ui_tree = result[0].result
            ui_tree_path = os.path.join(
                self.ui_tree_path, f"ui_tree_step{self.session_step}.json"
            )
            save_dir = os.path.dirname(ui_tree_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            with open(ui_tree_path, "w") as file:
                json.dump(step_ui_tree, file, indent=4)

    async def save_desktop_screenshot(self):
        """
        Save the full screenshot of the desktop.
        """

        desktop_save_path = (
            self.log_path + f"desktop_action_step{self.session_step}.png"
        )

        self._memory_data.add_values_from_dict(
            {"DesktopCleanScreenshot": desktop_save_path}
        )

        # Capture the desktop screenshot for all screens.

        result = await self.context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="capture_desktop_screenshot",
                    parameters={"all_screens": True},
                    tool_type="data_collection",
                )
            ]
        )

        desktop_screenshot_url = result[0].result
        utils.save_image_string(desktop_screenshot_url, desktop_save_path)
        self.logger.info(f"Desktop screenshot saved to {desktop_save_path}")

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def get_control_info(self) -> None:
        """
        Get the control information.
        """

        # Get the control information for the control items and the filtered control items, in a format of list of dictionaries.
        filtered_control_info = self.control_inspector.get_control_info_list_of_dict(
            self.filtered_annotation_dict,
            ["control_text", "control_type", "control_rect"],
        )

        revised_filtered_control_info = [
            {
                "kind": TargetKind.CONTROL,
                "id": control["label"],
                "name": control["control_text"],
                "type": control["control_type"],
                "rect": control["control_rect"],
            }
            for control in filtered_control_info
        ]

        self.target_registry.register_from_dicts(revised_filtered_control_info)

        self.logger.info(
            f"Get {len(revised_filtered_control_info)} filtered control items"
        )

    async def collect_uia_controls_info(self) -> List[UIAWrapper]:
        """
        Collect UIA control information.
        """
        result = await self.context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="get_app_window_controls_info",
                    parameters={"field_list": ControlInfoRecorder.recording_fields},
                    tool_type="data_collection",
                )
            ]
        )
        api_controls_info = result[0].result
        self.logger.info(
            f"Get {len(api_controls_info)} API controls from current application window"
        )
        self.control_recorder.uia_controls_info = api_controls_info
        api_control_list = self.convert_controls_info_to_uia(api_controls_info)

        return api_control_list

    async def collect_grounding_control_info(self, screenshot_path) -> List[UIAWrapper]:
        """
        Collect grounding control information.
        """
        self.grounding_service: BasicGrounding

        omniparser_configs = configs.get("OMNIPARSER", {})

        # print(omniparser_configs)

        grounding_control_list = self.grounding_service.convert_to_virtual_uia_elements(
            image_path=screenshot_path,
            application_window=self.application_window,
            box_threshold=omniparser_configs.get("BOX_THRESHOLD", 0.05),
            iou_threshold=omniparser_configs.get("IOU_THRESHOLD", 0.1),
            use_paddleocr=omniparser_configs.get("USE_PADDLEOCR", True),
            imgsz=omniparser_configs.get("IMGSZ", 640),
        )
        self.logger.info(f"Get {len(grounding_control_list)} grounding controls")

        # TODO: Server should send command to register grounding controls, to be implemented.

        grounding_control_dict = {
            i + 1: control for i, control in enumerate(grounding_control_list)
        }

        self.control_recorder.grounding_controls_info = (
            self.control_inspector.get_control_info_list_of_dict(
                grounding_control_dict, ControlInfoRecorder.recording_fields
            )
        )

        return grounding_control_list

    async def collect_window_control_info(
        self, screenshot_path: str
    ) -> List[UIAWrapper]:
        """
        Get the control list from the annotation dictionary.
        :param screenshot_path: The path to the clean screenshot.
        :return: The list of control items.
        """

        grounding_backend = None

        control_detection_backend = configs.get("CONTROL_BACKEND", ["uia"])

        if "omniparser" in control_detection_backend:
            grounding_backend = "omniparser"

        if "uia" in control_detection_backend:

            api_control_list = await self.collect_uia_controls_info()

        else:
            api_control_list = []
        # print(control_detection_backend, grounding_backend, screenshot_path)

        if grounding_backend == "omniparser" and self.grounding_service is not None:
            grounding_control_list = await self.collect_grounding_control_info(
                screenshot_path
            )
        else:
            grounding_control_list = []

        merged_control_list = self.photographer.merge_control_list(
            api_control_list,
            grounding_control_list,
            iou_overlap_threshold=configs.get("IOU_THRESHOLD_FOR_MERGE", 0.1),
        )

        self.logger.info(
            f"Get {len(merged_control_list)} merged controls from current application window"
        )
        merged_control_dict = {
            i + 1: control for i, control in enumerate(merged_control_list)
        }

        # Record the control information for the merged controls.
        self.control_recorder.merged_controls_info = (
            self.control_inspector.get_control_info_list_of_dict(
                merged_control_dict, ControlInfoRecorder.recording_fields
            )
        )

        return merged_control_list

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def get_prompt_message(self) -> None:
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

        self.logger.debug(f"Last success actions: {last_success_actions}")

        action_keys = ["function", "arguments", "Results", "RepeatTimes"]

        filtered_last_success_actions = [
            {key: action.get(key, "") for key in action_keys}
            for action in last_success_actions
        ]

        # Construct the prompt message for the AppAgent.
        self._prompt_message = self.app_agent.message_constructor(
            dynamic_examples=retrieved_results,
            dynamic_knowledge=external_knowledge_prompt,
            image_list=self._image_url,
            control_info=self.target_registry.to_list(keep_keys=["id", "name", "type"]),
            prev_subtask=self.previous_subtasks,
            plan=self.prev_plan,
            request=self.request,
            subtask=self.subtask,
            current_application=self.application_process_name,
            host_message=self.host_message,
            blackboard_prompt=blackboard_prompt,
            last_success_actions=last_success_actions,
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
            image_list=self._image_url,
            prev_subtask=self.previous_subtasks,
            plan=self.prev_plan,
            request=self.request,
            control_info=self.target_registry.to_list(keep_keys=["id", "name", "type"]),
            subtask=self.subtask,
            current_application=self.application_process_name,
            host_message=self.host_message,
            blackboard_prompt=blackboard_prompt,
            last_success_actions=filtered_last_success_actions,
            include_last_screenshot=configs.get("INCLUDE_LAST_SCREENSHOT", True),
            prompt=self._prompt_message,
            control_info_recording=asdict(self.control_recorder),
        )

        request_log_str = json.dumps(asdict(request_data), ensure_ascii=False)
        self.request_logger.write(request_log_str)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def get_response(self) -> None:
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

        response_dict = self.app_agent.response_to_dict(self._response)

        self.response = AppAgentResponse(**response_dict)

        if type(self.response.arguments) == dict:
            if "id" in self.response.arguments:
                self.control_label = self.response.arguments.get("id", "")
            if "name" in self.response.arguments:
                self.control_text = self.response.arguments.get("name", "")

        arguments = self.response.arguments

        if type(arguments) == dict:
            self.response.arguments = utils.revise_line_breaks(arguments)
        else:
            args = json.loads(arguments)
            self.response.arguments = utils.revise_line_breaks(args)

        # Convert the plan from a string to a list if the plan is a string.
        self.plan = self.string2list(self.response.plan)
        self.status = self.response.status

        # self.status = self._response_json.get("Status", "")
        self.app_agent.print_response(response=self.response, print_action=True)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def execute_action(self) -> None:
        """
        Execute the action.
        """

        if not self.response.function:
            utils.print_with_color(
                "No action to execute. Skipping execution.", "yellow"
            )
            return

        result = await self.context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name=self.response.function,
                    parameters=self.response.arguments,
                    tool_type="action",
                )
            ]
        )

        self.logger.info(f"Result for execution of {self.response.function}: {result}")

        control_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_selected_controls.png"
        )

        self._memory_data.add_values_from_dict(
            {"SelectedControlScreenshot": control_screenshot_save_path}
        )

        control_selected = self._annotation_dict.get(self._control_label, None)

        self.photographer.capture_app_window_screenshot_with_rectangle(
            self.application_window,
            sub_control_list=[control_selected],
            save_path=control_screenshot_save_path,
            background_screenshot_path=self.screenshot_save_path,
        )

        action = ActionCommandInfo(
            function=self.response.function,
            arguments=self.response.arguments,
            target=self.target_registry.get(self.control_label),
            status=self.response.status,
            result=result[0],
        )

        self.actions.add_action(action)

    def sync_memory(self):
        """
        Sync the memory of the AppAgent.
        """

        app_root = self.app_root

        action_type = [action.result.namespace for action in self.actions.actions]

        all_previous_success_actions = self.get_all_success_actions()

        action_success = self.actions.to_list_of_dicts(
            success_only=True,
            previous_actions=all_previous_success_actions,
            keep_keys=["action_string", "result", "repeat_time"],
        )

        self.logger.debug(f"Current action success: {action_success}")

        self.logger.debug(
            f"All previous success actions: {all_previous_success_actions}"
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
            Agent=self.agent.__class__.__name__,
            AgentName=self.app_agent.name,
            Application=app_root,
            Cost=self._cost,
            Results=self.actions.get_results(),
            error=self._exeception_traceback,
            time_cost=self._time_cost,
            ControlLog=self.actions.get_target_info(),
            UserConfirm=(
                "Yes"
                if self.response.status.upper()
                == self._agent_status_manager.CONFIRM.value.upper()
                else None
            ),
        )

        # Log the original response from the LLM.
        self.add_to_memory(asdict(self.response))

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

        self.logger.info(f"Memorized action: {memorized_action}")

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

    def get_filtered_annotation_dict(
        self, annotation_dict: Dict[str, UIAWrapper], configs: Dict[str, Any] = configs
    ) -> Dict[str, UIAWrapper]:
        """
        Get the filtered annotation dictionary.
        :param annotation_dict: The annotation dictionary.
        :param configs: The configuration dictionary.
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
                self.application_window, annotation_dict
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

    @staticmethod
    def convert_controls_info_to_uia(
        controls_info_list: List[Dict[str, Any]],
    ) -> List[UIAWrapper]:
        """
        Convert ControlInfo to UIA properties and add to the API control list.
        :param control_info: The ControlInfo object to convert.
        :param api_control_list: The list to append the converted UIA properties.
        :return: None
        """

        control_list = []

        for control_info in controls_info_list:

            left, top, right, bottom = control_info.get("control_rect", [0, 0, 0, 0])

            new_control_info = {
                "control_type": control_info.get("control_type", "Button"),
                "name": control_info.get("control_text", ""),
                "x0": left,
                "y0": top,
                "x1": right,
                "y1": bottom,
            }

            virtual_uia = BasicGrounding.uia_wrapping(new_control_info)

            control_list.append(virtual_uia)

        return control_list
