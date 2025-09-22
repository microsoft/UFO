import threading
from fastapi import WebSocket
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ClientInfo:
    """Information about a connected client."""

    websocket: WebSocket
    client_type: str  # "device" or "constellation"
    connected_at: datetime
    metadata: Dict = None


class WSManager:
    """
    WSManager is responsible for managing WebSocket connections and clients.
    Supports both device clients and constellation clients.
    """

    def __init__(self):
        """
        Initialize the WSManager.
        """
        self.online_clients: Dict[str, ClientInfo] = {}
        self.lock = threading.Lock()

    def add_client(
        self,
        client_id: str,
        ws: WebSocket,
        client_type: str = "device",
        metadata: Dict = None,
    ):
        """
        Add a new client to the online clients list.
        :param client_id: The ID of the client to add.
        :param ws: The WebSocket connection for the client.
        :param client_type: The type of client ("device" or "constellation").
        :param metadata: Additional metadata about the client.
        """
        with self.lock:
            self.online_clients[client_id] = ClientInfo(
                websocket=ws,
                client_type=client_type,
                connected_at=datetime.now(),
                metadata=metadata or {},
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
            return client_info is not None and client_info.client_type == "device"

    def list_clients_by_type(self, client_type: str) -> List[str]:
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
                if info.client_type == "device"
            )
            constellation_count = sum(
                1
                for info in self.online_clients.values()
                if info.client_type == "constellation"
            )
            return {
                "total": len(self.online_clients),
                "device_clients": device_count,
                "constellation_clients": constellation_count,
            }
