# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Message Processor

Processes incoming messages from UFO servers.
Single responsibility: Message handling and routing.
"""

import asyncio
import json
import logging
from typing import Dict, Any
from websockets import WebSocketClientProtocol
import websockets

from ufo.contracts.contracts import (
    ServerMessage,
    ServerMessageType,
    TaskStatus,
)
from .device_registry import DeviceRegistry
from .heartbeat_manager import HeartbeatManager
from .event_manager import EventManager


class MessageProcessor:
    """
    Processes incoming messages from UFO servers.
    Single responsibility: Message handling and routing.
    """

    def __init__(
        self,
        device_registry: DeviceRegistry,
        heartbeat_manager: HeartbeatManager,
        event_manager: EventManager,
    ):
        self.device_registry = device_registry
        self.heartbeat_manager = heartbeat_manager
        self.event_manager = event_manager
        self._message_handlers: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger(f"{__name__}.MessageProcessor")

    def start_message_handler(
        self, device_id: str, websocket: WebSocketClientProtocol
    ) -> None:
        """Start message handling for a device"""
        if device_id not in self._message_handlers:
            self._message_handlers[device_id] = asyncio.create_task(
                self._handle_device_messages(device_id, websocket)
            )
            self.logger.debug(f"📨 Started message handler for device {device_id}")

    def stop_message_handler(self, device_id: str) -> None:
        """Stop message handling for a device"""
        if device_id in self._message_handlers:
            task = self._message_handlers[device_id]
            if not task.done():
                task.cancel()
            del self._message_handlers[device_id]
            self.logger.debug(f"📨 Stopped message handler for device {device_id}")

    async def _handle_device_messages(
        self, device_id: str, websocket: WebSocketClientProtocol
    ) -> None:
        """Handle incoming messages from a device"""
        try:
            async for message in websocket:
                try:
                    server_msg = ServerMessage.model_validate_json(message)
                    await self._process_server_message(device_id, server_msg)
                except json.JSONDecodeError as e:
                    self.logger.error(f"❌ Invalid JSON from device {device_id}: {e}")
                except Exception as e:
                    self.logger.error(
                        f"❌ Error processing message from device {device_id}: {e}"
                    )

        except websockets.ConnectionClosed:
            self.logger.warning(f"🔌 Connection to device {device_id} closed")
        except Exception as e:
            self.logger.error(f"❌ Message handler error for device {device_id}: {e}")

    async def _process_server_message(
        self, device_id: str, server_msg: ServerMessage
    ) -> None:
        """Process a message received from the UFO server"""
        try:
            self.logger.debug(
                f"📨 Processing message type {server_msg.type} from device {device_id}"
            )

            if server_msg.type == ServerMessageType.TASK_END:
                await self._handle_task_completion(device_id, server_msg)
            elif server_msg.type == ServerMessageType.ERROR:
                await self._handle_error_message(device_id, server_msg)
            elif server_msg.type == ServerMessageType.HEARTBEAT:
                self.heartbeat_manager.handle_heartbeat_response(device_id)
            elif server_msg.type == ServerMessageType.COMMAND:
                await self._handle_command_message(device_id, server_msg)
            else:
                self.logger.debug(
                    f"📋 Unhandled message type {server_msg.type} from device {device_id}"
                )

        except Exception as e:
            self.logger.error(
                f"❌ Error processing server message from device {device_id}: {e}"
            )

    async def _handle_task_completion(
        self, device_id: str, server_msg: ServerMessage
    ) -> None:
        """Handle task completion messages"""
        try:
            session_id = server_msg.session_id

            # Prepare result
            result = {
                "success": server_msg.status == TaskStatus.COMPLETED,
                "device_id": device_id,
                "session_id": session_id,
                "status": server_msg.status,
                "error": getattr(server_msg, "error", None),
                "results": getattr(server_msg, "results", None),
                "timestamp": server_msg.timestamp,
            }

            # Notify event handlers
            task_id = session_id  # Using session_id as task_id for now
            await self.event_manager.notify_task_completed(device_id, task_id, result)

        except Exception as e:
            self.logger.error(
                f"❌ Error handling task completion from device {device_id}: {e}"
            )

    async def _handle_error_message(
        self, device_id: str, server_msg: ServerMessage
    ) -> None:
        """Handle error messages from the server"""
        error_text = getattr(server_msg, "error", "Unknown error")
        self.logger.error(f"❌ Error from device {device_id}: {error_text}")

        session_id = getattr(server_msg, "session_id", None)
        if session_id:
            # Notify event handlers about task failure
            await self.event_manager.notify_task_failed(
                device_id, session_id, error_text
            )

    async def _handle_command_message(
        self, device_id: str, server_msg: ServerMessage
    ) -> None:
        """Handle command messages from the server"""
        # For constellation clients, acknowledge and continue processing
        try:
            # Commands are typically handled by local clients, not constellation
            self.logger.debug(
                f"🔄 Received command from device {device_id}, delegating to local clients"
            )
        except Exception as e:
            self.logger.error(f"❌ Error handling command from device {device_id}: {e}")

    async def _process_device_info_response(self, device_id: str, results: Any) -> None:
        """Process device information response"""
        try:
            if isinstance(results, dict):
                self.device_registry.set_device_capabilities(device_id, results)
                self.logger.info(f"📊 Updated device info for {device_id}")
        except Exception as e:
            self.logger.error(f"❌ Error processing device info for {device_id}: {e}")

    def stop_all_handlers(self) -> None:
        """Stop all message handlers"""
        for device_id in list(self._message_handlers.keys()):
            self.stop_message_handler(device_id)
