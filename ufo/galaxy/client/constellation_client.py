# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation Client

Main client class that integrates device management, task distribution,
and configuration loading for the Constellation v2 system.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable

from ufo.contracts.contracts import (
    ClientMessage,
    ClientMessageType,
    TaskStatus,
)

from .device_manager import ConstellationDeviceManager
from .components import DeviceInfo, TaskRequest
from .config_loader import ConstellationConfig, DeviceConfig


class ConstellationClient:
    """
    Main client for Constellation v2 system.

    This class provides:
    1. Device registration and management
    2. Task distribution across devices
    3. Configuration loading from multiple sources
    4. Event handling for connections and task completion
    5. High-level API for multi-device coordination
    """

    def __init__(
        self,
        config: Optional[ConstellationConfig] = None,
        constellation_id: Optional[str] = None,
    ):
        """
        Initialize the constellation client.

        :param config: Constellation configuration
        :param constellation_id: Override constellation ID
        """
        self.config = config or ConstellationConfig()

        if constellation_id:
            self.config.constellation_id = constellation_id

        # Initialize device manager
        self.device_manager = ConstellationDeviceManager(
            constellation_id=self.config.constellation_id,
            heartbeat_interval=self.config.heartbeat_interval,
            reconnect_delay=self.config.reconnect_delay,
        )

        # Task management
        self._task_counter = 0
        self._pending_tasks: Dict[str, asyncio.Future] = {}
        self._task_callbacks: Dict[str, Callable] = {}

        # Event handlers
        self._setup_event_handlers()

        self.logger = logging.getLogger(__name__)

    def _setup_event_handlers(self) -> None:
        """Setup event handlers for device manager events."""
        self.device_manager.add_connection_handler(self._on_device_connected)
        self.device_manager.add_disconnection_handler(self._on_device_disconnected)
        self.device_manager.add_task_completion_handler(self._on_task_completed)

    async def _on_device_connected(
        self, device_id: str, device_info: DeviceInfo
    ) -> None:
        """Handle device connection events."""
        self.logger.info(f"🔗 Device {device_id} connected successfully")

    async def _on_device_disconnected(self, device_id: str) -> None:
        """Handle device disconnection events."""
        self.logger.warning(f"🔌 Device {device_id} disconnected")

    async def _on_task_completed(
        self, device_id: str, task_id: str, result: Dict[str, Any]
    ) -> None:
        """Handle task completion events."""
        self.logger.info(f"✅ Task {task_id} completed on device {device_id}")

        # Execute callback if registered
        if task_id in self._task_callbacks:
            try:
                callback = self._task_callbacks[task_id]
                await callback(task_id, device_id, result)
            except Exception as e:
                self.logger.error(f"Error in task callback for {task_id}: {e}")
            finally:
                del self._task_callbacks[task_id]

    async def initialize(self) -> None:
        """
        Initialize the constellation client and register devices from configuration.
        """
        self.logger.info(
            f"🚀 Initializing Constellation Client: {self.config.constellation_id}"
        )

        # Register devices from configuration
        for device_config in self.config.devices:
            success = await self.register_device_from_config(device_config)
            if success:
                self.logger.info(f"✅ Registered device {device_config.device_id}")
            else:
                self.logger.error(
                    f"❌ Failed to register device {device_config.device_id}"
                )

    async def register_device_from_config(self, device_config: DeviceConfig) -> bool:
        """
        Register a device from configuration.

        :param device_config: Device configuration
        :return: True if registration successful
        """
        return await self.device_manager.register_device(
            device_id=device_config.device_id,
            server_url=device_config.server_url,
            local_client_ids=device_config.local_client_ids,
            capabilities=device_config.capabilities,
            metadata=device_config.metadata,
            auto_connect=device_config.auto_connect,
        )

    async def register_device(
        self,
        device_id: str,
        server_url: str,
        local_client_ids: List[str],
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_connect: bool = True,
    ) -> bool:
        """
        Register a device manually.

        :param device_id: Unique device identifier
        :param server_url: UFO WebSocket server URL
        :param local_client_ids: List of local client IDs on this device
        :param capabilities: Device capabilities
        :param metadata: Additional device metadata
        :param auto_connect: Whether to automatically connect
        :return: True if registration successful
        """
        return await self.device_manager.register_device(
            device_id=device_id,
            server_url=server_url,
            local_client_ids=local_client_ids,
            capabilities=capabilities,
            metadata=metadata,
            auto_connect=auto_connect,
        )

    async def execute_task(
        self,
        request: str,
        device_id: Optional[str] = None,
        target_client_id: Optional[str] = None,
        task_name: Optional[str] = None,
        capabilities_required: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: float = 300.0,
        callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task on a device.

        :param request: Task request description
        :param device_id: Target device ID (auto-select if None)
        :param target_client_id: Specific local client ID (auto-select if None)
        :param task_name: Task name
        :param capabilities_required: Required capabilities for device selection
        :param metadata: Additional task metadata
        :param timeout: Task timeout in seconds
        :param callback: Completion callback function
        :return: Task execution result
        """
        # Generate task ID
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{uuid.uuid4().hex[:8]}"

        if not task_name:
            task_name = f"constellation_task_{self._task_counter}"

        # Auto-select device if not specified
        if not device_id:
            device_id = await self._select_best_device(capabilities_required)
            if not device_id:
                raise ValueError("No suitable device available for task execution")

        # Validate device
        if device_id not in self.device_manager.get_connected_devices():
            raise ValueError(f"Device {device_id} is not connected")

        # Register callback if provided
        if callback:
            self._task_callbacks[task_id] = callback

        try:
            # Execute task via device manager
            result = await self.device_manager.assign_task_to_device(
                task_id=task_id,
                device_id=device_id,
                target_client_id=target_client_id,
                task_description=request,
                task_data=metadata or {},
                timeout=timeout,
            )

            self.logger.info(
                f"✅ Task {task_id} completed successfully on device {device_id}"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ Task {task_id} failed on device {device_id}: {e}")
            # Clean up callback
            self._task_callbacks.pop(task_id, None)
            raise

    async def execute_tasks_parallel(
        self,
        tasks: List[Dict[str, Any]],
        max_concurrent: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute multiple tasks in parallel across devices.

        :param tasks: List of task dictionaries with keys: request, device_id (optional), etc.
        :param max_concurrent: Maximum concurrent tasks (uses config default if None)
        :return: Dictionary mapping task IDs to results
        """
        if max_concurrent is None:
            max_concurrent = self.config.max_concurrent_tasks

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single_task(task_config: Dict[str, Any]) -> tuple:
            async with semaphore:
                task_id = f"parallel_task_{len(results)}_{uuid.uuid4().hex[:8]}"
                try:
                    result = await self.execute_task(**task_config)
                    return task_id, result
                except Exception as e:
                    return task_id, {"success": False, "error": str(e)}

        # Execute tasks concurrently
        results = {}
        tasks_futures = [execute_single_task(task) for task in tasks]

        completed_tasks = await asyncio.gather(*tasks_futures, return_exceptions=True)

        for task_result in completed_tasks:
            if isinstance(task_result, tuple):
                task_id, result = task_result
                results[task_id] = result
            else:
                # Handle exceptions
                error_task_id = f"error_task_{len(results)}"
                results[error_task_id] = {"success": False, "error": str(task_result)}

        return results

    async def _select_best_device(
        self, capabilities_required: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Select the best available device for task execution.

        :param capabilities_required: Required capabilities
        :return: Selected device ID or None
        """
        connected_devices = self.device_manager.get_connected_devices()

        if not connected_devices:
            return None

        # If no specific capabilities required, use first available device
        if not capabilities_required:
            return connected_devices[0]

        # Find devices with required capabilities
        suitable_devices = []

        for device_id in connected_devices:
            device_info = self.device_manager.get_device_info(device_id)
            device_capabilities = self.device_manager.get_device_capabilities(device_id)

            if device_info and device_capabilities:
                # Check if device has required capabilities
                available_caps = device_info.capabilities + device_capabilities.get(
                    "capabilities", []
                )

                if all(cap in available_caps for cap in capabilities_required):
                    suitable_devices.append(device_id)

        # Return first suitable device (could be enhanced with load balancing)
        return suitable_devices[0] if suitable_devices else connected_devices[0]

    def get_device_status(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get device status information.

        :param device_id: Specific device ID, or None for all devices
        :return: Device status information
        """
        if device_id:
            device_info = self.device_manager.get_device_info(device_id)
            device_caps = self.device_manager.get_device_capabilities(device_id)

            if device_info:
                return {
                    "device_id": device_id,
                    "status": device_info.status.value,
                    "server_url": device_info.server_url,
                    "local_clients": device_info.local_client_ids,
                    "capabilities": device_info.capabilities
                    + device_caps.get("capabilities", []),
                    "metadata": {
                        **device_info.metadata,
                        **device_caps.get("metadata", {}),
                    },
                    "last_heartbeat": (
                        device_info.last_heartbeat.isoformat()
                        if device_info.last_heartbeat
                        else None
                    ),
                    "connection_attempts": device_info.connection_attempts,
                }
            else:
                return {"error": f"Device {device_id} not found"}
        else:
            # Return status for all devices
            all_devices = self.device_manager.get_all_devices()
            return {
                device_id: self.get_device_status(device_id)
                for device_id in all_devices.keys()
            }

    def get_connected_devices(self) -> List[str]:
        """Get list of connected device IDs."""
        return self.device_manager.get_connected_devices()

    def get_constellation_info(self) -> Dict[str, Any]:
        """
        Get constellation information and status.

        :return: Constellation status and statistics
        """
        connected_devices = self.get_connected_devices()
        all_devices = self.device_manager.get_all_devices()

        return {
            "constellation_id": self.config.constellation_id,
            "total_devices": len(all_devices),
            "connected_devices": len(connected_devices),
            "device_list": connected_devices,
            "max_concurrent_tasks": self.config.max_concurrent_tasks,
            "heartbeat_interval": self.config.heartbeat_interval,
            "pending_tasks": len(self._pending_tasks),
            "active_callbacks": len(self._task_callbacks),
        }

    async def disconnect_device(self, device_id: str) -> None:
        """
        Disconnect from a specific device.

        :param device_id: Device to disconnect
        """
        await self.device_manager.disconnect_device(device_id)

    async def reconnect_device(self, device_id: str) -> bool:
        """
        Reconnect to a specific device.

        :param device_id: Device to reconnect
        :return: True if reconnection successful
        """
        return await self.device_manager.connect_device(device_id)

    async def shutdown(self) -> None:
        """
        Shutdown the constellation client and disconnect all devices.
        """
        self.logger.info("🛑 Shutting down Constellation Client")

        # Cancel pending tasks
        for task_id, future in self._pending_tasks.items():
            if not future.done():
                future.cancel()

        # Shutdown device manager
        await self.device_manager.shutdown()

        self.logger.info("✅ Constellation Client shutdown complete")


# Convenience functions for common operations


async def create_constellation_client(
    config_file: Optional[str] = None,
    constellation_id: Optional[str] = None,
    devices: Optional[List[Dict[str, Any]]] = None,
) -> ConstellationClient:
    """
    Create and initialize a constellation client.

    :param config_file: Path to configuration file
    :param constellation_id: Override constellation ID
    :param devices: List of device configurations
    :return: Initialized ConstellationClient
    """
    # Load configuration
    if config_file:
        config = ConstellationConfig.from_file(config_file)
    else:
        config = ConstellationConfig()

    # Add devices if provided
    if devices:
        for device in devices:
            config.add_device(
                device_id=device["device_id"],
                server_url=device["server_url"],
                local_client_ids=device["local_client_ids"],
                capabilities=device.get("capabilities"),
                metadata=device.get("metadata"),
            )

    # Create and initialize client
    client = ConstellationClient(config=config, constellation_id=constellation_id)
    await client.initialize()

    return client
