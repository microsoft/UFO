# Project Directory Structure

This repository implements **UFO³**, a multi-tier AgentOS architecture spanning from single-device automation (UFO²) to cross-device orchestration (Galaxy). This document provides an overview of the directory structure to help you understand the codebase organization.

!!!tip "Architecture Overview"
    - **🌌 Galaxy**: Multi-device DAG-based orchestration framework that coordinates agents across different platforms
    - **🎯 UFO²**: Single-device Windows desktop agent system that can serve as Galaxy's sub-agent
    - **🔌 AIP**: Agent Integration Protocol for cross-device communication
    - **⚙️ Modular Configuration**: Type-safe configs in `config/galaxy/` and `config/ufo/`

---

## 📦 Root Directory Structure

```
UFO/
├── galaxy/                 # 🌌 Multi-device orchestration framework
├── ufo/                    # 🎯 Desktop AgentOS (can be Galaxy sub-agent)
├── config/                 # ⚙️ Modular configuration system
├── aip/                    # 🔌 Agent Integration Protocol
├── documents/              # 📖 MkDocs documentation site
├── vectordb/               # 🗄️ Vector database for RAG
├── learner/                # 📚 Help document indexing tools
├── record_processor/       # 🎥 Human demonstration parser
├── dataflow/               # 📊 Data collection pipeline
├── model_worker/           # 🤖 Custom LLM deployment tools
├── logs/                   # 📝 Execution logs (auto-generated)
├── scripts/                # 🛠️ Utility scripts
├── tests/                  # 🧪 Unit and integration tests
└── requirements.txt        # 📦 Python dependencies
```

---

## 🌌 Galaxy Framework (`galaxy/`)

The cross-device orchestration framework that transforms natural language requests into executable DAG workflows distributed across heterogeneous devices.

### Directory Structure

```
galaxy/
├── agents/                 # 🤖 Constellation orchestration agents
│   ├── agent/              # ConstellationAgent and basic agent classes
│   ├── states/             # Agent state machines
│   ├── processors/         # Request/result processing
│   └── presenters/         # Response formatting
│
├── constellation/          # 🌟 Core DAG management system
│   ├── constellation.py    # TaskConstellation - DAG container
│   ├── task_star.py        # TaskStar - Task nodes
│   ├── task_star_line.py   # TaskStarLine - Dependency edges
│   ├── editor/             # Interactive DAG editing with undo/redo
│   ├── orchestrator/       # Event-driven execution coordination
│   └── types/              # Type definitions (priority, dependency, device)
│
├── session/                # 📊 Session lifecycle management
│   ├── galaxy_session.py   # GalaxySession implementation
│   └── observers/          # Event-driven observers
│
├── client/                 # 📡 Device management
│   ├── constellation_client.py              # Device registration interface
│   ├── constellation_device_manager.py      # Device management coordinator
│   ├── constellation_config.py              # Configuration loading
│   ├── components/         # Device registry, connection manager, etc.
│   └── orchestration/      # Client orchestration
│
├── core/                   # ⚡ Foundational components
│   ├── types/              # Type system (protocols, dataclasses, enums)
│   ├── interfaces/         # Interface definitions
│   ├── di/                 # Dependency injection container
│   └── events/             # Event system
│
├── visualization/          # 🎨 Rich console visualization
│   ├── dag_visualizer.py   # DAG topology visualization
│   ├── task_display.py     # Task status displays
│   └── components/         # Visualization components
│
├── prompts/                # 💬 Prompt templates
│   ├── constellation_agent/ # ConstellationAgent prompts
│   └── share/              # Shared examples
│
├── trajectory/             # 📈 Execution trajectory parsing
│
├── __main__.py             # 🚀 Entry point: python -m galaxy
├── galaxy.py               # Main Galaxy orchestrator
├── galaxy_client.py        # Galaxy client interface
├── README.md               # Galaxy overview
└── README_UFO3.md          # UFO³ detailed documentation
```

### Key Components

| Component | Description | Documentation |
|-----------|-------------|---------------|
| **ConstellationAgent** | AI-powered agent that generates and modifies task DAGs | [Galaxy Overview](galaxy/overview.md) |
| **TaskConstellation** | DAG container with validation and state management | [Constellation](galaxy/constellation.md) |
| **TaskOrchestrator** | Event-driven execution coordinator | [Task Orchestrator](galaxy/task_orchestrator.md) |
| **DeviceManager** | Multi-device coordination and assignment | [Device Pool](galaxy/device_pool.md) |
| **Visualization** | Rich console DAG monitoring | [Monitoring & Visualization](galaxy/monitoring_visualization.md) |

!!!info "Galaxy Documentation"
    - **[Galaxy Overview](galaxy/overview.md)** - Architecture and concepts
    - **[Quick Start](galaxy/quick_start.md)** - Get started with Galaxy
    - **[Planning](galaxy/planning.md)** - Task planning and DAG generation
    - **[Task Assignment](galaxy/task_assignment.md)** - Device assignment strategies
    - **[Dynamic Editing](galaxy/dynamic_editing.md)** - Runtime DAG modification
    - **[Parallel Execution](galaxy/parallel_execution.md)** - Concurrent task execution
    - **[Fault Tolerance](galaxy/fault_tolerance.md)** - Error handling and recovery

---

## 🎯 UFO² Desktop AgentOS (`ufo/`)

Single-device desktop automation system implementing a two-tier agent architecture (HostAgent + AppAgent) with hybrid GUI-API automation.

### Directory Structure

```
ufo/
├── agents/                 # Two-tier agent implementation
│   ├── agent/              # Base agent classes (HostAgent, AppAgent)
│   ├── states/             # State machine implementations
│   ├── processors/         # Processing strategy pipelines
│   ├── memory/             # Agent memory and blackboard
│   └── presenters/         # Response presentation logic
│
├── client/                 # MCP client and device management
│   ├── mcp/                # MCP server manager
│   │   ├── local_servers/  # Built-in MCP servers (UI, CLI, Office COM)
│   │   └── http_servers/   # Remote MCP servers (hardware, Linux)
│   ├── ufo_client.py       # UFO² client implementation
│   └── computer.py         # Computer/device abstraction
│
├── automator/              # GUI and API automation layer
│   ├── ui_control/         # GUI automation (inspector, controller)
│   ├── puppeteer/          # Execution orchestration
│   └── *_automator.py      # App-specific automators (Excel, Word, etc.)
│
├── prompter/               # Prompt construction engines
├── prompts/                # Jinja2 prompt templates
│   ├── host_agent/         # HostAgent prompts
│   ├── app_agent/          # AppAgent prompts
│   └── share/              # Shared components
│
├── llm/                    # LLM provider integrations
├── rag/                    # Retrieval-Augmented Generation
├── trajectory/             # Task trajectory parsing
├── experience/             # Self-experience learning
├── module/                 # Core modules (session, round, context)
├── utils/                  # Utility functions
├── tools/                  # CLI tools (config conversion, etc.)
│
├── __main__.py             # Entry point: python -m ufo
└── ufo.py                  # Main UFO² orchestrator
```

### Key Components

| Component | Description | Documentation |
|-----------|-------------|---------------|
| **HostAgent** | Desktop-level orchestration with 7-state FSM | [HostAgent Overview](ufo2/host_agent/overview.md) |
| **AppAgent** | Application-level execution with 6-state FSM | [AppAgent Overview](ufo2/app_agent/overview.md) |
| **MCP System** | Extensible command execution framework | [MCP Overview](mcp/overview.md) |
| **Automator** | Hybrid GUI-API automation with fallback | [Core Features](ufo2/core_features/hybrid_actions.md) |
| **RAG** | Knowledge retrieval from multiple sources | [Knowledge Substrate](ufo2/core_features/knowledge_substrate/overview.md) |

!!!info "UFO² Documentation"
    - **[UFO² Overview](ufo2/overview.md)** - Architecture and concepts
    - **[Quick Start](ufo2/quick_start.md)** - Get started with UFO²
    - **[HostAgent States](ufo2/host_agent/state.md)** - Desktop orchestration states
    - **[AppAgent States](ufo2/app_agent/state.md)** - Application execution states
    - **[As Galaxy Device](ufo2/as_galaxy_device.md)** - Using UFO² as Galaxy sub-agent

---

## 🔌 Agent Integration Protocol (`aip/`)

Standardized message passing protocol for cross-device communication between Galaxy and UFO² agents.

```
aip/
├── messages.py             # Message types (Command, Result, Event, Error)
├── protocol/               # Protocol definitions
├── transport/              # Transport layers (HTTP, WebSocket, MQTT)
├── endpoints/              # API endpoints
├── extensions/             # Protocol extensions
└── resilience/             # Retry and error handling
```

**Purpose**: Enables Galaxy to coordinate UFO² agents running on different devices and platforms through standardized messaging over HTTP/WebSocket.

---

## ⚙️ Configuration (`config/`)

Modular configuration system with type-safe schemas and auto-discovery.

```
config/
├── galaxy/                 # Galaxy configuration
│   ├── galaxy.yaml.template    # Galaxy settings template
│   ├── devices.yaml            # Multi-device registry
│   ├── dag_templates/          # Pre-built DAG templates
│   └── visualization.yaml      # Visualization preferences
│
├── ufo/                    # UFO² configuration
│   ├── agents.yaml.template    # Agent LLM configs template
│   ├── rag.yaml                # RAG settings
│   ├── system.yaml             # System settings
│   ├── mcp.yaml                # MCP server configs
│   └── prices.yaml             # API pricing data
│
├── config_loader.py        # Auto-discovery config loader
└── config_schemas.py       # Pydantic validation schemas
```

!!!warning "Configuration Files"
    - Template files (`.yaml.template`) should be copied and edited
    - Actual config files (`.yaml`) contain API keys and should NOT be committed
    - Use `python -m ufo.tools.convert_config` to migrate from legacy configs

!!!info "Configuration Documentation"
    - **[Galaxy Configuration](configuration/models/overview.md)** - Multi-device setup
    - **[UFO² System Configuration](configuration/system/overview.md)** - Agent settings
    - **[Model Configuration](configuration/models/overview.md)** - LLM provider setup
    - **[MCP Configuration](mcp/configuration.md)** - MCP server setup

---

## 📖 Documentation (`documents/`)

MkDocs documentation site with comprehensive guides and API references.

```
documents/
├── docs/                   # Markdown documentation source
│   ├── getting_started/    # Installation and quick starts
│   ├── galaxy/             # Galaxy framework docs
│   ├── ufo2/               # UFO² architecture docs
│   ├── mcp/                # MCP server documentation
│   ├── configuration/      # Configuration guides
│   ├── tutorials/          # Step-by-step tutorials
│   └── about/              # Project information
│
├── mkdocs.yml              # MkDocs configuration
└── site/                   # Generated static site
```

**Documentation Sections**:

| Section | Description |
|---------|-------------|
| **Getting Started** | Installation, quick starts, migration guides |
| **Galaxy** | Multi-device orchestration, DAG workflows, device management |
| **UFO²** | Desktop agents, automation features, benchmarks |
| **MCP** | Server documentation, custom server development |
| **Configuration** | System settings, model configs, deployment |
| **Tutorials** | Creating agents, custom automators, advanced usage |

---

## 🗄️ Supporting Modules

### VectorDB (`vectordb/`)
Vector database storage for RAG knowledge sources (help documents, execution traces, user demonstrations).

### Learner (`learner/`)
Tools for indexing help documents into vector database for RAG retrieval.

### Record Processor (`record_processor/`)
Parses human demonstrations from Windows Step Recorder for learning from user actions.

### Dataflow (`dataflow/`)
Data collection pipeline for Large Action Model (LAM) training.

### Model Worker (`model_worker/`)
Custom LLM deployment tools for running local models.

### Logs (`logs/`)
Auto-generated execution logs organized by task and timestamp, including screenshots, UI trees, and agent actions.

---

## 🎯 Galaxy vs UFO²: When to Use What?

| Aspect | Galaxy | UFO² |
|--------|--------|------|
| **Scope** | Multi-device orchestration | Single-device automation |
| **Use Cases** | Cross-platform workflows, distributed tasks | Desktop automation, Office tasks |
| **Architecture** | DAG-based task workflows | Two-tier state machines |
| **Device Support** | Windows, Linux, Android, Hardware | Windows (primary), Linux (experimental) |
| **Complexity** | Complex multi-step workflows | Simple to moderate tasks |
| **Best For** | Cross-device collaboration | Standalone automation |

!!!tip "Choosing the Right Framework"
    - **Use Galaxy** when: Tasks span multiple devices/platforms, complex workflows with dependencies
    - **Use UFO² Standalone** when: Single-device automation, rapid prototyping, simple tasks
    - **Best Practice**: Galaxy can orchestrate multiple UFO² instances as sub-agents for device-specific execution

---

## 🚀 Quick Start

### Galaxy Multi-Device Orchestration

```bash
# Interactive mode
python -m galaxy --interactive

# Single request
python -m galaxy --request "Your cross-device task"
```

**Documentation**: [Galaxy Quick Start](galaxy/quick_start.md)

### UFO² Desktop Automation

```bash
# Interactive mode
python -m ufo --task <task_name>

# With custom config
python -m ufo --task <task_name> --config_path config/ufo/
```

**Documentation**: [UFO² Quick Start](ufo2/quick_start.md)

---

## 📚 Key Documentation Links

### Getting Started
- [Installation & Setup](getting_started/quick_start_galaxy.md)
- [Galaxy Quick Start](getting_started/quick_start_galaxy.md)
- [UFO² Quick Start](getting_started/quick_start_ufo2.md)
- [Migration Guide](getting_started/migration_ufo2_to_galaxy.md)

### Galaxy Framework
- [Galaxy Overview](galaxy/overview.md)
- [Constellation Management](galaxy/constellation.md)
- [Device Pool](galaxy/device_pool.md)
- [Task Orchestrator](galaxy/task_orchestrator.md)

### UFO² Desktop AgentOS
- [UFO² Overview](ufo2/overview.md)
- [HostAgent](ufo2/host_agent/overview.md)
- [AppAgent](ufo2/app_agent/overview.md)
- [Core Features](ufo2/core_features/hybrid_actions.md)

### MCP System
- [MCP Overview](mcp/overview.md)
- [Local Servers](mcp/local_servers.md)
- [Custom Servers](mcp/custom_servers.md)

### Configuration
- [System Configuration](configuration/system/overview.md)
- [Model Configuration](configuration/models/overview.md)
- [MCP Configuration](mcp/configuration.md)

---

## 🏗️ Architecture Principles

UFO³ follows **SOLID principles** and established software engineering patterns:

- **Single Responsibility**: Each component has a focused purpose
- **Open/Closed**: Extensible through interfaces and plugins
- **Interface Segregation**: Focused interfaces for different capabilities
- **Dependency Inversion**: Dependency injection for loose coupling
- **Event-Driven**: Observer pattern for real-time monitoring
- **State Machines**: Well-defined states and transitions for agents
- **Command Pattern**: Encapsulated DAG editing with undo/redo

---

## 📝 Additional Resources

- **[GitHub Repository](https://github.com/microsoft/UFO)** - Source code and issues
- **[Research Paper](https://arxiv.org/abs/2504.14603)** - UFO³ technical details
- **[Documentation Site](https://microsoft.github.io/UFO/)** - Full documentation
- **[Video Demo](https://www.youtube.com/watch?v=QT_OhygMVXU)** - YouTube demonstration

---

!!!success "Next Steps"
    1. Start with **[Galaxy Quick Start](galaxy/quick_start.md)** for multi-device orchestration
    2. Or explore **[UFO² Quick Start](ufo2/quick_start.md)** for single-device automation
    3. Check **[FAQ](faq.md)** for common questions
    4. Join our community and contribute!

