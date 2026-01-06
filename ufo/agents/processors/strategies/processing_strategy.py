import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Protocol, TYPE_CHECKING
import time
from ufo.agents.processors.core.processor_framework import (
    ProcessingContext,
    ProcessingPhase,
    ProcessingResult,
)


if TYPE_CHECKING:
    from ufo.agents.processors.core.strategy_dependency import StrategyDependency
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
        :raises ProcessingException: If dependency not found or wrong type
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
            from ufo.agents.processors.core.processor_framework import (
                ProcessingException,
            )

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


class ComposedStrategy(BaseProcessingStrategy):
    """
    Generic composed strategy that can combine multiple strategies into a single execution flow.

    This strategy allows for flexible composition of multiple processing strategies while
    maintaining the framework requirement of one strategy per processing phase. It executes
    strategies sequentially and combines their results.

    Features:
    - Sequential execution of multiple strategies
    - Context data propagation between strategies
    - Combined result aggregation
    - Flexible error handling (fail-fast or continue)
    - Dynamic dependency and provides declaration
    """

    def __init__(
        self,
        strategies: List[BaseProcessingStrategy],
        name: str = "",
        fail_fast: bool = True,
        phase: ProcessingPhase = ProcessingPhase.DATA_COLLECTION,
    ) -> None:
        """
        Initialize generic composed strategy.

        :param strategies: List of strategies to execute in sequence
        :param name: Name of the composed strategy
        :param fail_fast: Whether to stop on first error or continue with partial results
        :param phase: Processing phase for this composed strategy
        """
        super().__init__(name=name, fail_fast=fail_fast)

        if not strategies:
            raise ValueError("At least one strategy must be provided")

        self.strategies = strategies
        self.execution_phase = phase

        if not self.name:
            self.name = "ComposedStrategy_" + "_".join([s.name for s in strategies])

        # Collect all dependencies and provides from component strategies
        self._collect_strategy_metadata()

    def _collect_strategy_metadata(self) -> None:
        """
        Collect dependencies and provides metadata from all component strategies.
        This allows the composed strategy to declare its full interface.
        """
        all_dependencies = []
        all_provides = set()

        for strategy in self.strategies:
            # Get dependencies using the proper method
            strategy_dependencies = strategy.get_dependencies()
            all_dependencies.extend(strategy_dependencies)

            # Get provides using the proper method
            strategy_provides = strategy.get_provides()
            all_provides.update(strategy_provides)

        # Store collected metadata for the composed strategy
        self._collected_dependencies = all_dependencies
        self._collected_provides = list(all_provides)

    def get_dependencies(self) -> List["StrategyDependency"]:
        """
        Return the collected dependencies from all component strategies.

        :return: List of all dependencies from component strategies
        """
        return self._collected_dependencies

    def get_provides(self) -> List[str]:
        """
        Return the collected provides from all component strategies.

        :return: List of all field names provided by component strategies
        """
        return self._collected_provides

    async def execute(self, agent, context: ProcessingContext) -> ProcessingResult:
        """
        Execute all component strategies in sequence.

        :param agent: The agent instance (can be AppAgent, HostAgent, etc.)
        :param context: Processing context
        :return: ProcessingResult with combined data from all strategies
        """
        try:
            start_time = time.time()
            self.logger.info(
                f"Starting composed strategy '{self.name}' with {len(self.strategies)} components"
            )

            combined_data = {}
            execution_results = []

            # Execute each strategy in sequence
            for i, strategy in enumerate(self.strategies):
                strategy_name = strategy.name

                self.logger.info(
                    f"Executing component {i+1}/{len(self.strategies)}: {strategy_name}"
                )

                try:
                    # Execute the strategy
                    result: ProcessingResult = await strategy.execute(agent, context)
                    execution_results.append(result)

                    if result.success:
                        # Update context with strategy results for next strategy
                        if result.data:
                            context.update_local(result.data)

                        self.logger.debug(
                            f"Strategy '{strategy_name}' completed successfully"
                        )
                    else:
                        # Handle strategy failure
                        error_msg = f"Strategy '{strategy_name}' failed: {result.error or 'Unknown error'}"
                        self.logger.error(error_msg)

                        if self.fail_fast:
                            return ProcessingResult(
                                success=False,
                                data=combined_data,
                                error=error_msg,
                                phase=self.execution_phase,
                            )
                        else:
                            # Continue with next strategy, log warning
                            self.logger.warning(
                                f"Continuing with remaining strategies despite failure in '{strategy_name}'"
                            )

                except Exception as e:
                    error_msg = f"Strategy '{strategy_name}' raised exception: {str(e)}"
                    self.logger.error(error_msg)

                    if self.fail_fast:
                        return ProcessingResult(
                            success=False,
                            data=combined_data,
                            error=error_msg,
                            phase=self.execution_phase,
                        )
                    else:
                        self.logger.warning(
                            f"Continuing with remaining strategies despite exception in '{strategy_name}'"
                        )

            # Calculate total execution time
            total_time = time.time() - start_time

            # Determine overall success
            successful_strategies = sum(
                1 for result in execution_results if result.success
            )
            overall_success = (
                successful_strategies > 0
            )  # At least one strategy succeeded

            if not self.fail_fast:
                # In non-fail-fast mode, success if any strategy succeeded
                overall_success = successful_strategies > 0
            else:
                # In fail-fast mode, success if all strategies succeeded
                overall_success = successful_strategies == len(self.strategies)

            self.logger.info(
                f"Composed strategy '{self.name}' completed: {successful_strategies}/{len(self.strategies)} "
                f"strategies succeeded in {total_time:.2f}s"
            )

            return ProcessingResult(
                success=overall_success,
                data=combined_data,
                phase=self.execution_phase,
                execution_time=total_time,
            )

        except Exception as e:
            error_msg = f"Composed strategy '{self.name}' failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, self.execution_phase, context)
