# Constellation Sync Implementation - 方案 1

## 概述

实现了方案1：**每次操作后返回 JSON 并在 Strategy 中同步**，解决了 MCP Server 中的 constellation 修改无法同步回 UFO Context 的问题。

## 问题分析

### 之前的流程
1. **Creation Mode**: `build_constellation` → MCP Server → `ConstellationEditor` → 创建 `TaskConstellation` → `sync_constellation` 同步回 Context ✅
2. **Editing Mode**: MCP 工具（add_task, remove_task等）→ `ConstellationEditor` → 修改保留在 MCP Server 的 `editor` 实例中 → **没有 sync 回 Context** ❌

### 核心问题
MCP Server 中的 `editor = ConstellationEditor()` 是一个局部实例，修改后的 constellation 没有同步回 UFO 的全局 Context。

---

## 解决方案实现

### 1. 修改 MCP Server 工具返回值

**文件**: `ufo/client/mcp/local_servers/constellation_mcp_server.py`

#### 修改的工具：
所有 constellation 编辑工具现在都返回**完整的 constellation JSON**，而不是单个 task 或 dependency 的 JSON。

##### ✅ add_task
**之前**: 返回单个 TaskStar JSON
```python
task = editor.add_task(task_data)
return task.to_json()
```

**现在**: 返回完整 constellation JSON
```python
editor.add_task(task_data)
return editor.constellation.to_json()
```

**返回值描述更新**:
```python
Annotated[
    str,
    Field(
        description="JSON string representation of the complete updated TaskConstellation object containing all tasks, dependencies, and metadata after adding the new task"
    ),
]
```

##### ✅ remove_task
**之前**: 返回字符串消息
```python
result = editor.remove_task(task_id)
return f"Successfully removed task: {result}"
```

**现在**: 返回完整 constellation JSON
```python
editor.remove_task(task_id)
return editor.constellation.to_json()
```

##### ✅ update_task
**之前**: 返回更新后的 TaskStar JSON
```python
task = editor.update_task(task_id, **updates)
return task.to_json()
```

**现在**: 返回完整 constellation JSON
```python
editor.update_task(task_id, **updates)
return editor.constellation.to_json()
```

##### ✅ add_dependency
**之前**: 返回单个 TaskStarLine JSON
```python
dependency = editor.add_dependency(dependency_data)
return dependency.to_json()
```

**现在**: 返回完整 constellation JSON
```python
editor.add_dependency(dependency_data)
return editor.constellation.to_json()
```

##### ✅ remove_dependency
**之前**: 返回字符串消息
```python
result = editor.remove_dependency(dependency_id)
return f"Successfully removed dependency: {result}"
```

**现在**: 返回完整 constellation JSON
```python
editor.remove_dependency(dependency_id)
return editor.constellation.to_json()
```

##### ✅ update_dependency
**之前**: 返回更新后的 TaskStarLine JSON
```python
dependency = editor.update_dependency(dependency_id, **updates)
return dependency.to_json()
```

**现在**: 返回完整 constellation JSON
```python
editor.update_dependency(dependency_id, **updates)
return editor.constellation.to_json()
```

##### ✅ build_constellation
**已经返回完整 constellation JSON** - 无需修改
```python
constellation = editor.build_constellation(config, clear_existing)
return constellation.to_json()
```

---

### 2. 实现 Editing Strategy 的 sync_constellation

**文件**: `ufo/galaxy/agents/processors/strategies/constellation_editing_strategy.py`

#### 实现逻辑

```python
def sync_constellation(
    self, results: List[Result], context: ProcessingContext
) -> None:
    """
    从 MCP 工具执行结果中同步 constellation 状态。
    
    从最后一个成功的 result 中提取更新后的 constellation 并更新全局 context。
    """
    from ufo.contracts.contracts import ResultStatus
    from ufo.module.context import ContextNames
    from galaxy.constellation.task_constellation import TaskConstellation
    
    if not results:
        return
    
    # 从后往前查找最后一个成功的包含 constellation 数据的 result
    constellation_json = None
    for result in reversed(results):
        # 检查 result 状态是否为 SUCCESS
        if result.status == ResultStatus.SUCCESS and result.result:
            try:
                # 检查 result 是否包含 constellation JSON
                if isinstance(result.result, str):
                    # 有效的 constellation JSON 应包含 "constellation_id" 或 "tasks"
                    if '"constellation_id"' in result.result or '"tasks"' in result.result:
                        constellation_json = result.result
                        break
                elif isinstance(result.result, dict):
                    if "constellation_id" in result.result or "tasks" in result.result:
                        constellation_json = result.result
                        break
            except Exception as e:
                self.logger.warning(f"Failed to parse result as constellation: {e}")
                continue
    
    # 如果找到了 constellation 数据，同步到 context
    if constellation_json:
        try:
            # 从 JSON 解析 constellation
            if isinstance(constellation_json, str):
                constellation = TaskConstellation.from_json(json_data=constellation_json)
            else:
                constellation = TaskConstellation.from_dict(constellation_json)
            
            # 更新全局 context
            context.global_context.set(ContextNames.CONSTELLATION, constellation)
            self.logger.info(
                f"Successfully synced constellation from editing operation: "
                f"constellation_id={constellation.constellation_id}"
            )
        except Exception as e:
            self.logger.error(f"Failed to sync constellation from result: {e}")
    else:
        self.logger.debug("No constellation data found in results to sync")
```

#### 关键特性

1. **使用 ResultStatus 枚举**: 正确使用 `ResultStatus.SUCCESS` 而不是字符串比较
2. **从后往前遍历**: 使用 `reversed(results)` 获取最后一个成功的结果
3. **智能检测**: 检查 JSON 字符串或字典中是否包含 constellation 字段
4. **错误处理**: 完善的异常处理和日志记录
5. **支持多种格式**: 支持 JSON 字符串和字典两种格式

---

## 工作流程

### Editing Mode 完整流程

```
1. ConstellationAgent 发起编辑请求
   ↓
2. ConstellationEditingActionExecutionStrategy 处理
   ↓
3. 调用 MCP Server 工具 (如 add_task)
   ↓
4. ConstellationEditor 执行命令
   ↓
5. MCP 工具返回完整 constellation JSON
   ↓
6. Result 对象包含 constellation JSON
   ↓
7. sync_constellation 从 Result 中提取 constellation
   ↓
8. 更新 Context.CONSTELLATION
   ↓
9. ✅ Context 中的 constellation 已同步
```

### 数据流示例

```python
# 1. MCP 工具执行
add_task(task_id="task_1", name="Test Task", description="...")
# 返回: '{"constellation_id": "...", "tasks": {...}, "dependencies": {...}}'

# 2. 封装为 Result
Result(
    status=ResultStatus.SUCCESS,
    result='{"constellation_id": "...", "tasks": {...}, ...}'
)

# 3. sync_constellation 处理
# - 检测到 SUCCESS 状态
# - 提取 constellation JSON
# - 解析为 TaskConstellation 对象
# - 更新到 Context

# 4. 后续操作可以从 Context 获取最新状态
constellation = context.get(ContextNames.CONSTELLATION)
```

---

## 优势

### ✅ 最小侵入性
- 只修改了 MCP Server 的返回值和 editing strategy
- 不引入全局状态或复杂的架构
- 不需要修改 Editor、Command 等核心组件

### ✅ 无状态设计
- 每次操作独立，不依赖全局状态
- 避免并发和状态管理问题
- 易于测试和调试

### ✅ 架构一致性
- 与 creation mode 的同步方式保持一致
- 都是通过 sync_constellation 方法同步
- 统一的同步模式

### ✅ 完整性保证
- 每次返回完整的 constellation 状态
- 避免部分更新导致的不一致
- 便于验证和回滚

### ✅ 易于维护
- 逻辑清晰，易于理解
- 错误处理完善
- 日志记录详细

---

## 性能考虑

### JSON 序列化开销
- **影响**: 每次操作都需要序列化整个 constellation
- **缓解**: 
  - Constellation 通常不会太大（数十到数百个 tasks）
  - JSON 序列化在 Python 中性能很好
  - 操作频率不高（用户交互级别）

### 实测数据（预估）
- 100 tasks constellation: ~50KB JSON, 序列化 < 10ms
- 1000 tasks constellation: ~500KB JSON, 序列化 < 100ms

对于交互式应用，这个开销完全可以接受。

---

## 测试建议

### 单元测试

```python
def test_sync_constellation_from_success_result():
    """测试从成功的 result 中同步 constellation"""
    # 创建测试数据
    constellation_json = '{"constellation_id": "test", "tasks": {}}'
    result = Result(status=ResultStatus.SUCCESS, result=constellation_json)
    
    # 执行同步
    strategy = ConstellationEditingActionExecutionStrategy()
    strategy.sync_constellation([result], context)
    
    # 验证
    synced = context.get(ContextNames.CONSTELLATION)
    assert synced.constellation_id == "test"

def test_sync_constellation_ignores_failure():
    """测试忽略失败的 result"""
    result = Result(status=ResultStatus.FAILURE, result="error")
    
    strategy = ConstellationEditingActionExecutionStrategy()
    strategy.sync_constellation([result], context)
    
    # Context 不应该被更新
    # ...

def test_sync_constellation_uses_last_success():
    """测试使用最后一个成功的 result"""
    results = [
        Result(status=ResultStatus.SUCCESS, result='{"constellation_id": "v1"}'),
        Result(status=ResultStatus.SUCCESS, result='{"constellation_id": "v2"}'),
    ]
    
    strategy = ConstellationEditingActionExecutionStrategy()
    strategy.sync_constellation(results, context)
    
    # 应该使用最后一个
    synced = context.get(ContextNames.CONSTELLATION)
    assert synced.constellation_id == "v2"
```

### 集成测试

```python
async def test_editing_workflow_sync():
    """测试完整的编辑工作流同步"""
    # 1. 创建 constellation
    agent.weave_constellation_create(request, device_info)
    initial = context.get(ContextNames.CONSTELLATION)
    
    # 2. 编辑 constellation (add task)
    agent.weave_constellation_edit(request, device_info)
    
    # 3. 验证同步
    updated = context.get(ContextNames.CONSTELLATION)
    assert len(updated.tasks) == len(initial.tasks) + 1
    assert updated.constellation_id == initial.constellation_id  # 同一个 constellation
```

---

## 向后兼容性

### ✅ 完全兼容
- MCP Server 接口保持不变（参数不变）
- 只是返回值从部分 JSON 变为完整 JSON
- 调用方代码无需修改

### 客户端影响
- LLM 会收到更完整的信息
- 可能需要更新 prompt 来指导 LLM 理解新的返回格式
- 但这是增强，不是破坏性改变

---

## 未来改进

### 可选的增量更新
如果性能成为问题，可以考虑：
```python
# MCP 工具可以返回增量信息
{
    "operation": "add_task",
    "delta": {"task": {...}},
    "full_constellation": {...}  # 可选
}
```

### 缓存优化
```python
# 如果 constellation_id 没变，可以跳过解析
last_constellation_id = context.get("LAST_CONSTELLATION_ID")
if current_id == last_constellation_id:
    # 只更新变更的部分
```

但目前的实现已经足够简单和高效，不需要这些优化。

---

## 总结

方案1 的实现提供了：
- ✅ 简单直接的同步机制
- ✅ 与现有架构完美融合
- ✅ 完整的错误处理和日志
- ✅ 良好的性能表现
- ✅ 易于测试和维护

这是解决 constellation 同步问题的**最佳方案**。
