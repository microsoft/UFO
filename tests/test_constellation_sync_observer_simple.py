# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Comprehensive tests for ConstellationModificationSynchronizer.

This test suite covers:
1. Basic synchronization flow
2. Race condition prevention  
3. Timeout handling
4. Error recovery
5. Multiple concurrent modifications
"""

import asyncio
import logging
import time
import sys
import os
import pytest
from unittest.mock import Mock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from galaxy.session.observers.constellation_sync_observer import (
    ConstellationModificationSynchronizer,
)
from galaxy.core.events import (
    TaskEvent,
    ConstellationEvent,
    EventType,
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


def create_task_event(
    task_id: str,
    event_type: EventType = EventType.TASK_COMPLETED,
    constellation_id: str = "test_constellation",
    status: str = "completed",
) -> TaskEvent:
    """Helper function to create TaskEvent."""
    return TaskEvent(
        event_type=event_type,
        source_id="test_source",
        timestamp=time.time(),
        task_id=task_id,
        status=status,
        data={"constellation_id": constellation_id},
    )


def create_constellation_event(
    task_id: str,
    constellation_id: str = "test_constellation",
) -> ConstellationEvent:
    """Helper function to create ConstellationEvent."""
    return ConstellationEvent(
        event_type=EventType.CONSTELLATION_MODIFIED,
        source_id="test_agent",
        timestamp=time.time(),
        data={"on_task_id": task_id},
        constellation_id=constellation_id,
        constellation_state="executing",
    )


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""
    orchestrator = Mock()
    orchestrator.name = "test_orchestrator"
    return orchestrator


@pytest.fixture
def synchronizer(mock_orchestrator):
    """Create a synchronizer instance for testing."""
    logger = logging.getLogger("test_synchronizer")
    return ConstellationModificationSynchronizer(
        orchestrator=mock_orchestrator,
        logger=logger,
    )


class TestBasicSynchronization:
    """Test basic synchronization functionality."""

    @pytest.mark.asyncio
    async def test_register_pending_modification(self, synchronizer):
        """Test that task completion events register pending modifications."""
        event = create_task_event("task_1")
        await synchronizer.on_event(event)

        assert synchronizer.has_pending_modifications()
        assert synchronizer.get_pending_count() == 1
        assert "task_1" in synchronizer.get_pending_task_ids()

    @pytest.mark.asyncio
    async def test_complete_modification(self, synchronizer):
        """Test that constellation modified events complete pending modifications."""
        # Register pending modification
        task_event = create_task_event("task_1")
        await synchronizer.on_event(task_event)
        assert synchronizer.has_pending_modifications()

        # Complete modification
        mod_event = create_constellation_event("task_1")
        await synchronizer.on_event(mod_event)

        # Verify modification was completed
        assert not synchronizer.has_pending_modifications()
        assert synchronizer.get_pending_count() == 0

    @pytest.mark.asyncio
    async def test_wait_for_single_modification(self, synchronizer):
        """Test waiting for a single pending modification."""
        # Register pending modification
        task_event = create_task_event("task_1")
        await synchronizer.on_event(task_event)

        # Start waiting in background
        wait_task = asyncio.create_task(
            synchronizer.wait_for_pending_modifications()
        )

        # Give wait task time to start
        await asyncio.sleep(0.1)

        # Complete modification
        mod_event = create_constellation_event("task_1")
        await synchronizer.on_event(mod_event)

        # Wait should complete successfully
        result = await wait_task
        assert result is True

    @pytest.mark.asyncio
    async def test_wait_with_no_pending_modifications(self, synchronizer):
        """Test that waiting with no pending modifications returns immediately."""
        result = await synchronizer.wait_for_pending_modifications()
        assert result is True


class TestRaceConditionPrevention:
    """Test race condition prevention scenarios."""

    @pytest.mark.asyncio
    async def test_orchestrator_waits_for_modification(self, synchronizer):
        """Test that orchestrator waits for agent to complete modification."""
        # Simulate task completion
        task_event = create_task_event("task_A")
        await synchronizer.on_event(task_event)

        # Track timing
        orchestrator_proceeded = False
        modification_completed = False

        async def orchestrator_flow():
            """Simulate orchestrator waiting."""
            nonlocal orchestrator_proceeded
            await synchronizer.wait_for_pending_modifications()
            orchestrator_proceeded = True

        async def agent_flow():
            """Simulate agent modifying constellation."""
            nonlocal modification_completed
            await asyncio.sleep(0.2)  # Simulate modification work
            modification_completed = True

            # Publish modification complete event
            mod_event = create_constellation_event("task_A")
            await synchronizer.on_event(mod_event)

        # Run both flows concurrently
        await asyncio.gather(orchestrator_flow(), agent_flow())

        # Verify orchestrator waited for modification
        assert modification_completed
        assert orchestrator_proceeded

    @pytest.mark.asyncio
    async def test_multiple_tasks_concurrent(self, synchronizer):
        """Test handling multiple task completions and modifications concurrently."""
        task_ids = ["task_1", "task_2", "task_3"]

        # Register all tasks as pending
        for task_id in task_ids:
            event = create_task_event(task_id)
            await synchronizer.on_event(event)

        assert synchronizer.get_pending_count() == 3

        # Start waiting
        wait_task = asyncio.create_task(
            synchronizer.wait_for_pending_modifications()
        )

        # Complete modifications with delays
        async def complete_modification(task_id: str, delay: float):
            await asyncio.sleep(delay)
            mod_event = create_constellation_event(task_id)
            await synchronizer.on_event(mod_event)

        # Complete modifications in random order with delays
        await asyncio.gather(
            complete_modification("task_2", 0.1),
            complete_modification("task_1", 0.2),
            complete_modification("task_3", 0.15),
        )

        # Wait should complete after all modifications
        result = await wait_task
        assert result is True
        assert synchronizer.get_pending_count() == 0


class TestTimeoutHandling:
    """Test timeout and error handling."""

    @pytest.mark.asyncio
    async def test_modification_timeout(self, synchronizer):
        """Test that modifications timeout after specified duration."""
        # Set short timeout for testing
        synchronizer.set_modification_timeout(0.5)

        # Register pending modification
        event = create_task_event("slow_task")
        await synchronizer.on_event(event)

        # Wait for modification (should timeout)
        result = await synchronizer.wait_for_pending_modifications(timeout=0.3)

        # Should return False due to timeout
        assert result is False
        # Pending modifications should be cleared
        assert synchronizer.get_pending_count() == 0

    @pytest.mark.asyncio
    async def test_auto_complete_on_timeout(self, synchronizer):
        """Test that pending modifications auto-complete on timeout."""
        # Set very short timeout
        synchronizer.set_modification_timeout(0.2)

        # Register pending modification
        event = create_task_event("timeout_task")
        await synchronizer.on_event(event)

        # Wait for auto-timeout
        await asyncio.sleep(0.3)

        # Modification should have been auto-completed
        assert synchronizer.get_pending_count() == 0


class TestErrorRecovery:
    """Test error recovery scenarios."""

    @pytest.mark.asyncio
    async def test_clear_pending_modifications(self, synchronizer):
        """Test forcefully clearing pending modifications."""
        # Register multiple pending modifications
        for i in range(3):
            event = create_task_event(f"task_{i}")
            await synchronizer.on_event(event)

        assert synchronizer.get_pending_count() == 3

        # Clear all pending modifications
        synchronizer.clear_pending_modifications()

        # Verify all cleared
        assert synchronizer.get_pending_count() == 0
        assert not synchronizer.has_pending_modifications()

    @pytest.mark.asyncio
    async def test_handle_missing_constellation_id(self, synchronizer):
        """Test handling events with missing constellation_id."""
        # Event without constellation_id
        event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test",
            timestamp=time.time(),
            task_id="task_missing_id",
            status="completed",
            data={},  # No constellation_id
        )

        # Should not raise exception
        await synchronizer.on_event(event)

        # Should not register pending modification
        assert synchronizer.get_pending_count() == 0

    @pytest.mark.asyncio
    async def test_task_failed_event(self, synchronizer):
        """Test that TASK_FAILED events also register pending modifications."""
        event = create_task_event(
            "failed_task",
            event_type=EventType.TASK_FAILED,
            status="failed"
        )

        await synchronizer.on_event(event)

        # Should register pending modification for failed tasks too
        assert synchronizer.has_pending_modifications()
        assert "failed_task" in synchronizer.get_pending_task_ids()


class TestStatistics:
    """Test statistics tracking."""

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, synchronizer):
        """Test that statistics are properly tracked."""
        initial_stats = synchronizer.get_statistics()
        assert initial_stats["total_modifications"] == 0

        # Complete one modification successfully
        task_event = create_task_event("stats_task")
        await synchronizer.on_event(task_event)

        mod_event = create_constellation_event("stats_task")
        await synchronizer.on_event(mod_event)

        # Check updated statistics
        stats = synchronizer.get_statistics()
        assert stats["total_modifications"] == 1
        assert stats["completed_modifications"] == 1


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_ignore_non_completion_events(self, synchronizer):
        """Test that non-completion task events are ignored."""
        # Task started event (should be ignored)
        event = create_task_event(
            "started_task",
            event_type=EventType.TASK_STARTED,
            status="started"
        )

        await synchronizer.on_event(event)

        # Should not register pending modification
        assert synchronizer.get_pending_count() == 0

    @pytest.mark.asyncio
    async def test_set_invalid_timeout(self, synchronizer):
        """Test that setting invalid timeout raises error."""
        with pytest.raises(ValueError):
            synchronizer.set_modification_timeout(-1)

        with pytest.raises(ValueError):
            synchronizer.set_modification_timeout(0)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
