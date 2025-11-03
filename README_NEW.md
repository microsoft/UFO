<!-- markdownlint-disable MD033 MD041 -->
<!-- <h1 align="center">
  <img src="assets/logo3.png" alt="UFO logo" width="50">
  <br>
  <b>UFO³</b>
  <br>
  <em>Weaving the Digital Agent Galaxy</em>
</h1> -->


<h1 align="center">
  <b>UFO³</b> <img src="assets/logo3.png" alt="UFO logo" width="80"> :Weaving the Digital Agent Galaxy
</h1>
<p align="center">
  <em>Turn natural‑language requests into automatic, reliable, multi‑application workflows on Windows, beyond UI-Focused.</em>
</p>


<p align="center">
  <strong>From Single Windows Agent to Multi-Device Orchestration</strong>
  <br>
  Turn complex tasks into intelligent workflows across devices, applications, and platforms.
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

### 🌌 **Galaxy** – Multi-Device Orchestration
<sub>**✨ NEW & RECOMMENDED**</sub>

**Perfect for:**
- 🔗 Cross-device collaboration
- 📊 Complex workflow automation  
- 🎯 DAG-based task orchestration
- 🤖 Multi-agent coordination

**Key Features:**
- Intelligent task decomposition
- Dynamic device assignment
- Real-time workflow adaptation
- Event-driven monitoring

**Get Started:**
```bash
python -m ufo.galaxy \
  --request "Your complex task"
```

**📖 [Galaxy Documentation →](./galaxy/README.md)**

</td>
<td width="50%" valign="top">

### 🪟 **UFO² Desktop AgentOS** – Windows Single Agent
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

**Get Started:**
```bash
python -m ufo \
  --task <your_task_name>
```

**📖 [UFO² Documentation →](./README.md)**

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

<h3 align="center">
  <img src="./assets/poster.png" width="70%"/> 
</h3>

### Evolution Timeline

```
2024.02  →  2025.04  →  2025.11
   ↓           ↓          ↓
  UFO       UFO²      UFO³ Galaxy
Single    Desktop    Multi-Device
Agent     AgentOS    Orchestration
```

### 🚀 UFO³ = **Galaxy** (Multi-Device) + **UFO²** (Desktop AgentOS)

| Aspect | UFO² | UFO³ Galaxy |
|--------|------|-------------|
| **Architecture** | Single Windows Agent | Multi-Device Orchestration |
| **Task Model** | Sequential ReAct Loop | DAG-based Workflows |
| **Scope** | One application at a time | Cross-device, cross-platform |
| **Coordination** | HostAgent + AppAgents | ConstellationAgent + Orchestrator |
| **Device Support** | Windows Desktop | Windows, Linux, Mobile, Web |
| **Complexity** | Simple to Moderate | Simple to Very Complex |
| **Learning Curve** | Low | Moderate |
| **Status** | ✅ LTS (Long-Term Support) | ⚡ Active Development |

### 🎓 Migration Path

**For UFO² Users:**
1. ✅ **Keep using UFO²** – Fully supported, actively maintained
2. 🔄 **Gradual adoption** – Galaxy can call UFO² agents on Windows devices
3. 📈 **Scale up** – Move to Galaxy when you need multi-device capabilities
4. 📚 **Learning resources** – [Migration Guide](./docs/migration_guide.md)

---

## ✨ Capabilities at a Glance

### 🌌 Galaxy Framework – What's Different?

<table>
<tr>
<td width="33%" valign="top">

#### 🎯 Intelligent Task Decomposition
```
"Analyze data on Windows,
 visualize on Mac,
 deploy to Linux server"
        ↓
   [Task DAG]
  /     |     \
Data  Viz    Deploy
(Win) (Mac) (Linux)
```

</td>
<td width="33%" valign="top">

#### 🔗 Cross-Device Coordination
```python
# Automatic device selection
constellation = TaskConstellation(
  name="Multi-Platform Pipeline"
)
# Tasks auto-assigned to
# best-fit devices
```

</td>
<td width="33%" valign="top">

#### 📊 Real-Time Monitoring
```
┌─ Task Graph ──────┐
│ ✅ Data Collection │
│ 🔄 Processing     │
│ ⏸️  Visualization  │
│ ⏳ Deployment     │
└───────────────────┘
```

</td>
</tr>
</table>

### 🪟 UFO² Desktop AgentOS – Core Strengths

<div align="center">

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Deep OS Integration** | Windows UIA, Win32, WinCOM native control | [Learn More](https://microsoft.github.io/UFO) |
| **Hybrid Actions** | GUI clicks + API calls for optimal performance | [Learn More](https://microsoft.github.io/UFO/automator/overview) |
| **Speculative Multi-Action** | Batch predictions → **51% fewer LLM calls** | [Learn More](https://microsoft.github.io/UFO/advanced_usage/multi_action) |
| **Visual + UIA Detection** | Hybrid control detection for robustness | [Learn More](https://microsoft.github.io/UFO/advanced_usage/control_detection/hybrid_detection) |
| **Knowledge Substrate** | RAG with docs, demos, execution traces | [Learn More](https://microsoft.github.io/UFO/advanced_usage/reinforce_appagent/overview/) |

</div>

---

## 🚀 Quick Start Guide

### 📦 Installation (Common for Both)

```powershell
# Clone the repository
git clone https://github.com/microsoft/UFO.git
cd UFO

# Create conda environment (recommended)
conda create -n ufo3 python=3.10
conda activate ufo3

# Install dependencies
pip install -r requirements.txt
```

### ⚙️ Configuration

Both Galaxy and UFO² require LLM configuration:

```powershell
# Copy configuration template
copy ufo\config\config.yaml.template ufo\config\config.yaml

# Edit configuration
notepad ufo\config\config.yaml
```

**Quick Config (OpenAI):**
```yaml
VISUAL_MODE: True
API_TYPE: "openai"
API_BASE: "https://api.openai.com/v1/chat/completions"
API_KEY: "sk-your-key-here"
API_MODEL: "gpt-4o"
```

**Quick Config (Azure OpenAI):**
```yaml
VISUAL_MODE: True
API_TYPE: "aoai"
API_BASE: "https://YOUR-RESOURCE.openai.azure.com"
API_KEY: "your-azure-key"
API_MODEL: "gpt-4o"
API_DEPLOYMENT_ID: "your-deployment-id"
```

> 💡 **Tip:** See [Model Configuration Guide](https://microsoft.github.io/UFO/supported_models/overview/) for Qwen, Gemini, and more.

---

### 🌌 Option 1: Start with Galaxy (Multi-Device)

#### Interactive Mode (Recommended for First-Time Users)
```powershell
python -m ufo.galaxy --interactive
```

#### Single Request Mode
```powershell
python -m ufo.galaxy --request "Create a data analysis pipeline with visualization"
```

#### Example Complex Workflow
```powershell
python -m ufo.galaxy --request "
  1. Collect sales data from Excel on Windows
  2. Process data using Python on Linux server
  3. Create visualizations on Mac
  4. Generate report and email to team
"
```

#### Programmatic Usage
```python
from galaxy import GalaxyClient

# Initialize client
client = GalaxyClient(
    session_name="my_workflow",
    use_mock_agent=False,
    max_rounds=10
)

# Execute request
result = await client.execute_request(
    "Your complex multi-device task"
)
```

**📖 Full Galaxy Guide:** [galaxy/README.md](./galaxy/README.md)

---

### 🪟 Option 2: Start with UFO² (Windows Single Agent)

#### Command Line
```powershell
# Interactive mode
python -m ufo --task <your_task_name>

# Direct request
python -m ufo --task <task_name> -r "Open Excel and create a sales chart"
```

#### Example Tasks
```powershell
# Office automation
python -m ufo --task "excel_report" -r "Create a pivot table from sales data"

# Multi-application
python -m ufo --task "research" -r "Search in Edge, summarize in Word"

# System operation
python -m ufo --task "file_mgmt" -r "Organize downloads by file type"
```

**📖 Full UFO² Guide:** [README.md](./README.md)

---

## 📚 Documentation Structure

<table>
<tr>
<td width="50%" valign="top">

### 🌌 Galaxy Documentation

- **[Galaxy Overview](./galaxy/README.md)** – Architecture & concepts
- **[Quick Start](./galaxy/README.md#-quick-start)** – Get running in 5 minutes
- **[Core Components](./galaxy/README.md#-core-components)** – ConstellationAgent, TaskOrchestrator
- **[Workflow Guide](./galaxy/README.md#-workflow-process)** – DAG creation & execution
- **[Device Management](./galaxy/client/README.md)** – Multi-device coordination
- **[Visualization](./galaxy/visualization/README.md)** – Monitoring & debugging
- **[API Reference](./docs/galaxy_api.md)** – Programmatic usage

**📖 Detailed Modules:**
- [Agents](./galaxy/agents/README.md)
- [Constellation](./galaxy/constellation/README.md)
- [Session Management](./galaxy/session/README.md)
- [Events & Observers](./galaxy/core/README.md)

</td>
<td width="50%" valign="top">

### 🪟 UFO² Documentation

- **[UFO² Overview](./README.md)** – Desktop AgentOS architecture
- **[Installation](./README.md#️-step-1-installation)** – Setup & dependencies
- **[Configuration](./README.md#️-step-2-configure-the-llms)** – LLM & RAG setup
- **[Usage Guide](./README.md#-step-4-start-ufo)** – Running UFO²
- **[Advanced Features](https://microsoft.github.io/UFO/advanced_usage/overview/)** – Multi-action, RAG, etc.
- **[Automator Guide](https://microsoft.github.io/UFO/automator/overview)** – Hybrid GUI + API
- **[Benchmarks](./README.md#-evaluation)** – WAA & OSWorld results

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
   └─ [docs/migration_guide.md](./docs/migration_guide.md)
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

```
User Request
    ↓
HostAgent (FSM Coordinator)
    ↓
┌─────────┬─────────┬─────────┐
│AppAgent│AppAgent │AppAgent │ (per app)
│   1     │    2    │    3    │
└─────────┴─────────┴─────────┘
    ↓         ↓         ↓
┌─────────┬─────────┬─────────┐
│ Excel   │  Word   │  Edge   │ (Windows apps)
└─────────┴─────────┴─────────┘
```

**Key Characteristics:**
- Sequential task execution
- Single-device focus (Windows)
- ReAct loop per application
- Deep Windows integration

---

### UFO³ Galaxy – Multi-Device Orchestration

```
User Request
    ↓
ConstellationAgent (DAG Creator)
    ↓
Task DAG (Constellation)
  /    |    \
Task  Task  Task
  1     2     3
  ↓     ↓     ↓
┌────┬────┬────┐
│Win │Mac │Linux│ (Auto device assignment)
└────┴────┴────┘
  ↓     ↓     ↓
TaskOrchestrator (Execution Coordinator)
  ↓
Event System (Real-time Monitoring)
```

**Key Characteristics:**
- DAG-based parallel execution
- Multi-device coordination
- Dynamic task assignment
- Event-driven architecture
- Real-time adaptation

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
- 🔗 Tasks spanning multiple devices
- 📊 Complex data pipelines
- 🤖 Multi-step automation workflows
- 🌍 Cross-platform operations
- 📈 Scalable task orchestration
- 🔄 Dynamic workflow adaptation
- 🎯 Advanced agent coordination

**Example Scenarios:**
```
✓ "Collect data on Windows, process on Linux, visualize on Mac"
✓ "Multi-device testing workflow across platforms"
✓ "Distributed data processing pipeline"
✓ "Cross-platform CI/CD automation"
✓ "Multi-device IoT orchestration"
```

---

### Hybrid Approach (Best of Both Worlds)

```python
# Use Galaxy for orchestration
# Use UFO² agents on Windows devices

from galaxy import TaskConstellation
from ufo import UFOAgent

constellation = TaskConstellation("Hybrid Workflow")

# Windows task → UFO² agent
windows_task = TaskStar(
    task_id="excel_processing",
    device_type=DeviceType.WINDOWS,
    agent_type="UFO2"  # Use stable UFO² agent
)

# Linux task → Galaxy agent
linux_task = TaskStar(
    task_id="data_processing",
    device_type=DeviceType.LINUX,
    agent_type="Galaxy"
)

constellation.add_tasks([windows_task, linux_task])
```

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

See [Migration Guide](./docs/migration_guide.md) for details.

</details>

<details>
<summary><strong>🎯 Can Galaxy do everything UFO² does?</strong></summary>

**Functionally: Yes.** Galaxy includes UFO² capabilities for Windows tasks.

**Practically: It depends.**
- For **simple Windows tasks**: UFO² is easier and more streamlined
- For **complex workflows**: Galaxy provides more power and flexibility
- For **production**: UFO² offers proven stability

**Recommendation:** Use the right tool for the job.

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
- See [Evaluation Section](./README.md#-evaluation)

### UFO³ Galaxy

**Tested on:**
- 🔬 Internal multi-device benchmarks
- 🧪 Complex workflow scenarios
- 📊 Performance metrics available in `./galaxy/benchmarks/`

**Status:** Benchmark suite under active development

---

## 🗺️ Roadmap

### UFO² Desktop AgentOS (Stable/LTS)
- ✅ Long-term support and maintenance
- ✅ Bug fixes and security updates
- ✅ Performance optimization
- 🔄 Integration with Galaxy as Windows device executor
- 🔜 Picture-in-Picture desktop mode

### UFO³ Galaxy (Active Development)
- ✅ Core DAG orchestration **[DONE]**
- ✅ Multi-device coordination **[DONE]**
- ✅ Event-driven architecture **[DONE]**
- 🔄 Advanced device types **[IN PROGRESS]**
- 🔄 Enhanced visualization **[IN PROGRESS]**
- 🔜 AgentOS-as-a-Service
- 🔜 MCP integration
- 🔜 Agent-to-Agent communication
- 🔜 Auto-debugging toolkit
- 🔜 Comprehensive benchmarks

**Legend:** ✅ Done | 🔄 In Progress | 🔜 Planned

---

## 📢 Latest Updates

### 2025-11 – UFO³ Galaxy Framework
- 🌌 **NEW:** Galaxy multi-device orchestration framework
- 🎯 DAG-based task workflows
- 🔗 Cross-device coordination
- 📊 Real-time visualization and monitoring
- 🤖 ConstellationAgent for intelligent task decomposition

### 2025-04 – UFO² v2.0.0
- 📅 UFO² Desktop AgentOS released
- 🏗️ Enhanced architecture with AgentOS concept
- 📄 [Technical Report](https://arxiv.org/pdf/2504.14603) published
- ✅ Entered Long-Term Support (LTS) status

### 2024-02 – Original UFO
- 🎈 First UFO release
- 📄 [Original Paper](https://arxiv.org/abs/2402.07939)
- 🌍 Wide media coverage and adoption

---

## 📚 Citation

### UFO³ Galaxy Framework (2025)
```bibtex
@article{zhang2025ufo3galaxy,
  title   = {{UFO3: Weaving the Digital Agent Galaxy}},
  author  = {Zhang, Chaoyun and [Authors TBD]},
  journal = {arXiv preprint arXiv:[TBD]},
  year    = {2025}
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

## 🌐 Media & Community

**Media Coverage:**
- [微软正式开源UFO²，Windows桌面迈入「AgentOS 时代」](https://www.jiqizhixin.com/articles/2025-05-06-13)
- [Microsoft's UFO: Smarter Windows Experience](https://the-decoder.com/microsofts-ufo-abducts-traditional-user-interfaces-for-a-smarter-windows-experience/)
- [下一代Windows系统曝光](https://baijiahao.baidu.com/s?id=1790938358152188625)
- [More coverage...](./README.md#-media-coverage)

**Community:**
- 💬 [GitHub Discussions](https://github.com/microsoft/UFO/discussions)
- 🐛 [Issue Tracker](https://github.com/microsoft/UFO/issues)
- 📧 Email: [ufo-agent@microsoft.com](mailto:ufo-agent@microsoft.com)
- 📺 [YouTube Channel](https://www.youtube.com/watch?v=QT_OhygMVXU)

---

## 🎨 Related Projects

- **[TaskWeaver](https://github.com/microsoft/TaskWeaver)** – Code-first LLM agent for data analytics
- **[LLM-Brained GUI Agents Survey](https://github.com/vyokky/LLM-Brained-GUI-Agents-Survey)** – Comprehensive survey of GUI agents
- **[Interactive Survey Site](https://vyokky.github.io/LLM-Brained-GUI-Agents-Survey/)** – Explore GUI agent research

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

[![Start UFO²](https://img.shields.io/badge/Start-UFO²-green?style=for-the-badge)](./README.md)

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
