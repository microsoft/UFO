import logging
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ufo.agents.agent.basic import BasicAgent
from ufo.module.context import Context
from ufo.agents.processors2.core.processing_context import (
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
)

from ufo.agents.processors2.middleware.processing_middleware import ProcessorMiddleware
from ufo.agents.processors2.strategies.processing_strategy import ProcessingStrategy
from ufo.agents.processors2.core.strategy_dependency import (
    StrategyDependency,
    StrategyDependencyValidator,
    DependencyValidationResult,
    validate_provides_consistency,
)

T = TypeVar("T")


class ProcessingException(Exception):
    """
    Exception raised during processing that contains additional context.
    """

    def __init__(
        self,
        message: str,
        phase: Optional[ProcessingPhase] = None,
        context_data: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.phase = phase
        self.context_data = context_data or {}
        self.original_exception = original_exception


class ProcessorTemplate(ABC):
    """
    Processor template base class - defines the processing workflow.
    """

    def __init__(self, agent: BasicAgent, global_context: Context):
        """
        Initialize the processor template.
        :param agent: The agent instance which this processor serves.
        :param context: The global context.
        """
        self.agent = agent
        self.global_context = global_context  # Shared global context
        self.strategies: Dict[ProcessingPhase, ProcessingStrategy] = {}
        self.middleware_chain: List[ProcessorMiddleware] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self._exceptions: List[Dict[str, Any]] = []

        # Initialize dependency validator
        self.dependency_validator = StrategyDependencyValidator()

        self._setup_strategies()
        self._setup_middleware()

        self.processing_context = self._create_processing_context()

        # Validate strategy chain after setup
        self._validate_strategy_chain()

    @abstractmethod
    def _setup_strategies(self) -> None:
        """
        Set up processing strategies.
        """
        pass

    @abstractmethod
    def _setup_middleware(self) -> None:
        """
        Set up middleware.
        """
        pass

    @abstractmethod
    def _create_memory_item(self) -> None:
        """
        Create a memory item for this processor.
        """
        pass

    def _create_processing_context(self) -> ProcessingContext:
        """
        Create a processing context for this execution.
        Uses the new unified type-safe context system.
        """
        # Import here to avoid circular imports
        try:
            from ufo.agents.processors2.core.processing_context import (
                ProcessorContextFactory,
            )

            # Create typed processor context using factory
            local_context = ProcessorContextFactory.create_context(
                agent=self.agent, processor=self, global_context=self.global_context
            )

            # Create ProcessingContext with unified type-safe local_context
            return ProcessingContext(
                global_context=self.global_context, local_context=local_context
            )

        except ImportError:
            # Fallback to basic context if factory not available
            self.logger.warning("Context factory not available, using basic context")
            from ufo.agents.processors2.core.processing_context import (
                BasicProcessorContext,
            )

            basic_context = BasicProcessorContext()
            # Initialize with fallback data

            return ProcessingContext(
                global_context=self.global_context, local_context=basic_context
            )

    def _finalize_processing_context(
        self, processing_context: ProcessingContext
    ) -> None:
        """
        Finalize processing context, deciding what to promote to global context.
        Can be overridden by subclasses.
        :param processing_context: The processing context to finalize.
        """
        # Promote keys from local context to global context
        keys_to_promote = self._get_keys_to_promote()
        processing_context.promote_multiple_to_global(keys_to_promote)

    def _get_keys_to_promote(self) -> List[str]:
        """
        Get keys that should be promoted to global context.
        Can be overridden by subclasses.
        :return: A list of keys to promote.
        """
        # This method can be overridden by subclasses to customize the keys to promote
        return []

    def _validate_strategy_chain(self) -> None:
        """
        Validate the entire strategy chain for dependency consistency.
        This runs at initialization to catch configuration errors early.
        """
        try:
            # Create a list of strategies in execution order
            strategy_list = []
            for phase in ProcessingPhase:
                if phase in self.strategies:
                    strategy_list.append(self.strategies[phase])

            # Validate the chain
            validation_result = self.dependency_validator.validate_strategy_chain(
                strategy_list
            )

            if not validation_result.is_valid:
                self.logger.error(
                    f"Strategy chain validation failed: {validation_result.report}"
                )
                # Log detailed errors
                for error in validation_result.errors:
                    self.logger.error(f"  - {error}")

                # You can choose to raise an exception or just log warnings
                # For now, we'll log as warnings to allow flexibility
                for error in validation_result.errors:
                    self.logger.warning(f"Strategy dependency issue: {error}")
            else:
                self.logger.info("Strategy chain validation passed")

        except Exception as e:
            self.logger.error(f"Error during strategy chain validation: {e}")

    def _validate_strategy_dependencies_runtime(
        self, strategy, processing_context: ProcessingContext
    ) -> None:
        """
        Validate strategy dependencies at runtime before execution.

        :param strategy: Strategy to validate
        :param processing_context: Current processing context
        :raises: ProcessingException if dependencies not satisfied
        """
        try:
            # Get strategy dependencies
            dependencies = getattr(strategy, "get_dependencies", lambda: [])()
            if not dependencies:
                return  # No dependencies to validate

            # Validate runtime dependencies
            validation_result = self.dependency_validator.validate_runtime_dependencies(
                dependencies, processing_context
            )

            if not validation_result.is_valid:
                missing_deps = [
                    dep.field_name
                    for dep in dependencies
                    if processing_context.get_local(dep.field_name) is None
                ]

                raise ProcessingException(
                    f"Strategy {strategy.name} dependencies not satisfied",
                    context_data={
                        "strategy": strategy.name,
                        "missing_dependencies": missing_deps,
                        "validation_errors": validation_result.errors,
                    },
                )

        except AttributeError:
            # Strategy doesn't have dependency declarations
            self.logger.debug(
                f"Strategy {strategy.name} has no dependency declarations"
            )
        except Exception as e:
            self.logger.error(
                f"Runtime dependency validation error for {strategy.name}: {e}"
            )

    async def process(self) -> ProcessingResult:
        """
        A template method that defines the processing workflow.
        Process the input data through the defined strategies and middleware.
        """
        start_time = time.time()

        try:
            # Execute pre-processing middleware
            for middleware in self.middleware_chain:
                self.logger.info(
                    f"Executing middleware before_process: {middleware.name}"
                )
                await middleware.before_process(self, self.processing_context)

            # Execute each phase processing
            combined_result = ProcessingResult(success=True, data={})

            for phase in ProcessingPhase:
                if phase in self.strategies:
                    phase_start = time.time()

                    strategy = self.strategies[phase]

                    self.logger.info(
                        f"Starting phase: {phase.value}, with strategy: {strategy.name}"
                    )

                    # Validate strategy dependencies at runtime
                    self._validate_strategy_dependencies_runtime(
                        strategy, self.processing_context
                    )

                    result = await strategy.execute(self.processing_context)
                    result.execution_time = time.time() - phase_start
                    result.phase = phase

                    # Validate provides consistency after execution
                    try:
                        validation_errors = validate_provides_consistency(
                            strategy, self.processing_context.local_context
                        )
                        if validation_errors:
                            # Report as warning (configurable to error if needed)
                            warning_msg = f"Strategy {strategy.name} provides consistency errors: {validation_errors}"
                            self.logger.warning(warning_msg)
                            # Could be configured to raise error instead based on configuration:
                            # if getattr(self, 'strict_provides_validation', False):
                            #     raise ProcessingException(warning_msg, phase=phase)
                    except Exception as consistency_error:
                        self.logger.error(
                            f"Error during provides consistency check for {strategy.name}: {consistency_error}"
                        )

                    # Store the phase result in context
                    self.processing_context.set_phase_result(phase, result)

                    if not result.success:
                        # If the strategy returns a failed result, create an exception and trigger the on_error middleware
                        strategy_error = Exception(
                            f"Strategy {strategy.name} failed: {result.error}"
                        )

                        # Execute error handling middleware
                        for middleware in self.middleware_chain:
                            self.logger.info(
                                f"Executing middleware on_error for strategy failure: {middleware.name}"
                            )
                            await middleware.on_error(self, strategy_error)

                        break

                    # Merge strategy results into local context for the next strategy
                    self.processing_context.update_local(result.data)

            combined_result.execution_time = time.time() - start_time

            # Add phase results to the final result
            combined_result.data["phase_results"] = (
                self.processing_context.get_all_phase_results()
            )
            combined_result.data["phase_results_summary"] = (
                self.processing_context.get_phase_results_summary()
            )

            # Decide what data needs to be promoted to global context
            self._finalize_processing_context(self.processing_context)

            # Execute post-processing middleware
            for middleware in reversed(self.middleware_chain):
                self.logger.info(
                    f"Executing middleware after_process: {middleware.name}"
                )
                await middleware.after_process(self, combined_result)

            return combined_result

        except Exception as e:
            error_result = ProcessingResult(
                success=False,
                error=str(e),
                data={},
                execution_time=time.time() - start_time,
            )

            self.logger.error(f"Processing failed: {error_result.error}")

            # If the error is a ProcessingException, extract more context
            if isinstance(e, ProcessingException):
                error_result.phase = e.phase
                error_result.data = e.context_data
                self.logger.error(
                    f"Processing failed at phase: {e.phase}, context: {e.context_data}"
                )

            # Execute error handling middleware
            for middleware in self.middleware_chain:
                self.logger.info(f"Executing middleware on_error: {middleware.name}")
                await middleware.on_error(self, e)

            return error_result
