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

from .components import (
    DeviceStatus,
    DeviceInfo,
    TaskRequest,
    DeviceRegistry,
    WebSocketConnectionManager,
    HeartbeatManager,
    EventManager,
    MessageProcessor,
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
        )

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
            device_info = self.device_registry.register_device(
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
            await self.connection_manager.request_device_info(device_id)

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
        target_client_id: Optional[str],
        task_description: str,
        task_data: Dict[str, Any],
        timeout: float = 300.0,
    ) -> Dict[str, Any]:
        """
        Assign a task to a specific device.

        :param task_id: Unique task identifier
        :param device_id: Target device ID
        :param target_client_id: Specific local client ID (optional)
        :param task_description: Task description
        :param task_data: Task data and metadata
        :param timeout: Task timeout in seconds
        :return: Task execution result
        """
        # Check if device is connected
        device_info = self.device_registry.get_device(device_id)
        if not device_info or device_info.status != DeviceStatus.CONNECTED:
            raise ValueError(f"Device {device_id} is not connected")

        # Create task request
        task_request = TaskRequest(
            task_id=task_id,
            device_id=device_id,
            target_client_id=target_client_id,
            request=task_description,
            task_name=task_id,
            metadata=task_data,
            timeout=timeout,
        )

        # Execute task through connection manager
        try:
            result = await self.connection_manager.send_task_to_device(
                device_id, task_request
            )

            # Notify task completion handlers
            await self.event_manager.notify_task_completed(device_id, task_id, result)

            return result
        except Exception as e:
            self.logger.error(f"❌ Task {task_id} failed on device {device_id}: {e}")
            raise

    async def execute_task_direct(
        self,
        task_id: str,
        device_id: str,
        description: str,
        task_data: Dict[str, Any],
        timeout: float = 300.0,
    ) -> Dict[str, Any]:
        """
        直接执行任务，整合原TaskExecutionManager功能

        :param task_id: Task identifier
        :param device_id: Target device ID
        :param description: Task description
        :param task_data: Task data
        :param timeout: Timeout in seconds
        :return: Task execution result
        """
        return await self.assign_task_to_device(
            task_id=task_id,
            device_id=device_id,
            target_client_id=None,
            task_description=description,
            task_data=task_data,
            timeout=timeout,
        )

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

    def get_all_devices(self) -> Dict[str, DeviceInfo]:
        """Get all registered devices"""
        return self.device_registry.get_all_devices()

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
        }

    async def shutdown(self) -> None:
        """Shutdown the device manager and disconnect all devices"""
        self.logger.info("🛑 Shutting down device manager")

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
