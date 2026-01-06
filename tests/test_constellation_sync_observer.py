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
6. Edge cases
"""

import asyncio
import logging
import time
import sys
import os
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

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
logging.basicConfig(level=logging.DEBUG)


def create_task_event(
    task_id: str,
    event_type: EventType = EventType.TASK_COMPLETED,
    constellation_id: str = "test_constellation",
    status: str = "completed",
    **extra_data
) -> TaskEvent:
    """Helper function to create TaskEvent with correct parameters."""
    return TaskEvent(
        event_type=event_type,
        source_id="test_source",
        timestamp=time.time(),
        task_id=task_id,
        status=status,
        data={"constellation_id": constellation_id, **extra_data},
    )


def create_constellation_event(
    task_id: str,
    constellation_id: str = "test_constellation",
    **extra_data
) -> ConstellationEvent:
    """Helper function to create ConstellationEvent with correct parameters."""
    return ConstellationEvent(
        event_type=EventType.CONSTELLATION_MODIFIED,
        source_id="test_agent",
        timestamp=time.time(),
        data={"on_task_id": task_id, **extra_data},
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


@pytest.fixture
def task_completed_event():
    """Create a TASK_COMPLETED event."""
    return create_task_event(
        task_id="task_1",
        constellation_id="constellation_123",
        result={"status": "success"},
    )


@pytest.fixture
def constellation_modified_event():
    """Create a CONSTELLATION_MODIFIED event."""
    return create_constellation_event(
        task_id="task_1",
        constellation_id="constellation_123",
        modification_type="edited",
    )


class TestBasicSynchronization:
    """Test basic synchronization functionality."""

    @pytest.mark.asyncio
    async def test_register_pending_modification(
        self, synchronizer, task_completed_event
    ):
        """Test that task completion events register pending modifications."""
        # Process task completed event
        await synchronizer.on_event(task_completed_event)

        # Verify pending modification was registered
        assert synchronizer.has_pending_modifications()
        assert synchronizer.get_pending_count() == 1
        assert "task_1" in synchronizer.get_pending_task_ids()

    @pytest.mark.asyncio
    async def test_complete_modification(
        self, synchronizer, task_completed_event, constellation_modified_event
    ):
        """Test that constellation modified events complete pending modifications."""
        # Register pending modification
        await synchronizer.on_event(task_completed_event)
        assert synchronizer.has_pending_modifications()

        # Complete modification
        await synchronizer.on_event(constellation_modified_event)

        # Verify modification was completed
        assert not synchronizer.has_pending_modifications()
        assert synchronizer.get_pending_count() == 0

    @pytest.mark.asyncio
    async def test_wait_for_single_modification(
        self, synchronizer, task_completed_event, constellation_modified_event
    ):
        """Test waiting for a single pending modification."""
        # Register pending modification
        await synchronizer.on_event(task_completed_event)

        # Start waiting in background
        wait_task = asyncio.create_task(
            synchronizer.wait_for_pending_modifications()
        )

        # Give wait task time to start
        await asyncio.sleep(0.1)

        # Complete modification
        await synchronizer.on_event(constellation_modified_event)

        # Wait should complete successfully
        result = await wait_task
        assert result is True

    @pytest.mark.asyncio
    async def test_wait_with_no_pending_modifications(self, synchronizer):
        """Test that waiting with no pending modifications returns immediately."""
        # Should return True immediately
        result = await synchronizer.wait_for_pending_modifications()
        assert result is True


class TestRaceConditionPrevention:
    """Test race condition prevention scenarios."""

    @pytest.mark.asyncio
    async def test_orchestrator_waits_for_modification(self, synchronizer):
        """Test that orchestrator waits for agent to complete modification."""
        # Simulate task completion
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test",
            timestamp=time.time(),
            task_id="task_A",
            task_name="Task A",
            data={"constellation_id": "test_constellation"},
        )
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
            mod_event = ConstellationEvent(
                event_type=EventType.CONSTELLATION_MODIFIED,
                source_id="agent",
                timestamp=time.time(),
                data={"on_task_id": "task_A"},
                constellation_id="test_constellation",
                constellation_state="executing",
            )
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
            event = TaskEvent(
                event_type=EventType.TASK_COMPLETED,
                source_id="test",
                timestamp=time.time(),
                task_id=task_id,
                task_name=f"Task {task_id}",
                data={"constellation_id": "test_constellation"},
            )
            await synchronizer.on_event(event)

        assert synchronizer.get_pending_count() == 3

        # Start waiting
        wait_task = asyncio.create_task(
            synchronizer.wait_for_pending_modifications()
        )

        # Complete modifications with delays
        async def complete_modification(task_id: str, delay: float):
            await asyncio.sleep(delay)
            mod_event = ConstellationEvent(
                event_type=EventType.CONSTELLATION_MODIFIED,
                source_id="agent",
                timestamp=time.time(),
                data={"on_task_id": task_id},
                constellation_id="test_constellation",
                constellation_state="executing",
            )
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
        event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test",
            timestamp=time.time(),
            task_id="slow_task",
            task_name="Slow Task",
            data={"constellation_id": "test_constellation"},
        )
        await synchronizer.on_event(event)

        # Wait for modification (should timeout)
        result = await synchronizer.wait_for_pending_modifications(timeout=0.3)

        # Should return False due to timeout
        assert result is False
        # Pending modifications should be cleared
        assert synchronizer.get_pending_count() == 0

        # Check statistics
        stats = synchronizer.get_statistics()
        assert stats["timeout_modifications"] >= 1

    @pytest.mark.asyncio
    async def test_auto_complete_on_timeout(self, synchronizer):
        """Test that pending modifications auto-complete on timeout."""
        # Set very short timeout
        synchronizer.set_modification_timeout(0.2)

        # Register pending modification
        event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test",
            timestamp=time.time(),
            task_id="timeout_task",
            task_name="Timeout Task",
            data={"constellation_id": "test_constellation"},
        )
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
            event = TaskEvent(
                event_type=EventType.TASK_COMPLETED,
                source_id="test",
                timestamp=time.time(),
                task_id=f"task_{i}",
                task_name=f"Task {i}",
                data={"constellation_id": "test_constellation"},
            )
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
            task_name="Task Missing ID",
            data={},  # No constellation_id
        )

        # Should not raise exception
        await synchronizer.on_event(event)

        # Should not register pending modification
        assert synchronizer.get_pending_count() == 0

    @pytest.mark.asyncio
    async def test_handle_missing_task_id(self, synchronizer):
        """Test handling constellation events with missing on_task_id."""
        # Register a pending modification first
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test",
            timestamp=time.time(),
            task_id="task_1",
            task_name="Task 1",
            data={"constellation_id": "test_constellation"},
        )
        await synchronizer.on_event(task_event)

        # Constellation event without on_task_id
        mod_event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_MODIFIED,
            source_id="agent",
            timestamp=time.time(),
            data={},  # Missing on_task_id
            constellation_id="test_constellation",
            constellation_state="executing",
        )

        # Should not raise exception
        await synchronizer.on_event(mod_event)

        # Pending modification should still exist
        assert synchronizer.get_pending_count() == 1

    @pytest.mark.asyncio
    async def test_handle_duplicate_task_completion(self, synchronizer):
        """Test handling duplicate task completion events."""
        # Register same task twice
        event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test",
            timestamp=time.time(),
            task_id="duplicate_task",
            task_name="Duplicate Task",
            data={"constellation_id": "test_constellation"},
        )

        await synchronizer.on_event(event)
        await synchronizer.on_event(event)  # Duplicate

        # Should only register once
        assert synchronizer.get_pending_count() == 1


class TestStatistics:
    """Test statistics tracking."""

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, synchronizer):
        """Test that statistics are properly tracked."""
        initial_stats = synchronizer.get_statistics()
        assert initial_stats["total_modifications"] == 0
        assert initial_stats["completed_modifications"] == 0

        # Complete one modification successfully
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test",
            timestamp=time.time(),
            task_id="stats_task",
            task_name="Stats Task",
            data={"constellation_id": "test_constellation"},
        )
        await synchronizer.on_event(task_event)

        mod_event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_MODIFIED,
            source_id="agent",
            timestamp=time.time(),
            data={"on_task_id": "stats_task"},
            constellation_id="test_constellation",
            constellation_state="executing",
        )
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
        event = TaskEvent(
            event_type=EventType.TASK_STARTED,
            source_id="test",
            timestamp=time.time(),
            task_id="started_task",
            task_name="Started Task",
            data={"constellation_id": "test_constellation"},
        )

        await synchronizer.on_event(event)

        # Should not register pending modification
        assert synchronizer.get_pending_count() == 0

    @pytest.mark.asyncio
    async def test_modification_complete_before_wait(self, synchronizer):
        """Test case where modification completes before wait is called."""
        # Register and complete modification immediately
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test",
            timestamp=time.time(),
            task_id="quick_task",
            task_name="Quick Task",
            data={"constellation_id": "test_constellation"},
        )
        await synchronizer.on_event(task_event)

        mod_event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_MODIFIED,
            source_id="agent",
            timestamp=time.time(),
            data={"on_task_id": "quick_task"},
            constellation_id="test_constellation",
            constellation_state="executing",
        )
        await synchronizer.on_event(mod_event)

        # Now call wait (should return immediately)
        result = await synchronizer.wait_for_pending_modifications()
        assert result is True

    @pytest.mark.asyncio
    async def test_set_invalid_timeout(self, synchronizer):
        """Test that setting invalid timeout raises error."""
        with pytest.raises(ValueError):
            synchronizer.set_modification_timeout(-1)

        with pytest.raises(ValueError):
            synchronizer.set_modification_timeout(0)

    @pytest.mark.asyncio
    async def test_task_failed_event(self, synchronizer):
        """Test that TASK_FAILED events also register pending modifications."""
        event = TaskEvent(
            event_type=EventType.TASK_FAILED,
            source_id="test",
            timestamp=time.time(),
            task_id="failed_task",
            task_name="Failed Task",
            data={
                "constellation_id": "test_constellation",
                "error": "Task execution failed",
            },
        )

        await synchronizer.on_event(event)

        # Should register pending modification for failed tasks too
        assert synchronizer.has_pending_modifications()
        assert "failed_task" in synchronizer.get_pending_task_ids()


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_sequential_task_execution(self, synchronizer):
        """Test sequential task execution with modifications."""
        tasks = ["task_A", "task_B", "task_C"]

        for task_id in tasks:
            # Task completes
            task_event = TaskEvent(
                event_type=EventType.TASK_COMPLETED,
                source_id="orchestrator",
                timestamp=time.time(),
                task_id=task_id,
                task_name=f"Task {task_id}",
                data={"constellation_id": "sequential_constellation"},
            )
            await synchronizer.on_event(task_event)

            # Wait for modification
            wait_task = asyncio.create_task(
                synchronizer.wait_for_pending_modifications()
            )

            # Simulate agent processing
            await asyncio.sleep(0.1)

            # Modification completes
            mod_event = ConstellationEvent(
                event_type=EventType.CONSTELLATION_MODIFIED,
                source_id="agent",
                timestamp=time.time(),
                data={"on_task_id": task_id},
                constellation_id="sequential_constellation",
                constellation_state="executing",
            )
            await synchronizer.on_event(mod_event)

            # Wait should complete
            await wait_task

        # All should be completed
        assert synchronizer.get_pending_count() == 0
        stats = synchronizer.get_statistics()
        assert stats["completed_modifications"] == 3

    @pytest.mark.asyncio
    async def test_parallel_task_execution(self, synchronizer):
        """Test parallel task execution with concurrent modifications."""
        task_ids = [f"parallel_task_{i}" for i in range(5)]

        # All tasks complete simultaneously
        for task_id in task_ids:
            event = TaskEvent(
                event_type=EventType.TASK_COMPLETED,
                source_id="orchestrator",
                timestamp=time.time(),
                task_id=task_id,
                task_name=task_id,
                data={"constellation_id": "parallel_constellation"},
            )
            await synchronizer.on_event(event)

        assert synchronizer.get_pending_count() == 5

        # Start waiting
        wait_task = asyncio.create_task(
            synchronizer.wait_for_pending_modifications()
        )

        # Complete all modifications concurrently
        async def complete_mod(task_id: str):
            await asyncio.sleep(0.05)
            mod_event = ConstellationEvent(
                event_type=EventType.CONSTELLATION_MODIFIED,
                source_id="agent",
                timestamp=time.time(),
                data={"on_task_id": task_id},
                constellation_id="parallel_constellation",
                constellation_state="executing",
            )
            await synchronizer.on_event(mod_event)

        await asyncio.gather(*[complete_mod(tid) for tid in task_ids])

        # Wait should complete
        result = await wait_task
        assert result is True
        assert synchronizer.get_pending_count() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
