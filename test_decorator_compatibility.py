#!/usr/bin/env python3
"""
Test that our corrected ComposedStrategy can properly read decorator-registered metadata.
Verify compatibility with @depends_on and @provides decorators.
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


class MockLogger:
    def info(self, msg):
        print(f"INFO: {msg}")

    def debug(self, msg):
        print(f"DEBUG: {msg}")

    def warning(self, msg):
        print(f"WARNING: {msg}")

    def error(self, msg):
        print(f"ERROR: {msg}")


# Mock StrategyMetadataRegistry
class StrategyMetadataRegistry:
    _registry = {}

    @classmethod
    def register_strategy(cls, strategy_class, dependencies=None, provides=None):
        class_name = strategy_class.__name__
        cls._registry[class_name] = {
            "dependencies": dependencies or [],
            "provides": provides or [],
        }

    @classmethod
    def get_dependencies(cls, strategy_class):
        class_name = strategy_class.__name__
        return cls._registry.get(class_name, {}).get("dependencies", [])

    @classmethod
    def get_provides(cls, strategy_class):
        class_name = strategy_class.__name__
        return cls._registry.get(class_name, {}).get("provides", [])


# Mock the decorators
def depends_on(*dependencies: str):
    """Mock depends_on decorator that registers dependencies in metadata registry."""

    def decorator(cls):
        # Convert string dependencies to StrategyDependency objects
        dep_objects = [StrategyDependency(field_name=dep) for dep in dependencies]

        # Get existing provides if already registered
        existing_provides = StrategyMetadataRegistry.get_provides(cls)

        # Register in the metadata registry
        StrategyMetadataRegistry.register_strategy(
            cls, dependencies=dep_objects, provides=existing_provides
        )

        # Add method to class to get dependencies from registry
        def get_dependencies(self) -> List[StrategyDependency]:
            return StrategyMetadataRegistry.get_dependencies(self.__class__)

        cls.get_dependencies = get_dependencies
        return cls

    return decorator


def provides(*fields: str):
    """Mock provides decorator that registers provides in metadata registry."""

    def decorator(cls):
        # Get existing dependencies if already registered
        existing_dependencies = StrategyMetadataRegistry.get_dependencies(cls)

        # Register in the metadata registry
        StrategyMetadataRegistry.register_strategy(
            cls, dependencies=existing_dependencies, provides=list(fields)
        )

        # Add method to class to get provides from registry
        def get_provides(self) -> List[str]:
            return StrategyMetadataRegistry.get_provides(self.__class__)

        cls.get_provides = get_provides
        return cls

    return decorator


# Base strategy class
class BaseProcessingStrategy:
    def __init__(self, name: str = None, fail_fast: bool = True):
        self.name = name or self.__class__.__name__
        self.fail_fast = fail_fast
        self.logger = MockLogger()

    def get_dependencies(self) -> List[StrategyDependency]:
        """Override this method in subclasses or use decorators."""
        return []

    def get_provides(self) -> List[str]:
        """Override this method in subclasses or use decorators."""
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
        """Return the collected dependencies from all component strategies."""
        return self._collected_dependencies

    def get_provides(self) -> List[str]:
        """Return the collected provides from all component strategies."""
        return self._collected_provides

    async def execute(self, agent, context: ProcessingContext) -> ProcessingResult:
        """Execute all component strategies in sequence."""
        import time

        try:
            start_time = time.time()
            combined_data = {}

            # Execute each strategy in sequence
            for strategy in self.strategies:
                result = await strategy.execute(agent, context)
                if result.success and result.data:
                    for key, value in result.data.items():
                        context.set(key, value)
                        combined_data[key] = value

            total_time = time.time() - start_time
            return ProcessingResult(
                success=True,
                data=combined_data,
                phase=self.execution_phase,
                execution_time=total_time,
            )

        except Exception as e:
            return ProcessingResult(
                success=False, error=str(e), phase=self.execution_phase
            )


# Test strategies using decorators
@depends_on("app_root", "log_path")
@provides("screenshot_path", "screenshot_url")
class DecoratedScreenshotStrategy(BaseProcessingStrategy):
    def __init__(self):
        super().__init__("decorated_screenshot")

    async def execute(self, agent, context: ProcessingContext) -> ProcessingResult:
        return ProcessingResult(
            success=True,
            data={
                "screenshot_path": "/decorated/screenshot.png",
                "screenshot_url": "data:image/png;base64,decorated",
            },
            phase=ProcessingPhase.DATA_COLLECTION,
        )


@depends_on("screenshot_path")
@provides("control_info", "filtered_controls")
class DecoratedControlStrategy(BaseProcessingStrategy):
    def __init__(self):
        super().__init__("decorated_control_info")

    async def execute(self, agent, context: ProcessingContext) -> ProcessingResult:
        return ProcessingResult(
            success=True,
            data={
                "control_info": [{"id": "decorated", "type": "button"}],
                "filtered_controls": [{"id": "decorated", "type": "button"}],
            },
            phase=ProcessingPhase.DATA_COLLECTION,
        )


@depends_on("screenshot_url", "control_info")
@provides("llm_response", "action_plan")
class DecoratedLLMStrategy(BaseProcessingStrategy):
    def __init__(self):
        super().__init__("decorated_llm")

    async def execute(self, agent, context: ProcessingContext) -> ProcessingResult:
        return ProcessingResult(
            success=True,
            data={
                "llm_response": "Click decorated button",
                "action_plan": ["click", "decorated", "button"],
            },
            phase=ProcessingPhase.LLM_INTERACTION,
        )


# Test functions
async def test_decorator_compatibility():
    """Test that ComposedStrategy works with decorator-registered strategies."""
    print("\n🧪 Test: Decorator Compatibility")
    print("-" * 40)

    # Create instances of decorated strategies
    screenshot_strategy = DecoratedScreenshotStrategy()
    control_strategy = DecoratedControlStrategy()
    llm_strategy = DecoratedLLMStrategy()

    print("Testing individual strategy metadata:")

    # Test screenshot strategy
    screenshot_deps = screenshot_strategy.get_dependencies()
    screenshot_provides = screenshot_strategy.get_provides()
    print(f"  Screenshot Strategy:")
    print(f"    Dependencies: {[dep.field_name for dep in screenshot_deps]}")
    print(f"    Provides: {screenshot_provides}")

    # Test control strategy
    control_deps = control_strategy.get_dependencies()
    control_provides = control_strategy.get_provides()
    print(f"  Control Strategy:")
    print(f"    Dependencies: {[dep.field_name for dep in control_deps]}")
    print(f"    Provides: {control_provides}")

    # Test LLM strategy
    llm_deps = llm_strategy.get_dependencies()
    llm_provides = llm_strategy.get_provides()
    print(f"  LLM Strategy:")
    print(f"    Dependencies: {[dep.field_name for dep in llm_deps]}")
    print(f"    Provides: {llm_provides}")

    # Create composed strategy
    strategies = [screenshot_strategy, control_strategy, llm_strategy]
    composed = ComposedStrategy(strategies=strategies, name="decorated_composed")

    print(f"\nComposed Strategy Metadata:")
    composed_deps = composed.get_dependencies()
    composed_provides = composed.get_provides()
    print(f"  Dependencies: {[dep.field_name for dep in composed_deps]}")
    print(f"  Provides: {composed_provides}")

    # Verify metadata collection
    expected_dep_fields = {
        "app_root",
        "log_path",
        "screenshot_path",
        "screenshot_url",
        "control_info",
    }
    expected_provides = {
        "screenshot_path",
        "screenshot_url",
        "control_info",
        "filtered_controls",
        "llm_response",
        "action_plan",
    }

    actual_dep_fields = {dep.field_name for dep in composed_deps}
    actual_provides = set(composed_provides)

    print(f"\nVerification:")
    print(f"  Expected dependencies: {expected_dep_fields}")
    print(f"  Actual dependencies: {actual_dep_fields}")
    print(f"  Expected provides: {expected_provides}")
    print(f"  Actual provides: {actual_provides}")

    assert actual_dep_fields == expected_dep_fields, f"Dependencies mismatch"
    assert actual_provides == expected_provides, f"Provides mismatch"

    print("✅ Decorator compatibility working correctly!")


async def test_execution_with_decorators():
    """Test execution with decorator-registered strategies."""
    print("\n🧪 Test: Execution with Decorated Strategies")
    print("-" * 50)

    strategies = [
        DecoratedScreenshotStrategy(),
        DecoratedControlStrategy(),
        DecoratedLLMStrategy(),
    ]

    composed = ComposedStrategy(strategies=strategies, name="decorated_execution")

    # Set up context with initial dependencies
    context = ProcessingContext()
    context.set("app_root", "/app")
    context.set("log_path", "/logs")

    result = await composed.execute(agent=None, context=context)

    print(f"Execution result: {result.success}")
    print(f"Data keys: {list(result.data.keys()) if result.data else []}")

    expected_keys = {
        "screenshot_path",
        "screenshot_url",
        "control_info",
        "filtered_controls",
        "llm_response",
        "action_plan",
    }
    actual_keys = set(result.data.keys()) if result.data else set()

    assert result.success, "Execution should succeed"
    assert (
        actual_keys == expected_keys
    ), f"Data keys mismatch: expected {expected_keys}, got {actual_keys}"

    print("✅ Execution with decorated strategies working correctly!")


async def run_all_tests():
    """Run all tests."""
    print("🚀 Testing Decorator Compatibility with ComposedStrategy")
    print("=" * 60)

    try:
        await test_decorator_compatibility()
        await test_execution_with_decorators()

        print("\n" + "=" * 60)
        print("🎉 All tests passed!")
        print(
            "✅ ComposedStrategy correctly reads @depends_on and @provides decorators"
        )
        print("✅ Metadata collection works with decorator-registered strategies")
        print("✅ Composed strategy execution works with decorated strategies")

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
