import logging
import threading
from typing import Any, Dict, Optional

from fastapi import WebSocket

from ufo.config import Config
from ufo.module.sessions.service_session import ServiceSession

configs = Config.get_instance().config_data


class SessionManager:
    """
    This class manages active sessions for the UFO service.
    """

    def __init__(self):
        """
        Initialize the SessionManager.
        This class manages active sessions for the UFO service.
        """
        self.sessions: Dict[str, ServiceSession] = {}

        # Mapping of task names to session IDs
        self.session_id_dict: Dict[str, str] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.results: Dict[str, Dict[str, Any]] = {}

    def get_or_create_session(
        self,
        session_id: str,
        task_name: Optional[str] = "test_task",
        request: Optional[str] = None,
        websocket: Optional[WebSocket] = None,
    ) -> ServiceSession:
        """
        Get an existing session or create a new one if it doesn't exist.
        :param session_id: The ID of the session to retrieve or create.
        :param request: Optional request text to initialize the session.
        :param websocket: Optional WebSocket connection to attach to the session.
        :return: The ServiceSession object for the session.
        """
        with self.lock:
            if session_id not in self.sessions:
                session = ServiceSession(
                    task=task_name,
                    should_evaluate=configs.get("EVA_SESSION", False),
                    id=session_id,
                    request=request,
                    websocket=websocket,
                )

                self.session_id_dict[task_name] = session_id
                self.sessions[session_id] = session
                self.logger.info(f"Created new session: {session_id}")
            else:
                self.logger.info(f"Retrieved existing session: {session_id}")

            return self.sessions[session_id]

    def get_result(self, session_id: str) -> Optional[Dict[str, any]]:
        """
        Get the result of a completed session.
        :param session_id: The ID of the session to retrieve the result for.
        :return: A dictionary containing the session result, or None if not found.
        """
        with self.lock:
            if session_id in self.sessions:
                return self.sessions[session_id].results
            return None

    def get_result_by_task(self, task_name: str) -> Optional[Dict[str, any]]:
        """
        Get the result of a completed session by task name.
        :param task_name: The name of the task to retrieve the result for.
        :return: A dictionary containing the session result, or None if not found.
        """
        with self.lock:
            session_id = self.session_id_dict.get(task_name)
            if session_id:
                return self.get_result(session_id)

    def set_results(self, session_id: str):
        """
        Set the result for a completed session.
        :param session_id: The ID of the session to set the result for.
        """
        with self.lock:
            if session_id in self.sessions:
                self.results[session_id] = self.sessions[session_id].results

    def remove_session(self, session_id: str):
        """
        Remove a session by its ID.
        :param session_id: The ID of the session to remove.
        """
        with self.lock:
            self.sessions.pop(session_id, None)
            self.logger.info(f"Removed session: {session_id}")
