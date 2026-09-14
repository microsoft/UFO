# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test AIP Transport Layer

Tests transport abstractions and WebSocket implementation.
"""

import asyncio
import socket
from http import HTTPStatus

import pytest
import websockets

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

    @pytest.mark.asyncio
    async def test_connect_pins_destination_and_preserves_tls_hostname(
        self, monkeypatch
    ):
        """Pinned WSS connections use the approved IP and original SNI."""
        connect_call = {}

        class WebSocket:
            remote_address = ("8.8.8.8", 8443)
            closed = False

        async def connect(url, **kwargs):
            connect_call["url"] = url
            connect_call["kwargs"] = kwargs
            return WebSocket()

        monkeypatch.setattr("aip.transport.websocket._PinnedWebSocketConnect", connect)

        transport = WebSocketTransport()
        await transport.connect(
            "wss://device.test:8443/ws", pinned_addresses=("8.8.8.8",)
        )

        assert connect_call["url"] == "wss://device.test:8443/ws"
        assert connect_call["kwargs"]["host"] == "8.8.8.8"
        assert connect_call["kwargs"]["server_hostname"] == "device.test"
        assert "pinned_addresses" not in connect_call["kwargs"]

    @pytest.mark.asyncio
    async def test_connect_rejects_peer_outside_pinned_addresses(self, monkeypatch):
        """A connection is rejected if its actual peer wasn't validated."""
        websocket = None

        class WebSocket:
            remote_address = ("127.0.0.1", 8443)
            closed = False

            async def close(self):
                self.closed = True

        async def connect(url, **kwargs):
            nonlocal websocket
            websocket = WebSocket()
            return websocket

        monkeypatch.setattr("aip.transport.websocket._PinnedWebSocketConnect", connect)

        transport = WebSocketTransport()
        with pytest.raises(ConnectionError, match="unexpected peer"):
            await transport.connect(
                "wss://device.test:8443/ws", pinned_addresses=("8.8.8.8",)
            )

        assert websocket.closed

    @pytest.mark.asyncio
    async def test_connect_with_pin_does_not_resolve_uri_hostname(self, monkeypatch):
        """The real websockets client bypasses DNS for a pinned URI host."""
        async with websockets.serve(lambda websocket, path: None, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            original_getaddrinfo = socket.getaddrinfo

            def reject_uri_hostname(host, *args, **kwargs):
                if host == "rebinding.test":
                    raise AssertionError("URI hostname was resolved")
                return original_getaddrinfo(host, *args, **kwargs)

            monkeypatch.setattr(socket, "getaddrinfo", reject_uri_hostname)

            transport = WebSocketTransport()
            await transport.connect(
                f"ws://rebinding.test:{port}/ws",
                pinned_addresses=("127.0.0.1",),
            )
            await transport.close()

    @pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
    @pytest.mark.parametrize("pinned", [True, False])
    @pytest.mark.asyncio
    async def test_connect_only_follows_redirects_without_pins(self, status, pinned):
        """Pinned redirects must fail before opening a connection to the target."""
        initial_requests = []
        target_connections = []
        target_requests = []

        async def record_request(reader, writer):
            target_connections.append(writer.get_extra_info("peername"))
            try:
                request = await asyncio.wait_for(
                    reader.readuntil(b"\r\n\r\n"), timeout=3
                )
                target_requests.append(request.split(b"\r\n", 1)[0])
                writer.write(
                    b"HTTP/1.1 400 Bad Request\r\n"
                    b"Content-Length: 0\r\nConnection: close\r\n\r\n"
                )
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()

        target = await asyncio.start_server(record_request, "127.0.0.2", 0)
        async with target:
            target_port = target.sockets[0].getsockname()[1]

            async def redirect_request(reader, writer):
                try:
                    request = await asyncio.wait_for(
                        reader.readuntil(b"\r\n\r\n"), timeout=3
                    )
                    initial_requests.append(request.split(b"\r\n", 1)[0])
                    writer.write(
                        (
                            f"HTTP/1.1 {status} Redirect\r\n"
                            f"Location: ws://127.0.0.2:{target_port}/audit-marker\r\n"
                            "Content-Length: 0\r\nConnection: close\r\n\r\n"
                        ).encode("ascii")
                    )
                    await writer.drain()
                finally:
                    writer.close()
                    await writer.wait_closed()

            initial = await asyncio.start_server(redirect_request, "127.0.0.1", 0)
            async with initial:
                initial_port = initial.sockets[0].getsockname()[1]
                transport = WebSocketTransport(close_timeout=1)
                try:
                    with pytest.raises(ConnectionError) as error:
                        await transport.connect(
                            f"ws://127.0.0.1:{initial_port}/ws",
                            pinned_addresses=("127.0.0.1",) if pinned else None,
                            open_timeout=3,
                        )

                    assert initial_requests == [b"GET /ws HTTP/1.1"]
                    assert transport.state == TransportState.ERROR
                    if pinned:
                        assert target_connections == []
                        assert target_requests == []
                        assert "redirect" in str(error.value).lower()
                    else:
                        assert len(target_connections) == 1
                        assert target_requests == [b"GET /audit-marker HTTP/1.1"]
                        assert "HTTP 400" in str(error.value)
                finally:
                    await transport.close()

    @pytest.mark.parametrize("absolute_location", [True, False])
    @pytest.mark.asyncio
    async def test_connect_with_pin_rejects_same_origin_redirects(
        self, absolute_location
    ):
        """Relative and absolute same-origin redirects must not send a second request."""
        requests = []

        async def process_request(path, headers):
            requests.append(path)
            if path == "/ws":
                location = (
                    f"ws://127.0.0.1:{port}/audit-marker"
                    if absolute_location
                    else "/audit-marker"
                )
                return HTTPStatus.FOUND, [("Location", location)], b""
            return HTTPStatus.BAD_REQUEST, [], b""

        async def handle_connection(websocket, path):
            await websocket.wait_closed()

        async with websockets.serve(
            handle_connection, "127.0.0.1", 0, process_request=process_request
        ) as server:
            port = server.sockets[0].getsockname()[1]
            transport = WebSocketTransport(close_timeout=1)
            try:
                with pytest.raises(ConnectionError) as error:
                    await transport.connect(
                        f"ws://127.0.0.1:{port}/ws",
                        pinned_addresses=("127.0.0.1",),
                        open_timeout=3,
                    )

                assert requests == ["/ws"]
                assert transport.state == TransportState.ERROR
                assert "redirect" in str(error.value).lower()
            finally:
                await transport.close()

    @pytest.mark.asyncio
    async def test_galaxy_connection_manager_forwards_profile_pinned_addresses(
        self, monkeypatch
    ):
        """Galaxy connections consume the address snapshot stored at validation."""
        from galaxy.client.components.connection_manager import (
            WebSocketConnectionManager,
        )
        from galaxy.client.components.types import AgentProfile

        connect_call = {}

        class Transport:
            def __init__(self, **kwargs):
                pass

            async def connect(self, url, **kwargs):
                connect_call["url"] = url
                connect_call["kwargs"] = kwargs

        class MessageProcessor:
            def start_message_handler(self, device_id, transport):
                pass

        async def registration_succeeds(device_info):
            return True

        monkeypatch.setattr(
            "galaxy.client.components.connection_manager.WebSocketTransport",
            Transport,
        )

        manager = WebSocketConnectionManager("test-task")
        monkeypatch.setattr(
            manager, "_register_constellation_client", registration_succeeds
        )
        profile = AgentProfile(
            device_id="device-1",
            server_url="wss://device.test:8443/ws",
            pinned_addresses=("8.8.8.8",),
        )

        await manager.connect_to_device(profile, MessageProcessor())

        assert connect_call == {
            "url": "wss://device.test:8443/ws",
            "kwargs": {"pinned_addresses": ("8.8.8.8",)},
        }

    @pytest.mark.parametrize("pinned_addresses", [None, ()])
    @pytest.mark.asyncio
    async def test_galaxy_connection_manager_pins_unpinned_profile(
        self, monkeypatch, pinned_addresses
    ):
        """Legacy profiles are resolved before the transport can connect."""
        from galaxy.client.components.connection_manager import (
            WebSocketConnectionManager,
        )
        from galaxy.client.components.types import AgentProfile

        connect_call = {}

        class Transport:
            def __init__(self, **kwargs):
                pass

            async def connect(self, url, **kwargs):
                connect_call["url"] = url
                connect_call["kwargs"] = kwargs

        class MessageProcessor:
            def start_message_handler(self, device_id, transport):
                pass

        async def registration_succeeds(device_info):
            return True

        public_result = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", 0),
            )
        ]
        monkeypatch.setattr(socket, "getaddrinfo", lambda *args: public_result)
        monkeypatch.setattr(
            "galaxy.client.components.connection_manager.WebSocketTransport",
            Transport,
        )

        manager = WebSocketConnectionManager("test-task")
        monkeypatch.setattr(
            manager, "_register_constellation_client", registration_succeeds
        )
        profile = AgentProfile(
            device_id="legacy-device",
            server_url="wss://device.test:8443/ws",
            pinned_addresses=pinned_addresses,
        )

        await manager.connect_to_device(profile, MessageProcessor())

        assert connect_call == {
            "url": "wss://device.test:8443/ws",
            "kwargs": {"pinned_addresses": ("8.8.8.8",)},
        }

    @pytest.mark.asyncio
    async def test_galaxy_connection_manager_rejects_unpinned_blocked_address(
        self, monkeypatch
    ):
        """Legacy profiles cannot resolve to a blocked destination."""
        from galaxy.client.components.connection_manager import (
            WebSocketConnectionManager,
        )
        from galaxy.client.components.types import AgentProfile
        from galaxy.webui.security import ServerUrlValidationError

        connect_calls = []

        class Transport:
            def __init__(self, **kwargs):
                pass

            async def connect(self, url, **kwargs):
                connect_calls.append((url, kwargs))

        class MessageProcessor:
            def start_message_handler(self, device_id, transport):
                pass

        async def registration_succeeds(device_info):
            return True

        loopback_result = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("127.0.0.1", 0),
            )
        ]
        monkeypatch.setattr(socket, "getaddrinfo", lambda *args: loopback_result)
        monkeypatch.setattr(
            "galaxy.client.components.connection_manager.WebSocketTransport",
            Transport,
        )

        manager = WebSocketConnectionManager("test-task")
        monkeypatch.setattr(
            manager, "_register_constellation_client", registration_succeeds
        )
        profile = AgentProfile(
            device_id="legacy-device",
            server_url="wss://device.test:8443/ws",
        )

        with pytest.raises(ServerUrlValidationError, match="loopback"):
            await manager.connect_to_device(profile, MessageProcessor())

        assert connect_calls == []

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
