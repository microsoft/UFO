from .basic import BasicMemoryItem, BasicMemory
from dataclasses import dataclass, field
from typing import List


@dataclass
class HostAgentMemoryItem(BasicMemoryItem):
    """
    The HostAgent class the manager of AppAgents.
    """
    _additional_attributes: List[str] = field(default_factory=list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._memory_attributes = self._memory_attributes + self._additional_attributes



@dataclass
class AppAgentMemoryItem(BasicMemoryItem):
    """
    The AppAgent class the manager of.
    """
    _additional_attributes: List[str] = field(default_factory=list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._memory_attributes = self._memory_attributes + self._additional_attributes





