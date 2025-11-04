# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Heartbeat Manager

Manages periodic heartbeat messages to monitor connection health
and detect disconnections early.
"""

import asyncio
import logging
from typing import Dict, Optional

from aip.protocol.heartbeat import HeartbeatProtocol


class HeartbeatManager:
    """
    Manages heartbeat for multiple clients/devices.

    Features:
    - Per-client heartbeat tracking
    - Configurable intervals
    - Automatic heartbeat sending
    - Connection health monitoring
    """

    def __init__(
        self,
        protocol: HeartbeatProtocol,
        default_interval: float = 30.0,
    ):
        """
        Initialize heartbeat manager.

        :param protocol: Heartbeat protocol instance
        :param default_interval: Default interval between heartbeats (seconds)
        """
        self.protocol = protocol
        self.default_interval = default_interval
        self.logger = logging.getLogger(f"{__name__}.HeartbeatManager")

        # Track heartbeat tasks per client
        self._heartbeat_tasks: Dict[str, asyncio.Task] = {}
        self._intervals: Dict[str, float] = {}

    async def start_heartbeat(
        self, client_id: str, interval: Optional[float] = None
    ) -> None:
        """
        Start heartbeat for a client.

        :param client_id: Client ID
        :param interval: Heartbeat interval (default: use default_interval)
        """
        if client_id in self._heartbeat_tasks:
            self.logger.warning(
                f"Heartbeat already running for {client_id}, stopping existing"
            )
            await self.stop_heartbeat(client_id)

        interval = interval or self.default_interval
        self._intervals[client_id] = interval

        # Create heartbeat task
        task = asyncio.create_task(self._heartbeat_loop(client_id, interval))
        self._heartbeat_tasks[client_id] = task

        self.logger.info(f"Started heartbeat for {client_id} (interval: {interval}s)")

    async def stop_heartbeat(self, client_id: str) -> None:
        """
        Stop heartbeat for a client.

        :param client_id: Client ID
        """
        task = self._heartbeat_tasks.pop(client_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            self._intervals.pop(client_id, None)
            self.logger.info(f"Stopped heartbeat for {client_id}")

    async def stop_all(self) -> None:
        """Stop all heartbeats."""
        client_ids = list(self._heartbeat_tasks.keys())
        for client_id in client_ids:
            await self.stop_heartbeat(client_id)
        self.logger.info("Stopped all heartbeats")

    def is_running(self, client_id: str) -> bool:
        """
        Check if heartbeat is running for a client.

        :param client_id: Client ID
        :return: True if running, False otherwise
        """
        task = self._heartbeat_tasks.get(client_id)
        return task is not None and not task.done()

    def get_interval(self, client_id: str) -> Optional[float]:
        """
        Get heartbeat interval for a client.

        :param client_id: Client ID
        :return: Interval in seconds, or None if not running
        """
        return self._intervals.get(client_id)

    async def _heartbeat_loop(self, client_id: str, interval: float) -> None:
        """
        Internal heartbeat loop for a client.

        :param client_id: Client ID
        :param interval: Heartbeat interval (seconds)
        """
        try:
            while True:
                await asyncio.sleep(interval)

                # Check if protocol is still connected
                if self.protocol.is_connected():
                    try:
                        await self.protocol.send_heartbeat(client_id)
                        self.logger.debug(f"Sent heartbeat for {client_id}")
                    except Exception as e:
                        self.logger.error(
                            f"Error sending heartbeat for {client_id}: {e}"
                        )
                        # Let the loop continue, connection manager will handle disconnection
                else:
                    self.logger.warning(
                        f"Protocol not connected for {client_id}, skipping heartbeat"
                    )

        except asyncio.CancelledError:
            self.logger.debug(f"Heartbeat loop cancelled for {client_id}")
        except Exception as e:
            self.logger.error(
                f"Unexpected error in heartbeat loop for {client_id}: {e}",
                exc_info=True,
            )
