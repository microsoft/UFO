# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
App Agent Processing Strategies V2 - Simplified modular strategies for App Agent.

This module contains simplified processing strategies for App Agent.
"""

import time
from typing import TYPE_CHECKING, Any, Dict, List

from ufo.agents.processors2.core.processing_context import (
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
)
from ufo.agents.processors2.strategies.processing_strategy import BaseProcessingStrategy

if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent


class AppScreenshotCaptureStrategy(BaseProcessingStrategy):
    """Strategy for capturing application screenshots."""

    def __init__(self, fail_fast: bool = True) -> None:
        super().__init__(name="app_screenshot_capture", fail_fast=fail_fast)

    async def execute(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """Execute screenshot capture for App Agent."""
        try:
            start_time = time.time()

            # Mock screenshot capture
            log_path = getattr(context, "log_path", "")
            session_step = getattr(context, "session_step", 0)

            clean_screenshot_path = f"{log_path}action_step{session_step}.png"
            annotated_screenshot_path = (
                f"{log_path}action_step{session_step}_annotated.png"
            )

            screenshot_time = time.time() - start_time

            return ProcessingResult(
                success=True,
                data={
                    "clean_screenshot_path": clean_screenshot_path,
                    "annotated_screenshot_path": annotated_screenshot_path,
                    "screenshot_saved_time": screenshot_time,
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error=str(e),
                phase=ProcessingPhase.DATA_COLLECTION,
                data={},
            )


class AppControlInfoStrategy(BaseProcessingStrategy):
    """Strategy for collecting and filtering UI control information."""

    def __init__(self, fail_fast: bool = True) -> None:
        super().__init__(name="app_control_info", fail_fast=fail_fast)

    async def execute(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """Execute control information collection and filtering."""
        try:
            start_time = time.time()

            # Mock control collection
            filtered_controls = [
                {"text": "Button", "type": "button", "rect": {}},
                {"text": "TextBox", "type": "textbox", "rect": {}},
            ]

            annotation_dict = {
                "0": {"text": "Button", "type": "button"},
                "1": {"text": "TextBox", "type": "textbox"},
            }

            control_filter_time = time.time() - start_time

            return ProcessingResult(
                success=True,
                data={
                    "filtered_controls": filtered_controls,
                    "control_info": filtered_controls,
                    "annotation_dict": annotation_dict,
                    "control_filter_time": control_filter_time,
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error=str(e),
                phase=ProcessingPhase.DATA_COLLECTION,
                data={},
            )


class AppLLMInteractionStrategy(BaseProcessingStrategy):
    """Strategy for LLM interaction with App Agent specific prompting."""

    def __init__(self, fail_fast: bool = True) -> None:
        super().__init__(name="app_llm_interaction", fail_fast=fail_fast)

    async def execute(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """Execute LLM interaction for App Agent."""
        try:
            # Mock prompt construction
            prompt_message = {"message": "test prompt"}

            # Mock LLM response
            response_text = '{"observation": "Test observation", "thought": "Test thought", "status": "CONTINUE", "function": "test_function"}'
            llm_cost = 0.01

            # Mock parsed response
            parsed_response_dict = {
                "observation": "Test observation",
                "thought": "Test thought",
                "status": "CONTINUE",
                "function": "test_function",
                "arguments": {},
            }

            return ProcessingResult(
                success=True,
                data={
                    "parsed_response": parsed_response_dict,
                    "response_text": response_text,
                    "llm_cost": llm_cost,
                    "prompt_message": prompt_message,
                    "function_name": "test_function",
                    "function_arguments": {},
                },
                phase=ProcessingPhase.LLM_INTERACTION,
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error=str(e),
                phase=ProcessingPhase.LLM_INTERACTION,
                data={},
            )


class AppActionExecutionStrategy(BaseProcessingStrategy):
    """Strategy for executing App Agent actions."""

    def __init__(self, fail_fast: bool = False) -> None:
        super().__init__(name="app_action_execution", fail_fast=fail_fast)

    async def execute(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """Execute App Agent actions."""
        try:
            # Mock action execution
            execution_result = [{"status": "success", "result": "Action completed"}]
            action_success = True

            action_info = {
                "function": "test_function",
                "arguments": {},
                "status": "CONTINUE",
            }

            control_log = {"function": "test_function", "status": "success"}

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
            return ProcessingResult(
                success=False,
                error=str(e),
                phase=ProcessingPhase.ACTION_EXECUTION,
                data={},
            )


class AppMemoryUpdateStrategy(BaseProcessingStrategy):
    """Strategy for updating App Agent memory and blackboard."""

    def __init__(self, fail_fast: bool = False) -> None:
        super().__init__(name="app_memory_update", fail_fast=fail_fast)

    async def execute(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """Execute App Agent memory update with comprehensive memory management."""
        try:
            # Extract data from context for memory update
            session_step = getattr(context, "session_step", 0)
            round_step = getattr(context, "round_step", 0)
            round_num = getattr(context, "round_num", 0)
            subtask = getattr(context, "subtask", "")
            request = getattr(context, "request", "")
            function_name = getattr(context, "function_name", "")
            action_success = getattr(context, "action_success", False)
            llm_cost = getattr(context, "llm_cost", 0.0)
            execution_result = getattr(context, "execution_result", [])

            # Create comprehensive additional memory data
            additional_memory = {
                "Step": session_step,
                "RoundStep": round_step,
                "AgentStep": getattr(agent, "step", 0),
                "Round": round_num,
                "Subtask": subtask,
                "SubtaskIndex": getattr(context, "subtask_index", 0),
                "FunctionCall": [function_name] if function_name else [],
                "ActionSuccess": [action_success],
                "ActionType": ["ui_action"] if function_name else [],
                "Request": request,
                "Agent": agent.__class__.__name__,
                "AgentName": getattr(agent, "name", "AppAgent"),
                "Application": str(getattr(context, "app_root", "")),
                "Cost": llm_cost,
                "Results": str(execution_result),
                "error": getattr(context, "last_error", ""),
                "time_cost": getattr(context, "execution_times", {}),
                "ControlLog": getattr(context, "control_log", {}),
                "UserConfirm": None,  # Will be set if needed
            }

            # Create memory item for agent memory
            memory_item = {
                "session_step": session_step,
                "agent_type": "AppAgent",
                "subtask": subtask,
                "function_call": function_name,
                "action_success": action_success,
                "llm_cost": llm_cost,
                "timestamp": time.time(),
            }

            # Update agent memory if available
            updated_agent_memory = False
            if hasattr(agent, "memory") and agent.memory:
                try:
                    # Add memory item to agent's memory
                    agent.memory.add_memory_item(memory_item)
                    updated_agent_memory = True

                    # Cleanup old memory if needed
                    self._cleanup_old_memory(agent)

                except Exception as e:
                    self.logger.warning(f"Failed to update agent memory: {str(e)}")

            # Update blackboard if available
            updated_blackboard = False
            if hasattr(agent, "blackboard") and agent.blackboard:
                try:
                    # Add trajectory to blackboard
                    memorized_action = {
                        "step": session_step,
                        "function": function_name,
                        "success": action_success,
                        "cost": llm_cost,
                    }
                    agent.blackboard.add_trajectories(memorized_action)
                    updated_blackboard = True

                    # Save screenshot to blackboard if requested
                    save_screenshot = getattr(context, "save_screenshot", {})
                    if save_screenshot.get("save", False):
                        self._update_image_blackboard(agent, context, save_screenshot)

                except Exception as e:
                    self.logger.warning(f"Failed to update blackboard: {str(e)}")

            # Update global context with memory state
            self._sync_to_global_context(agent, context)

            return ProcessingResult(
                success=True,
                data={
                    "additional_memory": additional_memory,
                    "memory_item": memory_item,
                    "updated_agent_memory": updated_agent_memory,
                    "updated_blackboard": updated_blackboard,
                    "memory_stats": self._get_memory_stats(agent),
                },
                phase=ProcessingPhase.MEMORY_UPDATE,
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error=str(e),
                phase=ProcessingPhase.MEMORY_UPDATE,
                data={},
            )

    def _cleanup_old_memory(self, agent: "AppAgent") -> None:
        """
        Cleanup old memory items based on configuration.
        :param agent: The AppAgent instance
        """
        try:
            from ufo.config import Config

            configs = Config.get_instance().config_data
            max_memory_items = configs.get("MAX_MEMORY_ITEMS", 100)

            if hasattr(agent, "memory") and agent.memory:
                current_count = getattr(agent.memory, "length", 0)

                if current_count > max_memory_items:
                    # Remove oldest items
                    items_to_remove = current_count - max_memory_items
                    if hasattr(agent.memory, "remove_oldest"):
                        agent.memory.remove_oldest(items_to_remove)
                        self.logger.info(
                            f"Cleaned up {items_to_remove} old memory items"
                        )

        except Exception as e:
            self.logger.warning(f"Memory cleanup failed: {str(e)}")

    def _update_image_blackboard(
        self, agent: "AppAgent", context: ProcessingContext, save_screenshot: dict
    ) -> None:
        """
        Save screenshot to blackboard if requested.
        :param agent: The AppAgent instance
        :param context: Processing context
        :param save_screenshot: Screenshot saving configuration
        """
        try:
            if hasattr(agent, "blackboard") and agent.blackboard:
                screenshot_path = getattr(context, "clean_screenshot_path", "")
                if screenshot_path and hasattr(agent.blackboard, "add_screenshot"):
                    agent.blackboard.add_screenshot(
                        screenshot_path, save_screenshot.get("description", "")
                    )
                    self.logger.info(
                        f"Screenshot saved to blackboard: {screenshot_path}"
                    )

        except Exception as e:
            self.logger.warning(f"Blackboard screenshot update failed: {str(e)}")

    def _sync_to_global_context(
        self, agent: "AppAgent", context: ProcessingContext
    ) -> None:
        """
        Synchronize agent state to global context.
        :param agent: The AppAgent instance
        :param context: Processing context
        """
        try:
            global_context = context.global_context

            if hasattr(agent, "name"):
                global_context.set(f"agent_{agent.name}_last_update", time.time())

            if hasattr(agent, "step"):
                global_context.set("agent_step", agent.step)

            # Update structural logs if available
            if hasattr(global_context, "add_to_structural_logs"):
                log_data = {
                    "agent_type": "AppAgent",
                    "session_step": getattr(context, "session_step", 0),
                    "memory_updated": True,
                    "timestamp": time.time(),
                }
                global_context.add_to_structural_logs(log_data)

        except Exception as e:
            self.logger.warning(f"Global context sync failed: {str(e)}")

    def _get_memory_stats(self, agent: "AppAgent") -> dict:
        """
        Get memory statistics for logging and monitoring.
        :param agent: The AppAgent instance
        :return: Memory statistics dictionary
        """
        try:
            stats = {
                "agent_memory_count": 0,
                "blackboard_empty": True,
                "blackboard_screenshot_count": 0,
                "blackboard_trajectory_count": 0,
            }

            if hasattr(agent, "memory") and agent.memory:
                stats["agent_memory_count"] = getattr(agent.memory, "length", 0)

            if hasattr(agent, "blackboard") and agent.blackboard:
                stats["blackboard_empty"] = agent.blackboard.is_empty()
                if hasattr(agent.blackboard, "screenshots"):
                    stats["blackboard_screenshot_count"] = len(
                        agent.blackboard.screenshots
                    )
                if hasattr(agent.blackboard, "trajectories"):
                    stats["blackboard_trajectory_count"] = len(
                        agent.blackboard.trajectories
                    )

            return stats

        except Exception as e:
            self.logger.warning(f"Memory stats collection failed: {str(e)}")
            return {}


# ============================================================================
# Composed Strategy - Combines multiple strategies for framework compatibility
# ============================================================================


class ComposedAppDataCollectionStrategy(BaseProcessingStrategy):
    """
    Composed strategy for App Agent data collection combining screenshot capture and control info collection.

    This simplified composed strategy combines:
    - AppScreenshotCaptureStrategy: Mock screenshot capture
    - AppControlInfoStrategy: Mock control info collection

    This design follows the framework requirement of one strategy per processing phase.
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
            start_time = time.time()

            # Step 1: Execute screenshot capture
            screenshot_result = await self.screenshot_strategy.execute(agent, context)

            if not screenshot_result.success:
                return screenshot_result

            # Update context with screenshot data
            for key, value in screenshot_result.data.items():
                setattr(context, key, value)

            # Step 2: Execute control info collection
            control_result = await self.control_info_strategy.execute(agent, context)

            if not control_result.success:
                if self.fail_fast:
                    return control_result
                else:
                    # Continue with partial data
                    control_result.data = {
                        "filtered_controls": [],
                        "control_info": [],
                        "annotation_dict": {},
                        "control_filter_time": 0.0,
                    }

            # Step 3: Combine results
            combined_data = {}
            combined_data.update(screenshot_result.data)
            combined_data.update(control_result.data)

            total_time = time.time() - start_time

            return ProcessingResult(
                success=True,
                data=combined_data,
                phase=ProcessingPhase.DATA_COLLECTION,
                execution_time=total_time,
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error=str(e),
                phase=ProcessingPhase.DATA_COLLECTION,
                data={},
            )
