# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Heartbeat Protocol

Handles periodic keepalive messages to maintain connection health.
"""

import asyncio
import datetime
import logging
from typing import Optional
from uuid import uuid4

from aip.messages import (
    ClientMessage,
    ClientMessageType,
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from aip.protocol.base import AIPProtocol


class HeartbeatProtocol(AIPProtocol):
    """
    Heartbeat protocol for AIP.

    Provides:
    - Periodic heartbeat messages
    - Connection health monitoring
    - Automatic heartbeat management
    """

    def __init__(self, *args, **kwargs):
        """Initialize heartbeat protocol."""
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(f"{__name__}.HeartbeatProtocol")
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval: float = 30.0  # Default: 30 seconds

    async def send_heartbeat(
        self, client_id: str, metadata: Optional[dict] = None
    ) -> None:
        """
        Send a single heartbeat message (client-side).

        :param client_id: Client ID
        :param metadata: Optional metadata dictionary
        """
        heartbeat_msg = ClientMessage(
            type=ClientMessageType.HEARTBEAT,
            client_id=client_id,
            status=TaskStatus.OK,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            metadata=metadata,
        )
        await self.send_message(heartbeat_msg)
        self.logger.debug(f"Sent heartbeat from {client_id}")

    async def send_heartbeat_ack(self, response_id: Optional[str] = None) -> None:
        """
        Send heartbeat acknowledgment (server-side).

        :param response_id: Optional response ID
        """
        ack_msg = ServerMessage(
            type=ServerMessageType.HEARTBEAT,
            status=TaskStatus.OK,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            response_id=response_id or str(uuid4()),
        )
        await self.send_message(ack_msg)
        self.logger.debug("Sent heartbeat acknowledgment")

    async def start_heartbeat(self, client_id: str, interval: float = 30.0) -> None:
        """
        Start automatic heartbeat sending.

        :param client_id: Client ID
        :param interval: Interval between heartbeats (seconds)
        """
        if self._heartbeat_task is not None:
            self.logger.warning("Heartbeat already running, stopping existing task")
            await self.stop_heartbeat()

        self._heartbeat_interval = interval
        self._heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(client_id, interval)
        )
        self.logger.info(f"Started heartbeat for {client_id} (interval: {interval}s)")

    async def stop_heartbeat(self) -> None:
        """Stop automatic heartbeat sending."""
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            self.logger.info("Stopped heartbeat")

    async def _heartbeat_loop(self, client_id: str, interval: float) -> None:
        """
        Internal heartbeat loop.

        :param client_id: Client ID
        :param interval: Interval between heartbeats (seconds)
        """
        try:
            while True:
                await asyncio.sleep(interval)
                if self.is_connected():
                    await self.send_heartbeat(client_id)
                else:
                    self.logger.warning("Transport not connected, skipping heartbeat")
        except asyncio.CancelledError:
            self.logger.debug("Heartbeat loop cancelled")
        except Exception as e:
            self.logger.error(f"Error in heartbeat loop: {e}", exc_info=True)
