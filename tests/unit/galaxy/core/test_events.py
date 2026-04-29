# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for galaxy/core/events.py

Covers EventType enum, Event dataclasses, IEventObserver / IEventPublisher
interfaces, and EventBus behaviour (subscribe, unsubscribe, publish).
"""

import asyncio
import sys
import os
import time
from unittest.mock import AsyncMock, Mock

import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from galaxy.core.events import (
    AgentEvent,
    ConstellationEvent,
    DeviceEvent,
    Event,
    EventBus,
    EventType,
    IEventObserver,
    IEventPublisher,
    TaskEvent,
    get_event_bus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(event_type: EventType = EventType.TASK_STARTED) -> Event:
    return Event(
        event_type=event_type,
        source_id="test_source",
        timestamp=time.time(),
        data={"key": "value"},
    )


class ConcreteObserver(IEventObserver):
    """Minimal concrete observer for testing the abstract interface."""

    def __init__(self):
        self.received: list = []

    async def on_event(self, event: Event) -> None:
        self.received.append(event)


# ---------------------------------------------------------------------------
# EventType
# ---------------------------------------------------------------------------


class TestEventType:
    def test_all_values_are_strings(self):
        for member in EventType:
            assert isinstance(member.value, str)

    def test_task_event_types_exist(self):
        assert EventType.TASK_STARTED
        assert EventType.TASK_COMPLETED
        assert EventType.TASK_FAILED

    def test_constellation_event_types_exist(self):
        assert EventType.CONSTELLATION_STARTED
        assert EventType.CONSTELLATION_COMPLETED
        assert EventType.CONSTELLATION_FAILED
        assert EventType.CONSTELLATION_MODIFIED

    def test_device_event_types_exist(self):
        assert EventType.DEVICE_CONNECTED
        assert EventType.DEVICE_DISCONNECTED
        assert EventType.DEVICE_STATUS_CHANGED

    def test_agent_event_types_exist(self):
        assert EventType.AGENT_RESPONSE
        assert EventType.AGENT_ACTION

    def test_unique_values(self):
        values = [m.value for m in EventType]
        assert len(values) == len(set(values)), "Duplicate EventType values detected"


# ---------------------------------------------------------------------------
# Event dataclasses
# ---------------------------------------------------------------------------


class TestEventDataclass:
    def test_base_event_fields(self):
        evt = _make_event(EventType.TASK_STARTED)
        assert evt.event_type is EventType.TASK_STARTED
        assert evt.source_id == "test_source"
        assert isinstance(evt.timestamp, float)
        assert evt.data == {"key": "value"}

    def test_task_event_fields(self):
        evt = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="src",
            timestamp=time.time(),
            data={},
            task_id="task-1",
            status="completed",
            result={"output": "ok"},
            error=None,
        )
        assert evt.task_id == "task-1"
        assert evt.status == "completed"
        assert evt.result == {"output": "ok"}
        assert evt.error is None

    def test_task_event_defaults(self):
        evt = TaskEvent(
            event_type=EventType.TASK_FAILED,
            source_id="src",
            timestamp=time.time(),
            data={},
            task_id="task-2",
            status="failed",
        )
        assert evt.result is None
        assert evt.error is None

    def test_constellation_event_fields(self):
        evt = ConstellationEvent(
            event_type=EventType.CONSTELLATION_STARTED,
            source_id="src",
            timestamp=time.time(),
            data={},
            constellation_id="c-1",
            constellation_state="executing",
            new_ready_tasks=["t1", "t2"],
        )
        assert evt.constellation_id == "c-1"
        assert evt.new_ready_tasks == ["t1", "t2"]

    def test_agent_event_fields(self):
        evt = AgentEvent(
            event_type=EventType.AGENT_RESPONSE,
            source_id="src",
            timestamp=time.time(),
            data={},
            agent_name="app_agent",
            agent_type="app",
            output_type="response",
            output_data={"thought": "thinking..."},
        )
        assert evt.agent_name == "app_agent"
        assert evt.output_data == {"thought": "thinking..."}

    def test_device_event_fields(self):
        evt = DeviceEvent(
            event_type=EventType.DEVICE_CONNECTED,
            source_id="src",
            timestamp=time.time(),
            data={},
            device_id="dev-1",
            device_status="connected",
            device_info={"os": "Windows"},
            all_devices={"dev-1": {"status": "connected"}},
        )
        assert evt.device_id == "dev-1"
        assert evt.device_status == "connected"


# ---------------------------------------------------------------------------
# IEventObserver interface
# ---------------------------------------------------------------------------


class TestIEventObserver:
    def test_concrete_subclass_is_instantiable(self):
        obs = ConcreteObserver()
        assert isinstance(obs, IEventObserver)

    @pytest.mark.asyncio
    async def test_on_event_is_called(self):
        obs = ConcreteObserver()
        evt = _make_event()
        await obs.on_event(evt)
        assert obs.received == [evt]

    def test_abstract_class_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            IEventObserver()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# IEventPublisher interface
# ---------------------------------------------------------------------------


class TestIEventPublisher:
    def test_abstract_class_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            IEventPublisher()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------


class TestEventBus:
    # ------------------------------------------------------------------
    # subscribe / unsubscribe
    # ------------------------------------------------------------------

    def test_subscribe_all_events(self):
        bus = EventBus()
        obs = ConcreteObserver()
        bus.subscribe(obs)
        assert obs in bus._all_observers

    def test_subscribe_specific_event_types(self):
        bus = EventBus()
        obs = ConcreteObserver()
        bus.subscribe(obs, {EventType.TASK_STARTED, EventType.TASK_COMPLETED})
        assert obs in bus._observers[EventType.TASK_STARTED]
        assert obs in bus._observers[EventType.TASK_COMPLETED]

    def test_unsubscribe_removes_from_all_observers(self):
        bus = EventBus()
        obs = ConcreteObserver()
        bus.subscribe(obs)
        bus.unsubscribe(obs)
        assert obs not in bus._all_observers

    def test_unsubscribe_removes_from_typed_observers(self):
        bus = EventBus()
        obs = ConcreteObserver()
        bus.subscribe(obs, {EventType.TASK_STARTED})
        bus.unsubscribe(obs)
        assert obs not in bus._observers.get(EventType.TASK_STARTED, set())

    def test_unsubscribe_nonexistent_observer_is_noop(self):
        bus = EventBus()
        obs = ConcreteObserver()
        bus.unsubscribe(obs)  # should not raise

    # ------------------------------------------------------------------
    # publish_event
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_all_events_subscriber_receives_every_event(self):
        bus = EventBus()
        obs = ConcreteObserver()
        bus.subscribe(obs)

        for et in [EventType.TASK_STARTED, EventType.TASK_COMPLETED, EventType.DEVICE_CONNECTED]:
            await bus.publish_event(_make_event(et))

        assert len(obs.received) == 3

    @pytest.mark.asyncio
    async def test_typed_subscriber_receives_only_matching_events(self):
        bus = EventBus()
        obs = ConcreteObserver()
        bus.subscribe(obs, {EventType.TASK_STARTED})

        await bus.publish_event(_make_event(EventType.TASK_STARTED))
        await bus.publish_event(_make_event(EventType.TASK_COMPLETED))

        assert len(obs.received) == 1
        assert obs.received[0].event_type is EventType.TASK_STARTED

    @pytest.mark.asyncio
    async def test_multiple_observers_all_notified(self):
        bus = EventBus()
        obs1 = ConcreteObserver()
        obs2 = ConcreteObserver()
        bus.subscribe(obs1)
        bus.subscribe(obs2)

        await bus.publish_event(_make_event())

        assert len(obs1.received) == 1
        assert len(obs2.received) == 1

    @pytest.mark.asyncio
    async def test_no_subscribers_publish_is_noop(self):
        bus = EventBus()
        # Should not raise
        await bus.publish_event(_make_event())

    @pytest.mark.asyncio
    async def test_observer_exception_does_not_propagate(self):
        """A failing observer must not crash the event bus."""
        bus = EventBus()

        bad_obs = Mock()
        bad_obs.on_event = AsyncMock(side_effect=RuntimeError("observer failure"))
        bus.subscribe(bad_obs)

        good_obs = ConcreteObserver()
        bus.subscribe(good_obs)

        # publish_event uses gather(return_exceptions=True) so this should not raise
        await bus.publish_event(_make_event())

        assert len(good_obs.received) == 1

    @pytest.mark.asyncio
    async def test_unsubscribed_observer_receives_no_events(self):
        bus = EventBus()
        obs = ConcreteObserver()
        bus.subscribe(obs)
        bus.unsubscribe(obs)

        await bus.publish_event(_make_event())

        assert obs.received == []

    # ------------------------------------------------------------------
    # Singleton helper
    # ------------------------------------------------------------------

    def test_get_event_bus_returns_same_instance(self):
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_get_event_bus_returns_event_bus_instance(self):
        assert isinstance(get_event_bus(), EventBus)
