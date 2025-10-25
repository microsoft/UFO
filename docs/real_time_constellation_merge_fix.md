# Real-Time Constellation Merge Fix

## 问题描述

### 原始问题场景

在以下时间线中发现了一个竞态条件问题：

```
task_1 complete → task_1 editing start → task_2 complete → task_1 editing complete → task_2 editing start → task_2 editing complete
```

**问题**：task_2 editing start 基于的是 task_2 complete 时的 constellation 版本，而不是包含 task_1 editing 修改的 merged 版本。

### 根本原因

1. **事件队列机制**：当 task_2 complete 时，orchestrator 发布 `TASK_COMPLETED` 事件，该事件包含当前的 constellation 快照
2. **等待机制**：Orchestrator 在 `wait_for_pending_modifications()` 中被阻塞，直到所有 pending modifications 完成
3. **Agent 处理时机**：Agent 从队列取出 task_2 事件时，使用的是事件中保存的 constellation 快照，而不是最新的 merged 版本

### 时间线分析

| 时刻 | 事件 | Orchestrator 状态 | Agent 状态 | Constellation 版本 |
|-----|------|------------------|-----------|------------------|
| T1 | task_1 complete | 发布事件，开始等待 | - | Original |
| T2 | task_1 editing start | 等待中 🔒 | 处理 task_1 | Original |
| T3 | task_2 complete | 等待中 🔒 | - | Original (事件快照) |
| T4 | task_1 editing complete | 继续等待 🔒 | - | Agent: task_1 修改后 |
| T5 | task_2 editing start | 等待中 🔒 | 处理 task_2 | ❌ Original (来自 T3 快照) |
| T6 | task_2 editing complete | 释放 ✅ | - | Agent: task_1+task_2 修改后 |
| T7 | Merge | 合并状态 | - | Merged |

**问题**：T5 时刻，task_2 editing 看到的是 T3 时的 Original 版本，没有包含 T4 的 task_1 修改。

## 解决方案：实时 Merge

### 方案概述

在 Agent 处理每个 task completion 事件之前，主动从 synchronizer 获取实时 merged constellation，确保使用最新的状态。

### 实现细节

#### 1. 新增 `_get_merged_constellation` 方法

在 `ContinueConstellationAgentState` 类中添加：

```python
async def _get_merged_constellation(
    self, agent: "ConstellationAgent", orchestrator_constellation
):
    """
    Get real-time merged constellation from synchronizer.

    This ensures that the agent always processes with the most up-to-date
    constellation state, including any structural modifications from previous
    editing sessions that may have completed while this task was running.

    :param agent: The ConstellationAgent instance
    :param orchestrator_constellation: The constellation from orchestrator's event
    :return: Merged constellation with latest agent modifications + orchestrator state
    """
    synchronizer = agent.orchestrator._modification_synchronizer

    if not synchronizer:
        agent.logger.debug(
            "No modification synchronizer available, using orchestrator constellation"
        )
        return orchestrator_constellation

    # Get real-time merged constellation from synchronizer
    merged_constellation = (
        synchronizer.merge_and_sync_constellation_states(
            orchestrator_constellation=orchestrator_constellation
        )
    )

    agent.logger.info(
        f"🔄 Real-time merged constellation for editing. "
        f"Tasks before: {len(orchestrator_constellation.tasks)}, "
        f"Tasks after merge: {len(merged_constellation.tasks)}"
    )

    return merged_constellation
```

#### 2. 在 `handle` 方法中调用

修改处理逻辑，在调用 `process_editing` 之前进行实时 merge：

```python
# Get the latest constellation from the last event
latest_constellation = completed_task_events[-1].data.get("constellation")

# ⭐ NEW: Get real-time merged constellation before processing
merged_constellation = await self._get_merged_constellation(
    agent, latest_constellation
)

# Update constellation based on task completion
await agent.process_editing(
    context=context,
    task_ids=task_ids,
    before_constellation=merged_constellation,  # Use merged version
)
```

### 修复后的时间线

| 时刻 | 事件 | Orchestrator 状态 | Agent 状态 | Constellation 版本 |
|-----|------|------------------|-----------|------------------|
| T1 | task_1 complete | 发布事件，开始等待 | - | Original |
| T2 | task_1 editing start | 等待中 🔒 | 处理 task_1 | Original |
| T3 | task_2 complete | 等待中 🔒 | - | Original (事件快照) |
| T4 | task_1 editing complete | 继续等待 🔒 | - | Agent: task_1 修改后 |
| T5 | task_2 editing start | 等待中 🔒 | 处理 task_2 | ✅ Merged (task_1 修改 + task_2 状态) |
| T6 | task_2 editing complete | 释放 ✅ | - | Agent: task_1+task_2 修改后 |
| T7 | Merge | 合并状态 | - | Merged |

**改进**：T5 时刻，通过实时 merge，task_2 editing 能够看到 task_1 的所有修改！

## 优势

### 1. 解决竞态条件
- Task_2 editing 现在能看到 task_1 editing 的所有修改
- 避免了修改冲突和丢失

### 2. 保持架构简洁
- 不需要修改事件系统
- 不需要修改 orchestrator 的主循环
- 只在 agent 端添加一个小的辅助方法

### 3. 向后兼容
- 如果没有 synchronizer，自动回退到原始逻辑
- 不影响现有的同步机制

### 4. 性能友好
- 只在需要时进行 merge（每次 agent 处理前）
- 不影响 orchestrator 的执行效率

## 关键组件交互

```
┌─────────────────┐
│  Orchestrator   │
│                 │
│  1. 发布事件     │──┐
│  2. 等待 pending│  │
│  3. 最终 merge  │  │
└─────────────────┘  │
                     │ TASK_COMPLETED Event
                     │ (含原始 constellation)
                     ▼
              ┌──────────────┐
              │ Event Queue  │
              └──────────────┘
                     │
                     │ Agent 从队列取出
                     ▼
         ┌────────────────────────┐
         │ ContinueConstellationAgentState │
         │                                  │
         │ 1. 取出事件                       │
         │ 2. ⭐ 调用 _get_merged_constellation │
         │ 3. 使用 merged 版本处理             │
         └────────────────────────┘
                     │
                     │ 获取最新状态
                     ▼
         ┌────────────────────────┐
         │  Synchronizer          │
         │                        │
         │  _current_constellation│ ← 每次 CONSTELLATION_MODIFIED 更新
         │                        │
         │  merge_and_sync_...()  │ ← 合并 orchestrator + agent 状态
         └────────────────────────┘
```

## 测试建议

### 场景 1：顺序完成
```
task_1 complete → task_1 editing complete → task_2 complete → task_2 editing complete
```
预期：正常工作（与之前行为一致）

### 场景 2：交叉完成（修复的场景）
```
task_1 complete → task_1 editing start → task_2 complete → task_1 editing complete → task_2 editing start
```
预期：task_2 editing 应该看到 task_1 的修改

### 场景 3：多任务并发
```
task_1, task_2, task_3 complete → task_1 editing → task_2 editing → task_3 editing
```
预期：每个 editing 都应该看到之前所有的修改

### 验证方法

1. **日志检查**：查看 `🔄 Real-time merged constellation for editing` 日志
2. **任务数量**：检查 merge 前后的 tasks 数量变化
3. **依赖关系**：验证新添加的依赖是否被后续任务看到
4. **状态一致性**：确保 COMPLETED 状态正确保留

## 相关文件

- `galaxy/agents/constellation_agent_states.py` - 主要修改文件
- `galaxy/session/observers/constellation_sync_observer.py` - Synchronizer 实现
- `galaxy/constellation/orchestrator/orchestrator.py` - Orchestrator 主循环

## 日期

2025-10-24

## 作者

Chaoyun Zhang
