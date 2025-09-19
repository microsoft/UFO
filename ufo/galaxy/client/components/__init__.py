# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Device Manager Components

This package contains the modular components that make up the Constellation Device Manager:
- DeviceRegistry: Device registration and information management
- WebSocketConnectionManager: WebSocket connection management
- HeartbeatManager: Device health monitoring
- EventManager: Event handling and callbacks
- MessageProcessor: Message handling and routing
"""

from .types import DeviceStatus, DeviceInfo, TaskRequest, DeviceEventHandler
from .device_registry import DeviceRegistry
from .connection_manager import WebSocketConnectionManager
from .heartbeat_manager import HeartbeatManager
from .event_manager import EventManager
from .message_processor import MessageProcessor

__all__ = [
    "DeviceStatus",
    "DeviceInfo",
    "TaskRequest",
    "DeviceEventHandler",
    "DeviceRegistry",
    "WebSocketConnectionManager",
    "HeartbeatManager",
    "EventManager",
    "MessageProcessor",
]
