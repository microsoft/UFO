# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base AIP Endpoint

Provides the foundation for all AIP endpoint implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from aip.protocol import AIPProtocol
from aip.resilience import ReconnectionStrategy, TimeoutManager


class AIPEndpoint(ABC):
    """
    Abstract base class for AIP endpoints.

    An endpoint combines:
    - Protocol (message handling)
    - Session management (state tracking)
    - Resilience (reconnection, heartbeat, timeout)

    Subclasses implement specific endpoint types:
    - DeviceServerEndpoint: Server-side device connection management
    - DeviceClientEndpoint: Client-side device operations
    - ConstellationEndpoint: Constellation client operations
    """

    def __init__(
        self,
        protocol: AIPProtocol,
        reconnection_strategy: Optional[ReconnectionStrategy] = None,
        heartbeat_interval: float = 30.0,
        default_timeout: float = 120.0,
    ):
        """
        Initialize AIP endpoint.

        :param protocol: AIP protocol instance
        :param reconnection_strategy: Optional reconnection strategy
        :param heartbeat_interval: Heartbeat interval (seconds)
        :param default_timeout: Default timeout for operations (seconds)
        """
        self.protocol = protocol
        self.logger = logging.getLogger(self.__class__.__name__)

        # Resilience components
        self.reconnection_strategy = reconnection_strategy or ReconnectionStrategy()
        self.timeout_manager = TimeoutManager(default_timeout=default_timeout)

        # Session tracking
        self.session_handlers: Dict[str, Any] = {}

    @abstractmethod
    async def start(self) -> None:
        """
        Start the endpoint.

        Should establish connections, register handlers, and begin listening for messages.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the endpoint.

        Should gracefully close connections and cleanup resources.
        """
        pass

    @abstractmethod
    async def handle_message(self, msg: Any) -> None:
        """
        Handle an incoming message.

        :param msg: Message to handle
        """
        pass

    def is_connected(self) -> bool:
        """
        Check if endpoint is connected.

        :return: True if connected, False otherwise
        """
        return self.protocol.is_connected()

    async def send_with_timeout(
        self, msg: Any, timeout: Optional[float] = None
    ) -> None:
        """
        Send a message with timeout.

        :param msg: Message to send
        :param timeout: Optional timeout override
        """
        await self.timeout_manager.with_timeout(
            self.protocol.send_message(msg), timeout, "send_message"
        )

    async def receive_with_timeout(
        self, message_type: type, timeout: Optional[float] = None
    ) -> Any:
        """
        Receive a message with timeout.

        :param message_type: Expected message type
        :param timeout: Optional timeout override
        :return: Received message
        """
        return await self.timeout_manager.with_timeout(
            self.protocol.receive_message(message_type), timeout, "receive_message"
        )

    @abstractmethod
    async def reconnect_device(self, device_id: str) -> bool:
        """
        Attempt to reconnect to a device.

        :param device_id: Device to reconnect to
        :return: True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def cancel_device_tasks(self, device_id: str, reason: str) -> None:
        """
        Cancel all tasks for a device.

        :param device_id: Device ID
        :param reason: Cancellation reason
        """
        pass

    @abstractmethod
    async def on_device_disconnected(self, device_id: str) -> None:
        """
        Handle device disconnection notification.

        :param device_id: Disconnected device ID
        """
        pass
