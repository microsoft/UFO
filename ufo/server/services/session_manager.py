import threading
from ufo.cs.service_session import ServiceSession


class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()

    def get_or_create_session(self, session_id, request=None):
        with self.lock:
            if session_id not in self.sessions:
                session = ServiceSession(
                    task=session_id,
                    should_evaluate=False,
                    id=session_id,
                    request=request,
                )
                self.sessions[session_id] = session
            return self.sessions[session_id]

    def process_action_results(self, session_id, action_results):
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].process_action_results(action_results)

    def remove_session(self, session_id):
        with self.lock:
            self.sessions.pop(session_id, None)
