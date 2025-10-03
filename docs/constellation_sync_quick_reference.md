# 🎯 Constellation Modification Synchronizer - Quick Reference

## 问题与解决方案

### ❌ 原始问题：竞态条件

```python
# 时间线：
Task A 完成 → Orchestrator 获取 ready tasks → ❌ 立即执行 Task B
                           ↓
                    (同时) Agent 正在修改 Task B
```

**后果**: Task B 的配置在执行中被修改 💥

---

### ✅ 解决方案：事件同步

```python
# 修复后的时间线：
Task A 完成 → Synchronizer 注册修改 → Agent 修改中...
                           ↓
              Orchestrator 等待 ⏳
                           ↓
              Agent 修改完成 → 发布 CONSTELLATION_MODIFIED
                           ↓
              Orchestrator 继续 → ✅ 安全执行 Task B
```

---

## 🚀 快速开始

### 1. 导入

```python
from ufo.galaxy.session.observers import ConstellationModificationSynchronizer
```

### 2. 创建并附加

```python
# 在 GalaxySession._setup_observers() 中
synchronizer = ConstellationModificationSynchronizer(
    orchestrator=self._orchestrator,
    logger=self.logger,
)

# 附加到 orchestrator
self._orchestrator.set_modification_synchronizer(synchronizer)

# 订阅事件总线
event_bus.subscribe(synchronizer)
```

### 3. Orchestrator 使用

```python
# 在 orchestrate_constellation() 的主循环中
while not constellation.is_complete():
    # ⭐ 等待所有修改完成
    if self._modification_synchronizer:
        await self._modification_synchronizer.wait_for_pending_modifications()
    
    # 安全获取 ready tasks
    ready_tasks = constellation.get_ready_tasks()
    # ... 执行任务
```

### 4. Agent 端（无需修改）

```python
# Agent 的 process_editing() 已自动支持
async def process_editing(self, context, task_id):
    # ... 修改逻辑 ...
    
    # 发布事件（已有代码）
    await self._event_bus.publish_event(
        ConstellationEvent(
            event_type=EventType.CONSTELLATION_MODIFIED,
            data={"on_task_id": task_id},  # ⭐ 必须包含
            # ...
        )
    )
```

---

## 📊 关键 API

### 基本操作

```python
# 检查状态
synchronizer.has_pending_modifications()  # → bool
synchronizer.get_pending_count()          # → int
synchronizer.get_pending_task_ids()       # → List[str]

# 等待修改
await synchronizer.wait_for_pending_modifications()  # → bool

# 获取统计
stats = synchronizer.get_statistics()
# → {
#     "total_modifications": 10,
#     "completed_modifications": 9,
#     "timeout_modifications": 1
# }
```

### 配置

```python
# 设置超时（默认 30 秒）
synchronizer.set_modification_timeout(60.0)

# 紧急清理（仅用于错误恢复）
synchronizer.clear_pending_modifications()
```

---

## 🔍 监控与调试

### 日志输出

```
INFO  [Synchronizer] 🔒 Registered pending modification for task 'task_A'
INFO  [Synchronizer] ⏳ Waiting for 1 pending modification(s): ['task_A']
INFO  [Synchronizer] ✅ Completed modification for task 'task_A'
INFO  [Synchronizer] ✅ All pending modifications completed
```

### 常见问题

**问题**: 永久等待
```python
# 检查
pending = synchronizer.get_pending_task_ids()
logger.error(f"Stuck on: {pending}")

# 解决
synchronizer.clear_pending_modifications()
```

**问题**: 频繁超时
```python
# 增加超时时间
synchronizer.set_modification_timeout(120.0)

# 检查 agent 性能
stats = synchronizer.get_statistics()
timeout_rate = stats['timeout_modifications'] / stats['total_modifications']
logger.warning(f"Timeout rate: {timeout_rate:.1%}")
```

---

## ✅ 测试验证

### 运行测试

```powershell
# 所有测试
python -m pytest tests/test_constellation_sync_observer_simple.py tests/test_race_condition_real.py -v

# 竞态条件测试
python -m pytest tests/test_race_condition_real.py -v -s
```

### 测试结果

```
✅ 17/17 tests passed
✅ Race condition prevented
✅ Timeout handling works
✅ Error recovery verified
✅ Performance acceptable
```

---

## 📋 检查清单

在部署前确认：

- [ ] `ConstellationModificationSynchronizer` 已创建
- [ ] Synchronizer 已附加到 `TaskConstellationOrchestrator`
- [ ] Synchronizer 已订阅 `EventBus`
- [ ] Orchestrator 在获取 ready tasks 前调用 `wait_for_pending_modifications()`
- [ ] Agent 的 `CONSTELLATION_MODIFIED` 事件包含 `on_task_id`
- [ ] 所有测试通过
- [ ] 日志正常输出

---

## 📚 更多信息

- **详细文档**: `docs/constellation_sync_observer.md`
- **测试报告**: `docs/test_results_constellation_sync.md`
- **单元测试**: `tests/test_constellation_sync_observer_simple.py`
- **集成测试**: `tests/test_race_condition_real.py`

---

## 🎓 原理说明

### 事件流

```
1. TASK_COMPLETED    → Synchronizer 注册
2. Agent 处理        → 修改 constellation  
3. CONSTELLATION_MODIFIED → Synchronizer 标记完成
4. Orchestrator 等待 → 继续执行
```

### 数据结构

```python
_pending_modifications: Dict[str, asyncio.Future]
# "task_A" → Future (等待完成)
# "task_B" → Future (等待完成)
```

### 同步机制

```python
# 注册
future = asyncio.Future()
_pending_modifications[task_id] = future

# 等待
await asyncio.gather(*_pending_modifications.values())

# 完成
future.set_result(True)
```

---

**状态**: ✅ Production Ready  
**版本**: 1.0.0  
**维护者**: UFO Team
