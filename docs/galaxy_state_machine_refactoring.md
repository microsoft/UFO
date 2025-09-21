# Galaxy Agent State Machine Refactoring

本重构解决了 Galaxy Agent 中constellation执行和agent更新之间的竞态条件问题，实现了基于状态机的事件驱动架构。

## 问题分析

### 原始问题
1. **竞态条件**: `constellation.is_complete()` 是同步检查，而 `TaskEvent` 发布和观察者处理是异步的
2. **时序问题**: 最后一个任务完成 → `is_complete()` 返回 true → 编排循环退出 → 观察者还未处理事件
3. **缺乏协调**: 编排器和代理更新之间缺乏同步机制

### 解决方案
采用基于状态机的事件驱动架构，确保任务完成事件的顺序处理和同步协调。

## 架构设计

### 状态机设计

```
┌─────────────┐    constellation创建    ┌─────────────┐
│    START    │──────────────────────→│   MONITOR   │
│             │    开始orchestration    │             │
└─────────────┘                       └─────────────┘
       ↑                                      │
       │                                      │ 接收TaskEvent
       │                                      ↓
       │                              ┌─────────────┐
       │               agent决定continue │             │
       └─────────────────────────────│  decision   │
                                    │             │
                                    └─────────────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        │                  │                  │
                  agent决定finish    agent决定failed    agent决定continue
                        ↓                  ↓                  ↓
                ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                │   FINISH    │    │    FAIL     │    │ 返回 START   │
                │             │    │             │    │             │
                └─────────────┘    └─────────────┘    └─────────────┘
```

### 核心组件

#### 1. GalaxyAgentState 状态机
- **StartGalaxyAgentState**: 创建constellation并启动编排
- **MonitorGalaxyAgentState**: 等待任务完成事件，协调更新
- **FinishGalaxyAgentState**: 任务完成终止状态
- **FailGalaxyAgentState**: 任务失败终止状态

#### 2. 事件队列机制
```python
# Agent维护任务完成事件队列
agent.task_completion_queue: asyncio.Queue

# Observer将TaskEvent放入队列而不是直接调用更新
await agent.task_completion_queue.put(task_event)

# Monitor状态等待队列事件
task_event = await agent.task_completion_queue.get()
```

#### 3. 同步协调机制
- 只有在收到TaskEvent时Monitor状态才进行状态转换
- Agent的`update_constellation_with_lock`确保更新的原子性
- 状态转换基于Agent的决策而非Constellation的同步检查

## 关键特性

### 1. 事件驱动的状态转换
```python
# Monitor状态无超时，纯事件驱动
task_event = await agent.task_completion_queue.get()  # 无超时
await agent.update_constellation_with_lock(task_result, context)
should_continue = await agent.should_continue(constellation, context)
```

### 2. 任务级超时控制
```python
# 在START状态配置任务超时
def _configure_task_timeouts(self, constellation):
    default_timeout = config.get("GALAXY_TASK_TIMEOUT", 1800.0)  # 30分钟
    critical_timeout = config.get("GALAXY_CRITICAL_TASK_TIMEOUT", 3600.0)  # 1小时
```

### 3. 灵活的继续/终止机制
```python
async def should_continue(self, constellation, context=None):
    # Agent可以根据复杂逻辑决定是否继续
    # - constellation完成但需要添加新任务 → continue
    # - constellation未完成但满足提前终止条件 → finish/fail
    # - constellation完成且无需添加任务 → finish
```

## 测试覆盖

### 单元测试
1. **状态机测试** (`test_galaxy_agent_states.py`)
   - 各状态的handle方法测试
   - 状态转换逻辑测试
   - 异常处理测试
   - 超时配置测试

2. **GalaxyRound测试** (`test_galaxy_round_refactored.py`)
   - 状态机集成测试
   - 观察者集成测试
   - 错误场景测试
   - 异步行为测试

3. **Observer测试** (`test_observers_refactored.py`)
   - 事件队列机制测试
   - 事件路由测试
   - 并发处理测试
   - 异常处理测试

### 集成测试
1. **Constellation执行到完成无更新** 
2. **Constellation执行中途Agent提前终止**
3. **Constellation完成后Agent添加新任务**
4. **复杂多轮场景**
5. **竞态条件处理**

## 使用方法

### 运行测试
```bash
# 运行所有测试
python tests/run_galaxy_tests.py

# 运行特定测试
python -m pytest tests/unit/galaxy/agents/test_galaxy_agent_states.py -v

# 运行集成测试
python -m pytest tests/integration/galaxy/ -v

# 生成覆盖率报告
python -m pytest --cov=ufo.galaxy --cov-report=html
```

### 配置选项
```yaml
# config.yaml
GALAXY_TASK_TIMEOUT: 1800.0          # 普通任务30分钟
GALAXY_CRITICAL_TASK_TIMEOUT: 3600.0  # 关键任务1小时
```

### 自定义Agent行为
```python
class CustomGalaxyAgent(GalaxyWeaverAgent):
    async def should_continue(self, constellation, context=None):
        # 自定义继续/终止逻辑
        if self.check_custom_conditions():
            return True
        return super().should_continue(constellation, context)
        
    async def process_task_result(self, task_result, constellation, context=None):
        # 自定义任务结果处理
        result = await super().process_task_result(task_result, constellation, context)
        
        # 添加自定义逻辑
        if self.should_add_followup_tasks(task_result):
            self.add_followup_tasks(constellation, task_result)
            
        return result
```

## 优势

1. **解决竞态条件**: 事件队列确保任务完成事件的顺序处理
2. **清晰的职责分离**: 状态机明确定义各阶段的职责
3. **灵活的控制流**: Agent可以在任何时候决定继续、终止或添加新任务
4. **可测试性**: 状态机和事件队列易于单元测试和集成测试
5. **可扩展性**: 易于添加新状态或修改状态转换逻辑
6. **错误恢复**: 明确的错误状态和清理机制

## 向后兼容性

重构保持了与现有UFO框架的兼容性：
- 继承现有的`BaseRound`和`AgentState`接口
- 保持现有的事件系统和观察者模式
- 保持现有的Context和配置系统
- 保持现有的TaskConstellation和TaskStar接口

## 未来扩展

1. **状态持久化**: 支持会话恢复
2. **分布式协调**: 支持多Agent协作
3. **动态超时调整**: 基于任务历史动态调整超时
4. **智能状态转换**: 基于机器学习的状态转换决策
5. **可视化监控**: 实时状态机可视化界面
