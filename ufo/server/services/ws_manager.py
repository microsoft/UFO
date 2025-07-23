import threading


class WSManager:
    def __init__(self):
        self.online_clients = {}
        self.lock = threading.Lock()

    def add_client(self, client_id, ws):
        with self.lock:
            self.online_clients[client_id] = ws

    def remove_client(self, client_id):
        with self.lock:
            self.online_clients.pop(client_id, None)

    def get_client(self, client_id):
        with self.lock:
            return self.online_clients.get(client_id)

    def list_clients(self):
        with self.lock:
            return list(self.online_clients.keys())
