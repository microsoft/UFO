# UFO² — Windows AgentOS

[![arxiv](https://img.shields.io/badge/Paper-arXiv:2504.14603-b31b1b.svg)](https://arxiv.org/abs/2504.14603)&ensp;
![Python Version](https://img.shields.io/badge/Python-3776AB?&logo=python&logoColor=white-blue&label=3.10%20%7C%203.11)&ensp;
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)&ensp;
[![github](https://img.shields.io/github/stars/microsoft/UFO)](https://github.com/microsoft/UFO)&ensp;
[![YouTube](https://img.shields.io/badge/YouTube-white?logo=youtube&logoColor=%23FF0000)](https://www.youtube.com/watch?v=QT_OhygMVXU)&ensp;


**UFO²** is a Windows AgentOS that reimagines desktop automation as a first-class operating system abstraction. Unlike traditional Computer-Using Agents (CUAs) that rely on screenshots and simulated inputs, UFO² deeply integrates with Windows OS through UI Automation APIs, application-specific introspection, and hybrid GUI–API execution—enabling robust, efficient, and non-disruptive automation across 20+ real-world applications.

---

## What is UFO²?

UFO² addresses fundamental limitations of existing desktop automation solutions:

**Traditional RPA (UiPath, Power Automate):**  
❌ Fragile scripts that break with UI changes  
❌ Requires extensive manual maintenance  
❌ Limited adaptability to dynamic environments

**Current CUAs (Claude, Operator):**  
❌ Visual-only inputs with high cognitive overhead  
❌ Miss native OS APIs and application internals  
❌ Lock users out during automation (poor UX)

**UFO² AgentOS:**  
✅ **Deep OS Integration** — Windows UIA, Win32, WinCOM APIs  
✅ **Hybrid GUI–API Actions** — Native APIs + fallback GUI automation  
✅ **Continuous Knowledge Learning** — RAG-enhanced from docs & execution history  
✅ **Picture-in-Picture Desktop** — Parallel automation without user disruption  
✅ **10%+ better success rate** than state-of-the-art CUAs

<figure markdown>
  ![AgentOS vs Traditional CUA](../img/comparison.png)
  <figcaption><b>Figure 1:</b> Comparison between (a) traditional CUAs that rely on screenshots and simulated inputs, and (b) UFO² AgentOS that deeply integrates with OS APIs, application internals, and hybrid GUI–API execution.</figcaption>
</figure>

---

## Core Architecture

UFO² implements a **hierarchical multi-agent system** optimized for Windows desktop automation:

<figure markdown>
  ![UFO² System Architecture](../img/framework2.png)
  <figcaption><b>Figure 2:</b> UFO² system architecture featuring the two-tier agent hierarchy (HostAgent + AppAgents), hybrid control detection pipeline, continuous knowledge substrate integration, and unified GUI–API action layer coordinated through MCP servers.</figcaption>
</figure>


### Two-Tier Agent Hierarchy

| Agent Type | Role | Key Capabilities |
|------------|------|------------------|
| **HostAgent** | Desktop Orchestrator | Task decomposition • Application selection • Cross-app coordination • AppAgent lifecycle management |
| **AppAgent** | Application Executor | UI element interaction • Hybrid GUI–API execution • Application-specific automation • Result reporting |

**Design Philosophy:**  
- **HostAgent** handles **WHAT** (which application) and **WHEN** (task sequencing)  
- **AppAgent** handles **HOW** (UI/API interaction) and **WHERE** (control targeting)  
- **Blackboard** facilitates inter-agent communication without tight coupling  
- **State Machines** ensure deterministic execution flow and error recovery

!!!info "Learn More"
    - [**HostAgent Documentation**](host_agent/overview.md) — 7-state FSM, desktop orchestration, AppAgent lifecycle  
    - [**AppAgent Documentation**](app_agent/overview.md) — 6-state FSM, UI automation, hybrid action execution  
    - [**Agent Architecture**](../infrastructure/agents/overview.md) — Three-layer design principles

---

## Key Innovations

### 1. Deep OS Integration 🔧

UFO² embeds directly into Windows OS infrastructure:

- **UI Automation (UIA):** Introspects accessibility trees for standard controls  
- **Win32 APIs:** Low-level window management and process control  
- **WinCOM:** Interacts with Office applications (Excel, Word, Outlook)  
- **Hybrid Detection:** Fuses UIA metadata + visual grounding for non-standard UI elements

!!!tip "Hybrid Control Detection"
    Combines Windows UIA APIs with vision models ([OmniParser](https://arxiv.org/abs/2408.00203)) to detect both standard and custom UI controls—bridging structured accessibility trees and pixel-level perception.
    
    📖 [Control Detection Guide](core_features/control_detection/overview.md)

### 2. Unified GUI–API Action Layer ⚡

Traditional CUAs simulate mouse/keyboard only. UFO² chooses the best execution method:

**GUI Actions** (fallback):  
`click`, `type`, `select`, `scroll` → Reliable for any application

**Native APIs** (preferred):  
- Excel: `xlwings` for direct cell/chart manipulation  
- Outlook: `win32com` for email operations  
- PowerPoint: `python-pptx` for slide editing  
→ **51% fewer LLM calls** via speculative multi-action execution

**Model Context Protocol (MCP) Servers:**  
Extensible framework for adding application-specific APIs without modifying agent code.

!!!info "Learn More"
    📖 [Hybrid Actions Guide](core_features/hybrid_actions.md) • [MCP Integration](../mcp/overview.md)

### 3. Continuous Knowledge Substrate 📚

UFO² learns from three knowledge sources without model retraining:

| Source | Content | Integration Method |
|--------|---------|-------------------|
| **Help Documents** | Official app documentation, API references | Vectorized retrieval (RAG) |
| **Bing Search** | Real-time web knowledge for latest features | Dynamic query expansion |
| **Execution History** | Past successful/failed action sequences | Experience replay & pattern mining |

**Result:** Agents improve autonomously by retrieving relevant context at execution time.

!!!info "Knowledge Integration"
    📖 [Knowledge Substrate Overview](core_features/knowledge_substrate/overview.md)  
    📖 [Learning from Help Documents](core_features/knowledge_substrate/learning_from_help_document.md)  
    📖 [Experience Learning](core_features/knowledge_substrate/experience_learning.md)

### 4. Speculative Multi-Action Execution 🚀

Reduce LLM latency by predicting and validating action sequences:

**Traditional Approach:**  
1 LLM call → 1 action → observe → repeat → **High latency**

**UFO² Speculative Execution:**  
1 LLM call → predict N actions → validate with UI state → execute all → **51% fewer queries**

**Validation Mechanism:**  
Lightweight control-state checks ensure predicted actions remain valid before execution.

!!!example "Efficiency Gain"
    **Task:** "Fill form fields A1–A10 with sequential numbers"
    
    - **Traditional CUA:** 10 LLM calls (1 per field) → ~30 seconds  
    - **UFO² Speculative:** 1 LLM call predicts all 10 actions → ~8 seconds
    
    📖 [Multi-Action Execution Guide](core_features/multi_action.md)

### 5. Picture-in-Picture Desktop 🖼️

**Problem:** Existing CUAs lock users out during automation (poor UX).

**UFO² Solution:** Nested virtual desktop via Windows Remote Desktop loopback:

- **User Desktop:** Continue working normally  
- **Agent Desktop (PiP):** Automation runs in parallel sandboxed environment  
- **Zero Interference:** User and agent don't compete for mouse/keyboard

**Implementation:**  
Built on Windows native remote desktop infrastructure—secure, isolated, non-disruptive.

!!!success "User Experience"
    Users can continue email, browsing, or coding while UFO² automates Excel reports in the background PiP desktop.

---

## System Components

### Processing Pipeline

Both HostAgent and AppAgent execute a **4-phase processing cycle**:

| Phase | Purpose | HostAgent Strategy | AppAgent Strategy |
|-------|---------|-------------------|------------------|
| **1. Data Collection** | Gather environment state | Desktop screenshot, app list | App screenshot, UI tree, control annotations |
| **2. LLM Interaction** | Decide next action | Select application, plan subtask | Select control, plan action sequence |
| **3. Action Execution** | Execute commands | Launch app, create AppAgent | Execute GUI/API actions |
| **4. Memory Update** | Record execution | Save orchestration step | Save interaction step, update blackboard |

!!!info "Processing Details"
    📖 [Strategy Layer](../infrastructure/agents/design/processor.md) — Processing framework and dependency chain  
    📖 [State Layer](../infrastructure/agents/design/state.md) — FSM design principles

### Command System

Commands are dispatched through **MCP (Model Context Protocol)** servers:

**HostAgent Commands:**

- **Desktop Capture:** `capture_desktop_screenshot`  
- **Window Management:** `get_desktop_app_info`, `get_app_window`  
- **Process Control:** `launch_application`, `close_application`

**AppAgent Commands:**

- **Screenshot:** `capture_screenshot`, `annotate_screenshot`  
- **UI Inspection:** `get_control_info`, `get_ui_tree`  
- **UI Interaction:** `click`, `set_edit_text`, `wheel_mouse_input`  
- **Control Selection:** `select_control_by_index`, `select_control_by_name`

!!!info "Command Architecture"
    📖 [Command Layer](../infrastructure/agents/design/command.md) — MCP integration and command dispatch  
    📖 [MCP Servers](../mcp/overview.md) — Server architecture and custom server creation

---


## Configuration

UFO² integrates with a centralized YAML-based configuration system:

```yaml
# config/ufo/host_agent_config.yaml
host_agent:
  visual_mode: true                  # Enable screenshot-based reasoning
  max_subtasks: 10                   # Maximum subtasks per session
  llm_config:
    model: "gpt-4o"
    temperature: 0.0

# config/ufo/app_agent_config.yaml
app_agent:
  visual_mode: true                  # Enable UI screenshot analysis
  control_backend: "uia"             # UI Automation (uia) or Win32 (win32)
  max_steps: 20                      # Maximum steps per subtask
```

!!!tip "Complete Configuration Guide"
    For detailed configuration options, model setup, and advanced customization:
    
    📖 **[Configuration & Setup](../configuration/system/overview.md)** — Complete system configuration reference  
    📖 **[Model Setup](../configuration/models/overview.md)** — LLM provider configuration (OpenAI, Azure, Gemini, Claude, etc.)  
    📖 **[MCP Configuration](../configuration/system/mcp_reference.md)** — MCP server and extension configuration

---

## Quick Start

### Basic Usage

UFO² is designed to be run from the command line:

**Interactive Mode:**
```powershell
# Start UFO² in interactive mode
python -m ufo --task <your_task_name>
```

**Example:**
```powershell
python -m ufo --task excel_demo
```

This will prompt you to enter your request interactively:
```
Welcome to use UFO🛸, A UI-focused Agent for Windows OS Interaction.
Please enter your request to be completed🛸: Create a chart from Sheet1 data in Excel
```

**Direct Request Mode:**
```powershell
# Execute with a specific request directly
python -m ufo --task <your_task_name> -r "<your_request>"
```

**Example:**
```powershell
python -m ufo --task excel_demo -r "Open Excel and create a chart from Sheet1 data"
```

!!!tip "Complete Setup Guide"
    For detailed installation, configuration, and advanced usage options, see the **[Quick Start Guide](../getting_started/quick_start_ufo2.md)**.

### What Happens Under the Hood

1. **Session** creates **HostAgent** with user request  
2. **HostAgent** captures desktop, selects "Microsoft Excel", launches app  
3. **HostAgent** creates **AppAgent** for Excel, delegates subtask  
4. **AppAgent** captures Excel UI, identifies chart insertion control  
5. **AppAgent** executes hybrid action (API if available, GUI fallback)  
6. **AppAgent** reports completion to **HostAgent**  
7. **HostAgent** verifies task, returns success to **Session**

!!!tip "Next Steps"
    📖 [Getting Started Guide](../getting_started/quick_start_ufo2.md)  
    📖 [Creating Your AppAgent](../tutorials/creating_app_agent/overview.md)

---

## Documentation Navigation

### Core Concepts

- [**HostAgent**](host_agent/overview.md) — Desktop orchestrator with 7-state FSM  
- [**AppAgent**](app_agent/overview.md) — Application executor with 6-state FSM  
- [**Agent Types**](../infrastructure/agents/agent_types.md) — Platform-specific implementations  
- [**Evaluation Agent**](evaluation/evaluation_agent.md) — Automated testing and benchmarking

### Advanced Features

- [**Hybrid Actions**](core_features/hybrid_actions.md) — GUI–API execution layer  
- [**Control Detection**](core_features/control_detection/overview.md) — UIA + visual grounding  
- [**Knowledge Substrate**](core_features/knowledge_substrate/overview.md) — RAG-enhanced learning  
- [**Multi-Action Execution**](core_features/multi_action.md) — Speculative action planning  
- [**Follower Mode**](advanced_usage/follower_mode.md) — Human-in-the-loop execution  
- [**Batch Mode**](advanced_usage/batch_mode.md) — Bulk task processing

### System Architecture

- [**Device Agent Overview**](../infrastructure/agents/overview.md) — Three-layer architecture  
- [**State Layer**](../infrastructure/agents/design/state.md) — FSM design principles  
- [**Strategy Layer**](../infrastructure/agents/design/processor.md) — Processing framework  
- [**Command Layer**](../infrastructure/agents/design/command.md) — MCP integration  

### Development

- [**Creating AppAgent**](../tutorials/creating_app_agent/overview.md) — Custom agent development  
- [**MCP Servers**](../mcp/overview.md) — Building custom MCP servers  
- [**Configuration**](../configuration/system/overview.md) — System configuration reference  
- [**Prompts**](prompts/overview.md) — Prompt engineering guide

### Benchmarking & Logs

- [**Benchmark Overview**](evaluation/benchmark/overview.md) — WindowsAgentArena, OSWorld  
- [**Performance Logs**](evaluation/logs/overview.md) — Execution logs and debugging  

---

## Research Impact

UFO² demonstrates that **system-level integration** and **architectural design** matter more than model size alone:

!!!success "Key Findings"
    - **10%+ improvement** over Claude/Operator on WindowsAgentArena  
    - **51% fewer LLM calls** via speculative multi-action execution  
    - **Robust to UI changes** through hybrid UIA + visual detection  
    - **Continuous learning** without model retraining via RAG  
    - **Non-disruptive UX** via Picture-in-Picture desktop

**Research Paper:**  
📄 [UFO²: A Grounded OS Agent for Windows](https://arxiv.org/abs/2504.14603)

---

## Get Started

Ready to explore UFO²? Choose your path:

!!!info "Learning Paths"
    **🚀 New Users:** Start with [Quick Start Guide](../getting_started/quick_start_ufo2.md)  
    **🔧 Developers:** Read [Creating AppAgent](../tutorials/creating_app_agent/overview.md)  
    **🏗️ System Architects:** Study [Device Agent Architecture](../infrastructure/agents/overview.md)  
    **📊 Researchers:** Check [Benchmark Results](evaluation/benchmark/overview.md)

**Next:** [HostAgent Deep Dive](host_agent/overview.md) → Understand desktop orchestration

---

## 🌐 Media Coverage

Check out our official deep dive of UFO on [this Youtube Video](https://www.youtube.com/watch?v=QT_OhygMVXU).

UFO sightings have garnered attention from various media outlets, including:

- [微软正式开源UFO²，Windows桌面迈入「AgentOS 时代」](https://www.jiqizhixin.com/articles/2025-05-06-13)
- [Microsoft's UFO abducts traditional user interfaces for a smarter Windows experience](https://the-decoder.com/microsofts-ufo-abducts-traditional-user-interfaces-for-a-smarter-windows-experience/)
- [🚀 UFO & GPT-4-V: Sit back and relax, mientras GPT lo hace todo🌌](https://www.linkedin.com/posts/gutierrezfrancois_ai-ufo-microsoft-activity-7176819900399652865-pLoo?utm_source=share&utm_medium=member_desktop)
- [The AI PC - The Future of Computers? - Microsoft UFO](https://www.youtube.com/watch?v=1k4LcffCq3E)
- [下一代Windows系统曝光：基于GPT-4V，Agent跨应用调度，代号UFO](https://baijiahao.baidu.com/s?id=1790938358152188625&wfr=spider&for=pc)
- [下一代智能版 Windows 要来了？微软推出首个 Windows Agent，命名为 UFO！](https://blog.csdn.net/csdnnews/article/details/136161570)
- [Microsoft発のオープンソース版「UFO」登場！　Windowsを自動操縦するAIエージェントを試す](https://internet.watch.impress.co.jp/docs/column/shimizu/1570581.html)

---

## 📚 Citation

If you build on this work, please cite the AgentOS framework:

**UFO² – The Desktop AgentOS (2025)**  
<https://arxiv.org/abs/2504.14603>

```bibtex
@article{zhang2025ufo2,
  title   = {{UFO2: The Desktop AgentOS}},
  author  = {Zhang, Chaoyun and Huang, He and Ni, Chiming and Mu, Jian and Qin, Si and He, Shilin and Wang, Lu and Yang, Fangkai and Zhao, Pu and Du, Chao and Li, Liqun and Kang, Yu and Jiang, Zhao and Zheng, Suzhen and Wang, Rujia and Qian, Jiaxu and Ma, Minghua and Lou, Jian-Guang and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei},
  journal = {arXiv preprint arXiv:2504.14603},
  year    = {2025}
}
```

**UFO – A UI‑Focused Agent for Windows OS Interaction (2024)**  
<https://arxiv.org/abs/2402.07939>

```bibtex
@article{zhang2024ufo,
  title   = {{UFO: A UI-Focused Agent for Windows OS Interaction}},
  author  = {Zhang, Chaoyun and Li, Liqun and He, Shilin and Zhang, Xu and Qiao, Bo and Qin, Si and Ma, Minghua and Kang, Yu and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei and Zhang, Qi},
  journal = {arXiv preprint arXiv:2402.07939},
  year    = {2024}
}
```

---

## 🎨 Related Projects

- **TaskWeaver** — a code‑first LLM agent for data analytics: <https://github.com/microsoft/TaskWeaver>  
- **LLM‑Brained GUI Agents: A Survey**: <https://arxiv.org/abs/2411.18279> • [GitHub](https://github.com/vyokky/LLM-Brained-GUI-Agents-Survey) • [Interactive site](https://vyokky.github.io/LLM-Brained-GUI-Agents-Survey/)

---

## ❓Get Help

- ❔GitHub Issues (preferred)
- For other communications, please contact [ufo-agent@microsoft.com](mailto:ufo-agent@microsoft.com)

