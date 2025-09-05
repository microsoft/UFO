# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Host Agent Processor V2 - Refactored processor for Host Agent using the new framework.

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


from dataclasses import dataclass, field
import logging

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type


from ufo import utils

from ufo.agents.processors.actions import ActionCommandInfo
from ufo.agents.processors.target import TargetInfo
from ufo.agents.processors2.strategies.host_agent_processing_strategy import (
    DesktopDataCollectionStrategy,
    HostLLMInteractionStrategy,
    HostActionExecutionStrategy,
    HostMemoryUpdateStrategy,
)
from ufo.agents.processors2.core.processor_framework import (
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
    ProcessorTemplate,
)
from ufo.agents.processors2.core.processing_context import BasicProcessorContext
from ufo.agents.processors2.middleware.enhanced_middleware import (
    EnhancedLoggingMiddleware,
)
from ufo.config import Config
from ufo.module.context import Context, ContextNames

# Load configuration
configs = Config.get_instance().config_data

if TYPE_CHECKING:
    from ufo.agents.agent.host_agent import HostAgent


if TYPE_CHECKING:
    from ufo.agents.agent.host_agent import HostAgent


@dataclass
class HostAgentProcessorContext(BasicProcessorContext):
    """
    Host Agent specific processor context.

    This extends the basic context with Host Agent specific data including
    target management, application selection, and third-party agent coordination.
    """

    # Host Agent specific data
    agent_type: str = "HostAgent"

    # Plan and subtask management
    prev_plan: List[str] = field(default_factory=list)
    previous_subtasks: List[str] = field(default_factory=list)
    current_plan: List[str] = field(default_factory=list)

    # Target and application state
    target_info_list: List[Dict[str, TargetInfo]] = field(default_factory=list)
    selected_application_root: Optional[str] = None
    selected_target_id: Optional[str] = None
    assigned_third_party_agent: Optional[str] = None

    # Screenshot and visual data
    desktop_screenshot_url: Optional[str] = None
    screenshot_paths: Dict[str, str] = field(default_factory=dict)

    # Action and control information
    action_info: Optional[ActionCommandInfo] = None
    control_label: str = ""
    control_text: str = ""
    action_result: Optional[Any] = None

    assigned_third_party_agent: Optional[str] = None

    # Additional fields from HostAgentUnifiedMemory for complete compatibility
    step: int = (
        0  # Duplicated from basic context session_step but kept for compatibility
    )
    agent_step: int = 0
    subtask_index: int = -1
    action: List[Dict[str, Any]] = field(default_factory=list)
    function_call: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    action_type: str = ""
    agent_name: str = ""
    application: str = ""
    results: str = ""
    control_log: Dict[str, Any] = field(default_factory=dict)

    # LLM and cost tracking
    llm_cost: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    # Logging and debugging
    log_path: str = ""
    debug_info: Dict[str, Any] = field(default_factory=dict)

    @property
    def selected_keys(self) -> List[str]:
        """
        The list of selected keys for to dict.
        Returns fields corresponding to HostAgentAdditionalMemory.
        """
        return [
            "step",  # Step
            "round_step",  # RoundStep
            "agent_step",  # AgentStep
            "round_num",  # Round
            "control_label",  # ControlLabel
            "subtask_index",  # SubtaskIndex
            "action",  # Action
            "function_call",  # FunctionCall
            "arguments",  # Arguments
            "action_type",  # ActionType
            "request",  # Request
            "agent_type",  # Agent
            "agent_name",  # AgentName
            "application",  # Application
            "cost",  # Cost
            "results",  # Results
            "last_error",  # error (mapped to last_error)
            "execution_times",  # time_cost (mapped to execution_times)
            "total_time",
            "control_log",  # ControlLog
        ]


class HostAgentProcessorV2(ProcessorTemplate):
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
        # Core components and tools - kept in __init__
        self.host_agent: "HostAgent" = agent

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
        utils.print_with_color(
            f"Round {round_num + 1}, Step {round_step + 1}, HostAgent: "
            f"Analyzing user intent and decomposing request...",
            "magenta",
        )

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
                utils.print_with_color(
                    f"HostAgent: Successfully selected target '{target_name}'", "green"
                )
        else:
            # Enhanced error logging for Host Agent
            error_phase = getattr(result, "phase", "unknown")
            self.logger.error(
                f"Host Agent processing failed at phase: {error_phase} - {result.error}"
            )

            # Display user-friendly error message (maintaining original UX)
            utils.print_with_color(
                f"HostAgent: Processing failed - {result.error}", "red"
            )

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """
        Enhanced error handling for Host Agent with contextual information.
        :param processor: Host Agent processor instance
        :param error: Exception that occurred
        """
        # Call parent implementation for standard error handling
        await super().on_error(processor, error)

        utils.print_with_color(
            f"HostAgent: Encountered error - {str(error)[:100]}", "red"
        )
