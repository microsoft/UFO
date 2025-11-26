# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
App Agent Processor - Modern, extensible App Agent processing implementation.

This module implements the architecture for App Agent processing, providing:
- Type-safe context management with AppAgentProcessorContext
- Modular strategy-based processing pipeline
- Comprehensive middleware stack for error handling, performance monitoring, and logging
- Flexible dependency injection and configuration
- Robust error handling and recovery mechanisms
"""

import logging
from typing import TYPE_CHECKING, Any, Dict

from rich.console import Console
from rich.panel import Panel

from ufo.agents.processors.context.app_agent_processing_context import (
    AppAgentProcessorContext,
)
from ufo.agents.processors.context.processing_context import ProcessingContext
from ufo.agents.processors.core.processing_middleware import EnhancedLoggingMiddleware
from ufo.agents.processors.core.processor_framework import ProcessorTemplate
from ufo.agents.processors.strategies.app_agent_processing_strategy import (
    AppActionExecutionStrategy,
    AppControlInfoStrategy,
    AppLLMInteractionStrategy,
    AppMemoryUpdateStrategy,
    AppScreenshotCaptureStrategy,
)
from ufo.agents.processors.strategies.processing_strategy import ComposedStrategy
from ufo.module.context import Context, ContextNames

console = Console()

if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent
    from ufo.agents.processors.core.processor_framework import ProcessingResult


class AppAgentProcessor(ProcessorTemplate):
    """
    App Agent Processor - Modern, extensible App Agent processing implementation.

    This processor implements the complete  architecture for App Agent:
    - Uses AppAgentProcessorContext for type-safe app-specific data
    - Implements modular strategy-based processing pipeline
    - Provides comprehensive middleware stack
    - Supports flexible configuration and dependency injection
    - Includes robust error handling and performance monitoring

    Processing Pipeline:
    1. Data Collection: Screenshot capture and UI control information (using a composed strategy)
    2. LLM Interaction: Context-aware prompting and response parsing
    3. Action Execution: UI automation and control interaction
    4. Memory Update: Agent memory and blackboard synchronization

    Middleware Stack:
    - Structured logging and debugging middleware
    """

    # Specify the custom context class for this processor
    processor_context_class = AppAgentProcessorContext

    def __init__(self, agent: "AppAgent", global_context: "Context") -> None:
        """Initialize App Agent Processor."""
        super().__init__(agent, global_context)

    def _setup_strategies(self) -> None:
        """Setup processing strategies for App Agent."""
        from ufo.agents.processors.context.processing_context import ProcessingPhase

        # Data collection strategy (combines screenshot + control info)
        self.strategies[ProcessingPhase.DATA_COLLECTION] = ComposedStrategy(
            strategies=[
                AppScreenshotCaptureStrategy(),
                AppControlInfoStrategy(),
            ],
            name="AppDataCollectionStrategy",
            fail_fast=True,
        )

        # LLM interaction strategy
        self.strategies[ProcessingPhase.LLM_INTERACTION] = AppLLMInteractionStrategy(
            fail_fast=True  # LLM interaction failure should trigger recovery
        )

        # Action execution strategy
        self.strategies[ProcessingPhase.ACTION_EXECUTION] = AppActionExecutionStrategy(
            fail_fast=False  # Action failures can be handled gracefully
        )

        # Memory update strategy
        self.strategies[ProcessingPhase.MEMORY_UPDATE] = AppMemoryUpdateStrategy(
            fail_fast=False  # Memory update failures shouldn't stop the process
        )

    def _setup_middleware(self) -> None:
        """Setup middleware pipeline for App Agent."""
        # Core middleware (order matters)
        self.middleware_chain = [AppAgentLoggingMiddleware()]

    def _get_processor_specific_context_data(self) -> Dict[str, Any]:
        """
        Get processor-specific context data for App Agent. This data is merged into the processing local context.
        :return: Dictionary of processor-specific context data
        """
        context_data = {
            "subtask": self.global_context.get(ContextNames.SUBTASK),
            "application_process_name": self.global_context.get(
                ContextNames.APPLICATION_PROCESS_NAME
            ),
            "app_root": self.global_context.get(ContextNames.APPLICATION_ROOT_NAME),
        }

        return context_data


class AppAgentLoggingMiddleware(EnhancedLoggingMiddleware):
    """
    Specialized logging middleware for App Agent with enhanced contextual information.

    This middleware provides:
    - App Agent specific progress messages with color coding
    - Detailed step information with subtask and application context
    - Performance metrics and execution summaries
    - Enhanced error reporting with App Agent context
    - Maintains compatibility with legacy AppAgent logging features
    """

    def __init__(self) -> None:
        """Initialize App Agent logging middleware with appropriate log level."""
        super().__init__(log_level=logging.INFO)

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """
        Log App Agent processing start with detailed context information.
        Replicates the functionality of the legacy print_step_info method.

        :param processor: App Agent processor instance
        :param context: Processing context with round and step information
        """
        # Import here to avoid circular imports

        # Call parent implementation for standard logging
        await super().before_process(processor, context)

        # Extract context information
        round_num = context.get("round_num")
        round_step = context.get("round_step")
        request = context.get("request")

        panel_title = f"🚀 Round {round_num + 1}, Step {round_step + 1}, Agent: {processor.agent.name}"
        panel_content = self.starting_message(context)

        console.print(Panel(panel_content, title=panel_title, style="magenta"))

        # Additional context logging for debugging
        if self.logger.isEnabledFor(logging.DEBUG):
            context_keys = list(context.local_data.keys())
            self.logger.debug(f"Available App Agent context keys: {context_keys}")

            if request:
                self.logger.debug(
                    f"App Agent Request: '{request[:100]}{'...' if len(request) > 100 else ''}'"
                )

    def starting_message(self, context: ProcessingContext) -> str:
        """
        Return the starting message of the agent.
        :param context: Processing context with round and step information
        :return: Starting message string
        """
        subtask = context.get("subtask")
        application_process_name = context.get("application_process_name")

        return f"Completing the subtask [{subtask}] on application [{application_process_name}]."

    async def after_process(
        self, processor: ProcessorTemplate, result: "ProcessingResult"
    ) -> None:
        """
        Log App Agent processing completion with execution summary.

        :param processor: App Agent processor instance
        :param result: Processing result with execution data
        """
        # Import here to avoid circular imports
        from ufo import utils

        # Call parent implementation for standard logging
        await super().after_process(processor, result)

        if result.success:
            # Log App Agent specific success information
            subtask = result.data.get("subtask", "")
            application_process_name = result.data.get("application_process_name", "")
            action_result = result.data.get("action_result", "")
            llm_cost = result.data.get("llm_cost", 0.0)

            success_msg = "App Agent processing completed successfully"
            if subtask:
                success_msg += f" - Subtask: {subtask}"
            if application_process_name:
                success_msg += f" - Application: {application_process_name}"
            if action_result:
                success_msg += f" - Action: {action_result}"

            self.logger.info(success_msg)

            # Log cost information if available
            if llm_cost > 0:
                self.logger.debug(f"App Agent LLM cost: ${llm_cost:.4f}")

            # Display user-friendly completion message (maintaining original UX)
            if subtask and application_process_name:
                console.print(
                    f"✅ AppAgent: Successfully completed subtask '{subtask}' "
                    f"on application '{application_process_name}'",
                    style="green",
                )
        else:
            # Enhanced error logging for App Agent
            error_phase = getattr(result, "phase", "unknown")
            self.logger.error(
                f"App Agent processing failed at phase: {error_phase} - {result.error}"
            )

            # Display user-friendly error message (maintaining original UX)
            console.print(
                f"❌ AppAgent: Processing failed - {result.error}", style="red"
            )

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """
        Enhanced error handling for App Agent with contextual information.

        :param processor: App Agent processor instance
        :param error: Exception that occurred
        """
        # Import here to avoid circular imports
        from ufo import utils

        # Call parent implementation for standard error handling
        await super().on_error(processor, error)

        # Display user-friendly error message (maintaining original UX)
        console.print(f"❌ AppAgent: Encountered error - {str(error)}", style="red")
