import time
from typing import Callable, Dict, List, Optional, Any, Union
import uuid
from pydantic import BaseModel, Field

from ufo.agents.agent.basic import BasicAgent
from ufo.cs.contracts import ActionBase, AppWindowControlInfo, CallbackAction, WindowInfo
import mmh3
import os

class SessionState(BaseModel):
    desktop_screen_url: Optional[str] = None
    desktop_windows_info: Optional[List[WindowInfo]] = None
    
    _control_info: Optional[List[Dict[str, Any]]] = None
    _annotation_dict: Optional[Dict[str, Any]] = None
    
    app_winddow_screen_url: Optional[list[str]] = []
    active_app_window: Optional[WindowInfo] = None
    app_window_control_info: Optional[AppWindowControlInfo] = None
    filtered_control_info: Optional[List[Dict[str, Any]]] = None
    annotation_dict: Optional[Dict[str, Any]] = None
    filtered_annotation_dict: Optional[Dict[str, Any]] = None

class SessionData(BaseModel):
    session_id: str
    state: SessionState = Field(default=SessionState())
    messages: List[str] = Field(default=[])
    actions_to_run: List[ActionBase] = Field(default=[])
    
class SessionDataManager:
    result_available = False
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_data = SessionData(session_id=session_id)
        self.action_id_setters = {}
        
    @staticmethod
    def time_hash_str(data: str):
        timestamp = int(time.time())  
        hash_value = mmh3.hash64(f"{data}-{timestamp}")[0]  # Generate hash
        return str(uuid.uuid4())  # Convert to string

    def add_action(self, action: ActionBase, setter: Callable[[Any], None] = None):
        call_id = SessionDataManager.time_hash_str(action.name)
        action.call_id = call_id
        self.session_data.actions_to_run.append(action)
        if setter is None:
            setter = lambda x: None
        self.action_id_setters[call_id] = setter
        
    def add_callback(self, callback: Callable[[Any], None] = None):
        callback_action = CallbackAction()
        call_id = SessionDataManager.time_hash_str("callback")
        callback_action.call_id = call_id
        self.session_data.actions_to_run.append(callback_action)
        if callback is None:
            callback = lambda x: None
        self.action_id_setters[call_id] = callback

    def clear_roundtrip_data(self):
        self.action_id_setters = {}
        self.session_data.actions_to_run = []
        self.session_data.messages = []
        
    def update_session_state_from_action_results(self, action_results: Dict[str, Any]):
        for call_id, result in action_results.items():
            if call_id in self.action_id_setters:
                try:
                    setter = self.action_id_setters[call_id]
                    setter(result)
                except Exception as e:
                    print(f"Error in action setter for {call_id}: {e}")
        
        self.result_available = True
        
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

    
    

    
