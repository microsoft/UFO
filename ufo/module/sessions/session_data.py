import uuid
import logging
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from ufo.contracts.contracts import AppWindowControlInfo, Command, Result, WindowInfo


class SessionState(BaseModel):
    desktop_screen_url: Optional[str] = None
    desktop_windows_info: Optional[List[WindowInfo]] = None

    _control_info: Optional[List[Dict[str, Any]]] = None
    _annotation_dict: Optional[Dict[str, Any]] = None

    app_window_screen_url: Optional[list[str]] = []
    active_app_window: Optional[WindowInfo] = None
    app_window_control_info: Optional[AppWindowControlInfo] = None
    filtered_control_info: Optional[List[Dict[str, Any]]] = None
    annotation_dict: Optional[Dict[str, Any]] = None
    filtered_annotation_dict: Optional[Dict[str, Any]] = None


class SessionData(BaseModel):
    session_id: str
    state: SessionState = Field(default=SessionState())
    messages: List[str] = Field(default=[])
    actions_to_run: List[Command] = Field(default=[])


class SessionDataManager:
    result_available = False

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_data = SessionData(session_id=session_id)
        self.action_id_setters = {}
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def time_hash_str(data: str):
        """
        Generate a unique identifier.
        """
        # timestamp = int(time.time())
        # hash_value = mmh3.hash64(f"{data}-{timestamp}")[0]  # Generate hash
        return str(uuid.uuid4())  # Convert to string

    def add_action(self, command: Command, setter: Callable[[Any], None] = None):
        """
        Add an action to the session data manager.
        :param action: The action to be added.
        :param setter: Optional callback function to set the action result.
        If not provided, a default no-op function will be used.
        """
        call_id = SessionDataManager.time_hash_str(command.tool_name)
        command.call_id = call_id
        self.session_data.actions_to_run.append(command)
        self.logger.info(
            f"Adding action {command.tool_name} with call_id {call_id} to session {self.session_id}"
        )
        if setter is None:
            setter = lambda x: None
        self.action_id_setters[call_id] = setter

    def add_callback(self, callback: Callable[[Any], None] = None):
        """
        Add a callback action to the session data manager.
        :param callback: Optional callback function to set the action result.
        """
        nop_command = Command(
            tool_name="nop",
            parameters={},
            tool_type="action",
        )
        call_id = SessionDataManager.time_hash_str("nop")
        nop_command.call_id = call_id
        self.session_data.actions_to_run.append(nop_command)
        if callback is None:
            callback = lambda x: None
        self.action_id_setters[call_id] = callback

    def clear_roundtrip_data(self):
        """
        Clear any roundtrip data stored in the session data manager.
        """
        self.action_id_setters = {}
        self.session_data.actions_to_run = []
        self.session_data.messages = []

    def process_action_results(self, action_results: Dict[str, Result]) -> None:
        """
        Process the results of executed actions and update session state.
        This method iterates through the action results and calls the corresponding
        callbacks for each action based on its call_id.
        :param action_results: Dictionary containing results of executed actions.
        """
        for call_id, result in action_results.items():
            if call_id in self.action_id_setters:
                try:
                    setter = self.action_id_setters[call_id]
                    setter(result)
                except Exception as e:
                    self.logger.error(
                        f"Error processing action result for call_id {call_id}: {e}"
                    )

        self.result_available = True

    @property
    def actions_to_run(self) -> List[Command]:
        return self.session_data.actions_to_run

    def get_desktop_windows_info(self) -> List[Dict[str, str]]:
        windows_info = self.session_data.state.desktop_windows_info
        return [
            dict(
                label=window.annotation_id,
                control_type=window.control_type,
                control_text=window.name,
            )
            for window in windows_info
        ]
