from .agent import BasicAgent, BasicMemoryItem, BasicMemory
from dataclasses import dataclass



def update_memory_attributes(cls):
    cls.memory_attributes = cls.memory_attributes + cls._additional_attributes
    return cls



@update_memory_attributes
@dataclass
class HostAgentMemoryItem(BasicMemoryItem):
    """
    The HostAgent class the manager of AppAgents.
    """





@update_memory_attributes
@dataclass
class AppAgentMemoryItem(BasicMemoryItem):
    """
    The HostAgent class the manager of AppAgents.
    """





