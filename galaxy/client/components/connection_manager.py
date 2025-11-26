# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
WebSocket Connection Manager

Manages WebSocket connections to UFO servers using AIP protocols.
Single responsibility: Connection management with AIP abstraction.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional

import websockets

from aip.messages import (
    ClientMessage,
    ClientMessageType,
    ClientType,
    ServerMessage,
    TaskStatus,
)
from aip.protocol.device_info import DeviceInfoProtocol
from aip.protocol.registration import RegistrationProtocol
from aip.protocol.task_execution import TaskExecutionProtocol
from aip.transport.websocket import WebSocketTransport
from galaxy.core.types import ExecutionResult

from .types import AgentProfile, TaskRequest

if TYPE_CHECKING:
    from galaxy.client.components.message_processor import MessageProcessor


class WebSocketConnectionManager:
    """
    Manages WebSocket connections to UFO servers using AIP protocols.
    Single responsibility: Connection management with AIP abstraction.
    """

    def __init__(self, task_name: str):
        """
        Initialize WebSocketConnectionManager.
        :param task_name: Unique identifier for the task
        """

        self.task_name = task_name
        # AIP Protocol instances for each device
        self._transports: Dict[str, WebSocketTransport] = {}
        self._registration_protocols: Dict[str, RegistrationProtocol] = {}
        self._task_protocols: Dict[str, TaskExecutionProtocol] = {}
        self._device_info_protocols: Dict[str, DeviceInfoProtocol] = {}

        # Dictionary to track pending task responses using asyncio.Future
        # Key: task_id (request_id), Value: (device_id, Future)
        self._pending_tasks: Dict[str, tuple[str, asyncio.Future]] = {}
        # Dictionary to track pending device info requests
        # Key: request_id, Value: Future that will be resolved with device info dict
        self._pending_device_info: Dict[str, asyncio.Future] = {}
        # Dictionary to track pending registration responses
        # Key: device_id, Value: Future that will be resolved with registration result (bool)
        self._pending_registration: Dict[str, asyncio.Future] = {}
        self.logger = logging.getLogger(f"{__name__}.WebSocketConnectionManager")

    async def connect_to_device(
        self,
        device_info: AgentProfile,
        message_processor: "MessageProcessor",
    ) -> None:
        """
        Establish WebSocket connection to a device using AIP protocols.

        :param device_info: Device information
        :param message_processor: MessageProcessor to start message handling
        :raises: ConnectionError if connection fails
        """
        try:
            self.logger.info(
                f"🔌 Connecting to device {device_info.device_id} at {device_info.server_url}"
            )

            # Create AIP WebSocket transport and connect
            transport = WebSocketTransport(
                ping_interval=30.0,
                ping_timeout=180.0,
                close_timeout=10.0,
                max_size=100 * 1024 * 1024,
            )

            await transport.connect(device_info.server_url)

            # Store transport
            self._transports[device_info.device_id] = transport

            # Initialize AIP protocols for this connection
            self._registration_protocols[device_info.device_id] = RegistrationProtocol(
                transport
            )
            self._task_protocols[device_info.device_id] = TaskExecutionProtocol(
                transport
            )
            self._device_info_protocols[device_info.device_id] = DeviceInfoProtocol(
                transport
            )

            # ⚠️ CRITICAL: Start message handler BEFORE sending registration
            # This ensures we don't miss the server's registration response
            # Pass the transport instead of raw websocket
            message_processor.start_message_handler(device_info.device_id, transport)
            # Small delay to ensure handler is listening
            await asyncio.sleep(0.05)
            self.logger.debug(f"📨 Message handler started for {device_info.device_id}")

            # Register as constellation client using AIP RegistrationProtocol
            success = await self._register_constellation_client(device_info)

            if not success:
                await transport.close()
                raise ConnectionError("Failed to register constellation client")

        except websockets.InvalidURI as e:
            self.logger.error(
                f"❌ Invalid WebSocket URI for device {device_info.device_id}: {e}"
            )
            self._cleanup_device_protocols(device_info.device_id)
            raise ConnectionError(f"Invalid WebSocket URI: {e}") from e
        except websockets.WebSocketException as e:
            self.logger.warning(
                f"⚠️ WebSocket error connecting to device {device_info.device_id}: {e}"
            )
            self._cleanup_device_protocols(device_info.device_id)
            raise
        except OSError as e:
            self.logger.warning(
                f"⚠️ Network error connecting to device {device_info.device_id}: {e}"
            )
            self._cleanup_device_protocols(device_info.device_id)
            raise ConnectionError(f"Network error: {e}") from e
        except asyncio.TimeoutError as e:
            self.logger.warning(
                f"⚠️ Connection timeout for device {device_info.device_id}: {e}"
            )
            self._cleanup_device_protocols(device_info.device_id)
            raise
        except Exception as e:
            self.logger.error(
                f"❌ Unexpected error connecting to device {device_info.device_id}: {e}"
            )
            self._cleanup_device_protocols(device_info.device_id)
            raise

    def _cleanup_device_protocols(self, device_id: str) -> None:
        """
        Clean up all AIP protocol instances and connections for a device.
        
        Removes the device's transport, registration protocol, task protocol,
        and device info protocol from internal dictionaries.
        
        :param device_id: Device identifier whose protocols should be cleaned up
        """
        self._transports.pop(device_id, None)
        self._registration_protocols.pop(device_id, None)
        self._task_protocols.pop(device_id, None)
        self._device_info_protocols.pop(device_id, None)

    async def _register_constellation_client(self, device_info: AgentProfile) -> bool:
        """
        Register this constellation as a client using AIP RegistrationProtocol.

        :param device_info: Device information to register with
        :return: True if registration successful, False otherwise
        """
        try:
            constellation_client_id = f"{self.task_name}@{device_info.device_id}"
            transport = self._transports.get(device_info.device_id)

            if not transport:
                self.logger.error(f"❌ No transport for device {device_info.device_id}")
                return False

            # Prepare metadata for constellation registration
            metadata = {
                "type": "constellation_client",
                "task_name": self.task_name,
                "targeted_device_id": device_info.device_id,
                "capabilities": [
                    "task_distribution",
                    "session_management",
                    "device_coordination",
                ],
                "version": "2.0",
            }

            self.logger.info(
                f"📝 Registering constellation client: {constellation_client_id}"
            )

            # Create a Future to wait for registration response
            registration_future = asyncio.Future()
            self._pending_registration[device_info.device_id] = registration_future

            # Manually create and send registration message
            # (don't use register_as_constellation which calls receive_message)
            from aip.messages import (
                ClientMessage,
                ClientMessageType,
                ClientType,
                TaskStatus,
            )
            import datetime

            reg_msg = ClientMessage(
                type=ClientMessageType.REGISTER,
                client_id=constellation_client_id,
                client_type=ClientType.CONSTELLATION,
                target_id=device_info.device_id,
                status=TaskStatus.OK,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                metadata=metadata,
            )

            # Send registration message via transport
            await transport.send(reg_msg.model_dump_json().encode())
            self.logger.info(
                f"📤 Sent constellation registration for {constellation_client_id} → {device_info.device_id}"
            )

            # Wait for MessageProcessor to complete the registration via Future
            # (with timeout)
            try:
                success = await asyncio.wait_for(registration_future, timeout=30.0)
            except asyncio.TimeoutError:
                self.logger.error("❌ Registration timeout")
                self._pending_registration.pop(device_info.device_id, None)
                return False

            if not success:
                self.logger.error(
                    f"❌ Registration failed for {constellation_client_id}"
                )
                return False

            self.logger.info(
                f"✅ Registration successful for {constellation_client_id}"
            )
            return True

        except (ConnectionError, IOError) as e:
            self.logger.warning(
                f"⚠️ Connection error during registration for device {device_info.device_id}: {e}"
            )
            return False
        except asyncio.TimeoutError as e:
            self.logger.warning(
                f"⚠️ Registration timeout for device {device_info.device_id}: {e}"
            )
            return False
        except Exception as e:
            self.logger.error(
                f"❌ Unexpected error during registration for device {device_info.device_id}: {e}"
            )
            return False

    async def send_task_to_device(
        self, device_id: str, task_request: TaskRequest
    ) -> ExecutionResult:
        """
        Send a task to a specific device and wait for response using AIP.

        :param device_id: Target device ID
        :param task_request: Task request details
        :return: Task execution result
        :raises: ConnectionError if device not connected or task fails
        """
        transport = self._transports.get(device_id)
        task_protocol = self._task_protocols.get(device_id)

        if not transport or not task_protocol or not transport.is_connected:
            raise ConnectionError(f"Device {device_id} is not connected")

        try:
            task_client_id = f"{self.task_name}@{device_id}"
            constellation_task_id = f"{self.task_name}@{task_request.task_id}"

            # Create client message for task execution
            # Note: Constellation sends ClientMessage.TASK to server, which is different
            # from server sending ServerMessage.TASK to device
            task_message = ClientMessage(
                type=ClientMessageType.TASK,
                client_type=ClientType.CONSTELLATION,
                client_id=task_client_id,
                target_id=device_id,
                task_name=f"galaxy/{self.task_name}/{task_request.task_name}",
                request=task_request.request,
                session_id=constellation_task_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                status=TaskStatus.CONTINUE,
            )

            self.logger.info(
                f"📤 Sending task {task_request.task_id} to device {device_id}"
            )

            # Send via AIP transport instead of raw WebSocket
            await transport.send(task_message.model_dump_json().encode("utf-8"))

            # Wait for response with timeout
            response = await asyncio.wait_for(
                self._wait_for_task_response(device_id, constellation_task_id),
                timeout=task_request.timeout,
            )

            self.logger.info(f"✅ Received task response: status={response.status}")

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
            self._pending_tasks.pop(constellation_task_id, None)
            self.logger.error(
                f"⏰ Task {task_request.task_id} timed out on device {device_id}"
            )
            raise asyncio.TimeoutError(f"Task {task_request.task_id} timed out")
        except (ConnectionError, IOError) as e:
            # Clean up the pending future for this task
            self._pending_tasks.pop(constellation_task_id, None)
            self.logger.error(
                f"🔌 Device {device_id} connection error during task {task_request.task_id}: {e}"
            )
            raise ConnectionError(
                f"Device {device_id} connection error during task execution: {e}"
            )
        except Exception as e:
            # Clean up the pending future for this task
            self._pending_tasks.pop(constellation_task_id, None)
            self.logger.error(
                f"❌ Failed to send task {task_request.task_id} to device {device_id}: {e}"
            )
            # Check if it's a connection-related error
            if isinstance(e, (ConnectionError, ConnectionResetError)):
                raise ConnectionError(f"Device {device_id} connection error: {e}")
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
        self._pending_tasks[task_id] = (device_id, task_future)

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
        task_entry = self._pending_tasks.get(task_id)

        if task_entry is None:
            self.logger.warning(
                f"⚠️ Received task completion for unknown task: {task_id} "
                f"(task may have timed out or was already completed)"
            )
            return

        device_id, task_future = task_entry

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

    def is_connected(self, device_id: str) -> bool:
        """Check if device has active AIP connection"""
        transport = self._transports.get(device_id)
        return transport is not None and transport.is_connected

    async def disconnect_device(self, device_id: str) -> None:
        """
        Disconnect from a specific device and cancel all pending tasks.
        Cleans up all AIP protocol instances and connections.

        :param device_id: Device ID to disconnect
        """
        transport = self._transports.get(device_id)
        if transport:
            # Cancel all pending tasks for this device BEFORE closing connection
            self._cancel_pending_tasks_for_device(device_id)

            # Close AIP transport (which closes the underlying WebSocket)
            try:
                await transport.close()
            except Exception as e:
                self.logger.debug(f"Error closing transport for {device_id}: {e}")

            # Clean up all protocol instances and connections
            self._cleanup_device_protocols(device_id)

            self.logger.warning(f"🔌 Disconnected from device {device_id}")

    def _cancel_pending_tasks_for_device(self, device_id: str) -> None:
        """
        Cancel all pending task responses for a specific device.

        This is called when a device disconnects to ensure all waiting
        tasks receive a ConnectionError instead of hanging indefinitely.

        :param device_id: Device ID whose tasks should be cancelled
        """
        # Find all pending tasks for this device
        tasks_to_cancel = []
        for task_id, (dev_id, task_future) in list(self._pending_tasks.items()):
            if dev_id == device_id and not task_future.done():
                tasks_to_cancel.append(task_id)

        # Cancel all pending tasks with ConnectionError
        error = ConnectionError(
            f"Device {device_id} disconnected while waiting for task response"
        )

        for task_id in tasks_to_cancel:
            task_entry = self._pending_tasks.get(task_id)
            if task_entry:
                _, task_future = task_entry
                if not task_future.done():
                    task_future.set_exception(error)
                    self.logger.warning(
                        f"⚠️ Cancelled pending task {task_id} due to device {device_id} disconnection"
                    )
            self._pending_tasks.pop(task_id, None)

        if tasks_to_cancel:
            self.logger.info(
                f"🔄 Cancelled {len(tasks_to_cancel)} pending tasks for device {device_id}"
            )

    async def disconnect_all(self) -> None:
        """Disconnect from all devices"""
        for device_id in list(self._transports.keys()):
            await self.disconnect_device(device_id)

    async def request_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Request device system information using AIP DeviceInfoProtocol.

        This method sends a DEVICE_INFO_REQUEST message and waits for MessageProcessor
        to receive and route the DEVICE_INFO_RESPONSE back via complete_device_info_response().
        Uses the same Future pattern as send_task_to_device() to avoid recv() conflicts.

        :param device_id: The device ID to get information for
        :return: Device system information dictionary, or None if not available
        """
        device_info_protocol = self._device_info_protocols.get(device_id)
        transport = self._transports.get(device_id)

        if not device_info_protocol or not transport or not transport.is_connected:
            self.logger.warning(
                f"⚠️ Device {device_id} not connected, cannot request info"
            )
            return None

        try:
            # Create a unique request ID
            request_id = (
                f"device_info_{device_id}_{datetime.now(timezone.utc).timestamp()}"
            )

            # Create a Future to wait for response
            info_future = asyncio.Future()
            self._pending_device_info[request_id] = info_future

            # Use AIP DeviceInfoProtocol to request device info
            # Note: We still use manual ClientMessage construction because constellation
            # needs to specify client_id and target_id differently than a regular device
            request_message = ClientMessage(
                type=ClientMessageType.DEVICE_INFO_REQUEST,
                client_type=ClientType.CONSTELLATION,
                client_id=f"{self.task_name}@{device_id}",
                target_id=device_id,
                request_id=request_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                status=TaskStatus.OK,
            )

            await transport.send(request_message.model_dump_json().encode("utf-8"))
            self.logger.debug(f"📤 Sent device info request for {device_id}")

            # Wait for MessageProcessor to complete the Future (timeout: 10s)
            try:
                device_info = await asyncio.wait_for(info_future, timeout=10.0)
                self.logger.info(f"📊 Retrieved device info for {device_id}")
                return device_info
            except asyncio.TimeoutError:
                self.logger.error(f"⏰ Timeout requesting device info for {device_id}")
                return None
            finally:
                # Clean up the pending future
                self._pending_device_info.pop(request_id, None)

        except (ConnectionError, IOError) as e:
            self.logger.error(
                f"❌ Connection error requesting device info for {device_id}: {e}"
            )
            self._pending_device_info.pop(request_id, None)
            return None
        except Exception as e:
            self.logger.error(f"❌ Error requesting device info for {device_id}: {e}")
            self._pending_device_info.pop(request_id, None)
            return None

    def complete_device_info_response(
        self, request_id: str, device_info: Optional[Dict[str, Any]]
    ) -> None:
        """
        Complete a pending device info request with the response from the server.

        This method is called by MessageProcessor when it receives a DEVICE_INFO_RESPONSE.
        It resolves the asyncio.Future associated with the request_id.

        :param request_id: Unique request identifier
        :param device_info: Device system information dictionary, or None if error
        """
        info_future = self._pending_device_info.get(request_id)

        if info_future is None:
            self.logger.warning(
                f"⚠️ Received device info response for unknown request: {request_id}"
            )
            return

        if info_future.done():
            self.logger.warning(
                f"⚠️ Received duplicate device info response for: {request_id}"
            )
            return

        # Resolve the Future with the device info
        info_future.set_result(device_info)
        self.logger.debug(f"✅ Completed device info response for {request_id}")

    def complete_registration_response(
        self, device_id: str, success: bool, error_message: Optional[str] = None
    ) -> None:
        """
        Complete a pending registration request with the response from the server.

        This method is called by MessageProcessor when it receives the first HEARTBEAT
        or ERROR message after registration (which is the server's response to registration).
        It resolves the asyncio.Future associated with the device_id.

        :param device_id: Device identifier
        :param success: True if registration was accepted, False if rejected
        :param error_message: Optional error message if registration failed
        """
        registration_future = self._pending_registration.get(device_id)

        if registration_future is None:
            # No pending registration - this is a regular heartbeat/error, not a registration response
            return

        if registration_future.done():
            self.logger.warning(
                f"⚠️ Received duplicate registration response for device: {device_id}"
            )
            return

        # Resolve the Future with the registration result
        registration_future.set_result(success)

        # Clean up the pending registration
        self._pending_registration.pop(device_id, None)

        if success:
            self.logger.debug(f"✅ Registration accepted for device {device_id}")
        else:
            self.logger.warning(
                f"⚠️ Registration rejected for device {device_id}: {error_message}"
            )
