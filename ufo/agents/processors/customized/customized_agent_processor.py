# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Customized Agent Processor - Modern, extensible Customized Agent processing implementation.

This module implements the architecture for Customized Agent processing, providing:
- Type-safe context management with AppAgentProcessorContext
- Modular strategy-based processing pipeline
- Comprehensive middleware stack for error handling, performance monitoring, and logging
- Flexible dependency injection and configuration
- Robust error handling and recovery mechanisms
"""

from typing import TYPE_CHECKING
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.agents.processors.context.processing_context import (
    ProcessingContext,
    ProcessingPhase,
)
from ufo.agents.processors.strategies.app_agent_processing_strategy import (
    AppActionExecutionStrategy,
    AppMemoryUpdateStrategy,
)
from ufo.agents.processors.strategies.customized_agent_processing_strategy import (
    CustomizedLLMInteractionStrategy,
    CustomizedScreenshotCaptureStrategy,
)
from ufo.agents.processors.strategies.linux_agent_strategy import (
    LinuxActionExecutionStrategy,
    LinuxLLMInteractionStrategy,
    LinuxLoggingMiddleware,
)
from ufo.agents.processors.strategies.mobile_agent_strategy import (
    MobileScreenshotCaptureStrategy,
    MobileAppsCollectionStrategy,
    MobileControlsCollectionStrategy,
    MobileLLMInteractionStrategy,
    MobileActionExecutionStrategy,
    MobileLoggingMiddleware,
)
from ufo.agents.processors.strategies.processing_strategy import ComposedStrategy
from ufo.module.context import Context, ContextNames


if TYPE_CHECKING:
    from ufo.agents.agent.customized_agent import CustomizedAgent


class CustomizedProcessor(AppAgentProcessor):
    """
    Customized Agent Processor - Modern, extensible Customized Agent processing implementation.
    """

    def __init__(self, agent: "CustomizedAgent", global_context: "Context") -> None:
        """Initialize Customized Agent Processor."""
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
    Processor for Hardware Agent.
    """

    pass


class LinuxAgentProcessor(CustomizedProcessor):
    """
    Processor for Linux MCP Agent.
    """

    def _setup_strategies(self) -> None:

        self.strategies[ProcessingPhase.LLM_INTERACTION] = LinuxLLMInteractionStrategy(
            fail_fast=True
        )

        self.strategies[ProcessingPhase.ACTION_EXECUTION] = (
            LinuxActionExecutionStrategy(fail_fast=False)
        )

        # Memory update strategy
        self.strategies[ProcessingPhase.MEMORY_UPDATE] = AppMemoryUpdateStrategy(
            fail_fast=False  # Memory update failures shouldn't stop the process
        )

    def _setup_middleware(self) -> None:
        """Setup middleware pipeline for App Agent."""
        # Core middleware (order matters)
        self.middleware_chain = [LinuxLoggingMiddleware()]

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

            result = processing_context.get_local("result")
            if result:
                self.global_context.set(ContextNames.ROUND_RESULT, result)

        except Exception as e:
            self.logger.warning(f"Failed to update ContextNames from results: {e}")


class MobileAgentProcessor(CustomizedProcessor):
    """
    Processor for Mobile Android MCP Agent.
    Handles data collection, LLM interaction, and action execution for Android devices.
    """

    def _setup_strategies(self) -> None:
        """Setup processing strategies for Mobile Agent."""

        # Data collection strategies - compose multiple strategies into one
        self.strategies[ProcessingPhase.DATA_COLLECTION] = ComposedStrategy(
            strategies=[
                MobileScreenshotCaptureStrategy(fail_fast=True),
                MobileAppsCollectionStrategy(fail_fast=False),
                MobileControlsCollectionStrategy(fail_fast=False),
            ],
            name="MobileDataCollectionStrategy",
            fail_fast=True,
        )

        # LLM interaction strategy (depends on all collected data)
        self.strategies[ProcessingPhase.LLM_INTERACTION] = MobileLLMInteractionStrategy(
            fail_fast=True
        )

        # Action execution strategy
        self.strategies[ProcessingPhase.ACTION_EXECUTION] = (
            MobileActionExecutionStrategy(fail_fast=False)
        )

        # Memory update strategy
        self.strategies[ProcessingPhase.MEMORY_UPDATE] = AppMemoryUpdateStrategy(
            fail_fast=False
        )

    def _setup_middleware(self) -> None:
        """Setup middleware pipeline for Mobile Agent."""
        # Use Mobile logging middleware for proper request display
        self.middleware_chain = [MobileLoggingMiddleware()]

    def _finalize_processing_context(
        self, processing_context: ProcessingContext
    ) -> None:
        """
        Finalize processing context by updating existing ContextNames fields.
        :param processing_context: The processing context to finalize.
        """
        super()._finalize_processing_context(processing_context)
        try:
            result = processing_context.get_local("result")
            if result:
                self.global_context.set(ContextNames.ROUND_RESULT, result)
        except Exception as e:
            self.logger.warning(f"Failed to update ContextNames from results: {e}")
