# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
WebSocket Connection Manager

Manages WebSocket connections to UFO servers.
Single responsibility: Connection management.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from websockets import WebSocketClientProtocol
import websockets

from ufo.contracts.contracts import (
    ClientMessage,
    ClientMessageType,
    TaskStatus,
)
from .types import DeviceInfo


class WebSocketConnectionManager:
    """
    Manages WebSocket connections to UFO servers.
    Single responsibility: Connection management.
    """

    def __init__(self, constellation_id: str):
        self.constellation_id = constellation_id
        self._connections: Dict[str, WebSocketClientProtocol] = {}
        self.logger = logging.getLogger(f"{__name__}.WebSocketConnectionManager")

    async def connect_to_device(
        self, device_info: DeviceInfo
    ) -> WebSocketClientProtocol:
        """
        Establish WebSocket connection to a device.

        :param device_info: Device information
        :return: WebSocket connection
        :raises: ConnectionError if connection fails
        """
        try:
            self.logger.info(
                f"🔌 Connecting to device {device_info.device_id} at {device_info.server_url}"
            )

            websocket = await websockets.connect(device_info.server_url)
            self._connections[device_info.device_id] = websocket

            # Register as constellation client
            success = await self._register_constellation_client(device_info, websocket)
            if not success:
                await websocket.close()
                raise ConnectionError("Failed to register constellation client")

            return websocket

        except Exception as e:
            self.logger.error(
                f"❌ Failed to connect to device {device_info.device_id}: {e}"
            )
            self._connections.pop(device_info.device_id, None)
            raise

    async def _register_constellation_client(
        self, device_info: DeviceInfo, websocket: WebSocketClientProtocol
    ) -> bool:
        """Register this constellation as a special client with the UFO server"""
        try:
            constellation_client_id = f"{self.constellation_id}@{device_info.device_id}"

            registration_message = ClientMessage(
                type=ClientMessageType.REGISTER,
                client_id=constellation_client_id,
                status=TaskStatus.OK,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={
                    "type": "constellation_client",
                    "constellation_id": self.constellation_id,
                    "device_id": device_info.device_id,
                    "local_clients": device_info.local_client_ids,
                    "capabilities": [
                        "task_distribution",
                        "session_management",
                        "device_coordination",
                    ],
                    "version": "2.0",
                },
            )

            await websocket.send(registration_message.model_dump_json())
            self.logger.info(
                f"📝 Sent registration for constellation client: {constellation_client_id}"
            )

            # Brief pause to allow server processing
            await asyncio.sleep(0.5)
            return True

        except Exception as e:
            self.logger.error(
                f"❌ Registration failed for device {device_info.device_id}: {e}"
            )
            return False

    async def request_device_info(self, device_id: str) -> None:
        """Request device information and capabilities from the server"""
        try:
            websocket = self._connections.get(device_id)
            if not websocket:
                return

            info_request = ClientMessage(
                type=ClientMessageType.GET_INFO,
                client_id=self.constellation_id,
                target_id=device_id,
                task_name="device_info_request",
                request_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc).isoformat(),
                status=TaskStatus.CONTINUE,
            )

            await websocket.send(info_request.model_dump_json())
            self.logger.info(f"📊 Requested device info from {device_id}")

        except Exception as e:
            self.logger.error(f"❌ Failed to request device info from {device_id}: {e}")

    def get_connection(self, device_id: str) -> Optional[WebSocketClientProtocol]:
        """Get WebSocket connection for a device"""
        return self._connections.get(device_id)

    def is_connected(self, device_id: str) -> bool:
        """Check if device has active connection"""
        websocket = self._connections.get(device_id)
        return websocket is not None and not websocket.closed

    async def disconnect_device(self, device_id: str) -> None:
        """Disconnect from a specific device"""
        if device_id in self._connections:
            try:
                await self._connections[device_id].close()
            except:
                pass
            del self._connections[device_id]
            self.logger.info(f"🔌 Disconnected from device {device_id}")

    async def disconnect_all(self) -> None:
        """Disconnect from all devices"""
        for device_id in list(self._connections.keys()):
            await self.disconnect_device(device_id)
