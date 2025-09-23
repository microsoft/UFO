# TaskConstellation Editor - Command Pattern Implementation

## 概述

TaskConstellation Editor 采用命令模式实现对 TaskConstellation 的一系列增删改操作，包括节点（任务）和边（依赖关系）的管理，以及整体构建等操作。

## 主要特性

### 🎯 核心功能
- **任务管理**：创建、更新、删除任务
- **依赖管理**：添加、修改、删除任务依赖关系
- **批量操作**：批量构建、清空整个星座
- **文件操作**：保存到/从 JSON 文件加载星座
- **撤销/重做**：完整的命令历史和撤销/重做支持

### 🏗️ 架构模式
- **命令模式**：所有操作都封装为可撤销的命令
- **观察者模式**：支持操作事件监听
- **组合模式**：支持子图创建和星座合并

## 使用示例

### 基本任务操作

```python
from ufo.galaxy.constellation.editor import ConstellationEditor

# 创建编辑器
editor = ConstellationEditor()

# 创建和添加任务
task1 = editor.create_and_add_task(
    task_id="task1",
    description="第一个任务",
    priority=TaskPriority.HIGH
)

# 更新任务
editor.update_task("task1", description="更新后的任务描述")

# 获取任务
task = editor.get_task("task1")

# 删除任务
editor.remove_task("task1")
```

### 依赖关系管理

```python
# 创建两个任务
editor.create_and_add_task("task1", "任务一")
editor.create_and_add_task("task2", "任务二")

# 添加依赖关系
dependency = editor.create_and_add_dependency(
    from_task_id="task1",
    to_task_id="task2",
    dependency_type="UNCONDITIONAL"
)

# 更新依赖
editor.update_dependency(
    dependency.line_id,
    condition_description="新的条件描述"
)

# 删除依赖
editor.remove_dependency(dependency.line_id)
```

### 撤销/重做操作

```python
# 执行一些操作
editor.create_and_add_task("task1", "测试任务")
editor.create_and_add_task("task2", "另一个任务")

# 检查撤销状态
print(f"可以撤销: {editor.can_undo()}")
print(f"撤销描述: {editor.get_undo_description()}")

# 撤销最后一个操作
if editor.can_undo():
    editor.undo()

# 重做操作
if editor.can_redo():
    editor.redo()

# 获取操作历史
history = editor.get_history()
for command_desc in history:
    print(f"历史操作: {command_desc}")
```

### 批量操作

```python
# 批量构建星座
tasks_config = [
    {"task_id": "A", "description": "任务 A"},
    {"task_id": "B", "description": "任务 B"},
    {"task_id": "C", "description": "任务 C"}
]

dependencies_config = [
    {
        "from_task_id": "A",
        "to_task_id": "B",
        "dependency_type": "UNCONDITIONAL"
    },
    {
        "from_task_id": "B", 
        "to_task_id": "C",
        "dependency_type": "UNCONDITIONAL"
    }
]

# 构建星座
editor.build_from_tasks_and_dependencies(
    tasks_config,
    dependencies_config,
    metadata={"created_by": "editor_example"}
)

# 验证结构
is_valid, errors = editor.validate_constellation()
if is_valid:
    print("星座结构有效")
    topo_order = editor.get_topological_order()
    print(f"拓扑排序: {topo_order}")
else:
    print(f"星座结构无效: {errors}")
```

### 文件操作

```python
# 保存到文件
editor.save_constellation("my_constellation.json")

# 从文件加载
editor2 = ConstellationEditor()
editor2.load_constellation("my_constellation.json")

# 或者使用 JSON 字符串
json_str = editor.constellation.to_json()
editor3 = ConstellationEditor()
editor3.load_from_json_string(json_str)
```

### 高级操作

```python
# 创建子图
subgraph_editor = editor.create_subgraph(["task1", "task2", "task3"])

# 合并星座
other_editor = ConstellationEditor()
other_editor.create_and_add_task("external_task", "外部任务")

editor.merge_constellation(other_editor, prefix="merged_")

# 批量操作
operations = [
    lambda e: e.create_and_add_task("batch1", "批量任务1"),
    lambda e: e.create_and_add_task("batch2", "批量任务2"),
    lambda e: e.create_and_add_dependency("batch1", "batch2")
]

results = editor.batch_operations(operations)
```

### 观察者模式

```python
def task_observer(editor, command, result):
    print(f"操作执行: {command}")
    print(f"结果: {result}")

# 添加观察者
editor.add_observer(task_observer)

# 执行操作（会触发观察者）
editor.create_and_add_task("observed_task", "被观察的任务")

# 移除观察者
editor.remove_observer(task_observer)
```

### 统计和分析

```python
# 获取统计信息
stats = editor.get_statistics()
print(f"任务数量: {stats['total_tasks']}")
print(f"依赖数量: {stats['total_dependencies']}")
print(f"执行次数: {stats['editor_execution_count']}")

# 获取就绪任务
ready_tasks = editor.get_ready_tasks()
print(f"就绪任务: {[t.task_id for t in ready_tasks]}")

# 检查循环依赖
has_cycles = editor.has_cycles()
if has_cycles:
    print("警告: 星座中存在循环依赖")
```

## 命令类型

### 任务命令
- `AddTaskCommand`: 添加任务
- `RemoveTaskCommand`: 删除任务
- `UpdateTaskCommand`: 更新任务

### 依赖命令
- `AddDependencyCommand`: 添加依赖
- `RemoveDependencyCommand`: 删除依赖
- `UpdateDependencyCommand`: 更新依赖

### 批量命令
- `BuildConstellationCommand`: 批量构建星座
- `ClearConstellationCommand`: 清空星座

### 文件命令
- `LoadConstellationCommand`: 从文件加载
- `SaveConstellationCommand`: 保存到文件

## 错误处理

所有命令都会进行适当的验证和错误处理：

```python
try:
    # 尝试添加重复任务
    editor.create_and_add_task("duplicate", "重复任务")
    editor.create_and_add_task("duplicate", "重复任务")  # 会抛出异常
except CommandExecutionError as e:
    print(f"命令执行失败: {e}")

try:
    # 尝试创建循环依赖
    editor.create_and_add_task("cycle1", "循环任务1")
    editor.create_and_add_task("cycle2", "循环任务2")
    editor.create_and_add_dependency("cycle1", "cycle2")
    editor.create_and_add_dependency("cycle2", "cycle1")  # 会抛出异常
except CommandExecutionError as e:
    print(f"检测到循环依赖: {e}")
```

## 最佳实践

1. **使用撤销功能**: 在执行批量操作前检查撤销状态
2. **验证结构**: 定期验证星座结构的有效性
3. **观察者监听**: 使用观察者模式监控重要操作
4. **错误处理**: 始终包装可能失败的操作在 try-catch 中
5. **文件备份**: 在大型修改前保存当前状态到文件

这个命令模式实现提供了完整的 TaskConstellation 操作接口，支持撤销/重做、批量操作和高级星座管理功能。
