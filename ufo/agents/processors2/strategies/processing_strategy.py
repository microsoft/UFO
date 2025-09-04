import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Protocol, TYPE_CHECKING

from ufo.agents.processors2.core.processing_context import (
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
)

if TYPE_CHECKING:
    from ufo.agents.processors2.core.processor_framework import ProcessingException
    from ufo.agents.processors2.core.strategy_dependency import StrategyDependency
    from ufo.agents.agent.basic import BasicAgent


class ProcessingStrategy(Protocol):
    """
    Protocol for processing strategies.
    """

    name: str  # Strategy name for logging and identification

    async def execute(
        self, agent: "BasicAgent", context: ProcessingContext
    ) -> ProcessingResult: ...


class BaseProcessingStrategy(ABC):
    """
    Base class for processing strategies.
    """

    def __init__(self, name: Optional[str] = None, fail_fast: bool = True):
        """
        Initialize the processing strategy.
        :param name: Optional custom name for the strategy. If not provided, uses class name.
        :param fail_fast: Whether to raise exceptions immediately or return failed results.
        """
        self.name = name or self.__class__.__name__
        self.fail_fast = fail_fast
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.name}")

    def get_dependencies(self) -> List["StrategyDependency"]:
        """
        Declare dependencies that this strategy requires.
        Override this method in subclasses to declare dependencies.

        :return: List of strategy dependencies
        """
        return []

    def get_provides(self) -> List[str]:
        """
        Declare what fields this strategy provides to subsequent strategies.
        Override this method in subclasses to declare outputs.

        :return: List of field names this strategy provides
        """
        return []

    def validate_dependencies(self, context: ProcessingContext) -> List[str]:
        """
        Validate that all dependencies are satisfied in the context.

        :param context: Processing context to validate against
        :return: List of missing dependency field names
        """
        missing = []
        for dependency in self.get_dependencies():
            value = context.get_local(dependency.field_name)
            if dependency.required and value is None:
                missing.append(dependency.field_name)
            elif value is not None and dependency.expected_type:
                if not isinstance(value, dependency.expected_type):
                    self.logger.warning(
                        f"Dependency '{dependency.field_name}' has type {type(value).__name__} "
                        f"but expected {dependency.expected_type.__name__}"
                    )
        return missing

    def require_dependency(
        self, context: ProcessingContext, field_name: str, expected_type: type = None
    ):
        """
        Safely get a required dependency from context.

        :param context: Processing context
        :param field_name: Name of the field to retrieve
        :param expected_type: Expected type for validation
        :return: The required value
        :raises: ProcessingException if dependency not found or wrong type
        """
        return context.require_local(field_name, expected_type)

    @abstractmethod
    async def execute(
        self, agent: "BasicAgent", context: ProcessingContext
    ) -> ProcessingResult:
        """
        Execute the processing strategy.
        :param agent: The agent instance that owns this processor.
        :param context: The processing context with both global and local data.
        :return: The processing result.
        """
        pass

    def handle_error(
        self, error: Exception, phase: ProcessingPhase, context: ProcessingContext
    ) -> ProcessingResult:
        """
        Handle errors in a consistent way.
        :param error: The exception that occurred.
        :param phase: The processing phase where the error occurred.
        :param context: The processing context.
        :return: Either raises an exception or returns a failed result.
        """
        error_message = f"{self.__class__.__name__} failed: {str(error)}"

        if self.fail_fast:
            # Throw ProcessingException to trigger middleware's on_error
            raise ProcessingException(
                message=error_message,
                phase=phase,
                context_data={"strategy_name": self.name},
                original_exception=error,
            )
        else:
            # Return failed result without triggering on_error middleware
            self.logger.error(error_message)
            return ProcessingResult(
                success=False, error=error_message, data={}, phase=phase
            )
