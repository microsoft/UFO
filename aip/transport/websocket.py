# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
WebSocket Transport Implementation

Implements the Transport interface using WebSockets.
Provides reliable, bidirectional, full-duplex communication over a single TCP connection.
Supports both text frames (for JSON messages) and binary frames (for efficient file transfer).
"""

import asyncio
import logging
from typing import Optional, Union

import websockets
from websockets import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException

from .adapters import WebSocketAdapter, create_adapter
from .base import Transport, TransportState


class WebSocketTransport(Transport):
    """
    WebSocket-based transport for AIP.

    Features:
    - Automatic ping/pong keepalive
    - Configurable timeouts
    - Large message support (up to 100MB by default)
    - Graceful connection shutdown
    - Text and binary frame support for efficient data transfer

    Usage:
        # Text messages (JSON)
        transport = WebSocketTransport(ping_interval=30, ping_timeout=180)
        await transport.connect("ws://localhost:8000/ws")
        await transport.send(b"Hello")
        data = await transport.receive()

        # Binary data (files, images)
        await transport.send_binary(image_bytes)
        binary_data = await transport.receive_binary()

        # Auto-detect frame type
        data = await transport.receive_auto()  # Returns str or bytes

        await transport.close()
    """

    def __init__(
        self,
        websocket=None,  # Accept existing WebSocket (FastAPI server-side)
        ping_interval: float = 30.0,
        ping_timeout: float = 180.0,
        close_timeout: float = 10.0,
        max_size: int = 100 * 1024 * 1024,  # 100MB
    ):
        """
        Initialize WebSocket transport.

        :param websocket: Optional existing WebSocket connection (for server-side use)
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
        self._adapter: Optional[WebSocketAdapter] = None
        self.logger = logging.getLogger(f"{__name__}.WebSocketTransport")

        # If websocket provided (server-side), create adapter and mark as connected
        if websocket is not None:
            self._ws = websocket
            self._adapter = create_adapter(websocket)
            self._state = TransportState.CONNECTED
            adapter_type = type(self._adapter).__name__
            self.logger.info(
                f"WebSocket transport initialized with existing connection ({adapter_type})"
            )

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
            self._adapter = create_adapter(self._ws)
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
        if not self.is_connected or self._adapter is None:
            raise ConnectionError("Transport not connected")

        # Check if WebSocket is still open using adapter
        if not self._adapter.is_open():
            self._state = TransportState.DISCONNECTED
            raise ConnectionError("WebSocket connection is closed")

        try:
            # Convert bytes to text for consistent transport (JSON messages are text-based)
            text_data = data.decode("utf-8") if isinstance(data, bytes) else data

            adapter_type = type(self._adapter).__name__
            self.logger.debug(f"Sending {len(text_data)} chars via {adapter_type}")

            # Use adapter to send (abstracts away FastAPI vs websockets library)
            await self._adapter.send(text_data)

            self.logger.debug(f"✅ Sent {len(text_data)} chars successfully")
        except ConnectionClosed as e:
            self._state = TransportState.DISCONNECTED
            self.logger.debug(f"Connection closed during send: {e}")
            raise ConnectionError(f"Connection closed: {e}") from e
        except (ConnectionError, OSError) as e:
            self._state = TransportState.ERROR
            # Check if this is a normal disconnection scenario
            error_msg = str(e).lower()
            if "closed" in error_msg or "not connected" in error_msg:
                self.logger.debug(f"Cannot send (connection closed): {e}")
            else:
                self.logger.warning(f"Connection error sending data: {e}")
            raise IOError(f"Failed to send data: {e}") from e
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
        if not self.is_connected or self._adapter is None:
            raise ConnectionError("Transport not connected")

        try:
            adapter_type = type(self._adapter).__name__
            self.logger.debug(f"🔍 Attempting to receive data via {adapter_type}...")

            # Use adapter to receive (abstracts away FastAPI vs websockets library)
            text_data = await self._adapter.receive()
            data = text_data.encode("utf-8")

            self.logger.debug(f"✅ Received {len(data)} bytes successfully")
            return data
        except ConnectionClosed as e:
            self._state = TransportState.DISCONNECTED
            self.logger.debug(f"Connection closed during receive: {e}")
            raise ConnectionError(f"Connection closed: {e}") from e
        except (ConnectionError, OSError) as e:
            self._state = TransportState.ERROR
            # Check if this is a normal disconnection scenario
            error_msg = str(e).lower()
            if "closed" in error_msg or "not connected" in error_msg:
                self.logger.debug(f"Cannot receive (connection closed): {e}")
            else:
                self.logger.warning(f"Connection error receiving data: {e}")
            raise IOError(f"Failed to receive data: {e}") from e
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
            if self._adapter is not None:
                await self._adapter.close()
                self.logger.info("WebSocket closed")
        except Exception as e:
            self.logger.warning(f"Error during close: {e}")
        finally:
            self._state = TransportState.DISCONNECTED
            self._ws = None
            self._adapter = None

    async def wait_closed(self) -> None:
        """
        Wait for WebSocket to fully close.

        Useful for graceful shutdown.
        """
        if self._ws is not None:
            await self._ws.wait_closed()
        self._state = TransportState.DISCONNECTED

    async def send_binary(self, data: bytes) -> None:
        """
        Send binary data through WebSocket as a binary frame.

        This method sends raw binary data (images, files, etc.) without
        text encoding overhead, providing maximum efficiency for binary transfers.

        :param data: Binary bytes to send
        :raises: ConnectionError if not connected
        :raises: IOError if send fails

        Example:
            # Send an image file
            with open("screenshot.png", "rb") as f:
                image_data = f.read()
            await transport.send_binary(image_data)
        """
        if not self.is_connected or self._adapter is None:
            raise ConnectionError("Transport not connected")

        if not self._adapter.is_open():
            self._state = TransportState.DISCONNECTED
            raise ConnectionError("WebSocket connection is closed")

        try:
            adapter_type = type(self._adapter).__name__
            self.logger.debug(
                f"Sending {len(data)} bytes (binary frame) via {adapter_type}"
            )

            await self._adapter.send_bytes(data)

            self.logger.debug(f"✅ Sent {len(data)} bytes successfully")
        except ConnectionClosed as e:
            self._state = TransportState.DISCONNECTED
            self.logger.debug(f"Connection closed during binary send: {e}")
            raise ConnectionError(f"Connection closed: {e}") from e
        except (ConnectionError, OSError) as e:
            self._state = TransportState.ERROR
            error_msg = str(e).lower()
            if "closed" in error_msg or "not connected" in error_msg:
                self.logger.debug(f"Cannot send binary (connection closed): {e}")
            else:
                self.logger.warning(f"Connection error sending binary data: {e}")
            raise IOError(f"Failed to send binary data: {e}") from e
        except Exception as e:
            self._state = TransportState.ERROR
            self.logger.error(f"Error sending binary data: {e}")
            raise IOError(f"Failed to send binary data: {e}") from e

    async def receive_binary(self) -> bytes:
        """
        Receive binary data from WebSocket as a binary frame.

        This method expects a binary WebSocket frame and returns raw bytes.
        Raises an error if a text frame is received.

        :return: Received binary bytes
        :raises: ConnectionError if connection closed
        :raises: ValueError if a text frame is received instead of binary
        :raises: IOError if receive fails

        Example:
            # Receive a binary file
            file_data = await transport.receive_binary()
            with open("received_file.bin", "wb") as f:
                f.write(file_data)
        """
        if not self.is_connected or self._adapter is None:
            raise ConnectionError("Transport not connected")

        try:
            adapter_type = type(self._adapter).__name__
            self.logger.debug(
                f"🔍 Attempting to receive binary data via {adapter_type}..."
            )

            data = await self._adapter.receive_bytes()

            self.logger.debug(f"✅ Received {len(data)} bytes successfully")
            return data
        except ConnectionClosed as e:
            self._state = TransportState.DISCONNECTED
            self.logger.debug(f"Connection closed during binary receive: {e}")
            raise ConnectionError(f"Connection closed: {e}") from e
        except ValueError as e:
            # Raised when expecting binary but got text frame
            self.logger.error(f"Frame type mismatch: {e}")
            raise
        except (ConnectionError, OSError) as e:
            self._state = TransportState.ERROR
            error_msg = str(e).lower()
            if "closed" in error_msg or "not connected" in error_msg:
                self.logger.debug(f"Cannot receive binary (connection closed): {e}")
            else:
                self.logger.warning(f"Connection error receiving binary data: {e}")
            raise IOError(f"Failed to receive binary data: {e}") from e
        except Exception as e:
            self._state = TransportState.ERROR
            self.logger.error(f"Error receiving binary data: {e}")
            raise IOError(f"Failed to receive binary data: {e}") from e

    async def receive_auto(self) -> Union[bytes, str]:
        """
        Receive data and automatically detect frame type (text or binary).

        This method receives a WebSocket frame and returns the appropriate type:
        - str for text frames (JSON messages)
        - bytes for binary frames (files, images)

        :return: Received data (str for text frames, bytes for binary frames)
        :raises: ConnectionError if connection closed
        :raises: IOError if receive fails

        Example:
            data = await transport.receive_auto()
            if isinstance(data, bytes):
                # Handle binary data
                print(f"Received {len(data)} bytes")
            else:
                # Handle text data
                message = json.loads(data)
        """
        if not self.is_connected or self._adapter is None:
            raise ConnectionError("Transport not connected")

        try:
            adapter_type = type(self._adapter).__name__
            self.logger.debug(
                f"🔍 Attempting to receive data (auto-detect) via {adapter_type}..."
            )

            data = await self._adapter.receive_auto()

            if isinstance(data, bytes):
                self.logger.debug(
                    f"✅ Received {len(data)} bytes (binary frame) successfully"
                )
            else:
                self.logger.debug(
                    f"✅ Received {len(data)} chars (text frame) successfully"
                )

            return data
        except ConnectionClosed as e:
            self._state = TransportState.DISCONNECTED
            self.logger.debug(f"Connection closed during receive: {e}")
            raise ConnectionError(f"Connection closed: {e}") from e
        except (ConnectionError, OSError) as e:
            self._state = TransportState.ERROR
            error_msg = str(e).lower()
            if "closed" in error_msg or "not connected" in error_msg:
                self.logger.debug(f"Cannot receive (connection closed): {e}")
            else:
                self.logger.warning(f"Connection error receiving data: {e}")
            raise IOError(f"Failed to receive data: {e}") from e
        except Exception as e:
            self._state = TransportState.ERROR
            self.logger.error(f"Error receiving data: {e}")
            raise IOError(f"Failed to receive data: {e}") from e

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
