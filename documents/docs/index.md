# Welcome to UFO³ Documentation

<div align="center">
  <h1>
    <b>UFO³</b> <img src="./img/logo3.png" alt="UFO logo" width="80" style="vertical-align: -30px;"> : Weaving the Digital Agent Galaxy
  </h1>
  <p><em>A Multi-Device Orchestration Framework for Cross-Platform Intelligent Automation</em></p>
</div>

<div align="center">

[![arxiv](https://img.shields.io/badge/Paper-arXiv:2504.14603-b31b1b.svg)](https://arxiv.org/abs/2504.14603)&ensp;
![Python Version](https://img.shields.io/badge/Python-3776AB?&logo=python&logoColor=white-blue&label=3.10%20%7C%203.11)&ensp;
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)&ensp;
[![github](https://img.shields.io/github/stars/microsoft/UFO)](https://github.com/microsoft/UFO)&ensp;
[![YouTube](https://img.shields.io/badge/YouTube-white?logo=youtube&logoColor=%23FF0000)](https://www.youtube.com/watch?v=QT_OhygMVXU)&ensp;

</div>

---

## 🎯 Choose Your Path

UFO³ offers two complementary frameworks for intelligent automation:

<table align="center">
<tr>
<td width="50%" valign="top">

### 🌌 **Galaxy** – Multi-Device Orchestration
<sub>**✨ NEW & CUTTING-EDGE**</sub>

**Perfect for:**
- 🔗 Cross-device collaboration workflows
- 📊 Complex multi-step automation  
- 🎯 DAG-based task orchestration
- 🌍 Heterogeneous platform integration

**Key Features:**
- **Constellation Framework**: Task decomposition into executable DAGs
- **Dynamic device assignment** via capability matching
- **Real-time workflow monitoring** and adaptation
- **Event-driven coordination** across devices
- **Fault tolerance** with automatic recovery

**Get Started:**
```bash
python -m galaxy --interactive
```

**📖 [Galaxy Documentation →](galaxy/overview.md)**  
**📖 [Galaxy Quick Start →](getting_started/quick_start_galaxy.md)** ⭐

</td>
<td width="50%" valign="top">

### 🪟 **UFO² Desktop AgentOS** – Windows Agent
<sub>**STABLE & BATTLE-TESTED**</sub>

**Perfect for:**
- 💻 Single Windows automation
- ⚡ Quick task execution
- 🎓 Learning agent basics
- 🛠️ Simple workflows

**Key Features:**
- Deep Windows OS integration (UIA, Win32, WinCOM)
- Hybrid GUI + API actions
- Proven reliability and stability
- Easy setup and learning curve
- Can serve as Galaxy device agent

**Get Started:**
```bash
python -m ufo --task <your_task_name>
```

**📖 [UFO² Documentation →](ufo2/overview.md)**  
**📖 [UFO² Quick Start →](getting_started/quick_start_ufo2.md)**

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

## 🌟 What's New in UFO³?

<div align="center">
  <img src="./img/poster.png" width="70%" alt="UFO³ Evolution"/> 
</div>

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

---

## ✨ Capabilities at a Glance

### 🌌 Galaxy Framework – Cross-Device Orchestration

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
```
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

**Key Innovations:**
- **Constellation-based Planning**: Decomposes complex requests into executable DAG workflows
- **Heterogeneous Device Integration**: Seamlessly orchestrates Windows, Linux, macOS, Android, and Web
- **Event-Driven Architecture**: Real-time monitoring and adaptive execution with observer pattern
- **Intelligent Device Assignment**: Capability matching and dynamic resource allocation
- **Fault Tolerance**: Automatic error detection, recovery, and task rescheduling

### 🪟 UFO² Desktop AgentOS – Core Strengths

UFO² serves dual roles: **standalone Windows automation** and **Galaxy device agent** for Windows platforms.

<div align="center">

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Deep OS Integration** | Windows UIA, Win32, WinCOM native control | [Learn More](ufo2/overview.md) |
| **Hybrid Actions** | GUI clicks + API calls for optimal performance | [Learn More](ufo2/core_features/hybrid_actions.md) |
| **Speculative Multi-Action** | Batch predictions → **51% fewer LLM calls** | [Learn More](ufo2/core_features/multi_action.md) |
| **Visual + UIA Detection** | Hybrid control detection for robustness | [Learn More](ufo2/core_features/control_detection/hybrid_detection.md) |
| **Knowledge Substrate** | RAG with docs, demos, execution traces | [Learn More](ufo2/core_features/knowledge_substrate/overview.md) |
| **Device Agent Role** | Can serve as Windows executor in Galaxy orchestration | [Learn More](galaxy/overview.md) |

</div>

---

## 🏗️ Architecture Comparison

### UFO² – Desktop AgentOS

<div align="center">
  <img src="./img/framework2.png" alt="UFO² Architecture" width="80%"/>
  <p><em>UFO² Desktop AgentOS Architecture</em></p>
</div>

**Key Characteristics:**
- Sequential task execution with ReAct loop
- Single-device focus (Windows)
- HostAgent coordinates AppAgents per application
- Deep Windows integration (UIA, Win32, WinCOM)

**Components:**
1. **HostAgent** – Desktop orchestrator, application lifecycle management
2. **AppAgents** – Per-application executors with hybrid GUI–API actions
3. **Knowledge Substrate** – RAG-enhanced learning from docs & execution history
4. **Speculative Executor** – Multi-action prediction for efficiency

---

### UFO³ Galaxy – Multi-Device Orchestration Framework

<div align="center">
  <img src="./img/overview2.png" alt="UFO³ Galaxy Architecture" width="90%"/>
  <p><em>UFO³ Galaxy Layered Architecture — Cross-device orchestration</em></p>
</div>

**Key Components:**
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

## 🚀 Quick Start Guide

Choose your path and follow the detailed setup guide:

<table align="center">
<tr>
<td width="50%" valign="top">

### 🌌 Galaxy Quick Start

**For cross-device orchestration**

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
copy config\galaxy\agents.yaml.template config\galaxy\agents.yaml
# Edit and add your API keys

# 3. Start device agents
python -m ufo --mode agent-server --port 5005

# 4. Launch Galaxy
python -m galaxy --interactive
```

**📖 Complete Guide:**
- [Galaxy Quick Start](getting_started/quick_start_galaxy.md) – Step-by-step tutorial
- [Galaxy Overview](galaxy/overview.md) – Architecture & concepts
- [Configuration](configuration/system/galaxy_devices.md) – Device setup

</td>
<td width="50%" valign="top">

### 🪟 UFO² Quick Start

**For Windows automation**

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
copy config\ufo\agents.yaml.template config\ufo\agents.yaml
# Edit and add your API keys

# 3. Run
python -m ufo --task <task_name>
```

**📖 Complete Guide:**
- [UFO² Quick Start](getting_started/quick_start_ufo2.md) – Step-by-step tutorial
- [UFO² Overview](ufo2/overview.md) – Full documentation
- [Advanced Features](ufo2/core_features/overview.md) – Multi-action, RAG

</td>
</tr>
</table>

---

## 📚 Documentation Structure

<table>
<tr>
<td width="50%" valign="top">

### 🌌 Galaxy Documentation

- **[Galaxy Framework Overview](galaxy/overview.md)** ⭐ **Start Here** – Architecture & technical concepts
- **[Quick Start Tutorial](getting_started/quick_start_galaxy.md)** – Get running in minutes
- **[Galaxy Client](galaxy/client/overview.md)** – Device coordination and API
- **[Constellation Agent](galaxy/constellation_agent/overview.md)** – Task decomposition and planning
- **[Task Orchestrator](galaxy/constellation_orchestrator/overview.md)** – Execution engine
- **[Task Constellation](galaxy/constellation/overview.md)** – DAG structure
- **[Agent Registration](galaxy/agent_registration/overview.md)** – Device registry
- **[Configuration Guide](configuration/system/galaxy_devices.md)** – Setup and device pools

**📖 Technical Documentation:**
- [AIP Protocol](aip/overview.md) – WebSocket messaging
- [Session Management](galaxy/session/overview.md) – Session lifecycle
- [Visualization](galaxy/visualization/overview.md) – Real-time monitoring
- [Events & Observers](galaxy/core/overview.md) – Event system

</td>
<td width="50%" valign="top">

### 🪟 UFO² Documentation

- **[UFO² Overview](ufo2/overview.md)** – Desktop AgentOS architecture
- **[Quick Start](getting_started/quick_start_ufo2.md)** – Setup & basic usage
- **[HostAgent](ufo2/host_agent/overview.md)** – Desktop orchestrator
- **[AppAgent](ufo2/app_agent/overview.md)** – Application executor
- **[Hybrid Actions](ufo2/core_features/hybrid_actions.md)** – GUI–API execution
- **[Control Detection](ufo2/core_features/control_detection/overview.md)** – UIA + visual grounding
- **[Knowledge Substrate](ufo2/core_features/knowledge_substrate/overview.md)** – RAG-enhanced learning
- **[Multi-Action](ufo2/core_features/multi_action.md)** – Speculative execution

**📖 Advanced Topics:**
- [Agent Architecture](infrastructure/agents/overview.md) – Three-layer design
- [MCP Integration](mcp/overview.md) – Model Context Protocol
- [Benchmarks](ufo2/evaluation/benchmark/overview.md) – WAA & OSWorld results

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

**Example Scenarios:**
```
✓ "Extract data from Windows Excel, process on Linux server, visualize on Mac"
✓ "Run tests on Windows, deploy to Linux production, update mobile app"
✓ "Collect logs from multiple devices, aggregate and analyze centrally"
✓ "Distributed data processing across heterogeneous compute resources"
✓ "Cross-platform CI/CD pipeline with device-specific testing"
```

---

## 🌐 Media Coverage

Check out our official deep dive of UFO on [this Youtube Video](https://www.youtube.com/watch?v=QT_OhygMVXU).

UFO sightings have garnered attention from various media outlets:

- [微软正式开源UFO²，Windows桌面迈入「AgentOS 时代」](https://www.jiqizhixin.com/articles/2025-05-06-13)
- [Microsoft's UFO: Smarter Windows Experience](https://the-decoder.com/microsofts-ufo-abducts-traditional-user-interfaces-for-a-smarter-windows-experience/)
- [🚀 UFO & GPT-4-V: Sit back and relax, mientras GPT lo hace todo🌌](https://www.linkedin.com/posts/gutierrezfrancois_ai-ufo-microsoft-activity-7176819900399652865-pLoo?utm_source=share&utm_medium=member_desktop)
- [The AI PC - The Future of Computers? - Microsoft UFO](https://www.youtube.com/watch?v=1k4LcffCq3E)
- [下一代Windows系统曝光：基于GPT-4V，Agent跨应用调度，代号UFO](https://baijiahao.baidu.com/s?id=1790938358152188625&wfr=spider&for=pc)
- [下一代智能版 Windows 要来了？微软推出首个 Windows Agent，命名为 UFO！](https://blog.csdn.net/csdnnews/article/details/136161570)
- [Microsoft発のオープンソース版「UFO」登場！　Windowsを自動操縦するAIエージェントを試す](https://internet.watch.impress.co.jp/docs/column/shimizu/1570581.html)

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

## 📝 Roadmap

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

**Legend:** ✅ Done | 🔄 In Progress | 🔜 Planned

---

## 🎨 Related Projects

**Microsoft Research:**
- **[TaskWeaver](https://github.com/microsoft/TaskWeaver)** – Code-first LLM agent framework for data analytics
- **[AutoGen](https://github.com/microsoft/autogen)** – Multi-agent conversation framework

**GUI Agent Research:**
- **[LLM-Brained GUI Agents Survey](https://github.com/vyokky/LLM-Brained-GUI-Agents-Survey)** – Comprehensive survey
- **[Interactive Survey Site](https://vyokky.github.io/LLM-Brained-GUI-Agents-Survey/)** – Latest GUI agent research

**Benchmarks:**
- **[Windows Agent Arena (WAA)](https://github.com/nice-mee/WindowsAgentArena)** – Evaluation benchmark
- **[OSWorld](https://github.com/nice-mee/WindowsAgentArena/tree/2020-qqtcg/osworld)** – Cross-application tasks

---

## ❓Get Help

- 📖 **Documentation**: [https://microsoft.github.io/UFO/](https://microsoft.github.io/UFO/)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/microsoft/UFO/discussions)
- 🐛 **Issues**: [GitHub Issues](https://github.com/microsoft/UFO/issues)
- 📧 **Email**: [ufo-agent@microsoft.com](mailto:ufo-agent@microsoft.com)

---

## ⚖️ License & Disclaimer

**License:** This project is licensed under the [MIT License](https://github.com/microsoft/UFO/blob/main/LICENSE).

**Disclaimer:** By using this software, you acknowledge and agree to the terms in the [DISCLAIMER](https://github.com/microsoft/UFO/blob/main/DISCLAIMER.md).

**Trademarks:** Use of Microsoft trademarks follows [Microsoft's Trademark Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).

---

<div align="center">

## 🚀 Ready to Get Started?

<table>
<tr>
<td align="center" width="50%">

### 🌌 Explore Galaxy
**Multi-Device Orchestration**

[![Start Galaxy](https://img.shields.io/badge/Start-Galaxy-blue?style=for-the-badge)](galaxy/overview.md)

</td>
<td align="center" width="50%">

### 🪟 Try UFO²
**Windows Desktop Agent**

[![Start UFO²](https://img.shields.io/badge/Start-UFO²-green?style=for-the-badge)](ufo2/overview.md)

</td>
</tr>
</table>

---

<sub>© Microsoft 2025 | UFO³ is an open-source research project</sub>

<sub>⭐ Star us on GitHub | 🤝 Contribute | 📖 Read the docs | 💬 Join discussions</sub>

</div>

---

<p align="center">
  <img src="./img/logo3.png" alt="UFO logo" width="60">
  <br>
  <em>From Single Agent to Digital Galaxy</em>
  <br>
  <strong>UFO³ - Weaving the Future of Intelligent Automation</strong>
</p>

---
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-FX17ZGJYGC"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-FX17ZGJYGC');
</script>
