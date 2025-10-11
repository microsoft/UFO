# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation Device Manager

Main coordinator for device management in Constellation v2.
Uses modular components for clean separation of concerns.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable

from galaxy.core.types import ExecutionResult

from .components import (
    DeviceStatus,
    DeviceInfo,
    TaskRequest,
    DeviceRegistry,
    WebSocketConnectionManager,
    HeartbeatManager,
    EventManager,
    MessageProcessor,
    TaskQueueManager,
)


class ConstellationDeviceManager:
    """
    Main coordinator for device management in Constellation v2.

    This refactored class delegates responsibilities to focused components:
    - DeviceRegistry: Device registration and information
    - WebSocketConnectionManager: Connection management
    - HeartbeatManager: Health monitoring
    - EventManager: Event handling
    - MessageProcessor: Message routing
    - TaskQueueManager: Task queuing and scheduling
    """

    def __init__(
        self,
        constellation_id: str = "constellation_orchestrator",
        heartbeat_interval: float = 30.0,
        reconnect_delay: float = 5.0,
    ):
        """
        Initialize the device manager with modular components.

        :param constellation_id: Unique identifier for this constellation instance
        :param heartbeat_interval: Interval for heartbeat messages (seconds)
        :param reconnect_delay: Delay between reconnection attempts (seconds)
        """
        self.constellation_id = constellation_id
        self.reconnect_delay = reconnect_delay

        # Initialize modular components
        self.device_registry = DeviceRegistry()
        self.connection_manager = WebSocketConnectionManager(constellation_id)
        self.heartbeat_manager = HeartbeatManager(
            self.connection_manager, self.device_registry, heartbeat_interval
        )
        self.event_manager = EventManager()
        self.message_processor = MessageProcessor(
            self.device_registry,
            self.heartbeat_manager,
            self.event_manager,
            self.connection_manager,
        )
        self.task_queue_manager = TaskQueueManager()

        # Reconnection management
        self._reconnect_tasks: Dict[str, asyncio.Task] = {}

        self.logger = logging.getLogger(__name__)

    async def register_device(
        self,
        device_id: str,
        server_url: str,
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
                device_id, server_url, capabilities, metadata
            )

            if auto_connect:
                return await self.connect_device(device_id)

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to register device {device_id}: {e}")
            return False

    async def connect_device(self, device_id: str) -> bool:
        """
        Connect to a registered device.

        :param device_id: Device to connect to
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
            # Update status and increment attempts
            self.device_registry.update_device_status(
                device_id, DeviceStatus.CONNECTING
            )
            self.device_registry.increment_connection_attempts(device_id)

            # Establish connection
            websocket = await self.connection_manager.connect_to_device(device_info)

            # Update status to connected
            self.device_registry.update_device_status(device_id, DeviceStatus.CONNECTED)
            self.device_registry.update_heartbeat(device_id)

            # Start background services
            self.message_processor.start_message_handler(device_id, websocket)
            self.heartbeat_manager.start_heartbeat(device_id)

            # Request device capabilities
            # await self.connection_manager.request_device_info(device_id)

            # Set device to IDLE (ready to accept tasks)
            self.device_registry.set_device_idle(device_id)

            # Notify connection handlers
            await self.event_manager.notify_device_connected(device_id, device_info)

            self.logger.info(f"✅ Successfully connected to device {device_id}")
            return True

        except Exception as e:
            self.device_registry.update_device_status(device_id, DeviceStatus.FAILED)
            self.logger.error(f"❌ Failed to connect to device {device_id}: {e}")

            # Schedule reconnection if under retry limit
            if device_info.connection_attempts < device_info.max_retries:
                self._schedule_reconnection(device_id)

            return False

    async def disconnect_device(self, device_id: str) -> None:
        """Manually disconnect from a device"""
        # Stop background services
        self.message_processor.stop_message_handler(device_id)
        self.heartbeat_manager.stop_heartbeat(device_id)

        # Disconnect connection
        await self.connection_manager.disconnect_device(device_id)

        # Update status
        self.device_registry.update_device_status(device_id, DeviceStatus.DISCONNECTED)

        # Notify handlers
        await self.event_manager.notify_device_disconnected(device_id)

    def _schedule_reconnection(self, device_id: str) -> None:
        """Schedule automatic reconnection for a device"""
        if device_id not in self._reconnect_tasks:
            self._reconnect_tasks[device_id] = asyncio.create_task(
                self._reconnect_device(device_id)
            )

    async def _reconnect_device(self, device_id: str) -> None:
        """Attempt to reconnect to a device after a delay"""
        try:
            await asyncio.sleep(self.reconnect_delay)
            self.logger.info(f"🔄 Attempting to reconnect to device {device_id}")
            await self.connect_device(device_id)
        except Exception as e:
            self.logger.error(f"❌ Reconnection failed for device {device_id}: {e}")
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

        :param device_id: Device ID
        :param task_request: Task to execute
        :return: Task execution result
        """
        try:
            # Set device to BUSY
            self.device_registry.set_device_busy(device_id, task_request.task_id)

            # Execute task through connection manager
            result = await self.connection_manager.send_task_to_device(
                device_id, task_request
            )

            # Notify task completion handlers
            await self.event_manager.notify_task_completed(
                device_id, task_request.task_id, result
            )

            # Complete the task in queue manager if it was queued
            self.task_queue_manager.complete_task(
                device_id, task_request.task_id, result
            )

            return result

        except Exception as e:
            self.logger.error(
                f"❌ Task {task_request.task_id} failed on device {device_id}: {e}"
            )
            # Fail the task in queue manager
            self.task_queue_manager.fail_task(device_id, task_request.task_id, e)
            raise

        finally:
            # Set device back to IDLE
            self.device_registry.set_device_idle(device_id)

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

    # Event handler registration (delegate to EventManager)
    def add_connection_handler(self, handler: Callable) -> None:
        """Add a handler for device connection events"""
        self.event_manager.add_connection_handler(handler)

    def add_disconnection_handler(self, handler: Callable) -> None:
        """Add a handler for device disconnection events"""
        self.event_manager.add_disconnection_handler(handler)

    def add_task_completion_handler(self, handler: Callable) -> None:
        """Add a handler for task completion events"""
        self.event_manager.add_task_completion_handler(handler)

    # Device information access (delegate to DeviceRegistry)
    def get_device_info(self, device_id: str) -> Optional[DeviceInfo]:
        """Get device information"""
        return self.device_registry.get_device(device_id)

    def get_connected_devices(self) -> List[str]:
        """Get list of connected device IDs"""
        return self.device_registry.get_connected_devices()

    def get_device_capabilities(self, device_id: str) -> Dict[str, Any]:
        """Get device capabilities and information"""
        return self.device_registry.get_device_capabilities(device_id)

    def get_all_devices(self, connected=False) -> Dict[str, DeviceInfo]:
        """
        Get all registered devices
        :param connected: If True, return only connected devices
        :return: Dictionary of device_id to DeviceInfo
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

        # Cancel reconnection tasks
        for task in self._reconnect_tasks.values():
            if not task.done():
                task.cancel()

        self.logger.info("✅ Device manager shutdown complete")
