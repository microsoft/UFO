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
from ufo.agents.processors2.app_agent_processor import (
    AppAgentProcessorContext,
    AppAgentProcessorV2,
)
from ufo.agents.processors2.strategies.app_agent_processing_strategy import (
    AppActionExecutionStrategy,
    AppMemoryUpdateStrategy,
)
from ufo.agents.processors2.strategies.customized_agent_processing_strategy import (
    CustomizedLLMInteractionStrategy,
    CustomizedScreenshotCaptureStrategy,
)
from ufo.module.context import Context


if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent


class CustomizedProcessorV2(AppAgentProcessorV2):
    """
    Customized Agent Processor V2 - Modern, extensible Customized Agent processing implementation.

    This processor implements the complete V2 architecture for Customized Agent:
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
    - Error handling and recovery middleware
    - Performance monitoring and timing middleware
    - Structured logging and debugging middleware
    - Memory and blackboard synchronization middleware
    """

    # Specify the custom context class for this processor
    processor_context_class = AppAgentProcessorContext

    def __init__(self, agent: "AppAgent", global_context: "Context") -> None:
        """Initialize App Agent Processor V2."""
        super().__init__(agent, global_context)

    def _setup_strategies(self) -> None:
        """Setup processing strategies for App Agent."""
        from ufo.agents.processors2.core.processing_context import ProcessingPhase

        # Data collection strategy (combines screenshot + control info)
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
