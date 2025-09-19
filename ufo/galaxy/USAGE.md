# Galaxy Framework CLI Usage Guide

Galaxy框架现在提供了完整的命令行界面，支持DAG-based任务编排和constellation执行，并采用了Rich库实现美观的彩色输出界面。

## 🌟 界面特性

### Rich UI 增强
- 🎨 **彩色输出**: 使用Rich库提供美观的彩色界面
- 📊 **表格显示**: 状态和结果以表格形式清晰展示  
- 🎯 **进度指示**: 实时进度条和旋转器显示
- 📦 **面板布局**: 信息以面板形式组织，易于阅读
- 🎪 **交互提示**: Rich风格的命令行提示

## 🚀 主要入口点

### 1. 主CLI入口 (推荐)
```bash
# 从项目根目录执行
python -m ufo.galaxy [选项]
```

### 2. 快速入口脚本
```bash
# 从galaxy目录执行
cd ufo/galaxy
python galaxy.py [参数]
```

### 3. 包模式运行
```bash
# 从项目根目录执行
python -m ufo.galaxy
```

## 📋 CLI 选项

### 主要参数
- `--request TEXT`: 任务请求文本
- `--session-name NAME`: Galaxy会话名称
- `--task-name NAME`: 任务名称
- `--interactive`: 启动交互模式
- `--mock-agent`: 使用模拟代理进行测试

### 配置参数
- `--max-rounds N`: 每个会话的最大轮次 (默认: 10)
- `--log-level LEVEL`: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL, OFF)
- `--output-dir DIR`: 日志和结果输出目录 (默认: ./logs)

### 帮助
- `--help`: 显示帮助信息

## 💡 使用示例

### 单次请求执行
```bash
# 执行单个任务请求
python -m ufo.galaxy --request "Create a data processing pipeline" --mock-agent

# 自定义会话名称和任务名称
python -m ufo.galaxy --request "Build ML workflow" --session-name "ml_session" --task-name "ml_task" --mock-agent
```

### 交互模式
```bash
# 启动交互模式
python -m ufo.galaxy --interactive --mock-agent

# 在交互模式中的命令:
# - 输入任务请求
# - 'help': 显示可用命令
# - 'status': 显示会话状态
# - 'quit' 或 'exit': 退出
```

### 配置选项
```bash
# 设置日志级别和输出目录
python -m ufo.galaxy --request "Task" --log-level DEBUG --output-dir ./my_logs --mock-agent

# 设置最大轮次
python -m ufo.galaxy --request "Task" --max-rounds 5 --mock-agent
```

## 🛠️ 开发和测试

### Mock Agent模式
推荐在开发和测试时使用 `--mock-agent` 标志：
```bash
python -m ufo.galaxy --request "Test task" --mock-agent
```

### 输出结果
- 日志文件保存在指定的输出目录
- 执行结果以JSON格式保存
- 交互模式提供实时状态反馈

## 🎯 功能特性

### 已实现功能
- ✅ 单次请求处理
- ✅ 交互模式
- ✅ 会话管理
- ✅ Mock agent支持
- ✅ 日志和结果输出
- ✅ 可配置的参数

### 支持的工作流
- DAG-based任务编排
- Constellation执行
- 设备管理和分配
- 任务状态监控
- 错误处理和恢复

## 🔧 故障排除

### 常见问题
1. **配置文件未找到**: 这是正常的警告，系统会使用环境变量
2. **代理跳过**: 第三方代理被跳过是正常行为
3. **设备分配警告**: 在mock模式下没有真实设备是正常的

### 调试模式
```bash
# 启用详细日志
python -m ufo.galaxy --request "Task" --log-level DEBUG --mock-agent
```

## 📚 更多信息

- Galaxy框架基于UFO项目构建
- 支持DAG-based工作流编排
- 提供constellation执行引擎
- 集成设备管理和任务分配
- 支持扩展和自定义代理

## 🎪 示例会话

```bash
$ python -m ufo.galaxy --interactive --mock-agent

🌌 Galaxy Framework - Interactive Mode
============================================================
Enter your requests below. Type 'quit' or 'exit' to stop.
Type 'help' for available commands.
============================================================

Galaxy[0]> Create a web scraping pipeline with data validation
📝 Processing request: Create a web scraping pipeline with data validation...
✅ Request processed successfully in 0.15s

Galaxy[1]> status
📊 Session Status:
  Session ID: galaxy_session_20250919_170723
  Rounds: 1
  Agent Status: finished

Galaxy[2]> quit
👋 Goodbye!
```

---

**注意**: 目前推荐使用主CLI入口点 (`python -m ufo.galaxy`) 和mock agent模式进行测试。
