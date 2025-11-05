# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
WebSocket Adapter Interface

Provides a unified interface for different WebSocket implementations.
Uses the Adapter pattern to abstract away differences between:
- FastAPI WebSocket (server-side)
- websockets library (client-side)
"""

from abc import ABC, abstractmethod

from websockets import WebSocketClientProtocol


class WebSocketAdapter(ABC):
    """
    Abstract adapter for WebSocket operations.

    Provides a consistent interface regardless of the underlying WebSocket implementation.
    """

    @abstractmethod
    async def send(self, data: str) -> None:
        """
        Send text data through WebSocket.

        :param data: Text data to send
        :raises: Exception if send fails
        """
        pass

    @abstractmethod
    async def receive(self) -> str:
        """
        Receive text data from WebSocket.

        :return: Received text data
        :raises: Exception if receive fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the WebSocket connection.
        """
        pass

    @abstractmethod
    def is_open(self) -> bool:
        """
        Check if the WebSocket connection is open.

        :return: True if connection is open, False otherwise
        """
        pass


class FastAPIWebSocketAdapter(WebSocketAdapter):
    """
    Adapter for FastAPI/Starlette WebSocket (server-side).

    Used when the server accepts WebSocket connections from clients.
    """

    def __init__(self, websocket):
        """
        Initialize FastAPI WebSocket adapter.

        :param websocket: FastAPI WebSocket instance
        """
        from fastapi import WebSocket

        self._ws: WebSocket = websocket

    async def send(self, data: str) -> None:
        """Send text data via FastAPI WebSocket."""
        await self._ws.send_text(data)

    async def receive(self) -> str:
        """Receive text data via FastAPI WebSocket."""
        return await self._ws.receive_text()

    async def close(self) -> None:
        """Close FastAPI WebSocket connection."""
        await self._ws.close()

    def is_open(self) -> bool:
        """Check if FastAPI WebSocket is still connected."""
        from starlette.websockets import WebSocketState

        return self._ws.client_state == WebSocketState.CONNECTED


class WebSocketsLibAdapter(WebSocketAdapter):
    """
    Adapter for websockets library (client-side).

    Used when the client connects to a WebSocket server.
    """

    def __init__(self, websocket: WebSocketClientProtocol):
        """
        Initialize websockets library adapter.

        :param websocket: websockets library WebSocket instance
        """
        self._ws: WebSocketClientProtocol = websocket

    async def send(self, data: str) -> None:
        """Send text data via websockets library."""
        await self._ws.send(data)

    async def receive(self) -> str:
        """Receive data via websockets library (handles both text and bytes)."""
        received = await self._ws.recv()
        # websockets library can return either str or bytes
        if isinstance(received, bytes):
            return received.decode("utf-8")
        return received

    async def close(self) -> None:
        """Close websockets library connection."""
        await self._ws.close()

    def is_open(self) -> bool:
        """Check if websockets library connection is still open."""
        return not self._ws.closed


def create_adapter(websocket) -> WebSocketAdapter:
    """
    Factory function to create the appropriate WebSocket adapter.

    Auto-detects the WebSocket type and returns the correct adapter.

    :param websocket: Either FastAPI WebSocket or websockets library WebSocket
    :return: Appropriate adapter instance
    """
    # Check if it's a FastAPI WebSocket by looking for server-side attributes
    if hasattr(websocket, "client_state") or hasattr(websocket, "application_state"):
        return FastAPIWebSocketAdapter(websocket)
    else:
        return WebSocketsLibAdapter(websocket)
