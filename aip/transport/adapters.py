# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
WebSocket Adapter Interface

Provides a unified interface for different WebSocket implementations.
Uses the Adapter pattern to abstract away differences between:
- FastAPI WebSocket (server-side)
- websockets library (client-side)

Supports both text and binary frame transmission for efficient file transfer.
"""

from abc import ABC, abstractmethod
from typing import Union

from websockets import WebSocketClientProtocol


class WebSocketAdapter(ABC):
    """
    Abstract adapter for WebSocket operations.

    Provides a consistent interface regardless of the underlying WebSocket implementation.
    Supports both text frames (for JSON messages) and binary frames (for file transfer).
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
    async def send_bytes(self, data: bytes) -> None:
        """
        Send binary data through WebSocket.

        Sends data as a binary WebSocket frame for efficient transmission
        of images, files, and other binary content.

        :param data: Binary data to send
        :raises: Exception if send fails
        """
        pass

    @abstractmethod
    async def receive_bytes(self) -> bytes:
        """
        Receive binary data from WebSocket.

        Expects a binary WebSocket frame. Raises an error if a text frame is received.

        :return: Received binary data
        :raises: ValueError if a text frame is received instead of binary
        :raises: Exception if receive fails
        """
        pass

    @abstractmethod
    async def receive_auto(self) -> Union[str, bytes]:
        """
        Receive data and auto-detect frame type (text or binary).

        This method automatically detects whether the received WebSocket frame
        is text or binary and returns the appropriate type.

        :return: Received data (str for text frames, bytes for binary frames)
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
    Supports both text and binary frame transmission.
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

    async def send_bytes(self, data: bytes) -> None:
        """
        Send binary data via FastAPI WebSocket.

        FastAPI provides native send_bytes() method for binary frames.
        """
        await self._ws.send_bytes(data)

    async def receive_bytes(self) -> bytes:
        """
        Receive binary data via FastAPI WebSocket.

        FastAPI provides native receive_bytes() method.
        Raises an error if a text frame is received.
        """
        return await self._ws.receive_bytes()

    async def receive_auto(self) -> Union[str, bytes]:
        """
        Auto-detect and receive text or binary data.

        Uses FastAPI's receive() to get the raw message and extract
        the appropriate data type.
        """
        message = await self._ws.receive()
        if "text" in message:
            return message["text"]
        elif "bytes" in message:
            return message["bytes"]
        else:
            raise ValueError(f"Unknown WebSocket message type: {message}")

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
    Supports both text and binary frame transmission.
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

    async def send_bytes(self, data: bytes) -> None:
        """
        Send binary data via websockets library.

        The websockets library automatically detects bytes type and sends
        as a binary WebSocket frame.
        """
        await self._ws.send(data)

    async def receive_bytes(self) -> bytes:
        """
        Receive binary data via websockets library.

        Raises ValueError if a text frame is received instead of binary.
        """
        received = await self._ws.recv()
        if isinstance(received, str):
            raise ValueError(
                "Expected binary WebSocket frame, but received text frame. "
                f"Received data: {received[:100]}..."
            )
        return received

    async def receive_auto(self) -> Union[str, bytes]:
        """
        Auto-detect and receive text or binary data.

        The websockets library's recv() automatically returns the correct type
        (str for text frames, bytes for binary frames).
        """
        return await self._ws.recv()

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
