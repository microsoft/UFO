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
| **🪟 UFO²** <br> <sub>⚡ STABLE & LTS</sub> | Windows automation<br>Quick tasks<br>Learning basics | Deep Windows integration<br>Hybrid GUI + API<br>Stable & reliable | [Quick Start →](getting_started/quick_start_ufo2.md) |

### 🤔 Decision Guide

| Question | Galaxy | UFO² |
|----------|:------:|:----:|
| Need cross-device collaboration? | ✅ | ❌ |
| Complex multi-step workflows? | ✅ | ⚠️ Limited |
| Windows-only automation? | ✅ | ✅ Optimized |
| Quick setup & learning? | ⚠️ Moderate | ✅ Easy |
| Stable & reliable? | 🚧 Active Dev | ✅ LTS |

---

## 🌟 What's New in UFO³?

**UFO³ is a scalable, universal cross-device agent framework** that enables you to develop new device agents for different platforms and applications. Through the **Agent Interaction Protocol (AIP)**, custom device agents can seamlessly integrate into UFO³ Galaxy for coordinated multi-device orchestration.

### Evolution Timeline

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#E8F4F8','primaryTextColor':'#1A1A1A','primaryBorderColor':'#7CB9E8','lineColor':'#A8D5E2','secondaryColor':'#B8E6F0','tertiaryColor':'#D4F1F4','fontSize':'16px','fontFamily':'Segoe UI, Arial, sans-serif'}}}%%
graph LR
    A["<b>🎈 UFO</b><br/><span style='font-size:14px'>February 2024</span><br/><span style='font-size:13px; color:#666'><i>GUI Agent for Windows</i></span>"] 
    B["<b>🖥️ UFO²</b><br/><span style='font-size:14px'>April 2025</span><br/><span style='font-size:13px; color:#666'><i>Desktop AgentOS</i></span>"]
    C["<b>🌌 UFO³ Galaxy</b><br/><span style='font-size:14px'>November 2025</span><br/><span style='font-size:13px; color:#666'><i>Multi-Device Orchestration</i></span>"]
    
    A -->|Evolve| B
    B -->|Scale| C
    
    style A fill:#E8F4F8,stroke:#7CB9E8,stroke-width:2.5px,color:#1A1A1A,rx:15,ry:15
    style B fill:#C5E8F5,stroke:#5BA8D0,stroke-width:2.5px,color:#1A1A1A,rx:15,ry:15
    style C fill:#A4DBF0,stroke:#3D96BE,stroke-width:2.5px,color:#1A1A1A,rx:15,ry:15
```

### 🚀 UFO³ = **Galaxy** (Multi-Device Orchestration) + **UFO²** (Device Agent)

UFO³ introduces **Galaxy**, a revolutionary multi-device orchestration framework that coordinates intelligent agents across heterogeneous platforms. Built on five tightly integrated design principles:

1. **🌟 Declarative Decomposition into Dynamic DAG** - Requests decomposed into structured DAG with TaskStars and dependencies for automated scheduling and runtime rewriting

2. **🔄 Continuous Result-Driven Graph Evolution** - Living constellation that adapts to execution feedback through controlled rewrites and dynamic adjustments

3. **⚡ Heterogeneous, Asynchronous & Safe Orchestration** - Capability-based device matching with async execution, safe locking, and formally verified correctness

4. **🔌 Unified Agent Interaction Protocol (AIP)** - WebSocket-based secure coordination layer with fault tolerance and automatic reconnection

5. **🛠️ Template-Driven MCP-Empowered Device Agents** - Lightweight toolkit for rapid agent development with MCP integration for tool augmentation

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
| **Cross-Device Collaboration** | ❌ Not Supported | ✅ Core Feature |
| **Setup Difficulty** | ✅ Easy | ⚠️ Moderate |
| **Status** | ✅ LTS (Long-Term Support) | ⚡ Active Development |

### 🎓 Migration Path

**For UFO² Users:**
1. ✅ **Keep using UFO²** – Fully supported, actively maintained
2. 🔄 **Gradual adoption** – Galaxy can use UFO² as Windows device agent
3. 📈 **Scale up** – Move to Galaxy when you need multi-device capabilities
4. 📚 **Learning resources** – [Migration Guide](./getting_started/migration_ufo2_to_galaxy.md)

---

## ✨ Capabilities at a Glance

### 🌌 Galaxy Framework – What's Different?

#### 🌟 Constellation Planning

```
User Request
     ↓
ConstellationAgent
     ↓
  [Task DAG]
   /   |   \
Task1 Task2 Task3
(Win) (Linux)(Mac)
```

**Benefits:**
- Cross-device dependency tracking
- Parallel execution optimization
- Cross-device dataflow management

#### 🎯 Device Assignment

```
Selection Criteria
  • Platform
  • Resource
  • Task requirements
  • Performance history
        ↓
  Auto-Assignment
        ↓
  Optimal Devices
```

**Smart Matching:**
- Capability-based selection
- Real-time resource monitoring
- Dynamic reallocation

#### 📊 Orchestration

```
Task1 → Running  ✅
Task2 → Pending  ⏸️
Task3 → Running  🔄
        ↓
   Completion
        ↓
   Final Report
```

**Orchestration:**
- Real-time status updates
- Automatic error recovery
- Progress tracking with feedback

---

### 🪟 UFO² Desktop AgentOS – Core Strengths

UFO² serves dual roles: **standalone Windows automation** and **Galaxy device agent** for Windows platforms.

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Deep OS Integration** | Windows UIA, Win32, WinCOM native control | [Learn More](ufo2/overview.md) |
| **Hybrid Actions** | GUI clicks + API calls for optimal performance | [Learn More](ufo2/core_features/hybrid_actions.md) |
| **Speculative Multi-Action** | Batch predictions → **51% fewer LLM calls** | [Learn More](ufo2/core_features/multi_action.md) |
| **Visual + UIA Detection** | Hybrid control detection for robustness | [Learn More](ufo2/core_features/control_detection/hybrid_detection.md) |
| **Knowledge Substrate** | RAG with docs, demos, execution traces | [Learn More](ufo2/core_features/knowledge_substrate/overview.md) |
| **Device Agent Role** | Can serve as Windows executor in Galaxy orchestration | [Learn More](galaxy/overview.md) |

**As Galaxy Device Agent:**
- Receives tasks from ConstellationAgent through Galaxy orchestration layer
- Executes Windows-specific operations using proven UFO² capabilities
- Reports status and results back to TaskOrchestrator
- Seamlessly participates in cross-device workflows

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
| [Linux Agent Quick Start](getting_started/quick_start_linux.md) | Automate Linux systems | 🐧 Linux |
| [Mobile Agent Quick Start](getting_started/quick_start_mobile.md) | Automate Android devices via ADB | 📱 Mobile |
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
| **Stability** | ⭐⭐⭐⭐⭐ Stable | ⭐⭐⭐ Active dev | UFO² |
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


## 🚀 Ready to Start?

Choose your framework and begin your automation journey:


### 🌌 Start with Galaxy
**For multi-device orchestration**

[![Galaxy Quick Start](https://img.shields.io/badge/Quick_Start-Galaxy-blue?style=for-the-badge)](getting_started/quick_start_galaxy.md)


### 🪟 Start with UFO²
**For Windows automation**

[![UFO² Quick Start](https://img.shields.io/badge/Quick_Start-UFO²-green?style=for-the-badge)](getting_started/quick_start_ufo2.md)


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