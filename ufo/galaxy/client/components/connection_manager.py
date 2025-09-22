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
from typing import Dict, Optional, Any
from websockets import WebSocketClientProtocol
import websockets

from ufo.contracts.contracts import (
    ClientMessage,
    ClientMessageType,
    TaskStatus,
)
from .types import DeviceInfo, TaskRequest


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
        """
        Register this constellation as a special client with the UFO server.

        :param device_info: Device information to register with
        :param websocket: WebSocket connection to the server
        :return: True if registration successful, False otherwise
        """
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

            # Wait for server response to validate registration
            registration_success = await self._validate_registration_response(
                websocket, constellation_client_id, device_info.device_id
            )

            return registration_success

        except Exception as e:
            self.logger.error(
                f"❌ Registration failed for device {device_info.device_id}: {e}"
            )
            return False

    async def _validate_registration_response(
        self,
        websocket: WebSocketClientProtocol,
        constellation_client_id: str,
        device_id: str,
    ) -> bool:
        """
        Validate the server's response to constellation client registration.

        :param websocket: WebSocket connection to the server
        :param constellation_client_id: The constellation client ID that was registered
        :param device_id: The target device ID
        :return: True if registration was accepted, False otherwise
        """
        try:
            # Wait for server response with timeout
            response_text = await asyncio.wait_for(websocket.recv(), timeout=10.0)

            # Parse server response
            from ufo.contracts.contracts import ServerMessage

            response = ServerMessage.model_validate_json(response_text)

            if response.status == TaskStatus.ERROR:
                self.logger.error(
                    f"❌ Server rejected constellation registration for {constellation_client_id}: {response.error}"
                )
                if "not connected" in (response.error or "").lower():
                    self.logger.warning(
                        f"⚠️ Target device '{device_id}' is not connected to the server"
                    )
                return False
            elif response.status == TaskStatus.OK:
                self.logger.info(
                    f"✅ Server accepted constellation registration for {constellation_client_id}"
                )
                return True
            else:
                self.logger.warning(
                    f"⚠️ Unexpected server response status: {response.status}"
                )
                return False

        except asyncio.TimeoutError:
            self.logger.error(
                f"⏰ Timeout waiting for registration response for {constellation_client_id}"
            )
            return False
        except Exception as e:
            self.logger.error(
                f"❌ Error validating registration response for {constellation_client_id}: {e}"
            )
            return False

    async def request_device_info(self, device_id: str) -> None:
        """Request device information and capabilities from the server"""
        try:
            websocket = self._connections.get(device_id)
            if not websocket:
                return

            info_request = ClientMessage(
                type=ClientMessageType.DEVICE_INFO,
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

    async def send_task_to_device(
        self, device_id: str, task_request: TaskRequest
    ) -> Dict[str, Any]:
        """
        Send a task to a specific device and wait for response.

        :param device_id: Target device ID
        :param task_request: Task request details
        :return: Task execution result
        :raises: ConnectionError if device not connected or task fails
        """
        websocket = self._connections.get(device_id)
        if not websocket or websocket.closed:
            raise ConnectionError(f"Device {device_id} is not connected")

        try:
            # Create client message for task execution
            task_message = ClientMessage(
                type=ClientMessageType.TASK,
                client_id=self.constellation_id,
                target_id=task_request.target_client_id or device_id,
                task_name=task_request.task_name,
                request=task_request.request,
                request_id=task_request.task_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                status=TaskStatus.CONTINUE,
            )

            # Send task message
            await websocket.send(task_message.model_dump_json())
            self.logger.info(
                f"📤 Sent task {task_request.task_id} to device {device_id}"
            )

            # Wait for response with timeout
            response = await asyncio.wait_for(
                self._wait_for_task_response(device_id, task_request.task_id),
                timeout=task_request.timeout,
            )

            return response

        except asyncio.TimeoutError:
            self.logger.error(
                f"⏰ Task {task_request.task_id} timed out on device {device_id}"
            )
            raise ConnectionError(f"Task {task_request.task_id} timed out")
        except Exception as e:
            self.logger.error(
                f"❌ Failed to send task {task_request.task_id} to device {device_id}: {e}"
            )
            raise

    async def _wait_for_task_response(
        self, device_id: str, task_id: str
    ) -> Dict[str, Any]:
        """
        Wait for task response from device.
        This is a simplified implementation - in practice, you might want to use
        a more sophisticated response tracking system.
        """
        # This is a placeholder implementation
        # In a real implementation, you would:
        # 1. Store pending tasks and their completion callbacks
        # 2. Handle responses in the message processor
        # 3. Use asyncio.Event or Future to wait for completion

        # For now, simulate a successful response
        await asyncio.sleep(0.1)
        return {
            "task_id": task_id,
            "device_id": device_id,
            "status": "completed",
            "result": "Task completed successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

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
