# More Guidance

This page provides additional guidance and resources for different user types and use cases.

---

## 🎯 For End Users

If you want to use UFO³ to automate your tasks on Windows, Linux, or across multiple devices, here's your learning path:

### 1. Getting Started (5-10 minutes)

Choose your path based on your needs:

| Your Goal | Start Here | Time |
|-----------|-----------|------|
| **Automate Windows desktop tasks** | [UFO² Quick Start](quick_start_ufo2.md) | 5 min |
| **Manage Linux servers** | [Linux Quick Start](quick_start_linux.md) | 10 min |
| **Orchestrate multiple devices** | [Galaxy Quick Start](quick_start_galaxy.md) | 10 min |

### 2. Configure Your Environment (10-20 minutes)

After installation, customize UFO³ to your needs:

**Essential Configuration:**

- **[Agent Configuration](../configuration/system/agents_config.md)** - Set up LLM API keys (OpenAI, Azure, Gemini, Claude, etc.)
- **[System Configuration](../configuration/system/system_config.md)** - Adjust runtime settings (step limits, timeouts, logging)

**Optional Enhancements:**

- **[RAG Configuration](../configuration/system/rag_config.md)** - Add external knowledge sources:
  - Offline help documents
  - Bing search integration
  - Experience learning from past tasks
  - User demonstrations
- **[MCP Configuration](../configuration/system/mcp_reference.md)** - Enable tool servers for:
  - Better Office automation
  - Linux command execution
  - Custom tool integration

> **💡 Configuration Tip:** Start with default settings and adjust only what you need. See [Configuration Overview](../configuration/system/overview.md) for the big picture.

### 3. Learn Core Features (20-30 minutes)

**For UFO² Users (Windows Desktop Automation):**

| Feature | Documentation | What It Does |
|---------|---------------|--------------|
| **Hybrid GUI-API Execution** | [Hybrid Actions](../ufo2/core_features/hybrid_actions.md) | Combines UI automation with native API calls for faster, more reliable execution |
| **Knowledge Substrate** | [Knowledge Overview](../ufo2/core_features/knowledge_substrate/overview.md) | Augments agents with external knowledge (docs, search, experience) |
| **MCP Integration** | [MCP Overview](../mcp/overview.md) | Extends capabilities with custom tools and Office APIs |

**For Galaxy Users (Multi-Device Orchestration):**

| Feature | Documentation | What It Does |
|---------|---------------|--------------|
| **Task Constellation** | [Constellation Overview](../galaxy/constellation_orchestrator/overview.md) | Decomposes tasks into parallel DAGs across devices |
| **Device Capabilities** | [Galaxy Devices Config](../configuration/system/galaxy_devices.md) | Routes tasks based on device capabilities and metadata |
| **Asynchronous Execution** | [Constellation Overview](../galaxy/constellation/overview.md) | Executes subtasks in parallel for faster completion |
| **Agent Interaction Protocol** | [AIP Overview](../aip/overview.md) | Enables persistent WebSocket communication between devices |

### 4. Troubleshooting & Support

**When Things Go Wrong:**

1. **Check the [FAQ](../faq.md)** - Common issues and solutions
2. **Review logs** - Located in `logs/<task-name>/`:
   ```
   logs/my-task-2025-11-11/
   ├── request.log                    # Request logs
   ├── response.log                   # Response logs
   ├── action_step*.png               # Screenshots at each step
   └── action_step*_annotated.png     # Annotated screenshots
   ```
3. **Validate configuration:**
   ```bash
   python -m ufo.tools.validate_config ufo --show-config
   ```
4. **Enable debug logging:**
   ```yaml
   # config/ufo/system.yaml
   LOG_LEVEL: "DEBUG"
   ```

**Get Help:**

- **[GitHub Discussions](https://github.com/microsoft/UFO/discussions)** - Ask questions, share tips
- **[GitHub Issues](https://github.com/microsoft/UFO/issues)** - Report bugs, request features
- **Email:** ufo-agent@microsoft.com

---

## 👨‍💻 For Developers

If you want to contribute to UFO³ or build extensions, here's your development guide:

### 1. Understand the Architecture (30-60 minutes)

**Start with the big picture:**

- **[Project Structure](../project_directory_structure.md)** - Codebase organization and component roles
- **[Configuration Architecture](../configuration/system/overview.md)** - New modular config system design

**Deep dive into core components:**

| Component | Documentation | What to Learn |
|-----------|---------------|---------------|
| **Session** | [Session Module](../infrastructure/modules/session.md) | Task lifecycle management, state tracking |
| **Round** | [Round Module](../infrastructure/modules/round.md) | Single agent reasoning cycle |
| **HostAgent** | [HostAgent](../ufo2/host_agent/overview.md) | High-level task planning and app selection |
| **AppAgent** | [AppAgent](../ufo2/app_agent/overview.md) | Low-level action execution |
| **ConstellationAgent** | [ConstellationAgent](../galaxy/constellation_agent/overview.md) | Multi-device task orchestration |

### 2. Set Up Development Environment (15-30 minutes)

**Installation:**

```bash
# Clone the repository
git clone https://github.com/microsoft/UFO.git
cd UFO

# Create development environment
conda create -n ufo-dev python=3.10
conda activate ufo-dev

# Install dependencies (including dev tools)
pip install -r requirements.txt
pip install pytest pytest-cov black flake8  # Testing & linting
```

**Configuration:**

```bash
# Create config files from templates
cp config/ufo/agents.yaml.template config/ufo/agents.yaml
cp config/galaxy/agent.yaml.template config/galaxy/agent.yaml

# Edit with your development API keys
# (Consider using lower-cost models for testing)
```

### 3. Explore the Codebase (1-2 hours)

**Key Directories:**

```
UFO/
├── ufo/                    # Core UFO² implementation
│   ├── agents/            # HostAgent, AppAgent
│   ├── automator/         # UI automation engines
│   ├── prompter/          # Prompt management
│   └── module/            # Core modules (Session, Round)
├── galaxy/                 # Galaxy orchestration framework
│   ├── agents/            # ConstellationAgent
│   ├── constellation/     # DAG orchestration
│   └── core/              # Core Galaxy infrastructure
├── aip/                    # Agent Interaction Protocol
│   ├── protocol/          # Message definitions
│   └── transport/         # WebSocket transport
├── ufo/client/            # Device agents (Windows, Linux)
│   ├── client.py          # Generic client
│   └── mcp/               # MCP integration
├── ufo/server/            # Device agent server
│   └── app.py             # FastAPI server
└── config/                 # Configuration system
    ├── ufo/               # UFO² configs
    └── galaxy/            # Galaxy configs
```

**Entry Points:**

- **UFO² Main:** `ufo/__main__.py`
- **Galaxy Main:** `galaxy/__main__.py`
- **Server:** `ufo/server/app.py`
- **Client:** `ufo/client/client.py`

### 4. Development Workflows

#### Adding a New Feature

1. **Identify the component** to modify (Agent, Module, Automator, etc.)
2. **Read existing code** in that component
3. **Check related tests** in `tests/` directory
4. **Implement your feature** following existing patterns
5. **Add tests** for your feature
6. **Update documentation** if needed

#### Extending Configuration

See **[Extending Configuration](../configuration/system/extending.md)** for:
- Adding custom fields
- Creating new config modules
- Environment-specific overrides
- Plugin configuration patterns

#### Creating Custom MCP Servers

See **[Creating MCP Servers Tutorial](../tutorials/creating_mcp_servers.md)** for:
- MCP server architecture
- Tool definition and registration
- HTTP vs. local vs. stdio servers
- Integration with UFO³

### 5. Testing & Debugging

**Run Tests:**

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/config/test_config_system.py

# Run with coverage
pytest --cov=ufo --cov-report=html
```

**Debug Logging:**

```python
# Add debug logs to your code
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message with context: %s", variable)
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error message")
```

**Interactive Debugging:**

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use VS Code debugger with launch.json
```

### 6. Code Style & Best Practices

**Formatting:**

```bash
# Auto-format with black
black ufo/ galaxy/

# Check style with flake8
flake8 ufo/ galaxy/
```

**Best Practices:**

- ✅ Use type hints: `def process(data: Dict[str, Any]) -> Optional[str]:`
- ✅ Write docstrings for public functions
- ✅ Follow existing code patterns
- ✅ Add comments for complex logic
- ✅ Keep functions focused and modular
- ✅ Handle errors gracefully
- ✅ Write tests for new features

**Configuration Best Practices:**

- ✅ Use typed config access: `config.system.max_step`
- ✅ Provide `.template` files for sensitive configs
- ✅ Document custom fields in YAML comments
- ✅ Use environment variables for secrets: `${OPENAI_API_KEY}`
- ✅ Validate configurations early: `ConfigValidator.validate()`

### 7. Contributing Guidelines

**Before Submitting a PR:**

1. **Test your changes** thoroughly
2. **Update documentation** if needed
3. **Follow code style** (black + flake8)
4. **Write clear commit messages**
5. **Reference related issues** in PR description

**PR Template:**

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Added tests for new functionality
- [ ] All tests pass locally
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### 8. Advanced Topics

**For Deep Customization:**

- **[Prompt Engineering](../ufo2/prompts/overview.md)** - Customize agent prompts
- **[State Management](../galaxy/constellation/overview.md)** - Constellation state machine internals
- **[Protocol Extensions](../aip/messages.md)** - Extend AIP message types
- **[Custom Automators](../ufo2/core_features/control_detection/overview.md)** - Implement new automation backends

---

## 🎓 Learning Paths

### Path 1: Basic User → Power User

1. ✅ Complete quick start for your platform
2. ✅ Run 5-10 simple automation tasks
3. ✅ Configure RAG for your organization's docs
4. ✅ Enable MCP for better Office automation
5. ✅ Set up experience learning for common tasks
6. ✅ Create custom device configurations (Galaxy)

**Time Investment:** 2-4 hours  
**Outcome:** Efficient automation of daily tasks

### Path 2: Power User → Developer

1. ✅ Understand project structure and architecture
2. ✅ Read Session and Round module code
3. ✅ Create a custom MCP server
4. ✅ Add custom metadata to device configs
5. ✅ Contribute documentation improvements
6. ✅ Submit your first bug fix PR

**Time Investment:** 10-20 hours  
**Outcome:** Ability to extend and customize UFO³

### Path 3: Developer → Core Contributor

1. ✅ Deep dive into agent implementations
2. ✅ Understand Galaxy orchestration internals
3. ✅ Study AIP protocol and transport layer
4. ✅ Implement a new agent capability
5. ✅ Add support for a new LLM provider
6. ✅ Contribute major features or refactorings

**Time Investment:** 40+ hours  
**Outcome:** Core contributor to UFO³ project

---

## 📚 Additional Resources

### Documentation Hubs

| Topic | Link | Description |
|-------|------|-------------|
| **Getting Started** | [Getting Started Index](../index.md#getting-started) | All quick start guides |
| **Configuration** | [Configuration Overview](../configuration/system/overview.md) | Complete config system documentation |
| **Architecture** | [Galaxy Overview](../galaxy/overview.md), [UFO² Overview](../ufo2/overview.md) | System architecture and design |
| **API Reference** | [Agent APIs](../infrastructure/agents/overview.md) | Agent interfaces and APIs |
| **Tutorials** | [Creating Device Agents](../tutorials/creating_device_agent/index.md) | Step-by-step guides |

### Community Resources

- **[GitHub Repository](https://github.com/microsoft/UFO)** - Source code and releases
- **[GitHub Discussions](https://github.com/microsoft/UFO/discussions)** - Q&A and community
- **[GitHub Issues](https://github.com/microsoft/UFO/issues)** - Bug reports and features
- **[Project Website](https://microsoft.github.io/UFO/)** - Official website

### Research Papers

- **UFO v1** (Feb 2024): [A UI-Focused Agent for Windows OS Interaction](https://arxiv.org/abs/2402.07939)
- **UFO² v2** (Apr 2025): [A Windows Agent for Seamless OS Interaction](https://arxiv.org/abs/2504.14603)
- **UFO³ Galaxy** (Nov 2025): UFO³: Weaving the Digital Agent Galaxy *(Coming Soon)*

---

## 🆘 Need More Help?

- **Can't find what you're looking for?** Check the [FAQ](../faq.md)
- **Still stuck?** Ask on [GitHub Discussions](https://github.com/microsoft/UFO/discussions)
- **Found a bug?** Open an issue on [GitHub Issues](https://github.com/microsoft/UFO/issues)
- **Want to contribute?** Read the [Contributing Guidelines](https://github.com/microsoft/UFO/blob/main/CONTRIBUTING.md)

**Happy automating!** 🚀
