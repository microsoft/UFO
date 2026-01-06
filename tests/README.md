# DAG可视化测试套件

本目录包含了用于测试DAG可视化功能的完整测试套件。

## 目录结构

```
tests/
├── run_dag_tests.py           # 主测试运行器
├── visualization/             # 可视化功能测试
│   ├── test_dag_simple.py     # 简单DAG测试
│   ├── test_dag_mock.py       # 模拟DAG可视化测试
│   └── test_dag_demo.py       # 交互式DAG演示
└── integration/               # 集成测试
    └── test_e2e_galaxy.py     # 端到端Galaxy框架测试
```

## 测试说明

### 1. 简单DAG测试 (`test_dag_simple.py`)
- **目的**: 验证基本的DAG可视化功能
- **特点**: 最小化测试，快速验证核心功能
- **运行时间**: ~5秒

### 2. 模拟DAG可视化测试 (`test_dag_mock.py`)
- **目的**: 使用模拟类测试完整的DAG生命周期
- **特点**: 包含任务创建、依赖添加、执行模拟
- **运行时间**: ~10秒

### 3. 交互式DAG演示 (`test_dag_demo.py`)
- **目的**: 展示所有可视化模式和功能
- **特点**: 包含用户交互，演示不同的可视化视图
- **运行时间**: 变化（取决于用户交互）

### 4. 端到端Galaxy测试 (`test_e2e_galaxy.py`)
- **目的**: 完整的系统集成测试
- **特点**: 测试真实的Galaxy框架工作流程
- **运行时间**: ~15秒

## 如何运行测试

### 运行所有测试
```bash
# 在UFO2根目录下
python tests/run_dag_tests.py
```

### 运行单个测试
```bash
# 简单测试
python tests/visualization/test_dag_simple.py

# 模拟DAG测试
python tests/visualization/test_dag_mock.py

# 交互式演示
python tests/visualization/test_dag_demo.py

# 端到端测试
python tests/integration/test_e2e_galaxy.py
```

## 预期输出

所有测试都应该显示以下类型的可视化输出：

### 1. 星座概览
```
─────── Task Constellation Overview ───────
╭────────── 📊 Constellation Info ───────────╮ ╭─ 📈 Statistics ─╮
│ ID: constellation_20250919_183339          │ │ Total Tasks: 5  │
│ Name: Sample DAG Demo                      │ │ Dependencies: 4 │
│ State: CREATED                             │ │ ✅ Completed: 0 │
╰────────────────────────────────────────────╯ ╰─────────────────╯
```

### 2. DAG拓扑图
```
📊 DAG Topology
🌌 Task Constellation
├── Layer 1
│   └── ⭕ task_1 (Initialize Project)
├── Layer 2
│   └── ⭕ task_2 (Load Data)
│       └── Dependencies: task_1
```

### 3. 任务详情表
```
📋 Task Details
╭──────────────┬───────────────┬──────────────┬──────────┬─────────────╮
│ ID           │ Name          │    Status    │ Priority │ Dependencies│
├──────────────┼───────────────┼──────────────┼──────────┼─────────────┤
│ task_1       │ Initialize    │  ⭕ pending  │    HIGH  │ none        │
╰──────────────┴───────────────┴──────────────┴──────────┴─────────────╯
```

## 故障排除

### 常见问题

1. **导入错误**
   ```
   ❌ Import error: No module named 'ufo.galaxy.visualization.dag_visualizer'
   ```
   - 检查是否在正确的目录下运行测试
   - 确保所有依赖模块都已正确安装

2. **可视化器加载失败**
   ```
   ❌ Could not import DAGVisualizer: ...
   ```
   - 检查Rich库是否安装：`pip install rich`
   - 验证DAGVisualizer类是否存在

3. **路径问题**
   - 确保从UFO2根目录运行测试
   - 检查Python路径是否正确设置

### 调试模式

如果测试失败，可以启用调试模式：

```python
# 在测试文件开头添加
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 测试要求

### 环境要求
- Python 3.8+
- Rich库用于控制台可视化
- UFO2框架的所有依赖

### 系统要求
- 支持Unicode字符的控制台
- 彩色输出支持（推荐）

## 贡献指南

### 添加新测试
1. 在相应目录下创建新的测试文件
2. 遵循现有的命名约定：`test_<功能名>.py`
3. 在`run_dag_tests.py`中添加新测试的配置
4. 更新本README文档

### 测试标准
- 每个测试都应该有清晰的目的说明
- 包含适当的错误处理
- 提供有意义的输出信息
- 运行时间应该合理（通常<30秒）

## 更新历史

- **2025-09-19**: 初始版本，包含四个核心测试
- **2025-09-19**: 添加了测试运行器和完整文档
