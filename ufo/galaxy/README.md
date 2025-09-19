# UFO Galaxy Framework

UFO Galaxy Framework 是一个基于DAG的任务编排和设备管理框架，现在提供了完整的命令行界面支持。

## 🌟 主要特性

- **Rich UI界面**: 使用Rich库提供美观的彩色命令行界面
- **DAG-based工作流编排**: 自动将用户请求转换为有向无环图（DAG）工作流
- **Constellation执行引擎**: 高效的任务调度和执行引擎
- **设备管理**: 智能设备分配和资源管理
- **交互式CLI**: 支持命令行交互和批处理模式，带有Rich面板和表格
- **WeaverAgent**: 智能代理用于任务分解和编排
- **实时进度**: Rich进度条和状态指示器

## 🚀 快速开始

### 安装和运行
```bash
# 克隆项目
cd UFO2

# 运行单个任务
python -m ufo.galaxy --request "Create a data processing pipeline" --mock-agent

# 启动交互模式
python -m ufo.galaxy --interactive --mock-agent
```

### 基本用法
```bash
# 查看帮助
python -m ufo.galaxy --help

# 执行任务
python -m ufo.galaxy --request "Your task description" --mock-agent

# 自定义会话
python -m ufo.galaxy --request "Task" --session-name "my_session" --mock-agent
```

## 📁 项目结构

```
ufo/galaxy/
├── __init__.py              # 主包导入
├── __main__.py              # 包执行入口
├── galaxy_client.py         # 主CLI客户端
├── galaxy.py                # 快速入口脚本
├── USAGE.md                 # 详细使用指南
├── constellation/           # DAG编排和执行
├── agents/                  # WeaverAgent实现
├── session/                 # Galaxy会话管理
├── client/                  # 设备和constellation客户端
└── core/                    # 核心类型和接口
```

## 🎯 核心组件

### GalaxyClient
主要的CLI客户端，提供:
- 会话管理
- 请求处理
- 交互模式
- 结果输出

### WeaverAgent
智能代理，负责:
- 任务分解
- DAG生成
- 工作流编排

### TaskOrchestration
任务编排器，支持:
- DAG执行
- 设备分配
- 状态监控

### ModularConstellationClient
模块化客户端，管理:
- 设备连接
- 任务分发
- 结果收集

## 📋 CLI选项详解

| 选项 | 描述 | 默认值 |
|------|------|--------|
| `--request` | 任务请求文本 | - |
| `--interactive` | 启动交互模式 | False |
| `--session-name` | 会话名称 | 自动生成 |
| `--task-name` | 任务名称 | galaxy_task |
| `--mock-agent` | 使用模拟代理 | False |
| `--max-rounds` | 最大轮次 | 10 |
| `--log-level` | 日志级别 | INFO |
| `--output-dir` | 输出目录 | ./logs |

## 🛠️ 开发模式

### Mock Agent
推荐在开发时使用mock agent:
```bash
python -m ufo.galaxy --request "Test task" --mock-agent
```

### 调试模式
启用详细日志:
```bash
python -m ufo.galaxy --request "Task" --log-level DEBUG --mock-agent
```

## 📊 执行结果

Galaxy框架会输出:
- 执行状态和时间
- DAG统计信息
- 任务结果
- 错误和警告信息
- JSON格式的详细结果

## 🎪 示例

### 数据处理管道
```bash
python -m ufo.galaxy --request "Create a data processing pipeline with validation and transformation" --mock-agent
```

### 机器学习工作流
```bash
python -m ufo.galaxy --request "Build a machine learning workflow with training and evaluation" --mock-agent
```

### 网页抓取系统
```bash
python -m ufo.galaxy --request "Design a web scraping system with data validation" --mock-agent
```

## 🔗 相关文档

- [详细使用指南](USAGE.md)
- [UFO项目主页](../README.md)
- [API文档](docs/)

---

**注意**: 当前版本建议使用 `--mock-agent` 标志进行测试和开发。
