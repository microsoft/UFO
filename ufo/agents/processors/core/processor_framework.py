import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar

from ufo.agents.processors.context.processing_context import (
    BasicProcessorContext,
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
)
from ufo.agents.processors.core.strategy_dependency import (
    StrategyDependencyValidator,
    StrategyMetadataRegistry,
    validate_provides_consistency,
)
from ufo.agents.processors.strategies.processing_strategy import ProcessingStrategy
from ufo.module.context import Context, ContextNames

if TYPE_CHECKING:
    from ufo.agents.agent.basic import BasicAgent
    from ufo.agents.processors.core.processing_middleware import ProcessorMiddleware

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

    Subclasses can override the processor_context_class to use their own
    ProcessorContext type for enhanced type safety and functionality.
    """

    # Class attribute that subclasses can override to specify their context class
    processor_context_class: Type[BasicProcessorContext] = BasicProcessorContext

    def __init__(self, agent: "BasicAgent", global_context: Context):
        """
        Initialize the processor template.
        :param agent: The agent instance which this processor serves.
        :param global_context: The global context.
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

    def _create_processing_context(self) -> ProcessingContext:
        """
        Create a processing context for this execution.
        Uses the unified type-safe context system with configurable context class.

        Subclasses can override processor_context_class or this method entirely
        for complete customization.
        """
        # Get the context class to use (allows subclass override)
        context_class = self.get_processor_context_class()

        # Create local context instance with common initialization
        local_context = self._create_local_context(context_class)

        # Create ProcessingContext with the initialized local context
        return ProcessingContext(
            global_context=self.global_context, local_context=local_context
        )

    def get_processor_context_class(self) -> Type[BasicProcessorContext]:
        """
        Get the processor context class to use for this processor.

        This method allows subclasses to dynamically determine the context class,
        or they can simply override the processor_context_class class attribute.

        :return: The processor context class to instantiate
        """
        return self.processor_context_class

    def _create_local_context(
        self, context_class: Type[BasicProcessorContext]
    ) -> BasicProcessorContext:
        """
        Create and initialize the local context instance.

        This method handles the common initialization logic and can be overridden
        by subclasses that need special initialization behavior.

        :param context_class: The context class to instantiate
        :return: Initialized local context instance
        """
        # Common initialization data that most processors need
        common_data = self._get_common_context_data()

        # Get processor-specific initialization data
        processor_data = self._get_processor_specific_context_data()

        # Combine data and create context instance
        context_data = {**common_data, **processor_data}

        # Try to create the context with the available data
        try:
            return context_class(**context_data)
        except TypeError as e:
            # If the context class doesn't accept some parameters, try with just common data
            self.logger.warning(
                f"Failed to initialize {context_class.__name__} with full data: {e}"
            )
            self.logger.info("Falling back to basic initialization")
            try:
                return context_class(**common_data)
            except TypeError:
                # Final fallback: create with no parameters and set attributes manually
                instance = context_class()
                for key, value in context_data.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                return instance

    def _get_common_context_data(self) -> Dict[str, Any]:
        """
        Get common context data that most processors need.

        :return: Dictionary of common context initialization data
        """

        return {
            "command_dispatcher": self.global_context.command_dispatcher,
            "agent_name": self.agent.name,
            "session_step": self.global_context.get(ContextNames.SESSION_STEP),
            "round_step": self.global_context.get(ContextNames.CURRENT_ROUND_STEP),
            "round_num": self.global_context.get(ContextNames.CURRENT_ROUND_ID),
            "request": self.global_context.get(ContextNames.REQUEST),
            "log_path": self.global_context.get(ContextNames.LOG_PATH),
        }

    def _get_processor_specific_context_data(self) -> Dict[str, Any]:
        """
        Get processor-specific context data.

        Subclasses can override this method to provide additional local context data
        specific to their processor type.

        :return: Dictionary of processor-specific context initialization data
        """
        return {}

    def _finalize_processing_context(
        self, processing_context: ProcessingContext
    ) -> None:
        """
        Finalize processing context, deciding what to promote to global context.
        Can be overridden by subclasses.
        :param processing_context: The processing context to finalize.
        """
        try:

            # Accumulate LLM cost to CURRENT_ROUND_COST
            llm_cost = processing_context.get_local("llm_cost")
            if llm_cost and isinstance(llm_cost, (int, float)):
                current_cost = (
                    self.global_context.get(ContextNames.CURRENT_ROUND_COST) or 0
                )
                self.global_context.set(
                    ContextNames.CURRENT_ROUND_COST, current_cost + llm_cost
                )

            # Accumulate to SESSION_COST as well
            if llm_cost and isinstance(llm_cost, (int, float)):
                session_cost = self.global_context.get(ContextNames.SESSION_COST) or 0
                self.global_context.set(
                    ContextNames.SESSION_COST, session_cost + llm_cost
                )

            # Update CURRENT_ROUND_STEP
            current_round_step = (
                self.global_context.get(ContextNames.CURRENT_ROUND_STEP) or 0
            )
            self.global_context.set(
                ContextNames.CURRENT_ROUND_STEP, current_round_step + 1
            )

            # Update CURRENT_SESSION_STEP
            session_step = self.global_context.get(ContextNames.SESSION_STEP) or 0
            self.global_context.set(ContextNames.SESSION_STEP, session_step + 1)

            self.logger.debug(
                "Successfully updated ContextNames from processing results"
            )

        except Exception as e:
            self.logger.warning(f"Failed to update ContextNames from results: {e}")

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

                for error in validation_result.errors:
                    self.logger.warning(f"Strategy dependency issue: {error}")
            else:
                self.logger.info("Strategy chain validation passed")

        except Exception as e:
            self.logger.error(f"Error during strategy chain validation: {e}")

    def _validate_strategy_dependencies_runtime(
        self, strategy: ProcessingStrategy, processing_context: ProcessingContext
    ) -> None:
        """
        Validate strategy dependencies at runtime before execution.

        :param strategy: Strategy to validate
        :param processing_context: Current processing context
        :raises: ProcessingException if dependencies not satisfied
        """
        try:
            # Get strategy dependencies from metadata registry
            dependencies = StrategyMetadataRegistry.get_dependencies(strategy.__class__)
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
            self.logger.warning(
                f"Runtime dependency validation error for {strategy.name}: {e}"
            )

    def _validate_strategy_provides_runtime(
        self, strategy: ProcessingStrategy, result: ProcessingResult
    ) -> None:
        """
        Validate strategy provides at runtime.
        :param strategy: Strategy to validate
        :param result: Processing result from strategy execution
        """
        try:
            declared_provides = StrategyMetadataRegistry.get_provides(
                strategy.__class__
            )
            actual_provides = list(result.data.keys()) if result.data else []
            validate_provides_consistency(
                strategy.name,
                declared_provides,
                actual_provides,
                self.logger,
            )
        except Exception as consistency_error:
            self.logger.error(
                f"Error during provides consistency check for {strategy.name}: {consistency_error}"
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

                    result = await strategy.execute(self.agent, self.processing_context)
                    result.execution_time = time.time() - phase_start
                    result.phase = phase

                    # Validate provides consistency after execution
                    self._validate_strategy_provides_runtime(strategy, result)

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
