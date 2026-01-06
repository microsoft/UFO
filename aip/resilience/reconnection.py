# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Reconnection Strategy

Implements automatic reconnection with exponential backoff for handling
transient network failures and connection interruptions.
"""

import asyncio
import logging
from enum import Enum
from typing import TYPE_CHECKING, Awaitable, Callable, Optional

if TYPE_CHECKING:
    from aip.endpoints.base import AIPEndpoint


class ReconnectionPolicy(str, Enum):
    """Reconnection policies."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE = "immediate"
    NONE = "none"


class ReconnectionStrategy:
    """
    Manages automatic reconnection for AIP endpoints.

    Features:
    - Exponential backoff
    - Configurable retry limits
    - Connection state callbacks
    - Task cancellation on disconnect
    """

    def __init__(
        self,
        max_retries: int = 5,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        backoff_multiplier: float = 2.0,
        policy: ReconnectionPolicy = ReconnectionPolicy.EXPONENTIAL_BACKOFF,
    ):
        """
        Initialize reconnection strategy.

        :param max_retries: Maximum number of reconnection attempts
        :param initial_backoff: Initial backoff time (seconds)
        :param max_backoff: Maximum backoff time (seconds)
        :param backoff_multiplier: Multiplier for exponential backoff
        :param policy: Reconnection policy
        """
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_multiplier = backoff_multiplier
        self.policy = policy
        self.logger = logging.getLogger(f"{__name__}.ReconnectionStrategy")

        self._retry_count = 0
        self._reconnection_task: Optional[asyncio.Task] = None

    async def handle_disconnection(
        self,
        endpoint: "AIPEndpoint",
        device_id: str,
        on_reconnect: Optional[Callable[[], Awaitable[None]]] = None,
    ) -> None:
        """
        Handle device disconnection with automatic reconnection.

        Workflow:
        1. Cancel all pending tasks for the device
        2. Notify upper layers of disconnection
        3. Attempt reconnection with backoff
        4. Call on_reconnect callback if successful

        :param endpoint: AIP endpoint managing the connection
        :param device_id: Device that disconnected
        :param on_reconnect: Optional callback after successful reconnection
        """
        self.logger.warning(f"Device {device_id} disconnected, starting recovery")

        # Step 1: Cancel pending tasks
        await self._cancel_pending_tasks(endpoint, device_id)

        # Step 2: Notify upper layers
        await self._notify_disconnection(endpoint, device_id)

        # Step 3: Attempt reconnection
        if self.policy != ReconnectionPolicy.NONE:
            reconnected = await self.attempt_reconnection(endpoint, device_id)

            # Step 4: Call reconnection callback
            if reconnected and on_reconnect:
                try:
                    await on_reconnect()
                    self.logger.info(f"Reconnection callback executed for {device_id}")
                except Exception as e:
                    self.logger.error(
                        f"Error in reconnection callback for {device_id}: {e}"
                    )

    async def attempt_reconnection(
        self, endpoint: "AIPEndpoint", device_id: str
    ) -> bool:
        """
        Attempt to reconnect to a device.

        :param endpoint: AIP endpoint managing the connection
        :param device_id: Device to reconnect to
        :return: True if reconnection successful, False otherwise
        """
        self._retry_count = 0

        while self._retry_count < self.max_retries:
            # Calculate backoff time
            backoff_time = self._calculate_backoff()

            self.logger.info(
                f"Reconnection attempt {self._retry_count + 1}/{self.max_retries} "
                f"for {device_id} in {backoff_time:.1f}s"
            )

            # Wait before attempting reconnection
            await asyncio.sleep(backoff_time)

            # Try to reconnect
            try:
                success = await endpoint.reconnect_device(device_id)
                if success:
                    self.logger.info(
                        f"Successfully reconnected to {device_id} "
                        f"after {self._retry_count + 1} attempt(s)"
                    )
                    self._retry_count = 0
                    return True
                else:
                    self.logger.warning(
                        f"Reconnection attempt {self._retry_count + 1} failed for {device_id}"
                    )
            except Exception as e:
                self.logger.error(
                    f"Error during reconnection attempt {self._retry_count + 1} for {device_id}: {e}"
                )

            self._retry_count += 1

        self.logger.error(
            f"Max reconnection attempts ({self.max_retries}) reached for {device_id}"
        )
        return False

    async def _cancel_pending_tasks(
        self, endpoint: "AIPEndpoint", device_id: str
    ) -> None:
        """
        Cancel all pending tasks for a disconnected device.

        :param endpoint: AIP endpoint
        :param device_id: Disconnected device ID
        """
        try:
            if hasattr(endpoint, "cancel_device_tasks"):
                await endpoint.cancel_device_tasks(
                    device_id, reason="device_disconnected"
                )
                self.logger.info(f"Cancelled pending tasks for {device_id}")
        except Exception as e:
            self.logger.error(
                f"Error cancelling tasks for {device_id}: {e}", exc_info=True
            )

    async def _notify_disconnection(
        self, endpoint: "AIPEndpoint", device_id: str
    ) -> None:
        """
        Notify upper layers of device disconnection.

        :param endpoint: AIP endpoint
        :param device_id: Disconnected device ID
        """
        try:
            if hasattr(endpoint, "on_device_disconnected"):
                await endpoint.on_device_disconnected(device_id)
                self.logger.info(f"Notified disconnection of {device_id}")
        except Exception as e:
            self.logger.error(
                f"Error notifying disconnection for {device_id}: {e}", exc_info=True
            )

    def _calculate_backoff(self) -> float:
        """
        Calculate backoff time based on policy.

        :return: Backoff time in seconds
        """
        if self.policy == ReconnectionPolicy.IMMEDIATE:
            return 0.0
        elif self.policy == ReconnectionPolicy.LINEAR_BACKOFF:
            backoff = self.initial_backoff * (self._retry_count + 1)
        elif self.policy == ReconnectionPolicy.EXPONENTIAL_BACKOFF:
            backoff = self.initial_backoff * (
                self.backoff_multiplier**self._retry_count
            )
        else:
            return 0.0

        # Cap at max_backoff
        return min(backoff, self.max_backoff)

    def reset(self) -> None:
        """Reset retry counter."""
        self._retry_count = 0
