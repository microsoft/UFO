# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Event system for Galaxy framework using Observer pattern.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class EventType(Enum):
    """
    Types of events in the Galaxy system.

    Defines enumeration for different event types that can occur
    during Galaxy framework execution.
    """

    # Task-level events (micro-level state changes)
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Constellation lifecycle events (macro-level state changes)
    CONSTELLATION_STARTED = "constellation_started"
    CONSTELLATION_COMPLETED = "constellation_completed"
    CONSTELLATION_FAILED = "constellation_failed"

    # Structure modification events (for dynamic constellation changes)
    CONSTELLATION_MODIFIED = "constellation_modified"

    # Agent output events (for real-time agent interaction display)
    AGENT_RESPONSE = "agent_response"  # Agent LLM response (thought, plan, etc.)
    AGENT_ACTION = "agent_action"  # Agent action execution details

    # Device events (for device connection and status monitoring)
    DEVICE_CONNECTED = "device_connected"  # Device connected to constellation
    DEVICE_DISCONNECTED = (
        "device_disconnected"  # Device disconnected from constellation
    )
    DEVICE_STATUS_CHANGED = "device_status_changed"  # Device status changed


@dataclass
class Event:
    """
    Base event class.

    Represents the fundamental structure of all events in the Galaxy system
    with common fields for type, source, timing, and data.
    """

    event_type: EventType
    source_id: str
    timestamp: float
    data: Dict[str, Any]


@dataclass
class TaskEvent(Event):
    """
    Task-specific event.

    Extends base Event class with task-specific information including
    task ID, status, result, and error details.
    """

    task_id: str
    status: str
    result: Any = None
    error: Optional[Exception] = None


@dataclass
class ConstellationEvent(Event):
    """
    Constellation-specific event.

    Extends base Event class with constellation-specific information including
    constellation ID, state, and list of newly ready tasks.
    """

    constellation_id: str
    constellation_state: str
    new_ready_tasks: List[str] = None


@dataclass
class AgentEvent(Event):
    """
    Agent output event.

    Extends base Event class with agent-specific information including
    agent name, output type, and the actual output content.
    """

    agent_name: str
    agent_type: str  # "constellation", "app", "host", etc.
    output_type: str  # "response", "action", "thought", "plan"
    output_data: Dict[str, Any]  # The actual output content


@dataclass
class DeviceEvent(Event):
    """
    Device-specific event.

    Extends base Event class with device-specific information including
    device ID, device status, and a snapshot of all devices in the registry.
    """

    device_id: str
    device_status: str
    device_info: Dict[str, Any]  # Current device information
    all_devices: Dict[str, Dict[str, Any]]  # Snapshot of all devices in registry


class IEventObserver(ABC):
    """
    Interface for event observers.

    Defines the contract for objects that want to receive
    and handle events from the Galaxy event system.
    """

    @abstractmethod
    async def on_event(self, event: Event) -> None:
        """
        Handle an event.

        Processes an incoming event and performs necessary actions
        based on the event type and data.

        :param event: The event object containing type, source, timestamp and data
        :return: None
        """
        pass


class IEventPublisher(ABC):
    """
    Interface for event publishers.

    Defines the contract for objects that can publish events
    and manage observer subscriptions in the Galaxy framework.
    """

    @abstractmethod
    def subscribe(
        self, observer: IEventObserver, event_types: Set[EventType] = None
    ) -> None:
        """
        Subscribe an observer to events.

        Registers an observer to receive notifications for specific
        event types or all events if no types specified.

        :param observer: The observer object that will handle events
        :param event_types: Set of event types to subscribe to, None for all events
        :return: None
        """
        pass

    @abstractmethod
    def unsubscribe(self, observer: IEventObserver) -> None:
        """
        Unsubscribe an observer.

        Removes an observer from all event subscriptions
        to stop receiving further notifications.

        :param observer: The observer object to remove from subscriptions
        :return: None
        """
        pass

    @abstractmethod
    async def publish_event(self, event: Event) -> None:
        """
        Publish an event to subscribers.

        Distributes an event to all registered observers
        that are subscribed to the event's type.

        :param event: The event object to publish to subscribers
        :return: None
        """
        pass


class EventBus(IEventPublisher):
    """
    Central event bus for Galaxy framework.

    Implements the event publishing system that manages observer
    subscriptions and distributes events throughout the Galaxy system.
    """

    def __init__(self):
        """
        Initialize the event bus.

        Sets up observer collections and logger for managing
        event subscriptions and notifications.

        :return: None
        """
        self._observers: Dict[EventType, Set[IEventObserver]] = {}
        self._all_observers: Set[IEventObserver] = set()
        self.logger = logging.getLogger(__name__)

    def subscribe(
        self, observer: IEventObserver, event_types: Set[EventType] = None
    ) -> None:
        """
        Subscribe an observer to specific event types or all events.

        Registers an observer to receive notifications for specified event types
        or subscribes to all events if no specific types are provided.

        :param observer: The observer object that will handle events
        :param event_types: Set of event types to subscribe to, None for all events
        :return: None
        """
        if event_types is None:
            self._all_observers.add(observer)
            self.logger.debug(f"Observer {observer} subscribed to all events.")
        else:
            for event_type in event_types:
                if event_type not in self._observers:
                    self._observers[event_type] = set()
                self._observers[event_type].add(observer)
                self.logger.info(
                    f"Observer {observer} subscribed to event type {event_type}."
                )

    def unsubscribe(self, observer: IEventObserver) -> None:
        """
        Unsubscribe an observer from all events.

        Removes the observer from all subscription lists to stop
        receiving any further event notifications.

        :param observer: The observer object to remove from subscriptions
        :return: None
        """
        self._all_observers.discard(observer)
        for observers in self._observers.values():
            observers.discard(observer)

    async def publish_event(self, event: Event) -> None:
        """
        Publish an event to all relevant subscribers.

        Distributes the event to observers subscribed to the specific event type
        and to observers subscribed to all events, executing notifications concurrently.

        :param event: The event object to publish to subscribers
        :return: None
        """
        observers_to_notify: Set[IEventObserver] = set()

        self.logger.info(f"Publishing event: {event.event_type} from {event.source_id}")

        # Add observers subscribed to this specific event type
        if event.event_type in self._observers:
            observers_to_notify.update(self._observers[event.event_type])

        # Add observers subscribed to all events
        observers_to_notify.update(self._all_observers)

        # Notify all observers concurrently
        if observers_to_notify:
            tasks = [observer.on_event(event) for observer in observers_to_notify]
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                self.logger.error(f"Error notifying observers: {e}")


# Global event bus instance
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.

    Returns the singleton EventBus instance used throughout
    the Galaxy framework for event publishing and subscription.

    :return: The global EventBus instance
    """
    return _event_bus
