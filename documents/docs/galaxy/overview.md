# UFO³ — Weaving the Digital Agent Galaxy

<div align="center">
  <img src="/img/poster.png" alt="UFO³ Galaxy Concept" style="max-width: 90%; height: auto; margin: 20px 0;">
  <p><em>From isolated device agents to interconnected constellations — Building the Digital Agent Galaxy</em></p>
</div>

---

## 🌌 Vision

Imagine a future where you could simply say: *"Prepare a production-ready demo of Project X and deliver a one-page executive summary with screenshots and performance numbers."* 

Today, this requires tedious, error-prone coordination across devices—checking out code on a laptop, triggering GPU builds on a server, deploying to a cloud instance, recording UI interactions on a phone, and stitching results into a report. Despite recent advances in intelligent agents, most systems remain **confined within a single device or platform**, leaving vast computational resources underutilized.

**UFO³ Galaxy** dissolves these boundaries, transforming your distributed digital estate—desktops, servers, mobile devices, and edge nodes—into a **coherent execution fabric** where agents collaborate seamlessly to execute complex, multi-device workflows.

---

## 🚀 What is UFO³ Galaxy?

**UFO³ Galaxy** is a **cross-device orchestration system** that turns isolated device agents into a unified digital collective. It models each request as a **Task Constellation**—a dynamic distributed DAG (Directed Acyclic Graph) whose nodes represent executable subtasks and whose edges capture data and control dependencies.

### The Challenge

Building truly ubiquitous intelligent agents requires overcoming three interlocking challenges:

1. **Asynchronous Parallelism**: Many subtasks can and should run concurrently across devices with varying capabilities
2. **Distributed Coordination**: Agents need reliable, low-latency communication for task dispatch and result streaming despite network variability
3. **Heterogeneous Extensibility**: The system should make it easy to develop and integrate new device agents while preserving safety and global consistency

### The Solution

UFO³ Galaxy addresses these challenges through a sophisticated orchestration framework that:

- **Decomposes** complex tasks into distributed workflows
- **Schedules** subtasks across heterogeneous devices
- **Executes** tasks asynchronously and in parallel
- **Adapts** dynamically to failures and intermediate results
- **Coordinates** seamlessly across OS boundaries

---

## 🏗️ Architecture

<div align="center">
  <img src="/img/overview2.png" alt="UFO³ Galaxy Layered Architecture" style="max-width: 100%; height: auto; margin: 20px 0;">
  <p><em>UFO³ Galaxy Layered Architecture — From natural language to distributed execution</em></p>
</div>

### Layered Design

UFO³ Galaxy is built on a **three-tier architecture**:

#### 1️⃣ **Orchestration Layer** (Constellation Agent)
- Decomposes user intents into Task Constellations (DAGs)
- Manages global workflow state and dependencies
- Schedules tasks across device agents
- Handles dynamic graph evolution and fault recovery

#### 2️⃣ **Communication Layer** (Agent Interaction Protocol)
- Persistent WebSocket channels for low-latency messaging
- Agent registry and discovery
- Session management and security
- Event-driven task dispatch and result streaming

#### 3️⃣ **Execution Layer** (Device Agents)
- OS-specific agents (Windows, Linux, Android, etc.)
- MCP (Model Context Protocol) server integration
- Local environment access and tool execution
- Capability-based task matching

---

## ✨ Core Design Principles

UFO³ Galaxy is built around **five tightly integrated design principles**:

### 1. 🌟 Declarative Decomposition into Dynamic DAG (Task Constellation)

Natural-language or programmatic requests are decomposed by the **Constellation Agent** into a structured DAG of **Task Stars** (nodes) and **Star Lines** (edges) that encode workflow logic and dependencies. This declarative structure enables automated scheduling, introspection, and rewriting throughout execution.

```
User Intent → Constellation Agent → Task Constellation (DAG)
                                    ├─ Task Star 1 (Windows)
                                    ├─ Task Star 2 (Linux GPU) ─┐
                                    ├─ Task Star 3 (Linux CPU) ─┼─ Task Star 5
                                    └─ Task Star 4 (Mobile)    ─┘
```

### 2. 🔄 Continuous, Result-Driven Graph Evolution

The Task Constellation is a **living data structure**. Intermediate outputs, transient failures, and new observations trigger controlled rewrites—adding diagnostic Task Stars, creating fallbacks, rewiring dependencies, or pruning completed nodes—so the system adapts dynamically instead of aborting on errors.

### 3. 🎯 Heterogeneous, Asynchronous, and Safe Orchestration

Each Task Star is matched to the most suitable device agent via rich **Agent Profiles** reflecting OS, hardware, and capabilities. The Constellation Orchestrator:

- Executes tasks **asynchronously**, allowing multiple Task Stars to progress in parallel
- Maintains **safe assignment locking** to prevent race conditions
- Performs **DAG consistency checks** to ensure correctness
- Uses **event-driven scheduling** for efficient resource utilization

**Result**: High efficiency without compromising reliability, with formal verification guarantees.

### 4. 🔌 Unified Agent Interaction Protocol (AIP)

Built atop persistent **WebSocket channels**, UFO³ establishes a unified, secure, and extensible layer for:

- Agent registry and discovery
- Session management and authentication
- Task dispatch and result streaming
- Inter-agent coordination

This protocol **abstracts OS and network heterogeneity**, enabling seamless collaboration among agents across desktops, servers, and edge devices.

### 5. 🛠️ Template-Driven Framework for MCP-Empowered Device Agents

To **democratize agent creation**, UFO³ provides:

- Lightweight development templates
- Toolkit for rapidly building new device agents
- Declarative capability profiles
- **MCP (Model Context Protocol)** server integration for tool augmentation

This modular design accelerates integration while maintaining consistency across the constellation.

---

## 🎯 Key Capabilities

### 🌐 Cross-Device Collaboration
Execute workflows that span Windows desktops, Linux servers, GPU clusters, mobile devices, and edge nodes—all from a single natural language request.

### ⚡ Asynchronous Parallelism
Automatically identify parallelizable subtasks and execute them concurrently across devices, dramatically reducing end-to-end latency (up to **31% faster** than sequential execution).

### 🛡️ Fault Tolerance & Recovery
- **Automatic retries** for transient failures
- **Task migration** when devices become unavailable
- **Graceful degradation** under partial failures
- **Conservative recovery** under global failures

### 📊 Rich Observability
- Real-time constellation visualization
- Execution width metrics (average **1.72×**, peaking at **~3.5×** parallelism)
- Subtask completion tracking
- Dependency graph inspection

### 🔐 Security & Isolation
- Agent authentication and authorization
- Secure WebSocket communication
- Resource access control
- Capability-based permissions

---

## 📈 Performance Highlights

Evaluated on **GalaxyBench**—a benchmark of **55** cross-device tasks spanning **10** categories across **5** machines:

| Metric | Value |
|--------|-------|
| **Subtask Completion Rate (SCR)** | 83.3% |
| **Task Success Rate (TSR)** | 70.9% |
| **Average Execution Width** | 1.72× (peak ~3.5×) |
| **Latency Reduction** | 31% vs. sequential baseline |
| **Devices Tested** | Windows 11, 3× Ubuntu CPU, 1× Ubuntu A100 GPU |

---

## 🎨 Use Cases

### 🖥️ Software Development & Deployment
*"Clone the repo on my laptop, build the Docker image on the GPU server, deploy to staging, and run the test suite on the CI cluster."*

### 📊 Data Science Workflows
*"Fetch the dataset from S3, preprocess on the Linux workstation, train the model on the A100 node, and generate a visualization dashboard on my Windows machine."*

### 📱 Multi-Device Content Creation
*"Record a screen demo on my phone, transfer to my laptop, edit in Premiere Pro, render on the GPU server, and upload to YouTube."*

### 🔬 Distributed Research
*"Run hyperparameter sweeps across all available GPU nodes, collect results, generate comparison plots, and compile a summary report."*

### 🏢 Enterprise Automation
*"Extract data from the CRM on Windows, process with Python on Linux, generate charts in Excel, and email the report to stakeholders."*

---

## 🗺️ Documentation Structure

<div class="grid cards" markdown>

-   :material-rocket-launch: **[Quick Start](../getting_started/quick_start_galaxy.md)**

    ---
    
    Get UFO³ Galaxy up and running in minutes with our step-by-step guide

-   :material-star-settings: **[Constellation Agent](constellation_agent.md)**

    ---
    
    Learn how the Constellation Agent decomposes tasks and orchestrates workflows

-   :material-devices: **[Device Agents](device_agent.md)**

    ---
    
    Understand device agent architecture and create your own agents

-   :material-network: **[Agent Interaction Protocol](../aip/overview.md)**

    ---
    
    Deep dive into the communication layer and messaging protocol

-   :material-graph: **[Task Constellation](task_constellation.md)**

    ---
    
    Explore the DAG structure, evolution, and scheduling algorithms

-   :material-cog: **[Configuration](../getting_started/configuration_galaxy.md)**

    ---
    
    Configure device pools, capabilities, and orchestration policies

-   :material-shield-check: **[Safety & Verification](safety.md)**

    ---
    
    Learn about consistency guarantees, locking, and formal verification

-   :material-api: **[MCP Integration](../mcp/overview.md)**

    ---
    
    Extend device agents with Model Context Protocol servers

</div>

---

## 🚦 Getting Started

Ready to build your Digital Agent Galaxy? Follow these steps:

### 1. Install UFO³
```bash
# Clone the repository
git clone https://github.com/microsoft/UFO.git
cd UFO

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Device Pool
Create `config/galaxy/devices.yaml` to define your device constellation:

```yaml
devices:
  - name: "windows-desktop"
    type: "windows"
    capabilities: ["ui", "office", "browser"]
    
  - name: "linux-gpu-server"
    type: "linux"
    capabilities: ["python", "cuda", "docker"]
    hardware: 
      gpu: "A100"
```

### 3. Start Device Agents
On each device, launch the appropriate agent:

```bash
# On Windows
python -m ufo --mode galaxy-device --device windows-desktop

# On Linux
python -m ufo --mode galaxy-device --device linux-gpu-server
```

### 4. Launch Constellation Agent
```bash
python -m galaxy --task "Your cross-device task here"
```

For detailed instructions, see the [Quick Start Guide](../getting_started/quick_start_galaxy.md).

---

## 🌟 From Devices to Constellations to Galaxy

UFO³ represents a paradigm shift in intelligent automation:

- **Single Device** → Isolated agents operating within one OS
- **Task Constellation** → Coordinated multi-device workflows for one task
- **Digital Agent Galaxy** → Interconnected constellations spanning your entire digital estate

Over time, multiple constellations can interconnect, weaving together agents, devices, and capabilities into a self-organizing **Digital Agent Galaxy**. This design elevates cross-device automation from a brittle engineering challenge to a unified orchestration paradigm, where multi-device workflows become naturally expressive, paving the way for large-scale, adaptive, and resilient intelligent ubiquitous computing systems.

---

## 📚 Learn More

- **Research Paper**: [UFO³: Weaving the Digital Agent Galaxy](https://arxiv.org/) *(Coming Soon)*
- **UFO² (Desktop AgentOS)**: [Documentation](../ufo2/overview.md)
- **UFO (Original)**: [GitHub Repository](https://github.com/microsoft/UFO)

---

## 🤝 Contributing

We welcome contributions! Whether you're building new device agents, improving orchestration algorithms, or enhancing the protocol, check out our [Contributing Guide](../../CONTRIBUTING.md).

---

## 📄 License

UFO³ Galaxy is released under the [MIT License](../../LICENSE).

---

<div align="center">
  <p><strong>Transform your distributed devices into a unified digital collective.</strong></p>
  <p><em>UFO³ Galaxy — Where every device is a star, and every task is a constellation.</em></p>
</div>
