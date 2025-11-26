# Processing Strategy Pattern

## Overview

The Constellation Agent employs a sophisticated **multi-phase processing architecture** based on the [`ProcessorTemplate`](../../infrastructure/agents/design/processor.md) framework. The core orchestrator `ConstellationAgentProcessor` assembles different processing strategies for three distinct phases: **LLM Interaction**, **Action Execution**, and **Memory Update**. This modular design separates concerns, enables mode-specific behaviors, and provides robust error handling across the processing pipeline.

The Constellation Agent uses `ConstellationAgentProcessor` as the central orchestrator, which dynamically creates and configures processing strategies based on the weaving mode (CREATION vs. EDITING). This follows the Template Method pattern with Strategy composition.

### Core Architecture

```mermaid
classDiagram
    class ProcessorTemplate {
        <<abstract>>
        +process()*
        +_setup_strategies()*
        +_setup_middleware()*
        -strategies: Dict
        -middleware_chain: List
    }
    
    class ConstellationAgentProcessor {
        +_setup_strategies()
        +_setup_middleware()
        +_get_processor_specific_context_data()
    }
    
    class ConstellationStrategyFactory {
        +create_llm_interaction_strategy()
        +create_action_execution_strategy(mode)
        +create_memory_update_strategy()
    }
    
    class ConstellationLLMInteractionStrategy {
        +execute()
        -_build_comprehensive_prompt()
        -_get_llm_response_with_retry()
        -_parse_and_validate_response()
    }
    
    class BaseConstellationActionExecutionStrategy {
        <<abstract>>
        +execute()
        +_create_mode_specific_action_info()*
        +publish_actions()*
        +sync_constellation()*
        -_execute_constellation_action()
    }
    
    class ConstellationCreationActionExecutionStrategy {
        +_create_mode_specific_action_info()
        +publish_actions()
        +sync_constellation()
    }
    
    class ConstellationEditingActionExecutionStrategy {
        +_create_mode_specific_action_info()
        +publish_actions()
        +sync_constellation()
    }
    
    class ConstellationMemoryUpdateStrategy {
        +execute()
        -_create_additional_memory_data()
        -_create_and_populate_memory_item()
    }
    
    ProcessorTemplate <|-- ConstellationAgentProcessor
    ConstellationAgentProcessor --> ConstellationStrategyFactory : uses
    ConstellationStrategyFactory --> ConstellationLLMInteractionStrategy : creates
    ConstellationStrategyFactory --> BaseConstellationActionExecutionStrategy : creates
    ConstellationStrategyFactory --> ConstellationMemoryUpdateStrategy : creates
    BaseConstellationActionExecutionStrategy <|-- ConstellationCreationActionExecutionStrategy
    BaseConstellationActionExecutionStrategy <|-- ConstellationEditingActionExecutionStrategy
```

### Processing Phases

| Phase | Strategy | Purpose | Mode-Specific |
|-------|----------|---------|---------------|
| **LLM Interaction** | `ConstellationLLMInteractionStrategy` | Prompt construction, LLM response parsing | ❌ Shared |
| **Action Execution** | `ConstellationCreation/EditingActionExecutionStrategy` | Action generation and execution | ✅ Mode-specific |
| **Memory Update** | `ConstellationMemoryUpdateStrategy` | Memory logging and state tracking | ❌ Shared |

---

## Processor Framework

### ConstellationAgentProcessor

The `ConstellationAgentProcessor` extends `ProcessorTemplate` to orchestrate the entire processing workflow. It assembles strategies based on weaving mode and manages the execution pipeline.

#### Initialization

```python
class ConstellationAgentProcessor(ProcessorTemplate):
    """Enhanced processor for Constellation Agent."""
    
    processor_context_class: Type[ConstellationProcessorContext] = (
        ConstellationProcessorContext
    )
    
    def __init__(
        self,
        agent: "ConstellationAgent",
        global_context: Context
    ) -> None:
        """Initialize with agent and global context."""
        super().__init__(agent, global_context)
```

#### Strategy Assembly

The processor creates appropriate strategies based on weaving mode:

```python
def _setup_strategies(self) -> None:
    """Configure processing strategies using factory pattern."""
    
    # Get weaving mode from context
    weaving_mode = self.global_context.get(ContextNames.WEAVING_MODE)
    
    if not weaving_mode:
        raise ValueError("Weaving mode must be specified in global context")
    
    # Create strategies via factory
    self.strategies[ProcessingPhase.LLM_INTERACTION] = (
        ConstellationStrategyFactory.create_llm_interaction_strategy(
            fail_fast=True,  # LLM interaction failure should trigger recovery
        )
    )
    
    self.strategies[ProcessingPhase.ACTION_EXECUTION] = (
        ConstellationStrategyFactory.create_action_execution_strategy(
            weaving_mode=weaving_mode,
            fail_fast=False,  # Action failures can be handled gracefully
        )
    )
    
    self.strategies[ProcessingPhase.MEMORY_UPDATE] = (
        ConstellationStrategyFactory.create_memory_update_strategy(
            fail_fast=False  # Memory update failures shouldn't stop the process
        )
    )
```

#### Middleware Configuration

```python
def _setup_middleware(self) -> None:
    """Set up enhanced middleware chain with comprehensive monitoring."""
    self.middleware_chain = [
        ConstellationLoggingMiddleware()  # Specialized logging for Constellation Agent
    ]
```

#### Context Management

```python
def _get_processor_specific_context_data(self) -> Dict[str, Any]:
    """Provide Constellation-specific context initialization."""
    
    before_constellation = self.global_context.get(
        ContextNames.CONSTELLATION
    )
    
    return {
        "weaving_mode": self.global_context.get(ContextNames.WEAVING_MODE),
        "device_info": self.global_context.get(ContextNames.DEVICE_INFO),
        "constellation_before": (
            before_constellation.to_json() if before_constellation else None
        ),
    }
```

### Processing Context

The `ConstellationProcessorContext` extends `BasicProcessorContext` with constellation-specific data:

```python
@dataclass
class ConstellationProcessorContext(BasicProcessorContext):
    """Constellation-specific processor context."""
    
    # Agent metadata
    agent_type: str = "ConstellationAgent"
    weaving_mode: str = "CREATION"
    
    # Device and constellation state
    device_info: List[Dict] = field(default_factory=list)
    constellation_before: Optional[str] = None
    constellation_after: Optional[str] = None
    
    # Action information
    action_info: Optional[ActionCommandInfo] = None
    target: Optional[TargetInfo] = None
    
    # Performance tracking
    llm_cost: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
```

---

## Strategy Factory

### ConstellationStrategyFactory

The factory provides centralized strategy creation with mode-aware instantiation.

#### Factory Methods

```python
class ConstellationStrategyFactory:
    """Factory for creating Constellation processing strategies."""
    
    _action_execution_strategies: Dict[WeavingMode, Type[BaseProcessingStrategy]] = {
        WeavingMode.CREATION: ConstellationCreationActionExecutionStrategy,
        WeavingMode.EDITING: ConstellationEditingActionExecutionStrategy,
    }
    
    @classmethod
    def create_llm_interaction_strategy(
        cls,
        fail_fast: bool = True
    ) -> BaseProcessingStrategy:
        """Create LLM interaction strategy (shared across modes)."""
        return ConstellationLLMInteractionStrategy(fail_fast)
    
    @classmethod
    def create_action_execution_strategy(
        cls,
        weaving_mode: WeavingMode,
        fail_fast: bool = False
    ) -> BaseProcessingStrategy:
        """Create mode-specific action execution strategy."""
        
        if weaving_mode not in cls._action_execution_strategies:
            raise ValueError(f"Unsupported mode: {weaving_mode}")
        
        strategy_class = cls._action_execution_strategies[weaving_mode]
        return strategy_class(fail_fast=fail_fast)
    
    @classmethod
    def create_memory_update_strategy(
        cls,
        fail_fast: bool = False
    ) -> BaseProcessingStrategy:
        """Create memory update strategy (shared across modes)."""
        return ConstellationMemoryUpdateStrategy(fail_fast=fail_fast)
```

#### Batch Strategy Creation

```python
@classmethod
def create_all_strategies(
    cls,
    weaving_mode: WeavingMode,
    llm_fail_fast: bool = True,
    action_fail_fast: bool = False,
    memory_fail_fast: bool = False,
) -> Dict[str, BaseProcessingStrategy]:
    """Create all required strategies for a weaving mode."""
    
    return {
        "llm_interaction": cls.create_llm_interaction_strategy(llm_fail_fast),
        "action_execution": cls.create_action_execution_strategy(
            weaving_mode, action_fail_fast
        ),
        "memory_update": cls.create_memory_update_strategy(memory_fail_fast),
    }
```

**Note:** The `create_llm_interaction_strategy()` returns a shared `ConstellationLLMInteractionStrategy` (not mode-specific), as LLM interaction logic is the same across creation and editing modes.

---

## LLM Interaction Strategy

### ConstellationLLMInteractionStrategy

Handles prompt construction, LLM communication, and response parsing. This strategy is **shared across both creation and editing modes**, with mode-specific prompt generation delegated to the agent's prompter.

#### Strategy Execution

```python
@provides(
    "parsed_response",
    "response_text",
    "llm_cost",
    "prompt_message",
    "status",
)
class ConstellationLLMInteractionStrategy(BaseProcessingStrategy):
    """LLM interaction strategy for Constellation Agent."""
    
    async def execute(
        self,
        agent: "ConstellationAgent",
        context: ProcessingContext
    ) -> ProcessingResult:
        """Execute LLM interaction with retry logic."""
        
        try:
            # Extract context
            session_step = context.get_local("session_step", 0)
            device_info = context.get_local("device_info", {})
            constellation = context.get_global("CONSTELLATION")
            request = context.get("request", "")
            
            # Build prompt (delegates to agent's prompter)
            prompt_message = await self._build_comprehensive_prompt(
                agent, device_info, constellation, request, ...
            )
            
            # Get LLM response with retry
            response_text, llm_cost = await self._get_llm_response_with_retry(
                agent, prompt_message
            )
            
            # Parse and validate
            parsed_response = self._parse_and_validate_response(
                agent, response_text
            )
            
            return ProcessingResult(
                success=True,
                data={
                    "parsed_response": parsed_response,
                    "response_text": response_text,
                    "llm_cost": llm_cost,
                    **parsed_response.model_dump(),
                },
                phase=ProcessingPhase.LLM_INTERACTION,
            )
            
        except Exception as e:
            return self.handle_error(e, ProcessingPhase.LLM_INTERACTION, context)
```

#### Prompt Construction

The strategy delegates mode-specific prompt building to the agent's prompter:

```python
async def _build_comprehensive_prompt(
    self,
    agent: "ConstellationAgent",
    device_info: Dict,
    constellation: TaskConstellation,
    request: str,
    ...
) -> Dict[str, Any]:
    """Build prompt using agent's mode-specific prompter."""
    
    # Agent's message_constructor uses the appropriate prompter
    # (ConstellationCreationPrompter or ConstellationEditingPrompter)
    prompt_message = agent.message_constructor(
        request=request,
        device_info=device_info,
        constellation=constellation
    )
    
    # Log request for debugging
    self._log_request_data(...)
    
    return prompt_message
```

The LLM strategy doesn't implement prompt construction directly. Instead, it calls `agent.message_constructor()`, which delegates to the appropriate prompter based on weaving mode. For details on prompter design, see the [Prompter Framework](../../infrastructure/agents/design/prompter.md). The prompters are responsible for mode-specific prompt formatting.

#### Retry Logic

```python
async def _get_llm_response_with_retry(
    self,
    agent: "ConstellationAgent",
    prompt_message: Dict[str, Any]
) -> tuple[str, float]:
    """Get LLM response with retry for JSON parsing failures."""
    
    max_retries = ufo_config.system.JSON_PARSING_RETRY
    
    for retry_count in range(max_retries):
        try:
            # Get response from LLM
            response_text, cost = await asyncio.get_event_loop().run_in_executor(
                None,
                agent.get_response,
                prompt_message,
                AgentType.CONSTELLATION,
                True  # use_backup_engine
            )
            
            # Validate JSON parsing
            agent.response_to_dict(response_text)
            
            return response_text, cost
            
        except Exception as e:
            if retry_count < max_retries - 1:
                self.logger.warning(f"Retry {retry_count + 1}/{max_retries}")
            else:
                raise Exception(f"Failed after {max_retries} attempts: {e}")
```

#### Response Validation

```python
def _parse_and_validate_response(
    self,
    agent: "ConstellationAgent",
    response_text: str
) -> ConstellationAgentResponse:
    """Parse and validate LLM response."""
    
    response_dict = agent.response_to_dict(response_text)
    parsed_response = ConstellationAgentResponse.model_validate(response_dict)
    
    # Validate required fields
    if not parsed_response.thought:
        raise ValueError("Missing 'thought' field")
    if not parsed_response.status:
        raise ValueError("Missing 'status' field")
    
    agent.print_response(parsed_response)
    return parsed_response
```

---

## Action Execution Strategies

### Base Action Execution Strategy

The `BaseConstellationActionExecutionStrategy` provides shared logic for action execution, with abstract methods for mode-specific behaviors.

```python
@depends_on("parsed_response")
@provides("execution_result", "action_info", "status")
class BaseConstellationActionExecutionStrategy(BaseProcessingStrategy):
    """Base strategy for executing Constellation actions."""
    
    def __init__(self, weaving_mode: WeavingMode, fail_fast: bool = False):
        super().__init__(
            name=f"constellation_action_execution_{weaving_mode.value}",
            fail_fast=fail_fast
        )
        self.weaving_mode = weaving_mode
    
    async def execute(
        self,
        agent: "ConstellationAgent",
        context: ProcessingContext
    ) -> ProcessingResult:
        """Execute constellation actions with mode-specific logic."""
        
        parsed_response = context.get_local("parsed_response")
        command_dispatcher = context.global_context.command_dispatcher
        
        # Create mode-specific action info (abstract method)
        action_info = await self._create_mode_specific_action_info(
            agent, parsed_response
        )
        
        # Execute actions via dispatcher
        execution_results = await self._execute_constellation_action(
            command_dispatcher, action_info
        )
        
        # Sync constellation state (abstract method)
        self.sync_constellation(execution_results, context)
        
        # Create action info for memory
        actions = self._create_action_info(action_info, execution_results)
        
        # Publish actions (abstract method)
        action_list_info = ListActionCommandInfo(actions)
        await self.publish_actions(agent, action_list_info)
        
        return ProcessingResult(
            success=True,
            data={
                "execution_result": execution_results,
                "action_info": action_list_info,
                "status": parsed_response.status,
            },
            phase=ProcessingPhase.ACTION_EXECUTION,
        )
    
    @abstractmethod
    async def _create_mode_specific_action_info(
        self, agent, parsed_response
    ) -> ActionCommandInfo | List[ActionCommandInfo]:
        """Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def publish_actions(
        self, agent, actions
    ) -> None:
        """Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def sync_constellation(self, results, context) -> None:
        """Must be implemented by subclasses."""
        pass
```

#### Shared Action Execution

```python
async def _execute_constellation_action(
    self,
    command_dispatcher: BasicCommandDispatcher,
    actions: ActionCommandInfo | List[ActionCommandInfo],
) -> List[Result]:
    """Execute actions via command dispatcher."""
    
    if isinstance(actions, ActionCommandInfo):
        actions = [actions]
    
    commands = [
        Command(
            tool_name=action.function,
            parameters=action.arguments or {},
            tool_type="action"
        )
        for action in actions if action.function
    ]
    
    return await command_dispatcher.execute_commands(commands)
```

### Creation Mode Strategy

The `ConstellationCreationActionExecutionStrategy` implements creation-specific action generation.

```python
class ConstellationCreationActionExecutionStrategy(
    BaseConstellationActionExecutionStrategy
):
    """Action execution for constellation creation mode."""
    
    def __init__(self, fail_fast: bool = False):
        super().__init__(weaving_mode=WeavingMode.CREATION, fail_fast=fail_fast)
    
    async def _create_mode_specific_action_info(
        self,
        agent: "ConstellationAgent",
        parsed_response: ConstellationAgentResponse
    ) -> List[ActionCommandInfo]:
        """Create constellation building action."""
        
        if not parsed_response.constellation:
            self.logger.warning("No constellation in response")
            return []
        
        return [
            ActionCommandInfo(
                function=agent._constellation_creation_tool_name,  # "build_constellation"
                arguments={"config": parsed_response.constellation},
            )
        ]
    
    def sync_constellation(
        self,
        results: List[Result],
        context: ProcessingContext
    ) -> None:
        """Sync newly created constellation to context."""
        
        constellation_json = results[0].result if results else None
        if constellation_json:
            constellation = TaskConstellation.from_json(constellation_json)
            context.global_context.set(ContextNames.CONSTELLATION, constellation)
    
    async def publish_actions(
        self, agent, actions: ListActionCommandInfo
    ) -> None:
        """Publish constellation creation actions as events."""
        # Publishes simplified event for WebUI display
        pass
```

### Editing Mode Strategy

The `ConstellationEditingActionExecutionStrategy` implements editing-specific action extraction and constellation synchronization.

```python
class ConstellationEditingActionExecutionStrategy(
    BaseConstellationActionExecutionStrategy
):
    """Action execution for constellation editing mode."""
    
    def __init__(self, fail_fast: bool = False):
        super().__init__(weaving_mode=WeavingMode.EDITING, fail_fast=fail_fast)
    
    async def _create_mode_specific_action_info(
        self,
        agent: "ConstellationAgent",
        parsed_response: ConstellationAgentResponse
    ) -> List[ActionCommandInfo]:
        """Extract editing actions from LLM response."""
        
        if parsed_response.action:
            return parsed_response.action
        else:
            return []
    
    def sync_constellation(
        self,
        results: List[Result],
        context: ProcessingContext
    ) -> None:
        """Sync modified constellation from MCP tool results."""
        
        # Find last successful result with constellation data
        constellation_json = None
        for result in reversed(results):
            if result.status == ResultStatus.SUCCESS and result.result:
                if isinstance(result.result, str):
                    if '"constellation_id"' in result.result or '"tasks"' in result.result:
                        constellation_json = result.result
                        break
                elif isinstance(result.result, dict):
                    if "constellation_id" in result.result or "tasks" in result.result:
                        constellation_json = result.result
                        break
        
        if constellation_json:
            if isinstance(constellation_json, str):
                constellation = TaskConstellation.from_json(constellation_json)
            else:
                constellation = TaskConstellation.from_dict(constellation_json)
            
            context.global_context.set(ContextNames.CONSTELLATION, constellation)
            self.logger.info(f"Synced constellation: {constellation.constellation_id}")
    
    async def publish_actions(self, agent, actions: ListActionCommandInfo) -> None:
        """Publish editing actions as events for WebUI display."""
        # Publishes detailed action events
        pass
```

---

## Memory Update Strategy

### ConstellationMemoryUpdateStrategy

The memory update strategy is **shared across both modes** and handles comprehensive memory logging.

```python
@depends_on("parsed_response")
@provides("additional_memory", "memory_item", "memory_keys_count")
class ConstellationMemoryUpdateStrategy(BaseProcessingStrategy):
    """Memory update strategy (shared across modes)."""
    
    async def execute(
        self,
        agent: "ConstellationAgent",
        context: ProcessingContext
    ) -> ProcessingResult:
        """Execute comprehensive memory update."""
        
        parsed_response = context.get_local("parsed_response")
        
        # Create additional memory data
        additional_memory = self._create_additional_memory_data(agent, context)
        
        # Create and populate memory item
        memory_item = self._create_and_populate_memory_item(
            parsed_response, additional_memory
        )
        
        # Add to agent memory
        agent.add_memory(memory_item)
        
        # Update structural logs
        self._update_structural_logs(memory_item, context.global_context)
        
        return ProcessingResult(
            success=True,
            data={
                "additional_memory": additional_memory,
                "memory_item": memory_item,
                "memory_keys_count": len(memory_item.to_dict()),
            },
            phase=ProcessingPhase.MEMORY_UPDATE,
        )
```

#### Memory Data Creation

```python
def _create_additional_memory_data(
    self,
    agent: "ConstellationAgent",
    context: ProcessingContext
) -> ConstellationProcessorContext:
    """Create comprehensive memory data from processing context."""
    
    constellation_context = context.local_context
    
    # Update with current state
    constellation_context.session_step = context.get_global("SESSION_STEP", 0)
    constellation_context.round_step = context.get_global("CURRENT_ROUND_STEP", 0)
    constellation_context.round_num = context.get_global("CURRENT_ROUND_ID", 0)
    constellation_context.agent_step = agent.step
    
    # Update action information
    action_info = constellation_context.action_info
    if action_info:
        constellation_context.action = [info.model_dump() for info in action_info.actions]
        constellation_context.function_call = [info.function for info in action_info.actions]
        constellation_context.arguments = [info.arguments for info in action_info.actions]
        
        # Update constellation_after
        constellation_after = context.get_global("CONSTELLATION")
        if constellation_after:
            constellation_context.constellation_after = constellation_after.to_json()
    
    return constellation_context
```

---

## Mode Comparison

### Strategy Differences by Mode

| Aspect | Creation Mode | Editing Mode |
|--------|---------------|--------------|
| **LLM Interaction** | Shared strategy | Shared strategy |
| **Prompt Generation** | `ConstellationCreationPrompter` | `ConstellationEditingPrompter` |
| **Action Generation** | `build_constellation` with JSON | Extract `action` field from response |
| **Action Execution** | Single bulk creation | Multiple MCP commands |
| **Constellation Sync** | Set from creation result | Extract from last successful MCP result |
| **Action Publishing** | Simplified event for WebUI | Detailed action events for WebUI |
| **Memory Update** | Shared strategy | Shared strategy |

### Processing Pipeline Comparison

```mermaid
sequenceDiagram
    participant Agent
    participant Processor
    participant Factory
    participant LLMStrat
    participant ActionStrat
    participant MemStrat
    
    Note over Agent,MemStrat: CREATION MODE
    Agent->>Processor: process()
    Processor->>Factory: create_action_execution_strategy(CREATION)
    Factory->>Processor: ConstellationCreationActionExecutionStrategy
    Processor->>LLMStrat: execute() [shared]
    LLMStrat->>Processor: parsed_response with constellation JSON
    Processor->>ActionStrat: execute()
    ActionStrat->>ActionStrat: Create build_constellation command
    ActionStrat->>Processor: execution_result
    Processor->>MemStrat: execute() [shared]
    MemStrat->>Processor: memory_item
    
    Note over Agent,MemStrat: EDITING MODE
    Agent->>Processor: process()
    Processor->>Factory: create_action_execution_strategy(EDITING)
    Factory->>Processor: ConstellationEditingActionExecutionStrategy
    Processor->>LLMStrat: execute() [shared]
    LLMStrat->>Processor: parsed_response with action list
    Processor->>ActionStrat: execute()
    ActionStrat->>ActionStrat: Extract MCP commands
    ActionStrat->>Processor: execution_result
    Processor->>MemStrat: execute() [shared]
    MemStrat->>Processor: memory_item
```

---

## Error Handling

### Fail-Fast Configuration

Each strategy can be configured with `fail_fast` to control error propagation:

```python
# LLM failures should trigger recovery
ConstellationStrategyFactory.create_llm_interaction_strategy(
    fail_fast=True
)

# Action failures can be handled gracefully
ConstellationStrategyFactory.create_action_execution_strategy(
    weaving_mode=mode,
    fail_fast=False
)

# Memory failures shouldn't stop the process
ConstellationStrategyFactory.create_memory_update_strategy(
    fail_fast=False
)
```

### Strategy-Level Error Handling

```python
class BaseProcessingStrategy:
    def handle_error(
        self,
        error: Exception,
        phase: ProcessingPhase,
        context: ProcessingContext
    ) -> ProcessingResult:
        """Handle strategy execution errors."""
        
        error_msg = f"{self.name} failed: {str(error)}"
        self.logger.error(error_msg)
        
        if self.fail_fast:
            raise error
        
        return ProcessingResult(
            success=False,
            data={"error": error_msg},
            phase=phase
        )
```

---

## Best Practices

### Strategy Design

1. **Keep strategies focused**: Each strategy handles one processing phase
2. **Use dependencies**: Declare data dependencies with `@depends_on` and `@provides`
3. **Handle errors gracefully**: Configure `fail_fast` appropriately per strategy
4. **Log comprehensively**: Use structured logging for debugging
5. **Validate outputs**: Ensure each strategy produces expected data structures

### Mode Selection

```python
def determine_strategy_mode(constellation: Optional[TaskConstellation]) -> WeavingMode:
    """Determine appropriate mode based on constellation state."""
    
    if constellation is None or len(constellation.tasks) == 0:
        return WeavingMode.CREATION
    else:
        return WeavingMode.EDITING
```

### Testing Strategies

```python
class TestConstellationStrategies(unittest.TestCase):
    def test_creation_action_strategy(self):
        """Test creation strategy generates build_constellation action."""
        
        strategy = ConstellationCreationActionExecutionStrategy()
        response = ConstellationAgentResponse(
            constellation={"tasks": [...], "dependencies": [...]}
        )
        
        actions = await strategy._create_mode_specific_action_info(
            agent, response
        )
        
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].function, "build_constellation")
    
    def test_editing_action_strategy(self):
        """Test editing strategy extracts actions from response."""
        
        strategy = ConstellationEditingActionExecutionStrategy()
        response = ConstellationAgentResponse(
            action=[
                ActionCommandInfo(function="add_task", arguments={...}),
                ActionCommandInfo(function="add_dependency", arguments={...})
            ]
        )
        
        actions = await strategy._create_mode_specific_action_info(
            agent, response
        )
        
        self.assertEqual(len(actions), 2)
```

---

## Summary

The Constellation Agent's processing strategy pattern provides:

- **Modular Processing**: Three distinct phases (LLM, Action, Memory) with dedicated strategies assembled by `ConstellationAgentProcessor`
- **Mode Flexibility**: Factory-based strategy creation adapts to CREATION vs. EDITING modes
- **Shared Logic**: LLM interaction and memory update strategies are mode-agnostic
- **Targeted Customization**: Only action execution varies by mode (creation builds entire constellation, editing applies MCP commands)
- **Robust Error Handling**: Per-strategy fail-fast configuration
- **Clean Architecture**: ProcessorTemplate provides the orchestration framework, strategies implement phase-specific logic
- **Testability**: Each strategy can be tested in isolation

This architecture enables the Constellation Agent to handle both initial constellation creation and subsequent modifications with appropriate processing strategies while maintaining clean separation of concerns. The processor assembles these strategies dynamically based on weaving mode, making the prompters support components rather than the primary focus of the strategy pattern.

## Related Documentation

- [Constellation Agent Overview](overview.md) - Learn about constellation creation and editing modes
- [Constellation Agent State Machine](state.md) - Understand the state transitions and lifecycle
- [Processor Framework Design](../../infrastructure/agents/design/processor.md) - Deep dive into the ProcessorTemplate architecture
- [Prompter Framework](../../infrastructure/agents/design/prompter.md) - Mode-specific prompt generation framework
- [Constellation Editor MCP Server](../../mcp/servers/constellation_editor.md) - MCP commands for constellation manipulation
