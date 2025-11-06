<!-- markdownlint-disable MD033 MD041 -->
<h1 align="center">
  <b>UFO³</b> <img src="../assets/logo3.png" alt="UFO³ logo" width="80" style="vertical-align: -30px;"> : Weaving the Digital Agent Galaxy
</h1>
<p align="center">
  <em>Cross-Device Orchestration Framework for Ubiquitous Intelligent Automation</em>
</p>

<div align="center">

[![arxiv](https://img.shields.io/badge/Paper-arXiv:TBD-b31b1b.svg)](https://arxiv.org/)&ensp;
![Python Version](https://img.shields.io/badge/Python-3776AB?&logo=python&logoColor=white-blue&label=3.10%20%7C%203.11)&ensp;
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)&ensp;
[![Documentation](https://img.shields.io/badge/Documentation-%230ABAB5?style=flat&logo=readthedocs&logoColor=black)](https://microsoft.github.io/UFO/)&ensp;

</div>

---

<h3 align="center">
  <img src="../assets/poster.png" width="85%"/> 
</h3>

<p align="center">
  <em><strong>From isolated device agents to interconnected constellations — Building the Digital Agent Galaxy</strong></em>
</p>

---

## 🌟 What is UFO³ Galaxy?

**UFO³ Galaxy** is a revolutionary **cross-device orchestration framework** that transforms isolated device agents into a unified digital ecosystem. It models complex user requests as **Task Constellations** (星座) — dynamic distributed DAGs where nodes represent executable subtasks and edges capture dependencies across heterogeneous devices.

### 🎯 The Vision

Building truly ubiquitous intelligent agents requires moving beyond single-device automation. UFO³ Galaxy addresses four fundamental challenges:

<table>
<tr>
<td width="50%" valign="top">

**🔄 Asynchronous Parallelism**
Concurrent task execution across devices while maintaining correctness through event-driven coordination

**⚡ Dynamic Adaptation**  
Real-time workflow evolution based on runtime feedback and task completion events

</td>
<td width="50%" valign="top">

**🌐 Distributed Coordination**  
Reliable, low-latency cross-device communication via WebSocket-based Agent Interaction Protocol

**🛡️ Safety Guarantees**  
Formal invariants (I1-I3) ensure DAG consistency during concurrent modifications and parallel execution

</td>
</tr>
</table>

---

## ✨ Key Innovations

### 1. 🌟 Task Constellation Framework

Natural language requests are decomposed into **Task Constellations** — structured DAG workflows with **TaskStars** (nodes) and **TaskStarLines** (edges) encoding task logic, dependencies, and device assignments.

```
User Intent → ConstellationAgent → Task Constellation (DAG)
                                    ├─ TaskStar 1 (Windows)
                                    ├─ TaskStar 2 (Linux GPU) ─┐
                                    ├─ TaskStar 3 (Linux CPU) ─┼─ TaskStar 5
                                    └─ TaskStar 4 (Mobile)    ─┘
```

**Key Benefits:**
- Declarative workflow representation for automated scheduling
- Runtime introspection and dynamic modification
- Parallel execution of independent subtasks
- Cross-device data flow management

### 2. 🎯 Intelligent Constellation Agent

LLM-powered agent that operates in two modes:

- **Creation Mode**: Synthesizes initial DAG from user request with device-aware task decomposition
- **Editing Mode**: Incrementally refines constellation based on task completion events and runtime feedback

**Features:**
- ReAct architecture for context-aware planning
- Capability-based device assignment
- Automatic error recovery and workflow adaptation
- State machine control with safe transitions

### 3. ⚡ Event-Driven Orchestration

**Constellation Orchestrator** executes DAGs asynchronously with:

- **Observer pattern** for real-time task status monitoring
- **Safe assignment locking** to prevent race conditions
- **Three formal invariants** ensuring DAG correctness:
  - **I1**: Single assignment per TaskStar
  - **I2**: Acyclic DAG consistency
  - **I3**: Valid device assignment
- **Dynamic task scheduling** based on dependency completion
- **Automatic retry and migration** on failures

### 4. 🔌 Agent Interaction Protocol (AIP)

Unified WebSocket-based communication layer providing:

- **Device registration** with capability profiles
- **Heartbeat monitoring** for availability tracking
- **Task dispatch** with dynamic routing
- **Result streaming** with real-time progress updates
- **Connection resilience** with automatic reconnection

---

## 🏗️ Architecture Overview

<div align="center">
  <img src="../documents/docs/img/overview2.png" alt="UFO³ Galaxy Architecture" style="max-width: 100%; height: auto; margin: 20px 0;">
  <p><em>UFO³ Galaxy Layered Architecture — From natural language to distributed execution</em></p>
</div>

### Hierarchical Design

**Control Plane:**
- **ConstellationClient**: Global device registry with capability profiles, health metrics, and load balancing
- **Device Agents**: Local orchestration on each device with unified MCP-based tool interfaces
- **Clean separation**: Global policies decoupled from device-specific heterogeneity

**Execution Flow:**
1. **DAG Synthesis**: ConstellationAgent constructs TaskConstellation from user request
2. **Device Assignment**: Tasks matched to capable devices based on profiles and availability
3. **Asynchronous Execution**: Orchestrator executes DAG with event-driven coordination
4. **Dynamic Adaptation**: Workflow evolves based on task completions, failures, and system dynamics

---

## 🚀 Quick Start

### 🛠️ Step 1: Installation

```powershell
# Clone repository
git clone https://github.com/microsoft/UFO.git
cd UFO

# Create environment (recommended)
conda create -n ufo3 python=3.10
conda activate ufo3

# Install dependencies
pip install -r requirements.txt
```

### ⚙️ Step 2: Configure LLM Services

```powershell
# Create configuration from template
copy config\galaxy\agents.yaml.template config\galaxy\agents.yaml
notepad config\galaxy\agents.yaml
```

**OpenAI Configuration:**
```yaml
CONSTELLATION_AGENT:
  VISUAL_MODE: true
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_KEY_HERE"
  API_MODEL: "gpt-4o"
```

**Azure OpenAI Configuration:**
```yaml
CONSTELLATION_AGENT:
  VISUAL_MODE: true
  API_TYPE: "aoai"
  API_BASE: "https://YOUR_RESOURCE.openai.azure.com"
  API_KEY: "YOUR_AOAI_KEY"
  API_VERSION: "2024-02-15-preview"
  API_MODEL: "gpt-4o"
  API_DEPLOYMENT_ID: "YOUR_DEPLOYMENT_ID"
```

### 🌐 Step 3: Configure Device Pool

```powershell
# Configure available devices
copy config\galaxy\devices.yaml.template config\galaxy\devices.yaml
notepad config\galaxy\devices.yaml
```

**Example Device Configuration:**
```yaml
devices:
  - device_id: "windows_desktop"
    server_url: "ws://localhost:5005/ws"
    os: "windows"
    capabilities:
      - "office_applications"
      - "web_browsing"
      - "file_management"
    metadata:
      performance: "high"
      location: "office"
    max_retries: 5
    
  - device_id: "linux_server"
    server_url: "ws://192.168.1.100:5001/ws"
    os: "linux"
    capabilities:
      - "python_execution"
      - "data_processing"
      - "gpu_compute"
    metadata:
      gpu: "NVIDIA A100"
      performance: "very_high"
    auto_connect: true
```

### 🖥️ Step 4: Start Device Agents

On each device, launch the Agent Server:

**Windows Device:**
```powershell
# Start UFO² Agent Server
python -m ufo --mode agent-server --port 5005
```

**Linux Device:**
```bash
# Start Agent Server
python -m ufo --mode agent-server --port 5001
```

### 🌌 Step 5: Launch Galaxy Client

**Interactive Mode:**
```powershell
python -m galaxy --interactive
```

**Direct Request:**
```powershell
python -m galaxy --request "Extract data from Excel on Windows, process with Python on Linux, and generate visualization report"
```

**Programmatic API:**
```python
from galaxy.galaxy_client import GalaxyClient

async def main():
    # Initialize client
    client = GalaxyClient(session_name="data_pipeline")
    await client.initialize()
    
    # Execute cross-device workflow
    result = await client.process_request(
        "Download sales data, analyze trends, generate executive summary"
    )
    
    # Access constellation details
    constellation = client.session.constellation
    print(f"Tasks executed: {len(constellation.tasks)}")
    print(f"Devices used: {set(t.assigned_device for t in constellation.tasks)}")
    
    await client.shutdown()

import asyncio
asyncio.run(main())
```

---

## 🎯 Use Cases

### 🖥️ Software Development & CI/CD

**Request:**  
*"Clone repository on Windows, build Docker image on Linux GPU server, deploy to staging, and run test suite on CI cluster"*

**Constellation Workflow:**
```
Clone (Windows) → Build (Linux GPU) → Deploy (Linux Server) → Test (Linux CI)
```

**Benefit:** Parallel execution reduces pipeline time by 60%

---

### 📊 Data Science Workflows

**Request:**  
*"Fetch dataset from cloud storage, preprocess on Linux workstation, train model on A100 node, visualize results on Windows"*

**Constellation Workflow:**
```
Fetch (Any) → Preprocess (Linux) → Train (Linux GPU) → Visualize (Windows)
```

**Benefit:** Automatic GPU detection and optimal device assignment

---

### 📝 Cross-Platform Document Processing

**Request:**  
*"Extract data from Excel on Windows, process with Python on Linux, generate PDF report, and email summary"*

**Constellation Workflow:**
```
Extract (Windows) → Process (Linux) ┬→ Generate PDF (Windows)
                                      └→ Send Email (Windows)
```

**Benefit:** Parallel report generation and email delivery

---

### 🔬 Distributed System Monitoring

**Request:**  
*"Collect server logs from all Linux machines, analyze for errors, generate alerts, create consolidated report"*

**Constellation Workflow:**
```
┌→ Collect (Linux 1) ┐
├→ Collect (Linux 2) ├→ Analyze (Any) → Report (Windows)
└→ Collect (Linux 3) ┘
```

**Benefit:** Parallel log collection with automatic aggregation

---

## 🌐 Core Capabilities

<table>
<tr>
<td width="50%" valign="top">

### ⚡ Asynchronous Parallelism
- Event-driven scheduling monitors DAG for ready tasks
- Non-blocking execution with Python `asyncio`
- Dynamic integration of new tasks without interruption
- **Result:** Up to 70% reduction in end-to-end latency

### 🛡️ Safety & Consistency
- Three formal invariants (I1-I3) for DAG correctness
- Safe assignment locking prevents race conditions
- Acyclicity validation ensures no circular dependencies
- State merging preserves execution progress during edits

</td>
<td width="50%" valign="top">

### 🔄 Dynamic Adaptation
- Dual-mode operation (creation/editing) with FSM control
- Feedback-driven constellation refinement
- LLM-powered reasoning via ReAct architecture
- Automatic error recovery and task rescheduling

### 👁️ Rich Observability
- Real-time constellation visualization with DAG updates
- Event bus with publish-subscribe pattern
- Detailed execution logs with markdown trajectories
- Task status tracking and dependency inspection

</td>
</tr>
</table>

---

## 📚 Documentation

| Component | Description | Link |
|-----------|-------------|------|
| **Galaxy Client** | Device coordination and ConstellationClient API | [Learn More](../documents/docs/galaxy/client/overview.md) |
| **Constellation Agent** | LLM-driven task decomposition and DAG evolution | [Learn More](../documents/docs/galaxy/constellation_agent/overview.md) |
| **Task Orchestrator** | Asynchronous execution and safety guarantees | [Learn More](../documents/docs/galaxy/constellation_orchestrator/overview.md) |
| **Task Constellation** | DAG structure and constellation editor | [Learn More](../documents/docs/galaxy/constellation/overview.md) |
| **Agent Registration** | Device registry and agent profiles | [Learn More](../documents/docs/galaxy/agent_registration/overview.md) |
| **AIP Protocol** | WebSocket messaging and communication patterns | [Learn More](../documents/docs/aip/overview.md) |
| **Configuration** | Device pools and orchestration policies | [Learn More](../documents/docs/configuration/system/galaxy_devices.md) |

---

## 📊 System Architecture

### Core Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| **GalaxyClient** | `galaxy/galaxy_client.py` | Session management, user interaction |
| **ConstellationClient** | `galaxy/client/constellation_client.py` | Device registry, connection lifecycle |
| **ConstellationAgent** | `galaxy/agents/constellation_agent.py` | DAG synthesis and evolution |
| **TaskConstellationOrchestrator** | `galaxy/constellation/orchestrator/` | Asynchronous execution, safety enforcement |
| **TaskConstellation** | `galaxy/constellation/task_constellation.py` | DAG data structure and validation |
| **DeviceManager** | `galaxy/client/device_manager.py` | WebSocket connections, heartbeat monitoring |
| **Agent Server** | `ufo/mode/agent_server.py` | Device-side WebSocket server |

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Language** | Python 3.10+, asyncio, dataclasses |
| **Communication** | WebSockets, JSON-RPC |
| **LLM** | OpenAI, Azure OpenAI, Gemini, Claude |
| **Tools** | Model Context Protocol (MCP) |
| **Config** | YAML, Pydantic validation |
| **Logging** | Rich console, Markdown trajectories |

---

## 🌟 From Devices to Galaxy

UFO³ represents a paradigm shift in intelligent automation:

```
Single Device  →  Task Constellation  →  Digital Agent Galaxy
   (UFO/UFO²)           (UFO³ Galaxy)         (Future Vision)
     ↓                    ↓                      ↓
  Windows          Cross-Device           Self-Organizing
  Desktop          Workflows              Ecosystem
```

Over time, multiple constellations interconnect, forming a self-organizing **Digital Agent Galaxy** where devices, agents, and capabilities weave together into adaptive, resilient, and intelligent ubiquitous computing systems.

---

## 📄 Citation

If you use UFO³ Galaxy in your research, please cite:

**UFO³ Galaxy Framework:**
```bibtex
@article{zhang2025ufo3,
  title   = {{UFO³: Weaving the Digital Agent Galaxy}},
  author  = {Zhang, Chaoyun and [Authors TBD]},
  journal = {arXiv preprint arXiv:[TBD]},
  year    = {2025}
}
```

**UFO² Desktop AgentOS:**
```bibtex
@article{zhang2025ufo2,
  title   = {{UFO2: The Desktop AgentOS}},
  author  = {Zhang, Chaoyun and Huang, He and Ni, Chiming and Mu, Jian and Qin, Si and He, Shilin and Wang, Lu and Yang, Fangkai and Zhao, Pu and Du, Chao and Li, Liqun and Kang, Yu and Jiang, Zhao and Zheng, Suzhen and Wang, Rujia and Qian, Jiaxu and Ma, Minghua and Lou, Jian-Guang and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei},
  journal = {arXiv preprint arXiv:2504.14603},
  year    = {2025}
}
```

---

## 🤝 Contributing

We welcome contributions! Whether building new device agents, improving orchestration algorithms, or enhancing the protocol:

- 🐛 [Report Issues](https://github.com/microsoft/UFO/issues)
- 💡 [Request Features](https://github.com/microsoft/UFO/discussions)
- 📝 [Improve Documentation](https://github.com/microsoft/UFO/pulls)
- 🧪 [Submit Pull Requests](../../CONTRIBUTING.md)

---

## 📬 Contact & Support

- 📖 **Documentation**: [https://microsoft.github.io/UFO/](https://microsoft.github.io/UFO/)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/microsoft/UFO/discussions)
- 🐛 **Issues**: [GitHub Issues](https://github.com/microsoft/UFO/issues)
- 📧 **Email**: [ufo-agent@microsoft.com](mailto:ufo-agent@microsoft.com)

---

## ⚖️ License

UFO³ Galaxy is released under the [MIT License](../../LICENSE).

See [DISCLAIMER.md](../../DISCLAIMER.md) for privacy and safety notices.

---

<div align="center">
  <p><strong>Transform your distributed devices into a unified digital collective.</strong></p>
  <p><em>UFO³ Galaxy — Where every device is a star, and every task is a constellation.</em></p>
  <br>
  <sub>© Microsoft 2025 • UFO³ is an open-source research project</sub>
</div>
