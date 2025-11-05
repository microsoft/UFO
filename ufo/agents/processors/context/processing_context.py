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
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar
from abc import ABC, abstractmethod
from ufo.agents.processors.schemas.target import TargetRegistry
from ufo.module.context import Context, ContextNames
from ufo.module.dispatcher import BasicCommandDispatcher


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
    def to_dict(self, selective: bool) -> Dict[str, Any]:
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

    agent_type: str

    # Session and timing information
    session_step: int = 0
    round_step: int = 0
    round_num: int = 0
    cost: float = 0.0
    status: Optional[str] = None
    target_registry: TargetRegistry = field(default_factory=TargetRegistry)
    command_dispatcher: Optional[BasicCommandDispatcher] = None

    action: List[Dict[str, Any]] = field(default_factory=list)
    action_representation: str = ""
    results: str = ""
    function_call: Optional[Any] = None
    arguments: Dict[str, Any] = field(default_factory=dict)
    action_type: str = ""

    # Request and response data
    request: str = ""
    parsed_response: Optional[Any] = None

    # Performance and error tracking
    execution_times: Dict[str, float] = field(default_factory=dict)
    total_time: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    llm_cost: float = 0.0
    result: Optional[Any] = None

    # Generic data storage for extensibility
    custom_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, selective: bool = True) -> Dict[str, Any]:
        """
        Convert context to dictionary for framework compatibility.
        :return: Dictionary representation of context data
        """
        if selective:
            if self.selected_keys:
                result = {}
                for key in self.selected_keys:
                    if hasattr(self, key):
                        value = getattr(self, key)
                        result[key] = value
                return result

        return asdict(self)

    @property
    def selected_keys(self) -> List[str]:
        """
        The list of selective keys to dict.
        """

        return []

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
        return self.local_context.to_dict()

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
        # Try to find matching ContextNames enum first

        key = key.upper()

        context_name = None
        for name in ContextNames:
            if name.name == key or name.value == key:
                context_name = name
                break

        if context_name:
            # Use the enum if found
            value = self.global_context.get(context_name)
            return value if value is not None else default
        else:
            # For keys not in ContextNames, check the internal dict directly
            return self.global_context._context.get(key, default)

    def set_global(self, key: str, value: Any) -> None:
        """
        Set global context value
        :param key: Key to set
        :param value: Value to set
        """
        # Try to find matching ContextNames enum first
        context_name = None
        for name in ContextNames:
            if name.name == key or name.value == key:
                context_name = name
                break

        if context_name:
            # Use the enum if found
            self.global_context.set(context_name, value)
        else:
            # For keys not in ContextNames, set directly to the internal dict
            self.global_context._context[key] = value

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

        # Then get from global context using the proper method
        return self.get_global(key, default)

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

    # === Enhanced type-safe field access methods ===
    def require_local(self, key: str, expected_type: type = None) -> Any:
        """
        Safely get required local data, raising exception if not found.

        :param key: Key to retrieve
        :param expected_type: Expected type for validation
        :return: Value from local context
        :raises ProcessingException: If field not found or wrong type
        """
        value = self.get_local(key)
        if value is None:
            from ufo.agents.processors.core.processor_framework import (
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
            from ufo.agents.processors.core.processor_framework import (
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
