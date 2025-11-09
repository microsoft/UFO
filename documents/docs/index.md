# Welcome to UFO³ Documentation

<div align="center">
  <h1>
    <b>UFO³</b> <img src="./img/logo3.png" alt="UFO logo" width="80" style="vertical-align: -30px;"> : Weaving the Digital Agent Galaxy
  </h1>
  <p><em>A Multi-Device Orchestration Framework for Cross-Platform Intelligent Automation</em></p>
</div>


[![arxiv](https://img.shields.io/badge/Paper-arXiv:2504.14603-b31b1b.svg)](https://arxiv.org/abs/2504.14603)
![Python Version](https://img.shields.io/badge/Python-3776AB?&logo=python&logoColor=white-blue&label=3.10%20%7C%203.11)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/github/stars/microsoft/UFO)](https://github.com/microsoft/UFO)
[![YouTube](https://img.shields.io/badge/YouTube-white?logo=youtube&logoColor=%23FF0000)](https://www.youtube.com/watch?v=QT_OhygMVXU)


---

<div align="center">
  <img src="./img/poster.png" width="100%" alt="UFO³ Evolution"/> 
</div>


## 📖 About This Documentation

Welcome to the official documentation for **UFO³**, Microsoft's open-source framework for intelligent automation across devices and platforms. Whether you're looking to automate Windows applications or orchestrate complex workflows across multiple devices, this documentation will guide you through every step.

**What you'll find here:**

- 🚀 **[Quick Start Guides](getting_started/quick_start_galaxy.md)** – Get up and running in minutes
- 📚 **[Core Concepts](galaxy/overview.md)** – Understand the architecture and key components  
- ⚙️ **[Configuration](configuration/system/agents_config.md)** – Set up your agents and models
- 🔧 **[Advanced Features](ufo2/core_features/multi_action.md)** – Deep dive into powerful capabilities
- 💡 **[FAQ](faq.md)** – Common questions and troubleshooting

---

## 🎯 Choose Your Path

UFO³ consists of two complementary frameworks. Choose the one that best fits your needs, or use both together!

| Framework | Best For | Key Strength | Get Started |
|-----------|----------|--------------|-------------|
| **🌌 Galaxy** <br> <sub>✨ NEW & RECOMMENDED</sub> | Cross-device workflows<br>Complex automation<br>Parallel execution | Multi-device orchestration<br>DAG-based planning<br>Real-time monitoring | [Quick Start →](getting_started/quick_start_galaxy.md) |
| **🪟 UFO²** <br> <sub>⚡ STABLE & LTS</sub> | Windows automation<br>Quick tasks<br>Learning basics | Deep Windows integration<br>Hybrid GUI + API<br>Production ready | [Quick Start →](getting_started/quick_start_ufo2.md) |

### 🤔 Decision Guide

| Question | Galaxy | UFO² |
|----------|:------:|:----:|
| Need cross-device collaboration? | ✅ | ❌ |
| Complex multi-step workflows? | ✅ | ⚠️ Limited |
| Windows-only automation? | ✅ | ✅ Optimized |
| Quick setup & learning? | ⚠️ Moderate | ✅ Easy |
| Production-ready stability? | 🚧 Active Dev | ✅ LTS |

---

## 🌟 What's New in UFO³?

**UFO³ is a scalable, universal cross-device agent framework** that enables you to develop new device agents for different platforms and applications. Through the **Agent Interaction Protocol (AIP)**, custom device agents can seamlessly integrate into UFO³ Galaxy for coordinated multi-device orchestration.

**Evolution Journey:** From single-device automation to multi-device orchestration

```
2024.02    →    2025.04    →    2025.11
   ↓              ↓              ↓
  UFO           UFO²         UFO³ Galaxy
Single        Desktop       Multi-Device
Agent        AgentOS       Orchestration
```

### 🚀 Key Innovations

UFO³ introduces the **Galaxy framework** – a revolutionary multi-device orchestration framework that coordinates intelligent agents across heterogeneous platforms. Built on five tightly integrated design principles:

1. **🌟 Declarative Decomposition into Dynamic DAG** - Natural language or programmatic requests are decomposed by the ConstellationAgent into a structured DAG of TaskStars and TaskStarLines that encode workflow logic, dependencies, and device assignments — amenable to automated scheduling, introspection, and rewriting throughout execution

2. **🔄 Continuous Result-Driven Graph Evolution** - The TaskConstellation is a living data structure that evolves in response to execution feedback. Intermediate outputs, transient failures, and new observations trigger controlled rewrites (diagnostic TaskStars, fallbacks, dependency rewiring, node pruning) — enabling dynamic adaptation instead of workflow abortion

3. **⚡ Heterogeneous, Asynchronous & Safe Orchestration** - Each TaskStar is matched to the most suitable device agent via rich AgentProfiles reflecting OS, hardware, and capabilities. The Constellation Orchestrator executes tasks asynchronously with safe assignment locking, event-driven scheduling, DAG consistency checks, and batched edits — ensuring high efficiency without compromising reliability, reinforced through formal verification

4. **🔌 Unified Agent Interaction Protocol (AIP)** - Built atop persistent WebSocket channels, AIP provides a unified, secure, and fault-tolerant layer for agent registry, session management, task dispatch, and coordination — ensuring reliability under network fluctuations through automatic reconnection and retry, while exposing a lightweight, extensible interface for seamless ecosystem integration

5. **🛠️ Template-Driven MCP-Empowered Device Agents** - A lightweight development template and toolkit for rapidly building new device agents. Developers can declare capabilities, bind to local environments, and extend through Model Context Protocol (MCP) servers for tool augmentation — this modular design accelerates integration while maintaining consistency across the constellation

| Component | What It Does | Learn More |
|-----------|-------------|------------|
| **🌟 TaskConstellation** | Decomposes tasks into DAG-based workflows with dependencies | [Documentation →](galaxy/constellation/task_constellation.md) |
| **🎯 ConstellationAgent** | Intelligent planning and device assignment | [Documentation →](galaxy/constellation_agent/overview.md) |
| **⚡ TaskOrchestrator** | Real-time monitoring and adaptive execution | [Documentation →](galaxy/constellation_orchestrator/overview.md) |
| **🔗 AIP Protocol** | WebSocket-based agent communication | [Documentation →](aip/overview.md) |

### Framework Comparison

Not sure which framework to use? Here's a quick comparison to help you decide:

| Aspect | UFO² Desktop AgentOS | UFO³ Galaxy | Documentation |
|--------|------|-------------|---------------|
| **Architecture** | Single Windows Agent | Multi-Device Orchestration | [UFO²](ufo2/overview.md) \| [Galaxy](galaxy/overview.md) |
| **Task Model** | Sequential ReAct Loop | DAG-based Constellation | [Details →](galaxy/constellation/overview.md) |
| **Scope** | Single device, multi-app | Multi-device, cross-platform | [Choose Path →](choose_path.md) |
| **Device Support** | Windows Desktop | Windows, Linux, macOS, Android, Web | [Device Setup →](configuration/system/galaxy_devices.md) |
| **Execution** | Sequential | Parallel DAG execution | [Orchestration →](galaxy/constellation_orchestrator/overview.md) |
| **Status** | ✅ LTS & Production Ready | ⚡ Active Development | [FAQ →](faq.md) |

**💡 See [Choosing Your Path](choose_path.md) for detailed guidance on which framework fits your needs.**

---

## ✨ Key Capabilities

### 🌌 Galaxy Framework

| Capability | Description |
|------------|-------------|
| **🌟 Constellation Planning** | Decomposes requests into DAG workflows with dependencies |
| **🎯 Device Assignment** | Intelligent matching based on platform, resources, capabilities |
| **📊 Real-Time Orchestration** | Live monitoring, error recovery, progress tracking |
| **⚡ Parallel Execution** | Concurrent task execution across multiple devices |
| **🔄 Fault Tolerance** | Automatic error detection, recovery, task rescheduling |

### 🪟 UFO² Desktop AgentOS

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Deep OS Integration** | Windows UIA, Win32, WinCOM native control | [Learn More](ufo2/overview.md) |
| **Hybrid Actions** | GUI clicks + API calls for optimal performance | [Learn More](ufo2/core_features/hybrid_actions.md) |
| **Multi-Action** | Batch predictions → **51% fewer LLM calls** | [Learn More](ufo2/core_features/multi_action.md) |
| **Hybrid Detection** | Visual + UIA control detection | [Learn More](ufo2/core_features/control_detection/hybrid_detection.md) |
| **Knowledge Substrate** | RAG with docs, demos, execution traces | [Learn More](ufo2/core_features/knowledge_substrate/overview.md) |

---

## 🏗️ Architecture

### UFO³ Galaxy – Multi-Device Orchestration

<div align="center">
  <img src="./img/overview2.png" alt="UFO³ Galaxy Architecture" width="70%"/>
</div>

| Component | Role |
|-----------|------|
| **ConstellationAgent** | Plans and decomposes tasks into DAG workflows |
| **TaskConstellation** | DAG representation with TaskStar nodes and dependencies |
| **Device Pool Manager** | Matches tasks to capable devices dynamically |
| **TaskOrchestrator** | Coordinates parallel execution and handles data flow |
| **Event System** | Real-time monitoring with observer pattern |

[📖 Learn More →](galaxy/overview.md)

### UFO² – Desktop AgentOS

<div align="center">
  <img src="./img/framework2.png" alt="UFO² Architecture" width="75%"/>
</div>

| Component | Role |
|-----------|------|
| **HostAgent** | Desktop orchestrator, application lifecycle management |
| **AppAgents** | Per-application executors with hybrid GUI–API actions |
| **Knowledge Substrate** | RAG-enhanced learning from docs & execution history |
| **Speculative Executor** | Multi-action prediction for efficiency |

[📖 Learn More →](ufo2/overview.md)

---

## 🚀 Quick Start

Ready to dive in? Follow these guides to get started with your chosen framework:

### 🌌 Galaxy Quick Start (Multi-Device Orchestration)

Perfect for complex workflows across multiple devices and platforms.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure agents (see detailed guide for API key setup)
copy config\galaxy\agent.yaml.template config\galaxy\agent.yaml
copy config\ufo\agents.yaml.template config\ufo\agents.yaml

# 3. Start device agents
python -m ufo.server.app --port 5000
python -m ufo.client.client --ws --ws-server ws://localhost:5000/ws --client-id device_1 --platform windows

# 4. Launch Galaxy
python -m galaxy --interactive
```

**📖 [Complete Galaxy Quick Start Guide →](getting_started/quick_start_galaxy.md)**  
**⚙️ [Galaxy Configuration Details →](configuration/system/galaxy_devices.md)**

### 🪟 UFO² Quick Start (Windows Automation)

Perfect for Windows-only automation tasks with quick setup.

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure (add your API keys)
copy config\ufo\agents.yaml.template config\ufo\agents.yaml

# 3. Run
python -m ufo --task <task_name>
```

**📖 [Complete UFO² Quick Start Guide →](getting_started/quick_start_ufo2.md)**  
**⚙️ [UFO² Configuration Details →](configuration/system/agents_config.md)**

---

## 📚 Documentation Navigation

### 🎯 Getting Started

Start here if you're new to UFO³:

| Guide | Description | Framework |
|-------|-------------|-----------|
| [Galaxy Quick Start](getting_started/quick_start_galaxy.md) | Set up multi-device orchestration in 10 minutes | 🌌 Galaxy |
| [UFO² Quick Start](getting_started/quick_start_ufo2.md) | Start automating Windows in 5 minutes | 🪟 UFO² |
| [Choosing Your Path](choose_path.md) | Decision guide for selecting the right framework | Both |

### 🏗️ Core Architecture

Understand how UFO³ works under the hood:

| Topic | Description | Framework |
|-------|-------------|-----------|
| [Galaxy Overview](galaxy/overview.md) | Multi-device orchestration architecture | 🌌 Galaxy |
| [UFO² Overview](ufo2/overview.md) | Desktop AgentOS architecture and concepts | 🪟 UFO² |
| [Task Constellation](galaxy/constellation/overview.md) | DAG-based workflow representation | 🌌 Galaxy |
| [ConstellationAgent](galaxy/constellation_agent/overview.md) | Intelligent task planner and decomposer | 🌌 Galaxy |
| [Task Orchestrator](galaxy/constellation_orchestrator/overview.md) | Execution engine and coordinator | 🌌 Galaxy |
| [AIP Protocol](aip/overview.md) | Agent communication protocol | 🌌 Galaxy |

### ⚙️ Configuration & Setup

Configure your agents, models, and environments:

| Topic | Description | Framework |
|-------|-------------|-----------|
| [Agent Configuration](configuration/system/agents_config.md) | LLM and agent settings | Both |
| [Galaxy Devices](configuration/system/galaxy_devices.md) | Device pool and capability management | 🌌 Galaxy |
| [Model Providers](configuration/models/overview.md) | Supported LLMs (OpenAI, Azure, Qwen, etc.) | Both |

### 🎓 Tutorials & Examples

Learn through practical examples in the documentation:

| Topic | Description | Framework |
|-------|-------------|-----------|
| [Creating App Agents](tutorials/creating_app_agent/overview.md) | Build custom application agents | 🪟 UFO² |
| [Multi-Action Prediction](ufo2/core_features/multi_action.md) | Efficient batch predictions | 🪟 UFO² |
| [Knowledge Substrate](ufo2/core_features/knowledge_substrate/overview.md) | RAG-enhanced learning | 🪟 UFO² |

### 🔧 Advanced Topics

Deep dive into powerful features:

| Topic | Description | Framework |
|-------|-------------|-----------|
| [Multi-Action Prediction](ufo2/core_features/multi_action.md) | Batch actions for 51% fewer LLM calls | 🪟 UFO² |
| [Hybrid Detection](ufo2/core_features/control_detection/hybrid_detection.md) | Visual + UIA control detection | 🪟 UFO² |
| [Knowledge Substrate](ufo2/core_features/knowledge_substrate/overview.md) | RAG-enhanced learning | 🪟 UFO² |
| [Constellation Agent](galaxy/constellation_agent/overview.md) | Task planning and decomposition | 🌌 Galaxy |
| [Task Orchestrator](galaxy/constellation_orchestrator/overview.md) | Execution coordination | 🌌 Galaxy |

### 🛠️ Development & Extension

Customize and extend UFO³:

| Topic | Description |
|-------|-------------|
| [Project Structure](project_directory_structure.md) | Understand the codebase layout |
| [Creating Custom Device Agents](tutorials/creating_device_agent/overview.md) | Build device agents for new platforms (mobile, web, IoT, etc.) |
| [Creating App Agents](tutorials/creating_app_agent/overview.md) | Build custom application agents |
| [Contributing Guide](about/CONTRIBUTING.md) | How to contribute to UFO³ |

### ❓ Support & Troubleshooting

Get help when you need it:

| Resource | What You'll Find |
|----------|------------------|
| [FAQ](faq.md) | Common questions and answers |
| [Getting Started FAQ](getting_started/faq.md) | Setup and installation questions |
| [GitHub Discussions](https://github.com/microsoft/UFO/discussions) | Community Q&A |
| [GitHub Issues](https://github.com/microsoft/UFO/issues) | Bug reports and feature requests |

---

## 📊 Feature Matrix

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

---

## 🎯 Use Cases & Examples

Explore what you can build with UFO³:

### 🌌 Galaxy Use Cases (Cross-Device)

Perfect for complex, multi-device workflows:

- **Cross-Platform Data Pipelines**: Extract from Windows Excel → Process on Linux → Visualize on Mac
- **Distributed Testing**: Run tests on Windows → Deploy to Linux → Update mobile app
- **Multi-Device Monitoring**: Collect logs from multiple devices → Aggregate centrally
- **Complex Automation**: Orchestrate workflows across heterogeneous platforms

### 🪟 UFO² Use Cases (Windows)

Perfect for Windows automation and rapid task execution:

- **Office Automation**: Excel/Word/PowerPoint report generation and data processing
- **Web Automation**: Browser-based research, form filling, data extraction
- **File Management**: Organize, rename, convert files based on rules
- **System Tasks**: Windows configuration, software installation, backups

---

## 🌐 Community & Resources

### 📺 Media & Videos

Check out our official deep dive of UFO on [YouTube](https://www.youtube.com/watch?v=QT_OhygMVXU).

### Media Coverage:
- [微软正式开源UFO²，Windows桌面迈入「AgentOS 时代」](https://www.jiqizhixin.com/articles/2025-05-06-13)
- [Microsoft's UFO: Smarter Windows Experience](https://the-decoder.com/microsofts-ufo-abducts-traditional-user-interfaces-for-a-smarter-windows-experience/)
- [下一代Windows系统曝光：基于GPT-4V](https://baijiahao.baidu.com/s?id=1790938358152188625)

### 💬 Get Help & Connect
- **📖 Documentation**: You're here! Browse the navigation above
- **💬 Discussions**: [GitHub Discussions](https://github.com/microsoft/UFO/discussions)
- **🐛 Issues**: [GitHub Issues](https://github.com/microsoft/UFO/issues)
- **📧 Email**: [ufo-agent@microsoft.com](mailto:ufo-agent@microsoft.com)

### 🎨 Related Projects
- **[TaskWeaver](https://github.com/microsoft/TaskWeaver)** – Code-first LLM agent framework
- **[Windows Agent Arena](https://github.com/nice-mee/WindowsAgentArena)** – Evaluation benchmark
- **[GUI Agents Survey](https://vyokky.github.io/LLM-Brained-GUI-Agents-Survey/)** – Latest research

---

## 📚 Research & Citation

UFO³ is built on cutting-edge research in multi-agent systems and GUI automation.

### Papers

If you use UFO³ in your research, please cite:

**UFO³ Galaxy Framework (2025)**
```bibtex
@article{zhang2025ufo3,
  title   = {{UFO³: Weaving the Digital Agent Galaxy}},
  author  = {Zhang, Chaoyun and [Authors TBD]},
  journal = {arXiv preprint arXiv:[TBD]},
  year    = {2025}
}
```

**UFO² Desktop AgentOS (2025)**
```bibtex
@article{zhang2025ufo2,
  title   = {{UFO2: The Desktop AgentOS}},
  author  = {Zhang, Chaoyun and Huang, He and Ni, Chiming and Mu, Jian and Qin, Si and He, Shilin and Wang, Lu and Yang, Fangkai and Zhao, Pu and Du, Chao and Li, Liqun and Kang, Yu and Jiang, Zhao and Zheng, Suzhen and Wang, Rujia and Qian, Jiaxu and Ma, Minghua and Lou, Jian-Guang and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei},
  journal = {arXiv preprint arXiv:2504.14603},
  year    = {2025}
}
```

**Original UFO (2024)**
```bibtex
@article{zhang2024ufo,
  title   = {{UFO: A UI-Focused Agent for Windows OS Interaction}},
  author  = {Zhang, Chaoyun and Li, Liqun and He, Shilin and Zhang, Xu and Qiao, Bo and Qin, Si and Ma, Minghua and Kang, Yu and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei and Zhang, Qi},
  journal = {arXiv preprint arXiv:2402.07939},
  year    = {2024}
}
```

**📖 [Read the Papers →](https://arxiv.org/abs/2504.14603)**

---


## 🗺️ Roadmap & Future

### UFO² Desktop AgentOS (Stable/LTS)
- ✅ Long-term support and maintenance  
- ✅ Windows device agent integration
- 🔜 Enhanced device capabilities
- 🔜 Picture-in-Picture mode

### UFO³ Galaxy (Active Development)
- ✅ Constellation Framework
- ✅ Multi-device coordination
- 🔄 Mobile, Web, IoT agents
- 🔄 Interactive visualization
- 🔜 Advanced fault tolerance

**Legend:** ✅ Done | 🔄 In Progress | 🔜 Planned

---

## ⚖️ License & Legal

- **License**: [MIT License](https://github.com/microsoft/UFO/blob/main/LICENSE)
- **Disclaimer**: [Read our disclaimer](https://github.com/microsoft/UFO/blob/main/DISCLAIMER.md)
- **Trademarks**: [Microsoft Trademark Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks)
- **Contributing**: [Contribution Guidelines](about/CONTRIBUTING.md)

---

<div align="center">

## 🚀 Ready to Start?

Choose your framework and begin your automation journey:

<table>
<tr>
<td align="center" width="50%">

### 🌌 Start with Galaxy
**For multi-device orchestration**

[![Galaxy Quick Start](https://img.shields.io/badge/Quick_Start-Galaxy-blue?style=for-the-badge)](getting_started/quick_start_galaxy.md)

</td>
<td align="center" width="50%">

### 🪟 Start with UFO²
**For Windows automation**

[![UFO² Quick Start](https://img.shields.io/badge/Quick_Start-UFO²-green?style=for-the-badge)](getting_started/quick_start_ufo2.md)

</td>
</tr>
</table>

### 📖 Explore the Documentation

[Core Concepts](galaxy/overview.md) | [Configuration](configuration/system/agents_config.md) | [FAQ](faq.md) | [GitHub](https://github.com/microsoft/UFO)


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