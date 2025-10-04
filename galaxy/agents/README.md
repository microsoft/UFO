# Galaxy Agents Module

The Agents module contains the ConstellationAgent for DAG-based task orchestration in the Galaxy Framework. This agent extends BasicAgent and implements focused interfaces for constellation creation and editing.

## 🎭 Overview

The ConstellationAgent is responsible for processing user requests into task constellations (DAGs) and updating these constellations based on task execution results. It follows the Interface Segregation Principle by implementing IRequestProcessor and IResultProcessor interfaces.

## 🏗️ Architecture

```
ufo/galaxy/agents/
├── __init__.py                     # Module exports
├── constellation_agent.py          # Main ConstellationAgent implementation
├── constellation_agent_states.py   # State machine for agent workflow
├── schema.py                       # Data schemas and enums
└── processors/                     # Request and result processing
    ├── processor.py                # ConstellationAgentProcessor
    ├── processor_context.py        # Processing context
    └── strategy.py                 # Processing strategies
```

## 🤖 Core Components

### ConstellationAgent

The primary agent that extends BasicAgent and implements constellation orchestration.

#### Key Responsibilities
- **Constellation Creation**: Process user requests to generate initial DAGs via `process_creation()`
- **Constellation Editing**: Update DAGs based on task execution results via `process_editing()`
- **State Management**: Maintain agent state through ConstellationAgentStatus states
- **Event Publishing**: Publish constellation modification events to the event bus
- **Orchestrator Coordination**: Work with TaskConstellationOrchestrator for execution

#### Interface Implementation
ConstellationAgent implements two focused interfaces:
- **IRequestProcessor**: For processing user requests into constellations
- **IResultProcessor**: For processing task results and updating constellations

#### Usage Example
```python
from galaxy.agents import ConstellationAgent
from galaxy.constellation import TaskConstellationOrchestrator
from ufo.module.context import Context

# Initialize orchestrator and agent
orchestrator = TaskConstellationOrchestrator()
agent = ConstellationAgent(
    orchestrator=orchestrator,
    name="constellation_agent"
)

# Create constellation from user request
context = Context()
context.set("user_request", "Create a data processing pipeline")

constellation = await agent.process_creation(context)
print(f"Created constellation: {constellation.constellation_id}")
print(f"Tasks: {len(constellation.tasks)}")

# Later, update constellation based on results
updated_constellation = await agent.process_editing(context)
```

#### Key Methods
- `process_creation(context: Context) -> TaskConstellation`: Generate DAG from user request
- `process_editing(context: Context) -> TaskConstellation`: Update DAG based on execution results
- `context_provision(context: Context, mask_creation: bool = True)`: Provide MCP tool context
- `orchestrator: TaskConstellationOrchestrator`: Access to the task orchestrator

#### Agent Status
The agent maintains status through ConstellationAgentStatus enum:
- **START**: Initial state, ready to create constellation
- **CONTINUE**: Waiting for task completion events  
- **FINISH**: Successfully completed
- **FAIL**: Failed state

### Agent State Machine

The agent uses a state machine defined in `constellation_agent_states.py` to manage workflow progression.

#### State Definitions
```python
class ConstellationAgentStatus(Enum):
    START = "START"          # Create and execute constellation
    CONTINUE = "CONTINUE"    # Wait for task completion events
    FINISH = "FINISH"        # Task completed successfully  
    FAIL = "FAIL"           # Task failed
```

#### State Classes
Each state has a corresponding state class that handles specific responsibilities:

- **StartConstellationAgentState**: Creates constellation and starts orchestration
- **ContinueConstellationAgentState**: Waits for task completion events and processes updates
- **FinishConstellationAgentState**: Terminal state for successful completion
- **FailConstellationAgentState**: Terminal state for failures

#### State Transitions
```
START → CONTINUE → [FINISH | FAIL]
  ↓         ↓          ↓
 FAIL ← ── FAIL ← ── FAIL
```

#### Usage Example
```python
from galaxy.agents.constellation_agent_states import StartConstellationAgentState

# Agent starts in START state
agent = ConstellationAgent(orchestrator)
assert isinstance(agent.current_state, StartConstellationAgentState)

# State transitions happen automatically based on execution
await agent.current_state.handle(agent, context)
next_state = agent.current_state.next_state(agent)
```

### Agent Processor

The ConstellationAgentProcessor handles the actual LLM interaction and action execution.

#### Key Features
- **Strategy-Based Processing**: Uses configurable strategies for different aspects
- **Context Management**: Manages processing context throughout workflow
- **Tool Integration**: Integrates with MCP tools for action execution
- **Weaving Modes**: Supports CREATION and EDITING modes

#### Weaving Modes
```python
class WeavingMode(str, Enum):
    CREATION = "creation"    # Creating new constellations
    EDITING = "editing"      # Editing existing constellations
```

#### Processing Strategies
The processor uses different strategies for:
- **ConstellationLLMInteractionStrategy**: LLM interaction and prompt management
- **ConstellationActionExecutionStrategy**: Action execution and tool calling
- **ConstellationMemoryUpdateStrategy**: Memory and context updates

#### Usage in Agent
```python
# Agent creates processor during processing
self.processor = ConstellationAgentProcessor(
    agent=self, 
    global_context=context
)

# Process with the appropriate mode
context.set(ContextNames.WEAVING_MODE, WeavingMode.CREATION)
await self.processor.process()

# Get results from context
constellation = context.get(ContextNames.CONSTELLATION)
status = self.processor.processing_context.get_local("status")
```

## 📊 Data Schemas

### WeavingMode
Defines the processing mode for the agent:
```python
class WeavingMode(str, Enum):
    CREATION = "creation"    # Creating new constellations from user requests
    EDITING = "editing"      # Editing existing constellations based on results
```

### ConstellationAgentResponse
Response format from the agent's LLM processing:
```python
class ConstellationAgentResponse(BaseModel):
    thought: str                                    # Agent's reasoning
    status: str                                     # Processing status
    constellation: Optional[str] = None             # Constellation JSON
    action: Optional[List[ActionCommandInfo]] = None # Actions to execute
    results: Any = None                            # Action results
```

### ConstellationRequestLog
Logging structure for agent requests:
```python
@dataclass
class ConstellationRequestLog:
    step: int                    # Processing step number
    weaving_mode: WeavingMode    # Current weaving mode
    device_info: str             # Target device information
    constellation: str           # Constellation state
    request: str                 # User request
    prompt: Dict[str, Any]       # LLM prompt data
```

## 🔄 Event Integration

### Event Publishing
The agent publishes events when constellations are modified:

```python
# Agent publishes constellation modification events
await self._event_bus.publish_event(
    ConstellationEvent(
        event_type=EventType.CONSTELLATION_MODIFIED,
        source_id=self.name,
        timestamp=time.time(),
        data={
            "old_constellation": before_constellation,
            "new_constellation": after_constellation,
            "modification_type": f"Edited by {self.name}",
        },
        constellation_id=after_constellation.constellation_id,
        constellation_state=after_constellation.state.value,
    )
)
```

### Task Completion Queue
The agent uses an async queue to receive task completion events:

```python
# Agent waits for task completion events in CONTINUE state
task_event = await agent.task_completion_queue.get()
agent.logger.info(
    f"Received task completion: {task_event.task_id} -> {task_event.status}"
)
```

## 🔧 MCP Tool Integration

### Context Provision
The agent loads MCP (Model Context Protocol) tools for action execution:

```python
async def context_provision(self, context: Context, mask_creation: bool = True):
    """Provide MCP tool context for the agent"""
    await self._load_mcp_context(context, mask_creation)

async def _load_mcp_context(self, context: Context, mask_creation: bool = True):
    """Load available MCP tools and create API prompt template"""
    # Get available tools
    result = await context.command_dispatcher.execute_commands([
        Command(tool_name="list_tools", parameters={"tool_type": "action"})
    ])
    
    # Create prompt template with tools
    tools_info = [MCPToolInfo(**tool) for tool in tool_list]
    self.prompter.create_api_prompt_template(tools=tools_info)
```

### Tool Masking
The constellation creation tool can be masked during editing mode:
```python
# Mask creation tool during editing
if mask_creation:
    tool_list = [
        tool for tool in tool_list 
        if tool.get("tool_name") != self._constellation_creation_tool_name
    ]
```

## � Getting Started

### Basic Agent Usage
```python
from galaxy.agents import ConstellationAgent
from galaxy.constellation import TaskConstellationOrchestrator
from ufo.module.context import Context, ContextNames
from galaxy.agents.schema import WeavingMode

# Initialize components
orchestrator = TaskConstellationOrchestrator()
agent = ConstellationAgent(orchestrator, name="my_agent")

# Setup context with user request
context = Context()
context.set("user_request", "Create a data validation pipeline")
context.set(ContextNames.WEAVING_MODE, WeavingMode.CREATION)

# Process constellation creation
constellation = await agent.process_creation(context)
print(f"Created constellation: {constellation.constellation_id}")
print(f"Agent status: {agent.status}")
```

### Advanced Agent Usage with State Management
```python
from galaxy.agents.constellation_agent_states import (
    ConstellationAgentStateManager, StartConstellationAgentState
)

# Initialize agent with state management
agent = ConstellationAgent(orchestrator)
state_manager = ConstellationAgentStateManager()

# Handle state transitions manually
current_state = agent.current_state
await current_state.handle(agent, context)

# Check if round/subtask ended
if current_state.is_round_end():
    print("Round completed")
if current_state.is_subtask_end():
    print("Subtask completed")

# Get next state
next_state = current_state.next_state(agent)
agent.set_state(next_state)
```

## 🧪 Testing

### Mock Agent Usage
Testing is supported through the mock framework in `tests/galaxy/mocks.py`:

```python
from tests.galaxy.mocks import MockConstellationAgent

# Create mock agent for testing
mock_agent = MockConstellationAgent()

# Mock agent provides predictable responses
constellation = await mock_agent.process_creation(context)
assert constellation.name == "Mock Data Processing Pipeline"
assert len(constellation.tasks) > 0
```

### Testing State Transitions
```python
from galaxy.agents.constellation_agent_states import (
    StartConstellationAgentState, ContinueConstellationAgentState
)

# Test state transitions
agent = ConstellationAgent(orchestrator)
assert isinstance(agent.current_state, StartConstellationAgentState)

# Simulate state transition
agent.status = "CONTINUE"
next_state = agent.current_state.next_state(agent)
assert isinstance(next_state, ContinueConstellationAgentState)
```

## 🔗 Integration

The agents module integrates seamlessly with other Galaxy components:

- **[Constellation](../constellation/README.md)**: Generate and manage task DAGs
- **[Session](../session/README.md)**: Coordinate workflow execution
- **[Core](../core/README.md)**: Leverage event system and interfaces
- **[Client](../client/README.md)**: Interface with device management

---

*Intelligent agents that transform natural language into executable workflows* 🎭
