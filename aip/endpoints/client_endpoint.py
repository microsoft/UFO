# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Device Client Endpoint

Wraps the existing UFO WebSocket client with AIP protocol abstractions.
"""

import logging
from typing import Any

from aip.endpoints.base import AIPEndpoint
from aip.protocol import AIPProtocol, HeartbeatProtocol, RegistrationProtocol
from aip.resilience import HeartbeatManager, ReconnectionStrategy
from aip.transport.websocket import WebSocketTransport


class DeviceClientEndpoint(AIPEndpoint):
    """
    Device Client endpoint for AIP.

    Wraps the existing UFOWebSocketClient to provide AIP protocol support
    while maintaining full backward compatibility.
    """

    def __init__(
        self,
        ws_url: str,
        ufo_client: Any,  # UFOClient
        max_retries: int = 3,
        timeout: float = 120.0,
    ):
        """
        Initialize device client endpoint.

        :param ws_url: WebSocket server URL
        :param ufo_client: UFOClient instance
        :param max_retries: Maximum reconnection retries
        :param timeout: Connection timeout
        """
        # Import here to avoid circular dependency
        from ufo.client.websocket import UFOWebSocketClient

        # Create transport and protocol
        transport = WebSocketTransport(
            ping_interval=20, ping_timeout=180, max_size=100 * 1024 * 1024
        )
        protocol = AIPProtocol(transport)

        # Create specialized protocols
        registration_protocol = RegistrationProtocol(transport)
        heartbeat_protocol = HeartbeatProtocol(transport)

        # Create reconnection strategy
        reconnection_strategy = ReconnectionStrategy(
            max_retries=max_retries,
            initial_backoff=2.0,
            max_backoff=60.0,
        )

        super().__init__(protocol=protocol, reconnection_strategy=reconnection_strategy)

        self.ws_url = ws_url
        self.ufo_client = ufo_client
        self.timeout = timeout

        # Use existing client for compatibility
        self.client = UFOWebSocketClient(ws_url, ufo_client, max_retries, timeout)

        # AIP-specific components
        self.registration_protocol = registration_protocol
        self.heartbeat_protocol = heartbeat_protocol
        self.heartbeat_manager = HeartbeatManager(heartbeat_protocol)

        self.logger = logging.getLogger(f"{__name__}.DeviceClientEndpoint")

    async def start(self) -> None:
        """
        Start the endpoint and connect to server.
        """
        self.logger.info(f"Starting device client endpoint: {self.ws_url}")

        # Use existing client's connection logic
        import asyncio

        asyncio.create_task(self.client.connect_and_listen())

        # Wait for connection
        await self.client.connected_event.wait()

        self.logger.info("Device client endpoint connected")

    async def stop(self) -> None:
        """Stop the endpoint."""
        self.logger.info("Stopping device client endpoint")

        # Stop heartbeat
        await self.heartbeat_manager.stop_all()

        # Close connection
        if self.client._ws:
            await self.client._ws.close()

        await self.protocol.close()
        self.logger.info("Device client endpoint stopped")

    async def handle_message(self, msg: Any) -> None:
        """
        Handle an incoming message.

        :param msg: Message to handle
        """
        # Messages are handled by the existing client
        await self.client.handle_message(msg)

    async def reconnect_device(self, device_id: str) -> bool:
        """
        Attempt to reconnect.

        :param device_id: Device ID (unused for client)
        :return: True if successful
        """
        try:
            await self.start()
            return True
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")
            return False

    async def cancel_device_tasks(self, device_id: str, reason: str) -> None:
        """
        Cancel device tasks.

        :param device_id: Device ID
        :param reason: Cancellation reason
        """
        # Client-side task cancellation handled by UFOClient
        self.logger.info(f"Cancelling tasks for {device_id}: {reason}")

    async def on_device_disconnected(self, device_id: str) -> None:
        """
        Handle disconnection.

        :param device_id: Device ID
        """
        self.logger.warning(f"Device disconnected: {device_id}")

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self.client.is_connected()
