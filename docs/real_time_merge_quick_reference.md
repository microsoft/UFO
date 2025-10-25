# Real-Time Constellation Merge - Quick Reference

## 问题

在并发任务完成场景下，后续任务的编辑可能看不到前一个任务编辑的修改。

**场景**：
```
task_1 complete → task_1 editing start → task_2 complete → 
task_1 editing complete → task_2 editing start ❌ (看不到 task_1 的修改)
```

## 解决方案

在每次 agent 处理任务之前，从 synchronizer 获取实时 merged constellation。

## 核心改动

**文件**：`galaxy/agents/constellation_agent_states.py`

**类**：`ContinueConstellationAgentState`

### 新增方法

```python
async def _get_merged_constellation(self, agent, orchestrator_constellation):
    """获取实时合并的 constellation"""
    synchronizer = agent.orchestrator._modification_synchronizer
    if not synchronizer:
        return orchestrator_constellation
    
    return synchronizer.merge_and_sync_constellation_states(
        orchestrator_constellation=orchestrator_constellation
    )
```

### 使用方式

```python
# 在 handle 方法中
latest_constellation = completed_task_events[-1].data.get("constellation")

# ⭐ 实时 merge
merged_constellation = await self._get_merged_constellation(
    agent, latest_constellation
)

# 使用 merged 版本
await agent.process_editing(
    before_constellation=merged_constellation
)
```

## 效果

✅ task_2 editing 现在能看到 task_1 editing 的所有修改  
✅ 避免修改冲突和丢失  
✅ 保持架构简洁  
✅ 向后兼容  

## 日志标识

查找日志：`🔄 Real-time merged constellation for editing`

## 日期

2025-10-24
