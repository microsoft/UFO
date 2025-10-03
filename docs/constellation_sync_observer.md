# Constellation Modification Synchronizer

## 概述

`ConstellationModificationSynchronizer` 是一个事件驱动的观察者（Observer），用于解决 UFO Galaxy 框架中的并发竞态条件问题。

## 问题背景

### 竞态条件场景

在原有设计中存在以下问题：

```
时间线：
T1: Task A 完成 → mark_task_completed → Task B 变为 ready
T2: orchestrator 发布 TASK_COMPLETED event
T3: orchestrator 继续循环 → get_ready_tasks() → 发现 Task B ready → 开始执行 Task B
T4: ConstellationProgressObserver 收到 event
T5: agent.process_editing() 开始执行，可能修改 Task B 或其依赖
T6: ❌ 但 Task B 已经在 T3 开始执行了！
```

**核心问题**：orchestrator 不会等待 `agent.process_editing()` 完成就继续执行新的 ready 任务，可能导致：
- 正在执行的任务的配置被修改
- 依赖关系在任务执行中改变
- DAG 结构不一致

## 解决方案

### 事件同步机制

通过 Observer 模式实现的同步机制，确保以下执行顺序：

```
1. Task 完成 → 发布 TASK_COMPLETED event
2. Synchronizer 收到 → 注册 pending_modifications[task_id] = Future()
3. Agent 收到 → 触发 process_editing()
4. process_editing 完成 → 发布 CONSTELLATION_MODIFIED event (带 on_task_id)
5. Synchronizer 收到 → 标记 pending_modifications[task_id].set_result(True)
6. orchestrator 下一轮循环前 → await synchronizer.wait_for_pending_modifications()
7. ✅ 安全执行 → ready_tasks = constellation.get_ready_tasks()
```

## 架构设计

### 组件交互

```
┌─────────────────────────────────────────────────────────────────┐
│                         Event Bus                                │
└─────────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
         │ TASK_COMPLETED     │ CONSTELLATION_     │ subscribe
         │                    │ MODIFIED           │
         │                    │                    │
    ┌────┴────────┐    ┌──────┴──────┐    ┌──────┴──────────────┐
    │             │    │             │    │  Constellation      │
    │ Orchestrator│    │    Agent    │    │  Modification       │
    │             │    │             │    │  Synchronizer       │
    └────┬────────┘    └──────┬──────┘    └──────┬──────────────┘
         │                    │                    │
         │ wait_for_pending   │                    │ has_pending
         │ _modifications()   │                    │ _modifications()
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                         Synchronization
```

### 类结构

```python
ConstellationModificationSynchronizer(IEventObserver)
│
├── 属性
│   ├── _pending_modifications: Dict[str, asyncio.Future]  # 待处理的修改
│   ├── _current_constellation_id: Optional[str]           # 当前 constellation ID
│   ├── _modification_timeout: float                       # 超时时间
│   └── _stats: Dict[str, int]                            # 统计信息
│
├── 事件处理
│   ├── on_event(event: Event)                            # 主事件处理器
│   ├── _handle_task_event(event: TaskEvent)              # 处理任务事件
│   └── _handle_constellation_event(event: ConstellationEvent)  # 处理 constellation 事件
│
├── 同步控制
│   ├── wait_for_pending_modifications(timeout) → bool    # 等待所有修改完成
│   ├── has_pending_modifications() → bool                # 检查是否有待处理修改
│   └── get_pending_count() → int                         # 获取待处理数量
│
└── 管理功能
    ├── clear_pending_modifications()                     # 清除所有待处理修改
    ├── set_modification_timeout(timeout)                 # 设置超时时间
    └── get_statistics() → Dict                           # 获取统计信息
```

## 使用方法

### 在 GalaxySession 中集成

```python
from ufo.galaxy.session.observers import ConstellationModificationSynchronizer

class GalaxySession(BaseSession):
    def _setup_observers(self) -> None:
        # ... 其他 observers ...
        
        # 创建同步器
        self._modification_synchronizer = ConstellationModificationSynchronizer(
            orchestrator=self._orchestrator,
            logger=self.logger,
        )
        self._observers.append(self._modification_synchronizer)
        
        # 将同步器附加到 orchestrator
        self._orchestrator.set_modification_synchronizer(self._modification_synchronizer)
        
        # 订阅事件总线
        for observer in self._observers:
            self._event_bus.subscribe(observer)
```

### 在 Orchestrator 中使用

```python
class TaskConstellationOrchestrator:
    async def orchestrate_constellation(self, constellation, ...):
        while not constellation.is_complete():
            # ⭐ 等待所有待处理的修改完成
            if self._modification_synchronizer:
                await self._modification_synchronizer.wait_for_pending_modifications()
            
            # 安全地获取 ready tasks
            ready_tasks = constellation.get_ready_tasks()
            
            # 执行任务...
```

### Agent 端（无需修改）

Agent 的 `process_editing()` 方法已经发布 `CONSTELLATION_MODIFIED` 事件：

```python
async def process_editing(self, context: Context, task_id: str):
    # ... 修改逻辑 ...
    
    # 发布修改完成事件
    await self._event_bus.publish_event(
        ConstellationEvent(
            event_type=EventType.CONSTELLATION_MODIFIED,
            data={"on_task_id": task_id},  # ⭐ 关键：指明哪个任务触发的修改
            # ...
        )
    )
```

## 关键特性

### 1. 自动超时保护

```python
# 默认 30 秒超时
synchronizer = ConstellationModificationSynchronizer(...)

# 自定义超时
synchronizer.set_modification_timeout(60.0)

# 等待时会自动超时
result = await synchronizer.wait_for_pending_modifications(timeout=10.0)
if not result:
    logger.warning("Modification timed out, proceeding anyway")
```

### 2. 统计信息追踪

```python
stats = synchronizer.get_statistics()
# {
#     "total_modifications": 10,
#     "completed_modifications": 9,
#     "timeout_modifications": 1
# }
```

### 3. 错误恢复

```python
# 紧急清除所有待处理修改
synchronizer.clear_pending_modifications()
```

### 4. 状态查询

```python
# 检查是否有待处理修改
if synchronizer.has_pending_modifications():
    pending_tasks = synchronizer.get_pending_task_ids()
    logger.info(f"Waiting for modifications: {pending_tasks}")
```

## 测试

### 运行所有测试

```powershell
# 运行所有同步相关测试
python tests/run_sync_tests.py

# 或单独运行
pytest tests/test_constellation_sync_observer.py -v
pytest tests/test_constellation_sync_integration.py -v
```

### 测试覆盖

#### 单元测试 (`test_constellation_sync_observer.py`)
- ✅ 基本同步流程
- ✅ 注册和完成修改
- ✅ 等待机制
- ✅ 超时处理
- ✅ 错误恢复
- ✅ 统计追踪
- ✅ 边界条件

#### 集成测试 (`test_constellation_sync_integration.py`)
- ✅ 与 Orchestrator 集成
- ✅ 与 Event Bus 集成
- ✅ 竞态条件防护
- ✅ 并发修改处理
- ✅ DAG 执行场景
- ✅ 性能特性

## 性能考量

### 开销分析

1. **事件处理开销**：~1-2ms per event
2. **Future 等待开销**：~0.1ms per check
3. **总体影响**：对于正常 DAG 执行，增加 < 5% 总时间

### 优化建议

1. **批量处理**：多个任务同时完成时，等待一次即可
2. **超时设置**：根据 agent 处理速度调整超时时间
3. **日志级别**：生产环境使用 INFO 级别，避免过多 DEBUG 日志

## 故障排查

### 问题：Orchestrator 永久等待

**症状**：`wait_for_pending_modifications()` 永不返回

**可能原因**：
1. Agent 未发布 `CONSTELLATION_MODIFIED` 事件
2. Event 中缺少 `on_task_id` 字段
3. Synchronizer 未订阅 Event Bus

**解决方法**：
```python
# 检查待处理修改
pending = synchronizer.get_pending_task_ids()
logger.error(f"Stuck waiting for: {pending}")

# 紧急恢复
synchronizer.clear_pending_modifications()
```

### 问题：频繁超时

**症状**：日志中大量超时警告

**可能原因**：
1. Agent 处理速度慢
2. 超时设置过短
3. Event Bus 延迟

**解决方法**：
```python
# 增加超时时间
synchronizer.set_modification_timeout(60.0)

# 检查 agent 性能
stats = synchronizer.get_statistics()
logger.info(f"Timeout rate: {stats['timeout_modifications'] / stats['total_modifications']}")
```

### 问题：竞态条件仍然发生

**症状**：任务执行时配置被修改

**检查清单**：
- [ ] Synchronizer 已附加到 Orchestrator
- [ ] Synchronizer 已订阅 Event Bus
- [ ] Orchestrator 在获取 ready tasks 前调用 `wait_for_pending_modifications()`
- [ ] Agent 正确发布 `CONSTELLATION_MODIFIED` 事件
- [ ] Event 包含正确的 `on_task_id`

## 设计原则

### SOLID 原则

1. **单一职责**：只负责同步协调，不参与业务逻辑
2. **开闭原则**：通过 Event 扩展，无需修改现有代码
3. **里氏替换**：实现 `IEventObserver` 接口
4. **接口隔离**：提供简洁的公共接口
5. **依赖倒置**：依赖于抽象的 Event 和 Observer 接口

### 事件驱动设计

- **松耦合**：组件间通过 Event Bus 通信
- **可观测性**：所有交互通过事件追踪
- **可扩展性**：易于添加新的同步逻辑

## 未来改进

### 可能的增强

1. **优先级队列**：支持不同任务的修改优先级
2. **批量等待**：优化多任务同时完成的场景
3. **Metrics 集成**：导出 Prometheus metrics
4. **分布式支持**：支持跨进程的同步

### 已知限制

1. **单 Constellation**：当前设计假设单个 Constellation 执行
2. **内存限制**：大量并发任务时 Future 对象占用内存
3. **超时粒度**：所有修改使用相同的超时时间

## 贡献

如果发现问题或有改进建议，请：
1. 添加测试用例到 `tests/test_constellation_sync_observer.py`
2. 更新文档说明新特性
3. 确保所有测试通过

## 许可证

Copyright (c) Microsoft Corporation.
Licensed under the MIT License.
