# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
WebSocket Observer for Galaxy Web UI.

This observer subscribes to all Galaxy events and pushes them to connected WebSocket clients.
"""

import json
import logging
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

from galaxy.core.events import Event, IEventObserver


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

    async def on_event(self, event: Event) -> None:
        """
        Handle an event by broadcasting to all WebSocket clients.

        :param event: The event to broadcast
        """
        try:
            self._event_count += 1

            # Convert event to JSON-serializable format
            event_data: Dict[str, Any] = self._event_to_dict(event)

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

    def _event_to_dict(self, event: Event) -> Dict[str, Any]:
        """
        Convert an Event object to a JSON-serializable dictionary.

        :param event: The event to convert
        :return: Dictionary representation of the event
        """
        # Import here to avoid circular imports
        from galaxy.core.events import (
            AgentEvent,
            ConstellationEvent,
            DeviceEvent,
            TaskEvent,
        )

        base_dict = {
            "event_type": event.event_type.value,
            "source_id": event.source_id,
            "timestamp": event.timestamp,
            "data": self._serialize_value(event.data),  # Serialize data field
        }

        # Add type-specific fields
        if isinstance(event, TaskEvent):
            base_dict.update(
                {
                    "task_id": event.task_id,
                    "status": event.status,
                    "result": self._serialize_value(event.result),
                    "error": str(event.error) if event.error else None,
                }
            )
        elif isinstance(event, ConstellationEvent):
            base_dict.update(
                {
                    "constellation_id": event.constellation_id,
                    "constellation_state": event.constellation_state,
                    "new_ready_tasks": event.new_ready_tasks or [],
                }
            )
        elif isinstance(event, AgentEvent):
            base_dict.update(
                {
                    "agent_name": event.agent_name,
                    "agent_type": event.agent_type,
                    "output_type": event.output_type,
                    "output_data": self._serialize_value(
                        event.output_data
                    ),  # Serialize output_data
                }
            )
        elif isinstance(event, DeviceEvent):
            base_dict.update(
                {
                    "device_id": event.device_id,
                    "device_status": event.device_status,
                    "device_info": self._serialize_value(event.device_info),
                    "all_devices": self._serialize_value(event.all_devices),
                }
            )

        return base_dict

    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize a value to JSON-compatible format.

        Handles various data types including primitives, collections, dataclasses,
        TaskStarLine objects, and TaskConstellation objects.

        :param value: The value to serialize
        :return: JSON-serializable value
        """
        if value is None:
            return None

        # Handle common primitive types
        if isinstance(value, (str, int, float, bool)):
            return value

        # Handle dictionary - recursively serialize values
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}

        # Handle list/tuple - recursively serialize items
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]

        # Handle TaskStarLine objects
        try:
            from galaxy.constellation.task_star_line import TaskStarLine

            if isinstance(value, TaskStarLine):
                # Use the built-in to_dict method
                return value.to_dict()
        except ImportError:
            pass

        # Handle TaskConstellation objects
        try:
            from galaxy.constellation import TaskConstellation

            if isinstance(value, TaskConstellation):
                # Serialize constellation to dictionary with all relevant fields
                constellation_dict: Dict[str, Any] = {
                    "constellation_id": value.constellation_id,
                    "name": value.name,
                    "state": (
                        value.state.value
                        if hasattr(value.state, "value")
                        else str(value.state)
                    ),
                    "tasks": {
                        task_id: {
                            "task_id": task.task_id,
                            "name": task.name,
                            "description": task.description,
                            "target_device_id": task.target_device_id,
                            "status": (
                                task.status.value
                                if hasattr(task.status, "value")
                                else str(task.status)
                            ),
                            "result": self._serialize_value(task.result),
                            "error": str(task.error) if task.error else None,
                            "input": (
                                self._serialize_value(task.input)
                                if hasattr(task, "input")
                                else None
                            ),
                            "output": (
                                self._serialize_value(task.output)
                                if hasattr(task, "output")
                                else None
                            ),
                            "started_at": (
                                task.execution_start_time.isoformat()
                                if hasattr(task, "execution_start_time")
                                and task.execution_start_time
                                else None
                            ),
                            "completed_at": (
                                task.execution_end_time.isoformat()
                                if hasattr(task, "execution_end_time")
                                and task.execution_end_time
                                else None
                            ),
                        }
                        for task_id, task in value.tasks.items()
                    },
                    "dependencies": (
                        self._serialize_dependencies(value.dependencies)
                        if hasattr(value, "dependencies")
                        else {}
                    ),
                    "metadata": (
                        self._serialize_value(value.metadata)
                        if hasattr(value, "metadata")
                        else {}
                    ),
                    "created_at": (
                        value.created_at.isoformat()
                        if hasattr(value, "created_at") and value.created_at
                        else None
                    ),
                }

                # Add statistics if available
                if hasattr(value, "get_statistics"):
                    try:
                        constellation_dict["statistics"] = value.get_statistics()
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to get constellation statistics: {e}"
                        )

                return constellation_dict
        except ImportError:
            pass

        # Handle dataclasses
        if is_dataclass(value):
            try:
                return self._serialize_value(asdict(value))
            except Exception:
                pass

        # Try to convert to dict if object has model_dump (Pydantic models)
        if hasattr(value, "model_dump"):
            try:
                return self._serialize_value(value.model_dump())
            except Exception:
                pass

        # Try to convert to dict if object has to_dict method
        if hasattr(value, "to_dict"):
            try:
                return self._serialize_value(value.to_dict())
            except Exception:
                pass

        # Fallback to string representation
        return str(value)

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
        result = {}
        for dep in dependencies.values():
            # Each TaskStarLine has from_task_id (parent) and to_task_id (child)
            child_id = dep.to_task_id
            parent_id = dep.from_task_id

            if child_id not in result:
                result[child_id] = []
            result[child_id].append(parent_id)

        return result

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)

    @property
    def total_events_sent(self) -> int:
        """Get the total number of events sent."""
        return self._event_count
