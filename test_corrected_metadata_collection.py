#!/usr/bin/env python3
"""
Test the corrected _collect_strategy_metadata implementation.
Verify that ComposedStrategy properly uses get_dependencies() and get_provides() methods.
"""

import sys
import os
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum


# Mock the basic types and classes needed for testing
class ProcessingPhase(Enum):
    DATA_COLLECTION = "data_collection"
    LLM_INTERACTION = "llm_interaction"


@dataclass
class ProcessingResult:
    success: bool
    data: Dict[str, Any] = None
    error: str = None
    phase: ProcessingPhase = None
    execution_time: float = None
    metadata: Dict[str, Any] = None


@dataclass
class StrategyDependency:
    field_name: str
    required: bool = True
    expected_type: type = None
    description: str = None


class ProcessingContext:
    def __init__(self):
        self.data = {}

    def set(self, key: str, value: Any):
        self.data[key] = value

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def get_local(self, key: str, default=None):
        return self.data.get(key, default)


class MockLogger:
    def info(self, msg):
        print(f"INFO: {msg}")

    def debug(self, msg):
        print(f"DEBUG: {msg}")

    def warning(self, msg):
        print(f"WARNING: {msg}")

    def error(self, msg):
        print(f"ERROR: {msg}")


# Base class implementation matching the corrected version
class BaseProcessingStrategy:
    def __init__(self, name: str = None, fail_fast: bool = True):
        self.name = name or self.__class__.__name__
        self.fail_fast = fail_fast
        self.logger = MockLogger()

    def get_dependencies(self) -> List[StrategyDependency]:
        """Override this method in subclasses to declare dependencies."""
        return []

    def get_provides(self) -> List[str]:
        """Override this method in subclasses to declare outputs."""
        return []

    async def execute(self, agent, context: ProcessingContext) -> ProcessingResult:
        raise NotImplementedError("Must implement execute method")


# Corrected ComposedStrategy implementation
class ComposedStrategy(BaseProcessingStrategy):
    def __init__(
        self,
        strategies: List[BaseProcessingStrategy],
        name: str = "composed_strategy",
        fail_fast: bool = True,
        phase: ProcessingPhase = ProcessingPhase.DATA_COLLECTION,
    ) -> None:
        super().__init__(name=name, fail_fast=fail_fast)

        if not strategies:
            raise ValueError("At least one strategy must be provided")

        self.strategies = strategies
        self.execution_phase = phase

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

    def get_dependencies(self) -> List[StrategyDependency]:
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
        """Execute all component strategies in sequence."""
        import time

        try:
            start_time = time.time()
            self.logger.info(
                f"Starting composed strategy '{self.name}' with {len(self.strategies)} components"
            )

            combined_data = {}
            execution_results = []

            # Execute each strategy in sequence
            for i, strategy in enumerate(self.strategies):
                strategy_name = getattr(strategy, "name", f"strategy_{i}")
                self.logger.info(
                    f"Executing component {i+1}/{len(self.strategies)}: {strategy_name}"
                )

                try:
                    result: ProcessingResult = await strategy.execute(agent, context)
                    execution_results.append(result)

                    if result.success:
                        if result.data:
                            for key, value in result.data.items():
                                context.set(key, value)
                                combined_data[key] = value
                        self.logger.debug(
                            f"Strategy '{strategy_name}' completed successfully"
                        )
                    else:
                        error_msg = f"Strategy '{strategy_name}' failed: {result.error or 'Unknown error'}"
                        self.logger.error(error_msg)
                        if self.fail_fast:
                            return ProcessingResult(
                                success=False,
                                data=combined_data,
                                error=error_msg,
                                phase=self.execution_phase,
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

            total_time = time.time() - start_time
            successful_strategies = sum(
                1 for result in execution_results if result.success
            )
            overall_success = successful_strategies > 0

            return ProcessingResult(
                success=overall_success,
                data=combined_data,
                phase=self.execution_phase,
                execution_time=total_time,
                metadata={
                    "strategy_results": execution_results,
                    "successful_strategies": successful_strategies,
                    "total_strategies": len(self.strategies),
                },
            )

        except Exception as e:
            error_msg = f"Composed strategy '{self.name}' failed: {str(e)}"
            self.logger.error(error_msg)
            return ProcessingResult(
                success=False, error=error_msg, phase=self.execution_phase
            )


# Test strategies with proper get_dependencies() and get_provides() methods
class MockScreenshotStrategy(BaseProcessingStrategy):
    def __init__(self):
        super().__init__("mock_screenshot")

    def get_dependencies(self) -> List[StrategyDependency]:
        return []  # No dependencies

    def get_provides(self) -> List[str]:
        return ["screenshot_path", "screenshot_url"]

    async def execute(self, agent, context: ProcessingContext) -> ProcessingResult:
        self.logger.info("Capturing mock screenshot")
        return ProcessingResult(
            success=True,
            data={
                "screenshot_path": "/mock/screenshot.png",
                "screenshot_url": "data:image/png;base64,mock",
            },
            phase=ProcessingPhase.DATA_COLLECTION,
        )


class MockControlStrategy(BaseProcessingStrategy):
    def __init__(self):
        super().__init__("mock_control_info")

    def get_dependencies(self) -> List[StrategyDependency]:
        return [
            StrategyDependency(
                field_name="screenshot_path",
                required=True,
                expected_type=str,
                description="Path to screenshot for control analysis",
            )
        ]

    def get_provides(self) -> List[str]:
        return ["control_info", "filtered_controls"]

    async def execute(self, agent, context: ProcessingContext) -> ProcessingResult:
        screenshot_path = context.get("screenshot_path")
        self.logger.info(f"Processing controls with screenshot: {screenshot_path}")

        return ProcessingResult(
            success=True,
            data={
                "control_info": [{"id": "1", "type": "button", "text": "OK"}],
                "filtered_controls": [{"id": "1", "type": "button", "text": "OK"}],
            },
            phase=ProcessingPhase.DATA_COLLECTION,
        )


class MockLLMStrategy(BaseProcessingStrategy):
    def __init__(self):
        super().__init__("mock_llm_interaction")

    def get_dependencies(self) -> List[StrategyDependency]:
        return [
            StrategyDependency(
                field_name="screenshot_url",
                required=True,
                expected_type=str,
                description="Screenshot URL for LLM analysis",
            ),
            StrategyDependency(
                field_name="control_info",
                required=True,
                expected_type=list,
                description="Control information for LLM processing",
            ),
        ]

    def get_provides(self) -> List[str]:
        return ["llm_response", "action_plan"]

    async def execute(self, agent, context: ProcessingContext) -> ProcessingResult:
        self.logger.info("Mock LLM interaction")
        return ProcessingResult(
            success=True,
            data={
                "llm_response": "Click the OK button",
                "action_plan": ["click", "button", "OK"],
            },
            phase=ProcessingPhase.LLM_INTERACTION,
        )


# Test functions
async def test_dependency_collection():
    """Test that dependencies are properly collected using get_dependencies() and get_provides() methods."""
    print("\n🧪 Test: Dependency Collection via Methods")
    print("-" * 50)

    strategies = [
        MockScreenshotStrategy(),  # provides: screenshot_path, screenshot_url
        MockControlStrategy(),  # depends: screenshot_path, provides: control_info, filtered_controls
        MockLLMStrategy(),  # depends: screenshot_url, control_info, provides: llm_response, action_plan
    ]

    composed = ComposedStrategy(strategies=strategies, name="test_dependencies")

    dependencies = composed.get_dependencies()
    provides = composed.get_provides()

    print("Collected Dependencies:")
    for dep in dependencies:
        print(
            f"  - {dep.field_name} (required: {dep.required}, type: {dep.expected_type})"
        )
        print(f"    Description: {dep.description}")

    print(f"\nCollected Provides: {provides}")

    # Verify the collection
    expected_dependency_fields = {"screenshot_path", "screenshot_url", "control_info"}
    expected_provides = {
        "screenshot_path",
        "screenshot_url",
        "control_info",
        "filtered_controls",
        "llm_response",
        "action_plan",
    }

    collected_dependency_fields = {dep.field_name for dep in dependencies}
    collected_provides_set = set(provides)

    print(f"\nExpected dependency fields: {expected_dependency_fields}")
    print(f"Collected dependency fields: {collected_dependency_fields}")
    print(f"Expected provides: {expected_provides}")
    print(f"Collected provides: {collected_provides_set}")

    assert (
        collected_dependency_fields == expected_dependency_fields
    ), f"Dependencies mismatch: expected {expected_dependency_fields}, got {collected_dependency_fields}"
    assert (
        collected_provides_set == expected_provides
    ), f"Provides mismatch: expected {expected_provides}, got {collected_provides_set}"

    print("✅ Dependency collection working correctly!")


async def test_composed_execution():
    """Test that the composed strategy executes correctly."""
    print("\n🧪 Test: Composed Strategy Execution")
    print("-" * 40)

    strategies = [MockScreenshotStrategy(), MockControlStrategy(), MockLLMStrategy()]

    composed = ComposedStrategy(strategies=strategies, name="test_execution")

    context = ProcessingContext()
    agent = None  # Mock agent

    result = await composed.execute(agent, context)

    print(f"Success: {result.success}")
    print(f"Data keys: {list(result.data.keys()) if result.data else []}")
    print(f"Execution time: {result.execution_time:.3f}s")

    expected_data_keys = {
        "screenshot_path",
        "screenshot_url",
        "control_info",
        "filtered_controls",
        "llm_response",
        "action_plan",
    }
    actual_data_keys = set(result.data.keys()) if result.data else set()

    assert result.success, "Execution should succeed"
    assert (
        actual_data_keys == expected_data_keys
    ), f"Data keys mismatch: expected {expected_data_keys}, got {actual_data_keys}"

    print("✅ Composed strategy execution working correctly!")


async def run_all_tests():
    """Run all tests."""
    print("🚀 Testing Corrected ComposedStrategy Implementation")
    print("=" * 60)

    try:
        await test_dependency_collection()
        await test_composed_execution()

        print("\n" + "=" * 60)
        print("🎉 All tests passed!")
        print(
            "✅ ComposedStrategy correctly uses get_dependencies() and get_provides() methods"
        )
        print("✅ Dependency collection works with proper StrategyDependency objects")
        print("✅ Metadata is properly aggregated from component strategies")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    import asyncio

    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
