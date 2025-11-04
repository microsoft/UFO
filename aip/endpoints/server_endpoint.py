# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Device Server Endpoint

Wraps the existing UFO server WebSocket handler with AIP protocol abstractions.
This maintains backward compatibility while providing the AIP interface.
"""

import logging
from typing import Any, Optional

from fastapi import WebSocket

from aip.endpoints.base import AIPEndpoint
from aip.protocol import AIPProtocol
from aip.resilience import ReconnectionStrategy


class DeviceServerEndpoint(AIPEndpoint):
    """
    Device Server endpoint for AIP.

    Wraps the existing UFOWebSocketHandler to provide AIP protocol support
    while maintaining full backward compatibility with existing implementations.
    """

    def __init__(
        self,
        ws_manager: Any,  # WSManager
        session_manager: Any,  # SessionManager
        local: bool = False,
        protocol: Optional[AIPProtocol] = None,
        reconnection_strategy: Optional[ReconnectionStrategy] = None,
    ):
        """
        Initialize device server endpoint.

        :param ws_manager: WebSocket manager instance
        :param session_manager: Session manager instance
        :param local: Whether running in local mode
        :param protocol: Optional AIP protocol instance
        :param reconnection_strategy: Optional reconnection strategy
        """
        # Import here to avoid circular dependency
        from ufo.server.ws.handler import UFOWebSocketHandler

        if protocol is None:
            # Create a minimal protocol for compatibility
            from aip.transport.websocket import WebSocketTransport

            protocol = AIPProtocol(WebSocketTransport())

        super().__init__(protocol=protocol, reconnection_strategy=reconnection_strategy)

        self.ws_manager = ws_manager
        self.session_manager = session_manager
        self.local = local

        # Use existing handler for actual implementation
        self.handler = UFOWebSocketHandler(ws_manager, session_manager, local)

        self.logger = logging.getLogger(f"{__name__}.DeviceServerEndpoint")

    async def start(self) -> None:
        """
        Start the endpoint.

        Note: For server endpoints, connections are handled per WebSocket.
        """
        self.logger.info("Device server endpoint ready")

    async def stop(self) -> None:
        """Stop the endpoint."""
        self.logger.info("Device server endpoint stopped")

    async def handle_websocket(self, websocket: WebSocket) -> None:
        """
        Handle a WebSocket connection.

        This delegates to the existing UFOWebSocketHandler for full compatibility.

        :param websocket: WebSocket connection
        """
        await self.handler.handler(websocket)

    async def handle_message(self, msg: Any) -> None:
        """
        Handle an incoming message.

        :param msg: Message to handle
        """
        # Messages are handled within the handler per connection
        pass

    async def reconnect_device(self, device_id: str) -> bool:
        """
        Server-side reconnection is handled by client reconnecting.

        :param device_id: Device ID
        :return: False (server waits for client)
        """
        self.logger.debug(f"Server endpoint does not actively reconnect to {device_id}")
        return False

    async def cancel_device_tasks(self, device_id: str, reason: str) -> None:
        """
        Cancel all tasks for a device.

        :param device_id: Device ID
        :param reason: Cancellation reason
        """
        session_ids = self.ws_manager.get_device_sessions(device_id)
        for session_id in session_ids:
            try:
                await self.session_manager.cancel_task(session_id, reason=reason)
            except Exception as e:
                self.logger.error(f"Error cancelling session {session_id}: {e}")

    async def on_device_disconnected(self, device_id: str) -> None:
        """
        Handle device disconnection notification.

        :param device_id: Disconnected device ID
        """
        self.logger.info(f"Device {device_id} disconnected")
