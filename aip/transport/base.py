# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base Transport Interface

Defines the abstract interface for all AIP transports.
This allows AIP to work with different underlying communication mechanisms
while maintaining a consistent protocol layer.
"""

from abc import ABC, abstractmethod
from enum import Enum


class TransportState(str, Enum):
    """
    State of a transport connection.

    DISCONNECTED: Not connected
    CONNECTING: Connection in progress
    CONNECTED: Active connection
    DISCONNECTING: Graceful shutdown in progress
    ERROR: Transport error occurred
    """

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"


class Transport(ABC):
    """
    Abstract base class for AIP transports.

    A transport handles the low-level sending and receiving of messages
    between AIP endpoints. It abstracts away the specifics of the
    underlying communication channel (WebSocket, HTTP, gRPC, etc.).

    Implementations must be:
    - Asynchronous (use async/await)
    - Thread-safe for state queries
    - Resilient to transient errors
    """

    def __init__(self):
        """Initialize transport."""
        self._state: TransportState = TransportState.DISCONNECTED

    @property
    def state(self) -> TransportState:
        """Get current transport state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._state == TransportState.CONNECTED

    @abstractmethod
    async def connect(self, url: str, **kwargs) -> None:
        """
        Establish connection to the remote endpoint.

        :param url: Target URL/address
        :param kwargs: Transport-specific connection parameters
        :raises: ConnectionError if connection fails
        """
        pass

    @abstractmethod
    async def send(self, data: bytes) -> None:
        """
        Send data through the transport.

        :param data: Bytes to send
        :raises: ConnectionError if not connected
        :raises: IOError if send fails
        """
        pass

    @abstractmethod
    async def receive(self) -> bytes:
        """
        Receive data from the transport.

        Blocks until data is available.

        :return: Received bytes
        :raises: ConnectionError if connection closed
        :raises: IOError if receive fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the transport connection.

        Should be idempotent (safe to call multiple times).
        """
        pass

    @abstractmethod
    async def wait_closed(self) -> None:
        """
        Wait for transport to fully close.

        Useful for graceful shutdown.
        """
        pass

    def __repr__(self) -> str:
        """String representation of transport."""
        return f"{self.__class__.__name__}(state={self.state})"
