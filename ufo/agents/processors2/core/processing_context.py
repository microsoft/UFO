"""
Processing Context Management Module

This module provides a clean separation between different types of context data:
- ProcessingContext: Enhanced processing context with unified typed/dict interface
- BasicProcessorContext: Base context for all processors
- HostAgentProcessorContext: Host Agent specific context
- AppAgentProcessorContext: App Agent specific context

The design follows composition over inheritance principles and provides
type-safe context management with clear separation of concerns.
"""

from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING, TypeVar, Union
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from ufo.agents.agent.basic import BasicAgent
    from ufo.agents.agent.host_agent import HostAgent
    from ufo.agents.agent.app_agent import AppAgent
    from ufo.module.context import Context


class ProcessingPhase(Enum):
    """
    Enum for processing phases.
    """

    SETUP = "setup"
    DATA_COLLECTION = "data_collection"
    LLM_INTERACTION = "llm_interaction"
    ACTION_EXECUTION = "action_execution"
    MEMORY_UPDATE = "memory_update"
    CLEANUP = "cleanup"


@dataclass
class ProcessingResult:
    """
    Data class for processing results.
    """

    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    phase: Optional[ProcessingPhase] = None
    execution_time: float = 0.0


class ProcessorContextProtocol(ABC):
    """
    Protocol for processor context classes.

    This defines the interface that all processor context classes should implement
    to ensure consistency and type safety across different agent types.
    """

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for framework compatibility."""
        pass

    @abstractmethod
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update context from dictionary data."""
        pass

    @abstractmethod
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of context data for logging/debugging."""
        pass


@dataclass
class BasicProcessorContext(ProcessorContextProtocol):
    """
    Basic processor context containing common data across all agent types.

    This serves as the base class for all processor-specific contexts and contains
    the fundamental data needed by the processing framework.
    """

    # Core processor data
    agent: Optional["BasicAgent"] = None
    processor: Optional[Any] = None  # Reference to the processor instance

    # Session and timing information
    session_step: int = 0
    round_step: int = 0
    round_num: int = 0
    cost: float = 0.0

    # Request and response data
    request: str = ""
    parsed_response: Optional[Any] = None

    # Performance and error tracking
    execution_times: Dict[str, float] = field(default_factory=dict)
    error_count: int = 0
    last_error: Optional[str] = None

    # Generic data storage for extensibility
    custom_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary for framework compatibility.
        :return: Dictionary representation of context data
        """
        return {
            "agent": self.agent,
            "processor": self.processor,
            "session_step": self.session_step,
            "round_step": self.round_step,
            "round_num": self.round_num,
            "cost": self.cost,
            "request": self.request,
            "parsed_response": self.parsed_response,
            "execution_times": self.execution_times.copy(),
            "error_count": self.error_count,
            "last_error": self.last_error,
            **self.custom_data,
        }

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Update context from dictionary data.
        :param data: Dictionary containing context updates
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.custom_data[key] = value

    def get_context_summary(self) -> Dict[str, Any]:
        """
        Get a summary of context data for logging/debugging.
        :return: Summary dictionary with key context information
        """
        return {
            "agent_type": self.agent.__class__.__name__ if self.agent else "Unknown",
            "session_step": self.session_step,
            "round_info": f"Round {self.round_num}, Step {self.round_step}",
            "cost": f"${self.cost:.4f}",
            "error_count": self.error_count,
            "custom_data_keys": list(self.custom_data.keys()),
            "has_response": self.parsed_response is not None,
        }

    def add_execution_time(self, phase: str, time: float) -> None:
        """
        Add execution time for a processing phase.
        :param phase: Name of the processing phase
        :param time: Execution time in seconds
        """
        self.execution_times[phase] = time

    def increment_error_count(self, error_msg: Optional[str] = None) -> None:
        """
        Increment error count and optionally store last error.
        :param error_msg: Optional error message to store
        """
        self.error_count += 1
        if error_msg:
            self.last_error = error_msg

    def reset_error_tracking(self) -> None:
        """Reset error tracking counters."""
        self.error_count = 0
        self.last_error = None


@dataclass
class HostAgentProcessorContext(BasicProcessorContext):
    """
    Host Agent specific processor context.

    This extends the basic context with Host Agent specific data including
    target management, application selection, and third-party agent coordination.
    """

    # Host Agent specific data
    host_agent: Optional["HostAgent"] = None
    target_registry: Optional[Any] = None
    command_dispatcher: Optional[Any] = None

    # Plan and subtask management
    prev_plan: List[str] = field(default_factory=list)
    previous_subtasks: List[str] = field(default_factory=list)
    current_plan: List[str] = field(default_factory=list)

    # Target and application state
    target_info_list: List[Dict[str, Any]] = field(default_factory=list)
    selected_application_root: Optional[str] = None
    selected_target_id: Optional[str] = None
    assigned_third_party_agent: Optional[str] = None

    # Screenshot and visual data
    desktop_screenshot_url: Optional[str] = None
    screenshot_paths: Dict[str, str] = field(default_factory=dict)

    # Action and control information
    action_info: Optional[Any] = None
    control_label: str = ""
    control_text: str = ""
    action_result: Optional[Any] = None

    # Additional fields from HostAgentUnifiedMemory for complete compatibility
    step: int = (
        0  # Duplicated from basic context session_step but kept for compatibility
    )
    agent_step: int = 0
    subtask_index: int = -1
    action: List[Dict[str, Any]] = field(default_factory=list)
    function_call: str = ""
    action_type: str = "MCP"
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

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Host Agent context to dictionary.
        :return: Dictionary representation including Host Agent specific data
        """
        base_dict = super().to_dict()
        host_dict = {
            "host_agent": self.host_agent,
            "target_registry": self.target_registry,
            "command_dispatcher": self.command_dispatcher,
            "prev_plan": self.prev_plan.copy(),
            "previous_subtasks": self.previous_subtasks.copy(),
            "current_plan": self.current_plan.copy(),
            "target_info_list": self.target_info_list.copy(),
            "selected_application_root": self.selected_application_root,
            "selected_target_id": self.selected_target_id,
            "assigned_third_party_agent": self.assigned_third_party_agent,
            "desktop_screenshot_url": self.desktop_screenshot_url,
            "screenshot_paths": self.screenshot_paths.copy(),
            "action_info": self.action_info,
            "control_label": self.control_label,
            "control_text": self.control_text,
            "action_result": self.action_result,
            "step": self.step,
            "agent_step": self.agent_step,
            "subtask_index": self.subtask_index,
            "action": self.action.copy(),
            "function_call": self.function_call,
            "action_type": self.action_type,
            "agent_name": self.agent_name,
            "application": self.application,
            "results": self.results,
            "control_log": self.control_log.copy(),
            "llm_cost": self.llm_cost,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "log_path": self.log_path,
            "debug_info": self.debug_info.copy(),
        }
        base_dict.update(host_dict)
        return base_dict

    def get_context_summary(self) -> Dict[str, Any]:
        """
        Get Host Agent context summary.
        :return: Summary with Host Agent specific information
        """
        base_summary = super().get_context_summary()
        host_summary = {
            "target_count": len(self.target_info_list),
            "selected_app": self.selected_application_root or "None",
            "third_party_agent": self.assigned_third_party_agent or "None",
            "has_screenshot": self.desktop_screenshot_url is not None,
            "plan_steps": len(self.prev_plan),
            "llm_cost": f"${self.llm_cost:.4f}",
            "tokens_used": f"{self.prompt_tokens + self.completion_tokens}",
        }
        base_summary.update(host_summary)
        return host_summary

    def update_target_selection(
        self,
        target_id: Optional[str] = None,
        app_root: Optional[str] = None,
        third_party_agent: Optional[str] = None,
    ) -> None:
        """
        Update target selection information.
        :param target_id: Selected target ID
        :param app_root: Selected application root
        :param third_party_agent: Assigned third-party agent
        """
        if target_id is not None:
            self.selected_target_id = target_id
        if app_root is not None:
            self.selected_application_root = app_root
        if third_party_agent is not None:
            self.assigned_third_party_agent = third_party_agent

    def update_control_info(self, label: str = "", text: str = "") -> None:
        """
        Update control information.
        :param label: Control label
        :param text: Control text
        """
        if label:
            self.control_label = label
        if text:
            self.control_text = text

    def add_llm_cost(
        self, cost: float, prompt_tokens: int = 0, completion_tokens: int = 0
    ) -> None:
        """
        Add LLM cost and token usage.
        :param cost: LLM cost to add
        :param prompt_tokens: Number of prompt tokens
        :param completion_tokens: Number of completion tokens
        """
        self.llm_cost += cost
        self.cost += cost  # Update base cost as well
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens

    def to_legacy_memory(self) -> Any:
        """
        Convert to legacy HostAgentAdditionalMemory format for backward compatibility.
        :return: HostAgentAdditionalMemory instance with uppercase fields
        """
        # Import here to avoid circular imports
        try:
            from ufo.agents.processors.host_agent_processor import (
                HostAgentAdditionalMemory,
            )

            return HostAgentAdditionalMemory(
                Step=self.step,
                RoundStep=self.round_step,
                AgentStep=self.agent_step,
                Round=self.round_num,
                ControlLabel=self.control_label,
                SubtaskIndex=self.subtask_index,
                Action=self.action.copy(),
                FunctionCall=self.function_call,
                ActionType=self.action_type,
                Request=self.request,
                Agent="HostAgent",
                AgentName=self.agent_name,
                Application=self.application,
                Cost=self.cost,
                Results=self.results,
                error=self.last_error or "",
                time_cost=self.execution_times.copy(),
                ControlLog=self.control_log.copy(),
            )
        except ImportError:
            # Fallback if import fails
            return None


@dataclass
class AppAgentProcessorContext(BasicProcessorContext):
    """
    App Agent specific processor context.

    This extends the basic context with App Agent specific data including
    screenshot management, control filtering, and action execution state.
    """

    # App Agent specific data
    app_agent: Optional["AppAgent"] = None
    host_agent: Optional["HostAgent"] = None  # Reference to host agent
    grounding_service: Optional[Any] = None

    # Screenshot and image data
    image_urls: List[str] = field(default_factory=list)
    screenshot_paths: Dict[str, str] = field(default_factory=dict)
    clean_screenshot_path: Optional[str] = None
    annotated_screenshot_path: Optional[str] = None

    # Control and UI information
    filtered_controls: List[Dict[str, Any]] = field(default_factory=list)
    control_filter_strategy: str = "default"
    max_controls: int = 20

    # Subtask and plan management
    subtask: str = ""
    subtask_index: int = 0
    plan: List[str] = field(default_factory=list)
    completed_subtasks: List[str] = field(default_factory=list)

    # Action execution state
    action_history: List[Dict[str, Any]] = field(default_factory=list)
    last_action_success: bool = True
    consecutive_failures: int = 0

    # LLM and prompting
    prompt_message: Optional[Dict[str, Any]] = None
    backup_engine_used: bool = False
    llm_cost: float = 0.0

    # Application context
    app_root: str = ""
    window_info: Dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    screenshot_time: float = 0.0
    control_extraction_time: float = 0.0
    llm_response_time: float = 0.0
    action_execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert App Agent context to dictionary.
        :return: Dictionary representation including App Agent specific data
        """
        base_dict = super().to_dict()
        app_dict = {
            "app_agent": self.app_agent,
            "host_agent": self.host_agent,
            "grounding_service": self.grounding_service,
            "image_urls": self.image_urls.copy(),
            "screenshot_paths": self.screenshot_paths.copy(),
            "clean_screenshot_path": self.clean_screenshot_path,
            "annotated_screenshot_path": self.annotated_screenshot_path,
            "filtered_controls": self.filtered_controls.copy(),
            "control_filter_strategy": self.control_filter_strategy,
            "max_controls": self.max_controls,
            "subtask": self.subtask,
            "subtask_index": self.subtask_index,
            "plan": self.plan.copy(),
            "completed_subtasks": self.completed_subtasks.copy(),
            "action_history": self.action_history.copy(),
            "last_action_success": self.last_action_success,
            "consecutive_failures": self.consecutive_failures,
            "prompt_message": self.prompt_message,
            "backup_engine_used": self.backup_engine_used,
            "llm_cost": self.llm_cost,
            "app_root": self.app_root,
            "window_info": self.window_info.copy(),
            "screenshot_time": self.screenshot_time,
            "control_extraction_time": self.control_extraction_time,
            "llm_response_time": self.llm_response_time,
            "action_execution_time": self.action_execution_time,
        }
        base_dict.update(app_dict)
        return base_dict

    def get_context_summary(self) -> Dict[str, Any]:
        """
        Get App Agent context summary.
        :return: Summary with App Agent specific information
        """
        base_summary = super().get_context_summary()
        app_summary = {
            "subtask_info": f"{self.subtask_index + 1}: {self.subtask[:50]}...",
            "controls_found": len(self.filtered_controls),
            "action_history_length": len(self.action_history),
            "consecutive_failures": self.consecutive_failures,
            "app_root": self.app_root or "Unknown",
            "backup_engine_used": self.backup_engine_used,
            "total_performance_time": (
                self.screenshot_time
                + self.control_extraction_time
                + self.llm_response_time
                + self.action_execution_time
            ),
        }
        base_summary.update(app_summary)
        return app_summary


# Define processor context type - any class that implements ProcessorContextProtocol
ProcessorContextType = TypeVar("ProcessorContextType", bound=ProcessorContextProtocol)


@dataclass
class ProcessingContext:
    """
    Enhanced processing context with unified typed/dict interface.

    This version provides a cleaner interface while maintaining backward compatibility.
    The local_context provides type-safe access to processor-specific data and can be
    any class that implements ProcessorContextProtocol.
    """

    global_context: "Context"
    local_context: (
        ProcessorContextType  # Any class implementing ProcessorContextProtocol
    )
    phase_results: OrderedDict[ProcessingPhase, ProcessingResult] = field(
        default_factory=OrderedDict
    )

    def __post_init__(self):
        """Initialize after construction"""
        if self.local_context is None:
            # If no local_context provided, create a basic one
            self.local_context = BasicProcessorContext()

    # === Primary interface: Direct access to typed attributes ===
    def __getattr__(self, name: str) -> Any:
        """Direct access to local context attributes - provides type-safe attribute access"""
        if hasattr(self.local_context, name):
            return getattr(self.local_context, name)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        """Direct setting of local context attributes - provides type-safe attribute setting"""
        # Exclude framework core attributes
        if name in ["global_context", "local_context", "phase_results"]:
            super().__setattr__(name, value)
        elif hasattr(self, "local_context") and hasattr(self.local_context, name):
            setattr(self.local_context, name, value)
        elif hasattr(self, "local_context") and hasattr(
            self.local_context, "custom_data"
        ):
            # Unknown attributes stored in custom_data
            if not isinstance(self.local_context.custom_data, dict):
                self.local_context.custom_data = {}
            self.local_context.custom_data[name] = value
        else:
            # Initial attribute setting during initialization
            super().__setattr__(name, value)

    # === Backward compatibility interface ===
    def get_local(self, key: str, default: Any = None) -> Any:
        """
        Backward compatibility: Get local data
        :param key: Key to get
        :param default: Default value
        :return: Value from local context or default
        """
        # First try to get as attribute (for known fields)
        if hasattr(self.local_context, key):
            value = getattr(self.local_context, key)
            if value is not None:  # Don't return None values, check custom_data
                return value

        # Then try to get from custom_data
        if hasattr(self.local_context, "custom_data") and isinstance(
            self.local_context.custom_data, dict
        ):
            if key in self.local_context.custom_data:
                return self.local_context.custom_data[key]

        return default

    def set_local(self, key: str, value: Any) -> None:
        """
        Backward compatibility: Set local data
        :param key: Key to set
        :param value: Value to set
        """
        if hasattr(self.local_context, key):
            setattr(self.local_context, key, value)
        else:
            # Store in custom_data
            if not hasattr(self.local_context, "custom_data"):
                self.local_context.custom_data = {}
            elif not isinstance(self.local_context.custom_data, dict):
                self.local_context.custom_data = {}
            self.local_context.custom_data[key] = value

    def update_local(self, data: Dict[str, Any]) -> None:
        """
        Backward compatibility: Batch update local data
        :param data: Dictionary of data to update
        """
        for key, value in data.items():
            self.set_local(key, value)

    @property
    def local_data(self) -> Dict[str, Any]:
        """
        Backward compatibility: Provide dictionary view
        :return: Dictionary representation of local context
        """
        if hasattr(self.local_context, "to_dict"):
            return self.local_context.to_dict()
        else:
            # Fallback: if no to_dict method, return custom_data
            if hasattr(self.local_context, "custom_data"):
                return self.local_context.custom_data
            return {}

    # === Typed context convenience methods ===
    def get_typed_context(self) -> ProcessorContextType:
        """
        Get typed local context
        :return: Typed processor context object
        """
        return self.local_context

    def update_typed_context(self, **kwargs) -> None:
        """
        Update typed local context
        :param kwargs: Key-value pairs to update
        """
        if hasattr(self.local_context, "update_from_dict"):
            self.local_context.update_from_dict(kwargs)
        else:
            # Fallback: directly set attributes or use custom_data
            for key, value in kwargs.items():
                self.set_local(key, value)

    # === Global context methods ===
    def get_global(self, key: str, default: Any = None) -> Any:
        """
        Get global context value
        :param key: Key to get
        :param default: Default value
        :return: Value from global context or default
        """
        return self.global_context.get(key, default)

    def set_global(self, key: str, value: Any) -> None:
        """
        Set global context value
        :param key: Key to set
        :param value: Value to set
        """
        self.global_context.set(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value, searching local context first, then global context
        :param key: Key to get
        :param default: Default value
        :return: Found value or default
        """
        # Try to get from local context first
        try:
            local_value = self.get_local(key)
            if local_value is not None:
                return local_value
        except AttributeError:
            pass

        # Then get from global context
        return self.global_context.get(key, default)

    def promote_to_global(self, key: str) -> None:
        """
        Promote local context data to global context
        :param key: Key to promote
        """
        local_value = self.get_local(key)
        if local_value is not None:
            self.global_context.set(key, local_value)

    def promote_multiple_to_global(self, keys: List[str]) -> None:
        """
        Promote multiple local context data to global context
        :param keys: List of keys to promote
        """
        for key in keys:
            self.promote_to_global(key)

    # === Phase result management methods ===
    def set_phase_result(
        self, phase: ProcessingPhase, result: ProcessingResult
    ) -> None:
        """Store processing phase result"""
        self.phase_results[phase] = result

    def get_phase_result(self, phase: ProcessingPhase) -> Optional[ProcessingResult]:
        """Get result of specific processing phase"""
        return self.phase_results.get(phase)

    def get_all_phase_results(self) -> OrderedDict[ProcessingPhase, ProcessingResult]:
        """Get all phase results as ordered dictionary"""
        return self.phase_results.copy()

    def get_phase_results_summary(self) -> Dict[str, Any]:
        """Get summary of all phase results"""
        summary = {}
        for phase, result in self.phase_results.items():
            summary[phase.value] = {
                "success": result.success,
                "execution_time": result.execution_time,
                "data_keys": list(result.data.keys()) if result.data else [],
                "error": result.error,
            }
        return summary

    def get_phase_results_in_order(
        self,
    ) -> List[tuple[ProcessingPhase, ProcessingResult]]:
        """Get phase results as list of tuples in order they were set"""
        return list(self.phase_results.items())

    def get_phase_execution_order(self) -> List[ProcessingPhase]:
        """Get phases in execution order"""
        return list(self.phase_results.keys())

    def has_phase_completed(self, phase: ProcessingPhase) -> bool:
        """Check if specific phase has completed"""
        return phase in self.phase_results

    def get_successful_phases(self) -> List[ProcessingPhase]:
        """Get list of successfully completed phases"""
        return [phase for phase, result in self.phase_results.items() if result.success]

    def get_failed_phases(self) -> List[ProcessingPhase]:
        """Get list of failed phases"""
        return [
            phase for phase, result in self.phase_results.items() if not result.success
        ]

    def get_context_summary(self) -> Dict[str, Any]:
        """
        Get context summary for logging/debugging
        :return: Context summary dictionary
        """
        if hasattr(self.local_context, "get_context_summary"):
            return self.local_context.get_context_summary()

        # Fallback summary
        local_dict = self.local_data
        return {
            "local_context_type": type(self.local_context).__name__,
            "local_data_keys": list(local_dict.keys()),
            "phase_results_count": len(self.phase_results),
            "successful_phases": len(self.get_successful_phases()),
            "failed_phases": len(self.get_failed_phases()),
        }

    # === Legacy compatibility methods ===
    def get_typed_context_legacy(self) -> Optional[Any]:
        """
        Backward compatibility: Get typed processor context (old method)
        :return: Typed processor context or None
        """
        # If local_data still has typed_context, return it
        if hasattr(self, "local_data") and isinstance(self.local_data, dict):
            return self.local_data.get("typed_context")
        return self.local_context

    def update_typed_context_legacy(self, **kwargs) -> None:
        """
        Backward compatibility: Update typed processor context (old method)
        :param kwargs: Key-value pairs to update
        """
        if (
            hasattr(self, "local_data")
            and isinstance(self.local_data, dict)
            and "typed_context" in self.local_data
        ):
            typed_context = self.local_data["typed_context"]
            if hasattr(typed_context, "update_from_dict"):
                typed_context.update_from_dict(kwargs)
                # Sync back to local_data
                if hasattr(typed_context, "to_dict"):
                    self.local_data.update(typed_context.to_dict())
        else:
            self.update_typed_context(**kwargs)

    def add_action_to_history(self, action_info: Dict[str, Any]) -> None:
        """
        Add action to history and update success tracking.
        :param action_info: Action information to add
        """
        self.action_history.append(action_info)

        # Update success tracking
        success = action_info.get("success", True)
        self.last_action_success = success

        if success:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1

    def update_screenshot_info(
        self,
        clean_path: Optional[str] = None,
        annotated_path: Optional[str] = None,
        image_urls: Optional[List[str]] = None,
    ) -> None:
        """
        Update screenshot information.
        :param clean_path: Path to clean screenshot
        :param annotated_path: Path to annotated screenshot
        :param image_urls: List of image URLs
        """
        if clean_path:
            self.clean_screenshot_path = clean_path
        if annotated_path:
            self.annotated_screenshot_path = annotated_path
        if image_urls:
            self.image_urls = image_urls

    def update_performance_metrics(
        self,
        screenshot_time: float = 0.0,
        control_time: float = 0.0,
        llm_time: float = 0.0,
        action_time: float = 0.0,
    ) -> None:
        """
        Update performance timing metrics.
        :param screenshot_time: Time spent on screenshot capture
        :param control_time: Time spent on control extraction
        :param llm_time: Time spent on LLM interaction
        :param action_time: Time spent on action execution
        """
        self.screenshot_time += screenshot_time
        self.control_extraction_time += control_time
        self.llm_response_time += llm_time
        self.action_execution_time += action_time

    # === Enhanced type-safe field access methods ===
    def require_local(self, key: str, expected_type: type = None) -> Any:
        """
        Safely get required local data, raising exception if not found.

        :param key: Key to retrieve
        :param expected_type: Expected type for validation
        :return: Value from local context
        :raises: ProcessingException if field not found or wrong type
        """
        value = self.get_local(key)
        if value is None:
            from ufo.agents.processors2.core.processor_framework import (
                ProcessingException,
            )

            raise ProcessingException(
                f"Required field '{key}' not found in local context",
                context_data={
                    "missing_field": key,
                    "available_keys": list(self.local_data.keys()),
                },
            )

        if expected_type and not isinstance(value, expected_type):
            from ufo.agents.processors2.core.processor_framework import (
                ProcessingException,
            )

            raise ProcessingException(
                f"Field '{key}' has type {type(value).__name__} but expected {expected_type.__name__}",
                context_data={
                    "field": key,
                    "actual_type": type(value).__name__,
                    "expected_type": expected_type.__name__,
                },
            )

        return value

    def get_local_safe(
        self, key: str, expected_type: type = None, default: Any = None
    ) -> Any:
        """
        Type-safe local data access with optional type validation.

        :param key: Key to retrieve
        :param expected_type: Expected type for validation (warning only)
        :param default: Default value if key not found
        :return: Value from local context or default
        """
        value = self.get_local(key, default)

        if value is not None and expected_type and not isinstance(value, expected_type):
            # Log warning but don't raise exception
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Field '{key}' has type {type(value).__name__} but expected {expected_type.__name__}"
            )

        return value

    def validate_required_fields(self, required_fields: List[str]) -> List[str]:
        """
        Validate that all required fields are present in local context.

        :param required_fields: List of field names that must be present
        :return: List of missing field names
        """
        missing = []
        for field in required_fields:
            if self.get_local(field) is None:
                missing.append(field)
        return missing


class ProcessorContextFactory:
    """
    Factory class for creating processor contexts.

    This provides a centralized way to create processor contexts
    and ensures proper initialization based on agent type.
    """

    @staticmethod
    def create_context(
        agent: "BasicAgent", processor: Any, global_context: Any, **kwargs
    ) -> BasicProcessorContext:
        """
        Create appropriate processor context based on agent type.
        :param agent: Agent instance
        :param processor: Processor instance
        :param global_context: Global context
        :param kwargs: Additional context parameters
        :return: Appropriate processor context instance
        """
        # Initialize common data from global context
        common_data = {
            "agent": agent,
            "processor": processor,
            "session_step": global_context.get("session_step", 0),
            "round_step": global_context.get("round_step", 0),
            "round_num": global_context.get("round_num", 0),
            "request": global_context.get("request", ""),
            **kwargs,
        }

        # Create context based on agent type
        agent_type = agent.__class__.__name__

        if agent_type == "HostAgent":
            return HostAgentProcessorContext(
                host_agent=agent,
                target_registry=getattr(processor, "target_registry", None),
                command_dispatcher=global_context.command_dispatcher,
                prev_plan=global_context.get("prev_plan", []),
                previous_subtasks=global_context.get("previous_subtasks", []),
                log_path=global_context.get("log_path", ""),
                **common_data,
            )

        elif agent_type == "AppAgent":
            return AppAgentProcessorContext(
                app_agent=agent,
                host_agent=getattr(agent, "host", None),
                grounding_service=getattr(processor, "grounding_service", None),
                app_root=global_context.get("app_root", ""),
                **common_data,
            )

        else:
            # Default to basic context for unknown agent types
            return BasicProcessorContext(**common_data)

    @staticmethod
    def create_host_context(
        host_agent: "HostAgent", processor: Any, global_context: Any, **kwargs
    ) -> HostAgentProcessorContext:
        """
        Create Host Agent specific context.
        :param host_agent: Host agent instance
        :param processor: Processor instance
        :param global_context: Global context
        :param kwargs: Additional parameters
        :return: Host Agent processor context
        """
        return HostAgentProcessorContext(
            host_agent=host_agent,
            agent=host_agent,
            processor=processor,
            target_registry=getattr(processor, "target_registry", None),
            command_dispatcher=global_context.command_dispatcher,
            session_step=global_context.get("session_step", 0),
            round_step=global_context.get("round_step", 0),
            round_num=global_context.get("round_num", 0),
            request=global_context.get("request", ""),
            prev_plan=global_context.get("prev_plan", []),
            previous_subtasks=global_context.get("previous_subtasks", []),
            log_path=global_context.get("log_path", ""),
            **kwargs,
        )

    @staticmethod
    def create_app_context(
        app_agent: "AppAgent", processor: Any, global_context: Any, **kwargs
    ) -> AppAgentProcessorContext:
        """
        Create App Agent specific context.
        :param app_agent: App agent instance
        :param processor: Processor instance
        :param global_context: Global context
        :param kwargs: Additional parameters
        :return: App Agent processor context
        """
        return AppAgentProcessorContext(
            app_agent=app_agent,
            agent=app_agent,
            processor=processor,
            host_agent=getattr(app_agent, "host", None),
            grounding_service=getattr(processor, "grounding_service", None),
            session_step=global_context.get("session_step", 0),
            round_step=global_context.get("round_step", 0),
            round_num=global_context.get("round_num", 0),
            request=global_context.get("request", ""),
            app_root=global_context.get("app_root", ""),
            **kwargs,
        )
