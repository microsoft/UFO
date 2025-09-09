#!/usr/bin/env python3
"""
Simple test for the generic ComposedStrategy implementation.
Tests the core functionality without importing the full UFO framework.
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
    ACTION_EXECUTION = "action_execution"
    MEMORY_UPDATE = "memory_update"


@dataclass
class ProcessingResult:
    success: bool
    data: Dict[str, Any] = None
    error: str = None
    phase: ProcessingPhase = None
    execution_time: float = None
    metadata: Dict[str, Any] = None


class ProcessingContext:
    def __init__(self):
        self.data = {}

    def set(self, key: str, value: Any):
        self.data[key] = value

    def get(self, key: str, default=None):
        return self.data.get(key, default)


class BaseProcessingStrategy:
    def __init__(self, name: str, fail_fast: bool = True):
        self.name = name
        self.fail_fast = fail_fast
        self.logger = MockLogger()

    async def execute(self, agent, context: ProcessingContext) -> ProcessingResult:
        raise NotImplementedError("Must implement execute method")

    def handle_error(
        self, error: Exception, phase: ProcessingPhase, context: ProcessingContext
    ) -> ProcessingResult:
        return ProcessingResult(success=False, error=str(error), phase=phase)


class MockLogger:
    def info(self, msg):
        print(f"INFO: {msg}")

    def debug(self, msg):
        print(f"DEBUG: {msg}")

    def warning(self, msg):
        print(f"WARNING: {msg}")

    def error(self, msg):
        print(f"ERROR: {msg}")


# Now implement our generic ComposedStrategy
class ComposedStrategy(BaseProcessingStrategy):
    """
    Generic composed strategy that can combine multiple strategies into a single execution flow.
    """

    def __init__(
        self,
        strategies: List[BaseProcessingStrategy],
        name: str = "composed_strategy",
        fail_fast: bool = True,
        phase: ProcessingPhase = ProcessingPhase.DATA_COLLECTION,
    ) -> None:
        """
        Initialize generic composed strategy.
        """
        super().__init__(name=name, fail_fast=fail_fast)

        if not strategies:
            raise ValueError("At least one strategy must be provided")

        self.strategies = strategies
        self.execution_phase = phase

        # Collect all dependencies and provides from component strategies
        self._collect_strategy_metadata()

    def _collect_strategy_metadata(self) -> None:
        """Collect dependencies and provides metadata from all component strategies."""
        all_dependencies = set()
        all_provides = set()

        for strategy in self.strategies:
            if hasattr(strategy, "_dependencies"):
                all_dependencies.update(strategy._dependencies)
            if hasattr(strategy, "_provides"):
                all_provides.update(strategy._provides)

        self._dependencies = list(all_dependencies)
        self._provides = list(all_provides)

    async def execute(self, agent, context: ProcessingContext) -> ProcessingResult:
        """Execute all component strategies in sequence."""
        try:
            import time

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
                    # Execute the strategy
                    result: ProcessingResult = await strategy.execute(agent, context)
                    execution_results.append(result)

                    if result.success:
                        # Update context with strategy results for next strategy
                        if result.data:
                            for key, value in result.data.items():
                                context.set(key, value)
                                combined_data[key] = value

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

            if not self.fail_fast:
                overall_success = successful_strategies > 0
            else:
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
                metadata={
                    "strategy_results": execution_results,
                    "successful_strategies": successful_strategies,
                    "total_strategies": len(self.strategies),
                },
            )

        except Exception as e:
            error_msg = f"Composed strategy '{self.name}' failed: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, self.execution_phase, context)


# Test strategies
class MockScreenshotStrategy(BaseProcessingStrategy):
    def __init__(self):
        super().__init__("mock_screenshot")
        self._provides = ["screenshot_path", "screenshot_url"]

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
        self._dependencies = ["screenshot_path"]
        self._provides = ["control_info", "filtered_controls"]

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


class MockFailingStrategy(BaseProcessingStrategy):
    def __init__(self):
        super().__init__("mock_failing")

    async def execute(self, agent, context: ProcessingContext) -> ProcessingResult:
        self.logger.info("This strategy will fail")
        return ProcessingResult(
            success=False,
            error="Mock failure for testing",
            phase=ProcessingPhase.DATA_COLLECTION,
        )


# Test functions
async def test_basic_composition():
    """Test basic strategy composition."""
    print("\n🧪 Test 1: Basic Composition")
    print("-" * 40)

    strategies = [MockScreenshotStrategy(), MockControlStrategy()]

    composed = ComposedStrategy(
        strategies=strategies, name="test_composition", fail_fast=True
    )

    context = ProcessingContext()
    agent = None  # Mock agent

    result = await composed.execute(agent, context)

    print(f"Success: {result.success}")
    print(f"Data keys: {list(result.data.keys()) if result.data else []}")
    print(f"Execution time: {result.execution_time:.3f}s")
    print(f"Metadata: {result.metadata}")

    assert result.success, "Basic composition should succeed"
    assert "screenshot_path" in result.data, "Should have screenshot data"
    assert "control_info" in result.data, "Should have control data"


async def test_fail_fast_mode():
    """Test fail-fast error handling."""
    print("\n🧪 Test 2: Fail-Fast Mode")
    print("-" * 40)

    strategies = [
        MockScreenshotStrategy(),
        MockFailingStrategy(),  # This will fail
        MockControlStrategy(),  # This won't run
    ]

    composed = ComposedStrategy(
        strategies=strategies, name="test_fail_fast", fail_fast=True
    )

    context = ProcessingContext()
    agent = None

    result = await composed.execute(agent, context)

    print(f"Success: {result.success}")
    print(f"Error: {result.error}")
    print(f"Data keys: {list(result.data.keys()) if result.data else []}")

    assert not result.success, "Should fail in fail-fast mode"
    assert "screenshot_path" in result.data, "Should have data from first strategy"


async def test_continue_mode():
    """Test continue-on-error mode."""
    print("\n🧪 Test 3: Continue Mode")
    print("-" * 40)

    strategies = [
        MockScreenshotStrategy(),
        MockFailingStrategy(),  # This will fail but we continue
        MockControlStrategy(),  # This should still run
    ]

    composed = ComposedStrategy(
        strategies=strategies, name="test_continue", fail_fast=False
    )

    context = ProcessingContext()
    agent = None

    result = await composed.execute(agent, context)

    print(f"Success: {result.success}")
    print(f"Data keys: {list(result.data.keys()) if result.data else []}")
    print(
        f"Successful strategies: {result.metadata['successful_strategies']}/{result.metadata['total_strategies']}"
    )

    assert result.success, "Should succeed in continue mode (partial success)"
    assert "screenshot_path" in result.data, "Should have screenshot data"
    assert (
        "control_info" in result.data
    ), "Should have control data despite middle failure"


async def test_dependency_collection():
    """Test automatic dependency collection."""
    print("\n🧪 Test 4: Dependency Collection")
    print("-" * 40)

    strategies = [
        MockScreenshotStrategy(),  # provides: screenshot_path, screenshot_url
        MockControlStrategy(),  # depends: screenshot_path, provides: control_info, filtered_controls
    ]

    composed = ComposedStrategy(strategies=strategies, name="test_dependencies")

    print(f"Dependencies: {composed._dependencies}")
    print(f"Provides: {composed._provides}")

    # Should collect all unique dependencies and provides
    expected_provides = {
        "screenshot_path",
        "screenshot_url",
        "control_info",
        "filtered_controls",
    }
    expected_dependencies = {"screenshot_path"}

    assert (
        set(composed._provides) == expected_provides
    ), f"Should collect all provides: expected {expected_provides}, got {set(composed._provides)}"
    assert (
        set(composed._dependencies) == expected_dependencies
    ), f"Should collect all dependencies: expected {expected_dependencies}, got {set(composed._dependencies)}"


async def run_all_tests():
    """Run all tests."""
    print("🚀 Testing Generic ComposedStrategy Implementation")
    print("=" * 60)

    try:
        await test_basic_composition()
        await test_fail_fast_mode()
        await test_continue_mode()
        await test_dependency_collection()

        print("\n" + "=" * 60)
        print("🎉 All tests passed!")
        print("✅ Generic ComposedStrategy works correctly")
        print("✅ Supports sequential execution")
        print("✅ Handles errors properly (fail-fast and continue modes)")
        print("✅ Collects dependencies and provides metadata")
        print("✅ Propagates context between strategies")

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
