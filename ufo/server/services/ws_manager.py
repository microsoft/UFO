import threading
from websockets import WebSocketServerProtocol
from typing import List


class WSManager:
    """
    WSManager is responsible for managing WebSocket connections and clients.
    """

    def __init__(self):
        """
        Initialize the WSManager.
        """
        self.online_clients = {}
        self.lock = threading.Lock()

    def add_client(self, client_id: str, ws: WebSocketServerProtocol):
        """
        Add a new client to the online clients list.
        :param client_id: The ID of the client to add.
        :param ws: The WebSocket connection for the client.
        """
        with self.lock:
            self.online_clients[client_id] = ws

    def remove_client(self, client_id: str):
        """
        Remove a client from the online clients list.
        :param client_id: The ID of the client to remove.
        """
        with self.lock:
            self.online_clients.pop(client_id, None)

    def get_client(self, client_id: str) -> WebSocketServerProtocol:
        """
        Get a client WebSocket connection by its ID.
        :param client_id: The ID of the client to retrieve.
        :return: The WebSocket connection for the client if it exists, None otherwise.
        """
        with self.lock:
            return self.online_clients.get(client_id)

    def list_clients(self) -> List[str]:
        """
        List all online clients.
        :return: A list of online client IDs.
        """
        with self.lock:
            return list(self.online_clients.keys())
