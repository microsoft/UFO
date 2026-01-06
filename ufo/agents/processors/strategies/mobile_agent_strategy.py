# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Mobile Agent Data Collection Strategy - Strategy for collecting data from Android devices.

This module contains data collection strategies for Mobile Agent including:
- Screenshot capture (clean and annotated)
- Installed apps information collection
- Current screen controls information collection
"""

import traceback
from typing import TYPE_CHECKING, List, Dict, Any

from ufo import utils
from ufo.agents.processors.context.processing_context import (
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
)
from ufo.agents.processors.core.strategy_dependency import depends_on, provides
from ufo.agents.processors.app_agent_processor import AppAgentLoggingMiddleware
from ufo.agents.processors.strategies.app_agent_processing_strategy import (
    AppLLMInteractionStrategy,
    AppActionExecutionStrategy,
)
from ufo.agents.processors.strategies.processing_strategy import BaseProcessingStrategy
from ufo.automator.ui_control.screenshot import PhotographerFacade
from config.config_loader import get_ufo_config
from aip.messages import Command, ResultStatus, Result
from ufo.module.dispatcher import BasicCommandDispatcher
from ufo.agents.processors.schemas.actions import (
    ListActionCommandInfo,
    ActionCommandInfo,
)
from ufo.llm.response_schema import AppAgentResponse
from ufo.agents.processors.schemas.target import TargetInfo, TargetKind

# Load configuration
ufo_config = get_ufo_config()

if TYPE_CHECKING:
    from ufo.agents.agent.customized_agent import MobileAgent


@depends_on("log_path", "session_step")
@provides(
    "clean_screenshot_path",
    "clean_screenshot_url",
    "annotated_screenshot_url",
    "screenshot_saved_time",
)
class MobileScreenshotCaptureStrategy(BaseProcessingStrategy):
    """
    Strategy for capturing Android device screenshots.

    This strategy handles:
    - Device screenshot capture via MCP server
    - Screenshot path management and storage
    - Performance timing for screenshot operations
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize screenshot capture strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="mobile_screenshot_capture", fail_fast=fail_fast)

    async def execute(
        self, agent: "MobileAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute screenshot capture for Mobile Agent.
        :param agent: The MobileAgent instance
        :param context: Processing context
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

            # Step 1: Capture clean screenshot
            self.logger.info("Capturing Android device screenshot")

            clean_screenshot_path = f"{log_path}action_step{session_step}.png"

            clean_screenshot_url = await self._capture_screenshot(
                clean_screenshot_path, command_dispatcher
            )

            # Step 2: Capture annotated screenshot (if available)
            annotated_screenshot_url = None
            # Note: Annotated screenshot would require additional processing
            # For now, we'll use the clean screenshot

            screenshot_time = time.time() - start_time

            return ProcessingResult(
                success=True,
                data={
                    "clean_screenshot_path": clean_screenshot_path,
                    "clean_screenshot_url": clean_screenshot_url,
                    "annotated_screenshot_url": annotated_screenshot_url,
                    "screenshot_saved_time": screenshot_time,
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            error_msg = f"Screenshot capture failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    async def _capture_screenshot(
        self, save_path: str, command_dispatcher: BasicCommandDispatcher
    ) -> str:
        """
        Capture Android device screenshot via MCP server.
        :param save_path: The path for saving screenshot
        :param command_dispatcher: Command dispatcher for executing commands
        :return: The base64 URL of the screenshot
        """
        try:
            if not command_dispatcher:
                raise ValueError("Command dispatcher not available")

            # Execute capture_screenshot command via MCP server
            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="capture_screenshot",
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
                raise ValueError("Failed to capture screenshot")

            # Extract image data from result - now it's directly a base64 string
            clean_screenshot_url = result[0].result

            # Save screenshot to file
            utils.save_image_string(clean_screenshot_url, save_path)
            self.logger.info(f"Screenshot saved to: {save_path}")

            return clean_screenshot_url

        except Exception as e:
            raise Exception(f"Failed to capture screenshot: {str(e)}")


@depends_on("clean_screenshot_url")
@provides("installed_apps", "apps_collection_time")
class MobileAppsCollectionStrategy(BaseProcessingStrategy):
    """
    Strategy for collecting installed apps information from Android device.

    This strategy handles:
    - Fetching installed apps via MCP server
    - Filtering and organizing app data
    - Caching app information
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize apps collection strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="mobile_apps_collection", fail_fast=fail_fast)

    async def execute(
        self, agent: "MobileAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute apps collection for Mobile Agent.
        :param agent: The MobileAgent instance
        :param context: Processing context
        :return: ProcessingResult with installed apps list
        """
        try:
            import time

            start_time = time.time()

            command_dispatcher = context.global_context.command_dispatcher

            if command_dispatcher is None:
                raise ValueError(
                    "command_dispatcher is required but not found in global context"
                )

            # Fetch installed apps via MCP server
            self.logger.info("Fetching installed apps from Android device")

            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="get_mobile_app_target_info",
                        parameters={"include_system_apps": False},
                        tool_type="data_collection",
                    )
                ]
            )

            if not result or result[0].status != ResultStatus.SUCCESS:
                if not result:
                    self.logger.warning("No result returned from MCP server")
                else:
                    self.logger.warning(
                        f"MCP server returned error. Status: {result[0].status}, Error: {result[0].error if hasattr(result[0], 'error') else 'N/A'}"
                    )
                self.logger.warning("Failed to fetch installed apps, using empty list")
                installed_apps = []
            else:
                # Parse the result - MCP returns dictionaries or TargetInfo objects
                # result[0].result could be an empty list [] which is valid
                apps_data = result[0].result or []
                if isinstance(apps_data, list):
                    installed_apps = []
                    for app in apps_data:
                        # Handle both dict and TargetInfo objects
                        if isinstance(app, dict):
                            installed_apps.append(self._dict_to_app_dict(app))
                        else:
                            installed_apps.append(self._target_info_to_dict(app))
                else:
                    installed_apps = []

            apps_time = time.time() - start_time

            self.logger.info(f"Collected {len(installed_apps)} installed apps")

            return ProcessingResult(
                success=True,
                data={
                    "installed_apps": installed_apps,
                    "apps_collection_time": apps_time,
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            error_msg = f"Apps collection failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    def _target_info_to_dict(self, target_info: TargetInfo) -> Dict[str, Any]:
        """
        Convert TargetInfo object to dictionary for prompt.
        :param target_info: TargetInfo object
        :return: Dictionary representation
        """
        return {
            "id": target_info.id,
            "name": target_info.name,
            "package": target_info.type,
        }

    def _dict_to_app_dict(self, app_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert MCP returned dictionary to app dictionary for prompt.
        :param app_dict: Dictionary from MCP server
        :return: Dictionary representation for prompt
        """
        return {
            "id": app_dict.get("id", ""),
            "name": app_dict.get("name", ""),
            "package": app_dict.get("type", ""),
        }


@depends_on("clean_screenshot_url")
@provides(
    "current_controls",
    "controls_collection_time",
    "annotated_screenshot_url",
    "annotated_screenshot_path",
    "annotation_dict",
)
class MobileControlsCollectionStrategy(BaseProcessingStrategy):
    """
    Strategy for collecting current screen controls information from Android device.

    This strategy handles:
    - Fetching current screen UI controls via MCP server
    - Filtering and organizing control data
    - Caching control information
    - Creating annotated screenshots with control labels
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize controls collection strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(name="mobile_controls_collection", fail_fast=fail_fast)
        self.photographer = PhotographerFacade()

    async def execute(
        self, agent: "MobileAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute controls collection for Mobile Agent.
        :param agent: The MobileAgent instance
        :param context: Processing context
        :return: ProcessingResult with current screen controls list
        """
        try:
            import time

            start_time = time.time()

            command_dispatcher = context.global_context.command_dispatcher

            if command_dispatcher is None:
                raise ValueError(
                    "command_dispatcher is required but not found in global context"
                )

            # Fetch current screen controls via MCP server
            self.logger.info("Fetching current screen controls from Android device")

            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="get_app_window_controls_target_info",
                        parameters={},
                        tool_type="data_collection",
                    )
                ]
            )

            if not result or result[0].status != ResultStatus.SUCCESS:
                if not result:
                    self.logger.warning("No result returned from MCP server")
                else:
                    self.logger.warning(
                        f"MCP server returned error. Status: {result[0].status}, Error: {result[0].error if hasattr(result[0], 'error') else 'N/A'}"
                    )
                self.logger.warning(
                    "Failed to fetch current controls, using empty list"
                )
                current_controls = []
            else:
                # Parse the result - MCP returns dictionaries or TargetInfo objects
                # result[0].result could be an empty list [] which is valid
                controls_data = result[0].result or []
                if isinstance(controls_data, list):
                    current_controls = []
                    for control in controls_data:
                        # Handle both dict and TargetInfo objects
                        if isinstance(control, dict):
                            control_dict = self._dict_to_control_dict(control)
                            # Only add if it has a valid rect
                            if control_dict is not None:
                                current_controls.append(control_dict)
                        else:
                            control_dict = self._target_info_to_dict(control)
                            if control_dict is not None:
                                current_controls.append(control_dict)
                else:
                    current_controls = []

            controls_time = time.time() - start_time

            self.logger.info(f"Collected {len(current_controls)} screen controls")

            # Generate annotated screenshot with control IDs and annotation dict
            annotated_screenshot_url = None
            annotated_screenshot_path = None
            annotation_dict = {}

            if len(current_controls) > 0:
                clean_screenshot_path = context.get_local("clean_screenshot_path")
                log_path = context.get_local("log_path")
                session_step = context.get_local("session_step", 0)

                if clean_screenshot_path and log_path:
                    annotated_screenshot_path = (
                        f"{log_path}action_step{session_step}_annotated.png"
                    )

                    # Convert controls to TargetInfo objects for photographer
                    # Use current_controls which are already validated dictionaries
                    target_info_list = self._controls_to_target_info_list(
                        current_controls
                    )

                    # Create annotation dict
                    annotation_dict = {
                        control.get("id"): control
                        for control in current_controls
                        if "id" in control
                    }

                    # Generate annotated screenshot using photographer
                    annotated_screenshot_url = self._save_annotated_screenshot(
                        clean_screenshot_path,
                        target_info_list,
                        annotated_screenshot_path,
                    )

                    if annotated_screenshot_url:
                        self.logger.info(
                            f"Created annotated screenshot with {len(current_controls)} controls"
                        )
                    else:
                        self.logger.warning("Failed to create annotated screenshot")

            return ProcessingResult(
                success=True,
                data={
                    "current_controls": current_controls,
                    "controls_collection_time": controls_time,
                    "annotated_screenshot_url": annotated_screenshot_url,
                    "annotated_screenshot_path": annotated_screenshot_path,
                    "annotation_dict": annotation_dict,
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            error_msg = f"Controls collection failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    def _target_info_to_dict(self, target_info: TargetInfo) -> Dict[str, Any]:
        """
        Convert TargetInfo object to dictionary for prompt.
        :param target_info: TargetInfo object
        :return: Dictionary representation
        """
        result = {
            "id": target_info.id,
            "name": target_info.name,
            "type": target_info.type,
        }
        if target_info.rect:
            result["rect"] = target_info.rect
        return result

    def _dict_to_control_dict(self, control_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert MCP returned dictionary to control dictionary for prompt.
        Validates rectangle and returns None if invalid.
        :param control_dict: Dictionary from MCP server
        :return: Dictionary representation for prompt, or None if invalid
        """
        rect = control_dict.get("rect")

        # Validate rectangle if present
        # rect format is [left, top, right, bottom] (bbox format)
        if rect:
            if not isinstance(rect, list) or len(rect) < 4:
                self.logger.debug(
                    f"Skipping control with malformed rect: {control_dict.get('id')}"
                )
                return None

            left, top, right, bottom = rect[0], rect[1], rect[2], rect[3]

            # Check if dimensions are valid (right > left and bottom > top)
            if right <= left or bottom <= top:
                self.logger.debug(
                    f"Skipping control with invalid dimensions: {control_dict.get('id')} - "
                    f"rect={rect} (right={right}, left={left}, bottom={bottom}, top={top})"
                )
                return None

        result = {
            "id": control_dict.get("id", ""),
            "name": control_dict.get("name", ""),
            "type": control_dict.get("type", ""),
        }
        if rect:
            result["rect"] = rect
        return result

    def _controls_to_target_info_list(self, controls_data: List) -> List[TargetInfo]:
        """
        Convert control dictionaries to TargetInfo objects.
        Filters out controls with invalid rectangles.
        :param controls_data: List of control dictionaries or TargetInfo objects
        :return: List of TargetInfo objects with valid rectangles
        """
        target_info_list = []
        invalid_count = 0

        for control in controls_data:
            if isinstance(control, dict):
                rect = control.get("rect")

                # Validate rectangle: [left, top, right, bottom] (bbox format)
                # Skip if rect is None, empty, or has invalid dimensions
                if rect and len(rect) >= 4:
                    left, top, right, bottom = rect[0], rect[1], rect[2], rect[3]

                    # Check if dimensions are valid (right > left and bottom > top)
                    if right > left and bottom > top:
                        # Create TargetInfo from dict
                        target_info = TargetInfo(
                            kind=TargetKind.CONTROL,
                            id=control.get("id", ""),
                            name=control.get("name", ""),
                            type=control.get("type", ""),
                            rect=rect,
                        )
                        target_info_list.append(target_info)
                    else:
                        invalid_count += 1
                        self.logger.debug(
                            f"Skipping control with invalid dimensions: {control.get('id')} - rect={rect}"
                        )
                else:
                    invalid_count += 1
                    self.logger.debug(
                        f"Skipping control without valid rect: {control.get('id')}"
                    )

            elif isinstance(control, TargetInfo):
                # Validate TargetInfo rect as well
                if control.rect and len(control.rect) >= 4:
                    left, top, right, bottom = (
                        control.rect[0],
                        control.rect[1],
                        control.rect[2],
                        control.rect[3],
                    )
                    if right > left and bottom > top:
                        target_info_list.append(control)
                    else:
                        invalid_count += 1
                else:
                    invalid_count += 1

        if invalid_count > 0:
            self.logger.warning(
                f"Filtered out {invalid_count} controls with invalid rectangles"
            )

        return target_info_list

    def _save_annotated_screenshot(
        self,
        clean_screenshot_path: str,
        target_list: List[TargetInfo],
        save_path: str,
    ) -> str:
        """
        Save annotated screenshot using photographer.
        :param clean_screenshot_path: Path to the clean screenshot
        :param target_list: List of TargetInfo objects
        :param save_path: The saved path of the annotated screenshot
        :return: The annotated image string (base64 URL)
        """
        try:
            # For mobile, we don't have application_window_info, so create a dummy one
            # The photographer will use the full screenshot
            dummy_window_info = TargetInfo(
                kind=TargetKind.WINDOW,
                id="mobile_screen",
                name="Mobile Screen",
                type="mobile",
            )

            self.photographer.capture_app_window_screenshot_with_target_list(
                application_window_info=dummy_window_info,
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


@depends_on("installed_apps", "current_controls", "clean_screenshot_url")
@provides(
    "parsed_response",
    "response_text",
    "llm_cost",
    "prompt_message",
    "action",
    "thought",
    "comment",
)
class MobileLLMInteractionStrategy(AppLLMInteractionStrategy):
    """
    Strategy for LLM interaction with Mobile Agent specific prompting.

    This strategy handles:
    - Context-aware prompt construction with mobile-specific data
    - Screenshot and control information integration in prompts
    - LLM interaction with retry logic
    - Response parsing and validation
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize Mobile Agent LLM interaction strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(fail_fast=fail_fast)

    async def execute(
        self, agent: "MobileAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute LLM interaction for Mobile Agent.
        :param agent: The MobileAgent instance
        :param context: Processing context with mobile device data
        :return: ProcessingResult with parsed response and cost
        """
        try:
            request = context.get("request")
            installed_apps = context.get_local("installed_apps", [])
            current_controls = context.get_local("current_controls", [])
            clean_screenshot_url = context.get_local("clean_screenshot_url")
            annotated_screenshot_url = context.get_local("annotated_screenshot_url")
            plan = self._get_prev_plan(agent)

            # Build comprehensive prompt
            self.logger.info("Building Mobile Agent prompt")

            # Get blackboard context
            blackboard_prompt = []
            if not agent.blackboard.is_empty():
                blackboard_prompt = agent.blackboard.blackboard_to_prompt()

            prompt_message = agent.message_constructor(
                dynamic_examples=[],
                dynamic_knowledge="",
                plan=plan,
                request=request,
                installed_apps=installed_apps,
                current_controls=current_controls,
                screenshot_url=clean_screenshot_url,
                annotated_screenshot_url=annotated_screenshot_url,
                blackboard_prompt=blackboard_prompt,
                last_success_actions=self._get_last_success_actions(agent=agent),
            )

            # Get LLM response
            self.logger.info("Getting LLM response for Mobile Agent")
            response_text, llm_cost = await self._get_llm_response(
                agent, prompt_message
            )

            # Parse and validate response
            self.logger.info("Parsing Mobile Agent response")
            parsed_response = self._parse_app_response(agent, response_text)

            # Extract structured data
            structured_data = parsed_response.model_dump()

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
            error_msg = f"Mobile LLM interaction failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.LLM_INTERACTION, context)


class MobileActionExecutionStrategy(AppActionExecutionStrategy):
    """
    Strategy for executing actions in Mobile Agent.

    This strategy handles:
    - Action execution based on parsed LLM response
    - Result capturing and error handling
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize Mobile action execution strategy.
        :param fail_fast: Whether to raise exceptions immediately on errors
        """
        super().__init__(fail_fast=fail_fast)

    async def execute(
        self, agent: "MobileAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute Mobile Agent actions.
        :param agent: The MobileAgent instance
        :param context: Processing context with response and control data
        :return: ProcessingResult with execution results
        """
        try:
            # Step 1: Extract context variables
            parsed_response: AppAgentResponse = context.get_local("parsed_response")
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
                parsed_response.action,
                execution_results,
            )

            # Print action info
            action_info = ListActionCommandInfo(actions)
            action_info.color_print()

            # Create control log
            control_log = action_info.get_target_info()

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
                    "control_log": control_log,
                    "status": status,
                },
                phase=ProcessingPhase.ACTION_EXECUTION,
            )

        except Exception as e:
            error_msg = f"Mobile action execution failed: {str(traceback.format_exc())}"
            self.logger.error(error_msg)
            return self.handle_error(e, ProcessingPhase.ACTION_EXECUTION, context)

    def _create_action_info(
        self,
        actions: ActionCommandInfo | List[ActionCommandInfo],
        execution_results: List[Result],
    ) -> List[ActionCommandInfo]:
        """
        Create action information for memory tracking.
        :param actions: The action or list of actions
        :param execution_results: Execution results
        :return: List of ActionCommandInfo objects
        """
        try:
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
                action.result = execution_results[i]

                if not action.function:
                    action.function = "no_action"

            return actions

        except Exception as e:
            self.logger.warning(f"Failed to create action info: {str(e)}")
            return []


class MobileLoggingMiddleware(AppAgentLoggingMiddleware):
    """
    Specialized logging middleware for Mobile Agent with enhanced contextual information.
    """

    def starting_message(self, context: ProcessingContext) -> str:
        """
        Return the starting message of the agent.
        :param context: Processing context with round and step information
        :return: Starting message string
        """

        # Try both global and local context for request
        request = (
            context.get("request") or context.get_local("request") or "Unknown Request"
        )

        return (
            f"Completing the user request: [bold cyan]{request}[/bold cyan] on Mobile."
        )
