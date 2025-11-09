<!-- markdownlint-disable MD033 MD041 -->

<p align="center">
  <strong>📖 Language / 语言:</strong>
  <a href="README.md"><strong>English</strong></a> | 
  <a href="README_ZH.md">中文</a>
</p>

<!-- <h1 align="center">
  <img src="assets/logo3.png" alt="UFO logo" width="50">
  <br>
  <b>UFO³</b>
  <br>
  <em>Weaving the Digital Agent Galaxy</em>
</h1> -->


<h1 align="center">
  <b>UFO³</b> <img src="assets/logo3.png" alt="UFO logo" width="80" style="vertical-align: -20px;"> : Weaving the Digital Agent Galaxy
</h1>
<p align="center">
  <em>A From Single Device Agent to Multi-Device Galaxy</em>
</p>

<p align="center">
  <strong>📚 Quick Links:</strong>
  <a href="#-choose-your-path">🌌 UFO³ Overview</a> •
  <a href="./ufo/README.md">🖥️ UFO² README</a> •
  <a href="https://microsoft.github.io/UFO/">📖 Full Documentation</a>
</p>

<div align="center">

[![arxiv](https://img.shields.io/badge/Paper-arXiv:2504.14603-b31b1b.svg)](https://arxiv.org/abs/2504.14603)&ensp;
![Python Version](https://img.shields.io/badge/Python-3776AB?&logo=python&logoColor=white-blue&label=3.10%20%7C%203.11)&ensp;
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)&ensp;
[![Documentation](https://img.shields.io/badge/Documentation-%230ABAB5?style=flat&logo=readthedocs&logoColor=black)](https://microsoft.github.io/UFO/)&ensp;
[![YouTube](https://img.shields.io/badge/YouTube-white?logo=youtube&logoColor=%23FF0000)](https://www.youtube.com/watch?v=QT_OhygMVXU)&ensp;

</div>

---

## 🎯 Choose Your Path

<table align="center">
<tr>
<td width="50%" valign="top">

### <img src="assets/logo3.png" alt="Galaxy logo" width="40" style="vertical-align: -10px;"> **Galaxy** – Multi-Device Orchestration
<sub>**✨ NEW & RECOMMENDED**</sub>

**Perfect for:**
- 🔗 Cross-device collaboration workflows
- 📊 Complex multi-step automation  
- 🎯 DAG-based task orchestration
- 🌍 Heterogeneous platform integration

**Key Features:**
- **Constellation**: Task decomposition into executable DAGs
- **Dynamic device assignment** via capability matching
- **Real-time workflow monitoring** and adaptation
- **Event-driven coordination** across devices
- **Fault tolerance** with automatic recovery

**Get Started:**
```bash
python -m galaxy \
  --request "Your complex task"
```

**📖 [Galaxy Documentation →](./galaxy/README.md)**  
**📖 [Galaxy Quick Start →](https://microsoft.github.io/UFO/getting_started/quick_start_galaxy/)** ⭐ **Online Docs**

</td>
<td width="50%" valign="top">

### <img src="assets/ufo_blue.png" alt="UFO² logo" width="30" style="vertical-align: -5px;"> **UFO² Desktop AgentOS** – Windows AgentOS
<sub>**STABLE & BATTLE-TESTED**</sub>

**Perfect for:**
- 💻 Single Windows automation
- ⚡ Quick task execution
- 🎓 Learning agent basics
- 🛠️ Simple workflows

**Key Features:**
- Deep Windows OS integration
- Hybrid GUI + API actions
- Proven reliability
- Easy setup
- Can serve as Galaxy device agent

**Get Started:**
```bash
python -m ufo \
  --task <your_task_name>
```

**📖 [UFO² Documentation →](./ufo/README.md)**

</td>
</tr>
</table>

<div align="center">

### 🤔 Not sure which to choose?

| Question | Galaxy | UFO² |
|----------|:------:|:----:|
| Need cross-device collaboration? | ✅ | ❌ |
| Complex multi-step workflows? | ✅ | ⚠️ Limited |
| Windows-only automation? | ✅ | ✅ Optimized |
| Quick setup & learning? | ⚠️ Moderate | ✅ Easy |
| Production-ready stability? | 🚧 Active Dev | ✅ LTS |

</div>

---

## 🎬 See UFO³ Galaxy in Action

Watch how UFO³ Galaxy orchestrates complex workflows across multiple devices:

<div align="center">
  <a href="YOUR_YOUTUBE_VIDEO_URL_HERE">
    <img src="https://img.youtube.com/vi/VIDEO_ID_HERE/maxresdefault.jpg" alt="UFO³ Galaxy Demo" width="80%">
  </a>
  <p><em>🎥 Click to watch: Cross-device task orchestration with UFO³ Galaxy</em></p>
</div>

**What you'll see in the demo:**
- 🌟 Task constellation creation from natural language requests
- 🎯 Intelligent device assignment based on capabilities
- ⚡ Parallel execution across Windows and Linux devices
- 📊 Real-time monitoring and dynamic workflow adaptation

---

## 🌟 What's New in UFO³?

<h3 align="center">
  <img src="./assets/poster.png" width="70%"/> 
</h3>

### Evolution Timeline

```
2024.02    →    2025.04    →    2025.11
   ↓              ↓              ↓
  UFO           UFO²         UFO³ Galaxy
  GUI         Desktop        Multi-Device
Agent         AgentOS       Orchestration
```

### 🚀 UFO³ = **Galaxy** (Multi-Device Orchestration) + **UFO²** (Device Agent)

UFO³ introduces **Galaxy**, a novel multi-device orchestration framework that coordinates intelligent agents across heterogeneous platforms. Built on three core innovations:

1. **🌟 TaskConstellation** - Task decomposition into DAG-based workflows
2. **🎯 ConstellationAgent** - Intelligent task planning and device assignment  
3. **⚡ Dynamic Orchestration** - Real-time monitoring and adaptive execution

| Aspect | UFO² | UFO³ Galaxy |
|--------|------|-------------|
| **Architecture** | Single Windows Agent | Multi-Device Orchestration |
| **Task Model** | Sequential ReAct Loop | DAG-based Constellation Workflows |
| **Scope** | Single device, multi-app | Multi-device, cross-platform |
| **Coordination** | HostAgent + AppAgents | ConstellationAgent + TaskOrchestrator |
| **Device Support** | Windows Desktop | Windows, Linux, macOS, Android, Web |
| **Task Planning** | Application-level | Device-level with dependencies |
| **Execution** | Sequential | Parallel DAG execution |
| **Device Agent Role** | Standalone | Can serve as Galaxy device agent |
| **Complexity** | Simple to Moderate | Simple to Very Complex |
| **Learning Curve** | Low | Moderate |
| **Status** | ✅ LTS (Long-Term Support) | ⚡ Active Development |

### 🎓 Migration Path

**For UFO² Users:**
1. ✅ **Keep using UFO²** – Fully supported, actively maintained
2. 🔄 **Gradual adoption** – Galaxy can use UFO² as Windows device agent
3. 📈 **Scale up** – Move to Galaxy when you need multi-device capabilities
4. 📚 **Learning resources** – [Migration Guide](./documents/docs/getting_started/migration_ufo2_to_galaxy.md)

---

## ✨ Capabilities at a Glance

### 🌌 Galaxy Framework – What's Different?

<table>
<tr>
<td width="33%" valign="top">

#### 🌟 Constellation Planning
```
User: "Collect sales data from 
Excel on Windows, analyze on 
Linux, visualize on Mac"
        ↓
 ConstellationAgent
        ↓
    [Task DAG]
    /    |    \
 Task1 Task2 Task3
 (Win) (Linux)(Mac)
 
 ✓ Dependency tracking
 ✓ Parallel execution
 ✓ Cross-device data flow
```

</td>
<td width="33%" valign="top">

#### 🎯 Dynamic Device Assignment
```python
# Capability-based matching
Device Selection:
  - Platform compatibility
  - Resource availability
  - Task requirements
  - Performance history
  
Auto-assignment to:
  ✓ Best-fit devices
  ✓ Load balancing
  ✓ Fault tolerance
```

</td>
<td width="33%" valign="top">

#### 📊 Real-Time Orchestration
```
Task Execution Monitor:
┌─ Constellation ────┐
│ ✅ Data Collection │
│ 🔄 Processing     │
│ ⏸️  Visualization  │
│ ⏳ Report Gen     │
└───────────────────┘

✓ Live status updates
✓ Error recovery
✓ Progress tracking
```

</td>
</tr>
</table>

**Key Innovations from [UFO³ Paper](https://arxiv.org/abs/[TBD]):**

<div align="center">

| 🎯 Innovation | 💡 Description | 🚀 Impact |
|---------------|----------------|-----------|
| **🌟 Constellation Planning** | Decomposes complex requests into executable DAG workflows with task dependencies | Enables automated parallel execution and intelligent scheduling |
| **🌐 Heterogeneous Integration** | Seamless orchestration across Windows, Linux, macOS, Android, and Web platforms | Break free from single-platform limitations |
| **⚡ Event-Driven Architecture** | Real-time monitoring and adaptive execution with observer pattern | Dynamic workflow adjustments based on runtime feedback |
| **🎯 Intelligent Assignment** | Capability-based matching and dynamic resource allocation to optimal devices | Maximizes efficiency through smart device selection |
| **🛡️ Fault Tolerance** | Automatic error detection, recovery, and task rescheduling mechanisms | Ensures workflow completion despite device failures |

</div>

### 🪟 UFO² Desktop AgentOS – Core Strengths

UFO² serves dual roles: **standalone Windows automation** and **Galaxy device agent** for Windows platforms.

<div align="center">

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Deep OS Integration** | Windows UIA, Win32, WinCOM native control | [Learn More](https://microsoft.github.io/UFO) |
| **Hybrid Actions** | GUI clicks + API calls for optimal performance | [Learn More](https://microsoft.github.io/UFO/automator/overview) |
| **Speculative Multi-Action** | Batch predictions → **51% fewer LLM calls** | [Learn More](https://microsoft.github.io/UFO/advanced_usage/multi_action) |
| **Visual + UIA Detection** | Hybrid control detection for robustness | [Learn More](https://microsoft.github.io/UFO/advanced_usage/control_detection/hybrid_detection) |
| **Knowledge Substrate** | RAG with docs, demos, execution traces | [Learn More](https://microsoft.github.io/UFO/advanced_usage/reinforce_appagent/overview/) |
| **Device Agent Role** | Can serve as Windows executor in Galaxy orchestration | [Learn More](./galaxy/README.md) |

</div>

**As Galaxy Device Agent:**
- Receives tasks from ConstellationAgent via Galaxy orchestration layer
- Executes Windows-specific operations using proven UFO² capabilities
- Reports status and results back to TaskOrchestrator
- Participates in cross-device workflows seamlessly

---

## 🚀 Quick Start Guide

Choose your path and follow the detailed setup guide:

<table align="center">
<tr>
<td width="50%" valign="top">

### 🌌 Galaxy Quick Start

**For cross-device orchestration**

```powershell
# 1. Install
pip install -r requirements.txt

# 2. Configure ConstellationAgent
copy config\galaxy\agent.yaml.template config\galaxy\agent.yaml
# Edit and add your API keys

# 3. Start device agents (with platform flags)
# Windows:
python -m ufo.server.app --port 5000
python -m ufo.client.client --ws --ws-server ws://localhost:5000/ws --client-id windows_device_1 --platform windows

# Linux:
python -m ufo.server.app --port 5001
python -m ufo.client.client --ws --ws-server ws://localhost:5001/ws --client-id linux_device_1 --platform linux

# 4. Launch Galaxy
python -m galaxy --interactive
```

**📖 Complete Guide:**
- [Galaxy README](./galaxy/README.md) – Architecture & concepts
- [Online Quick Start](https://microsoft.github.io/UFO/getting_started/quick_start_galaxy/) – Step-by-step tutorial
- [Configuration](https://microsoft.github.io/UFO/configuration/system/galaxy_devices/) – Device setup

</td>
<td width="50%" valign="top">

### 🪟 UFO² Quick Start

**For Windows automation**

```powershell
# 1. Install
pip install -r requirements.txt

# 2. Configure
copy config\ufo\agents.yaml.template config\ufo\agents.yaml
# Edit and add your API keys

# 3. Run
python -m ufo --task <task_name>
```

**📖 Complete Guide:**
- [UFO² README](./ufo/README.md) – Full documentation
- [Configuration Guide](./ufo/README.md#️-step-2-configure-the-llms) – LLM setup
- [Advanced Features](https://microsoft.github.io/UFO/advanced_usage/overview/) – Multi-action, RAG

</td>
</tr>
</table>

### 📋 Common Configuration

Both frameworks require LLM API configuration. Choose your provider:

<details>
<summary><strong>OpenAI Configuration</strong></summary>

**For Galaxy (`config/galaxy/agent.yaml`):**
```yaml
CONSTELLATION_AGENT:
  REASONING_MODEL: false
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-your-key-here"
  API_MODEL: "gpt-4o"
```

**For UFO² (`config/ufo/agents.yaml`):**
```yaml
VISUAL_MODE: True
API_TYPE: "openai"
API_BASE: "https://api.openai.com/v1/chat/completions"
API_KEY: "sk-your-key-here"
API_MODEL: "gpt-4o"
```

</details>

<details>
<summary><strong>Azure OpenAI Configuration</strong></summary>

**For Galaxy (`config/galaxy/agent.yaml`):**
```yaml
CONSTELLATION_AGENT:
  REASONING_MODEL: false
  API_TYPE: "aoai"
  API_BASE: "https://YOUR-RESOURCE.openai.azure.com"
  API_KEY: "your-azure-key"
  API_MODEL: "gpt-4o"
  API_DEPLOYMENT_ID: "your-deployment-id"
```

**For UFO² (`config/ufo/agents.yaml`):**
```yaml
VISUAL_MODE: True
API_TYPE: "aoai"
API_BASE: "https://YOUR-RESOURCE.openai.azure.com"
API_KEY: "your-azure-key"
API_MODEL: "gpt-4o"
API_DEPLOYMENT_ID: "your-deployment-id"
```

</details>

> 💡 **More LLM Options:** See [Model Configuration Guide](https://microsoft.github.io/UFO/supported_models/overview/) for Qwen, Gemini, Claude, and more.

---

## 📚 Documentation Structure

<table>
<tr>
<td width="50%" valign="top">

### 🌌 Galaxy Documentation

- **[Galaxy Framework Overview](./galaxy/README.md)** ⭐ **Start Here** – Architecture & technical concepts
- **[Quick Start Tutorial](https://microsoft.github.io/UFO/getting_started/quick_start_galaxy/)** – Get running in minutes
- **[Galaxy Client](https://microsoft.github.io/UFO/galaxy/client/overview/)** – Device coordination and API
- **[Constellation Agent](https://microsoft.github.io/UFO/galaxy/constellation_agent/overview/)** – Task decomposition and planning
- **[Task Orchestrator](https://microsoft.github.io/UFO/galaxy/constellation_orchestrator/overview/)** – Execution engine
- **[Task Constellation](https://microsoft.github.io/UFO/galaxy/constellation/overview/)** – DAG structure
- **[Agent Registration](https://microsoft.github.io/UFO/galaxy/agent_registration/overview/)** – Device registry
- **[Configuration Guide](https://microsoft.github.io/UFO/configuration/system/galaxy_devices/)** – Setup and device pools

**📖 Technical Documentation:**
- [AIP Protocol](https://microsoft.github.io/UFO/aip/overview/) – WebSocket messaging
- [Session Management](https://microsoft.github.io/UFO/galaxy/session/overview/) – Session lifecycle
- [Visualization](https://microsoft.github.io/UFO/galaxy/visualization/overview/) – Real-time monitoring
- [Events & Observers](https://microsoft.github.io/UFO/galaxy/core/overview/) – Event system

</td>
<td width="50%" valign="top">

### 🪟 UFO² Documentation

- **[UFO² Overview](./ufo/README.md)** – Desktop AgentOS architecture
- **[Installation](./ufo/README.md#️-step-1-installation)** – Setup & dependencies
- **[Configuration](./ufo/README.md#️-step-2-configure-the-llms)** – LLM & RAG setup
- **[Usage Guide](./ufo/README.md#-step-4-start-ufo)** – Running UFO²
- **[Advanced Features](https://microsoft.github.io/UFO/advanced_usage/overview/)** – Multi-action, RAG, etc.
- **[Automator Guide](https://microsoft.github.io/UFO/automator/overview)** – Hybrid GUI + API
- **[Benchmarks](./ufo/README.md#-evaluation)** – WAA & OSWorld results

**📖 Online Docs:**
- [Complete Documentation](https://microsoft.github.io/UFO/)
- [Model Support](https://microsoft.github.io/UFO/supported_models/overview/)
- [RAG Configuration](https://microsoft.github.io/UFO/advanced_usage/reinforce_appagent/overview/)

</td>
</tr>
</table>

---

## 🎓 Learning Path

### For Complete Beginners
```
1. 📖 Read UFO² Overview (simpler)
   └─ Understand single-agent concepts
   
2. 🧪 Try UFO² with simple tasks
   └─ Get hands-on experience
   
3. 📈 Explore Galaxy when ready
   └─ Scale to multi-device workflows
```

### For UFO² Users
```
1. ✅ Continue using UFO² for Windows tasks
   └─ Fully supported, no pressure to migrate
   
2. 📚 Learn Galaxy concepts gradually
   └─ DAG workflows, device orchestration
   
3. 🔄 Hybrid approach
   └─ Use Galaxy for complex tasks, UFO² for simple ones
   
4. 📖 Follow migration guide when ready
   └─ [Migration Guide](./documents/docs/getting_started/migration_ufo2_to_galaxy.md)
```

### For Advanced Users
```
1. 🌌 Dive into Galaxy architecture
   └─ ConstellationAgent, TaskOrchestrator
   
2. 🔧 Customize and extend
   └─ Custom agents, device types, visualizations
   
3. 🤝 Contribute
   └─ Join development, share feedback
```

---

## 🏗️ Architecture Comparison

### UFO² – Desktop AgentOS

<div align="center">
  <img src="./assets/framework2.png" alt="UFO² Architecture" width="80%"/>
  <p><em>UFO² Desktop AgentOS Architecture</em></p>
</div>

**Key Characteristics:**
- Sequential task execution with ReAct loop
- Single-device focus (Windows)
- HostAgent coordinates AppAgents per application
- Deep Windows integration (UIA, Win32, WinCOM)

---

### UFO³ Galaxy – Multi-Device Orchestration Framework

<div align="center">
  <img src="./documents/docs/img/overview2.png" alt="UFO³ Galaxy Architecture" width="90%"/>
  <p><em>UFO³ Galaxy Layered Architecture — Cross-device orchestration</em></p>
</div>

**Key Components (from UFO³ Paper):**
1. **ConstellationAgent**: Plans and decomposes tasks into DAG workflows
2. **TaskConstellation (星座)**: DAG representation with TaskStar nodes and dependencies
3. **Device Pool Manager**: Matches tasks to capable devices dynamically
4. **TaskOrchestrator**: Coordinates parallel execution and handles data flow
5. **Event System**: Real-time monitoring with observer pattern for adaptation
6. **Device Agents**: Platform-specific executors (UFO² for Windows, shell for Linux/macOS, etc.)

**Key Characteristics:**
- **Constellation-based planning** with task dependencies
- **Parallel DAG execution** for efficiency
- **Multi-device coordination** across heterogeneous platforms
- **Dynamic device assignment** via capability matching
- **Event-driven architecture** for real-time adaptation
- **Fault tolerance** with automatic recovery

---

## 📊 Feature Matrix

<div align="center">

| Feature | UFO² Desktop AgentOS | UFO³ Galaxy | Winner |
|---------|:--------------------:|:-----------:|:------:|
| **Windows Automation** | ⭐⭐⭐⭐⭐ Optimized | ⭐⭐⭐⭐ Supported | UFO² |
| **Cross-Device Tasks** | ❌ Not supported | ⭐⭐⭐⭐⭐ Core feature | Galaxy |
| **Setup Complexity** | ⭐⭐⭐⭐⭐ Very easy | ⭐⭐⭐ Moderate | UFO² |
| **Learning Curve** | ⭐⭐⭐⭐⭐ Gentle | ⭐⭐⭐ Moderate | UFO² |
| **Task Complexity** | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent | Galaxy |
| **Parallel Execution** | ❌ Sequential | ⭐⭐⭐⭐⭐ Native DAG | Galaxy |
| **Production Ready** | ⭐⭐⭐⭐⭐ Stable | ⭐⭐⭐ Active dev | UFO² |
| **Monitoring Tools** | ⭐⭐⭐ Logs | ⭐⭐⭐⭐⭐ Real-time viz | Galaxy |
| **API Flexibility** | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Extensive | Galaxy |
| **Community Support** | ⭐⭐⭐⭐⭐ Established | ⭐⭐⭐ Growing | UFO² |

</div>

---

## 🎯 Use Case Guide

### When to Use UFO² Desktop AgentOS

✅ **Perfect for:**
- 📊 Excel/Word/PowerPoint automation
- 🌐 Browser automation (Edge, Chrome)
- 📁 File system operations
- ⚙️ Windows system configuration
- 🎓 Learning agent-based automation
- ⚡ Quick, simple tasks
- 🏢 Production-critical workflows (stable)

**Example Scenarios:**
```
✓ "Create monthly sales report in Excel"
✓ "Search for research papers and save PDFs"
✓ "Organize downloads folder by file type"
✓ "Update product catalog in Access database"
✓ "Extract data from PDF to Excel"
```

---

### When to Use UFO³ Galaxy

✅ **Perfect for:**
- 🔗 **Multi-device workflows** - Tasks spanning heterogeneous platforms
- 📊 **Complex data pipelines** - ETL processes across different systems
- 🤖 **Parallel task execution** - DAG-based workflows with dependencies
- 🌍 **Cross-platform orchestration** - Windows, Linux, macOS, Android coordination
- 📈 **Scalable automation** - Dynamic device pool management
- 🔄 **Adaptive workflows** - Real-time monitoring and recovery
- 🎯 **Advanced orchestration** - Constellation-based task planning

**Example Scenarios (from UFO³ Paper):**
```
✓ "Extract data from Windows Excel, process on Linux server, visualize on Mac"
✓ "Run tests on Windows, deploy to Linux production, update mobile app"
✓ "Collect logs from multiple devices, aggregate and analyze centrally"
✓ "Distributed data processing across heterogeneous compute resources"
✓ "Cross-platform CI/CD pipeline with device-specific testing"
✓ "Multi-device IoT orchestration and monitoring"
```

**Key Advantage:** Constellation framework automatically handles task dependencies, device assignment, and parallel execution.

---

### Hybrid Approach (Best of Both Worlds)

**UFO² as Galaxy Device Agent:**
Galaxy can leverage UFO² as a specialized Windows device agent, combining Galaxy's orchestration power with UFO²'s proven Windows automation capabilities.


---

## 💡 FAQ

<details>
<summary><strong>🤔 Should I use Galaxy or UFO²?</strong></summary>

**Start with UFO²** if:
- You only need Windows automation
- You want quick setup and learning
- You need production stability
- Tasks are relatively simple

**Choose Galaxy** if:
- You need cross-device coordination
- Tasks are complex and multi-step
- You want advanced orchestration
- You're comfortable with active development

**Hybrid approach** if:
- You want best of both worlds
- Some tasks are simple (UFO²), some complex (Galaxy)
- You're gradually migrating

</details>

<details>
<summary><strong>⚠️ Will UFO² be deprecated?</strong></summary>

**No!** UFO² has entered **Long-Term Support (LTS)** status:
- ✅ Actively maintained
- ✅ Bug fixes and security updates
- ✅ Performance improvements
- ✅ Full community support
- ✅ No plans for deprecation

UFO² is the stable, proven solution for Windows automation.

</details>

<details>
<summary><strong>🔄 How do I migrate from UFO² to Galaxy?</strong></summary>

Migration is **gradual and optional**:

1. **Phase 1: Learn** – Understand Galaxy concepts
2. **Phase 2: Experiment** – Try Galaxy with non-critical tasks
3. **Phase 3: Hybrid** – Use both frameworks
4. **Phase 4: Migrate** – Gradually move complex tasks to Galaxy

**No forced migration!** Continue using UFO² as long as it meets your needs.

See [Migration Guide](./documents/docs/getting_started/migration_ufo2_to_galaxy.md) for details.

</details>

<details>
<summary><strong>🎯 Can Galaxy do everything UFO² does?</strong></summary>

**Functionally: Yes.** Galaxy can use UFO² as a Windows device agent.

**Practically: It depends.**
- For **simple Windows tasks**: UFO² standalone is easier and more streamlined
- For **complex workflows**: Galaxy orchestrates UFO² with other device agents
- For **production**: UFO² offers proven stability

**Recommendation:** Use the right tool for the job. UFO² can work standalone or as Galaxy's Windows device agent.

</details>

<details>
<summary><strong>📊 How mature is Galaxy?</strong></summary>

**Status: Active Development** 🚧

**Stable:**
- ✅ Core architecture
- ✅ DAG orchestration
- ✅ Basic multi-device support
- ✅ Event system

**In Development:**
- 🔨 Advanced device types
- 🔨 Enhanced monitoring
- 🔨 Performance optimization
- 🔨 Extended documentation

**Recommendation:** Great for experimentation and non-critical workflows. For production, consider UFO² or hybrid approach.

</details>

<details>
<summary><strong>🔧 Can I extend or customize?</strong></summary>

**Both frameworks are highly extensible:**

**UFO²:**
- Custom actions and automators
- Custom knowledge sources (RAG)
- Custom control detectors
- Custom evaluation metrics

**Galaxy:**
- Custom agents
- Custom device types
- Custom orchestration strategies
- Custom visualization components

See respective documentation for extension guides.

</details>

<details>
<summary><strong>🤝 How can I contribute?</strong></summary>

We welcome contributions to both UFO² and Galaxy!

**Ways to contribute:**
- 🐛 Report bugs and issues
- 💡 Suggest features and improvements
- 📝 Improve documentation
- 🧪 Add tests and examples
- 🔧 Submit pull requests

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

</details>

---

## 📊 Benchmarks & Evaluation

### UFO² Desktop AgentOS

**Tested on:**
- ✅ [Windows Agent Arena (WAA)](https://github.com/nice-mee/WindowsAgentArena) – 154 real tasks
- ✅ [OSWorld (Windows)](https://github.com/nice-mee/WindowsAgentArena/tree/2020-qqtcg/osworld) – 49 cross-app tasks

**Performance:**
- High success rate on Office automation
- Robust control detection
- Efficient multi-action speculation

**📖 [Detailed Results →](./ufo/README.md#-evaluation)**

### UFO³ Galaxy

**Evaluated on Multi-Device Benchmarks:**

According to the [UFO³ technical paper](https://arxiv.org/abs/[TBD]):

- ✅ **Cross-Device Workflows**: 50+ complex multi-device scenarios
- ✅ **Heterogeneous Platforms**: Windows, Linux, macOS, Android integration
- ✅ **Parallel Execution**: DAG-based workflows with dependency management
- ✅ **Fault Tolerance**: Automatic error recovery and task rescheduling

**Key Metrics:**
- **Task Completion Rate**: Successful orchestration across multiple devices
- **Parallel Efficiency**: Speedup from DAG-based parallel execution
- **Device Assignment Accuracy**: Correct capability matching and selection
- **Fault Recovery**: Automatic detection and recovery from device failures

**Research Highlights:**
1. **Novel Constellation Framework**: First multi-device orchestration system for GUI agents
2. **Dynamic Device Assignment**: Intelligent capability-based task-to-device matching
3. **Real-time Adaptation**: Event-driven monitoring and workflow adjustments
4. **Heterogeneous Integration**: Seamless coordination across diverse platforms

**📖 [Full Evaluation Details →](./galaxy/benchmarks/)** | **📄 [Read the Paper →](https://arxiv.org/abs/[TBD])**

**Status:** Active research project with ongoing benchmark development

---

## 🗺️ Roadmap

### UFO² Desktop AgentOS (Stable/LTS)
- ✅ Long-term support and maintenance
- ✅ Bug fixes and security updates
- ✅ Performance optimization
- ✅ Integration with Galaxy as Windows device agent
- 🔜 Enhanced device agent capabilities for Galaxy
- 🔜 Picture-in-Picture desktop mode

### UFO³ Galaxy (Active Development)
- ✅ **Constellation Framework** - DAG-based task planning **[DONE]**
- ✅ **ConstellationAgent** - Intelligent task decomposition **[DONE]**
- ✅ **Multi-device coordination** - Heterogeneous platform support **[DONE]**
- ✅ **Event-driven architecture** - Real-time monitoring with observers **[DONE]**
- ✅ **Dynamic device assignment** - Capability-based matching **[DONE]**
- 🔄 **Advanced device types** - Mobile, Web, IoT agents **[IN PROGRESS]**
- 🔄 **Enhanced visualization** - Interactive constellation graphs **[IN PROGRESS]**
- 🔄 **Performance optimization** - Parallel execution efficiency **[IN PROGRESS]**
- 🔜 **Fault tolerance enhancement** - Advanced recovery strategies
- 🔜 **Cross-device data flow** - Optimized inter-device communication
- 🔜 Auto-debugging toolkit

**Legend:** ✅ Done | 🔄 In Progress | 🔜 Planned

---

## 📢 Latest Updates

### 2025-11 – UFO³ Galaxy Framework Released 🌌
**Major Research Breakthrough:** Multi-Device Orchestration System

- 🌟 **Constellation Framework**: Novel DAG-based task planning for multi-device workflows
- 🎯 **ConstellationAgent**: Intelligent task decomposition with dependency analysis
- 🔗 **Cross-Platform Integration**: Seamless orchestration across Windows, Linux, macOS, Android
- ⚡ **Dynamic Device Assignment**: Capability-based matching and resource allocation
- 📊 **Real-Time Monitoring**: Event-driven architecture with observer pattern
- 🛡️ **Fault Tolerance**: Automatic error detection and recovery mechanisms
- 📄 **Research Paper**: [UFO³: Weaving the Digital Agent Galaxy](https://arxiv.org/abs/[TBD])

**Key Innovations:**
- First multi-device orchestration framework for GUI agents
- Constellation (星座) metaphor for distributed task workflows
- Heterogeneous platform coordination with unified interface
- Parallel DAG execution for improved efficiency

### 2025-04 – UFO² v2.0.0
- 📅 UFO² Desktop AgentOS released
- 🏗️ Enhanced architecture with AgentOS concept
- 📄 [Technical Report](https://arxiv.org/pdf/2504.14603) published
- ✅ Entered Long-Term Support (LTS) status

### 2024-02 – Original UFO
- 🎈 First UFO release - UI-Focused agent for Windows
- 📄 [Original Paper](https://arxiv.org/abs/2402.07939)
- 🌍 Wide media coverage and adoption

---

## 📚 Citation

If you use UFO³ Galaxy or UFO² in your research, please cite the relevant papers:

### UFO³ Galaxy Framework (2025)
```bibtex
@article{zhang2025ufo3,
  title   = {{UFO³: Weaving the Digital Agent Galaxy}},
  author  = {Zhang, Chaoyun and [Authors TBD]},
  journal = {arXiv preprint arXiv:[TBD]},
  year    = {2025},
  note    = {Multi-device orchestration framework with Constellation-based planning}
}
```

**Paper Highlights:**
- Novel Constellation framework for multi-device task orchestration
- ConstellationAgent for intelligent task decomposition into DAG workflows
- Dynamic device assignment via capability-based matching
- Event-driven architecture for real-time monitoring and adaptation
- Evaluation on cross-platform workflows and heterogeneous device integration

### UFO² Desktop AgentOS (2025)
```bibtex
@article{zhang2025ufo2,
  title   = {{UFO2: The Desktop AgentOS}},
  author  = {Zhang, Chaoyun and Huang, He and Ni, Chiming and Mu, Jian and Qin, Si and He, Shilin and Wang, Lu and Yang, Fangkai and Zhao, Pu and Du, Chao and Li, Liqun and Kang, Yu and Jiang, Zhao and Zheng, Suzhen and Wang, Rujia and Qian, Jiaxu and Ma, Minghua and Lou, Jian-Guang and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei},
  journal = {arXiv preprint arXiv:2504.14603},
  year    = {2025}
}
```

### Original UFO (2024)
```bibtex
@article{zhang2024ufo,
  title   = {{UFO: A UI-Focused Agent for Windows OS Interaction}},
  author  = {Zhang, Chaoyun and Li, Liqun and He, Shilin and Zhang, Xu and Qiao, Bo and Qin, Si and Ma, Minghua and Kang, Yu and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei and Zhang, Qi},
  journal = {arXiv preprint arXiv:2402.07939},
  year    = {2024}
}
```

---

## 🌐 Media & Community

**Media Coverage:**
- [微软正式开源UFO²，Windows桌面迈入「AgentOS 时代」](https://www.jiqizhixin.com/articles/2025-05-06-13)
- [Microsoft's UFO: Smarter Windows Experience](https://the-decoder.com/microsofts-ufo-abducts-traditional-user-interfaces-for-a-smarter-windows-experience/)
- [下一代Windows系统曝光](https://baijiahao.baidu.com/s?id=1790938358152188625)
- **[More coverage →](./ufo/README.md#-tracing-the-stars)**

**Community:**
- 💬 [GitHub Discussions](https://github.com/microsoft/UFO/discussions)
- 🐛 [Issue Tracker](https://github.com/microsoft/UFO/issues)
- 📧 Email: [ufo-agent@microsoft.com](mailto:ufo-agent@microsoft.com)
- 📺 [YouTube Channel](https://www.youtube.com/watch?v=QT_OhygMVXU)

---

## 🎨 Related Projects & Research

**Microsoft Research:**
- **[TaskWeaver](https://github.com/microsoft/TaskWeaver)** – Code-first LLM agent framework for data analytics and task automation
- **[AutoGen](https://github.com/microsoft/autogen)** – Multi-agent conversation framework for building LLM applications

**GUI Agent Research:**
- **[LLM-Brained GUI Agents Survey](https://github.com/vyokky/LLM-Brained-GUI-Agents-Survey)** – Comprehensive survey of GUI automation agents
- **[Interactive Survey Site](https://vyokky.github.io/LLM-Brained-GUI-Agents-Survey/)** – Explore latest GUI agent research and developments

**Multi-Agent Systems:**
- **UFO³ Galaxy** represents a novel approach to multi-device orchestration, introducing the Constellation framework for coordinating heterogeneous agents across platforms
- Builds on multi-agent coordination research while addressing unique challenges of cross-device GUI automation

**Benchmarks:**
- **[Windows Agent Arena (WAA)](https://github.com/nice-mee/WindowsAgentArena)** – Evaluation benchmark for Windows automation agents
- **[OSWorld](https://github.com/nice-mee/WindowsAgentArena/tree/2020-qqtcg/osworld)** – Cross-application task evaluation suite

---

## ⚠️ Disclaimer & License

**Disclaimer:** By using this software, you acknowledge and agree to the terms in [DISCLAIMER.md](./DISCLAIMER.md).

**License:** This project is licensed under the [MIT License](LICENSE).

**Trademarks:** Use of Microsoft trademarks follows [Microsoft's Trademark Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).

---

<div align="center">

## 🚀 Ready to Get Started?

<table>
<tr>
<td align="center" width="50%">

### 🌌 Explore Galaxy
**Multi-Device Orchestration**

[![Start Galaxy](https://img.shields.io/badge/Start-Galaxy-blue?style=for-the-badge)](./galaxy/README.md)

</td>
<td align="center" width="50%">

### 🪟 Try UFO²
**Windows Desktop Agent**

[![Start UFO²](https://img.shields.io/badge/Start-UFO²-green?style=for-the-badge)](./ufo/README.md)

</td>
</tr>
</table>

---

<sub>© Microsoft 2025 | UFO³ is an open-source research project</sub>

<sub>⭐ Star us on GitHub | 🤝 Contribute | 📖 Read the docs | 💬 Join discussions</sub>

</div>

---

<p align="center">
  <img src="assets/logo3.png" alt="UFO logo" width="60">
  <br>
  <em>From Single Agent to Digital Galaxy</em>
  <br>
  <strong>UFO³ - Weaving the Future of Intelligent Automation</strong>
</p>
