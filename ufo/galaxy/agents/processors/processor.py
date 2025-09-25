# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation Agent Processor - Processor for Constellation Agent using the new framework.
"""


import logging
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, Type

from rich.console import Console
from rich.panel import Panel

from ufo import utils
from ufo.agents.processors.core.processing_middleware import EnhancedLoggingMiddleware
from ufo.agents.processors.core.processor_framework import (
    ProcessingContext,
    ProcessingPhase,
    ProcessorTemplate,
)
from ufo.config import Config
from ufo.galaxy.agents.processors.processor_context import ConstellationProcessorContext
from ufo.galaxy.agents.processors.factory.constellation_factory import (
    ConstellationStrategyFactory,
)
from ufo.module.context import Context, ContextNames

if TYPE_CHECKING:
    from ufo.galaxy.agents.constellation_agent import ConstellationAgent


console = Console()

# Load configuration
configs = Config.get_instance().config_data


class ConstellationAgentProcessor(ProcessorTemplate):
    """
    Enhanced processor for Galaxy Creator Agent with comprehensive functionality.

    This processor manages the complete workflow of a Galaxy Creator Agent including:
    - Desktop environment analysis and screenshot capture
    - Application window detection and registration
    - Third-party agent integration and management
    - LLM-based decision making with context-aware prompting
    - Action execution including application selection and command dispatch
    - Memory management with detailed logging and state tracking

    This processor maintains compatibility with the original BaseProcessor
    interface while providing enhanced modularity and error handling.
    """

    # Override the processor context class to use ConstellationProcessorContext
    processor_context_class: Type[ConstellationProcessorContext] = (
        ConstellationProcessorContext
    )

    def __init__(self, agent: "ConstellationAgent", global_context: Context) -> None:
        """
        Initialize the Galaxy Creator Agent Processor with enhanced capabilities.
        :param agent: The Galaxy Creator Agent instance to be processed
        :param global_context: Global context shared across the session
        """

        # Initialize parent class
        super().__init__(agent, global_context)

    def _setup_strategies(self) -> None:
        """
        Configure processing strategies with enhanced error handling and logging capabilities.
        Uses factory pattern to create appropriate strategies based on weaving mode.
        """
        # Get weaving mode from global context
        weaving_mode = self.global_context.get(ContextNames.WEAVING_MODE)

        if not weaving_mode:
            raise ValueError("Weaving mode must be specified in global context")

        # Create strategies using factory based on weaving mode
        self.strategies[ProcessingPhase.LLM_INTERACTION] = (
            ConstellationStrategyFactory.create_llm_interaction_strategy(
                fail_fast=True,  # LLM interaction failure should trigger recovery
            )
        )
        self.strategies[ProcessingPhase.ACTION_EXECUTION] = (
            ConstellationStrategyFactory.create_action_execution_strategy(
                weaving_mode=weaving_mode,
                fail_fast=False,  # Action failures can be handled gracefully
            )
        )
        self.strategies[ProcessingPhase.MEMORY_UPDATE] = (
            ConstellationStrategyFactory.create_memory_update_strategy(
                fail_fast=False  # Memory update failures shouldn't stop the process
            )
        )

    def _setup_middleware(self) -> None:
        """
        Set up enhanced middleware chain with comprehensive monitoring and recovery.
        The middleware chain includes:
        - ConstellationLoggingMiddleware: Specialized logging for Constellation Agent operations
        """
        self.middleware_chain = [
            ConstellationLoggingMiddleware(),  # Specialized logging for Constellation Agent
        ]

    def _get_processor_specific_context_data(self) -> Dict[str, Any]:
        """
        Get processor-specific context data.

        Subclasses can override this method to provide additional context data
        specific to their processor type.

        :return: Dictionary of processor-specific context initialization data
        """

        before_constellation = self.global_context.get(ContextNames.CONSTELLATION)

        if before_constellation:
            constellation_before_json = before_constellation.to_json()
        else:
            constellation_before_json = None

        return {
            "weaving_mode": self.global_context.get(ContextNames.WEAVING_MODE),
            "device_info": [self.global_context.get(ContextNames.DEVICE_INFO)],
            "constellation_before": constellation_before_json,
        }


class ConstellationLoggingMiddleware(EnhancedLoggingMiddleware):
    """
    Specialized logging middleware for Constellation Agent with enhanced contextual information.

    This middleware provides:
    - Constellation Agent specific progress messages with color coding
    - Detailed step information and context logging
    - Performance metrics and execution summaries
    - Enhanced error reporting with Constellation Agent context
    """

    def __init__(self) -> None:
        """Initialize Constellation Agent logging middleware with appropriate log level."""
        super().__init__(log_level=logging.INFO)

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """
        Log Constellation Agent processing start with detailed context information.
        :param processor: Constellation Agent processor instance
        :param context: Processing context with round and step information
        """
        # Call parent implementation for standard logging
        await super().before_process(processor, context)

        # Add Constellation Agent specific logging
        round_num = context.get("round_num", 0)
        round_step = context.get("round_step", 0)
        request = context.get("request", "")

        # Log detailed context information
        self.logger.info(
            f"Constellation Agent Processing Context - "
            f"Round: {round_num + 1}, Step: {round_step + 1}, "
            f"Request: '{request[:100]}{'...' if len(request) > 100 else ''}'"
        )

        panel_title = f"🚀 Round {round_num + 1}, Step {round_step + 1}, Agent: {processor.agent.name}"
        panel_content = (
            f"Analyzing user intent and decomposing request into device agents..."
        )

        console.print(Panel(panel_content, title=panel_title, style="magenta"))

        # Log available context data for debugging
        if self.logger.isEnabledFor(logging.DEBUG):
            context_keys = list(
                context.local_data.keys()
            )  # This uses the backward-compatible property
            self.logger.debug(f"Available context keys: {context_keys}")

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """
        Enhanced error handling for Constellation Agent with contextual information.
        :param processor: Constellation Agent processor instance
        :param error: Exception that occurred
        """
        # Call parent implementation for standard error handling
        await super().on_error(processor, error)

        utils.print_with_color(
            f"ConstellationAgent: Encountered error - {str(error)}", "red"
        )
