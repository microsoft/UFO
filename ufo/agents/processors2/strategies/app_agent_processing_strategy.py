# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
App Agent Processing Strategies V2 - Modular strategies for App Agent using the new framework.

This module contains all the processing strategies for App Agent including:
- Screenshot capture and UI control information collection
- Control filtering and annotation
- LLM interaction with app-specific prompting
- Action execution and control interaction
- Memory management and blackboard updates

Each strategy is designed to be modular, testable, and follows the dependency injection pattern.
"""

import json
import os
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, List, Optional


from ufo import utils
from ufo.agents.memory.memory import MemoryItem
from ufo.agents.processors.actions import ActionCommandInfo
from ufo.agents.processors.app_agent_processor import (
    AppAgentAdditionalMemory,
    AppAgentRequestLog,
    AppAgentResponse,
    ControlInfoRecorder,
)
from ufo.agents.processors.target import TargetInfo, TargetKind, TargetRegistry
from ufo.agents.processors2.strategies.processing_strategy import BaseProcessingStrategy
from ufo.agents.processors2.core.processing_context import (
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
)
from ufo.agents.processors2.core.strategy_dependency import (
    depends_on,
    provides,
)
from ufo.automator.ui_control.grounding.omniparser import OmniparserGrounding
from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.config import Config
from ufo.contracts.contracts import Command, Result, ResultStatus
from ufo.llm import AgentType
from ufo.llm.grounding_model.omniparser_service import OmniParser
from ufo.module.basic import FileWriter
from ufo.module.context import ContextNames
from ufo.module.dispatcher import BasicCommandDispatcher

# Load configuration
configs = Config.get_instance().config_data

if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent

if configs is not None:
    CONTROL_BACKEND = configs.get("CONTROL_BACKEND", ["uia"])
    BACKEND = "win32" if "win32" in CONTROL_BACKEND else "uia"


@depends_on("app_root", "log_path", "session_step")
@provides(
    "clean_screenshot_path",
    "annotated_screenshot_path",
    "desktop_screenshot_path",
    "ui_tree_path",
    "clean_screenshot_url",
    "desktop_screenshot_url",
    "application_window_info",
    "screenshot_saved_time",
)
class AppScreenshotCaptureStrategy(BaseProcessingStrategy):
    """
    Strategy for capturing application screenshots and desktop screenshots.

    This strategy handles:
    - Application window screenshot capture
    - Desktop screenshot capture (if needed)
    - Screenshot path management and storage
    - Performance timing for screenshot operations
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize screenshot capture strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="app_screenshot_capture", fail_fast=fail_fast)

    async def execute(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute screenshot capture for App Agent.
        :param agent: The AppAgent instance
        :param context: Processing context with app information
        :return: ProcessingResult with screenshot paths and timing
        """
        try:
            import time

            start_time = time.time()

            # Extract context variables
            log_path = context.get("log_path", "")
            session_step = context.get("session_step", 0)
            command_dispatcher = context.global_context.command_dispatcher

            # Step 1: Capture application window screenshot
            self.logger.info("Capturing application window screenshot")
            clean_screenshot_path = f"{log_path}action_step{session_step}.png"

            clean_screenshot_url = await self._capture_app_screenshot(
                clean_screenshot_path, command_dispatcher
            )

            # Step 2: Capture desktop screenshot if needed
            desktop_screenshot_path = f"{log_path}desktop_step{session_step}.png"

            if configs.get("SAVE_FULL_SCREEN", False):
                self.logger.info("Capturing desktop screenshot")
                desktop_screenshot_url = await self._capture_desktop_screenshot(
                    desktop_screenshot_path, command_dispatcher
                )
            else:
                desktop_screenshot_url = ""

            # Step 3: Capture ui tree if needed.
            ui_tree_path = os.path.join(
                log_path, "ui_trees", f"ui_tree_step{session_step}.json"
            )
            if configs.get("SAVE_UI_TREE", False):
                self.logger.info("Capturing UI tree")
                await self._capture_ui_tree(ui_tree_path, command_dispatcher)

            # Step 4: Get application window information
            self.logger.info("Getting application window information")
            application_window_info = await self._get_application_window_info(
                command_dispatcher
            )

            screenshot_time = time.time() - start_time

            return ProcessingResult(
                success=True,
                data={
                    "clean_screenshot_path": clean_screenshot_path,
                    "desktop_screenshot_path": desktop_screenshot_path,
                    "screenshot_saved_time": screenshot_time,
                    "ui_tree_path": ui_tree_path,
                    "clean_screenshot_url": clean_screenshot_url,
                    "desktop_screenshot_url": desktop_screenshot_url,
                    "application_window_info": application_window_info,
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            error_msg = f"Screenshot capture failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    async def _capture_app_screenshot(
        self, save_path: str, command_dispatcher: BasicCommandDispatcher
    ) -> str:
        """
        Capture application window screenshot.
        :param save_path: The path for saving screenshots
        :param command_dispatcher: Command dispatcher for executing commands
        :return: The path to the saved screenshot
        """
        try:
            # Generate screenshot paths

            # Execute capture_window_screenshot command (matching original implementation)
            if not command_dispatcher:
                raise ValueError("Command dispatcher not available")

            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="capture_window_screenshot",
                        parameters={},
                        tool_type="data_collection",
                    )
                ]
            )

            if (
                not result
                or not result[0].result
                or result[0].status != ResultStatus.SUCCESS
            ):
                raise ValueError("Failed to capture window screenshot")

            clean_screenshot_url = result[0].result
            utils.save_image_string(clean_screenshot_url, save_path)
            self.logger.info(f"Clean screenshot saved to: {save_path}")

            return clean_screenshot_url

        except Exception as e:
            raise Exception(f"Failed to capture app screenshot: {str(e)}")

    async def _get_application_window_info(
        self, command_dispatcher: BasicCommandDispatcher
    ) -> None:
        """
        Get application window information and set up the application window (from original implementation).
        :param command_dispatcher: Command dispatcher for executing commands
        """
        try:
            if not command_dispatcher:
                raise ValueError("Command dispatcher not available")

            # Get application window information
            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="get_app_window_info",
                        parameters={"field_list": ControlInfoRecorder.recording_fields},
                        tool_type="data_collection",
                    )
                ]
            )

            if result and result[0].result:
                app_window_info = result[0].result
                self.logger.info(f"Application window information: {app_window_info}")

                # Convert to virtual UIA representation (from original implementation)
                application_window_target_info = TargetInfo(
                    kind=TargetKind.WINDOW,
                    name=app_window_info.get("control_text"),
                    type=app_window_info.get("control_type"),
                    rect=app_window_info.get("control_rect"),
                    # Add other relevant fields as needed
                )

                # Store in global context for other strategies to use
                return application_window_target_info
            else:
                self.logger.error(f"Application window info is empty")

        except Exception as e:
            self.logger.warning(f"Failed to get application window info: {str(e)}")

    async def _capture_ui_tree(
        self, save_path: str, command_dispatcher: BasicCommandDispatcher
    ) -> Dict[str, Any]:
        """
        Capture UI tree.
        :param save_path: The log path for saving UI tree
        :param command_dispatcher: Command dispatcher for executing commands
        :return: The dict of UI tree.
        """
        try:

            # Execute get_ui_tree command
            if not command_dispatcher:
                raise ValueError("Command dispatcher not available")

            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="get_ui_tree",
                        parameters={},
                        tool_type="data_collection",
                    )
                ]
            )

            if not result or not result[0].result:
                raise ValueError("Failed to capture UI tree")

            save_dir = os.path.dirname(save_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            with open(save_path, "w") as file:
                json.dump(result[0].result, file, indent=4)

            self.logger.info(f"UI tree saved to: {save_path}")

            return result[0].result

        except Exception as e:
            raise Exception(f"Failed to capture UI tree: {str(e)}")

    async def _capture_desktop_screenshot(
        self, save_path: str, command_dispatcher: BasicCommandDispatcher
    ) -> str:
        """
        Capture desktop screenshot if needed.
        :param save_path: The path for saving screenshots
        :param command_dispatcher: Command dispatcher for executing commands
        :return: Desktop screenshot string
        """
        try:

            # Check if desktop screenshot is needed based on configuration
            # include_last_screenshot = configs.get("INCLUDE_LAST_SCREENSHOT", False)

            # if include_last_screenshot:
            if command_dispatcher:
                # Execute desktop screenshot command
                result = await command_dispatcher.execute_commands(
                    [
                        Command(
                            tool_name="capture_desktop_screenshot",
                            parameters={"all_screens": True},
                            tool_type="data_collection",
                        )
                    ]
                )

                if result and result[0].result:
                    desktop_screenshot_url = result[0].result
                    utils.save_image_string(desktop_screenshot_url, save_path)
                    self.logger.info(f"Desktop screenshot saved to: {save_path}")

            return desktop_screenshot_url

        except Exception as e:
            self.logger.warning(f"Desktop screenshot capture failed: {str(e)}")
            return ""


@depends_on("clean_screenshot_path", "application_window_info")
@provides(
    "control_info",
    "annotation_dict",
    "control_filter_time",
    "control_info_recorder",
    "annotated_screenshot_path",
    "annotated_screenshot_url",
)
class AppControlInfoStrategy(BaseProcessingStrategy):
    """
    Strategy for collecting and filtering UI control information.

    This strategy handles:
    - UI control tree collection via UIA
    - Control filtering based on various criteria
    - Control annotation and grounding
    - Performance timing for control operations
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize control info strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="app_control_info", fail_fast=fail_fast)
        self.photographer = PhotographerFacade()
        self.control_detection_backend = configs.get("CONTROL_BACKEND", ["uia"])
        self.control_recorder = ControlInfoRecorder()

        if "omniparser" in self.control_detection_backend:
            self.grounding_service = self._init_omniparser_service()
        else:
            self.grounding_service = None

    def _init_omniparser_service(self) -> Optional[OmniparserGrounding]:
        """
        Initialized for the OmniParser service.
        """
        omniparser_endpoint = configs.get("OMNIPARSER", {}).get("ENDPOINT", "")
        if omniparser_endpoint:
            omniparser_service = OmniParser(endpoint=omniparser_endpoint)
            return OmniparserGrounding(service=omniparser_service)
        else:
            self.logger.warning("OmniParser endpoint is not configured.")
            return None

    async def execute(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute control information collection and filtering.
        :param agent: The AppAgent instance
        :param context: Processing context with screenshot information
        :return: ProcessingResult with filtered controls and timing
        """
        try:
            import time

            start_time = time.time()

            self.logger.info("Collecting UI control information")

            # Extract context variables
            target_registry: TargetRegistry = context.local_context.get(
                "target_registry"
            )
            application_window_info: TargetInfo = context.get("application_window_info")
            clean_screenshot_path = context.get("clean_screenshot_path")
            command_dispatcher = context.global_context.command_dispatcher
            log_path = context.get("log_path", "")
            session_step = context.get("session_step", 0)

            # Step 1: Getting control info from UIA
            if "uia" in self.control_detection_backend:
                self.logger.info("Collecting Control Information from UIA API...")
                api_control_list = await self._collect_uia_controls(command_dispatcher)
                self.control_recorder.uia_controls_info = api_control_list

                self.logger.info(
                    f"Collected {len(api_control_list)} controls from UIA."
                )
            else:
                api_control_list = []

            # Step 2: Getting control info from OmniParser
            if (
                "omniparser" in self.control_detection_backend
                and self.grounding_service
            ):
                self.logger.info("Collecting Control Information from OmniParser...")

                grounding_control_list = await self._collect_grounding_controls(
                    clean_screenshot_path, application_window_info
                )
                self.control_recorder.grounding_controls_info = grounding_control_list
                self.logger.info(
                    f"Collected {len(grounding_control_list)} controls from OmniParser."
                )
            else:
                grounding_control_list = []

            # Step 3: Merging control list
            merged_control_list = self._collect_merged_control_list(
                api_control_list, grounding_control_list
            )
            self.control_recorder.merged_controls_info = merged_control_list
            self.control_recorder.application_windows_info = application_window_info

            self.logger.info(
                f"Collected {len(merged_control_list)} controls after merging."
            )

            target_registry.register(merged_control_list)

            # Step 4: Taking annotated screenshot.
            annotation_dict = self._create_annotation_dict(merged_control_list)

            annotated_screenshot_path = (
                f"{log_path}action_step{session_step}_annotated.png"
            )

            annotated_screenshot_url = self._save_annotated_screenshot(
                clean_screenshot_path,
                target_registry.all_targets(),
                annotated_screenshot_path,
            )

            control_filter_time = time.time() - start_time

            return ProcessingResult(
                success=True,
                data={
                    "control_recorder": self.control_recorder,
                    "control_info": target_registry.all_targets(),  # Alias for backward compatibility
                    "annotation_dict": annotation_dict,
                    "control_filter_time": control_filter_time,
                    "annotated_screenshot_path": annotated_screenshot_path,
                    "annotated_screenshot_url": annotated_screenshot_url,
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            error_msg = f"Control info collection failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    def _create_annotation_dict(
        self, control_info_list: List[TargetInfo]
    ) -> Dict[str, TargetInfo]:
        """
        Create a dict of control base on their id.
        :param control_info_list: The list of control information
        :return: A dictionary mapping control IDs to their information
        """
        return {control_info.id: control_info for control_info in control_info_list}

    async def _collect_uia_controls(
        self, command_dispatcher: BasicCommandDispatcher
    ) -> List[TargetInfo]:
        """
        Collect UIA controls from the application window.
        :param command_dispatcher: Command dispatcher for executing commands
        :return: List of UIA controls
        """
        try:
            # Execute get_app_window_controls_info command (matching original implementation)
            if not command_dispatcher:
                raise ValueError("Command dispatcher not available")

            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="get_app_window_controls_target_info",
                        parameters={"field_list": ControlInfoRecorder.recording_fields},
                        tool_type="data_collection",
                    )
                ]
            )

            if not result:
                return []

            api_controls_info = result[0].result
            self.logger.info(
                f"Get {len(api_controls_info)} API controls from current application window"
            )

            return api_controls_info

        except Exception as e:
            self.logger.warning(f"UIA control collection failed: {str(e)}")
            return []

    async def _collect_grounding_controls(
        self,
        clean_screenshot_path: str,
        application_window_info: TargetInfo,
    ) -> List[TargetInfo]:
        """
        Collect controls using grounding service.
        :param clean_screenshot_path: Path to the clean screenshot
        :param application_window_info: Information about the application window
        :return: List of grounded controls
        """

        try:
            if not clean_screenshot_path or not os.path.exists(clean_screenshot_path):
                return []

            # Use grounding service to detect controls
            grounding_controls = self.grounding_service.screen_parsing(
                clean_screenshot_path, application_window_info
            )
            return grounding_controls

        except Exception as e:
            self.logger.warning(f"Grounding control collection failed: {str(e)}")
            return []

    def _collect_merged_control_list(
        self,
        api_control_list: List[TargetInfo],
        grounding_control_list: List[TargetInfo],
    ) -> List[TargetInfo]:
        """
        Collect merged control list from UIA and grounding sources (using optimized approach).
        :param api_control_list: The list of API controls
        :param grounding_control_list: The list of grounding controls
        :return: List of merged UI controls
        """
        try:
            merged_control_list = self.photographer.merge_target_info_list(
                api_control_list,
                grounding_control_list,
                iou_overlap_threshold=configs.get("IOU_THRESHOLD_FOR_MERGE", 0.1),
            )
            return merged_control_list

        except Exception as e:
            self.logger.warning(f"Control collection failed: {str(e)}")
            return []

    async def _save_annotated_screenshot(
        self,
        clean_screenshot_path: str,
        target_list: Dict[str, TargetInfo],
        save_path: str,
    ) -> str:
        """
        Save annotated screenshot using photographer with optimized TargetRegistry approach.
        :param clean_screenshot_path: Path to the clean screenshot
        :param target_list: List of TargetInfo objects
        :param save_path: The saved path of the annotated screenshot
        :return: The return annotated image string
        """
        try:
            self.photographer.capture_app_window_screenshot_with_target_list(
                target_list=target_list,
                path=clean_screenshot_path,
                save_path=save_path,
                highlight_bbox=True,
            )

            annotated_screenshot_url = self.photographer.encode_image_from_path(
                save_path
            )
            return annotated_screenshot_url
        except Exception as e:
            self.logger.warning(f"Failed to save annotated screenshot: {str(e)}")
            return None


@depends_on("control_info", "clean_screenshot_path", "request")
@provides(
    "parsed_response",
    "response_text",
    "llm_cost",
    "prompt_message",
    "status",
    "function_name",
    "function_arguments",
    "save_screenshot",
)
class AppLLMInteractionStrategy(BaseProcessingStrategy):
    """
    Strategy for LLM interaction with App Agent specific prompting.

    This strategy handles:
    - Context-aware prompt construction with app-specific data
    - Control information integration in prompts
    - LLM interaction with retry logic
    - Response parsing and validation
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize App Agent LLM interaction strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="app_llm_interaction", fail_fast=fail_fast)

    async def execute(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute LLM interaction for App Agent.
        :param agent: The AppAgent instance
        :param context: Processing context with control and screenshot data
        :return: ProcessingResult with parsed response and cost
        """
        try:
            # Extract context variables
            control_info = context.get("control_info", [])
            clean_screenshot_path = context.get("clean_screenshot_path", "")
            request = context.get("request", "")
            subtask = context.get("subtask", "")
            plan = context.get("plan", [])
            prev_subtask = context.get("previous_subtasks", [])
            host_message = context.global_context.get(ContextNames.HOST_MESSAGE)
            application_process_name = context.global_context.get(
                ContextNames.APPLICATION_PROCESS_NAME
            )
            desktop_screenshot_path = context.get("desktop_screenshot_path", "")
            session_step = context.get("session_step", 0)
            request_logger = context.global_context.get(ContextNames.REQUEST_LOGGER)
            log_path = context.get("log_path", "")
            annotated_screenshot_path = context.get("annotated_screenshot_path")

            # Step 1: Collect image strings:

            self.logger.info("Collecting screenshots...")
            last_control_screenshot_path = (
                log_path + f"action_step{session_step - 1}_selected_controls.png"
            )

            concat_screenshot_path = log_path + f"action_step{session_step}_concat.png"

            image_string_list = self._collect_image_strings(
                last_control_screenshot_path,
                clean_screenshot_path,
                annotated_screenshot_path,
                concat_screenshot_path,
            )

            # Step 2: Retrieve knowledge from the knowledge base
            self.logger.info("Retrieving knowledge from the knowledge base")

            knowledge_retrieved = self._knowledge_retrieval(self.agent, subtask)

            # Step 3: Build comprehensive prompt
            self.logger.info("Building App Agent prompt with control information")
            prompt_message = await self._build_app_prompt(
                agent,
                control_info,
                image_string_list,
                knowledge_retrieved,
                request,
                subtask,
                plan,
                prev_subtask,
                host_message,
                application_process_name,
                desktop_screenshot_path,
                session_step,
                request_logger,
            )

            # Step 4: Get LLM response
            self.logger.info("Getting LLM response for App Agent")
            response_text, llm_cost = await self._get_llm_response(
                agent, prompt_message
            )

            # Step 5: Parse and validate response
            self.logger.info("Parsing App Agent response")
            parsed_response = self._parse_app_response(agent, response_text)

            # Step 5: Extract structured data
            structured_data = self._extract_response_data(parsed_response)

            return ProcessingResult(
                success=True,
                data={
                    "parsed_response": parsed_response,
                    "response_text": response_text,
                    "llm_cost": llm_cost,
                    "concat_screenshot_path": concat_screenshot_path,
                    "last_control_screenshot_path": last_control_screenshot_path,
                    "prompt_message": prompt_message,
                    **structured_data,
                },
                phase=ProcessingPhase.LLM_INTERACTION,
            )

        except Exception as e:
            error_msg = f"App LLM interaction failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.LLM_INTERACTION, context)

    def _collect_image_strings(
        self,
        last_control_screenshot_path: str,
        clean_screenshot_path: str,
        annotated_screenshot_path: str,
        concat_screenshot_save_path: str,
    ):
        """
        Collect a list of image strings for prompt construction.
        :param last_control_screenshot_path: The path of screenshot of last step with selected control annotated
        :param clean_screenshot_path: The path of clean application window screenshot
        :param annotated_screenshot_path: The path of application window screenshot with detected controls with SoM
        :concat_screenshot_save_path: The concated clean and annotated sceenshot path
        :return: A list of image base64 string.
        """

        photographer = PhotographerFacade()
        image_string_list = []

        if configs.get("INCLUDE_LAST_SCREENSHOT", True):

            image_string_list += [
                photographer.encode_image_from_path(last_control_screenshot_path)
            ]

        if configs.get("CONCAT_SCREENSHOT", False):
            photographer.concat_screenshots(
                clean_screenshot_path,
                annotated_screenshot_path,
                concat_screenshot_save_path,
            )
            image_string_list += [
                photographer.encode_image_from_path(concat_screenshot_save_path)
            ]
        else:
            screenshot_url = photographer.encode_image_from_path(clean_screenshot_path)
            screenshot_annotated_url = photographer.encode_image_from_path(
                annotated_screenshot_path
            )
            image_string_list += [screenshot_url, screenshot_annotated_url]

        return image_string_list

    def _knowledge_retrieval(self, agent: "AppAgent", subtask: str):
        """
        Retrieve knowledge for the given subtask.
        :param: agent: The agent to conduct the retrieval
        :param: subtask: The subtask for which to retrieve knowledge.
        """

        experience_examples, demonstration_examples = agent.demonstration_prompt_helper(
            request=subtask
        )

        # Get the external knowledge prompt for the AppAgent using the offline and online retrievers.

        offline_docs, online_docs = agent.external_knowledge_prompt_helper(
            subtask,
            configs.get("RAG_OFFLINE_DOCS_RETRIEVED_TOPK", 0),
            configs.get("RAG_ONLINE_RETRIEVED_TOPK", 0),
        )

        return {
            "experience_examples": experience_examples,
            "demonstration_examples": demonstration_examples,
            "offline_docs": offline_docs,
            "online_docs": online_docs,
        }

    async def _build_app_prompt(
        self,
        agent: "AppAgent",
        control_info: List[TargetInfo],
        image_string_list: List[str],
        knowledge_retrieved: Dict[str, str],
        request: str,
        subtask: str,
        plan: List[str],
        prev_subtask: List[str],
        application_process_name: str,
        host_message: str,
        session_step: int,
        request_logger,
    ) -> Dict[str, Any]:
        """
        Build comprehensive prompt for App Agent.
        :param agent: The AppAgent instance
        :param filtered_controls: List of filtered controls
        :param clean_screenshot_path: Path to clean screenshot
        :param request: User request
        :param subtask: Current subtask
        :param plan: Current plan
        :param prev_subtask: Previous subtasks
        :param host_message: Host message
        :param desktop_screenshot_path: Path to desktop screenshot
        :param session_step: Current session step
        :param request_logger: Request logger
        :return: Prompt message dictionary
        """
        try:
            # Get blackboard context
            blackboard_prompt = []
            if not agent.blackboard.is_empty():
                blackboard_prompt = agent.blackboard.blackboard_to_prompt()

            # Get last successful actions
            last_success_actions = self._get_last_success_actions(agent)

            retrieved_examples = knowledge_retrieved.get(
                "experience_examples"
            ) + knowledge_retrieved.get("demonstration_examples")
            retrieved_knowledge = knowledge_retrieved.get(
                "offline_docs"
            ) + knowledge_retrieved.get("online_docs")

            # Build prompt using agent's message constructor
            prompt_message = agent.message_constructor(
                dynamic_examples=retrieved_examples,
                dynamic_knowledge=retrieved_knowledge,
                image_list=image_string_list,
                control_info=control_info,
                prev_subtask=prev_subtask,
                plan=plan,
                request=request,
                subtask=subtask,
                current_application=application_process_name,
                host_message=host_message,
                blackboard_prompt=blackboard_prompt,
                last_success_actions=last_success_actions,
                include_last_screenshot=configs.get("INCLUDE_LAST_SCREENSHOT", True),
            )

            # Log request data for debugging
            self._log_request_data(
                session_step,
                plan,
                prev_subtask,
                request,
                control_info,
                subtask,
                host_message,
                last_success_actions,
                configs.get("INCLUDE_LAST_SCREENSHOT", False),
                prompt_message,
                agent,
                request_logger,
            )

            return prompt_message

        except Exception as e:
            raise Exception(f"Failed to build app prompt: {str(e)}")

    def _get_last_success_actions(self, agent: "AppAgent") -> List[Dict[str, Any]]:
        """
        Get last successful actions from agent memory.
        :param agent: The AppAgent instance
        :return: List of last successful actions
        """
        try:
            if hasattr(agent, "get_last_success_actions"):
                return agent.get_last_success_actions()
            return []
        except Exception as e:
            self.logger.warning(f"Failed to get last success actions: {str(e)}")
            return []

    def _log_request_data(
        self,
        session_step: int,
        plan: List[Any],
        prev_subtask: List[Any],
        request: str,
        filtered_controls: List[Any],
        subtask: str,
        host_message: str,
        last_success_actions: List[Dict[str, Any]],
        include_last_screenshot: bool,
        prompt_message: Dict[str, Any],
        request_logger: FileWriter,
    ) -> None:
        """
        Log request data for debugging.
        :param session_step: Current session step
        :param plan: Current plan
        :param prev_subtask: Previous subtasks
        :param request: User request
        :param filtered_controls: List of filtered controls
        :param subtask: Current subtask
        :param host_message: Host message
        :param last_success_actions: Last successful actions
        :param include_last_screenshot: Whether to include last screenshot
        :param prompt_message: Built prompt message
        :param agent: The AppAgent instance
        :param request_logger: Request logger
        """
        try:
            request_data = AppAgentRequestLog(
                step=session_step,
                dynamic_examples=[],  # Would be populated if examples are used
                experience_examples=[],
                demonstration_examples=[],
                offline_docs="",
                online_docs="",
                dynamic_knowledge="",
                image_list=prompt_message.get("image_list", []),
                prev_subtask=prev_subtask,
                plan=plan,
                request=request,
                control_info=filtered_controls,
                subtask=subtask,
                current_application="",  # Would need app_root from context
                host_message=host_message,
                blackboard_prompt=[],
                last_success_actions=last_success_actions,
                include_last_screenshot=include_last_screenshot,
                prompt=prompt_message,
            )

            # Log as JSON
            request_log_str = json.dumps(asdict(request_data), ensure_ascii=False)

            # Use request logger if available
            if request_logger:
                request_logger.write(request_log_str)

        except Exception as e:
            self.logger.warning(f"Failed to log request data: {str(e)}")

    async def _get_llm_response(
        self, agent: "AppAgent", prompt_message: Dict[str, Any]
    ) -> tuple[str, float]:
        """
        Get response from LLM with retry logic.
        :param agent: The AppAgent instance
        :param prompt_message: Prompt message to send
        :return: Tuple of (response_text, cost)
        """
        try:
            max_retries = configs.get("JSON_PARSING_RETRY", 3)
            last_exception = None

            for retry_count in range(max_retries):
                try:
                    # Get response from LLM
                    response_text, cost = agent.get_response(
                        prompt_message, AgentType.APP, use_backup_engine=True
                    )

                    # Validate response can be parsed
                    agent.response_to_dict(response_text)

                    if retry_count > 0:
                        self.logger.info(
                            f"LLM response successful after {retry_count} retries"
                        )

                    return response_text, cost

                except Exception as e:
                    last_exception = e
                    if retry_count < max_retries - 1:
                        self.logger.warning(
                            f"LLM response parsing failed (attempt {retry_count + 1}/{max_retries}): {str(e)}"
                        )

            raise Exception(
                f"LLM interaction failed after {max_retries} attempts: {str(last_exception)}"
            )

        except Exception as e:
            raise Exception(f"Failed to get LLM response: {str(e)}")

    def _parse_app_response(
        self, agent: "AppAgent", response_text: str
    ) -> AppAgentResponse:
        """
        Parse LLM response into structured AppAgentResponse.
        :param agent: The AppAgent instance
        :param response_text: Raw response text
        :return: Parsed AppAgentResponse
        """
        try:
            # Parse response to dictionary
            response_dict = agent.response_to_dict(response_text)

            # Create structured response
            parsed_response = AppAgentResponse(**response_dict)

            # Validate response fields
            self._validate_app_response(parsed_response)

            # Print response for user feedback
            if hasattr(agent, "print_response"):
                agent.print_response(parsed_response)

            return parsed_response

        except Exception as e:
            raise Exception(f"Failed to parse app response: {str(e)}")

    def _validate_app_response(self, response: AppAgentResponse) -> None:
        """
        Validate App Agent response fields.
        :param response: Parsed response
        """
        if not response.observation:
            raise ValueError("Response missing required 'observation' field")
        if not response.thought:
            raise ValueError("Response missing required 'thought' field")
        if not response.status:
            raise ValueError("Response missing required 'status' field")

    def _extract_response_data(self, response: AppAgentResponse) -> Dict[str, Any]:
        """
        Extract structured data from parsed response.
        :param response: Parsed response
        :return: Dictionary with extracted data
        """
        return {
            "status": response.status,
            "function_name": response.function,
            "function_arguments": response.arguments or {},
            "save_screenshot": response.save_screenshot or {},
        }


@depends_on("parsed_response", "filtered_controls")
@provides("execution_result", "action_info", "action_success", "control_log")
class AppActionExecutionStrategy(BaseProcessingStrategy):
    """
    Strategy for executing App Agent actions.

    This strategy handles:
    - Action execution with UI controls
    - Control interaction and automation
    - Action result validation
    - Error handling and recovery
    """

    def __init__(self, fail_fast: bool = False) -> None:
        """
        Initialize App Agent action execution strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="app_action_execution", fail_fast=fail_fast)

    async def execute(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute App Agent actions.
        :param agent: The AppAgent instance
        :param context: Processing context with response and control data
        :return: ProcessingResult with execution results
        """
        try:
            # Extract context variables
            parsed_response = context.get("parsed_response")
            filtered_controls = context.get("filtered_controls", [])
            command_dispatcher = context.global_context.command_dispatcher

            if not parsed_response:
                return ProcessingResult(
                    success=True,
                    data={"message": "No response available for action execution"},
                    phase=ProcessingPhase.ACTION_EXECUTION,
                )

            function_name = getattr(parsed_response, "function", None)
            if not function_name:
                return ProcessingResult(
                    success=True,
                    data={"message": "No action to execute"},
                    phase=ProcessingPhase.ACTION_EXECUTION,
                )

            self.logger.info(f"Executing App Agent action: {function_name}")

            # Execute the action
            execution_result = await self._execute_app_action(
                command_dispatcher, parsed_response
            )

            # Create action info for memory
            action_info = self._create_action_info(
                filtered_controls, parsed_response, execution_result
            )

            # Determine action success
            action_success = self._determine_action_success(execution_result)

            # Create control log
            control_log = self._create_control_log(
                filtered_controls, parsed_response, execution_result
            )

            return ProcessingResult(
                success=True,
                data={
                    "execution_result": execution_result,
                    "action_info": action_info,
                    "action_success": action_success,
                    "control_log": control_log,
                },
                phase=ProcessingPhase.ACTION_EXECUTION,
            )

        except Exception as e:
            error_msg = f"App action execution failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.ACTION_EXECUTION, context)

    async def _execute_app_action(
        self, command_dispatcher, response: AppAgentResponse
    ) -> List[Any]:
        """
        Execute the specific action from the response.
        :param command_dispatcher: Command dispatcher for executing commands
        :param response: Parsed response with action details
        :return: List of execution results
        """
        try:
            function_name = response.function
            arguments = response.arguments or {}

            # Use the command dispatcher to execute the action
            if not command_dispatcher:
                raise ValueError("Command dispatcher not available")

            # Execute the command
            execution_result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name=function_name,
                        parameters=arguments,
                        tool_type="action",
                    )
                ]
            )

            return execution_result

        except Exception as e:
            raise Exception(f"Failed to execute app action: {str(e)}")

    def _create_action_info(
        self,
        filtered_controls: List[Any],
        response: AppAgentResponse,
        execution_result: List[Any],
    ) -> ActionCommandInfo:
        """
        Create action information for memory tracking.
        :param filtered_controls: List of filtered controls
        :param response: Parsed response
        :param execution_result: Execution results
        :return: ActionCommandInfo object
        """
        try:
            # Get control information if action involved a control
            target_control = None
            if response.arguments and "control_id" in response.arguments:
                control_id = response.arguments["control_id"]
                if control_id.isdigit() and int(control_id) < len(filtered_controls):
                    target_control = filtered_controls[int(control_id)]

            return ActionCommandInfo(
                function=response.function or "unknown",
                arguments=response.arguments or {},
                target=target_control,
                status=response.status or "unknown",
                result=execution_result[0] if execution_result else None,
            )

        except Exception as e:
            self.logger.warning(f"Failed to create action info: {str(e)}")
            return ActionCommandInfo(
                function=response.function or "unknown",
                arguments=response.arguments or {},
                target=None,
                status=response.status or "unknown",
                result=None,
            )

    def _determine_action_success(self, execution_result: List[Any]) -> bool:
        """
        Determine if the action was successful.
        :param execution_result: Execution results
        :return: True if successful, False otherwise
        """
        try:
            if not execution_result:
                return False

            result = execution_result[0]
            if hasattr(result, "status"):
                return result.status == ResultStatus.SUCCESS
            elif hasattr(result, "success"):
                return result.success

            return True  # Assume success if no clear indication

        except Exception as e:
            self.logger.warning(f"Failed to determine action success: {str(e)}")
            return False

    def _create_control_log(
        self,
        filtered_controls: List[Any],
        response: AppAgentResponse,
        execution_result: List[Any],
    ) -> Dict[str, Any]:
        """
        Create control log for debugging and analysis.
        :param filtered_controls: List of filtered controls
        :param response: Parsed response
        :param execution_result: Execution results
        :return: Control log dictionary
        """
        try:
            control_log = {
                "function": response.function,
                "arguments": response.arguments,
                "status": response.status,
            }

            # Add control-specific information if available
            if response.arguments and "control_id" in response.arguments:
                control_id = response.arguments["control_id"]

                if control_id.isdigit() and int(control_id) < len(filtered_controls):
                    control = filtered_controls[int(control_id)]
                    control_log.update(
                        {
                            "control_text": control.get("control_text", ""),
                            "control_type": control.get("control_type", ""),
                            "control_rect": control.get("control_rect", {}),
                        }
                    )

            # Add execution result information
            if execution_result:
                result = execution_result[0]
                control_log["execution_status"] = getattr(result, "status", "unknown")
                control_log["execution_result"] = getattr(result, "result", None)

            return control_log

        except Exception as e:
            self.logger.warning(f"Failed to create control log: {str(e)}")
            return {"error": str(e)}


@depends_on("session_step", "round_step", "round_num")
@provides("additional_memory", "memory_item", "updated_blackboard")
class AppMemoryUpdateStrategy(BaseProcessingStrategy):
    """
    Strategy for updating App Agent memory and blackboard.

    This strategy handles:
    - Memory item creation with app-specific data
    - Agent memory synchronization
    - Blackboard updates with screenshots and actions
    - Structural logging for debugging
    """

    def __init__(self, fail_fast: bool = False) -> None:
        """
        Initialize App Agent memory update strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="app_memory_update", fail_fast=fail_fast)

    async def execute(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute App Agent memory update.
        :param agent: The AppAgent instance
        :param context: Processing context with execution data
        :return: ProcessingResult with memory update results
        """
        try:
            # Extract context variables
            session_step = context.get("session_step", 0)
            round_step = context.get("round_step", 0)
            round_num = context.get("round_num", 0)
            subtask = context.get("subtask", "")
            subtask_index = context.get("subtask_index", 0)
            request = context.get("request", "")
            app_root = context.get("app_root", "")
            llm_cost = context.get("llm_cost", 0.0)
            last_error = context.get("last_error", "")
            action_info = context.get("action_info")
            action_success = context.get("action_success", False)
            execution_result = context.get("execution_result", [])
            control_log = context.get("control_log", {})
            parsed_response = context.get("parsed_response")
            clean_screenshot_path = context.get("clean_screenshot_path", "")
            screenshot_saved_time = context.get("screenshot_saved_time", 0.0)
            control_filter_time = context.get("control_filter_time", 0.0)

            # Step 1: Create additional memory data
            self.logger.info("Creating App Agent additional memory data")
            additional_memory = self._create_additional_memory_data(
                agent,
                session_step,
                round_step,
                round_num,
                subtask,
                subtask_index,
                request,
                app_root,
                llm_cost,
                last_error,
                action_info,
                action_success,
                execution_result,
                control_log,
                screenshot_saved_time,
                control_filter_time,
            )

            # Step 2: Create and populate memory item
            memory_item = self._create_and_populate_memory_item(
                parsed_response, additional_memory
            )

            # Step 3: Add memory to agent
            agent.add_memory(memory_item)

            # Step 4: Update blackboard
            self._update_blackboard(agent, clean_screenshot_path, memory_item)

            # Step 5: Update structural logs
            self._update_structural_logs(context, memory_item)

            self.logger.info("App Agent memory update completed successfully")

            return ProcessingResult(
                success=True,
                data={
                    "additional_memory": additional_memory,
                    "memory_item": memory_item,
                    "updated_blackboard": True,
                },
                phase=ProcessingPhase.MEMORY_UPDATE,
            )

        except Exception as e:
            error_msg = f"App memory update failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.MEMORY_UPDATE, context)

    def _create_additional_memory_data(
        self,
        agent: "AppAgent",
        session_step: int,
        round_step: int,
        round_num: int,
        subtask: str,
        subtask_index: int,
        request: str,
        app_root: str,
        llm_cost: float,
        last_error: str,
        action_info,
        action_success: bool,
        execution_result: List[Any],
        control_log: Dict[str, Any],
        screenshot_saved_time: float,
        control_filter_time: float,
    ) -> AppAgentAdditionalMemory:
        """
        Create additional memory data for App Agent.
        :param agent: The AppAgent instance
        :param session_step: Current session step
        :param round_step: Current round step
        :param round_num: Current round number
        :param subtask: Current subtask
        :param subtask_index: Current subtask index
        :param request: User request
        :param app_root: Application root
        :param llm_cost: LLM cost
        :param last_error: Last error
        :param action_info: Action information
        :param action_success: Action success flag
        :param execution_result: Execution results
        :param control_log: Control log
        :param screenshot_saved_time: Screenshot time
        :param control_filter_time: Control filter time
        :return: AppAgentAdditionalMemory object
        """
        try:
            # Build action lists
            function_call = []
            action = []
            action_success_list = []
            action_type = []

            if action_info:
                function_call.append(action_info.function)
                action.append(action_info.arguments)
                action_success_list.append({"success": action_success})
                action_type.append(
                    getattr(action_info.result, "namespace", "")
                    if action_info.result
                    else ""
                )

            # Calculate time costs
            time_cost = {
                "screenshot_time": screenshot_saved_time,
                "control_filter_time": control_filter_time,
                "llm_time": 0.0,  # Would be tracked if available
                "action_time": 0.0,  # Would be tracked if available
            }

            return AppAgentAdditionalMemory(
                Step=session_step,
                RoundStep=round_step,
                AgentStep=getattr(agent, "step", 0),
                Round=round_num,
                Subtask=subtask,
                SubtaskIndex=subtask_index,
                FunctionCall=function_call,
                Action=action,
                ActionSuccess=action_success_list,
                ActionType=action_type,
                Request=request,
                Agent="AppAgent",
                AgentName=getattr(agent, "name", "AppAgent"),
                Application=app_root,
                Cost=llm_cost,
                Results=(
                    str(execution_result[0].result)
                    if execution_result and execution_result[0].result
                    else ""
                ),
                error=last_error,
                time_cost=time_cost,
                ControlLog=control_log,
            )

        except Exception as e:
            raise Exception(f"Failed to create additional memory data: {str(e)}")

    def _create_and_populate_memory_item(
        self, parsed_response, additional_memory: AppAgentAdditionalMemory
    ) -> MemoryItem:
        """
        Create and populate memory item.
        :param parsed_response: Parsed response from LLM
        :param additional_memory: Additional memory data
        :return: Populated MemoryItem
        """
        try:
            memory_item = MemoryItem()

            # Add response data if available
            if parsed_response:
                memory_item.add_values_from_dict(asdict(parsed_response))

            # Add additional memory data
            memory_item.add_values_from_dict(asdict(additional_memory))

            return memory_item

        except Exception as e:
            raise Exception(f"Failed to create memory item: {str(e)}")

    def _update_blackboard(
        self, agent: "AppAgent", clean_screenshot_path: str, memory_item: MemoryItem
    ) -> None:
        """
        Update agent blackboard with screenshots and actions.
        :param agent: The AppAgent instance
        :param clean_screenshot_path: Path to clean screenshot
        :param memory_item: Memory item with action data
        """
        try:
            if not hasattr(agent, "blackboard"):
                return

            # Update image blackboard with screenshots
            if clean_screenshot_path and os.path.exists(clean_screenshot_path):
                agent.blackboard.add_screenshot(clean_screenshot_path)

            # Add action trajectories to blackboard
            history_keys = configs.get("HISTORY_KEYS", [])
            if history_keys:
                memory_dict = memory_item.to_dict()
                memorized_action = {
                    key: memory_dict.get(key)
                    for key in history_keys
                    if key in memory_dict
                }
                if memorized_action:
                    agent.blackboard.add_trajectory(memorized_action)

        except Exception as e:
            self.logger.warning(f"Failed to update blackboard: {str(e)}")

    def _update_structural_logs(
        self, context: ProcessingContext, memory_item: MemoryItem
    ) -> None:
        """
        Update structural logs for debugging.
        :param context: Processing context
        :param memory_item: Memory item to log
        """
        try:
            context.global_context.add_to_structural_logs(memory_item.to_dict())
        except Exception as e:
            self.logger.warning(f"Failed to update structural logs: {str(e)}")


# ============================================================================
# Composed Strategy - Combines multiple strategies for framework compatibility
# ============================================================================


@depends_on("app_root", "log_path", "session_step")
@provides(
    "clean_screenshot_path",
    "annotated_screenshot_path",
    "desktop_screenshot_path",
    "screenshot_saved_time",
    "filtered_controls",
    "control_info",
    "annotation_dict",
    "control_filter_time",
    "control_info_recorder",
)
class ComposedAppDataCollectionStrategy(BaseProcessingStrategy):
    """
    Composed strategy for App Agent data collection combining screenshot capture and control info collection.

    This strategy combines the functionality of:
    - AppScreenshotCaptureStrategy: Screenshot capture and path management
    - AppControlInfoStrategy: UI control information collection and filtering

    This design follows the framework requirement of one strategy per processing phase,
    while maintaining the modularity of individual operations.
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize composed App Agent data collection strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="composed_app_data_collection", fail_fast=fail_fast)

        # Initialize component strategies
        self.screenshot_strategy = AppScreenshotCaptureStrategy(fail_fast=fail_fast)
        self.control_info_strategy = AppControlInfoStrategy(fail_fast=fail_fast)

    async def execute(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute composed data collection for App Agent.
        :param agent: The AppAgent instance
        :param context: Processing context with app information
        :return: ProcessingResult with combined screenshot and control data
        """
        try:
            import time

            start_time = time.time()
            self.logger.info("Starting composed App Agent data collection")

            # Step 1: Execute screenshot capture
            self.logger.info("Phase 1: Capturing screenshots")
            screenshot_result = await self.screenshot_strategy.execute(agent, context)

            if not screenshot_result.success:
                return screenshot_result  # Return screenshot error if fail_fast

            # Update context with screenshot data for control info strategy
            for key, value in screenshot_result.data.items():
                context.set(key, value)

            # Step 2: Execute control info collection
            self.logger.info("Phase 2: Collecting control information")
            control_result: ProcessingResult = await self.control_info_strategy.execute(
                agent, context
            )

            if not control_result.success:
                if self.fail_fast:
                    return control_result
                else:
                    # Continue with partial data if not fail_fast
                    self.logger.warning(
                        f"Control info collection failed: {control_result.error}"
                    )

            # Step 3: Combine results
            combined_data = {}
            combined_data.update(screenshot_result.data)

            if control_result.success:
                combined_data.update(control_result.data)
            else:
                # Provide fallback data for control info
                combined_data.update(
                    {
                        "filtered_controls": [],
                        "control_info": [],
                        "annotation_dict": {},
                        "control_filter_time": 0.0,
                        "control_info_recorder": None,
                    }
                )

            total_time = time.time() - start_time
            self.logger.info(f"Composed data collection completed in {total_time:.2f}s")

            return ProcessingResult(
                success=True,
                data=combined_data,
                phase=ProcessingPhase.DATA_COLLECTION,
                execution_time=total_time,
            )

        except Exception as e:
            error_msg = f"Composed data collection failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)
