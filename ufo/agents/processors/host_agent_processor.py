# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Host Agent Processor - Processor for Host Agent using the new framework.

This processor handles the Host Agent's workflow including:
- Desktop screenshot capture
- Application window detection and registration
- Third-party agent integration
- LLM interaction with proper context building
- Action execution and application selection
- Memory management and logging

The processor maintains backward compatibility with BaseProcessor interface
while providing enhanced modularity, error handling, and extensibility.
"""


import logging
from typing import TYPE_CHECKING, Any, Dict, Type
from unittest import result

from rich.console import Console
from rich.panel import Panel

from ufo.agents.processors.context.host_agent_processing_context import (
    HostAgentProcessorContext,
)
from ufo.agents.processors.core.processing_middleware import EnhancedLoggingMiddleware
from ufo.agents.processors.core.processor_framework import (
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
    ProcessorTemplate,
)
from ufo.agents.processors.schemas.target import TargetInfo
from ufo.agents.processors.strategies.host_agent_processing_strategy import (
    DesktopDataCollectionStrategy,
    HostActionExecutionStrategy,
    HostLLMInteractionStrategy,
    HostMemoryUpdateStrategy,
)
from config.config_loader import get_ufo_config
from ufo.module.context import Context, ContextNames

console = Console()

# Load configuration
ufo_config = get_ufo_config()

if TYPE_CHECKING:
    from ufo.agents.agent.host_agent import HostAgent


class HostAgentProcessor(ProcessorTemplate):
    """
    Enhanced processor for Host Agent with comprehensive functionality.

    This processor manages the complete workflow of a Host Agent including:
    - Desktop environment analysis and screenshot capture
    - Application window detection and registration
    - Third-party agent integration and management
    - LLM-based decision making with context-aware prompting
    - Action execution including application selection and command dispatch
    - Memory management with detailed logging and state tracking

    This processor maintains compatibility with the original BaseProcessor
    interface while providing enhanced modularity and error handling.
    """

    # Override the processor context class to use HostAgentProcessorContext
    processor_context_class: Type[HostAgentProcessorContext] = HostAgentProcessorContext

    def __init__(self, agent: "HostAgent", global_context: Context) -> None:
        """
        Initialize the Host Agent Processor with enhanced capabilities.
        :param agent: The Host Agent instance to be processed
        :param global_context: Global context shared across the session
        """

        # Initialize parent class
        super().__init__(agent, global_context)

    def _setup_strategies(self) -> None:
        """
        Configure processing strategies with enhanced error handling and logging capabilities.
        """
        self.strategies[ProcessingPhase.DATA_COLLECTION] = (
            DesktopDataCollectionStrategy(
                fail_fast=True  # Desktop data collection is critical for Host Agent
            )
        )
        self.strategies[ProcessingPhase.LLM_INTERACTION] = HostLLMInteractionStrategy(
            fail_fast=True  # LLM interaction failure should trigger recovery
        )
        self.strategies[ProcessingPhase.ACTION_EXECUTION] = HostActionExecutionStrategy(
            fail_fast=False  # Action failures can be handled gracefully
        )
        self.strategies[ProcessingPhase.MEMORY_UPDATE] = HostMemoryUpdateStrategy(
            fail_fast=False  # Memory update failures shouldn't stop the process
        )

    def _setup_middleware(self) -> None:
        """
        Set up enhanced middleware chain with comprehensive monitoring and recovery.
        The middleware chain includes:
        - HostAgentLoggingMiddleware: Specialized logging for Host Agent operations
        """
        self.middleware_chain = [
            HostAgentLoggingMiddleware(),  # Specialized logging for Host Agent
        ]

    def _get_processor_specific_context_data(self) -> Dict[str, Any]:
        """
        Get processor-specific context data.

        Subclasses can override this method to provide additional context data
        specific to their processor type.

        :return: Dictionary of processor-specific context initialization data
        """
        return {
            "previous_subtasks": self.global_context.get(ContextNames.PREVIOUS_SUBTASKS)
        }

    def _finalize_processing_context(
        self, processing_context: ProcessingContext
    ) -> None:
        """
        Finalize processing context by updating existing ContextNames fields.
        Instead of promoting arbitrary keys, we update the predefined ContextNames
        that the system actually uses.
        :param processing_context: The processing context to finalize.
        """

        super()._finalize_processing_context(processing_context)
        try:
            # Update SUBTASK if available
            subtask = processing_context.get_local("subtask")
            if subtask:
                self.global_context.set(ContextNames.SUBTASK, subtask)

            # Update HOST_MESSAGE if available
            host_message = processing_context.get_local("host_message")
            if host_message:
                self.global_context.set(ContextNames.HOST_MESSAGE, host_message)

            result = processing_context.get_local("result")
            if result:
                self.global_context.set(ContextNames.ROUND_RESULT, result)

            # Update APPLICATION_ROOT_NAME if selected
            selected_app_root = processing_context.get_local(
                "selected_application_root"
            )
            if selected_app_root:
                self.global_context.set(
                    ContextNames.APPLICATION_ROOT_NAME, selected_app_root
                )

            selected_target: TargetInfo = processing_context.get_local("target")

            if selected_target:
                self.global_context.set(
                    ContextNames.APPLICATION_PROCESS_NAME, selected_target.name
                )
                self.global_context.set(
                    ContextNames.APPLICATION_WINDOW_INFO, selected_target
                )

        except Exception as e:
            self.logger.warning(f"Failed to update ContextNames from results: {e}")


class HostAgentLoggingMiddleware(EnhancedLoggingMiddleware):
    """
    Specialized logging middleware for Host Agent with enhanced contextual information.

    This middleware provides:
    - Host Agent specific progress messages with color coding
    - Detailed step information and context logging
    - Performance metrics and execution summaries
    - Enhanced error reporting with Host Agent context
    """

    def __init__(self) -> None:
        """Initialize Host Agent logging middleware with appropriate log level."""
        super().__init__(log_level=logging.INFO)

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """
        Log Host Agent processing start with detailed context information.
        :param processor: Host Agent processor instance
        :param context: Processing context with round and step information
        """
        # Call parent implementation for standard logging
        await super().before_process(processor, context)

        # Add Host Agent specific logging
        round_num = context.get("round_num", 0)
        round_step = context.get("round_step", 0)
        request = context.get("request", "")

        # Log detailed context information
        self.logger.info(
            f"Host Agent Processing Context - "
            f"Round: {round_num + 1}, Step: {round_step + 1}, "
            f"Request: '{request[:100]}{'...' if len(request) > 100 else ''}'"
        )

        # Display colored progress message for user feedback (maintaining original UX)
        # This has been replaced with Rich Panel display below

        panel_title = f"🚀 Round {round_num + 1}, Step {round_step + 1}, Agent: {processor.agent.name}"
        panel_content = (
            f"Analyzing user intent and decomposing request of `{request}`..."
        )

        console.print(Panel(panel_content, title=panel_title, style="magenta"))

        # Log available context data for debugging
        if self.logger.isEnabledFor(logging.DEBUG):
            context_keys = list(
                context.local_data.keys()
            )  # This uses the backward-compatible property
            self.logger.debug(f"Available context keys: {context_keys}")

    async def after_process(
        self, processor: ProcessorTemplate, result: ProcessingResult
    ) -> None:
        """
        Log Host Agent processing completion with execution summary.
        :param processor: Host Agent processor instance
        :param result: Processing result with execution data
        """
        # Call parent implementation for standard logging
        await super().after_process(processor, result)

        if result.success:
            # Log Host Agent specific success information
            selected_app = result.data.get("selected_application_root", "")
            assigned_agent = result.data.get("assigned_third_party_agent", "")
            subtask = result.data.get("subtask", "")

            success_msg = "Host Agent processing completed successfully"
            if selected_app:
                success_msg += f" - Selected application: {selected_app}"
            elif assigned_agent:
                success_msg += f" - Assigned third-party agent: {assigned_agent}"
            if subtask:
                success_msg += f" - Current subtask: {subtask}"

            self.logger.info(success_msg)

            # Display user-friendly completion message (maintaining original UX)
            if selected_app or assigned_agent:
                target_name = selected_app or assigned_agent
                console.print(
                    Panel(
                        f"Successfully selected target '{target_name}'",
                        title="✅ HostAgent",
                        style="green",
                    )
                )
        else:
            # Enhanced error logging for Host Agent
            error_phase = getattr(result, "phase", "unknown")
            self.logger.error(
                f"Host Agent processing failed at phase: {error_phase} - {result.error}"
            )

            # Display user-friendly error message (maintaining original UX)
            console.print(
                Panel(
                    f"Processing failed - {result.error}",
                    title="❌ HostAgent",
                    style="red",
                )
            )

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """
        Enhanced error handling for Host Agent with contextual information.
        :param processor: Host Agent processor instance
        :param error: Exception that occurred
        """
        # Call parent implementation for standard error handling
        await super().on_error(processor, error)

        console.print(
            Panel(
                f"Encountered error - {str(error)}",
                title="❌ HostAgent",
                style="red",
            )
        )
