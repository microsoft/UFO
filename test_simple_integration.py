#!/usr/bin/env python3
"""
简化测试脚本，只验证ComposedAppDataCollectionStrategy是否正确集成到处理器中。
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the test modules
from ufo.agents.processors2.app_agent_processor import AppAgentProcessorV2
from ufo.agents.processors2.core.processing_context import ProcessingPhase
from ufo.agents.processors2.strategies.app_agent_processing_strategy import (
    ComposedAppDataCollectionStrategy,
)


def create_mock_agent():
    """Create a mock app agent for testing."""
    mock_agent = MagicMock()
    mock_agent.get_name.return_value = "MockAppAgent"
    mock_agent.status = "NORMAL"

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


def test_processor_integration():
    """Test that ComposedAppDataCollectionStrategy is properly integrated into the processor."""
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

        # Verify that the strategy contains both sub-strategies
        assert hasattr(
            data_collection_strategy, "screenshot_strategy"
        ), "Screenshot strategy not found"
        assert hasattr(
            data_collection_strategy, "control_info_strategy"
        ), "Control info strategy not found"

        print(
            "✓ ComposedAppDataCollectionStrategy properly contains both sub-strategies"
        )

        # Check strategy names
        assert (
            data_collection_strategy.name == "composed_app_data_collection"
        ), f"Expected strategy name 'composed_app_data_collection', got '{data_collection_strategy.name}'"

        print("✓ ComposedAppDataCollectionStrategy has correct name")

        # Check other strategies are still present
        llm_strategy = processor.strategies.get(ProcessingPhase.LLM_INTERACTION)
        action_strategy = processor.strategies.get(ProcessingPhase.ACTION_EXECUTION)
        memory_strategy = processor.strategies.get(ProcessingPhase.MEMORY_UPDATE)

        assert llm_strategy is not None, "LLM interaction strategy not found"
        assert action_strategy is not None, "Action execution strategy not found"
        assert memory_strategy is not None, "Memory update strategy not found"

        print("✓ All other strategies are properly installed")

        return True

    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing ComposedAppDataCollectionStrategy Processor Integration")
    print("=" * 60)

    # Test integration
    success = test_processor_integration()

    print("\n" + "=" * 60)
    if success:
        print("✓ ComposedAppDataCollectionStrategy integration test passed!")
        print("\n重构总结:")
        print("- AppAgentProcessorV2 现在使用 ComposedAppDataCollectionStrategy")
        print("- 这个组合策略整合了截图捕获和控制信息收集")
        print("- 遵循了框架要求的每个阶段一个策略的原则")
        print("- 内存更新逻辑已经完全分离，避免了重复")
    else:
        print("✗ Integration test failed!")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
