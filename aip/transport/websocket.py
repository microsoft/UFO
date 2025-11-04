# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
WebSocket Transport Implementation

Implements the Transport interface using WebSockets.
Provides reliable, bidirectional, full-duplex communication over a single TCP connection.
"""

import asyncio
import logging
from typing import Optional

import websockets
from websockets import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException

from .base import Transport, TransportState


class WebSocketTransport(Transport):
    """
    WebSocket-based transport for AIP.

    Features:
    - Automatic ping/pong keepalive
    - Configurable timeouts
    - Large message support (up to 100MB by default)
    - Graceful connection shutdown

    Usage:
        transport = WebSocketTransport(ping_interval=30, ping_timeout=180)
        await transport.connect("ws://localhost:8000/ws")
        await transport.send(b"Hello")
        data = await transport.receive()
        await transport.close()
    """

    def __init__(
        self,
        ping_interval: float = 30.0,
        ping_timeout: float = 180.0,
        close_timeout: float = 10.0,
        max_size: int = 100 * 1024 * 1024,  # 100MB
    ):
        """
        Initialize WebSocket transport.

        :param ping_interval: Interval between ping messages (seconds)
        :param ping_timeout: Timeout for ping response (seconds)
        :param close_timeout: Timeout for graceful close (seconds)
        :param max_size: Maximum message size in bytes
        """
        super().__init__()
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.close_timeout = close_timeout
        self.max_size = max_size
        self._ws: Optional[WebSocketClientProtocol] = None
        self.logger = logging.getLogger(f"{__name__}.WebSocketTransport")

    async def connect(self, url: str, **kwargs) -> None:
        """
        Connect to WebSocket server.

        :param url: WebSocket URL (ws:// or wss://)
        :param kwargs: Additional parameters passed to websockets.connect()
        :raises: ConnectionError if connection fails
        """
        if self._state == TransportState.CONNECTED:
            self.logger.warning("Already connected, disconnecting first")
            await self.close()

        try:
            self._state = TransportState.CONNECTING
            self.logger.info(f"Connecting to {url}")

            # Merge user kwargs with defaults
            connect_params = {
                "ping_interval": self.ping_interval,
                "ping_timeout": self.ping_timeout,
                "close_timeout": self.close_timeout,
                "max_size": self.max_size,
            }
            connect_params.update(kwargs)

            self._ws = await websockets.connect(url, **connect_params)
            self._state = TransportState.CONNECTED
            self.logger.info(f"Connected to {url}")

        except WebSocketException as e:
            self._state = TransportState.ERROR
            self.logger.error(f"WebSocket error during connection: {e}")
            raise ConnectionError(f"Failed to connect to {url}: {e}") from e
        except OSError as e:
            self._state = TransportState.ERROR
            self.logger.error(f"Network error during connection: {e}")
            raise ConnectionError(f"Network error connecting to {url}: {e}") from e
        except Exception as e:
            self._state = TransportState.ERROR
            self.logger.error(f"Unexpected error during connection: {e}")
            raise ConnectionError(f"Unexpected error connecting to {url}: {e}") from e

    async def send(self, data: bytes) -> None:
        """
        Send data through WebSocket.

        :param data: Bytes to send
        :raises: ConnectionError if not connected
        :raises: IOError if send fails
        """
        if not self.is_connected or self._ws is None:
            raise ConnectionError("Transport not connected")

        try:
            await self._ws.send(data)
            self.logger.debug(f"Sent {len(data)} bytes")
        except ConnectionClosed as e:
            self._state = TransportState.DISCONNECTED
            self.logger.error(f"Connection closed during send: {e}")
            raise ConnectionError(f"Connection closed: {e}") from e
        except Exception as e:
            self._state = TransportState.ERROR
            self.logger.error(f"Error sending data: {e}")
            raise IOError(f"Failed to send data: {e}") from e

    async def receive(self) -> bytes:
        """
        Receive data from WebSocket.

        Blocks until data is available.

        :return: Received bytes
        :raises: ConnectionError if connection closed
        :raises: IOError if receive fails
        """
        if not self.is_connected or self._ws is None:
            raise ConnectionError("Transport not connected")

        try:
            data = await self._ws.recv()
            if isinstance(data, str):
                # Convert string to bytes
                data = data.encode("utf-8")
            self.logger.debug(f"Received {len(data)} bytes")
            return data
        except ConnectionClosed as e:
            self._state = TransportState.DISCONNECTED
            self.logger.error(f"Connection closed during receive: {e}")
            raise ConnectionError(f"Connection closed: {e}") from e
        except Exception as e:
            self._state = TransportState.ERROR
            self.logger.error(f"Error receiving data: {e}")
            raise IOError(f"Failed to receive data: {e}") from e

    async def close(self) -> None:
        """
        Close WebSocket connection gracefully.

        Idempotent - safe to call multiple times.
        """
        if self._state in (TransportState.DISCONNECTED, TransportState.DISCONNECTING):
            return

        try:
            self._state = TransportState.DISCONNECTING
            if self._ws is not None:
                await self._ws.close()
                self.logger.info("WebSocket closed")
        except Exception as e:
            self.logger.warning(f"Error during close: {e}")
        finally:
            self._state = TransportState.DISCONNECTED
            self._ws = None

    async def wait_closed(self) -> None:
        """
        Wait for WebSocket to fully close.

        Useful for graceful shutdown.
        """
        if self._ws is not None:
            await self._ws.wait_closed()
        self._state = TransportState.DISCONNECTED

    @property
    def websocket(self) -> Optional[WebSocketClientProtocol]:
        """
        Get the underlying WebSocket connection.

        :return: WebSocket connection or None if not connected
        """
        return self._ws

    def __repr__(self) -> str:
        """String representation."""
        return f"WebSocketTransport(state={self.state}, ping_interval={self.ping_interval})"
