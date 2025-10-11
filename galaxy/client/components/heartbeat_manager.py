# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Heartbeat Manager

Manages device health monitoring through heartbeats.
Single responsibility: Health monitoring.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict

from ufo.contracts.contracts import ClientMessage, ClientMessageType, TaskStatus

from .connection_manager import WebSocketConnectionManager
from .device_registry import DeviceRegistry


class HeartbeatManager:
    """
    Manages device health monitoring through heartbeats.
    Single responsibility: Health monitoring.
    """

    def __init__(
        self,
        connection_manager: WebSocketConnectionManager,
        device_registry: DeviceRegistry,
        heartbeat_interval: float = 30.0,
    ):
        self.connection_manager = connection_manager
        self.device_registry = device_registry
        self.heartbeat_interval = heartbeat_interval
        self._heartbeat_tasks: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger(f"{__name__}.HeartbeatManager")

    def start_heartbeat(self, device_id: str) -> None:
        """Start heartbeat monitoring for a device"""
        if device_id not in self._heartbeat_tasks:
            self._heartbeat_tasks[device_id] = asyncio.create_task(
                self._heartbeat_loop(device_id)
            )
            self.logger.debug(f"💓 Started heartbeat for device {device_id}")

    def stop_heartbeat(self, device_id: str) -> None:
        """Stop heartbeat monitoring for a device"""
        if device_id in self._heartbeat_tasks:
            task = self._heartbeat_tasks[device_id]
            if not task.done():
                task.cancel()
            del self._heartbeat_tasks[device_id]
            self.logger.debug(f"💓 Stopped heartbeat for device {device_id}")

    async def _heartbeat_loop(self, device_id: str) -> None:
        """Send periodic heartbeat messages to a device"""
        while self.connection_manager.is_connected(device_id):
            try:
                websocket = self.connection_manager.get_connection(device_id)
                if not websocket:
                    break

                heartbeat_msg = ClientMessage(
                    type=ClientMessageType.HEARTBEAT,
                    client_id=f"constellation@{device_id}",
                    status=TaskStatus.OK,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    metadata={"device_id": device_id},
                )

                await websocket.send(heartbeat_msg.model_dump_json())
                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                self.logger.error(f"💓 Heartbeat error for device {device_id}: {e}")
                break

    def handle_heartbeat_response(self, device_id: str) -> None:
        """Handle heartbeat response from device"""
        self.device_registry.update_heartbeat(device_id)
        self.logger.debug(f"💓 Heartbeat response from device {device_id}")

    def stop_all_heartbeats(self) -> None:
        """Stop all heartbeat monitoring"""
        for device_id in list(self._heartbeat_tasks.keys()):
            self.stop_heartbeat(device_id)
