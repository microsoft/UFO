#!/usr/bin/env python3
"""
Demonstration of the Generic ComposedStrategy usage.

This script shows how to use the new generic ComposedStrategy to create
flexible compositions of processing strategies.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ufo.agents.processors2.strategies.app_agent_processing_strategy import (
    ComposedStrategy,
    AppScreenshotCaptureStrategy,
    AppControlInfoStrategy,
    AppLLMInteractionStrategy,
    AppActionExecutionStrategy,
    AppMemoryUpdateStrategy,
    ComposedAppDataCollectionStrategy,
)
from ufo.agents.processors2.core.processing_context import ProcessingPhase


def demo_generic_composed_strategy():
    """Demonstrate creating custom composed strategies."""

    print("🔧 Generic ComposedStrategy Demo")
    print("=" * 50)

    # Example 1: Custom data collection strategy
    print("\n📋 Example 1: Custom Data Collection Strategy")
    data_collection_strategies = [
        AppScreenshotCaptureStrategy(),
        AppControlInfoStrategy(),
    ]

    custom_data_strategy = ComposedStrategy(
        strategies=data_collection_strategies,
        name="custom_data_collection",
        fail_fast=True,
        phase=ProcessingPhase.DATA_COLLECTION,
    )

    print(f"✓ Created: {custom_data_strategy.name}")
    print(f"  - Strategies: {len(custom_data_strategy.strategies)}")
    print(f"  - Dependencies: {getattr(custom_data_strategy, '_dependencies', [])}")
    print(f"  - Provides: {getattr(custom_data_strategy, '_provides', [])}")

    # Example 2: Full processing pipeline
    print("\n📋 Example 2: Full Processing Pipeline")
    full_pipeline_strategies = [
        AppScreenshotCaptureStrategy(),
        AppControlInfoStrategy(),
        AppLLMInteractionStrategy(),
        AppActionExecutionStrategy(),
        AppMemoryUpdateStrategy(),
    ]

    full_pipeline_strategy = ComposedStrategy(
        strategies=full_pipeline_strategies,
        name="full_app_pipeline",
        fail_fast=False,  # Continue even if some steps fail
        phase=ProcessingPhase.DATA_COLLECTION,  # Override as needed
    )

    print(f"✓ Created: {full_pipeline_strategy.name}")
    print(f"  - Strategies: {len(full_pipeline_strategy.strategies)}")
    print(f"  - Fail Fast: {full_pipeline_strategy.fail_fast}")

    # Example 3: Flexible LLM + Action pipeline
    print("\n📋 Example 3: LLM + Action Pipeline")
    llm_action_strategies = [AppLLMInteractionStrategy(), AppActionExecutionStrategy()]

    llm_action_strategy = ComposedStrategy(
        strategies=llm_action_strategies,
        name="llm_action_pipeline",
        fail_fast=True,
        phase=ProcessingPhase.LLM_INTERACTION,
    )

    print(f"✓ Created: {llm_action_strategy.name}")
    print(f"  - Strategies: {len(llm_action_strategy.strategies)}")

    # Example 4: Using the pre-built App Data Collection strategy
    print("\n📋 Example 4: Pre-built App Data Collection")
    app_data_strategy = ComposedAppDataCollectionStrategy(fail_fast=True)

    print(f"✓ Created: {app_data_strategy.name}")
    print(f"  - Strategies: {len(app_data_strategy.strategies)}")
    print(f"  - Built-in composition for App Agent data collection")


def demo_strategy_benefits():
    """Demonstrate the benefits of the generic approach."""

    print("\n🎯 Benefits of Generic ComposedStrategy")
    print("=" * 50)

    benefits = [
        "✅ Flexible composition: Mix any strategies",
        "✅ Configurable error handling: fail-fast or continue",
        "✅ Automatic dependency collection from components",
        "✅ Sequential execution with context propagation",
        "✅ Combined result aggregation",
        "✅ Detailed execution metadata and timing",
        "✅ Reusable for any agent type (App, Host, etc.)",
        "✅ Easy to test individual components",
    ]

    for benefit in benefits:
        print(f"  {benefit}")


def demo_usage_patterns():
    """Show common usage patterns."""

    print("\n📝 Common Usage Patterns")
    print("=" * 50)

    patterns = [
        {
            "name": "Data + LLM Pipeline",
            "strategies": ["Screenshot", "ControlInfo", "LLM"],
            "use_case": "Quick decision making without action execution",
        },
        {
            "name": "Action + Memory Pipeline",
            "strategies": ["Action", "Memory"],
            "use_case": "Execute pre-determined actions and record results",
        },
        {
            "name": "Full Agent Pipeline",
            "strategies": ["Screenshot", "ControlInfo", "LLM", "Action", "Memory"],
            "use_case": "Complete agent processing cycle",
        },
        {
            "name": "Validation Pipeline",
            "strategies": ["Screenshot", "ControlInfo"],
            "use_case": "Validate UI state without taking actions",
        },
    ]

    for i, pattern in enumerate(patterns, 1):
        print(f"\n{i}. {pattern['name']}")
        print(f"   Strategies: {' → '.join(pattern['strategies'])}")
        print(f"   Use Case: {pattern['use_case']}")


def demo_advanced_features():
    """Show advanced features of the ComposedStrategy."""

    print("\n⚡ Advanced Features")
    print("=" * 50)

    print("\n1. Error Handling Modes:")
    print("   • fail_fast=True: Stop on first error")
    print("   • fail_fast=False: Continue with partial results")

    print("\n2. Metadata Collection:")
    print("   • Execution results from each strategy")
    print("   • Success/failure counts")
    print("   • Total execution time")
    print("   • Individual strategy timing")

    print("\n3. Context Propagation:")
    print("   • Results from Strategy 1 → available to Strategy 2")
    print("   • Automatic context updates between strategies")
    print("   • Preserves original context state")

    print("\n4. Flexible Initialization:")
    print("   • Accept any list of BaseProcessingStrategy instances")
    print("   • Custom naming and phases")
    print("   • Dynamic dependency declaration")


if __name__ == "__main__":
    try:
        print("🚀 Generic ComposedStrategy Demonstration")
        print("=" * 60)

        demo_generic_composed_strategy()
        demo_strategy_benefits()
        demo_usage_patterns()
        demo_advanced_features()

        print("\n" + "=" * 60)
        print("🎉 Demo completed successfully!")
        print("The generic ComposedStrategy provides flexible strategy composition")
        print("while maintaining compatibility with the processing framework.")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
