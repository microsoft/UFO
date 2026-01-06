# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation Client Endpoint

Wraps the existing Galaxy constellation client with AIP protocol abstractions.
"""

import logging
from typing import Any, Dict, Optional

from aip.endpoints.base import AIPEndpoint
from aip.protocol import AIPProtocol, RegistrationProtocol
from aip.resilience import ReconnectionStrategy
from aip.transport.websocket import WebSocketTransport


class ConstellationEndpoint(AIPEndpoint):
    """
    Constellation Client endpoint for AIP.

    Wraps the existing WebSocketConnectionManager to provide AIP protocol support.
    """

    def __init__(
        self,
        task_name: str,
        message_processor: Any = None,  # MessageProcessor
    ):
        """
        Initialize constellation endpoint.

        :param task_name: Task name for this constellation
        :param message_processor: Optional message processor
        """
        # Create transport and protocol
        transport = WebSocketTransport(
            ping_interval=30, ping_timeout=30, max_size=100 * 1024 * 1024
        )
        protocol = AIPProtocol(transport)

        # Create registration protocol
        registration_protocol = RegistrationProtocol(transport)

        # Create reconnection strategy
        reconnection_strategy = ReconnectionStrategy(
            max_retries=5, initial_backoff=1.0, max_backoff=60.0
        )

        super().__init__(protocol=protocol, reconnection_strategy=reconnection_strategy)

        self.task_name = task_name
        self.message_processor = message_processor
        self.registration_protocol = registration_protocol

        # Import here to avoid circular dependency
        from galaxy.client.components.connection_manager import (
            WebSocketConnectionManager,
        )

        self.connection_manager = WebSocketConnectionManager(task_name)

        self.logger = logging.getLogger(f"{__name__}.ConstellationEndpoint")

    async def start(self) -> None:
        """Start the endpoint."""
        self.logger.info(f"Constellation endpoint started for {self.task_name}")

    async def stop(self) -> None:
        """Stop the endpoint and disconnect all devices."""
        self.logger.info("Stopping constellation endpoint")
        await self.connection_manager.disconnect_all()
        await self.protocol.close()

    async def connect_to_device(
        self, device_info: Any, message_processor: Any = None
    ) -> Any:
        """
        Connect to a device.

        :param device_info: AgentProfile with device information
        :param message_processor: Optional message processor
        :return: WebSocket connection
        """
        processor = message_processor or self.message_processor
        return await self.connection_manager.connect_to_device(device_info, processor)

    async def send_task_to_device(self, device_id: str, task_request: Any) -> Any:
        """
        Send task to device.

        :param device_id: Target device ID
        :param task_request: Task request details
        :return: Execution result
        """
        return await self.connection_manager.send_task_to_device(
            device_id, task_request
        )

    async def request_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Request device information.

        :param device_id: Device ID
        :return: Device info dictionary or None
        """
        return await self.connection_manager.request_device_info(device_id)

    async def disconnect_device(self, device_id: str) -> None:
        """
        Disconnect from a device.

        :param device_id: Device ID
        """
        await self.connection_manager.disconnect_device(device_id)

    def is_device_connected(self, device_id: str) -> bool:
        """
        Check if device is connected.

        :param device_id: Device ID
        :return: True if connected
        """
        return self.connection_manager.is_connected(device_id)

    async def handle_message(self, msg: Any) -> None:
        """
        Handle incoming message.

        :param msg: Message to handle
        """
        # Messages handled by message processor
        if self.message_processor:
            await self.message_processor.process_message(msg)

    async def reconnect_device(self, device_id: str) -> bool:
        """
        Attempt to reconnect to device.

        :param device_id: Device ID
        :return: True if successful
        """
        try:
            # Get device info from somewhere
            # This would need to be implemented based on available device registry
            self.logger.warning(f"Reconnection for {device_id} not fully implemented")
            return False
        except Exception as e:
            self.logger.error(f"Reconnection failed for {device_id}: {e}")
            return False

    async def cancel_device_tasks(self, device_id: str, reason: str) -> None:
        """
        Cancel tasks for device.

        :param device_id: Device ID
        :param reason: Cancellation reason
        """
        # Cancel pending tasks managed by connection manager
        self.connection_manager._cancel_pending_tasks_for_device(device_id)
        self.logger.info(f"Cancelled tasks for {device_id}: {reason}")

    async def on_device_disconnected(self, device_id: str) -> None:
        """
        Handle device disconnection.

        :param device_id: Device ID
        """
        self.logger.warning(f"Device {device_id} disconnected from constellation")
        await self.cancel_device_tasks(device_id, "device_disconnected")
