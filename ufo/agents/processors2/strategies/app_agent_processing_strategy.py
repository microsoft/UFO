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

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agents.memory.memory import MemoryItem
from ufo.agents.processors.actions import ActionCommandInfo
from ufo.agents.processors.app_agent_processor import (
    AppAgentAdditionalMemory,
    AppAgentRequestLog,
    AppAgentResponse,
    ControlInfoRecorder,
)
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
from ufo.automator.ui_control.control_filter import ControlFilterFactory
from ufo.automator.ui_control.grounding.basic import BasicGrounding
from ufo.automator.ui_control.inspector import ControlInspectorFacade
from ufo.config import Config
from ufo.contracts.contracts import Command, Result, ResultStatus
from ufo.llm import AgentType
from ufo.module.context import ContextNames

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

            # Step 1: Capture application window screenshot
            self.logger.info("Capturing application window screenshot")
            clean_screenshot_path, annotated_screenshot_path = (
                await self._capture_app_screenshot(agent, context)
            )

            # Step 2: Capture desktop screenshot if needed
            self.logger.info("Capturing desktop screenshot")
            desktop_screenshot_path = await self._capture_desktop_screenshot(
                agent, context
            )

            screenshot_time = time.time() - start_time

            return ProcessingResult(
                success=True,
                data={
                    "clean_screenshot_path": clean_screenshot_path,
                    "annotated_screenshot_path": annotated_screenshot_path,
                    "desktop_screenshot_path": desktop_screenshot_path,
                    "screenshot_saved_time": screenshot_time,
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            error_msg = f"Screenshot capture failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    async def _capture_app_screenshot(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> tuple[str, str]:
        """
        Capture application window screenshot.
        :param agent: The AppAgent instance
        :param context: Processing context
        :return: Tuple of (clean_screenshot_path, annotated_screenshot_path)
        """
        try:
            log_path = context.get("log_path", "")
            session_step = context.get("session_step", 0)

            # Generate screenshot paths
            clean_screenshot_path = f"{log_path}action_step{session_step}.png"
            annotated_screenshot_path = (
                f"{log_path}action_step{session_step}_annotated.png"
            )

            # Capture application window screenshot
            app_root = context.get("app_root", "")
            if app_root and hasattr(agent, "app_root") and agent.app_root:
                # Save clean screenshot
                agent.app_root.take_screenshot(clean_screenshot_path)
                self.logger.info(f"Clean screenshot saved to: {clean_screenshot_path}")

                return clean_screenshot_path, annotated_screenshot_path
            else:
                raise ValueError("App root not available for screenshot capture")

        except Exception as e:
            raise Exception(f"Failed to capture app screenshot: {str(e)}")

    async def _capture_desktop_screenshot(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> str:
        """
        Capture desktop screenshot if needed.
        :param agent: The AppAgent instance
        :param context: Processing context
        :return: Desktop screenshot path
        """
        try:
            log_path = context.get("log_path", "")
            session_step = context.get("session_step", 0)

            desktop_screenshot_path = f"{log_path}desktop_step{session_step}.png"

            # Check if desktop screenshot is needed based on configuration
            include_last_screenshot = configs.get("INCLUDE_LAST_SCREENSHOT", False)

            if include_last_screenshot:
                command_dispatcher = context.global_context.command_dispatcher
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
                        utils.save_image_string(
                            desktop_screenshot_url, desktop_screenshot_path
                        )
                        self.logger.info(
                            f"Desktop screenshot saved to: {desktop_screenshot_path}"
                        )

            return desktop_screenshot_path

        except Exception as e:
            self.logger.warning(f"Desktop screenshot capture failed: {str(e)}")
            return ""


@depends_on("clean_screenshot_path", "app_root")
@provides(
    "filtered_controls",
    "control_info",
    "annotation_dict",
    "control_filter_time",
    "control_info_recorder",
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

            # Step 1: Collect UIA control information
            self.logger.info("Collecting UIA control information")
            control_info_recorder = await self._collect_control_info(agent, context)

            # Step 2: Filter and process controls
            self.logger.info("Filtering and processing controls")
            filtered_controls, annotation_dict = (
                await self._filter_and_annotate_controls(
                    agent, context, control_info_recorder
                )
            )

            control_filter_time = time.time() - start_time

            return ProcessingResult(
                success=True,
                data={
                    "filtered_controls": filtered_controls,
                    "control_info": filtered_controls,  # Alias for backward compatibility
                    "annotation_dict": annotation_dict,
                    "control_filter_time": control_filter_time,
                    "control_info_recorder": control_info_recorder,
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            error_msg = f"Control info collection failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    async def _collect_control_info(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> ControlInfoRecorder:
        """
        Collect comprehensive control information from the application window.
        :param agent: The AppAgent instance
        :param context: Processing context
        :return: ControlInfoRecorder with collected information
        """
        try:
            recorder = ControlInfoRecorder()

            # Get application window information
            app_root = context.get("app_root", "")
            if not app_root or not hasattr(agent, "app_root") or not agent.app_root:
                raise ValueError("App root not available for control collection")

            # Collect UIA controls
            uia_controls = await self._collect_uia_controls(agent, context)
            recorder.uia_controls_info = [
                self._extract_control_info(control) for control in uia_controls
            ]

            # Collect grounding controls if grounding service is available
            grounding_service = context.get("grounding_service")
            if grounding_service:
                grounding_controls = await self._collect_grounding_controls(
                    agent, context, grounding_service
                )
                recorder.grounding_controls_info = [
                    self._extract_control_info(control)
                    for control in grounding_controls
                ]

            # Merge control information
            recorder.merged_controls_info = self._merge_control_info(
                recorder.uia_controls_info, recorder.grounding_controls_info
            )

            return recorder

        except Exception as e:
            raise Exception(f"Failed to collect control info: {str(e)}")

    async def _collect_uia_controls(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> List[UIAWrapper]:
        """
        Collect UIA controls from the application window.
        :param agent: The AppAgent instance
        :param context: Processing context
        :return: List of UIA controls
        """
        try:
            # Use control inspector to get controls
            inspector = ControlInspectorFacade(backend=BACKEND)
            controls = inspector.get_control_info_list(
                agent.app_root, field_list=ControlInfoRecorder.recording_fields
            )
            return controls

        except Exception as e:
            self.logger.warning(f"UIA control collection failed: {str(e)}")
            return []

    async def _collect_grounding_controls(
        self,
        agent: "AppAgent",
        context: ProcessingContext,
        grounding_service: BasicGrounding,
    ) -> List[UIAWrapper]:
        """
        Collect controls using grounding service.
        :param agent: The AppAgent instance
        :param context: Processing context
        :param grounding_service: Grounding service instance
        :return: List of grounded controls
        """
        try:
            clean_screenshot_path = context.get("clean_screenshot_path", "")
            if not clean_screenshot_path or not os.path.exists(clean_screenshot_path):
                return []

            # Use grounding service to detect controls
            grounding_controls = grounding_service.get_control_info(
                agent.app_root, clean_screenshot_path
            )
            return grounding_controls

        except Exception as e:
            self.logger.warning(f"Grounding control collection failed: {str(e)}")
            return []

    def _extract_control_info(self, control: UIAWrapper) -> Dict[str, Any]:
        """
        Extract relevant information from a control.
        :param control: UI control wrapper
        :return: Dictionary with control information
        """
        try:
            return {
                "control_text": getattr(control, "control_text", ""),
                "control_type": getattr(control, "control_type", ""),
                "control_class": getattr(control, "control_class", ""),
                "control_rect": getattr(control, "control_rect", {}),
                "source": getattr(control, "source", ""),
            }
        except Exception as e:
            self.logger.warning(f"Failed to extract control info: {str(e)}")
            return {}

    def _merge_control_info(
        self,
        uia_controls: List[Dict[str, Any]],
        grounding_controls: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge UIA and grounding control information.
        :param uia_controls: UIA control information
        :param grounding_controls: Grounding control information
        :return: Merged control information
        """
        # Simple merge - could be enhanced with deduplication logic
        merged = list(uia_controls)
        merged.extend(grounding_controls)
        return merged

    async def _filter_and_annotate_controls(
        self,
        agent: "AppAgent",
        context: ProcessingContext,
        recorder: ControlInfoRecorder,
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Filter controls and create annotation dictionary.
        :param agent: The AppAgent instance
        :param context: Processing context
        :param recorder: Control info recorder
        :return: Tuple of (filtered_controls, annotation_dict)
        """
        try:
            # Get control filter
            control_filter = ControlFilterFactory.get_control_filter()

            # Filter controls
            filtered_controls = control_filter.filter(
                recorder.merged_controls_info,
                max_controls=context.get("max_controls", 20),
            )

            # Create annotation dictionary for screenshot annotation
            annotation_dict = {}
            for i, control in enumerate(filtered_controls):
                annotation_dict[str(i)] = {
                    "text": control.get("control_text", ""),
                    "type": control.get("control_type", ""),
                    "rect": control.get("control_rect", {}),
                }

            # Save annotated screenshot if needed
            await self._save_annotated_screenshot(context, annotation_dict)

            return filtered_controls, annotation_dict

        except Exception as e:
            raise Exception(f"Failed to filter and annotate controls: {str(e)}")

    async def _save_annotated_screenshot(
        self, context: ProcessingContext, annotation_dict: Dict[str, Any]
    ) -> None:
        """
        Save annotated screenshot with control annotations.
        :param context: Processing context
        :param annotation_dict: Annotation dictionary
        """
        try:
            clean_screenshot_path = context.get("clean_screenshot_path", "")
            annotated_screenshot_path = context.get("annotated_screenshot_path", "")

            if clean_screenshot_path and annotated_screenshot_path and annotation_dict:
                # Use utils to create annotated screenshot
                utils.create_annotated_screenshot(
                    clean_screenshot_path, annotated_screenshot_path, annotation_dict
                )
                self.logger.info(
                    f"Annotated screenshot saved to: {annotated_screenshot_path}"
                )

        except Exception as e:
            self.logger.warning(f"Failed to save annotated screenshot: {str(e)}")


@depends_on("filtered_controls", "clean_screenshot_path", "request")
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
            # Step 1: Build comprehensive prompt
            self.logger.info("Building App Agent prompt with control information")
            prompt_message = await self._build_app_prompt(agent, context)

            # Step 2: Get LLM response
            self.logger.info("Getting LLM response for App Agent")
            response_text, llm_cost = await self._get_llm_response(
                agent, prompt_message
            )

            # Step 3: Parse and validate response
            self.logger.info("Parsing App Agent response")
            parsed_response = self._parse_app_response(agent, response_text)

            # Step 4: Extract structured data
            structured_data = self._extract_response_data(parsed_response)

            return ProcessingResult(
                success=True,
                data={
                    "parsed_response": parsed_response,
                    "response_text": response_text,
                    "llm_cost": llm_cost,
                    "prompt_message": prompt_message,
                    **structured_data,
                },
                phase=ProcessingPhase.LLM_INTERACTION,
            )

        except Exception as e:
            error_msg = f"App LLM interaction failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.LLM_INTERACTION, context)

    async def _build_app_prompt(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> Dict[str, Any]:
        """
        Build comprehensive prompt for App Agent.
        :param agent: The AppAgent instance
        :param context: Processing context
        :return: Prompt message dictionary
        """
        try:
            # Get required data from context
            filtered_controls = context.get("filtered_controls", [])
            clean_screenshot_path = context.get("clean_screenshot_path", "")
            request = context.get("request", "")

            # Get additional context data
            subtask = context.get("subtask", "")
            plan = context.get("plan", [])
            prev_subtask = context.get("previous_subtasks", [])

            # Get host message if available
            host_message = context.global_context.get(ContextNames.HOST_MESSAGE, "")

            # Get blackboard context
            blackboard_prompt = []
            if hasattr(agent, "blackboard") and not agent.blackboard.is_empty():
                blackboard_prompt = agent.blackboard.blackboard_to_prompt()

            # Get last successful actions
            last_success_actions = self._get_last_success_actions(agent)

            # Build image list
            image_list = []
            if clean_screenshot_path and os.path.exists(clean_screenshot_path):
                image_list = [clean_screenshot_path]

            # Include desktop screenshot if configured
            include_last_screenshot = configs.get("INCLUDE_LAST_SCREENSHOT", False)
            if include_last_screenshot:
                desktop_screenshot_path = context.get("desktop_screenshot_path", "")
                if desktop_screenshot_path and os.path.exists(desktop_screenshot_path):
                    image_list.append(desktop_screenshot_path)

            # Build prompt using agent's message constructor
            prompt_message = agent.message_constructor(
                image_list=image_list,
                control_info=filtered_controls,
                prev_subtask=prev_subtask,
                plan=plan,
                request=request,
                subtask=subtask,
                host_message=host_message,
                blackboard_prompt=blackboard_prompt,
                last_success_actions=last_success_actions,
                include_last_screenshot=include_last_screenshot,
            )

            # Log request data for debugging
            self._log_request_data(context, prompt_message, agent)

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
        context: ProcessingContext,
        prompt_message: Dict[str, Any],
        agent: "AppAgent",
    ) -> None:
        """
        Log request data for debugging.
        :param context: Processing context
        :param prompt_message: Built prompt message
        :param agent: The AppAgent instance
        """
        try:
            request_data = AppAgentRequestLog(
                step=context.get("session_step", 0),
                dynamic_examples=[],  # Would be populated if examples are used
                experience_examples=[],
                demonstration_examples=[],
                offline_docs="",
                online_docs="",
                dynamic_knowledge="",
                image_list=prompt_message.get("image_list", []),
                prev_subtask=context.get("previous_subtasks", []),
                plan=context.get("plan", []),
                request=context.get("request", ""),
                control_info=context.get("filtered_controls", []),
                subtask=context.get("subtask", ""),
                current_application=context.get("app_root", ""),
                host_message=context.global_context.get(ContextNames.HOST_MESSAGE, ""),
                blackboard_prompt=[],
                last_success_actions=self._get_last_success_actions(agent),
                include_last_screenshot=configs.get("INCLUDE_LAST_SCREENSHOT", False),
                prompt=prompt_message,
            )

            # Log as JSON
            request_log_str = json.dumps(asdict(request_data), ensure_ascii=False)

            # Use request logger if available
            request_logger = context.global_context.get(ContextNames.REQUEST_LOGGER)
            if request_logger:
                request_logger.debug(request_log_str)

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
            parsed_response = context.get("parsed_response")
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
                agent, context, parsed_response
            )

            # Create action info for memory
            action_info = self._create_action_info(
                context, parsed_response, execution_result
            )

            # Determine action success
            action_success = self._determine_action_success(execution_result)

            # Create control log
            control_log = self._create_control_log(
                context, parsed_response, execution_result
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
        self, agent: "AppAgent", context: ProcessingContext, response: AppAgentResponse
    ) -> List[Any]:
        """
        Execute the specific action from the response.
        :param agent: The AppAgent instance
        :param context: Processing context
        :param response: Parsed response with action details
        :return: List of execution results
        """
        try:
            function_name = response.function
            arguments = response.arguments or {}

            # Use the agent's command dispatcher to execute the action
            command_dispatcher = context.global_context.command_dispatcher
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
        context: ProcessingContext,
        response: AppAgentResponse,
        execution_result: List[Any],
    ) -> ActionCommandInfo:
        """
        Create action information for memory tracking.
        :param context: Processing context
        :param response: Parsed response
        :param execution_result: Execution results
        :return: ActionCommandInfo object
        """
        try:
            # Get control information if action involved a control
            target_control = None
            if response.arguments and "control_id" in response.arguments:
                control_id = response.arguments["control_id"]
                filtered_controls = context.get("filtered_controls", [])
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
        context: ProcessingContext,
        response: AppAgentResponse,
        execution_result: List[Any],
    ) -> Dict[str, Any]:
        """
        Create control log for debugging and analysis.
        :param context: Processing context
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
                filtered_controls = context.get("filtered_controls", [])

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
            # Step 1: Create additional memory data
            self.logger.info("Creating App Agent additional memory data")
            additional_memory = self._create_additional_memory_data(agent, context)

            # Step 2: Create and populate memory item
            memory_item = self._create_and_populate_memory_item(
                context, additional_memory
            )

            # Step 3: Add memory to agent
            agent.add_memory(memory_item)

            # Step 4: Update blackboard
            self._update_blackboard(agent, context, memory_item)

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
        self, agent: "AppAgent", context: ProcessingContext
    ) -> AppAgentAdditionalMemory:
        """
        Create additional memory data for App Agent.
        :param agent: The AppAgent instance
        :param context: Processing context
        :return: AppAgentAdditionalMemory object
        """
        try:
            # Get action information
            action_info = context.get("action_info")
            action_success = context.get("action_success", False)
            execution_result = context.get("execution_result", [])

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
                "screenshot_time": context.get("screenshot_saved_time", 0.0),
                "control_filter_time": context.get("control_filter_time", 0.0),
                "llm_time": 0.0,  # Would be tracked if available
                "action_time": 0.0,  # Would be tracked if available
            }

            return AppAgentAdditionalMemory(
                Step=context.get("session_step", 0),
                RoundStep=context.get("round_step", 0),
                AgentStep=getattr(agent, "step", 0),
                Round=context.get("round_num", 0),
                Subtask=context.get("subtask", ""),
                SubtaskIndex=context.get("subtask_index", 0),
                FunctionCall=function_call,
                Action=action,
                ActionSuccess=action_success_list,
                ActionType=action_type,
                Request=context.get("request", ""),
                Agent="AppAgent",
                AgentName=getattr(agent, "name", "AppAgent"),
                Application=context.get("app_root", ""),
                Cost=context.get("llm_cost", 0.0),
                Results=(
                    str(execution_result[0].result)
                    if execution_result and execution_result[0].result
                    else ""
                ),
                error=context.get("last_error", ""),
                time_cost=time_cost,
                ControlLog=context.get("control_log", {}),
            )

        except Exception as e:
            raise Exception(f"Failed to create additional memory data: {str(e)}")

    def _create_and_populate_memory_item(
        self, context: ProcessingContext, additional_memory: AppAgentAdditionalMemory
    ) -> MemoryItem:
        """
        Create and populate memory item.
        :param context: Processing context
        :param additional_memory: Additional memory data
        :return: Populated MemoryItem
        """
        try:
            memory_item = MemoryItem()

            # Add response data if available
            parsed_response = context.get("parsed_response")
            if parsed_response:
                memory_item.add_values_from_dict(asdict(parsed_response))

            # Add additional memory data
            memory_item.add_values_from_dict(asdict(additional_memory))

            return memory_item

        except Exception as e:
            raise Exception(f"Failed to create memory item: {str(e)}")

    def _update_blackboard(
        self, agent: "AppAgent", context: ProcessingContext, memory_item: MemoryItem
    ) -> None:
        """
        Update agent blackboard with screenshots and actions.
        :param agent: The AppAgent instance
        :param context: Processing context
        :param memory_item: Memory item with action data
        """
        try:
            if not hasattr(agent, "blackboard"):
                return

            # Update image blackboard with screenshots
            clean_screenshot_path = context.get("clean_screenshot_path", "")
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
