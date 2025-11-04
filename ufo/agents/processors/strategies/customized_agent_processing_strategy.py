# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Customized Agent Processing Strategies - Modular strategies for Customized Agent using the new framework.

This module contains all the processing strategies for Customized Agent including:
- Screenshot capture and UI control information collection
- LLM interaction with app-specific prompting
- Action execution and control interaction
- Memory management and blackboard updates

Each strategy is designed to be modular, testable, and follows the dependency injection pattern.
"""

from typing import TYPE_CHECKING

from ufo import utils
from ufo.agents.processors.context.processing_context import (
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
)
from ufo.agents.processors.core.strategy_dependency import depends_on, provides
from ufo.agents.processors.strategies.app_agent_processing_strategy import (
    AppLLMInteractionStrategy,
)
from ufo.agents.processors.strategies.processing_strategy import BaseProcessingStrategy
from ufo.automator.ui_control.screenshot import PhotographerFacade
from config.config_loader import get_ufo_config
from aip.messages import Command, ResultStatus
from ufo.module.dispatcher import BasicCommandDispatcher

# Load configuration
ufo_config = get_ufo_config()

if TYPE_CHECKING:
    from ufo.agents.agent.customized_agent import CustomizedAgent


@depends_on("app_root", "log_path", "session_step")
@provides(
    "clean_screenshot_path",
    "clean_screenshot_url",
    "screenshot_saved_time",
)
class CustomizedScreenshotCaptureStrategy(BaseProcessingStrategy):
    """
    Strategy for capturing application screenshots and desktop screenshots.

    This strategy handles:
    - Application window screenshot capture
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
        self, agent: "CustomizedAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute screenshot capture for Customized Agent.
        :param agent: The CustomizedAgent instance
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

            clean_screenshot_url = await self._capture_screenshot(
                clean_screenshot_path, command_dispatcher
            )

            screenshot_time = time.time() - start_time

            return ProcessingResult(
                success=True,
                data={
                    "clean_screenshot_path": clean_screenshot_path,
                    "screenshot_saved_time": screenshot_time,
                    "clean_screenshot_url": clean_screenshot_url,
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
                        tool_name="take_screenshot",
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


@depends_on("target_registry", "clean_screenshot_path", "request")
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
class CustomizedLLMInteractionStrategy(AppLLMInteractionStrategy):
    """
    Strategy for LLM interaction with App Agent specific prompting.

    This strategy handles:
    - Context-aware prompt construction with app-specific data
    - Control information integration in prompts
    - LLM interaction with retry logic
    - Response parsing and validation
    """

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
        clean_image_url = photographer.encode_image_from_path(clean_screenshot_path)
        return [clean_image_url]
