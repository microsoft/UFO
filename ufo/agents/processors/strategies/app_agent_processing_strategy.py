# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
App Agent Processing Strategies - Modular strategies for App Agent using the new framework.

This module contains all the processing strategies for App Agent including:
- Screenshot capture and UI control information collection
- Control filtering and annotation
- LLM interaction with app-specific prompting
- Action execution and control interaction
- Memory management and blackboard updates

Each strategy is designed to be modular, testable, and follows the dependency injection pattern.
"""

import asyncio
import json
import os
import time
import traceback
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ufo import utils
from ufo.agents.memory.memory import MemoryItem
from ufo.agents.processors.context.app_agent_processing_context import (
    AppAgentProcessorContext,
)
from ufo.agents.processors.context.processing_context import (
    BasicProcessorContext,
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
)
from ufo.agents.processors.core.strategy_dependency import depends_on, provides
from ufo.agents.processors.schemas.actions import (
    ActionCommandInfo,
    ListActionCommandInfo,
)
from ufo.agents.processors.schemas.log_schema import (
    AppAgentRequestLog,
    ControlInfoRecorder,
)
from ufo.agents.processors.schemas.response_schema import AppAgentResponse
from ufo.agents.processors.schemas.target import TargetInfo, TargetKind, TargetRegistry
from ufo.agents.processors.strategies.processing_strategy import BaseProcessingStrategy
from ufo.automator.ui_control.grounding.omniparser import OmniparserGrounding
from ufo.automator.ui_control.screenshot import PhotographerFacade
from config.config_loader import get_ufo_config
from aip.messages import Command, Result, ResultStatus
from ufo.llm import AgentType
from ufo.llm.grounding_model.omniparser_service import OmniParser
from ufo.module.context import ContextNames
from ufo.module.dispatcher import BasicCommandDispatcher

# Load configuration
ufo_config = get_ufo_config()

if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent
    from ufo.module.basic import FileWriter

CONTROL_BACKEND = ufo_config.system.control_backend
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

            # Extract context variables with validation
            log_path = context.get("log_path")
            session_step = context.get("session_step", 0)
            command_dispatcher = context.global_context.command_dispatcher

            # Validate required context variables
            if log_path is None:
                raise ValueError("log_path is required but not found in context")
            if command_dispatcher is None:
                raise ValueError(
                    "command_dispatcher is required but not found in global context"
                )

            # Step 1: Capture application window screenshot
            self.logger.info("Capturing application window screenshot")

            clean_screenshot_path = f"{log_path}action_step{session_step}.png"

            clean_screenshot_url = await self._capture_app_screenshot(
                clean_screenshot_path, command_dispatcher
            )

            # Step 2: Capture desktop screenshot if needed
            desktop_screenshot_path = f"{log_path}desktop_step{session_step}.png"

            if ufo_config.system.save_full_screen:
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
            if ufo_config.system.save_ui_tree:
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
    ) -> TargetInfo:
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
                app_window_info: Dict[str, Any] = result[0].result
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
        self.control_detection_backend = ufo_config.system.control_backend
        self.control_recorder = ControlInfoRecorder()

        if "omniparser" in self.control_detection_backend:
            self.grounding_service = self._init_omniparser_service()
        else:
            self.grounding_service = None

    def _init_omniparser_service(self) -> Optional[OmniparserGrounding]:
        """
        Initialized for the OmniParser service.
        """
        omniparser_config = ufo_config.system.omniparser
        omniparser_endpoint = (
            omniparser_config.get("ENDPOINT", "") if omniparser_config else ""
        )
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
            start_time = time.time()

            self.logger.info("Collecting UI control information")

            # Extract context variables
            target_registry: TargetRegistry = context.get_local("target_registry")
            application_window_info: TargetInfo = context.get_local(
                "application_window_info"
            )

            clean_screenshot_path = context.get_local("clean_screenshot_path")
            command_dispatcher = context.global_context.command_dispatcher
            log_path = context.get_local("log_path")
            session_step = context.get_local("session_step")

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
                # TODO: Push added control info to client.
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
                application_window_info,
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

            target_info_list = [
                TargetInfo(**control_info) for control_info in api_controls_info
            ]

            return target_info_list

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
                iou_overlap_threshold=ufo_config.system.iou_threshold_for_merge,
            )
            return merged_control_list

        except Exception as e:
            self.logger.warning(f"Control collection failed: {str(e)}")
            return []

    def _save_annotated_screenshot(
        self,
        application_window_info: TargetInfo,
        clean_screenshot_path: str,
        target_list: List[TargetInfo],
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
                application_window_info=application_window_info,
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
            import traceback

            self.logger.error(f"Failed to save annotated screenshot: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None


@provides(
    "parsed_response",
    "response_text",
    "llm_cost",
    "prompt_message",
    "save_screenshot",
    "comment",
    "concat_screenshot_path",
    "plan",
    "observation",
    "last_control_screenshot_path",
    "action",
    "thought",
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
            target_registry: TargetRegistry = context.get_local("target_registry")
            if target_registry:
                control_info: List[Dict[str, Any]] = target_registry.to_list(
                    keep_keys=["id", "name", "type"]
                )
            else:
                self.logger.warning("Target registry is not available.")
                control_info = []
            clean_screenshot_path = context.get("clean_screenshot_path", "")
            request = context.get("request")
            subtask = context.get("subtask")
            plan = self._get_prev_plan(agent)
            prev_subtask = context.get("previous_subtasks")
            host_message = context.global_context.get(ContextNames.HOST_MESSAGE)
            application_process_name = context.global_context.get(
                ContextNames.APPLICATION_PROCESS_NAME
            )

            session_step = context.get("session_step")
            request_logger = context.global_context.get(ContextNames.REQUEST_LOGGER)
            log_path = context.get("log_path")
            annotated_screenshot_path = context.get("annotated_screenshot_path")

            # Step 1: Collect image strings:

            self.logger.info("Collecting screenshots...")
            last_control_screenshot_path = (
                log_path + f"action_step{session_step - 1}_selected_controls.png"
            )

            if not os.path.exists(last_control_screenshot_path):
                last_control_screenshot_path = (
                    log_path + f"action_step{session_step - 1}.png"
                )

            concat_screenshot_path = log_path + f"action_step{session_step}_concat.png"

            image_string_list = self._collect_image_strings(
                last_control_screenshot_path,
                clean_screenshot_path,
                annotated_screenshot_path,
                concat_screenshot_path,
            )

            self.logger.info(
                f"Collected {len(image_string_list)} screenshots for prompt."
            )

            # Step 2: Retrieve knowledge from the knowledge base
            self.logger.info("Retrieving knowledge from the knowledge base")

            knowledge_retrieved = self._knowledge_retrieval(agent, subtask)

            # Step 3: Build comprehensive prompt
            self.logger.info("Building App Agent prompt with control information")
            prompt_message = await self._build_app_prompt(
                agent=agent,
                control_info=control_info,
                image_string_list=image_string_list,
                knowledge_retrieved=knowledge_retrieved,
                request=request,
                subtask=subtask,
                plan=plan,
                prev_subtask=prev_subtask,
                host_message=host_message,
                application_process_name=application_process_name,
                session_step=session_step,
                request_logger=request_logger,
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
            structured_data = parsed_response.model_dump()

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

        if ufo_config.system.include_last_screenshot:

            image_string_list += [
                photographer.encode_image_from_path(last_control_screenshot_path)
            ]

        photographer.concat_screenshots(
            clean_screenshot_path,
            annotated_screenshot_path,
            concat_screenshot_save_path,
        )

        if ufo_config.system.concat_screenshot:
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

    def _get_prev_plan(self, agent: "AppAgent") -> List[str]:
        """
        Get the previous plan from the agent's memory.
        :param agent: The AppAgent instance
        :return: List of previous plan steps
        """
        try:
            agent_memory = agent.memory

            if agent_memory.length > 0:
                prev_plan = agent_memory.get_latest_item().to_dict().get("plan", [])
            else:
                prev_plan = []

            return prev_plan

        except Exception as e:
            self.logger.warning(f"Failed to get previous plan: {str(e)}")
            return []

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
            ufo_config.rag.offline_docs_retrieved_topk,
            ufo_config.rag.online_retrieved_topk,
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
        control_info: List[Dict[str, Any]],
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
    ) -> List[Dict]:
        """
        Build comprehensive prompt for App Agent.
        :param agent: The AppAgent instance
        :param control_info: List of TargetInfo objects representing UI controls
        :param image_string_list: List of image base64 strings
        :param knowledge_retrieved: Retrieved knowledge including examples and documents
        :param request: The user request
        :param subtask: The current subtask
        :param plan: The current plan
        :param prev_subtask: List of previous subtasks
        :param application_process_name: The name of the current application process
        :param host_message: The host message
        :param session_step: Current session step
        :param request_logger: Request logger for logging prompts
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
                include_last_screenshot=ufo_config.system.include_last_screenshot,
            )

            # Log request data for debugging
            self._log_request_data(
                session_step=session_step,
                plan=plan,
                prev_subtask=prev_subtask,
                request=request,
                control_info=control_info,
                image_list=image_string_list,
                subtask=subtask,
                host_message=host_message,
                application_process_name=application_process_name,
                last_success_actions=last_success_actions,
                include_last_screenshot=ufo_config.system.include_last_screenshot,
                prompt_message=prompt_message,
                request_logger=request_logger,
            )

            return prompt_message

        except Exception as e:
            raise Exception(f"Failed to build app prompt: {str(e)}")

    def _get_last_success_actions(self, agent: "AppAgent") -> List[Dict]:
        """
        Get last successful actions from agent memory.
        :param agent: The AppAgent instance
        :return: List of last successful actions
        """
        try:
            agent_memory = agent.memory

            if agent_memory.length > 0:
                last_success_actions = (
                    agent_memory.get_latest_item()
                    .to_dict()
                    .get("action_representation", [])
                )

            else:
                last_success_actions = []

            return last_success_actions
        except Exception as e:
            self.logger.warning(f"Failed to get last success actions: {str(e)}")
            return []

    def _log_request_data(
        self,
        session_step: int,
        plan: List[str],
        prev_subtask: List[str],
        request: str,
        control_info: List[TargetInfo],
        image_list: List[str],
        subtask: str,
        host_message: str,
        last_success_actions: List[Dict],
        application_process_name: str,
        include_last_screenshot: bool,
        prompt_message: List[Dict],
        request_logger: "FileWriter",
    ) -> None:
        """
        Log request data for debugging.
        :param session_step: Current session step
        :param plan: Current plan
        :param prev_subtask: Previous subtasks
        :param request: User request
        :param control_info: List of filtered controls
        :param subtask: Current subtask
        :param application_process_name: Current application process name
        :param image_list: List of image base64 strings
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
                image_list=image_list,
                prev_subtask=prev_subtask,
                plan=plan,
                request=request,
                control_info=control_info,
                subtask=subtask,
                current_application=application_process_name,  # Would need app_root from context
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
        self, agent: "AppAgent", prompt_message: List[Dict[str, Any]]
    ) -> tuple[str, float]:
        """
        Get response from LLM with retry logic.
        :param agent: The AppAgent instance
        :param prompt_message: Prompt message to send
        :return: Tuple of (response_text, cost)
        """
        try:
            max_retries = ufo_config.system.json_parsing_retry
            last_exception = None

            for retry_count in range(max_retries):
                try:
                    # 🔧 FIX: Run synchronous LLM call in thread executor to avoid blocking event loop
                    # This prevents WebSocket ping/pong timeout during long LLM responses
                    loop = asyncio.get_event_loop()
                    response_text, cost = await loop.run_in_executor(
                        None,  # Use default ThreadPoolExecutor
                        agent.get_response,
                        prompt_message,
                        AgentType.APP,
                        True,  # use_backup_engine
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
            parsed_response = AppAgentResponse.model_validate(response_dict)

            agent.print_response(parsed_response, print_action=False)

            return parsed_response

        except Exception as e:
            raise Exception(f"Failed to parse app response: {str(e)}")


@depends_on(
    "parsed_response",
    "log_path",
    "session_step",
)
@provides(
    "execution_result",
    "action_info",
    "control_log",
    "status",
    "selected_control_screenshot_path",
)
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
            # Step 1: Extract context variables
            parsed_response: AppAgentResponse = context.get_local("parsed_response")
            log_path = context.get_local("log_path")
            session_step = context.get_local("session_step")
            annotation_dict = context.get_local("annotation_dict")
            command_dispatcher = context.global_context.command_dispatcher

            if not parsed_response:
                return ProcessingResult(
                    success=True,
                    data={"message": "No response available for action execution"},
                    phase=ProcessingPhase.ACTION_EXECUTION,
                )

            # Execute the action
            execution_results = await self._execute_app_action(
                command_dispatcher, parsed_response.action
            )

            # Create action info for memory
            actions = self._create_action_info(
                annotation_dict,
                parsed_response.action,
                execution_results,
            )

            # Print action info
            action_info = ListActionCommandInfo(actions)
            action_info.color_print()

            # Create control log
            control_log = action_info.get_target_info()
            control_objects = action_info.get_target_objects()

            # Save annotated screenshot after action execution
            selected_control_screenshot_path = (
                log_path + f"action_step{session_step}_selected_controls.png"
            )

            self._save_annotated_screenshot(
                application_window_info=context.get_local("application_window_info"),
                clean_screenshot_path=context.get_local("clean_screenshot_path"),
                save_path=selected_control_screenshot_path,
                target_list=control_objects,
            )

            status = (
                parsed_response.action.status
                if isinstance(parsed_response.action, ActionCommandInfo)
                else action_info.status
            )

            return ProcessingResult(
                success=True,
                data={
                    "execution_result": execution_results,
                    "action_info": action_info,
                    "selected_control_screenshot_path": selected_control_screenshot_path,
                    "control_log": control_log,
                    "status": status,
                },
                phase=ProcessingPhase.ACTION_EXECUTION,
            )

        except Exception as e:

            error_msg = f"App action execution failed: {str(traceback.format_exc())}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.ACTION_EXECUTION, context)

    async def _execute_app_action(
        self,
        command_dispatcher: BasicCommandDispatcher,
        actions: ActionCommandInfo | List[ActionCommandInfo],
    ) -> List[Result]:
        """
        Execute the specific action from the response.
        :param command_dispatcher: Command dispatcher for executing commands
        :param response: Parsed response with action details
        :return: List of execution results
        """
        if not actions:

            return []

        try:
            commands = []

            if isinstance(actions, ActionCommandInfo):
                actions = [actions]

            for action in actions:
                if not action.function:
                    continue
                command = self._action_to_command(action)
                commands.append(command)

            # Use the command dispatcher to execute the action
            if not command_dispatcher:
                raise ValueError("Command dispatcher not available")

            # Execute the command
            execution_result = await command_dispatcher.execute_commands(commands)

            return execution_result

        except Exception as e:
            raise Exception(f"Failed to execute app action: {str(e)}")

    def _action_to_command(self, action: ActionCommandInfo) -> Command:
        """
        Convert ActionCommandInfo to Command for execution.
        :param action: ActionCommandInfo object
        :return: Command object
        """
        return Command(
            tool_name=action.function,
            parameters=action.arguments or {},
            tool_type="action",
        )

    def _create_action_info(
        self,
        annotation_dict: Dict[str, TargetInfo],
        actions: ActionCommandInfo | List[ActionCommandInfo],
        execution_results: List[Result],
    ) -> List[ActionCommandInfo]:
        """
        Create action information for memory tracking.
        :param control_info: List of filtered controls
        :param response: Parsed response
        :param execution_result: Execution results
        :return: ActionCommandInfo object
        """
        try:
            # Get control information if action involved a control
            if not actions:
                actions = []
            if not execution_results:
                execution_results = []

            if isinstance(actions, ActionCommandInfo):
                actions = [actions]

            assert len(execution_results) == len(
                actions
            ), "Mismatch in actions and execution results length"

            for i, action in enumerate(actions):

                target_control = None
                if action.arguments and "id" in action.arguments:
                    control_id = action.arguments["id"]
                    target_control = annotation_dict.get(control_id)
                    action.target = target_control
                action.result = execution_results[i]

                if not action.function:
                    action.function = "no_action"

            return actions

        except Exception as e:
            self.logger.warning(f"Failed to create action info: {str(e)}")

    def _save_annotated_screenshot(
        self,
        application_window_info: TargetInfo,
        clean_screenshot_path: str,
        target_list: List[TargetInfo],
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
            photographer = PhotographerFacade()
            photographer.capture_app_window_screenshot_with_target_list(
                application_window_info=application_window_info,
                target_list=target_list,
                path=clean_screenshot_path,
                save_path=save_path,
                highlight_bbox=True,
            )
            self.logger.info(
                f"application_window_info: {application_window_info}, clean_screenshot_path: {clean_screenshot_path}, target_list: {target_list}, save_path: {save_path}"
            )
            self.logger.info(
                f"Annotated screenshot for selected controls is saved to {save_path}"
            )

            annotated_screenshot_url = photographer.encode_image_from_path(save_path)
            return annotated_screenshot_url
        except Exception as e:
            import traceback

            self.logger.error(f"Failed to save annotated screenshot: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None


@depends_on("session_step", "parsed_response")
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
            parsed_response: AppAgentResponse = context.get("parsed_response")
            clean_screenshot_path = context.get("clean_screenshot_path", "")
            application_process_name = context.global_context.get(
                ContextNames.APPLICATION_PROCESS_NAME
            )

            # Step 1: Create additional memory data
            self.logger.info("Creating App Agent additional memory data")
            additional_memory = self._create_additional_memory_data(agent, context)

            # Step 2: Create and populate memory item
            memory_item = self._create_and_populate_memory_item(
                parsed_response, additional_memory
            )

            # Step 3: Add memory to agent
            agent.add_memory(memory_item)

            save_screenshot = parsed_response.save_screenshot

            # Step 4: Update blackboard
            self._update_blackboard(
                agent=agent,
                save_screenshot=save_screenshot.get("save", False),
                screenshot_path=clean_screenshot_path,
                memory_item=memory_item,
                save_reason=save_screenshot.get("reason", ""),
                application_process_name=application_process_name,
            )

            # Step 5: Update structural logs
            self._update_structural_logs(context, memory_item)

            self.logger.info("AppAgent memory update completed successfully")

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

            error_msg = f"App memory update failed: {str(traceback.format_exc())}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.MEMORY_UPDATE, context)

    def _get_all_success_actions(self, agent: "AppAgent") -> List[Dict[str, Any]]:
        """
        Get the previous action.
        :return: The previous action of the agent.
        """
        agent_memory = agent.memory

        if agent_memory.length > 0:
            success_action_memory = agent_memory.filter_memory_from_keys(
                ["action_success"]
            )
            success_actions = []
            for success_action in success_action_memory:
                success_actions += success_action.get("action_success", [])

        else:
            success_actions = []

        return success_actions

    def _create_additional_memory_data(
        self,
        agent: "AppAgent",
        context: ProcessingContext,
    ) -> "BasicProcessorContext":
        """
        Create additional memory data for App Agent.
        :param agent: The AppAgent instance
        :param context: Current session step
        :return: ProcessingContext object
        """
        try:
            # Build action lists
            from ufo.agents.processors.app_agent_processor import (
                AppAgentProcessorContext,
            )

            app_context: AppAgentProcessorContext = context.local_context

            all_previous_success_actions = self._get_all_success_actions(agent)
            action_info: ListActionCommandInfo = context.get("action_info")

            if action_info:

                app_context.function_call = action_info.get_function_calls()
                app_context.action = action_info.to_list_of_dicts(
                    previous_actions=all_previous_success_actions
                )
                app_context.action_success = action_info.to_list_of_dicts(
                    success_only=True,
                    previous_actions=all_previous_success_actions,
                    keep_keys=["action_string", "result", "repeat_time"],
                )
                app_context.action_type = [
                    action.result.namespace for action in action_info.actions
                ]
                app_context.action_representation = action_info.to_representation()

            app_context.session_step = context.get_global(
                ContextNames.SESSION_STEP.name, 0
            )
            app_context.round_step = context.get_global(
                ContextNames.CURRENT_ROUND_STEP.name, 0
            )
            app_context.round_num = context.get_global(
                ContextNames.CURRENT_ROUND_ID.name, 0
            )
            app_context.agent_step = agent.step if agent else 0

            app_context.subtask = context.get("subtask", "")
            app_context.subtask_index = context.get("subtask_index", 0)
            app_context.request = context.get("request", "")
            app_context.app_root = context.get("app_root", "")

            app_context.cost = context.get("llm_cost", 0.0)

            app_context.results = context.get("execution_result", [])

            return app_context

        except Exception as e:
            raise Exception(f"Failed to create additional memory data: {str(e)}")

    def _create_and_populate_memory_item(
        self,
        parsed_response: AppAgentResponse,
        additional_memory: "AppAgentProcessorContext",
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
                memory_item.add_values_from_dict(parsed_response.model_dump())

            # Add additional memory data
            memory_item.add_values_from_dict(additional_memory.to_dict(selective=True))

            return memory_item

        except Exception as e:
            raise Exception(f"Failed to create memory item: {str(e)}")

    def _update_blackboard(
        self,
        agent: "AppAgent",
        save_screenshot: bool,
        save_reason: str,
        screenshot_path: str,
        memory_item: MemoryItem,
        application_process_name: str = "",
    ) -> None:
        """
        Update agent blackboard with screenshots and actions.
        :param agent: The AppAgent instance
        :param save_screenshot: Whether to save screenshot to blackboard
        :param screenshot_path: Path to screenshot
        :param memory_item: Memory item with action data
        :param application_process_name: Name of the application process
        """
        try:
            # Add action trajectories to blackboard
            history_keys = ufo_config.system.history_keys
            if history_keys:
                memory_dict = memory_item.to_dict()
                memorized_action = {
                    key: memory_dict.get(key)
                    for key in history_keys
                    if key in memory_dict
                }
                if memorized_action:
                    agent.blackboard.add_trajectories(memorized_action)

            if save_screenshot:

                metadata = {
                    "screenshot application": application_process_name,
                    "saving reason": save_reason,
                }
                agent.blackboard.add_image(screenshot_path, metadata)

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
