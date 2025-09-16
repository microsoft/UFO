from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from ufo.agents.processors.schemas.actions import ActionCommandInfo


@dataclass
class HostAgentResponse:
    """
    The response data for the HostAgent.
    """

    observation: str
    thought: str
    status: str
    message: Optional[List[str]] = None
    questions: Optional[List[str]] = None
    current_subtask: Optional[str] = None
    plan: Optional[List[str]] = None
    comment: Optional[str] = None
    function: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None


class HostAgentResponseV2(BaseModel):
    """
    The response data for the HostAgent.
    """

    observation: str
    thought: str
    status: str
    message: Optional[List[str]] = None
    questions: Optional[List[str]] = None
    current_subtask: Optional[str] = None
    plan: Optional[List[str]] = None
    comment: Optional[str] = None
    function: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None


@dataclass
class AppAgentResponse:
    """
    The response data for the AppAgent.
    """

    observation: str
    thought: str
    status: str
    plan: Optional[List[str]] = None
    comment: Optional[str] = None
    function: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    save_screenshot: Optional[Dict[str, Any]] = None


class AppAgentResponseV2(BaseModel):
    """
    The multi-action response data for the AppAgent.
    """

    observation: str
    thought: str
    plan: Optional[List[str]] = None
    comment: Optional[str] = None
    actions: Union[List[ActionCommandInfo], ActionCommandInfo, None] = None
    save_screenshot: Optional[Dict[str, Any]] = None
