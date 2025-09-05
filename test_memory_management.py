#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify AppAgentProcessorV2 with updated memory management.
Now AppMemoryUpdateStrategy handles all memory updates, while AppMemorySyncMiddleware
only handles state monitoring and validation.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ufo.agents.processors2.app_agent_processor import (
    AppAgentProcessorV2,
    AppAgentProcessorContext,
)
from ufo.module.context import Context


class MockAppAgent:
    """Mock AppAgent for testing."""

    def __init__(self):
        self.name = "TestAppAgent"
        self.app_root = "MockAppRoot"
        self.step = 1
        self.memory = MockMemory()
        self.blackboard = MockBlackboard()

    def get_response(self, prompt):
        return "Mock LLM response"

    def message_constructor(self, context):
        return {"message": "test prompt"}

    def response_to_dict(self, response):
        return {"status": "CONTINUE", "function": "test_function"}


class MockMemory:
    """Mock memory for testing."""

    def __init__(self):
        self.length = 5
        self._items = []

    def get_latest_k_memories(self, k):
        return self._items[-k:] if self._items else []

    def get_latest_item(self):
        """Mock method for get_latest_item."""
        return MockMemoryItem()

    def get_latest_memory(self, limit=5):
        """Mock method for get_latest_memory."""
        return self._items[-limit:] if self._items else []

    def add_memory_item(self, item):
        """Mock method to add memory item."""
        self._items.append(item)
        self.length = len(self._items)
        print(f"✓ Added memory item: {item.get('session_step', 'unknown')}")

    def __len__(self):
        return self.length


class MockMemoryItem:
    """Mock memory item."""

    def to_dict(self):
        return {
            "plan": ["step1", "step2"],
            "subtask": "test subtask",
            "observation": "test observation",
        }


class MockBlackboard:
    """Mock blackboard for testing."""

    def __init__(self):
        self.screenshots = []
        self.trajectories = []

    def is_empty(self):
        return len(self.screenshots) == 0 and len(self.trajectories) == 0

    def add_trajectories(self, trajectory):
        """Mock method to add trajectory."""
        self.trajectories.append(trajectory)
        print(f"✓ Added trajectory: {trajectory.get('function', 'unknown')}")

    def add_screenshot(self, path, description=""):
        """Mock method to add screenshot."""
        self.screenshots.append({"path": path, "description": description})
        print(f"✓ Added screenshot: {path}")


async def test_memory_update_strategy():
    """Test that memory updates are handled by AppMemoryUpdateStrategy."""

    print("Testing AppMemoryUpdateStrategy memory update functionality...")

    try:
        # Create mock agent and global context
        mock_agent = MockAppAgent()
        global_context = Context()

        # Create processor
        processor = AppAgentProcessorV2(mock_agent, global_context)

        # Create processing context with test data
        context = processor._create_processing_context()

        # Set test data in context
        context.local_context.session_step = 10
        context.local_context.round_step = 2
        context.local_context.round_num = 1
        context.local_context.subtask = "Test memory update"
        context.local_context.request = "Test request"
        context.local_context.function_name = "test_function"
        context.local_context.action_success = True
        context.local_context.llm_cost = 0.05
        context.local_context.execution_result = [{"status": "success"}]

        # Get the memory update strategy
        from ufo.agents.processors2.core.processing_context import ProcessingPhase

        memory_strategy = processor.strategies[ProcessingPhase.MEMORY_UPDATE]

        print("1. Testing memory update strategy execution...")

        # Execute the memory update strategy
        result = await memory_strategy.execute(mock_agent, context)

        assert result.success, f"Memory update should succeed: {result.error}"
        assert result.phase == ProcessingPhase.MEMORY_UPDATE

        # Check that memory was updated
        assert result.data["updated_agent_memory"], "Agent memory should be updated"
        assert result.data["updated_blackboard"], "Blackboard should be updated"

        # Verify memory stats
        memory_stats = result.data["memory_stats"]
        assert memory_stats["agent_memory_count"] > 0, "Agent memory should have items"
        assert not memory_stats["blackboard_empty"], "Blackboard should not be empty"

        print("✓ Memory update strategy executed successfully")
        print(f"✓ Agent memory count: {memory_stats['agent_memory_count']}")
        print(f"✓ Blackboard empty: {memory_stats['blackboard_empty']}")
        print(
            f"✓ Blackboard trajectories: {memory_stats['blackboard_trajectory_count']}"
        )

        return True

    except Exception as e:
        print(f"\n❌ Memory update strategy test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_memory_sync_middleware():
    """Test that memory sync middleware only monitors without duplicating updates."""

    print("\n2. Testing AppMemorySyncMiddleware monitoring functionality...")

    try:
        # Create mock agent and global context
        mock_agent = MockAppAgent()
        global_context = Context()

        # Add some initial memory items
        mock_agent.memory.add_memory_item({"step": 1, "function": "initial_function"})
        mock_agent.blackboard.add_trajectories({"step": 1, "action": "initial_action"})

        # Create processor
        processor = AppAgentProcessorV2(mock_agent, global_context)

        # Create processing context
        context = processor._create_processing_context()

        # Get memory sync middleware
        memory_middleware = None
        for middleware in processor.middleware_chain:
            if middleware.name == "app_memory_sync":
                memory_middleware = middleware
                break

        assert (
            memory_middleware is not None
        ), "AppMemorySyncMiddleware should be available"

        # Test before_process (should sync state to context)
        await memory_middleware.before_process(processor, context)

        # Check that context was updated with memory state
        assert hasattr(context.local_context, "app_memory_sync_active")
        assert context.local_context.app_memory_sync_active

        # Simulate processing result
        from ufo.agents.processors2.core.processing_context import (
            ProcessingResult,
            ProcessingPhase,
        )

        mock_result = ProcessingResult(
            success=True, data={"test": "data"}, phase=ProcessingPhase.MEMORY_UPDATE
        )

        # Test after_process (should validate without modifying)
        initial_memory_count = mock_agent.memory.length
        initial_trajectory_count = len(mock_agent.blackboard.trajectories)

        await memory_middleware.after_process(processor, mock_result)

        # Memory counts should not change (middleware doesn't modify, only monitors)
        assert (
            mock_agent.memory.length == initial_memory_count
        ), "Middleware should not modify memory"
        assert (
            len(mock_agent.blackboard.trajectories) == initial_trajectory_count
        ), "Middleware should not modify blackboard"

        print("✓ Memory sync middleware monitoring working correctly")
        print("✓ Middleware does not duplicate memory updates")

        return True

    except Exception as e:
        print(f"\n❌ Memory sync middleware test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_integration():
    """Test integration of strategy and middleware working together."""

    print("\n3. Testing integration of memory strategy and middleware...")

    try:
        # Create mock agent and global context
        mock_agent = MockAppAgent()
        global_context = Context()

        # Create processor
        processor = AppAgentProcessorV2(mock_agent, global_context)

        # Test that both components are properly set up
        from ufo.agents.processors2.core.processing_context import ProcessingPhase

        # Check strategy exists
        assert ProcessingPhase.MEMORY_UPDATE in processor.strategies
        memory_strategy = processor.strategies[ProcessingPhase.MEMORY_UPDATE]
        assert memory_strategy.name == "app_memory_update"

        # Check middleware exists
        memory_middleware = None
        for middleware in processor.middleware_chain:
            if middleware.name == "app_memory_sync":
                memory_middleware = middleware
                break

        assert memory_middleware is not None

        print("✓ Both memory strategy and middleware are properly configured")
        print("✓ Strategy handles updates, middleware handles monitoring")
        print("✓ No duplication of responsibility")

        return True

    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all memory management tests."""

    print("🧠 Testing AppAgent Memory Management Architecture")
    print("=" * 60)

    success1 = await test_memory_update_strategy()
    success2 = await test_memory_sync_middleware()
    success3 = await test_integration()

    if all([success1, success2, success3]):
        print("\n🎉 All memory management tests passed!")
        print("\n✅ Memory architecture is correctly separated:")
        print("   - AppMemoryUpdateStrategy: Handles all memory updates")
        print("   - AppMemorySyncMiddleware: Monitors and validates memory state")
        print("   - No duplication of functionality")
        return True
    else:
        print("\n❌ Some memory management tests failed!")
        return False


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())

    if not success:
        sys.exit(1)
