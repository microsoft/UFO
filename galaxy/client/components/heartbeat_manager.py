# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Heartbeat Manager

Manages device health monitoring through heartbeats using AIP HeartbeatProtocol.
Single responsibility: Health monitoring with AIP abstraction.
"""

import asyncio
import logging
from typing import Dict

from aip.protocol.heartbeat import HeartbeatProtocol

from .connection_manager import WebSocketConnectionManager
from .device_registry import DeviceRegistry


class HeartbeatManager:
    """
    Manages device health monitoring through heartbeats using AIP.
    Single responsibility: Health monitoring with AIP abstraction.
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
        # Cache heartbeat protocols for each device
        self._heartbeat_protocols: Dict[str, HeartbeatProtocol] = {}
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
            # Clean up protocol instance
            if device_id in self._heartbeat_protocols:
                del self._heartbeat_protocols[device_id]
            self.logger.debug(f"💓 Stopped heartbeat for device {device_id}")

    async def _heartbeat_loop(self, device_id: str) -> None:
        """Send periodic heartbeat messages to a device"""
        while self.connection_manager.is_connected(device_id):
            try:
                # Get or create HeartbeatProtocol for this device
                if device_id not in self._heartbeat_protocols:
                    transport = self.connection_manager._transports.get(device_id)
                    if not transport:
                        break
                    self._heartbeat_protocols[device_id] = HeartbeatProtocol(transport)

                protocol = self._heartbeat_protocols[device_id]
                task_name = self.connection_manager.task_name
                client_id = f"{task_name}@{device_id}"

                # Send heartbeat using AIP HeartbeatProtocol
                await protocol.send_heartbeat(
                    client_id=client_id, metadata={"device_id": device_id}
                )

                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                self.logger.error(f"💓 Heartbeat error for device {device_id}: {e}")
                # Clean up protocol instance
                if device_id in self._heartbeat_protocols:
                    del self._heartbeat_protocols[device_id]
                break

    def handle_heartbeat_response(self, device_id: str) -> None:
        """Handle heartbeat response from device"""
        self.device_registry.update_heartbeat(device_id)
        self.logger.debug(f"💓 Heartbeat response from device {device_id}")

    def stop_all_heartbeats(self) -> None:
        """Stop all heartbeat monitoring"""
        for device_id in list(self._heartbeat_tasks.keys()):
            self.stop_heartbeat(device_id)
