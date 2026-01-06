# Part 6: Complete Example - MobileAgent

**Note**: This comprehensive hands-on tutorial is currently under development. Check back soon for a complete MobileAgent implementation walkthrough.

## What You'll Build

A fully functional **MobileAgent** that can:

- Control Android/iOS devices
- Perform UI automation
- Execute touch gestures (tap, swipe, type)
- Capture screenshots and UI hierarchy
- Integrate with Galaxy orchestration

## Planned Content

### 1. Platform-Specific Setup

#### Android
- ADB (Android Debug Bridge) integration
- UI Automator framework
- Accessibility services

#### iOS
- XCTest framework
- Accessibility API
- Instrument tools

### 2. Complete Implementation

- Agent class
- Processor and strategies
- State manager
- MCP server with mobile tools
- Prompter for mobile UI

### 3. Advanced Features

- Multi-device coordination
- App-specific automation
- Error recovery strategies
- Performance optimization

## Temporary Reference

For now, study the **LinuxAgent** implementation as a complete reference:

### Key Files

| Component | File Path |
|-----------|-----------|
| Agent Class | `ufo/agents/agent/customized_agent.py` |
| Processor | `ufo/agents/processors/customized/customized_agent_processor.py` |
| Strategies | `ufo/agents/processors/strategies/linux_agent_strategy.py` |
| States | `ufo/agents/states/linux_agent_state.py` |
| Prompter | `ufo/prompter/customized/linux_agent_prompter.py` |
| MCP Server | `ufo/client/mcp/http_servers/linux_mcp_server.py` |

### Quick Start Template

```python
# Minimal MobileAgent structure (to be expanded)

@AgentRegistry.register(
    agent_name="MobileAgent",
    third_party=True,
    processor_cls=MobileAgentProcessor
)
class MobileAgent(CustomizedAgent):
    def __init__(self, name, main_prompt, example_prompt):
        super().__init__(name, main_prompt, example_prompt,
                         process_name=None, app_root_name=None, is_visual=None)
        self._blackboard = Blackboard()
        self.set_state(self.default_state)
        self._context_provision_executed = False
    
    @property
    def default_state(self):
        return ContinueMobileAgentState()
    
    def message_constructor(
        self,
        dynamic_examples,
        dynamic_knowledge,
        plan,
        request,
        installed_apps,
        current_controls,
        screenshot_url=None,
        annotated_screenshot_url=None,
        blackboard_prompt=None,
        last_success_actions=None,
    ):
        # Construct prompt for LLM with mobile-specific context
        return self.prompter.prompt_construction(...)
```

## Related Documentation

- **[Agent Architecture](../../infrastructure/agents/overview.md)** - Architecture overview
- **[Agent Types](../../infrastructure/agents/agent_types.md)** - Platform implementations
- **[Linux Quick Start](../../getting_started/quick_start_linux.md)** - LinuxAgent deployment

---

**Previous**: [← Part 5: Testing & Debugging](testing.md)  
**Back to Index**: [Tutorial Series](index.md)
