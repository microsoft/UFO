# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Modular Constellation Client

Refactored client that uses modular orchestration components for clean separation of concerns.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable

from .device_manager import ConstellationDeviceManager
from .components import DeviceInfo, TaskRequest
from .config_loader import ConstellationConfig, DeviceConfig
from .orchestration import (
    TaskOrchestrator,
    ParallelTaskManager,
    DeviceSelector,
    ClientEventHandler,
    StatusManager,
    ClientConfigManager,
)


class ModularConstellationClient:
    """
    Modular Constellation Client with single responsibility components.

    This refactored class delegates responsibilities to focused orchestration components:
    - TaskOrchestrator: Single task execution and management
    - ParallelTaskManager: Multi-task parallel execution
    - DeviceSelector: Device selection based on capabilities
    - ClientEventHandler: Event handling and callbacks
    - StatusManager: Status reporting and information management
    - ClientConfigManager: Configuration-based initialization
    """

    def __init__(
        self,
        config: Optional[ConstellationConfig] = None,
        constellation_id: Optional[str] = None,
    ):
        """
        Initialize the modular constellation client.

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

        # Initialize modular orchestration components
        self.device_selector = DeviceSelector(self.device_manager)
        self.task_orchestrator = TaskOrchestrator(self.device_manager)
        self.parallel_task_manager = ParallelTaskManager(
            self.task_orchestrator,
            self.device_selector,
            self.config.max_concurrent_tasks,
        )
        self.event_handler = ClientEventHandler()
        self.status_manager = StatusManager(
            self.device_manager,
            self.config,
            self.task_orchestrator._task_callbacks,  # Reference to pending tasks
        )
        self.config_manager = ClientConfigManager(self.device_manager)

        # Setup event handlers
        self._setup_event_handlers()

        self.logger = logging.getLogger(__name__)

    def _setup_event_handlers(self) -> None:
        """Setup event handlers for device manager events."""
        self.device_manager.add_connection_handler(
            self.event_handler.handle_device_connected
        )
        self.device_manager.add_disconnection_handler(
            self.event_handler.handle_device_disconnected
        )
        self.device_manager.add_task_completion_handler(self._on_task_completed)

    async def _on_task_completed(
        self, device_id: str, task_id: str, result: Dict[str, Any]
    ) -> None:
        """Handle task completion events from device manager."""
        # Delegate to orchestration components
        await self.task_orchestrator.handle_task_completion(task_id, device_id, result)
        await self.event_handler.handle_task_completed(device_id, task_id, result)

    # Configuration and Initialization
    async def initialize(self) -> Dict[str, bool]:
        """
        Initialize the constellation client and register devices from configuration.

        :return: Dictionary mapping device_id to registration success status
        """
        self.logger.info(
            f"🚀 Initializing Modular Constellation Client: {self.config.constellation_id}"
        )
        return await self.config_manager.initialize_from_config(self.config)

    async def register_device_from_config(self, device_config: DeviceConfig) -> bool:
        """Register a device from configuration."""
        return await self.config_manager.register_device_from_config(device_config)

    async def register_device(
        self,
        device_id: str,
        server_url: str,
        local_client_ids: List[str],
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_connect: bool = True,
    ) -> bool:
        """Register a device manually."""
        return await self.device_manager.register_device(
            device_id=device_id,
            server_url=server_url,
            local_client_ids=local_client_ids,
            capabilities=capabilities,
            metadata=metadata,
            auto_connect=auto_connect,
        )

    # Task Execution
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
        # Auto-select device if not specified
        if not device_id:
            device_id = await self.device_selector.select_best_device(
                capabilities_required
            )
            if not device_id:
                raise ValueError("No suitable device available for task execution")

        # Execute task via orchestrator
        return await self.task_orchestrator.execute_task(
            request=request,
            device_id=device_id,
            target_client_id=target_client_id,
            task_name=task_name,
            metadata=metadata,
            timeout=timeout,
            callback=callback,
        )

    async def execute_tasks_parallel(
        self,
        tasks: List[Dict[str, Any]],
        max_concurrent: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Execute multiple tasks in parallel across devices."""
        return await self.parallel_task_manager.execute_tasks_parallel(
            tasks, max_concurrent
        )

    async def execute_tasks_with_dependencies(
        self,
        task_dag: Dict[str, Dict[str, Any]],
        max_concurrent: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Execute tasks with dependency resolution (DAG execution)."""
        return await self.parallel_task_manager.execute_tasks_with_dependencies(
            task_dag, max_concurrent
        )

    # Device Selection and Management
    def select_best_device(
        self,
        capabilities_required: Optional[List[str]] = None,
        device_type_preference: Optional[str] = None,
        exclude_devices: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Select the best available device for task execution."""
        # Note: This is synchronous wrapper for the async method
        # In practice, you might want to cache device selection results
        return asyncio.create_task(
            self.device_selector.select_best_device(
                capabilities_required, device_type_preference, exclude_devices
            )
        )

    def rank_devices_by_suitability(
        self,
        capabilities_required: Optional[List[str]] = None,
        device_type_preference: Optional[str] = None,
        exclude_devices: Optional[List[str]] = None,
    ) -> List[tuple]:
        """Rank all connected devices by their suitability for a task."""
        return self.device_selector.rank_devices_by_suitability(
            capabilities_required, device_type_preference, exclude_devices
        )

    # Event Handler Management
    def add_connection_handler(self, handler: Callable) -> None:
        """Add a handler for device connection events"""
        self.event_handler.add_connection_handler(handler)

    def add_disconnection_handler(self, handler: Callable) -> None:
        """Add a handler for device disconnection events"""
        self.event_handler.add_disconnection_handler(handler)

    def add_task_completion_handler(self, handler: Callable) -> None:
        """Add a handler for task completion events"""
        self.event_handler.add_task_completion_handler(handler)

    def add_error_handler(self, handler: Callable) -> None:
        """Add a handler for error events"""
        self.event_handler.add_error_handler(handler)

    # Status and Information
    def get_device_status(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Get device status information."""
        return self.status_manager.get_device_status(device_id)

    def get_connected_devices(self) -> List[str]:
        """Get list of connected device IDs."""
        return self.status_manager.get_connected_devices()

    def get_constellation_info(self) -> Dict[str, Any]:
        """Get constellation information and status."""
        return self.status_manager.get_constellation_info()

    def get_device_health_summary(self) -> Dict[str, Any]:
        """Get a health summary of all devices."""
        return self.status_manager.get_device_health_summary()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the constellation."""
        return self.status_manager.get_performance_metrics()

    def get_diagnostics_report(self) -> Dict[str, Any]:
        """Generate a comprehensive diagnostics report."""
        return self.status_manager.get_diagnostics_report()

    # Configuration Management
    def validate_config(
        self, config: Optional[ConstellationConfig] = None
    ) -> Dict[str, Any]:
        """Validate a constellation configuration."""
        return self.config_manager.validate_config(config or self.config)

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return self.config_manager.get_config_summary(self.config)

    async def add_device_to_config(
        self,
        device_id: str,
        server_url: str,
        local_client_ids: List[str],
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_connect: bool = True,
        register_immediately: bool = True,
    ) -> bool:
        """Add a new device to the configuration and optionally register it."""
        return await self.config_manager.add_device_to_config(
            self.config,
            device_id,
            server_url,
            local_client_ids,
            capabilities,
            metadata,
            auto_connect,
            register_immediately,
        )

    # Device Operations
    async def disconnect_device(self, device_id: str) -> None:
        """Disconnect from a specific device."""
        await self.device_manager.disconnect_device(device_id)

    async def reconnect_device(self, device_id: str) -> bool:
        """Reconnect to a specific device."""
        return await self.device_manager.connect_device(device_id)

    # Lifecycle Management
    async def shutdown(self) -> None:
        """Shutdown the constellation client and disconnect all devices."""
        self.logger.info("🛑 Shutting down Modular Constellation Client")

        # Cleanup orchestration components
        self.task_orchestrator.cleanup_callbacks()
        self.event_handler.clear_all_handlers()

        # Shutdown device manager
        await self.device_manager.shutdown()

        self.logger.info("✅ Modular Constellation Client shutdown complete")


# Convenience functions for backward compatibility and common operations


async def create_modular_constellation_client(
    config_file: Optional[str] = None,
    constellation_id: Optional[str] = None,
    devices: Optional[List[Dict[str, Any]]] = None,
) -> ModularConstellationClient:
    """
    Create and initialize a modular constellation client.

    :param config_file: Path to configuration file
    :param constellation_id: Override constellation ID
    :param devices: List of device configurations
    :return: Initialized ModularConstellationClient
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
    client = ModularConstellationClient(
        config=config, constellation_id=constellation_id
    )
    await client.initialize()

    return client


# Alias for backward compatibility
ConstellationClientV2 = ModularConstellationClient
create_constellation_client_v2 = create_modular_constellation_client
