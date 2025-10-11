# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
WebSocket Connection Manager

Manages WebSocket connections to UFO servers.
Single responsibility: Connection management.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from websockets import WebSocketClientProtocol
import websockets

from galaxy.core.types import ExecutionResult
from ufo.contracts.contracts import (
    ClientMessage,
    ClientMessageType,
    ClientType,
    ServerMessage,
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
        # Dictionary to track pending task responses using asyncio.Future
        # Key: task_id (request_id), Value: Future that will be resolved with ServerMessage
        self._pending_tasks: Dict[str, asyncio.Future] = {}
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
                client_type=ClientType.CONSTELLATION,
                target_id=device_info.device_id,
                status=TaskStatus.OK,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={
                    "type": "constellation_client",
                    "constellation_id": self.constellation_id,
                    "targeted_device_id": device_info.device_id,
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

    async def send_task_to_device(
        self, device_id: str, task_request: TaskRequest
    ) -> ExecutionResult:
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
                client_type=ClientType.CONSTELLATION,
                target_id=device_id,
                task_name=task_request.task_name,
                request=task_request.request,
                session_id=task_request.task_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                status=TaskStatus.CONTINUE,
            )

            # Send task message
            self.logger.info(
                f"📤 Sent task {task_request.task_id} to device {device_id}"
            )

            await websocket.send(task_message.model_dump_json())

            # Wait for response with timeout
            response = await asyncio.wait_for(
                self._wait_for_task_response(device_id, task_request.task_id),
                timeout=task_request.timeout,
            )

            self.logger.info(f"📤📤 Received response: {response}")

            task_result = ExecutionResult(
                task_id=task_request.task_id,
                status=response.status,
                metadata={"device_id": device_id},
                error=response.error,
                result=response.result,
            )

            return task_result

        except asyncio.TimeoutError:
            # Clean up the pending future for this task
            self._pending_tasks.pop(task_request.task_id, None)
            self.logger.error(
                f"⏰ Task {task_request.task_id} timed out on device {device_id}"
            )
            raise ConnectionError(f"Task {task_request.task_id} timed out")
        except Exception as e:
            # Clean up the pending future for this task
            self._pending_tasks.pop(task_request.task_id, None)
            self.logger.error(
                f"❌ Failed to send task {task_request.task_id} to device {device_id}: {e}"
            )
            raise

    async def _wait_for_task_response(
        self, device_id: str, task_id: str
    ) -> ServerMessage:
        """
        Wait for task response from device.

        This method creates an asyncio.Future that will be completed by the MessageProcessor
        when it receives a TASK_END message for this task. The Future-based approach allows
        synchronous-style waiting for asynchronous task completion.

        Workflow:
        1. Create a Future and register it in _pending_tasks
        2. Wait for the Future to be resolved (by complete_task_response)
        3. Return the ServerMessage result
        4. Clean up the Future from _pending_tasks

        :param device_id: Target device ID
        :param task_id: Unique task identifier (request_id)
        :return: ServerMessage containing task execution result
        :raises: Exception if task fails or is cancelled

        Example:
            >>> # This method is called internally by send_task_to_device
            >>> response = await self._wait_for_task_response(device_id, task_id)
            >>> print(response.status)  # TaskStatus.COMPLETED
        """
        # Create a Future to wait for task completion
        task_future = asyncio.Future()
        self._pending_tasks[task_id] = task_future

        self.logger.debug(
            f"⏳ Waiting for response for task {task_id} from device {device_id}"
        )

        try:
            # Wait for Future to be completed by MessageProcessor
            response = await task_future
            self.logger.debug(
                f"✅ Received response for task {task_id} from device {device_id}"
            )
            return response
        finally:
            # Clean up completed Future to prevent memory leaks
            self._pending_tasks.pop(task_id, None)

    def complete_task_response(self, task_id: str, response: ServerMessage) -> None:
        """
        Complete a pending task response with the result from the server.

        This method is called by MessageProcessor when it receives a TASK_END message.
        It resolves the asyncio.Future associated with the task_id, which unblocks
        the corresponding _wait_for_task_response() call.

        Thread-safety: This method is safe to call from the MessageProcessor's
        async context as asyncio.Future.set_result() is thread-safe.

        :param task_id: Unique task identifier (request_id from ServerMessage)
        :param response: ServerMessage containing task execution result

        Behavior:
        - If task_id exists and Future is pending: Resolves the Future with response
        - If task_id doesn't exist: Logs a warning (task may have timed out)
        - If Future already completed: Logs a warning (duplicate response)

        Example:
            >>> # Called by MessageProcessor when TASK_END is received
            >>> server_msg = ServerMessage(type=ServerMessageType.TASK_END, ...)
            >>> connection_manager.complete_task_response(server_msg.request_id, server_msg)
        """
        task_future = self._pending_tasks.get(task_id)

        if task_future is None:
            self.logger.warning(
                f"⚠️ Received task completion for unknown task: {task_id} "
                f"(task may have timed out or was already completed)"
            )
            return

        if task_future.done():
            self.logger.warning(
                f"⚠️ Received duplicate task completion for already completed task: {task_id}"
            )
            return

        # Resolve the Future with the server response
        task_future.set_result(response)
        self.logger.debug(
            f"✅ Completed task response for {task_id} (status: {response.status})"
        )

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
