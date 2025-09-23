from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from enum import Enum

from ufo.agents.processors.schemas.actions import ActionCommandInfo


class WeavingMode(str, Enum):
    """
    Represents the weaving mode for the Constellation Agent.
    """

    CREATION = "creation"
    EDITING = "editing"


class ConstellationAgentResponse(BaseModel):
    """
    The multi-action response data for the Constellation Creation.
    """

    thought: str
    status: str
    constellation: Optional[str] = None
    action: Optional[List[ActionCommandInfo]] = None
    results: Any = None


@dataclass
class ConstellationRequestLog:
    """
    The request log data for the ConstellationAgent.
    """

    step: int
    weaving_mode: WeavingMode
    device_info: str
    constellation: str
    request: str
    prompt: Dict[str, Any]
