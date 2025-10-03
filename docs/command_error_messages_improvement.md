# Command Error Messages Improvement

## 概述
为了改进调试体验，我们为所有 Command 类添加了详细的错误原因说明。现在当命令无法执行时，错误信息会明确说明具体原因。

## 修改内容

### 1. `command_interface.py`
在 `ICommand` 接口中添加了 `get_cannot_execute_reason()` 方法，提供默认实现：
```python
def get_cannot_execute_reason(self) -> str:
    """获取命令无法执行的详细原因"""
    return "Command cannot be executed"
```

### 2. `command_invoker.py`
修改了 `execute()` 方法，在抛出异常时调用 `get_cannot_execute_reason()` 获取详细原因：
```python
if not command.can_execute():
    reason = command.get_cannot_execute_reason()
    raise CommandExecutionError(
        command, 
        f"Command cannot be executed: {command.description}. Reason: {reason}"
    )
```

### 3. `commands.py`
为所有命令类实现了 `get_cannot_execute_reason()` 方法，根据 `can_execute()` 的逻辑返回具体原因。

## 各命令的错误原因

### AddTaskCommand
- ✅ Task ID 已存在: `"Task with ID '{task_id}' already exists in constellation"`
- ✅ 命令已执行: `"Command has already been executed"`

### RemoveTaskCommand
- ✅ Task 不存在: `"Task with ID '{task_id}' not found in constellation. Existing task IDs: [...]"`
- ✅ Task 正在运行: `"Cannot remove task '{task_id}' because it is currently running"`
- ✅ 命令已执行: `"Command has already been executed"`

### UpdateTaskCommand
- ✅ Task 不存在: `"Task with ID '{task_id}' not found in constellation. Existing task IDs: [...]"`
- ✅ 命令已执行: `"Command has already been executed"`

### AddDependencyCommand
- ✅ Dependency ID 已存在: `"Dependency with ID '{line_id}' already exists in constellation"`
- ✅ 源任务不存在: `"Source task '{from_task_id}' not found in constellation. Existing task IDs: [...]"`
- ✅ 目标任务不存在: `"Target task '{to_task_id}' not found in constellation. Existing task IDs: [...]"`
- ✅ 命令已执行: `"Command has already been executed"`

### RemoveDependencyCommand
- ✅ Dependency 不存在: `"Dependency with ID '{dependency_id}' not found in constellation. Existing dependency IDs: [...]"`
- ✅ 命令已执行: `"Command has already been executed"`

### UpdateDependencyCommand
- ✅ Dependency 不存在: `"Dependency with ID '{dependency_id}' not found in constellation. Existing dependency IDs: [...]"`
- ✅ 命令已执行: `"Command has already been executed"`

### BuildConstellationCommand
- ✅ 配置为空或无效: `"Configuration is empty or invalid"`
- ✅ 命令已执行: `"Command has already been executed"`

### ClearConstellationCommand
- ✅ 命令已执行: `"Command has already been executed"`

### LoadConstellationCommand
- ✅ 文件不存在: `"File '{file_path}' not found"`
- ✅ 命令已执行: `"Command has already been executed"`

### SaveConstellationCommand
- ✅ 命令已执行: `"Command has already been executed"`

## 使用示例

### 示例 1: Task 不存在
**之前的错误信息：**
```
CommandExecutionError: Command cannot be executed: Remove task: task_999
```

**现在的错误信息：**
```
CommandExecutionError: Command cannot be executed: Remove task: task_999. 
Reason: Task with ID 'task_999' not found in constellation. Existing task IDs: ['task_001', 'task_002', 'task_003']
```

### 示例 2: Task ID 已存在
**之前的错误信息：**
```
CommandExecutionError: Command cannot be executed: Add task: task_123
```

**现在的错误信息：**
```
CommandExecutionError: Command cannot be executed: Add task: task_123. 
Reason: Task with ID 'task_123' already exists in constellation
```

### 示例 3: Dependency 的源任务不存在
**之前的错误信息：**
```
CommandExecutionError: Command cannot be executed: Add dependency: task_A -> task_B
```

**现在的错误信息：**
```
CommandExecutionError: Command cannot be executed: Add dependency: task_A -> task_B. 
Reason: Source task 'task_A' not found in constellation. Existing task IDs: ['task_001', 'task_002', 'task_003']
```

## 优势
1. **更好的调试体验**: 错误信息明确指出了失败的具体原因
2. **快速定位问题**: 当 ID 不存在时，直接显示所有可用的 ID 列表
3. **节省时间**: 开发者不需要深入代码或查询数据库就能了解当前状态
4. **减少试错**: 看到现有 ID 列表后，可以立即使用正确的 ID
5. **易于维护**: 每个命令的 `get_cannot_execute_reason()` 方法与其 `can_execute()` 逻辑保持一致
6. **可扩展**: 未来添加新命令时，只需实现 `get_cannot_execute_reason()` 方法即可

## 向后兼容性
这些更改完全向后兼容：
- `ICommand` 接口的 `get_cannot_execute_reason()` 提供了默认实现
- 所有现有命令都已更新实现了该方法
- 调用方代码无需修改
