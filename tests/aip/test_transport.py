# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test AIP Transport Layer

Tests transport abstractions and WebSocket implementation.
"""

import asyncio

import pytest

from aip.transport import Transport, TransportState, WebSocketTransport


class MockTransport(Transport):
    """Mock transport for testing."""

    def __init__(self):
        super().__init__()
        self.sent_data = []
        self.receive_queue = asyncio.Queue()

    async def connect(self, url: str, **kwargs) -> None:
        """Mock connect."""
        self._state = TransportState.CONNECTED

    async def send(self, data: bytes) -> None:
        """Mock send."""
        if not self.is_connected:
            raise ConnectionError("Not connected")
        self.sent_data.append(data)

    async def receive(self) -> bytes:
        """Mock receive."""
        if not self.is_connected:
            raise ConnectionError("Not connected")
        return await self.receive_queue.get()

    async def close(self) -> None:
        """Mock close."""
        self._state = TransportState.DISCONNECTED

    async def wait_closed(self) -> None:
        """Mock wait_closed."""
        pass


class TestTransportBase:
    """Test transport base functionality."""

    @pytest.mark.asyncio
    async def test_transport_states(self):
        """Test transport state transitions."""
        transport = MockTransport()

        assert transport.state == TransportState.DISCONNECTED
        assert not transport.is_connected

        await transport.connect("test://localhost")
        assert transport.state == TransportState.CONNECTED
        assert transport.is_connected

        await transport.close()
        assert transport.state == TransportState.DISCONNECTED
        assert not transport.is_connected

    @pytest.mark.asyncio
    async def test_send_when_not_connected(self):
        """Test sending when not connected raises error."""
        transport = MockTransport()

        with pytest.raises(ConnectionError):
            await transport.send(b"test")

    @pytest.mark.asyncio
    async def test_receive_when_not_connected(self):
        """Test receiving when not connected raises error."""
        transport = MockTransport()

        with pytest.raises(ConnectionError):
            await transport.receive()

    @pytest.mark.asyncio
    async def test_send_receive_flow(self):
        """Test basic send/receive flow."""
        transport = MockTransport()
        await transport.connect("test://localhost")

        # Send data
        test_data = b"Hello, World!"
        await transport.send(test_data)

        assert test_data in transport.sent_data

        # Receive data
        await transport.receive_queue.put(test_data)
        received = await transport.receive()

        assert received == test_data


class TestWebSocketTransport:
    """Test WebSocket transport implementation."""

    def test_websocket_transport_init(self):
        """Test WebSocket transport initialization."""
        transport = WebSocketTransport(
            ping_interval=30.0,
            ping_timeout=180.0,
            max_size=100 * 1024 * 1024,
        )

        assert transport.ping_interval == 30.0
        assert transport.ping_timeout == 180.0
        assert transport.max_size == 100 * 1024 * 1024
        assert transport.state == TransportState.DISCONNECTED

    def test_websocket_transport_repr(self):
        """Test WebSocket transport string representation."""
        transport = WebSocketTransport()
        repr_str = repr(transport)

        assert "WebSocketTransport" in repr_str
        assert "disconnected" in repr_str.lower()

    @pytest.mark.asyncio
    async def test_websocket_idempotent_close(self):
        """Test WebSocket close is idempotent."""
        transport = WebSocketTransport()

        # Close multiple times should not raise error
        await transport.close()
        await transport.close()
        await transport.close()

        assert transport.state == TransportState.DISCONNECTED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
