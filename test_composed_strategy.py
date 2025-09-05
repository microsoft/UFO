#!/usr/bin/env python3
"""
Test script for ComposedAppDataCollectionStrategy integration.
This script verifies that the composed strategy properly combines screenshot
capture and control info collection.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the test modules
from ufo.agents.processors2.app_agent_processor import (
    AppAgentProcessorV2,
    AppAgentProcessorContext,
)
from ufo.agents.processors2.core.processing_context import ProcessingPhase
from ufo.agents.processors2.strategies.app_agent_processing_strategy import (
    ComposedAppDataCollectionStrategy,
)


def create_mock_agent():
    """Create a mock app agent for testing."""
    mock_agent = MagicMock()
    mock_agent.get_name.return_value = "MockAppAgent"
    mock_agent.status = "NORMAL"

    # Mock screenshot capabilities
    mock_agent.capture_screenshot.return_value = "mock_screenshot_data"

    # Mock control info capabilities
    mock_agent.get_control_info.return_value = {
        "controls": ["button1", "input1"],
        "current_window": "test_window",
    }

    # Mock memory with proper length property
    mock_memory = MagicMock()
    mock_memory.length = 0
    mock_agent.memory = mock_memory

    return mock_agent


def create_mock_global_context():
    """Create mock global context."""
    mock_context = MagicMock()
    mock_context.get.return_value = None
    return mock_context


def test_composed_strategy_integration():
    """Test that ComposedAppDataCollectionStrategy works in the processor."""
    print("Testing ComposedAppDataCollectionStrategy integration...")

    # Create mocks
    mock_agent = create_mock_agent()
    mock_global_context = create_mock_global_context()

    try:
        # Create processor
        processor = AppAgentProcessorV2(mock_agent, mock_global_context)

        # Check that the composed strategy is properly installed
        data_collection_strategy = processor.strategies.get(
            ProcessingPhase.DATA_COLLECTION
        )
        assert (
            data_collection_strategy is not None
        ), "Data collection strategy not found"
        assert isinstance(
            data_collection_strategy, ComposedAppDataCollectionStrategy
        ), f"Expected ComposedAppDataCollectionStrategy, got {type(data_collection_strategy)}"

        print("✓ ComposedAppDataCollectionStrategy is properly installed in processor")

        # Test strategy composition
        strategy = ComposedAppDataCollectionStrategy()

        # Create a test context
        context = AppAgentProcessorContext()
        context.agent = mock_agent
        context.current_phase = ProcessingPhase.DATA_COLLECTION

        # Execute the composed strategy
        result = asyncio.run(strategy.execute(mock_agent, context))

        # Verify the strategy executed successfully
        assert result.success, f"Strategy execution failed: {result.error_message}"

        # Verify both screenshot and control info were collected
        assert hasattr(
            context, "screenshot_data"
        ), "Screenshot data not found in context"
        assert hasattr(context, "control_info"), "Control info not found in context"

        print(
            "✓ ComposedAppDataCollectionStrategy successfully collects both screenshot and control info"
        )

        # Verify that the strategy contains both sub-strategies
        assert hasattr(strategy, "screenshot_strategy"), "Screenshot strategy not found"
        assert hasattr(
            strategy, "control_info_strategy"
        ), "Control info strategy not found"

        print(
            "✓ ComposedAppDataCollectionStrategy properly contains both sub-strategies"
        )

        return True

    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_strategy_error_handling():
    """Test that the composed strategy handles errors properly."""
    print("\nTesting error handling in ComposedAppDataCollectionStrategy...")

    # Create a mock agent that will fail on screenshot
    mock_agent = MagicMock()
    mock_agent.get_name.return_value = "FailingMockAgent"
    mock_agent.capture_screenshot.side_effect = Exception("Screenshot failed")
    mock_agent.get_control_info.return_value = {"controls": []}

    # Mock memory for the failing agent too
    mock_memory = MagicMock()
    mock_memory.length = 0
    mock_agent.memory = mock_memory

    try:
        strategy = ComposedAppDataCollectionStrategy(fail_fast=False)

        context = AppAgentProcessorContext()
        context.agent = mock_agent
        context.current_phase = ProcessingPhase.DATA_COLLECTION

        # Execute strategy with failure
        result = asyncio.run(strategy.execute(mock_agent, context))

        # Should handle errors gracefully when fail_fast=False
        print(
            f"Strategy result with failure: success={result.success}, error={result.error_message}"
        )

        return True

    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing ComposedAppDataCollectionStrategy Integration")
    print("=" * 60)

    all_passed = True

    # Test 1: Basic integration
    all_passed &= test_composed_strategy_integration()

    # Test 2: Error handling
    all_passed &= test_strategy_error_handling()

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All ComposedAppDataCollectionStrategy tests passed!")
    else:
        print("✗ Some tests failed!")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
