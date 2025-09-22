from dataclasses import dataclass
from typing import Any, Dict, Optional

from pydantic import BaseModel
from enum import Enum


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
    editing: Optional[str] = None
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
