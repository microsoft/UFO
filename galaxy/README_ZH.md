<!-- markdownlint-disable MD033 MD041 -->

<p align="center">
  <strong>📖 Language / 语言:</strong>
  <a href="README.md">English</a> | 
  <strong>中文</strong>
</p>

<h1 align="center">
  <b>UFO³</b> <img src="../assets/logo3.png" alt="UFO³ logo" width="80" style="vertical-align: -30px;"> : 编织数字智能体星系
</h1>
<p align="center">
  <em>跨设备编排框架，实现无处不在的智能自动化</em>
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
  <em><strong>从孤立的设备智能体到互联的星座——构建数字智能体星系</strong></em>
</p>

---

## 🌟 什么是 UFO³ Galaxy？

**UFO³ Galaxy** 是一个革命性的**跨设备编排框架**，将孤立的设备智能体转变为统一的数字生态系统。它将复杂的用户请求建模为**任务星座（Task Constellations，星座）** —— 动态分布式 DAG，其中节点表示可执行的子任务，边捕获跨异构设备的依赖关系。

### 🎯 愿景

构建真正无处不在的智能智能体需要超越单设备自动化。UFO³ Galaxy 解决了四个基本挑战：

<table>
<tr>
<td width="50%" valign="top">

**🔄 异步并行性**
跨设备并发任务执行，同时通过事件驱动协调保持正确性

**⚡ 动态适应**  
基于运行时反馈和任务完成事件的实时工作流演化

</td>
<td width="50%" valign="top">

**🌐 分布式协调**  
通过基于 WebSocket 的智能体交互协议实现可靠、低延迟的跨设备通信

**🛡️ 安全保证**  
形式不变量（I1-I3）确保并发修改和并行执行期间的 DAG 一致性

</td>
</tr>
</table>

---

## ✨ 关键创新

<table>
<tr>
<td width="50%" valign="top">

### 🌟 任务星座框架

自然语言请求被分解为**任务星座** —— 结构化的 DAG 工作流，带有编码任务逻辑、依赖关系和设备分配的 **TaskStars（任务星）**（节点）和 **TaskStarLines（任务星线）**（边）。这使得可以进行**声明式工作流表示**以用于自动调度、**运行时自省**和动态修改、独立子任务的**并行执行**以及**跨设备数据流**管理。

```
用户意图 → ConstellationAgent → 任务星座（DAG）
                                    ├─ TaskStar 1 (Windows)
                                    ├─ TaskStar 2 (Linux GPU) ─┐
                                    ├─ TaskStar 3 (Linux CPU) ─┼─ TaskStar 5
                                    └─ TaskStar 4 (Mobile)    ─┘
```

---

### ⚡ 事件驱动编排

**星座编排器（Constellation Orchestrator）**通过以下方式异步执行 DAG：

- 👁️ **观察者模式**用于实时任务状态监控
- 🔒 **安全分配锁定**以防止竞态条件
- ✅ **三个形式不变量**确保 DAG 正确性：
- 📅 基于依赖完成的**动态任务调度**
- 🔄 失败时**自动重试和迁移**

</td>
<td width="50%" valign="top">

### 🎯 智能星座智能体

由 LLM 驱动的智能体，以两种模式运行：

- **创建模式**：从用户请求合成初始 DAG，具有设备感知的任务分解
- **编辑模式**：基于任务完成事件和运行时反馈增量细化星座

**功能：**
- 🧠 用于上下文感知规划的 ReAct 架构
- 🎯 基于能力的设备分配
- 🛡️ 自动错误恢复和工作流适应
- 🔄 具有安全转换的状态机控制

---

### 🔌 智能体交互协议（AIP）

统一的基于 WebSocket 的通信层，提供：

- 📝 带有能力配置文件的**设备注册**
- 💓 用于可用性跟踪的**心跳监控**
- 📤 具有动态路由的**任务分发**
- 📊 带有实时进度更新的**结果流式传输**
- 🔌 具有自动重新连接的**连接弹性**

</td>
</tr>
</table>

---

## 🏗️ 架构概览

<div align="center">
  <img src="../documents/docs/img/overview2.png" alt="UFO³ Galaxy 架构" style="max-width: 100%; height: auto; margin: 20px 0;">
  <p><em>UFO³ Galaxy 分层架构 —— 从自然语言到分布式执行</em></p>
</div>

### 分层设计

<table>
<tr>
<td width="50%" valign="top">

#### 🎛️ 控制平面

| 组件 | 角色 | 关键功能 |
|-----------|------|--------------|
| **🌐 ConstellationClient** | 全局设备注册表 | • 能力配置文件<br>• 健康指标<br>• 负载平衡 |
| **🖥️ 设备智能体** | 本地编排 | • 统一 MCP 工具<br>• 特定于平台的执行 |
| **🔒 清晰分离** | 架构原则 | • 全局策略<br>• 设备独立性 |

</td>
<td width="50%" valign="top">

#### 🔄 执行流程

```mermaid
graph TD
    A[1️⃣ DAG 合成] --> B[2️⃣ 设备分配]
    B --> C[3️⃣ 异步执行]
    C --> D[4️⃣ 动态适应]
    
    A1[ConstellationAgent 构建<br/>TaskConstellation] -.-> A
    B1[基于配置文件<br/>匹配到有能力的设备] -.-> B
    C1[事件驱动协调<br/>并行执行] -.-> C
    D1[基于反馈的<br/>工作流演化] -.-> D
```

</td>
</tr>
</table>

---

## 🎥 演示视频

观看 UFO³ Galaxy 进行跨设备编排的全面演示：

<div align="center">
  <a href="https://github.com/microsoft/UFO/releases/download/v3.0.0/UFO3.mp4">
    <img src="../assets/demo_preview.png" alt="UFO³ Galaxy 演示视频" width="90%">
  </a>
  <p><em>🎬 观看完整演示：使用 UFO³ Galaxy 进行多设备工作流编排</em></p>
</div>

**演示亮点：**

| 功能 | 演示 |
|---------|---------------|
| 🌟 **星座规划** | 自然语言 → DAG 工作流分解 |
| 🎯 **设备分配** | 基于能力的任务路由到 Windows/Linux 设备 |
| ⚡ **并行执行** | 具有依赖管理的并发任务执行 |
| 📊 **实时监控** | 实时星座可视化和状态更新 |
| 🔄 **动态适应** | 自动错误恢复和工作流细化 |
| 🌐 **跨平台** | 跨异构设备的无缝协调 |


---

## 🚀 快速入门

### 🛠️ 步骤 1：安装

```powershell
# 克隆仓库
git clone https://github.com/microsoft/UFO.git
cd UFO

# 创建环境（推荐）
conda create -n ufo3 python=3.10
conda activate ufo3

# 安装依赖
pip install -r requirements.txt
```

### ⚙️ 步骤 2：配置 ConstellationAgent LLM

UFO³ Galaxy 使用协调所有设备智能体的 **ConstellationAgent**。配置其 LLM 设置：

```powershell
# 从模板创建配置
copy config\galaxy\agent.yaml.template config\galaxy\agent.yaml
notepad config\galaxy\agent.yaml
```

**配置文件位置：**
```
config/galaxy/
├── agent.yaml.template    # 模板 - 复制此文件
├── agent.yaml             # 您的配置与 API 密钥（不要提交）
└── devices.yaml           # 设备池配置（步骤 4）
```

**OpenAI 配置：**
```yaml
CONSTELLATION_AGENT:
  REASONING_MODEL: false
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_KEY_HERE"
  API_VERSION: "2025-02-01-preview"
  API_MODEL: "gpt-5-chat-20251003"
  # ...（提示配置使用默认值）
```

**Azure OpenAI 配置：**
```yaml
CONSTELLATION_AGENT:
  REASONING_MODEL: false
  API_TYPE: "aoai"
  API_BASE: "https://YOUR_RESOURCE.openai.azure.com"
  API_KEY: "YOUR_AOAI_KEY"
  API_VERSION: "2024-02-15-preview"
  API_MODEL: "gpt-5-chat-20251003"
  API_DEPLOYMENT_ID: "YOUR_DEPLOYMENT_ID"
  # ...（提示配置使用默认值）
```

### 🖥️ 步骤 3：配置设备智能体

每个设备智能体（Windows/Linux）需要自己的 LLM 配置来执行任务。

```powershell
# 配置设备智能体 LLM
copy config\ufo\agents.yaml.template config\ufo\agents.yaml
notepad config\ufo\agents.yaml
```

**配置文件位置：**
```
config/ufo/
├── agents.yaml.template    # 模板 - 复制此文件
└── agents.yaml             # 设备智能体 LLM 配置（不要提交）
```

**示例配置：**
```yaml
HOST_AGENT:
  VISUAL_MODE: true
  API_TYPE: "openai"  # 或 Azure OpenAI 为 "aoai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_KEY_HERE"
  API_MODEL: "gpt-4o"

APP_AGENT:
  VISUAL_MODE: true
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_KEY_HERE"
  API_MODEL: "gpt-4o"
```

> **💡 提示：** 您可以为 ConstellationAgent（步骤 2）和设备智能体（步骤 3）使用相同的 API 密钥和模型。

### 🌐 步骤 4：配置设备池

```powershell
# 配置可用设备
copy config\galaxy\devices.yaml.template config\galaxy\devices.yaml
notepad config\galaxy\devices.yaml
```

**示例设备配置：**
```yaml
devices:
  # Windows 设备（UFO²）
  - device_id: "windows_device_1"              # 必须匹配 --client-id
    server_url: "ws://localhost:5000/ws"       # 必须匹配服务器 WebSocket URL
    os: "windows"
    capabilities:
      - "desktop_automation"
      - "office_applications"
      - "excel"
      - "word"
      - "outlook"
      - "email"
      - "web_browsing"
    metadata:
      os: "windows"
      version: "11"
      performance: "high"
      installed_apps:
        - "Microsoft Excel"
        - "Microsoft Word"
        - "Microsoft Outlook"
        - "Google Chrome"
      description: "用于办公自动化的主 Windows 桌面"
    auto_connect: true
    max_retries: 5

  # Linux 设备
  - device_id: "linux_device_1"                # 必须匹配 --client-id
    server_url: "ws://localhost:5001/ws"       # 必须匹配服务器 WebSocket URL
    os: "linux"
    capabilities:
      - "server_management"
      - "log_analysis"
      - "file_operations"
      - "database_operations"
    metadata:
      os: "linux"
      performance: "medium"
      logs_file_path: "/var/log/myapp/app.log"
      dev_path: "/home/user/projects/"
      warning_log_pattern: "WARN"
      error_log_pattern: "ERROR|FATAL"
      description: "用于后端操作的开发服务器"
    auto_connect: true
    max_retries: 5
```

> **⚠️ 关键：ID 和 URL 必须匹配**
> - `device_id` **必须完全匹配** `--client-id` 标志
> - `server_url` **必须完全匹配**服务器 WebSocket URL
> - 否则，Galaxy 无法控制设备！

### 🖥️ 步骤 5：启动设备智能体

Galaxy 编排执行各个机器上任务的**设备智能体**。您需要根据需要启动适当的设备智能体。

#### 示例：快速 Windows 设备设置

**在您的 Windows 机器上：**

```powershell
# 终端 1：启动 UFO² 服务器
python -m ufo.server.app --port 5000

# 终端 2：启动 UFO² 客户端（连接到服务器）
python -m ufo.client.client `
  --ws `
  --ws-server ws://localhost:5000/ws `
  --client-id windows_device_1 `
  --platform windows
```

> **⚠️ 重要：需要平台标志**
> 始终为 Windows 设备包含 `--platform windows`，为 Linux 设备包含 `--platform linux`！

#### 示例：快速 Linux 设备设置

**在您的 Linux 机器上：**

```bash
# 终端 1：启动设备智能体服务器
python -m ufo.server.app --port 5001

# 终端 2：启动 Linux 客户端（连接到服务器）
python -m ufo.client.client \
  --ws \
  --ws-server ws://localhost:5001/ws \
  --client-id linux_device_1 \
  --platform linux

# 终端 3：启动 HTTP MCP 服务器（用于 Linux 工具）
python -m ufo.client.mcp.http_servers.linux_mcp_server
```

**📖 详细设置说明：**
- **对于 Windows 设备（UFO²）：** 参见 [UFO² 作为 Galaxy 设备](../documents/docs/ufo2/as_galaxy_device.md)
- **对于 Linux 设备：** 参见 [Linux 作为 Galaxy 设备](../documents/docs/linux/as_galaxy_device.md)

### 🌌 步骤 6：启动 Galaxy 客户端

#### 🎨 交互式 WebUI 模式（推荐）

使用交互式 Web 界面启动 Galaxy，实现实时星座可视化和监控：

```powershell
python -m galaxy --webui
```

这将启动带有 WebUI 的 Galaxy 服务器，并打开浏览器到交互式界面：

<div align="center">
  <img src="../assets/webui.png" alt="UFO³ Galaxy WebUI 界面" width="90%">
  <p><em>🎨 Galaxy WebUI - 交互式星座可视化和聊天界面</em></p>
</div>

**WebUI 功能：**
- 🗣️ **聊天界面**：提交请求并实时与 ConstellationAgent 交互
- 📊 **实时 DAG 可视化**：观察任务星座形成和执行
- 🎯 **任务状态跟踪**：监控每个 TaskStar 的进度和完成情况
- 🔄 **动态更新**：随着任务完成查看星座演化
- 📱 **响应式设计**：在桌面和平板设备上工作

**默认 URL：** `http://localhost:8000`（如果 8000 被占用，自动查找下一个可用端口）

---

#### 💬 交互式终端模式

用于命令行交互：

```powershell
python -m galaxy --interactive
```

---

#### ⚡ 直接请求模式

执行单个请求并退出：

```powershell
python -m galaxy --request "从 Windows 上的 Excel 提取数据，在 Linux 上使用 Python 处理，并生成可视化报告"
```

---

#### 🔧 编程 API

将 Galaxy 嵌入到您的 Python 应用程序中：

```python
from galaxy.galaxy_client import GalaxyClient

async def main():
    # 初始化客户端
    client = GalaxyClient(session_name="data_pipeline")
    await client.initialize()
    
    # 执行跨设备工作流
    result = await client.process_request(
        "下载销售数据，分析趋势，生成执行摘要"
    )
    
    # 访问星座详细信息
    constellation = client.session.constellation
    print(f"执行的任务：{len(constellation.tasks)}")
    print(f"使用的设备：{set(t.assigned_device for t in constellation.tasks)}")
    
    await client.shutdown()

import asyncio
asyncio.run(main())
```

---

## 🎯 用例

### 🖥️ 软件开发和 CI/CD

**请求：**  
*"在 Windows 上克隆仓库，在 Linux GPU 服务器上构建 Docker 镜像，部署到暂存环境，并在 CI 集群上运行测试套件"*

**星座工作流：**
```
克隆 (Windows) → 构建 (Linux GPU) → 部署 (Linux 服务器) → 测试 (Linux CI)
```

**优势：** 并行执行将管道时间减少 60%

---

### 📊 数据科学工作流

**请求：**  
*"从云存储获取数据集，在 Linux 工作站上预处理，在 A100 节点上训练模型，在 Windows 上可视化结果"*

**星座工作流：**
```
获取（任何）→ 预处理（Linux）→ 训练（Linux GPU）→ 可视化（Windows）
```

**优势：** 自动 GPU 检测和最佳设备分配

---

### 📝 跨平台文档处理

**请求：**  
*"从 Windows 上的 Excel 提取数据，在 Linux 上使用 Python 处理，生成 PDF 报告，并发送电子邮件摘要"*

**星座工作流：**
```
提取（Windows）→ 处理（Linux）┬→ 生成 PDF（Windows）
                              └→ 发送电子邮件（Windows）
```

**优势：** 并行报告生成和电子邮件传递

---

### 🔬 分布式系统监控

**请求：**  
*"从所有 Linux 机器收集服务器日志，分析错误，生成警报，创建合并报告"*

**星座工作流：**
```
┌→ 收集（Linux 1）┐
├→ 收集（Linux 2）├→ 分析（任何）→ 报告（Windows）
└→ 收集（Linux 3）┘
```

**优势：** 并行日志收集，自动聚合

---

## 🌐 核心能力

<table>
<tr>
<td width="50%" valign="top">

### ⚡ 异步并行性
- 事件驱动的调度监控 DAG 以查找准备好的任务
- 使用 Python `asyncio` 的非阻塞执行
- 动态集成新任务而不中断
- **结果：** 端到端延迟减少高达 70%

### 🛡️ 安全性和一致性
- 用于 DAG 正确性的三个形式不变量（I1-I3）
- 安全分配锁定防止竞态条件
- 无环性验证确保没有循环依赖
- 状态合并在编辑期间保留执行进度

</td>
<td width="50%" valign="top">

### 🔄 动态适应
- 具有 FSM 控制的双模式操作（创建/编辑）
- 反馈驱动的星座细化
- 通过 ReAct 架构的 LLM 驱动推理
- 自动错误恢复和任务重新调度

### 👁️ 丰富的可观察性
- 具有 DAG 更新的实时星座可视化
- 具有发布-订阅模式的事件总线
- 带有 markdown 轨迹的详细执行日志
- 任务状态跟踪和依赖关系检查

</td>
</tr>
</table>

### 🔌 可扩展性和自定义设备智能体

UFO³ 设计为**通用框架**，支持为不同平台（移动、Web、IoT、嵌入式系统等）和应用程序开发新的设备智能体。通过**智能体交互协议（AIP）**，自定义设备智能体可以无缝集成到 UFO³ Galaxy 中，实现协调的多设备自动化。

**📖 想构建自己的设备智能体？** 查看我们的[创建自定义设备智能体教程](../documents/docs/tutorials/creating_device_agent/overview.md)，了解如何将 UFO³ 扩展到新平台。

---

## 📚 文档

| 组件 | 描述 | 链接 |
|-----------|-------------|------|
| **Galaxy 客户端** | 设备协调和 ConstellationClient API | [了解更多](../documents/docs/galaxy/client/overview.md) |
| **星座智能体** | LLM 驱动的任务分解和 DAG 演化 | [了解更多](../documents/docs/galaxy/constellation_agent/overview.md) |
| **任务编排器** | 异步执行和安全保证 | [了解更多](../documents/docs/galaxy/constellation_orchestrator/overview.md) |
| **任务星座** | DAG 结构和星座编辑器 | [了解更多](../documents/docs/galaxy/constellation/overview.md) |
| **智能体注册** | 设备注册表和智能体配置文件 | [了解更多](../documents/docs/galaxy/agent_registration/overview.md) |
| **AIP 协议** | WebSocket 消息传递和通信模式 | [了解更多](../documents/docs/aip/overview.md) |
| **配置** | 设备池和编排策略 | [了解更多](../documents/docs/configuration/system/galaxy_devices.md) |
| **创建设备智能体** | 构建自定义设备智能体的教程 | [了解更多](../documents/docs/tutorials/creating_device_agent/overview.md) |

---

## 📊 系统架构

### 核心组件

| 组件 | 位置 | 职责 |
|-----------|----------|----------------|
| **GalaxyClient** | `galaxy/galaxy_client.py` | 会话管理，用户交互 |
| **ConstellationClient** | `galaxy/client/constellation_client.py` | 设备注册表，连接生命周期 |
| **ConstellationAgent** | `galaxy/agents/constellation_agent.py` | DAG 合成和演化 |
| **TaskConstellationOrchestrator** | `galaxy/constellation/orchestrator/` | 异步执行，安全执行 |
| **TaskConstellation** | `galaxy/constellation/task_constellation.py` | DAG 数据结构和验证 |
| **DeviceManager** | `galaxy/client/device_manager.py` | WebSocket 连接，心跳监控 |
| **Agent Server** | `ufo/mode/agent_server.py` | 设备端 WebSocket 服务器 |

### 技术栈

| 层 | 技术 |
|-------|-------------|
| **语言** | Python 3.10+、asyncio、dataclasses |
| **通信** | WebSockets、JSON-RPC |
| **LLM** | OpenAI、Azure OpenAI、Gemini、Claude |
| **工具** | 模型上下文协议（MCP） |
| **配置** | YAML、Pydantic 验证 |
| **日志** | Rich 控制台、Markdown 轨迹 |

---

## 🌟 从设备到星系

UFO³ 代表智能自动化的范式转变：

```
单设备  →  任务星座  →  数字智能体星系
   (UFO/UFO²)           (UFO³ Galaxy)         (未来愿景)
     ↓                    ↓                      ↓
  Windows          跨设备           自组织
  桌面            工作流            生态系统
```

随着时间的推移，多个星座相互连接，形成一个自组织的**数字智能体星系**，其中设备、智能体和能力编织在一起，形成适应性强、弹性强和智能的无处不在的计算系统。

---

## 📄 引用

如果您在研究中使用 UFO³ Galaxy，请引用：

**UFO³ Galaxy 框架：**
```bibtex
@article{zhang2025ufo3,
  title   = {{UFO³: Weaving the Digital Agent Galaxy}},
  author  = {Zhang, Chaoyun and [Authors TBD]},
  journal = {arXiv preprint arXiv:[TBD]},
  year    = {2025}
}
```

**UFO² 桌面智能体操作系统：**
```bibtex
@article{zhang2025ufo2,
  title   = {{UFO2: The Desktop AgentOS}},
  author  = {Zhang, Chaoyun and Huang, He and Ni, Chiming and Mu, Jian and Qin, Si and He, Shilin and Wang, Lu and Yang, Fangkai and Zhao, Pu and Du, Chao and Li, Liqun and Kang, Yu and Jiang, Zhao and Zheng, Suzhen and Wang, Rujia and Qian, Jiaxu and Ma, Minghua and Lou, Jian-Guang and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei},
  journal = {arXiv preprint arXiv:2504.14603},
  year    = {2025}
}
```

**第一代 UFO：**
```bibtex
@article{zhang2024ufo,
  title   = {{UFO: A UI-Focused Agent for Windows OS Interaction}},
  author  = {Zhang, Chaoyun and Li, Liqun and He, Shilin and Zhang, Xu and Qiao, Bo and Qin, Si and Ma, Minghua and Kang, Yu and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei and Zhang, Qi},
  journal = {arXiv preprint arXiv:2402.07939},
  year    = {2024}
}
```

---

## 🤝 贡献

我们欢迎贡献！无论是构建新的设备智能体、改进编排算法还是增强协议：

- 🐛 [报告问题](https://github.com/microsoft/UFO/issues)
- 💡 [请求功能](https://github.com/microsoft/UFO/discussions)
- 📝 [改进文档](https://github.com/microsoft/UFO/pulls)
- 🧪 [提交拉取请求](../../CONTRIBUTING.md)

---

## 📬 联系与支持

- 📖 **文档**：[https://microsoft.github.io/UFO/](https://microsoft.github.io/UFO/)
- 💬 **讨论**：[GitHub 讨论](https://github.com/microsoft/UFO/discussions)
- 🐛 **问题**：[GitHub 问题](https://github.com/microsoft/UFO/issues)
- 📧 **电子邮件**：[ufo-agent@microsoft.com](mailto:ufo-agent@microsoft.com)

---

## ⚖️ 许可证

UFO³ Galaxy 根据 [MIT 许可证](../../LICENSE) 发布。

有关隐私和安全通知，请参阅 [DISCLAIMER.md](../../DISCLAIMER.md)。

---

<div align="center">
  <p><strong>将您的分布式设备转变为统一的数字集体。</strong></p>
  <p><em>UFO³ Galaxy —— 每个设备都是一颗星，每个任务都是一个星座。</em></p>
  <br>
  <sub>© Microsoft 2025 • UFO³ 是一个开源研究项目</sub>
</div>
