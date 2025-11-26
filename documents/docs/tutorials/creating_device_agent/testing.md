# Part 5: Testing & Debugging

**Note**: This tutorial is currently under development. Check back soon for comprehensive testing and debugging guidance.

## What You'll Learn

- Unit testing strategies
- Integration testing
- Debugging techniques
- Common issues and solutions
- Performance optimization

## Temporary Quick Guide

### Basic Testing

```python
# tests/test_mobile_agent.py

import pytest
from ufo.agents.agent.customized_agent import MobileAgent

def test_agent_initialization():
    agent = MobileAgent(
        name="test_agent",
        main_prompt="ufo/prompts/third_party/mobile_agent.yaml",
        example_prompt="ufo/prompts/third_party/mobile_agent_example.yaml",
        platform="android",
    )
    assert agent.name == "test_agent"
    assert agent.platform == "android"
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Agent not registered | Check `@AgentRegistry.register()` decorator |
| MCP server not responding | Verify MCP server is running on correct port |
| WebSocket connection failed | Check server URL and network connectivity |

## Related Documentation

- **[Testing Best Practices](../../infrastructure/agents/overview.md#best-practices)** - Agent testing
- **[Troubleshooting](../../getting_started/quick_start_linux.md#common-issues-troubleshooting)** - Common issues

---

**Previous**: [← Part 4: Configuration](configuration.md)  
**Next**: [Part 6: Complete Example →](example_mobile_agent.md)
