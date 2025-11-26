# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Agent Interaction Protocol (AIP)

A lightweight, persistent, and extensible messaging layer for multi-agent orchestration.

AIP provides:
- Long-lived agent sessions spanning multiple task executions
- Low-latency event propagation for dynamic scheduling
- Standardized communication for registration, task dispatch, and result reporting
- Resilient connection handling with automatic reconnection
- Extensible protocol with middleware support

Architecture:
    Messages (aip.messages) - Strongly-typed message definitions
    ↓
    Protocol (aip.protocol) - Protocol logic (registration, task execution, heartbeat)
    ↓
    Transport (aip.transport) - Transport abstraction (WebSocket, future: HTTP/3, gRPC)
    ↓
    Endpoints (aip.endpoints) - Endpoint implementations (Device Server, Device Client, Constellation)
    ↓
    Resilience (aip.resilience) - Reconnection, heartbeat, timeout management

Usage:
    # Device Server
    from aip.endpoints import DeviceServerEndpoint
    endpoint = DeviceServerEndpoint(ws_manager, session_manager)
    await endpoint.handle_websocket(websocket)

    # Device Client
    from aip.endpoints import DeviceClientEndpoint
    endpoint = DeviceClientEndpoint(ws_url, ufo_client)
    await endpoint.start()

    # Constellation Client
    from aip.endpoints import ConstellationEndpoint
    endpoint = ConstellationEndpoint(task_name, message_processor)
    await endpoint.connect_to_device(device_info, message_processor)
"""

from . import endpoints, extensions, messages, protocol, resilience, transport

__version__ = "1.0.0"

__all__ = [
    "messages",
    "transport",
    "protocol",
    "endpoints",
    "resilience",
    "extensions",
]

# Convenience exports
from .endpoints import (
    ConstellationEndpoint,
    DeviceClientEndpoint,
    DeviceServerEndpoint,
)
from .messages import (
    ClientMessage,
    ClientMessageType,
    ClientType,
    Command,
    Result,
    ResultStatus,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from .protocol import (
    AIPProtocol,
    CommandProtocol,
    DeviceInfoProtocol,
    HeartbeatProtocol,
    RegistrationProtocol,
    TaskExecutionProtocol,
)
from .resilience import HeartbeatManager, ReconnectionStrategy, TimeoutManager
from .transport import Transport, WebSocketTransport

__all__.extend(
    [
        # Messages
        "ClientMessage",
        "ServerMessage",
        "ClientMessageType",
        "ServerMessageType",
        "ClientType",
        "TaskStatus",
        "Command",
        "Result",
        "ResultStatus",
        # Transport
        "Transport",
        "WebSocketTransport",
        # Protocol
        "AIPProtocol",
        "RegistrationProtocol",
        "TaskExecutionProtocol",
        "HeartbeatProtocol",
        "DeviceInfoProtocol",
        "CommandProtocol",
        # Endpoints
        "DeviceServerEndpoint",
        "DeviceClientEndpoint",
        "ConstellationEndpoint",
        # Resilience
        "ReconnectionStrategy",
        "HeartbeatManager",
        "TimeoutManager",
    ]
)
