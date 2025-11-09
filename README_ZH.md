<!-- markdownlint-disable MD033 MD041 -->

<p align="center">
  <strong>📖 Language / 语言:</strong>
  <a href="README.md">English</a> | 
  <strong>中文</strong>
</p>

<h1 align="center">
  <b>UFO³</b> <img src="assets/logo3.png" alt="UFO logo" width="80" style="vertical-align: -30px;"> : 编织数字智能体星系
</h1>
<p align="center">
  <em>从单设备智能体到多设备星系</em>
</p>

<p align="center">
  <strong>📚 快速链接：</strong>
  <a href="#-选择您的路径">🌌 UFO³ 概述</a> •
  <a href="./ufo/README_ZH.md">🖥️ UFO² 中文文档</a> •
  <a href="https://microsoft.github.io/UFO/">📖 完整文档</a>
</p>

<div align="center">

[![arxiv](https://img.shields.io/badge/Paper-arXiv:2504.14603-b31b1b.svg)](https://arxiv.org/abs/2504.14603)&ensp;
![Python Version](https://img.shields.io/badge/Python-3776AB?&logo=python&logoColor=white-blue&label=3.10%20%7C%203.11)&ensp;
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)&ensp;
[![Documentation](https://img.shields.io/badge/Documentation-%230ABAB5?style=flat&logo=readthedocs&logoColor=black)](https://microsoft.github.io/UFO/)&ensp;
[![YouTube](https://img.shields.io/badge/YouTube-white?logo=youtube&logoColor=%23FF0000)](https://www.youtube.com/watch?v=QT_OhygMVXU)&ensp;

</div>

---

## 🎯 选择您的路径

<table align="center">
<tr>
<td width="50%" valign="top">

### <img src="assets/logo3.png" alt="Galaxy logo" width="40" style="vertical-align: -10px;"> **Galaxy** – 多设备编排
<sub>**✨ 新功能 & 推荐**</sub>

**适用于：**
- 🔗 跨设备协作工作流
- 📊 复杂的多步骤自动化  
- 🎯 基于 DAG 的任务编排
- 🌍 异构平台集成

**关键功能：**
- **星座（Constellation）**：任务分解为可执行 DAG
- **动态设备分配**，通过能力匹配
- **实时工作流监控**和适应
- **事件驱动协调**跨设备
- **容错性**，自动恢复

**开始使用：**
```bash
python -m galaxy \
  --request "您的复杂任务"
```

**📖 [Galaxy 中文文档 →](./galaxy/README_ZH.md)**  
**📖 [Galaxy 快速入门 →](https://microsoft.github.io/UFO/getting_started/quick_start_galaxy/)** ⭐ **在线文档**

</td>
<td width="50%" valign="top">

### <img src="assets/ufo_blue.png" alt="UFO² logo" width="30" style="vertical-align: -5px;"> **UFO² 桌面智能体操作系统** – Windows 智能体操作系统
<sub>**稳定 & 经过实战检验**</sub>

**适用于：**
- 💻 单个 Windows 自动化
- ⚡ 快速任务执行
- 🎓 学习智能体基础知识
- 🛠️ 简单工作流

**关键功能：**
- 深度 Windows 操作系统集成
- 混合 GUI + API 操作
- 经过验证的可靠性
- 易于设置
- 可作为 Galaxy 设备智能体

**开始使用：**
```bash
python -m ufo \
  --task <your_task_name>
```

**📖 [UFO² 中文文档 →](./ufo/README_ZH.md)**

</td>
</tr>
</table>

<div align="center">

### 🤔 不确定选择哪个？

| 问题 | Galaxy | UFO² |
|----------|:------:|:----:|
| 需要跨设备协作？ | ✅ | ❌ |
| 复杂的多步骤工作流？ | ✅ | ⚠️ 有限 |
| 仅 Windows 自动化？ | ✅ | ✅ 优化 |
| 快速设置和学习？ | ⚠️ 中等 | ✅ 简单 |
| 生产就绪的稳定性？ | 🚧 积极开发 | ✅ LTS |

</div>

---

## 🎬 观看 UFO³ Galaxy 实际操作

观看 UFO³ Galaxy 如何跨多个设备编排复杂工作流：

<div align="center">
  <a href="https://github.com/microsoft/UFO/releases/download/v3.0.0/UFO3.mp4">
    <img src="assets/demo_preview.png" alt="UFO³ Galaxy 演示" width="80%">
  </a>
  <p><em>🎥 点击观看：使用 UFO³ Galaxy 进行跨设备任务编排</em></p>
</div>

**演示中您将看到：**
- 🌟 从自然语言请求创建任务星座
- 🎯 基于能力的智能设备分配
- ⚡ 跨 Windows 和 Linux 设备的并行执行
- 📊 实时监控和动态工作流适应

---

## 🌟 UFO³ 有什么新功能？

<h3 align="center">
  <img src="./assets/poster.png" width="70%"/> 
</h3>

### 演化时间线

```
2024.02    →    2025.04    →    2025.11
   ↓              ↓              ↓
  UFO           UFO²         UFO³ Galaxy
  GUI         桌面智能体      多设备
智能体        操作系统        编排
```

### 🚀 UFO³ = **Galaxy**（多设备编排）+ **UFO²**（设备智能体）

UFO³ 引入了 **Galaxy**，这是一个新颖的多设备编排框架，可在异构平台上协调智能智能体。建立在三个核心创新之上：

1. **🌟 TaskConstellation（任务星座）** - 任务分解为基于 DAG 的工作流
2. **🎯 ConstellationAgent（星座智能体）** - 智能任务规划和设备分配  
3. **⚡ 动态编排** - 实时监控和自适应执行

| 方面 | UFO² | UFO³ Galaxy |
|--------|------|-------------|
| **架构** | 单个 Windows 智能体 | 多设备编排 |
| **任务模型** | 顺序 ReAct 循环 | 基于 DAG 的星座工作流 |
| **范围** | 单设备，多应用 | 多设备，跨平台 |
| **协调** | HostAgent + AppAgents | ConstellationAgent + TaskOrchestrator |
| **设备支持** | Windows 桌面 | Windows、Linux、macOS、Android、Web |
| **任务规划** | 应用程序级别 | 设备级别，带依赖关系 |
| **执行** | 顺序 | 并行 DAG 执行 |
| **设备智能体角色** | 独立 | 可作为 Galaxy 设备智能体 |
| **复杂性** | 简单到中等 | 简单到非常复杂 |
| **学习曲线** | 低 | 中等 |
| **状态** | ✅ LTS（长期支持） | ⚡ 积极开发 |

### 🎓 迁移路径

**对于 UFO² 用户：**
1. ✅ **继续使用 UFO²** – 完全支持，积极维护
2. 🔄 **渐进式采用** – Galaxy 可以使用 UFO² 作为 Windows 设备智能体
3. 📈 **扩展** – 当您需要多设备功能时迁移到 Galaxy
4. 📚 **学习资源** – [迁移指南](./documents/docs/getting_started/migration_ufo2_to_galaxy.md)

---

## ✨ 功能概览

### 🌌 Galaxy 框架 – 有什么不同？

<table>
<tr>
<td width="33%" valign="top">

#### 🌟 星座规划
```
用户："从 Windows 上的 
Excel 收集销售数据，在 
Linux 上分析，在 Mac 上可视化"
        ↓
 ConstellationAgent
        ↓
    [任务 DAG]
    /    |    \
 Task1 Task2 Task3
 (Win) (Linux)(Mac)
 
 ✓ 依赖关系跟踪
 ✓ 并行执行
 ✓ 跨设备数据流
```

</td>
<td width="33%" valign="top">

#### 🎯 动态设备分配
```python
# 基于能力的匹配
设备选择：
  - 平台兼容性
  - 资源可用性
  - 任务要求
  - 性能历史记录
  
自动分配到：
  ✓ 最合适的设备
  ✓ 负载平衡
  ✓ 容错
```

</td>
<td width="33%" valign="top">

#### 📊 实时编排
```
任务执行监控：
┌─ 星座 ────────┐
│ ✅ 数据收集   │
│ 🔄 处理中     │
│ ⏸️  可视化    │
│ ⏳ 报告生成   │
└───────────────┘

✓ 实时状态更新
✓ 错误恢复
✓ 进度跟踪
```

</td>
</tr>
</table>

**来自 [UFO³ 论文](https://arxiv.org/abs/[TBD]) 的关键创新：**

<div align="center">

| 🎯 创新 | 💡 描述 | 🚀 影响 |
|---------------|----------------|-----------|
| **🌟 星座规划** | 将复杂请求分解为具有任务依赖关系的可执行 DAG 工作流 | 实现自动化并行执行和智能调度 |
| **🌐 异构集成** | 跨 Windows、Linux、macOS、Android 和 Web 平台的无缝编排 | 摆脱单平台限制 |
| **⚡ 事件驱动架构** | 具有观察者模式的实时监控和自适应执行 | 基于运行时反馈的动态工作流调整 |
| **🎯 智能分配** | 基于能力的匹配和动态资源分配到最佳设备 | 通过智能设备选择最大化效率 |
| **🛡️ 容错性** | 自动错误检测、恢复和任务重新调度机制 | 确保工作流完成，尽管设备失败 |

</div>

### 🪟 UFO² 桌面智能体操作系统 – 核心优势

UFO² 扮演双重角色：**独立 Windows 自动化**和 Windows 平台的 **Galaxy 设备智能体**。

<div align="center">

| 功能 | 描述 | 文档 |
|---------|-------------|---------------|
| **深度操作系统集成** | Windows UIA、Win32、WinCOM 原生控件 | [了解更多](https://microsoft.github.io/UFO) |
| **混合操作** | GUI 点击 + API 调用以获得最佳性能 | [了解更多](https://microsoft.github.io/UFO/automator/overview) |
| **推测性多操作** | 批量预测 → **减少 51% 的 LLM 调用** | [了解更多](https://microsoft.github.io/UFO/advanced_usage/multi_action) |
| **视觉 + UIA 检测** | 用于稳健性的混合控件检测 | [了解更多](https://microsoft.github.io/UFO/advanced_usage/control_detection/hybrid_detection) |
| **知识基底** | 带有文档、演示、执行轨迹的 RAG | [了解更多](https://microsoft.github.io/UFO/advanced_usage/reinforce_appagent/overview/) |
| **设备智能体角色** | 可作为 Galaxy 编排中的 Windows 执行器 | [了解更多](./galaxy/README_ZH.md) |

</div>

**作为 Galaxy 设备智能体：**
- 通过 Galaxy 编排层从 ConstellationAgent 接收任务
- 使用经过验证的 UFO² 功能执行 Windows 特定的操作
- 向 TaskOrchestrator 报告状态和结果
- 无缝参与跨设备工作流

---

## 🚀 快速入门指南

选择您的路径并遵循详细的设置指南：

<table align="center">
<tr>
<td width="50%" valign="top">

### 🌌 Galaxy 快速入门

**用于跨设备编排**

```powershell
# 1. 安装
pip install -r requirements.txt

# 2. 配置 ConstellationAgent
copy config\galaxy\agent.yaml.template config\galaxy\agent.yaml
# 编辑并添加您的 API 密钥

# 3. 启动设备智能体（带平台标志）
# Windows:
python -m ufo.server.app --port 5000
python -m ufo.client.client --ws --ws-server ws://localhost:5000/ws --client-id windows_device_1 --platform windows

# Linux:
python -m ufo.server.app --port 5001
python -m ufo.client.client --ws --ws-server ws://localhost:5001/ws --client-id linux_device_1 --platform linux

# 4. 启动 Galaxy
python -m galaxy --interactive
```

**📖 完整指南：**
- [Galaxy 中文文档](./galaxy/README_ZH.md) – 架构和概念
- [在线快速入门](https://microsoft.github.io/UFO/getting_started/quick_start_galaxy/) – 分步教程
- [配置](https://microsoft.github.io/UFO/configuration/system/galaxy_devices/) – 设备设置

</td>
<td width="50%" valign="top">

### 🪟 UFO² 快速入门

**用于 Windows 自动化**

```powershell
# 1. 安装
pip install -r requirements.txt

# 2. 配置
copy config\ufo\agents.yaml.template config\ufo\agents.yaml
# 编辑并添加您的 API 密钥

# 3. 运行
python -m ufo --task <task_name>
```

**📖 完整指南：**
- [UFO² 中文文档](./ufo/README_ZH.md) – 完整文档
- [配置指南](./ufo/README_ZH.md#️-步骤-2配置-llm) – LLM 设置
- [高级功能](https://microsoft.github.io/UFO/advanced_usage/overview/) – 多操作、RAG

</td>
</tr>
</table>

### 📋 常见配置

两个框架都需要 LLM API 配置。选择您的提供商：

<details>
<summary><strong>OpenAI 配置</strong></summary>

**对于 Galaxy (`config/galaxy/agent.yaml`)：**
```yaml
CONSTELLATION_AGENT:
  REASONING_MODEL: false
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-your-key-here"
  API_MODEL: "gpt-4o"
```

**对于 UFO² (`config/ufo/agents.yaml`)：**
```yaml
VISUAL_MODE: True
API_TYPE: "openai"
API_BASE: "https://api.openai.com/v1/chat/completions"
API_KEY: "sk-your-key-here"
API_MODEL: "gpt-4o"
```

</details>

<details>
<summary><strong>Azure OpenAI 配置</strong></summary>

**对于 Galaxy (`config/galaxy/agent.yaml`)：**
```yaml
CONSTELLATION_AGENT:
  REASONING_MODEL: false
  API_TYPE: "aoai"
  API_BASE: "https://YOUR-RESOURCE.openai.azure.com"
  API_KEY: "your-azure-key"
  API_MODEL: "gpt-4o"
  API_DEPLOYMENT_ID: "your-deployment-id"
```

**对于 UFO² (`config/ufo/agents.yaml`)：**
```yaml
VISUAL_MODE: True
API_TYPE: "aoai"
API_BASE: "https://YOUR-RESOURCE.openai.azure.com"
API_KEY: "your-azure-key"
API_MODEL: "gpt-4o"
API_DEPLOYMENT_ID: "your-deployment-id"
```

</details>

> 💡 **更多 LLM 选项：** 有关 Qwen、Gemini、Claude 等的信息，请参阅[模型配置指南](https://microsoft.github.io/UFO/supported_models/overview/)。

---

## 📚 文档结构

<table>
<tr>
<td width="50%" valign="top">

### 🌌 Galaxy 文档

- **[Galaxy 框架概述](./galaxy/README_ZH.md)** ⭐ **从这里开始** – 架构和技术概念
- **[快速入门教程](https://microsoft.github.io/UFO/getting_started/quick_start_galaxy/)** – 几分钟内开始运行
- **[Galaxy 客户端](https://microsoft.github.io/UFO/galaxy/client/overview/)** – 设备协调和 API
- **[星座智能体](https://microsoft.github.io/UFO/galaxy/constellation_agent/overview/)** – 任务分解和规划
- **[任务编排器](https://microsoft.github.io/UFO/galaxy/constellation_orchestrator/overview/)** – 执行引擎
- **[任务星座](https://microsoft.github.io/UFO/galaxy/constellation/overview/)** – DAG 结构
- **[智能体注册](https://microsoft.github.io/UFO/galaxy/agent_registration/overview/)** – 设备注册表
- **[配置指南](https://microsoft.github.io/UFO/configuration/system/galaxy_devices/)** – 设置和设备池

**📖 技术文档：**
- [AIP 协议](https://microsoft.github.io/UFO/aip/overview/) – WebSocket 消息传递
- [会话管理](https://microsoft.github.io/UFO/galaxy/session/overview/) – 会话生命周期
- [可视化](https://microsoft.github.io/UFO/galaxy/visualization/overview/) – 实时监控
- [事件和观察者](https://microsoft.github.io/UFO/galaxy/core/overview/) – 事件系统

</td>
<td width="50%" valign="top">

### 🪟 UFO² 文档

- **[UFO² 概述](./ufo/README_ZH.md)** – 桌面智能体操作系统架构
- **[安装](./ufo/README_ZH.md#️-步骤-1安装)** – 设置和依赖
- **[配置](./ufo/README_ZH.md#️-步骤-2配置-llm)** – LLM 和 RAG 设置
- **[使用指南](./ufo/README_ZH.md#-步骤-4启动-ufo)** – 运行 UFO²
- **[高级功能](https://microsoft.github.io/UFO/advanced_usage/overview/)** – 多操作、RAG 等
- **[自动化器指南](https://microsoft.github.io/UFO/automator/overview)** – 混合 GUI + API
- **[基准测试](./ufo/README_ZH.md#-评估)** – WAA 和 OSWorld 结果

**📖 在线文档：**
- [完整文档](https://microsoft.github.io/UFO/)
- [模型支持](https://microsoft.github.io/UFO/supported_models/overview/)
- [RAG 配置](https://microsoft.github.io/UFO/advanced_usage/reinforce_appagent/overview/)

</td>
</tr>
</table>

---

## 🎓 学习路径

### 对于完全初学者
```
1. 📖 阅读 UFO² 概述（更简单）
   └─ 了解单智能体概念
   
2. 🧪 尝试使用 UFO² 进行简单任务
   └─ 获得实践经验
   
3. 📈 准备好时探索 Galaxy
   └─ 扩展到多设备工作流
```

### 对于 UFO² 用户
```
1. ✅ 继续使用 UFO² 进行 Windows 任务
   └─ 完全支持，无需迁移压力
   
2. 📚 逐步学习 Galaxy 概念
   └─ DAG 工作流，设备编排
   
3. 🔄 混合方法
   └─ 对复杂任务使用 Galaxy，对简单任务使用 UFO²
   
4. 📖 准备好时遵循迁移指南
   └─ [迁移指南](./documents/docs/getting_started/migration_ufo2_to_galaxy.md)
```

### 对于高级用户
```
1. 🌌 深入了解 Galaxy 架构
   └─ ConstellationAgent、TaskOrchestrator
   
2. 🔧 自定义和扩展
   └─ 自定义智能体、设备类型、可视化
   
3. 🤝 贡献
   └─ 加入开发，分享反馈
```

---

## 🏗️ 架构比较

### UFO² – 桌面智能体操作系统

<div align="center">
  <img src="./assets/framework2.png" alt="UFO² 架构" width="80%"/>
  <p><em>UFO² 桌面智能体操作系统架构</em></p>
</div>

**关键特征：**
- 使用 ReAct 循环的顺序任务执行
- 单设备焦点（Windows）
- HostAgent 协调每个应用程序的 AppAgents
- 深度 Windows 集成（UIA、Win32、WinCOM）

---

### UFO³ Galaxy – 多设备编排框架

<div align="center">
  <img src="./documents/docs/img/overview2.png" alt="UFO³ Galaxy 架构" width="90%"/>
  <p><em>UFO³ Galaxy 分层架构 —— 跨设备编排</em></p>
</div>

**关键组件（来自 UFO³ 论文）：**
1. **ConstellationAgent（星座智能体）**：规划并将任务分解为 DAG 工作流
2. **TaskConstellation（任务星座，星座）**：具有 TaskStar 节点和依赖关系的 DAG 表示
3. **设备池管理器**：动态匹配任务到有能力的设备
4. **TaskOrchestrator（任务编排器）**：协调并行执行并处理数据流
5. **事件系统**：具有观察者模式的实时监控以实现适应
6. **设备智能体**：特定于平台的执行器（Windows 的 UFO²，Linux/macOS 的 shell 等）

**关键特征：**
- **基于星座的规划**，带任务依赖关系
- **并行 DAG 执行**以提高效率
- **多设备协调**跨异构平台
- **动态设备分配**，通过能力匹配
- **事件驱动架构**用于实时适应
- **容错性**，自动恢复

---

## 📊 功能矩阵

<div align="center">

| 功能 | UFO² 桌面智能体操作系统 | UFO³ Galaxy | 胜者 |
|---------|:--------------------:|:-----------:|:------:|
| **Windows 自动化** | ⭐⭐⭐⭐⭐ 优化 | ⭐⭐⭐⭐ 支持 | UFO² |
| **跨设备任务** | ❌ 不支持 | ⭐⭐⭐⭐⭐ 核心功能 | Galaxy |
| **设置复杂性** | ⭐⭐⭐⭐⭐ 非常简单 | ⭐⭐⭐ 中等 | UFO² |
| **学习曲线** | ⭐⭐⭐⭐⭐ 平缓 | ⭐⭐⭐ 中等 | UFO² |
| **任务复杂性** | ⭐⭐⭐ 良好 | ⭐⭐⭐⭐⭐ 优秀 | Galaxy |
| **并行执行** | ❌ 顺序 | ⭐⭐⭐⭐⭐ 原生 DAG | Galaxy |
| **生产就绪** | ⭐⭐⭐⭐⭐ 稳定 | ⭐⭐⭐ 积极开发 | UFO² |
| **监控工具** | ⭐⭐⭐ 日志 | ⭐⭐⭐⭐⭐ 实时可视化 | Galaxy |
| **API 灵活性** | ⭐⭐⭐ 良好 | ⭐⭐⭐⭐⭐ 广泛 | Galaxy |
| **社区支持** | ⭐⭐⭐⭐⭐ 已建立 | ⭐⭐⭐ 增长中 | UFO² |

</div>

---

## 🎯 用例指南

### 何时使用 UFO² 桌面智能体操作系统

✅ **适用于：**
- 📊 Excel/Word/PowerPoint 自动化
- 🌐 浏览器自动化（Edge、Chrome）
- 📁 文件系统操作
- ⚙️ Windows 系统配置
- 🎓 学习基于智能体的自动化
- ⚡ 快速、简单的任务
- 🏢 生产关键工作流（稳定）

**示例场景：**
```
✓ "在 Excel 中创建月度销售报告"
✓ "搜索研究论文并保存 PDF"
✓ "按文件类型整理下载文件夹"
✓ "在 Access 数据库中更新产品目录"
✓ "从 PDF 提取数据到 Excel"
```

---

### 何时使用 UFO³ Galaxy

✅ **适用于：**
- 🔗 **多设备工作流** - 跨异构平台的任务
- 📊 **复杂数据管道** - 跨不同系统的 ETL 过程
- 🤖 **并行任务执行** - 基于 DAG 的工作流，带依赖关系
- 🌍 **跨平台编排** - Windows、Linux、macOS、Android 协调
- 📈 **可扩展自动化** - 动态设备池管理
- 🔄 **自适应工作流** - 实时监控和恢复
- 🎯 **高级编排** - 基于星座的任务规划

**示例场景（来自 UFO³ 论文）：**
```
✓ "从 Windows Excel 提取数据，在 Linux 服务器上处理，在 Mac 上可视化"
✓ "在 Windows 上运行测试，部署到 Linux 生产环境，更新移动应用"
✓ "从多个设备收集日志，集中聚合和分析"
✓ "跨异构计算资源的分布式数据处理"
✓ "带设备特定测试的跨平台 CI/CD 管道"
✓ "多设备 IoT 编排和监控"
```

**关键优势：** 星座框架自动处理任务依赖关系、设备分配和并行执行。

---

### 混合方法（两全其美）

**UFO² 作为 Galaxy 设备智能体：**
Galaxy 可以利用 UFO² 作为专门的 Windows 设备智能体，将 Galaxy 的编排能力与 UFO² 经过验证的 Windows 自动化功能相结合。

---

## 💡 常见问题

<details>
<summary><strong>🤔 我应该使用 Galaxy 还是 UFO²？</strong></summary>

**从 UFO² 开始**，如果：
- 您只需要 Windows 自动化
- 您想要快速设置和学习
- 您需要生产稳定性
- 任务相对简单

**选择 Galaxy**，如果：
- 您需要跨设备协调
- 任务复杂且多步骤
- 您想要高级编排
- 您对积极开发感到满意

**混合方法**，如果：
- 您想要两全其美
- 一些任务简单（UFO²），一些复杂（Galaxy）
- 您正在逐步迁移

</details>

<details>
<summary><strong>⚠️ UFO² 会被弃用吗？</strong></summary>

**不会！** UFO² 已进入**长期支持（LTS）**状态：
- ✅ 积极维护
- ✅ 错误修复和安全更新
- ✅ 性能改进
- ✅ 完整的社区支持
- ✅ 没有弃用计划

UFO² 是 Windows 自动化的稳定、经过验证的解决方案。

</details>

<details>
<summary><strong>🔄 如何从 UFO² 迁移到 Galaxy？</strong></summary>

迁移是**渐进的和可选的**：

1. **阶段 1：学习** – 了解 Galaxy 概念
2. **阶段 2：实验** – 尝试使用 Galaxy 进行非关键任务
3. **阶段 3：混合** – 同时使用两个框架
4. **阶段 4：迁移** – 逐步将复杂任务移至 Galaxy

**无强制迁移！** 只要满足您的需求，就继续使用 UFO²。

有关详细信息，请参阅[迁移指南](./documents/docs/getting_started/migration_ufo2_to_galaxy.md)。

</details>

<details>
<summary><strong>🎯 Galaxy 能做 UFO² 做的所有事情吗？</strong></summary>

**功能上：是的。** Galaxy 可以使用 UFO² 作为 Windows 设备智能体。

**实际上：这取决于。**
- 对于**简单的 Windows 任务**：UFO² 独立更简单、更精简
- 对于**复杂工作流**：Galaxy 编排 UFO² 与其他设备智能体
- 对于**生产**：UFO² 提供经过验证的稳定性

**建议：** 使用正确的工具来完成工作。UFO² 可以独立工作或作为 Galaxy 的 Windows 设备智能体。

</details>

<details>
<summary><strong>📊 Galaxy 有多成熟？</strong></summary>

**状态：积极开发** 🚧

**稳定：**
- ✅ 核心架构
- ✅ DAG 编排
- ✅ 基本多设备支持
- ✅ 事件系统

**开发中：**
- 🔨 高级设备类型
- 🔨 增强监控
- 🔨 性能优化
- 🔨 扩展文档

**建议：** 非常适合实验和非关键工作流。对于生产，请考虑 UFO² 或混合方法。

</details>

<details>
<summary><strong>🔧 我可以扩展或自定义吗？</strong></summary>

**两个框架都是高度可扩展的：**

**UFO²：**
- 自定义操作和自动化器
- 自定义知识源（RAG）
- 自定义控件检测器
- 自定义评估指标

**Galaxy：**
- 自定义智能体
- 自定义设备类型
- 自定义编排策略
- 自定义可视化组件

有关扩展指南，请参阅各自的文档。

</details>

<details>
<summary><strong>🤝 我如何贡献？</strong></summary>

我们欢迎对 UFO² 和 Galaxy 的贡献！

**贡献方式：**
- 🐛 报告错误和问题
- 💡 建议功能和改进
- 📝 改进文档
- 🧪 添加测试和示例
- 🔧 提交拉取请求

有关指南，请参阅 [CONTRIBUTING.md](./CONTRIBUTING.md)。

</details>

---

## 📊 基准测试和评估

### UFO² 桌面智能体操作系统

**测试于：**
- ✅ [Windows Agent Arena (WAA)](https://github.com/nice-mee/WindowsAgentArena) – 154 个真实任务
- ✅ [OSWorld (Windows)](https://github.com/nice-mee/WindowsAgentArena/tree/2020-qqtcg/osworld) – 49 个跨应用任务

**性能：**
- Office 自动化的高成功率
- 稳健的控件检测
- 高效的多操作推测

**📖 [详细结果 →](./ufo/README_ZH.md#-评估)**

### UFO³ Galaxy

**在多设备基准测试上进行评估：**

根据 [UFO³ 技术论文](https://arxiv.org/abs/[TBD])：

- ✅ **跨设备工作流**：50+ 个复杂的多设备场景
- ✅ **异构平台**：Windows、Linux、macOS、Android 集成
- ✅ **并行执行**：基于 DAG 的工作流，带依赖管理
- ✅ **容错性**：自动错误恢复和任务重新调度

**关键指标：**
- **任务完成率**：跨多个设备的成功编排
- **并行效率**：基于 DAG 的并行执行的加速
- **设备分配准确性**：正确的能力匹配和选择
- **容错恢复**：自动检测和从设备故障中恢复

**研究亮点：**
1. **新颖的星座框架**：首个用于 GUI 智能体的多设备编排系统
2. **动态设备分配**：智能的基于能力的任务到设备匹配
3. **实时适应**：事件驱动的监控和工作流调整
4. **异构集成**：跨不同平台的无缝协调

**📖 [完整评估详情 →](./galaxy/benchmarks/)** | **📄 [阅读论文 →](https://arxiv.org/abs/[TBD])**

**状态：** 积极的研究项目，正在进行基准测试开发

---

## 🗺️ 路线图

### UFO² 桌面智能体操作系统（稳定/LTS）
- ✅ 长期支持和维护
- ✅ 错误修复和安全更新
- ✅ 性能优化
- ✅ 与 Galaxy 集成作为 Windows 设备智能体
- 🔜 Galaxy 的增强设备智能体功能
- 🔜 画中画桌面模式

### UFO³ Galaxy（积极开发）
- ✅ **星座框架** - 基于 DAG 的任务规划 **[完成]**
- ✅ **ConstellationAgent** - 智能任务分解 **[完成]**
- ✅ **多设备协调** - 异构平台支持 **[完成]**
- ✅ **事件驱动架构** - 带观察者的实时监控 **[完成]**
- ✅ **动态设备分配** - 基于能力的匹配 **[完成]**
- 🔄 **高级设备类型** - 移动、Web、IoT 智能体 **[进行中]**
- 🔄 **增强可视化** - 交互式星座图 **[进行中]**
- 🔄 **性能优化** - 并行执行效率 **[进行中]**
- 🔜 **容错性增强** - 高级恢复策略
- 🔜 **跨设备数据流** - 优化的设备间通信
- 🔜 自动调试工具包

**图例：** ✅ 完成 | 🔄 进行中 | 🔜 计划

---

## 📢 最新更新

### 2025-11 – UFO³ Galaxy 框架发布 🌌
**重大研究突破：** 多设备编排系统

- 🌟 **星座框架**：用于多设备工作流的新颖基于 DAG 的任务规划
- 🎯 **ConstellationAgent**：具有依赖分析的智能任务分解
- 🔗 **跨平台集成**：跨 Windows、Linux、macOS、Android 的无缝编排
- ⚡ **动态设备分配**：基于能力的匹配和资源分配
- 📊 **实时监控**：具有观察者模式的事件驱动架构
- 🛡️ **容错性**：自动错误检测和恢复机制
- 📄 **研究论文**：[UFO³: Weaving the Digital Agent Galaxy](https://arxiv.org/abs/[TBD])

**关键创新：**
- 首个用于 GUI 智能体的多设备编排框架
- 用于分布式任务工作流的星座（星座）隐喻
- 具有统一接口的异构平台协调
- 并行 DAG 执行以提高效率

### 2025-04 – UFO² v2.0.0
- 📅 UFO² 桌面智能体操作系统发布
- 🏗️ 具有 AgentOS 概念的增强架构
- 📄 [技术报告](https://arxiv.org/pdf/2504.14603)发布
- ✅ 进入长期支持（LTS）状态

### 2024-02 – 原始 UFO
- 🎈 第一个 UFO 版本 - Windows 的以 UI 为中心的智能体
- 📄 [原始论文](https://arxiv.org/abs/2402.07939)
- 🌍 广泛的媒体报道和采用

---

## 📚 引用

如果您在研究中使用 UFO³ Galaxy 或 UFO²，请引用相关论文：

### UFO³ Galaxy 框架（2025）
```bibtex
@article{zhang2025ufo3,
  title   = {{UFO³: Weaving the Digital Agent Galaxy}},
  author  = {Zhang, Chaoyun and [Authors TBD]},
  journal = {arXiv preprint arXiv:[TBD]},
  year    = {2025},
  note    = {Multi-device orchestration framework with Constellation-based planning}
}
```

**论文亮点：**
- 用于多设备任务编排的新颖星座框架
- 用于将任务智能分解为 DAG 工作流的 ConstellationAgent
- 通过基于能力的匹配进行动态设备分配
- 用于实时监控和适应的事件驱动架构
- 对跨平台工作流和异构设备集成的评估

### UFO² 桌面智能体操作系统（2025）
```bibtex
@article{zhang2025ufo2,
  title   = {{UFO2: The Desktop AgentOS}},
  author  = {Zhang, Chaoyun and Huang, He and Ni, Chiming and Mu, Jian and Qin, Si and He, Shilin and Wang, Lu and Yang, Fangkai and Zhao, Pu and Du, Chao and Li, Liqun and Kang, Yu and Jiang, Zhao and Zheng, Suzhen and Wang, Rujia and Qian, Jiaxu and Ma, Minghua and Lou, Jian-Guang and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei},
  journal = {arXiv preprint arXiv:2504.14603},
  year    = {2025}
}
```

### 原始 UFO（2024）
```bibtex
@article{zhang2024ufo,
  title   = {{UFO: A UI-Focused Agent for Windows OS Interaction}},
  author  = {Zhang, Chaoyun and Li, Liqun and He, Shilin and Zhang, Xu and Qiao, Bo and Qin, Si and Ma, Minghua and Kang, Yu and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei and Zhang, Qi},
  journal = {arXiv preprint arXiv:2402.07939},
  year    = {2024}
}
```

---

## 🌐 媒体和社区

**媒体报道：**
- [微软正式开源UFO²，Windows桌面迈入「AgentOS 时代」](https://www.jiqizhixin.com/articles/2025-05-06-13)
- [Microsoft's UFO: Smarter Windows Experience](https://the-decoder.com/microsofts-ufo-abducts-traditional-user-interfaces-for-a-smarter-windows-experience/)
- [下一代Windows系统曝光](https://baijiahao.baidu.com/s?id=1790938358152188625)
- **[更多报道 →](./ufo/README_ZH.md#-媒体报道)**

**社区：**
- 💬 [GitHub 讨论](https://github.com/microsoft/UFO/discussions)
- 🐛 [问题跟踪器](https://github.com/microsoft/UFO/issues)
- 📧 电子邮件：[ufo-agent@microsoft.com](mailto:ufo-agent@microsoft.com)
- 📺 [YouTube 频道](https://www.youtube.com/watch?v=QT_OhygMVXU)

---

## 🎨 相关项目和研究

**Microsoft Research：**
- **[TaskWeaver](https://github.com/microsoft/TaskWeaver)** – 用于数据分析和任务自动化的代码优先 LLM 智能体框架
- **[AutoGen](https://github.com/microsoft/autogen)** – 用于构建 LLM 应用程序的多智能体对话框架

**GUI 智能体研究：**
- **[基于 LLM 的 GUI 智能体综述](https://github.com/vyokky/LLM-Brained-GUI-Agents-Survey)** – GUI 自动化智能体的全面综述
- **[交互式综述网站](https://vyokky.github.io/LLM-Brained-GUI-Agents-Survey/)** – 探索最新的 GUI 智能体研究和发展

**多智能体系统：**
- **UFO³ Galaxy** 代表了多设备编排的新方法，引入了星座框架，用于跨平台协调异构智能体
- 基于多智能体协调研究，同时解决跨设备 GUI 自动化的独特挑战

**基准测试：**
- **[Windows Agent Arena (WAA)](https://github.com/nice-mee/WindowsAgentArena)** – Windows 自动化智能体的评估基准
- **[OSWorld](https://github.com/nice-mee/WindowsAgentArena/tree/2020-qqtcg/osworld)** – 跨应用程序任务评估套件

---

## ⚠️ 免责声明和许可证

**免责声明：** 使用本软件即表示您承认并同意 [DISCLAIMER.md](./DISCLAIMER.md) 中的条款。

**许可证：** 本项目根据 [MIT 许可证](LICENSE) 授权。

**商标：** Microsoft 商标的使用遵循 [Microsoft 商标指南](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general)。

---

<div align="center">

## 🚀 准备开始了吗？

<table>
<tr>
<td align="center" width="50%">

### 🌌 探索 Galaxy
**多设备编排**

[![开始 Galaxy](https://img.shields.io/badge/Start-Galaxy-blue?style=for-the-badge)](./galaxy/README_ZH.md)

</td>
<td align="center" width="50%">

### 🪟 试试 UFO²
**Windows 桌面智能体**

[![开始 UFO²](https://img.shields.io/badge/Start-UFO²-green?style=for-the-badge)](./ufo/README_ZH.md)

</td>
</tr>
</table>

---

<sub>© Microsoft 2025 | UFO³ 是一个开源研究项目</sub>

<sub>⭐ 在 GitHub 上给我们加星 | 🤝 贡献 | 📖 阅读文档 | 💬 加入讨论</sub>

</div>

---

<p align="center">
  <img src="assets/logo3.png" alt="UFO logo" width="60">
  <br>
  <em>从单智能体到数字星系</em>
  <br>
  <strong>UFO³ - 编织智能自动化的未来</strong>
</p>
