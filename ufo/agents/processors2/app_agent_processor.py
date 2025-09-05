# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
App Agent Processor V2 - Modern, extensible App Agent processing implementation.

This module implements the V2 architecture for App Agent processing, providing:
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

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ufo.agents.processors2.core.processor_framework import ProcessorTemplate
from ufo.agents.processors2.core.processing_context import (
    BasicProcessorContext,
    ProcessingContext,
)

from ufo.agents.processors2.middleware.enhanced_middleware import (
    EnhancedLoggingMiddleware,
)
from ufo.agents.processors2.strategies.app_agent_processing_strategy import (
    AppActionExecutionStrategy,
    AppLLMInteractionStrategy,
    AppMemoryUpdateStrategy,
    ComposedAppDataCollectionStrategy,
)
from ufo.module.context import Context

if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent


@dataclass
class AppAgentProcessorContext(BasicProcessorContext):
    """
    Extended processing context for App Agent with app-specific data fields.

    This context extends the basic ProcessingContext to include app-specific data:
    - Application window information and screenshot paths
    - UI control information and filtering results
    - LLM interaction data and parsed responses
    - Action execution results and memory updates
    - Performance metrics and debugging information

    All fields support selective serialization for robust error handling.
    """

    # App Agent type identifier
    agent_type: str = "AppAgent"

    # Application and UI data
    app_root: Optional[Any] = None  # Application window root element
    current_application: str = ""  # Application name/identifier

    # Screenshot and visual data
    clean_screenshot_path: str = ""  # Path to clean screenshot
    annotated_screenshot_path: str = ""  # Path to annotated screenshot
    desktop_screenshot_path: str = ""  # Path to desktop screenshot
    screenshot_saved_time: float = 0.0  # Time taken for screenshot operations

    # Control and UI information
    filtered_controls: List[Dict[str, Any]] = field(
        default_factory=list
    )  # Filtered UI controls
    control_info: List[Dict[str, Any]] = field(
        default_factory=list
    )  # Alias for filtered_controls
    annotation_dict: Dict[str, Any] = field(
        default_factory=dict
    )  # Control annotation dictionary
    control_filter_time: float = 0.0  # Time taken for control filtering
    control_info_recorder: Optional[Any] = None  # Control information recorder

    # LLM interaction data - extends base parsed_response
    response_text: str = ""  # Raw LLM response text
    prompt_message: Dict[str, Any] = field(
        default_factory=dict
    )  # Constructed prompt message
    function_name: str = ""  # Function name from response
    function_arguments: Dict[str, Any] = field(
        default_factory=dict
    )  # Function arguments from response
    save_screenshot: Dict[str, Any] = field(
        default_factory=dict
    )  # Screenshot saving configuration

    # Action execution data
    execution_result: List[Any] = field(
        default_factory=list
    )  # Action execution results
    action_info: Optional[Any] = None  # Action command information
    action_success: bool = False  # Whether action was successful
    control_log: Dict[str, Any] = field(default_factory=dict)  # Control interaction log

    # Memory and blackboard data
    additional_memory: Optional[Any] = (
        None  # Additional memory data (AppAgentAdditionalMemory)
    )
    memory_item: Optional[Any] = None  # Created memory item
    updated_blackboard: bool = False  # Whether blackboard was updated

    # Performance and debugging data
    app_performance_metrics: Dict[str, Any] = field(
        default_factory=dict
    )  # Performance monitoring data
    app_error_handler_active: bool = False  # Error handler status
    app_logging_active: bool = False  # Logging middleware status
    app_memory_sync_active: bool = False  # Memory sync middleware status

    def __post_init__(self) -> None:
        """
        Initialize after dataclass construction.
        """
        super().__post_init__() if hasattr(super(), "__post_init__") else None

        # Initialize app-specific performance metrics
        if not self.app_performance_metrics:
            self.app_performance_metrics = {
                "agent_type": "AppAgent",
                "start_time": 0.0,
                "phase_timings": {},
            }

    @property
    def selected_keys(self) -> List[str]:
        """
        Get keys that should be included in selective serialization.
        Excludes potentially unpicklable objects.
        """
        return [
            # Basic fields from parent
            "agent_type",
            "session_step",
            "round_step",
            "round_num",
            "cost",
            "status",
            "request",
            "llm_cost",
            # App-specific serializable fields
            "current_application",
            "clean_screenshot_path",
            "annotated_screenshot_path",
            "desktop_screenshot_path",
            "screenshot_saved_time",
            "filtered_controls",
            "annotation_dict",
            "control_filter_time",
            "response_text",
            "prompt_message",
            "function_name",
            "function_arguments",
            "save_screenshot",
            "action_success",
            "control_log",
            "updated_blackboard",
            "app_performance_metrics",
            "app_error_handler_active",
            "app_logging_active",
            "app_memory_sync_active",
            # Performance and error tracking from parent
            "execution_times",
            "total_time",
            "error_count",
            "last_error",
        ]


class AppAgentProcessorV2(ProcessorTemplate):
    """
    App Agent Processor V2 - Modern, extensible App Agent processing implementation.

    This processor implements the complete V2 architecture for App Agent:
    - Uses AppAgentProcessorContext for type-safe app-specific data
    - Implements modular strategy-based processing pipeline
    - Provides comprehensive middleware stack
    - Supports flexible configuration and dependency injection
    - Includes robust error handling and performance monitoring

    Processing Pipeline:
    1. Data Collection: Screenshot capture and UI control information
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

        # Initialize processing strategies
        self._setup_strategies()

        # Initialize middleware pipeline
        self._setup_middleware()

    def _setup_strategies(self) -> None:
        """Setup processing strategies for App Agent."""
        from ufo.agents.processors2.core.processing_context import ProcessingPhase

        # Data collection strategy (combines screenshot + control info)
        self.strategies[ProcessingPhase.DATA_COLLECTION] = ComposedAppDataCollectionStrategy(
            fail_fast=True  # Data collection is critical for App Agent
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
        self.middleware_chain = [EnhancedLoggingMiddleware()]

    def get_required_context_keys(self) -> List[str]:
        """
        Get list of required context keys for App Agent processing.
        :return: List of required context keys
        """
        return [
            # Basic processing data
            "request",  # User request
            "subtask",  # Current subtask
            "plan",  # Task plan
            "session_step",  # Current step number
            "round_step",  # Round step number
            "round_num",  # Round number
            "log_path",  # Logging path
            # Application-specific data
            "app_root",  # Application window root
            "current_application",  # Application identifier
            # Optional but commonly used
            "previous_subtasks",  # Previous subtasks (optional)
            "subtask_index",  # Subtask index (optional)
        ]

    def _finalize_processing_context(
        self, processing_context: "ProcessingContext"
    ) -> None:
        """
        Finalize processing context, deciding what to promote to global context.
        :param processing_context: The processing context to finalize.
        """
        try:
            # Call parent implementation for standard finalization
            super()._finalize_processing_context(processing_context)

            # Add app-specific context finalization
            if hasattr(processing_context, "llm_cost"):
                self.logger.debug(
                    f"App Agent LLM cost: ${processing_context.llm_cost:.4f}"
                )

            if hasattr(processing_context, "action_success"):
                self.logger.debug(
                    f"App Agent action success: {processing_context.action_success}"
                )

            if hasattr(processing_context, "app_performance_metrics"):
                metrics = processing_context.app_performance_metrics
                if "total_time" in metrics:
                    self.logger.debug(
                        f"App Agent total processing time: {metrics['total_time']:.2f}s"
                    )

        except Exception as e:
            self.logger.error(f"App Agent context finalization failed: {str(e)}")
