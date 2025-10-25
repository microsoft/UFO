from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from ufo.agents.processors.schemas.actions import ActionCommandInfo


class HostAgentResponse(BaseModel):
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
    result: Optional[Any] = None


class AppAgentResponse(BaseModel):
    """
    The multi-action response data for the AppAgent.
    """

    observation: str
    thought: str
    plan: Optional[List[str]] = None
    comment: Optional[str] = None
    action: Union[List[ActionCommandInfo], ActionCommandInfo, None] = None
    save_screenshot: Optional[Dict[str, Any]] = {}
    result: Optional[Any] = None


class EvaluationAgentResponse(BaseModel):
    """
    The response data for the EvaluationAgent.
    """

    complete: str
    sub_scores: Optional[List[Dict[str, str]]] = None
    reason: Optional[str] = None
