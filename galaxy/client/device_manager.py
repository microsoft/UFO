# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation Device Manager

Main coordinator for device management in Constellation v2.
Uses modular components for clean separation of concerns.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
import websockets

from galaxy.core.types import ExecutionResult
from galaxy.core.events import DeviceEvent, EventType, get_event_bus
from aip.messages import TaskStatus

from .components import (
    AgentProfile,
    DeviceRegistry,
    DeviceStatus,
    HeartbeatManager,
    MessageProcessor,
    TaskQueueManager,
    TaskRequest,
    WebSocketConnectionManager,
)


class ConstellationDeviceManager:
    """
    Main coordinator for device management in Constellation v2.

    This refactored class delegates responsibilities to focused components:
    - DeviceRegistry: Device registration and information
    - WebSocketConnectionManager: Connection management
    - HeartbeatManager: Health monitoring
    - MessageProcessor: Message routing
    - TaskQueueManager: Task queuing and scheduling
    """

    def __init__(
        self,
        task_name: str = "test_task",
        heartbeat_interval: float = 30.0,
        reconnect_delay: float = 5.0,
    ):
        """
        Initialize the device manager with modular components.

        :param task_name: Unique identifier for tasks
        :param heartbeat_interval: Interval for heartbeat messages (seconds)
        :param reconnect_delay: Delay between reconnection attempts (seconds)
        """
        self.task_name = task_name
        self.reconnect_delay = reconnect_delay

        # Initialize modular components
        self.device_registry = DeviceRegistry()
        self.connection_manager = WebSocketConnectionManager(task_name)
        self.heartbeat_manager = HeartbeatManager(
            self.connection_manager, self.device_registry, heartbeat_interval
        )
        self.message_processor = MessageProcessor(
            self.device_registry,
            self.heartbeat_manager,
            self.connection_manager,
        )
        self.task_queue_manager = TaskQueueManager()

        # Register disconnection handler with MessageProcessor
        self.message_processor.set_disconnection_handler(
            self._handle_device_disconnection
        )

        # Reconnection management
        self._reconnect_tasks: Dict[str, asyncio.Task] = {}

        # Event bus for device events
        self.event_bus = get_event_bus()

        self.logger = logging.getLogger(__name__)

    def _get_device_registry_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """
        Create a snapshot of all devices in the registry.

        :return: Dictionary mapping device_id to device status information
        """
        snapshot = {}
        all_devices = self.device_registry.get_all_devices()

        for device_id, device_info in all_devices.items():
            snapshot[device_id] = {
                "device_id": device_info.device_id,
                "status": device_info.status.value,
                "os": device_info.os,
                "server_url": device_info.server_url,
                "capabilities": device_info.capabilities,
                "metadata": device_info.metadata,
                "last_heartbeat": (
                    device_info.last_heartbeat.isoformat()
                    if device_info.last_heartbeat
                    else None
                ),
                "connection_attempts": device_info.connection_attempts,
                "max_retries": device_info.max_retries,
                "current_task_id": device_info.current_task_id,
            }

        return snapshot

    async def _publish_device_event(
        self, event_type: EventType, device_id: str, device_info: AgentProfile
    ) -> None:
        """
        Publish a device event to the event bus.

        :param event_type: Type of device event
        :param device_id: Device ID
        :param device_info: Device information
        """
        try:
            # Get device registry snapshot
            all_devices_snapshot = self._get_device_registry_snapshot()

            # Create device-specific info
            device_data = {
                "device_id": device_info.device_id,
                "status": device_info.status.value,
                "os": device_info.os,
                "server_url": device_info.server_url,
                "capabilities": device_info.capabilities,
                "metadata": device_info.metadata,
                "last_heartbeat": (
                    device_info.last_heartbeat.isoformat()
                    if device_info.last_heartbeat
                    else None
                ),
                "connection_attempts": device_info.connection_attempts,
                "max_retries": device_info.max_retries,
                "current_task_id": device_info.current_task_id,
            }

            # Create and publish device event
            event = DeviceEvent(
                event_type=event_type,
                source_id=f"device_manager.{device_id}",
                timestamp=time.time(),
                data={
                    "event_name": event_type.value,
                    "device_count": len(all_devices_snapshot),
                },
                device_id=device_id,
                device_status=device_info.status.value,
                device_info=device_data,
                all_devices=all_devices_snapshot,
            )

            await self.event_bus.publish_event(event)
            self.logger.debug(
                f"📢 Published {event_type.value} event for device {device_id}"
            )

        except Exception as e:
            self.logger.error(
                f"❌ Failed to publish device event for {device_id}: {e}",
                exc_info=True,
            )

    async def register_device(
        self,
        device_id: str,
        server_url: str,
        os: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_connect: bool = True,
    ) -> bool:
        """
        Register a device and optionally connect to it.

        :param device_id: Unique device identifier
        :param server_url: UFO WebSocket server URL
        :param capabilities: Device capabilities list
        :param metadata: Additional device metadata
        :param auto_connect: Whether to automatically connect after registration
        :return: True if registration (and connection if enabled) successful
        """
        try:
            # Register device in registry
            self.device_registry.register_device(
                device_id, server_url, os, capabilities, metadata
            )

            if auto_connect:
                return await self.connect_device(device_id)

            return True

        except ValueError as e:
            self.logger.error(
                f"❌ Invalid device configuration for {device_id}: {e}", exc_info=True
            )
            return False
        except TypeError as e:
            self.logger.error(
                f"❌ Type error registering device {device_id}: {e}", exc_info=True
            )
            return False
        except Exception as e:
            self.logger.error(
                f"❌ Unexpected error registering device {device_id}: {e}",
                exc_info=True,
            )
            return False

    async def connect_device(
        self, device_id: str, is_reconnection: bool = False
    ) -> bool:
        """
        Connect to a registered device.

        :param device_id: Device to connect to
        :param is_reconnection: True if this is a reconnection attempt (won't increment global attempts counter)
        :return: True if connection successful
        """
        if not self.device_registry.is_device_registered(device_id):
            self.logger.error(f"❌ Device {device_id} not registered")
            return False

        device_info = self.device_registry.get_device(device_id)
        if not device_info:
            return False

        if device_info.status == DeviceStatus.CONNECTED:
            self.logger.info(f"✅ Device {device_id} already connected")
            return True

        try:
            # Update status to CONNECTING
            self.device_registry.update_device_status(
                device_id, DeviceStatus.CONNECTING
            )

            # Only increment attempts for initial connection, not reconnections
            # Reconnections have their own retry counter in _reconnect_device()
            if not is_reconnection:
                self.device_registry.increment_connection_attempts(device_id)

            # Establish connection with message processor
            # ⚠️ Pass message_processor to ensure it starts BEFORE registration
            # This prevents race conditions where server responses arrive before we start listening
            await self.connection_manager.connect_to_device(
                device_info, message_processor=self.message_processor
            )

            # Update status to connected
            self.device_registry.update_device_status(device_id, DeviceStatus.CONNECTED)
            self.device_registry.update_heartbeat(device_id)

            # ⚠️ Message handler already started in connect_to_device()
            # No need to start it again here to avoid race conditions
            # self.message_processor.start_message_handler(device_id, websocket)

            # Start heartbeat monitoring
            self.heartbeat_manager.start_heartbeat(device_id)

            # Request device system info and update AgentProfile
            # The device already pushed its info during registration, now we retrieve it
            device_system_info = await self.connection_manager.request_device_info(
                device_id
            )
            if device_system_info:
                # Update AgentProfile with system information (delegate to DeviceRegistry)
                self.device_registry.update_device_system_info(
                    device_id, device_system_info
                )

            # Set device to IDLE (ready to accept tasks)
            self.device_registry.set_device_idle(device_id)

            # Publish DEVICE_CONNECTED event
            await self._publish_device_event(
                EventType.DEVICE_CONNECTED, device_id, device_info
            )

            self.logger.info(f"✅ Successfully connected to device {device_id}")
            return True

        except websockets.InvalidURI as e:
            self.device_registry.update_device_status(device_id, DeviceStatus.FAILED)
            # Use different log level for reconnection vs initial connection
            if is_reconnection:
                self.logger.debug(f"Invalid WebSocket URI for device {device_id}: {e}")
            else:
                self.logger.error(
                    f"❌ Invalid WebSocket URI for device {device_id}: {e}"
                )
            return False
        except websockets.WebSocketException as e:
            self.device_registry.update_device_status(device_id, DeviceStatus.FAILED)
            # Use different log level for reconnection vs initial connection
            if is_reconnection:
                self.logger.debug(
                    f"WebSocket error connecting to device {device_id}: {e}"
                )
            else:
                self.logger.error(
                    f"❌ WebSocket error connecting to device {device_id}: {e}"
                )
            # Schedule reconnection if under retry limit
            if device_info.connection_attempts < device_info.max_retries:
                self._schedule_reconnection(device_id)
            return False
        except OSError as e:
            self.device_registry.update_device_status(device_id, DeviceStatus.FAILED)
            # Use different log level for reconnection vs initial connection
            if is_reconnection:
                self.logger.debug(
                    f"Network error connecting to device {device_id}: {e}"
                )
            else:
                self.logger.error(
                    f"❌ Network error connecting to device {device_id}: {e}"
                )
            # Schedule reconnection if under retry limit
            if device_info.connection_attempts < device_info.max_retries:
                self._schedule_reconnection(device_id)
            return False
        except asyncio.TimeoutError as e:
            self.device_registry.update_device_status(device_id, DeviceStatus.FAILED)
            # Use different log level for reconnection vs initial connection
            if is_reconnection:
                self.logger.debug(f"Timeout connecting to device {device_id}: {e}")
            else:
                self.logger.error(f"❌ Timeout connecting to device {device_id}: {e}")
            # Schedule reconnection if under retry limit
            if device_info.connection_attempts < device_info.max_retries:
                self._schedule_reconnection(device_id)
            return False
        except Exception as e:
            self.device_registry.update_device_status(device_id, DeviceStatus.FAILED)
            # Use different log level for reconnection vs initial connection
            if is_reconnection:
                self.logger.debug(f"Error connecting to device {device_id}: {e}")
            else:
                self.logger.error(
                    f"❌ Unexpected error connecting to device {device_id}: {e}"
                )
            # Schedule reconnection if under retry limit
            if device_info.connection_attempts < device_info.max_retries:
                self._schedule_reconnection(device_id)
            return False

    async def disconnect_device(self, device_id: str) -> None:
        """Manually disconnect from a device"""
        # Get device info before disconnection for event publishing
        device_info = self.device_registry.get_device(device_id)

        # Stop background services
        self.message_processor.stop_message_handler(device_id)
        self.heartbeat_manager.stop_heartbeat(device_id)

        # Disconnect connection
        await self.connection_manager.disconnect_device(device_id)

        # Update status
        self.device_registry.update_device_status(device_id, DeviceStatus.DISCONNECTED)

        # Publish DEVICE_DISCONNECTED event
        if device_info:
            await self._publish_device_event(
                EventType.DEVICE_DISCONNECTED, device_id, device_info
            )

    async def _handle_device_disconnection(self, device_id: str) -> None:
        """
        Handle device disconnection cleanup and attempt reconnection.

        This method is called by MessageProcessor when a device disconnects.
        It performs cleanup, updates device status, and schedules reconnection.

        :param device_id: Device that disconnected
        """
        try:
            self.logger.warning(f"🔌 Device {device_id} disconnected, cleaning up...")

            # Get device info for reconnection logic
            device_info = self.device_registry.get_device(device_id)
            if not device_info:
                self.logger.error(
                    f"❌ Cannot handle disconnection: device {device_id} not found in registry"
                )
                return

            # Stop message handler (if not already stopped)
            self.message_processor.stop_message_handler(device_id)

            # Update device status to DISCONNECTED
            self.device_registry.update_device_status(
                device_id, DeviceStatus.DISCONNECTED
            )

            # Clean up connection
            await self.connection_manager.disconnect_device(device_id)

            # Publish DEVICE_DISCONNECTED event
            await self._publish_device_event(
                EventType.DEVICE_DISCONNECTED, device_id, device_info
            )

            # Cancel current task if device was executing one
            current_task_id = device_info.current_task_id
            if current_task_id:
                self.logger.warning(
                    f"⚠️ Device {device_id} was executing task {current_task_id}, marking as failed"
                )
                # Fail the task in queue manager
                error = ConnectionError(
                    f"Device {device_id} disconnected during task execution"
                )
                self.task_queue_manager.fail_task(device_id, current_task_id, error)
                # Clear current task
                device_info.current_task_id = None

            # Schedule reconnection (will retry internally until max_retries)
            # The reconnection loop manages its own retry counter
            self.logger.info(
                f"🔄 Scheduling automatic reconnection for device {device_id} "
                f"(max retries: {device_info.max_retries})"
            )
            self._schedule_reconnection(device_id)

        except KeyError as e:
            self.logger.error(
                f"❌ Device {device_id} not found during disconnection handling: {e}",
                exc_info=True,
            )
        except AttributeError as e:
            self.logger.error(
                f"❌ Invalid device state during disconnection for {device_id}: {e}",
                exc_info=True,
            )
        except Exception as e:
            self.logger.error(
                f"❌ Unexpected error handling disconnection for device {device_id}: {e}",
                exc_info=True,
            )

    def _schedule_reconnection(self, device_id: str) -> None:
        """Schedule automatic reconnection for a device"""
        if device_id not in self._reconnect_tasks:
            self._reconnect_tasks[device_id] = asyncio.create_task(
                self._reconnect_device(device_id)
            )

    async def _reconnect_device(self, device_id: str) -> None:
        """
        Attempt to reconnect to a device with automatic retries.

        This method will keep trying to reconnect until:
        1. Successfully reconnected, OR
        2. Reached max_retries attempts

        Each retry waits reconnect_delay seconds before attempting.

        :param device_id: Device ID to reconnect
        """
        try:
            device_info = self.device_registry.get_device(device_id)
            if not device_info:
                self.logger.error(f"❌ Device {device_id} not found in registry")
                return

            retry_count = 0
            max_retries = device_info.max_retries

            while retry_count < max_retries:
                # Wait before attempting reconnection
                await asyncio.sleep(self.reconnect_delay)

                retry_count += 1
                self.logger.info(
                    f"🔄 Reconnection attempt {retry_count}/{max_retries} for device {device_id}"
                )

                try:
                    # Attempt reconnection (pass is_reconnection=True to avoid incrementing global counter)
                    success = await self.connect_device(device_id, is_reconnection=True)

                    if success:
                        self.logger.info(
                            f"✅ Successfully reconnected to device {device_id} "
                            f"on attempt {retry_count}/{max_retries}"
                        )
                        # Reset connection attempts on successful reconnection
                        self.device_registry.reset_connection_attempts(device_id)
                        return  # Success, exit retry loop
                    else:
                        self.logger.info(
                            f"🔄 Reconnection attempt {retry_count}/{max_retries} failed for device {device_id}, will retry..."
                        )

                except websockets.WebSocketException as e:
                    self.logger.debug(
                        f"WebSocket error on reconnection attempt {retry_count}/{max_retries} "
                        f"for device {device_id}: {e}"
                    )
                except OSError as e:
                    self.logger.debug(
                        f"Network error on reconnection attempt {retry_count}/{max_retries} "
                        f"for device {device_id}: {e}"
                    )
                except asyncio.TimeoutError as e:
                    self.logger.debug(
                        f"Timeout on reconnection attempt {retry_count}/{max_retries} "
                        f"for device {device_id}: {e}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"⚠️ Error on reconnection attempt {retry_count}/{max_retries} "
                        f"for device {device_id}: {e}"
                    )

            # All retries exhausted
            self.logger.error(
                f"❌ Failed to reconnect to device {device_id} after {max_retries} attempts, giving up"
            )
            self.device_registry.update_device_status(device_id, DeviceStatus.FAILED)

        except Exception as e:
            self.logger.error(
                f"❌ Reconnection loop failed for device {device_id}: {e}",
                exc_info=True,
            )
        finally:
            self._reconnect_tasks.pop(device_id, None)

    async def assign_task_to_device(
        self,
        task_id: str,
        device_id: str,
        task_description: str,
        task_data: Dict[str, Any],
        timeout: float = 1000,
    ) -> ExecutionResult:
        """
        Assign a task to a specific device.
        If device is BUSY, the task will be queued and executed when device becomes IDLE.

        :param task_id: Unique task identifier
        :param device_id: Target device ID
        :param task_description: Task description
        :param task_data: Task data and metadata
        :param timeout: Task timeout in seconds
        :return: Task execution result
        """
        # Check if device is registered and connected
        device_info = self.device_registry.get_device(device_id)
        if not device_info:
            raise ValueError(f"Device {device_id} is not registered")

        if device_info.status not in [
            DeviceStatus.CONNECTED,
            DeviceStatus.IDLE,
            DeviceStatus.BUSY,
        ]:
            raise ValueError(
                f"Device {device_id} is not connected (status: {device_info.status.value})"
            )

        # Create task request
        task_request = TaskRequest(
            task_id=task_id,
            device_id=device_id,
            request=task_description,
            task_name=task_id,
            metadata=task_data,
            timeout=timeout,
        )

        # Check if device is busy
        if self.device_registry.is_device_busy(device_id):
            self.logger.info(
                f"⏸️  Device {device_id} is BUSY. Task {task_id} will be queued."
            )
            # Enqueue task and get future
            future = self.task_queue_manager.enqueue_task(device_id, task_request)
            # Wait for task to complete
            result = await future
            return result
        else:
            # Device is IDLE, execute task immediately
            return await self._execute_task_on_device(device_id, task_request)

    async def _execute_task_on_device(
        self, device_id: str, task_request: TaskRequest
    ) -> ExecutionResult:
        """
        Execute a task on a device (internal method).
        Sets device to BUSY before execution and IDLE after completion.

        Returns ExecutionResult with FAILED status if device disconnects or
        other errors occur, instead of raising exceptions.

        :param device_id: Device ID
        :param task_request: Task to execute
        :return: Task execution result (always returns, never raises)
        """
        try:
            # Set device to BUSY
            self.device_registry.set_device_busy(device_id, task_request.task_id)

            # Publish DEVICE_STATUS_CHANGED event (BUSY)
            device_info = self.device_registry.get_device(device_id)
            if device_info:
                await self._publish_device_event(
                    EventType.DEVICE_STATUS_CHANGED, device_id, device_info
                )

            # Execute task through connection manager
            result = await self.connection_manager.send_task_to_device(
                device_id, task_request
            )

            # Complete the task in queue manager if it was queued
            self.task_queue_manager.complete_task(
                device_id, task_request.task_id, result
            )

            return result

        except ConnectionError as e:
            # Handle device disconnection during task execution
            self.logger.error(
                f"❌ Device {device_id} disconnected during task {task_request.task_id}: {e}"
            )

            # Create ExecutionResult with FAILED status and disconnection message
            result = ExecutionResult(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                result={
                    "error_type": "device_disconnection",
                    "message": f"Device {device_id} disconnected during task execution",
                    "device_id": device_id,
                    "task_id": task_request.task_id,
                },
                metadata={
                    "device_id": device_id,
                    "disconnected": True,
                    "error_category": "connection_error",
                },
            )

            # Fail the task in queue manager
            self.task_queue_manager.fail_task(device_id, task_request.task_id, e)

            return result

        except asyncio.TimeoutError as e:
            # Handle task timeout
            self.logger.error(
                f"❌ Task {task_request.task_id} timed out on device {device_id}"
            )

            result = ExecutionResult(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error=f"Task execution timed out after {task_request.timeout} seconds",
                result={
                    "error_type": "timeout",
                    "message": f"Task timed out after {task_request.timeout} seconds",
                    "device_id": device_id,
                    "task_id": task_request.task_id,
                },
                metadata={
                    "device_id": device_id,
                    "timeout": task_request.timeout,
                    "error_category": "timeout_error",
                },
            )

            # Fail the task in queue manager
            self.task_queue_manager.fail_task(device_id, task_request.task_id, e)

            return result

        except Exception as e:
            # Handle other errors
            self.logger.error(
                f"❌ Task {task_request.task_id} failed on device {device_id}: {e}"
            )

            result = ExecutionResult(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                result={
                    "error_type": "execution_error",
                    "message": str(e),
                    "device_id": device_id,
                    "task_id": task_request.task_id,
                },
                metadata={
                    "device_id": device_id,
                    "error_category": "general_error",
                },
            )

            # Fail the task in queue manager
            self.task_queue_manager.fail_task(device_id, task_request.task_id, e)

            return result

        finally:
            # Set device back to IDLE
            self.device_registry.set_device_idle(device_id)

            # Publish DEVICE_STATUS_CHANGED event (IDLE)
            device_info = self.device_registry.get_device(device_id)
            if device_info:
                await self._publish_device_event(
                    EventType.DEVICE_STATUS_CHANGED, device_id, device_info
                )

            # Check if there are queued tasks and process next one
            await self._process_next_queued_task(device_id)

    async def _process_next_queued_task(self, device_id: str) -> None:
        """
        Process the next queued task for a device if available.

        :param device_id: Device ID
        """
        if self.task_queue_manager.has_queued_tasks(device_id):
            next_task = self.task_queue_manager.dequeue_task(device_id)
            if next_task:
                self.logger.info(
                    f"🚀 Processing next queued task {next_task.task_id} for device {device_id}"
                )
                # Execute next task asynchronously (don't await here to avoid blocking)
                asyncio.create_task(self._execute_task_on_device(device_id, next_task))

    # Device information access (delegate to DeviceRegistry)
    def get_device_info(self, device_id: str) -> Optional[AgentProfile]:
        """Get device information"""
        return self.device_registry.get_device(device_id)

    def get_connected_devices(self) -> List[str]:
        """Get list of connected device IDs"""
        return self.device_registry.get_connected_devices()

    def get_device_capabilities(self, device_id: str) -> Dict[str, Any]:
        """Get device capabilities and information"""
        return self.device_registry.get_device_capabilities(device_id)

    def get_device_system_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device system information (hardware, OS, features).
        Delegates to DeviceRegistry.

        :param device_id: Device ID
        :return: System information dictionary or None if not available
        """
        return self.device_registry.get_device_system_info(device_id)

    def get_all_devices(self, connected=False) -> Dict[str, AgentProfile]:
        """
        Get all registered devices
        :param connected: If True, return only connected devices
        :return: Dictionary of device_id to AgentProfile
        """
        return self.device_registry.get_all_devices(connected=connected)

    def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get device status information"""
        device_info = self.device_registry.get_device(device_id)
        if not device_info:
            return {"error": f"Device {device_id} not found"}

        return {
            "device_id": device_info.device_id,
            "status": device_info.status.value,
            "server_url": device_info.server_url,
            "capabilities": device_info.capabilities,
            "metadata": device_info.metadata,
            "last_heartbeat": (
                device_info.last_heartbeat.isoformat()
                if device_info.last_heartbeat
                else None
            ),
            "connection_attempts": device_info.connection_attempts,
            "max_retries": device_info.max_retries,
            "current_task_id": device_info.current_task_id,
            "queued_tasks": self.task_queue_manager.get_queue_size(device_id),
            "queued_task_ids": self.task_queue_manager.get_queued_task_ids(device_id),
        }

    def get_task_queue_status(self, device_id: str) -> Dict[str, Any]:
        """
        Get task queue status for a device.

        :param device_id: Device ID
        :return: Queue status information
        """
        return {
            "device_id": device_id,
            "is_busy": self.device_registry.is_device_busy(device_id),
            "current_task_id": self.device_registry.get_current_task(device_id),
            "queue_size": self.task_queue_manager.get_queue_size(device_id),
            "queued_task_ids": self.task_queue_manager.get_queued_task_ids(device_id),
            "pending_task_ids": self.task_queue_manager.get_pending_task_ids(device_id),
        }

    async def ensure_devices_connected(self) -> Dict[str, bool]:
        """
        Ensure all registered devices are connected.
        Attempts to reconnect any disconnected devices.

        :return: Dictionary mapping device_id to connection status (True if connected)
        """
        self.logger.info("🔌 Checking and ensuring all devices are connected...")
        results = {}

        all_devices = self.device_registry.get_all_devices()
        for device_id, device_info in all_devices.items():
            # Check if device is in a connected state (CONNECTED, IDLE, or BUSY all mean connected)
            is_connected_state = device_info.status in [
                DeviceStatus.CONNECTED,
                DeviceStatus.IDLE,
                DeviceStatus.BUSY,
            ]

            # Also verify the actual connection
            is_actually_connected = (
                is_connected_state and self.connection_manager.is_connected(device_id)
            )

            if is_actually_connected:
                self.logger.debug(
                    f"✅ Device {device_id} already connected (status: {device_info.status.value})"
                )
                results[device_id] = True
            else:
                self.logger.info(
                    f"🔄 Device {device_id} needs reconnection (status: {device_info.status.value}), attempting to connect..."
                )
                try:
                    # Use regular connect (not is_reconnection) to properly reset state
                    success = await self.connect_device(
                        device_id, is_reconnection=False
                    )
                    results[device_id] = success
                    if success:
                        self.logger.info(
                            f"✅ Successfully connected device {device_id}"
                        )
                    else:
                        self.logger.warning(f"⚠️ Failed to connect device {device_id}")
                except Exception as e:
                    self.logger.error(f"❌ Error connecting device {device_id}: {e}")
                    results[device_id] = False

        connected_count = sum(1 for connected in results.values() if connected)
        total_count = len(results)
        self.logger.info(
            f"🔌 Connection check complete: {connected_count}/{total_count} devices connected"
        )

        return results

    async def shutdown(self) -> None:
        """Shutdown the device manager and disconnect all devices"""
        self.logger.info("🛑 Shutting down device manager")

        # Cancel all queued tasks for all devices
        for device_id in self.device_registry.get_all_devices():
            self.task_queue_manager.cancel_all_tasks(device_id)

        # Stop all background services
        self.message_processor.stop_all_handlers()
        self.heartbeat_manager.stop_all_heartbeats()

        # Disconnect all devices
        await self.connection_manager.disconnect_all()

        # Cancel and wait for reconnection tasks to complete
        for task in self._reconnect_tasks.values():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass  # Expected when task is cancelled
                except Exception as e:
                    self.logger.warning(f"Error during reconnect task cleanup: {e}")

        self.logger.info("✅ Device manager shutdown complete")
