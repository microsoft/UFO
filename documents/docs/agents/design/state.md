# Agent State

The `State` class is a fundamental component of the UFO agent framework. It represents the current state of the agent and determines the next action and agent to handle the request. Each agent has a specific set of states that define the agent's behavior and workflow.



## AgentStatus
The set of states for an agent is defined in the `AgentStatus` class:
    
```python
class AgentStatus(Enum):
    """
    The status class for the agent.
    """

    ERROR = "ERROR"
    FINISH = "FINISH"
    CONTINUE = "CONTINUE"
    FAIL = "FAIL"
    PENDING = "PENDING"
    CONFIRM = "CONFIRM"
    SCREENSHOT = "SCREENSHOT"
```

Each agent implements its own set of `AgentStatus` to define the states of the agent.


## AgentStateManager

The class `AgentStateManager` manages the state mapping from a string to the corresponding state class. Each state class is registered with the `AgentStateManager` using the `register` decorator to associate the state class with a specific agent, e.g.,

```python
@AgentStateManager.register
class SomeAgentState(AgentState):
    """
    The state class for the some agent.
    """
```

!!! tip
    You can find examples on how to register the state class for the `AppAgent` in the `ufo/agents/states/app_agent_state.py` file. 

Below is the basic structure of the `AgentStateManager` class:
```python
class AgentStateManager(ABC, metaclass=SingletonABCMeta):
    """
    A abstract class to manage the states of the agent.
    """

    _state_mapping: Dict[str, Type[AgentState]] = {}

    def __init__(self):
        """
        Initialize the state manager.
        """

        self._state_instance_mapping: Dict[str, AgentState] = {}

    def get_state(self, status: str) -> AgentState:
        """
        Get the state for the status.
        :param status: The status string.
        :return: The state object.
        """

        # Lazy load the state class
        if status not in self._state_instance_mapping:
            state_class = self._state_mapping.get(status)
            if state_class:
                self._state_instance_mapping[status] = state_class()
            else:
                self._state_instance_mapping[status] = self.none_state

        state = self._state_instance_mapping.get(status, self.none_state)

        return state

    def add_state(self, status: str, state: AgentState) -> None:
        """
        Add a new state to the state mapping.
        :param status: The status string.
        :param state: The state object.
        """
        self.state_map[status] = state

    @property
    def state_map(self) -> Dict[str, AgentState]:
        """
        The state mapping of status to state.
        :return: The state mapping.
        """
        return self._state_instance_mapping

    @classmethod
    def register(cls, state_class: Type[AgentState]) -> Type[AgentState]:
        """
        Decorator to register the state class to the state manager.
        :param state_class: The state class to be registered.
        :return: The state class.
        """
        cls._state_mapping[state_class.name()] = state_class
        return state_class

    @property
    @abstractmethod
    def none_state(self) -> AgentState:
        """
        The none state of the state manager.
        """
        pass
```

## AgentState
Each state class inherits from the `AgentState` class and must implement the method of `handle` to process the action in the state. In addition, the `next_state` and `next_agent` methods are used to determine the next state and agent to handle the transition. Please find below the reference for the `State` class in UFO.

::: agents.states.basic.AgentState

!!!tip
    The state machine diagrams for the `HostAgent` and `AppAgent` are shown in their respective documents.

!!!tip
    A `Round` calls the `handle`, `next_state`, and `next_agent` methods of the current state to process the user request and determine the next state and agent to handle the request, and orchestrates the agents to execute the necessary actions.
