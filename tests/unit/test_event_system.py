# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for the event system in Galaxy framework.

This module tests the event bus, observers, and event-driven orchestration
functionality to ensure proper        # Create generic event (not TaskEvent or ConstellationEvent)
        generic_event = Event(
            event_type=EventType.TASK_STARTED,  # This should not match
            source_id="other_source",
            timestamp=time.time(),
            data={},
        )

        await observer.on_event(generic_event)

        # Verify generic events don't trigger task completion queue
        mock_agent.task_completion_queue.put.assert_not_called()nd communication between components.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch

from galaxy.core.events import (
    EventBus,
    Event,
    TaskEvent,
    ConstellationEvent,
    EventType,
    IEventObserver,
    get_event_bus,
)
from galaxy.session.observers import (
    ConstellationProgressObserver,
    SessionMetricsObserver,
)
from galaxy.constellation.enums import TaskStatus


class TestEventBus:
    """Test cases for EventBus functionality."""

    def test_event_bus_singleton(self):
        """Test that get_event_bus returns the same instance."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    @pytest.mark.asyncio
    async def test_event_subscription_and_publishing(self):
        """Test basic event subscription and publishing."""
        bus = EventBus()
        observer = Mock()
        observer.on_event = AsyncMock()

        # Subscribe observer
        bus.subscribe(observer)

        # Create and publish event
        event = Event(
            event_type=EventType.TASK_STARTED,
            source_id="test_source",
            timestamp=time.time(),
            data={"test": "data"},
        )

        await bus.publish_event(event)

        # Verify observer was called
        observer.on_event.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_multiple_observers(self):
        """Test that multiple observers receive events."""
        bus = EventBus()
        observer1 = Mock()
        observer1.on_event = AsyncMock()
        observer2 = Mock()
        observer2.on_event = AsyncMock()

        # Subscribe observers
        bus.subscribe(observer1)
        bus.subscribe(observer2)

        # Create and publish event
        event = Event(
            event_type=EventType.TASK_COMPLETED,
            source_id="test_source",
            timestamp=time.time(),
            data={"test": "data"},
        )

        await bus.publish_event(event)

        # Verify both observers were called
        observer1.on_event.assert_called_once_with(event)
        observer2.on_event.assert_called_once_with(event)

    def test_unsubscribe_observer(self):
        """Test unsubscribing observers."""
        bus = EventBus()
        observer = Mock()

        # Subscribe and then unsubscribe
        bus.subscribe(observer)
        assert observer in bus._all_observers

        bus.unsubscribe(observer)
        assert observer not in bus._all_observers

    @pytest.mark.asyncio
    async def test_observer_exception_handling(self):
        """Test that exceptions in observers don't break event publishing."""
        bus = EventBus()

        # Create observer that raises exception
        failing_observer = Mock()
        failing_observer.on_event = AsyncMock(side_effect=Exception("Test error"))

        # Create working observer
        working_observer = Mock()
        working_observer.on_event = AsyncMock()

        bus.subscribe(failing_observer)
        bus.subscribe(working_observer)

        # Create and publish event
        event = Event(
            event_type=EventType.TASK_FAILED,
            source_id="test_source",
            timestamp=time.time(),
            data={"test": "data"},
        )

        await bus.publish_event(event)

        # Verify working observer still got called despite exception
        working_observer.on_event.assert_called_once_with(event)


class TestEventTypes:
    """Test cases for different event types."""

    def test_task_event_creation(self):
        """Test TaskEvent creation and properties."""
        event = TaskEvent(
            event_type=EventType.TASK_STARTED,
            source_id="orchestrator_123",
            timestamp=time.time(),
            data={"constellation_id": "test_constellation"},
            task_id="task_123",
            status="running",
        )

        assert event.event_type == EventType.TASK_STARTED
        assert event.task_id == "task_123"
        assert event.status == "running"
        assert event.data["constellation_id"] == "test_constellation"

    def test_constellation_event_creation(self):
        """Test ConstellationEvent creation and properties."""
        event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_COMPLETED,
            source_id="session_456",
            timestamp=time.time(),
            data={"total_tasks": 5},
            constellation_id="constellation_789",
            constellation_state="completed",
        )

        assert event.event_type == EventType.CONSTELLATION_COMPLETED
        assert event.constellation_id == "constellation_789"
        assert event.constellation_state == "completed"
        assert event.data["total_tasks"] == 5


class TestConstellationProgressObserver:
    """Test cases for ConstellationProgressObserver."""

    @pytest.mark.asyncio
    async def test_task_progress_handling(self):
        """Test handling of task progress events."""
        # Create mock agent and context
        mock_agent = Mock()
        mock_agent.task_completion_queue = AsyncMock()
        mock_agent.task_completion_queue.put = AsyncMock()
        mock_context = Mock()

        observer = ConstellationProgressObserver(
            agent=mock_agent,
            context=mock_context,
        )

        # Create task event
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="orchestrator",
            timestamp=time.time(),
            data={},
            task_id="task_123",
            status=TaskStatus.COMPLETED.value,
        )

        await observer.on_event(task_event)

        # Verify task was queued to agent
        mock_agent.task_completion_queue.put.assert_called_once_with(task_event)
        # Verify task result was stored
        assert "task_123" in observer.task_results
        assert observer.task_results["task_123"]["status"] == TaskStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_constellation_event_handling(self):
        """Test handling of constellation events."""
        # Create mock agent and context
        mock_agent = Mock()
        mock_agent.task_completion_queue = AsyncMock()
        mock_context = Mock()

        observer = ConstellationProgressObserver(
            agent=mock_agent,
            context=mock_context,
        )

        # Create constellation event
        constellation_event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_COMPLETED,
            source_id="session",
            timestamp=time.time(),
            data={},
            constellation_id="constellation_123",
            constellation_state="completed",
        )

        await observer.on_event(constellation_event)

        # Verify constellation event was handled (no errors should occur)
        # The current implementation logs but doesn't queue constellation events

    @pytest.mark.asyncio
    async def test_irrelevant_event_filtering(self):
        """Test that irrelevant events are filtered out."""
        # Create mock agent and context
        mock_agent = Mock()
        mock_agent.task_completion_queue = AsyncMock()
        mock_context = Mock()

        observer = ConstellationProgressObserver(
            agent=mock_agent,
            context=mock_context,
        )

        # Create generic event (not task or constellation specific)
        generic_event = Event(
            event_type=EventType.TASK_STARTED,  # This should not match
            source_id="other_source",
            timestamp=time.time(),
            data={},
        )

        await observer.on_event(generic_event)

        # Verify generic events don't trigger task completion queue
        mock_agent.task_completion_queue.put.assert_not_called()


class TestSessionMetricsObserver:
    """Test cases for SessionMetricsObserver."""

    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test basic metrics collection."""
        observer = SessionMetricsObserver(session_id="test_session")

        # Create task events
        start_event = TaskEvent(
            event_type=EventType.TASK_STARTED,
            source_id="orchestrator",
            timestamp=time.time(),
            data={},
            task_id="task_1",
            status=TaskStatus.RUNNING.value,
        )

        completed_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="orchestrator",
            timestamp=time.time() + 1,  # 1 second later
            data={},
            task_id="task_1",
            status=TaskStatus.COMPLETED.value,
        )

        # Handle events
        await observer.on_event(start_event)
        await observer.on_event(completed_event)

        # Check metrics
        metrics = observer.get_metrics()
        assert metrics["task_count"] == 1
        assert metrics["completed_tasks"] == 1
        assert metrics["failed_tasks"] == 0
        assert "task_1" in metrics["task_timings"]

    @pytest.mark.asyncio
    async def test_failed_task_metrics(self):
        """Test metrics collection for failed tasks."""
        observer = SessionMetricsObserver(session_id="test_session")

        # Create started task event first (tasks need to be started before they can fail)
        start_event = TaskEvent(
            event_type=EventType.TASK_STARTED,
            source_id="orchestrator",
            timestamp=time.time(),
            data={},
            task_id="task_2",
            status=TaskStatus.RUNNING.value,
        )

        # Create failed task event
        failed_event = TaskEvent(
            event_type=EventType.TASK_FAILED,
            source_id="orchestrator",
            timestamp=time.time(),
            data={},
            task_id="task_2",
            status=TaskStatus.FAILED.value,
        )

        await observer.on_event(start_event)
        await observer.on_event(failed_event)

        # Check metrics
        metrics = observer.get_metrics()
        assert metrics["task_count"] == 1
        assert metrics["completed_tasks"] == 0
        assert metrics["failed_tasks"] == 1


class TestEventSystemIntegration:
    """Integration tests for the complete event system."""

    @pytest.mark.asyncio
    async def test_end_to_end_event_flow(self):
        """Test complete event flow from publishing to observer handling."""
        bus = get_event_bus()

        # Clear any existing observers
        bus._observers.clear()

        # Set up observer with mock agent and context
        mock_agent = Mock()
        mock_agent.task_completion_queue = AsyncMock()
        mock_context = Mock()

        progress_observer = ConstellationProgressObserver(
            agent=mock_agent,
            context=mock_context,
        )

        metrics_observer = SessionMetricsObserver(session_id="integration_test")

        bus.subscribe(progress_observer)
        bus.subscribe(metrics_observer)

        # Simulate task lifecycle
        start_event = TaskEvent(
            event_type=EventType.TASK_STARTED,
            source_id="test_orchestrator",
            timestamp=time.time(),
            data={"constellation_id": "test_constellation"},
            task_id="integration_task",
            status=TaskStatus.RUNNING.value,
        )

        completed_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test_orchestrator",
            timestamp=time.time() + 2,
            data={"constellation_id": "test_constellation"},
            task_id="integration_task",
            status=TaskStatus.COMPLETED.value,
        )

        # Publish events
        await bus.publish_event(start_event)
        await bus.publish_event(completed_event)

        # Verify task events were queued to agent
        assert (
            mock_agent.task_completion_queue.put.call_count == 2
        )  # Start and completed

        # Verify metrics were collected
        metrics = metrics_observer.get_metrics()
        assert metrics["task_count"] == 1
        assert metrics["completed_tasks"] == 1

    @pytest.mark.asyncio
    async def test_concurrent_event_publishing(self):
        """Test handling of concurrent event publishing."""
        bus = EventBus()
        observer = Mock()
        observer.on_event = AsyncMock()

        bus.subscribe(observer)

        # Create multiple events
        events = []
        for i in range(10):
            event = TaskEvent(
                event_type=EventType.TASK_STARTED,
                source_id=f"source_{i}",
                timestamp=time.time(),
                data={},
                task_id=f"task_{i}",
                status=TaskStatus.RUNNING.value,
            )
            events.append(event)

        # Publish events concurrently
        await asyncio.gather(*[bus.publish_event(event) for event in events])

        # Verify all events were handled
        assert observer.on_event.call_count == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
