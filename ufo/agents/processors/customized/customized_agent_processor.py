# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Customized Agent Processor V2 - Modern, extensible Customized Agent processing implementation.

This module implements the V2 architecture for Customized Agent processing, providing:
- Type-safe context management with AppAgentProcessorContext
- Modular strategy-based processing pipeline
- Comprehensive middleware stack for error handling, performance monitoring, and logging
- Flexible dependency injection and configuration
- Robust error handling and recovery mechanisms

The processor follows the established V2 patterns:
- ProcessorTemplate with processor_context_class override
- Strategy-based phase processing (screenshot, control info, LLM, action, memory)
- Middleware pipeline for cross-cutting concerns
- Structured logging and performance monitoring
"""

from typing import TYPE_CHECKING
from ufo.agents.processors.app_agent_processor import (
    AppAgentProcessorContext,
    AppAgentProcessor,
)
from ufo.agents.processors.strategies.app_agent_processing_strategy import (
    AppActionExecutionStrategy,
    AppMemoryUpdateStrategy,
)
from ufo.agents.processors.strategies.customized_agent_processing_strategy import (
    CustomizedLLMInteractionStrategy,
    CustomizedScreenshotCaptureStrategy,
)
from ufo.module.context import Context


if TYPE_CHECKING:
    from ufo.agents.agent.customized_agent import CustomizedAgent


class CustomizedProcessor(AppAgentProcessor):
    """
    Customized Agent Processor V2 - Modern, extensible Customized Agent processing implementation.
    """

    # Specify the custom context class for this processor
    processor_context_class = AppAgentProcessorContext

    def __init__(self, agent: "CustomizedAgent", global_context: "Context") -> None:
        """Initialize Customized Agent Processor V2."""
        super().__init__(agent, global_context)

    def _setup_strategies(self) -> None:
        """Setup processing strategies for Customized Agent."""
        from ufo.agents.processors.context.processing_context import ProcessingPhase

        # Data collection strategy for screenshots capture
        self.strategies[ProcessingPhase.DATA_COLLECTION] = (
            CustomizedScreenshotCaptureStrategy(
                fail_fast=True,
            )
        )

        # LLM interaction strategy
        self.strategies[ProcessingPhase.LLM_INTERACTION] = (
            CustomizedLLMInteractionStrategy(
                fail_fast=True  # LLM interaction failure should trigger recovery
            )
        )

        # Action execution strategy
        self.strategies[ProcessingPhase.ACTION_EXECUTION] = AppActionExecutionStrategy(
            fail_fast=False  # Action failures can be handled gracefully
        )

        # Memory update strategy
        self.strategies[ProcessingPhase.MEMORY_UPDATE] = AppMemoryUpdateStrategy(
            fail_fast=False  # Memory update failures shouldn't stop the process
        )


class HardwareAgentProcessor(CustomizedProcessor):
    """
    Processor for Hardware Agent using V2 architecture.
    """

    pass
