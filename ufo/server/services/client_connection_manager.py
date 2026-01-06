import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import WebSocket

from aip.messages import ClientType
from aip.protocol.task_execution import TaskExecutionProtocol
from aip.transport.websocket import WebSocketTransport


@dataclass
class ClientInfo:
    """Information about a connected client."""

    websocket: WebSocket
    client_type: ClientType
    connected_at: datetime
    metadata: Dict = None
    platform: str = "windows"
    system_info: Dict = None  # Device system information (for device clients)

    # AIP protocol instances for this client
    transport: Optional[WebSocketTransport] = None
    task_protocol: Optional[TaskExecutionProtocol] = None


class ClientConnectionManager:
    """
    ClientConnectionManager manages client connections and their associated resources.

    Responsibilities:
    - Track connected clients (devices and constellations) with their AIP protocol instances
    - Manage session-to-client mappings for both constellation and device sessions
    - Store and retrieve device system information and configurations
    - Provide client registry and lookup services

    Supports both device clients and constellation clients.
    """

    def __init__(self, device_config_path: Optional[str] = None):
        """
        Initialize the ClientConnectionManager.
        :param device_config_path: Optional path to device configuration file (YAML/JSON)
        """
        self.online_clients: Dict[str, ClientInfo] = {}
        self.lock = threading.Lock()
        self.device_config_path = device_config_path
        self._device_configs: Dict[str, Dict[str, Any]] = {}

        # Track constellation client -> session_ids mapping
        self._constellation_sessions: Dict[str, List[str]] = {}

        # Track device -> session_ids mapping (for constellation tasks targeting this device)
        self._device_sessions: Dict[str, List[str]] = {}

        # Load device configurations if path provided
        if device_config_path:
            self._load_device_configs(device_config_path)

    def add_constellation_session(self, client_id: str, session_id: str):
        """
        Track a session started by a constellation client.

        :param client_id: The constellation client ID.
        :param session_id: The session ID.
        """
        with self.lock:
            if client_id not in self._constellation_sessions:
                self._constellation_sessions[client_id] = []
            self._constellation_sessions[client_id].append(session_id)

    def get_constellation_sessions(self, client_id: str) -> List[str]:
        """
        Get all session IDs associated with a constellation client.

        :param client_id: The constellation client ID.
        :return: List of session IDs.
        """
        with self.lock:
            return self._constellation_sessions.get(client_id, []).copy()

    def remove_constellation_sessions(self, client_id: str) -> List[str]:
        """
        Remove and return all sessions for a constellation client.

        :param client_id: The constellation client ID.
        :return: List of session IDs that were removed.
        """
        with self.lock:
            return self._constellation_sessions.pop(client_id, [])

    def add_device_session(self, device_id: str, session_id: str):
        """
        Track a session running on a specific device.

        :param device_id: The target device ID.
        :param session_id: The session ID.
        """
        with self.lock:
            if device_id not in self._device_sessions:
                self._device_sessions[device_id] = []
            self._device_sessions[device_id].append(session_id)

    def get_device_sessions(self, device_id: str) -> List[str]:
        """
        Get all session IDs running on a specific device.

        :param device_id: The device ID.
        :return: List of session IDs.
        """
        with self.lock:
            return self._device_sessions.get(device_id, []).copy()

    def remove_device_sessions(self, device_id: str) -> List[str]:
        """
        Remove and return all sessions for a device.

        :param device_id: The device ID.
        :return: List of session IDs that were removed.
        """
        with self.lock:
            return self._device_sessions.pop(device_id, [])

    def add_client(
        self,
        client_id: str,
        platform: str,
        ws: WebSocket,
        client_type: ClientType = ClientType.DEVICE,
        metadata: Dict = None,
        transport: Optional[WebSocketTransport] = None,
        task_protocol: Optional[TaskExecutionProtocol] = None,
    ):
        """
        Add a new client to the online clients list.
        :param client_id: The ID of the client to add.
        :param ws: The WebSocket connection for the client.
        :param client_type: The type of client ("device" or "constellation").
        :param metadata: Additional metadata about the client.
        :param transport: Optional AIP WebSocketTransport instance for this client.
        :param task_protocol: Optional AIP TaskExecutionProtocol instance for this client.
        """
        with self.lock:
            # Extract and merge system info with server config for device clients
            system_info = None
            if (
                metadata
                and "system_info" in metadata
                and client_type == ClientType.DEVICE
            ):
                system_info = metadata.get("system_info")

                # Merge with server-configured metadata if available
                server_config = self._device_configs.get(client_id, {})
                if server_config:
                    system_info = self._merge_device_info(system_info, server_config)
                    import logging

                    logging.getLogger(__name__).info(
                        f"[ClientConnectionManager] Merged server config for device {client_id}"
                    )

            self.online_clients[client_id] = ClientInfo(
                websocket=ws,
                platform=platform,
                client_type=client_type,
                connected_at=datetime.now(),
                metadata=metadata or {},
                system_info=system_info,
                transport=transport,
                task_protocol=task_protocol,
            )

    def remove_client(self, client_id: str):
        """
        Remove a client from the online clients list.
        :param client_id: The ID of the client to remove.
        """
        with self.lock:
            self.online_clients.pop(client_id, None)

    def get_client(self, client_id: str) -> WebSocket:
        """
        Get a client WebSocket connection by its ID.
        :param client_id: The ID of the client to retrieve.
        :return: The WebSocket connection for the client if it exists, None otherwise.
        """
        with self.lock:
            client_info = self.online_clients.get(client_id)
            return client_info.websocket if client_info else None

    def get_client_info(self, client_id: str) -> ClientInfo:
        """
        Get complete client information by its ID.
        :param client_id: The ID of the client to retrieve.
        :return: The ClientInfo for the client if it exists, None otherwise.
        """
        with self.lock:
            return self.online_clients.get(client_id)

    def get_task_protocol(self, client_id: str) -> Optional[TaskExecutionProtocol]:
        """
        Get the AIP TaskExecutionProtocol for a client.
        :param client_id: The ID of the client.
        :return: The TaskExecutionProtocol instance if it exists, None otherwise.
        """
        with self.lock:
            client_info = self.online_clients.get(client_id)
            return client_info.task_protocol if client_info else None

    def get_client_type(self, client_id: str) -> str:
        """
        Get the type of a client.
        :param client_id: The ID of the client.
        :return: The client type ("device" or "constellation") or None if not found.
        """
        with self.lock:
            client_info = self.online_clients.get(client_id)
            return client_info.client_type if client_info else None

    def list_clients(self) -> List[str]:
        """
        List all online clients.
        :return: A list of online client IDs.
        """
        with self.lock:
            return list(self.online_clients.keys())

    def is_device_connected(self, device_id: str) -> bool:
        """
        Check if a specific device is connected and is of type 'device'.
        :param device_id: The device ID to check.
        :return: True if the device is connected and is a device client, False otherwise.
        """
        with self.lock:
            client_info = self.online_clients.get(device_id)
            return (
                client_info is not None and client_info.client_type == ClientType.DEVICE
            )

    def list_clients_by_type(self, client_type: ClientType) -> List[str]:
        """
        List all online clients of a specific type.
        :param client_type: The type of clients to list ("device" or "constellation").
        :return: A list of online client IDs of the specified type.
        """
        with self.lock:
            return [
                client_id
                for client_id, client_info in self.online_clients.items()
                if client_info.client_type == client_type
            ]

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about connected clients.
        :return: A dictionary with client statistics.
        """
        with self.lock:
            device_count = sum(
                1
                for info in self.online_clients.values()
                if info.client_type == ClientType.DEVICE
            )
            constellation_count = sum(
                1
                for info in self.online_clients.values()
                if info.client_type == ClientType.CONSTELLATION
            )
            return {
                "total": len(self.online_clients),
                "device_clients": device_count,
                "constellation_clients": constellation_count,
            }

    def get_device_system_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device system information by device ID.

        :param device_id: The device ID to retrieve information for.
        :return: Device system information dictionary, or None if not found or not a device.
        """
        with self.lock:
            client_info = self.online_clients.get(device_id)
            if client_info and client_info.client_type == ClientType.DEVICE:
                return client_info.system_info
            return None

    def get_all_devices_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get system information for all connected devices.

        :return: Dictionary mapping device_id to system_info.
        """
        with self.lock:
            return {
                device_id: client_info.system_info
                for device_id, client_info in self.online_clients.items()
                if client_info.client_type == ClientType.DEVICE
                and client_info.system_info
            }

    def _load_device_configs(self, config_path: str) -> None:
        """
        Load device configurations from a YAML or JSON file.

        Expected format:
        devices:
          device_id_1:
            tags: ["production", "office"]
            tier: "high_performance"
            ...
          device_id_2:
            ...

        :param config_path: Path to configuration file
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            path = Path(config_path)
            if not path.exists():
                logger.warning(
                    f"[ClientConnectionManager] Device config file not found: {config_path}"
                )
                return

            # Support both YAML and JSON
            if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                import yaml

                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
            elif config_path.endswith(".json"):
                import json

                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            else:
                logger.warning(
                    f"[ClientConnectionManager] Unsupported config file format: {config_path}"
                )
                return

            # Extract device-specific configurations
            if config and "devices" in config:
                self._device_configs = config["devices"]
                logger.info(
                    f"[ClientConnectionManager] Loaded {len(self._device_configs)} device configurations"
                )
            else:
                logger.warning(
                    "[ClientConnectionManager] No 'devices' section found in config file"
                )

        except Exception as e:
            logger.error(
                f"[ClientConnectionManager] Error loading device configs: {e}",
                exc_info=True,
            )

    def _merge_device_info(
        self, system_info: Dict[str, Any], server_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge device system information with server configuration.

        Server config takes precedence for overlapping keys, except for
        special cases like capabilities which are merged.

        :param system_info: Auto-detected system information from device
        :param server_config: Server-configured metadata
        :return: Merged dictionary
        """
        merged = {**system_info}

        # Add all server config to custom_metadata
        if "custom_metadata" not in merged:
            merged["custom_metadata"] = {}

        # Merge server config into custom_metadata
        merged["custom_metadata"].update(server_config)

        # Special handling: merge capabilities if both exist
        if (
            "supported_features" in system_info
            and "additional_features" in server_config
        ):
            merged["supported_features"] = list(
                set(
                    system_info["supported_features"]
                    + server_config["additional_features"]
                )
            )

        # Add server tags if provided
        if "tags" in server_config:
            merged["tags"] = server_config["tags"]

        return merged
