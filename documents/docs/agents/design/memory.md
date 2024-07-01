# Agent Memory

The `Memory` manages the memory of the agent and stores the information required for the agent to interact with the user and applications at every step. Parts of elements in the `Memory` will be visible to the agent for decision-making.


## MemoryItem
A `MemoryItem` is a `dataclass` that represents a single step in the agent's memory. The fields of a `MemoryItem` is flexible and can be customized based on the requirements of the agent. The `MemoryItem` class is defined as follows:

::: agents.memory.memory.MemoryItem

!!!info
    At each step, an instance of `MemoryItem` is created and stored in the `Memory` to record the information of the agent's interaction with the user and applications. 


## Memory
The `Memory` class is responsible for managing the memory of the agent. It stores a list of `MemoryItem` instances that represent the agent's memory at each step. The `Memory` class is defined as follows:

::: agents.memory.memory.Memory

!!!info
    Each agent has its own `Memory` instance to store their information.

!!!info
    Not all information in the `Memory` are provided to the agent for decision-making. The agent can access parts of the memory based on the requirements of the agent's logic.