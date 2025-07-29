import threading
from ufo.module.sessions.service_session import ServiceSession
from typing import Optional, Dict
import logging


class SessionManager:
    def __init__(self):
        """
        Initialize the SessionManager.
        This class manages active sessions for the UFO service.
        """
        self.sessions: Dict[str, ServiceSession] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def get_or_create_session(
        self, session_id: str, request: Optional[str] = None
    ) -> ServiceSession:
        """
        Get an existing session or create a new one if it doesn't exist.
        :param session_id: The ID of the session to retrieve or create.
        :param request: Optional request text to initialize the session.
        :return: The ServiceSession object for the session.
        """
        with self.lock:
            if session_id not in self.sessions:
                session = ServiceSession(
                    task=session_id,
                    should_evaluate=False,
                    id=session_id,
                    request=request,
                )
                self.sessions[session_id] = session
                self.logger.info(f"Created new session: {session_id}")
            else:
                self.logger.info(f"Retrieved existing session: {session_id}")

            return self.sessions[session_id]

    def process_action_results(
        self, session_id: str, action_results: Optional[Dict[str, any]] = None
    ):
        """
        Process action results for a given session.
        :param session_id: The ID of the session to update.
        :param action_results: Optional dictionary of action results to process.
        """
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].process_action_results(action_results)

    def remove_session(self, session_id: str):
        """
        Remove a session by its ID.
        :param session_id: The ID of the session to remove.
        """
        with self.lock:
            self.sessions.pop(session_id, None)
            self.logger.info(f"Removed session: {session_id}")
