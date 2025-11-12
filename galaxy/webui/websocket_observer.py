# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
WebSocket Observer for Galaxy Web UI.

This observer subscribes to all Galaxy events and pushes them to connected WebSocket clients.
Provides efficient event serialization and broadcasting capabilities.
"""

import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Type

from fastapi import WebSocket

from galaxy.core.events import (
    AgentEvent,
    ConstellationEvent,
    DeviceEvent,
    Event,
    IEventObserver,
    TaskEvent,
)


class EventSerializer:
    """
    Handles serialization of various data types to JSON-compatible format.

    This class provides a centralized, extensible way to serialize complex
    Python objects into JSON-serializable dictionaries for WebSocket transmission.
    """

    def __init__(self) -> None:
        """Initialize the event serializer with cached imports and type handlers."""
        self.logger: logging.Logger = logging.getLogger(__name__)

        # Cache imports to avoid repeated import attempts
        self._cached_types: Dict[str, Optional[Type]] = {}
        self._initialize_type_cache()

        # Register serialization handlers for specific types
        self._type_handlers: Dict[Type, Callable[[Any], Any]] = {}
        self._register_handlers()

    def _initialize_type_cache(self) -> None:
        """
        Initialize cache for commonly used types.

        Pre-loads types that will be frequently serialized to avoid
        repeated import attempts and try-except blocks.
        """
        # Try to import TaskStarLine
        try:
            from galaxy.constellation.task_star_line import TaskStarLine

            self._cached_types["TaskStarLine"] = TaskStarLine
        except ImportError:
            self._cached_types["TaskStarLine"] = None
            self.logger.debug("TaskStarLine not available for serialization")

        # Try to import TaskConstellation
        try:
            from galaxy.constellation import TaskConstellation

            self._cached_types["TaskConstellation"] = TaskConstellation
        except ImportError:
            self._cached_types["TaskConstellation"] = None
            self.logger.debug("TaskConstellation not available for serialization")

    def _register_handlers(self) -> None:
        """
        Register type-specific serialization handlers.

        Maps Python types to their corresponding serialization functions
        for efficient lookup during serialization.
        """
        task_star_line_type = self._cached_types.get("TaskStarLine")
        if task_star_line_type:
            self._type_handlers[task_star_line_type] = self._serialize_task_star_line

        task_constellation_type = self._cached_types.get("TaskConstellation")
        if task_constellation_type:
            self._type_handlers[task_constellation_type] = self._serialize_constellation

    def serialize_event(self, event: Event) -> Dict[str, Any]:
        """
        Convert an Event object to a JSON-serializable dictionary.

        :param event: The event to convert
        :return: Dictionary representation of the event
        """
        # Build base dictionary with common fields
        base_dict = {
            "event_type": event.event_type.value,
            "source_id": event.source_id,
            "timestamp": event.timestamp,
            "data": self.serialize_value(event.data),
        }

        # Add type-specific fields using polymorphism
        if isinstance(event, TaskEvent):
            base_dict.update(self._serialize_task_event_fields(event))
        elif isinstance(event, ConstellationEvent):
            base_dict.update(self._serialize_constellation_event_fields(event))
        elif isinstance(event, AgentEvent):
            base_dict.update(self._serialize_agent_event_fields(event))
        elif isinstance(event, DeviceEvent):
            base_dict.update(self._serialize_device_event_fields(event))

        return base_dict

    def _serialize_task_event_fields(self, event: TaskEvent) -> Dict[str, Any]:
        """
        Extract task-specific fields from a TaskEvent.

        :param event: The task event to serialize
        :return: Dictionary of task-specific fields
        """
        return {
            "task_id": event.task_id,
            "status": event.status,
            "result": self.serialize_value(event.result),
            "error": str(event.error) if event.error else None,
        }

    def _serialize_constellation_event_fields(
        self, event: ConstellationEvent
    ) -> Dict[str, Any]:
        """
        Extract constellation-specific fields from a ConstellationEvent.

        :param event: The constellation event to serialize
        :return: Dictionary of constellation-specific fields
        """
        return {
            "constellation_id": event.constellation_id,
            "constellation_state": event.constellation_state,
            "new_ready_tasks": event.new_ready_tasks or [],
        }

    def _serialize_agent_event_fields(self, event: AgentEvent) -> Dict[str, Any]:
        """
        Extract agent-specific fields from an AgentEvent.

        :param event: The agent event to serialize
        :return: Dictionary of agent-specific fields
        """
        return {
            "agent_name": event.agent_name,
            "agent_type": event.agent_type,
            "output_type": event.output_type,
            "output_data": self.serialize_value(event.output_data),
        }

    def _serialize_device_event_fields(self, event: DeviceEvent) -> Dict[str, Any]:
        """
        Extract device-specific fields from a DeviceEvent.

        :param event: The device event to serialize
        :return: Dictionary of device-specific fields
        """
        return {
            "device_id": event.device_id,
            "device_status": event.device_status,
            "device_info": self.serialize_value(event.device_info),
            "all_devices": self.serialize_value(event.all_devices),
        }

    def serialize_value(self, value: Any) -> Any:
        """
        Serialize a value to JSON-compatible format.

        Handles various data types including primitives, collections, dataclasses,
        and custom Galaxy objects using a chain of serialization strategies.

        :param value: The value to serialize
        :return: JSON-serializable value
        """
        # Handle None early
        if value is None:
            return None

        # Handle primitive types
        if isinstance(value, (str, int, float, bool)):
            return value

        # Handle datetime objects
        if isinstance(value, datetime):
            return value.isoformat()

        # Handle collections - recursively serialize
        if isinstance(value, dict):
            return {k: self.serialize_value(v) for k, v in value.items()}

        if isinstance(value, (list, tuple)):
            return [self.serialize_value(item) for item in value]

        # Check registered type handlers first
        value_type = type(value)
        if value_type in self._type_handlers:
            return self._type_handlers[value_type](value)

        # Try dataclass serialization
        if is_dataclass(value) and not isinstance(value, type):
            try:
                return self.serialize_value(asdict(value))
            except (TypeError, ValueError) as e:
                self.logger.debug(f"Failed to serialize dataclass: {e}")

        # Try Pydantic model serialization
        if hasattr(value, "model_dump"):
            try:
                return self.serialize_value(value.model_dump())
            except Exception as e:
                self.logger.debug(f"Failed to serialize Pydantic model: {e}")

        # Try generic to_dict method
        if hasattr(value, "to_dict") and callable(value.to_dict):
            try:
                return self.serialize_value(value.to_dict())
            except Exception as e:
                self.logger.debug(f"Failed to serialize using to_dict: {e}")

        # Fallback to string representation
        return str(value)

    def _serialize_task_star_line(self, value: Any) -> Dict[str, Any]:
        """
        Serialize a TaskStarLine object.

        :param value: TaskStarLine instance
        :return: Serialized dictionary
        """
        try:
            return value.to_dict()
        except Exception as e:
            self.logger.warning(f"Failed to serialize TaskStarLine: {e}")
            return str(value)

    def _serialize_constellation(self, value: Any) -> Dict[str, Any]:
        """
        Serialize a TaskConstellation object.

        :param value: TaskConstellation instance
        :return: Serialized dictionary with constellation details
        """
        try:
            constellation_dict = {
                "constellation_id": value.constellation_id,
                "name": value.name,
                "state": self._extract_enum_value(value.state),
                "tasks": self._serialize_constellation_tasks(value.tasks),
                "dependencies": self._serialize_dependencies(
                    getattr(value, "dependencies", {})
                ),
                "metadata": self.serialize_value(getattr(value, "metadata", {})),
                "created_at": self._serialize_datetime(
                    getattr(value, "created_at", None)
                ),
            }

            # Add statistics if available
            if hasattr(value, "get_statistics") and callable(value.get_statistics):
                try:
                    constellation_dict["statistics"] = value.get_statistics()
                except Exception as e:
                    self.logger.warning(f"Failed to get constellation statistics: {e}")

            return constellation_dict
        except Exception as e:
            self.logger.warning(f"Failed to serialize TaskConstellation: {e}")
            return str(value)

    def _serialize_constellation_tasks(
        self, tasks: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Serialize all tasks in a constellation.

        :param tasks: Dictionary of task ID to task object
        :return: Dictionary of serialized tasks
        """
        serialized_tasks = {}
        for task_id, task in tasks.items():
            try:
                # Get tips directly from property
                task_tips = task.tips if hasattr(task, "tips") else None

                serialized_tasks[task_id] = {
                    "task_id": task.task_id,
                    "name": task.name,
                    "description": task.description,
                    "target_device_id": task.target_device_id,
                    "status": self._extract_enum_value(task.status),
                    "result": self.serialize_value(task.result),
                    "error": str(task.error) if task.error else None,
                    "input": self.serialize_value(getattr(task, "input", None)),
                    "output": self.serialize_value(getattr(task, "output", None)),
                    "tips": (
                        task_tips if task_tips else []
                    ),  # Always send array, never null
                    "started_at": self._serialize_datetime(
                        getattr(task, "execution_start_time", None)
                    ),
                    "completed_at": self._serialize_datetime(
                        getattr(task, "execution_end_time", None)
                    ),
                }
            except Exception as e:
                self.logger.warning(f"Failed to serialize task {task_id}: {e}")
                serialized_tasks[task_id] = {"task_id": task_id, "error": str(e)}

        return serialized_tasks

    def _serialize_dependencies(
        self, dependencies: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Convert TaskStarLine dependencies to frontend format.

        Frontend expects: { child_task_id: [parent_task_id_1, parent_task_id_2, ...] }
        Backend has: { line_id: TaskStarLine(from_task_id, to_task_id) }

        :param dependencies: Dictionary of TaskStarLine objects keyed by line_id
        :return: Dictionary mapping child task IDs to lists of parent task IDs
        """
        result: Dict[str, List[str]] = {}
        for dep in dependencies.values():
            try:
                # Each TaskStarLine has from_task_id (parent) and to_task_id (child)
                child_id = dep.to_task_id
                parent_id = dep.from_task_id

                if child_id not in result:
                    result[child_id] = []
                result[child_id].append(parent_id)
            except AttributeError as e:
                self.logger.debug(f"Failed to extract dependency IDs: {e}")
                continue

        return result

    @staticmethod
    def _extract_enum_value(value: Any) -> Any:
        """
        Extract the value from an enum, or return as string.

        :param value: Potential enum value
        :return: Enum value or string representation
        """
        return value.value if hasattr(value, "value") else str(value)

    @staticmethod
    def _serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
        """
        Serialize a datetime object to ISO format string.

        :param dt: Datetime object or None
        :return: ISO format string or None
        """
        return dt.isoformat() if dt is not None else None


class WebSocketObserver(IEventObserver):
    """
    Observer that forwards all Galaxy events to WebSocket clients.

    This observer maintains a set of active WebSocket connections and
    broadcasts events to all connected clients in real-time.
    """

    def __init__(self) -> None:
        """Initialize the WebSocket observer."""
        self.logger: logging.Logger = logging.getLogger(__name__)
        self._connections: Set[WebSocket] = set()
        self._event_count: int = 0
        self._serializer: EventSerializer = EventSerializer()

    async def on_event(self, event: Event) -> None:
        """
        Handle an event by broadcasting to all WebSocket clients.

        :param event: The event to broadcast
        """
        try:
            self._event_count += 1

            # Convert event to JSON-serializable format using the serializer
            event_data: Dict[str, Any] = self._serializer.serialize_event(event)

            self.logger.debug(
                f"Broadcasting event #{self._event_count}: {event.event_type.value} to {len(self._connections)} clients"
            )

            # Broadcast to all connected clients
            disconnected: Set[WebSocket] = set()
            for connection in self._connections:
                try:
                    await connection.send_json(event_data)
                    self.logger.debug(f"Successfully sent event to client")
                except Exception as e:
                    self.logger.warning(
                        f"Failed to send event to client: {e}, marking for removal"
                    )
                    disconnected.add(connection)

            # Remove disconnected clients
            self._connections -= disconnected

        except Exception as e:
            self.logger.error(f"Error broadcasting event: {e}")

    def add_connection(self, websocket: WebSocket) -> None:
        """
        Add a WebSocket connection to receive events.

        :param websocket: The WebSocket connection to add
        """
        self._connections.add(websocket)
        self.logger.info(
            f"WebSocket client connected. Total connections: {len(self._connections)}"
        )

    def remove_connection(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        :param websocket: The WebSocket connection to remove
        """
        self._connections.discard(websocket)
        self.logger.info(
            f"WebSocket client disconnected. Total connections: {len(self._connections)}"
        )

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)

    @property
    def total_events_sent(self) -> int:
        """Get the total number of events sent."""
        return self._event_count
