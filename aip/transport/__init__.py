# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
AIP Transport Layer

Provides transport abstractions for the Agent Interaction Protocol.
Supports WebSocket and is extensible to other transports (HTTP/3, gRPC, etc.).
"""

from .adapters import (
    FastAPIWebSocketAdapter,
    WebSocketAdapter,
    WebSocketsLibAdapter,
    create_adapter,
)
from .base import Transport, TransportState
from .websocket import WebSocketTransport

__all__ = [
    "Transport",
    "TransportState",
    "WebSocketTransport",
    "WebSocketAdapter",
    "FastAPIWebSocketAdapter",
    "WebSocketsLibAdapter",
    "create_adapter",
]
