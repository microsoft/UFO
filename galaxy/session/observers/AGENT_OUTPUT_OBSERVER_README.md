# Agent Output Event System - Observer Pattern Implementation

## 概述

将Constellation Agent的输出从直接打印改为使用观察者模式发布事件，实现解耦和扩展性。

## 🎯 主要改动

### 1. **扩展事件类型** (`galaxy/core/events.py`)

添加了新的Agent输出事件类型：

```python
class EventType(Enum):
    # ... 现有事件类型 ...
    
    # Agent output events (新增)
    AGENT_RESPONSE = "agent_response"  # Agent LLM响应
    AGENT_ACTION = "agent_action"      # Agent动作执行
```

添加了新的`AgentEvent`事件类：

```python
@dataclass
class AgentEvent(Event):
    agent_name: str           # Agent名称
    agent_type: str          # Agent类型 (constellation, app, host等)
    output_type: str         # 输出类型 (response, action, thought, plan)
    output_data: Dict[str, Any]  # 输出内容
```

### 2. **创建AgentOutputObserver** (`galaxy/session/observers/agent_output_observer.py`)

新的Observer负责处理agent输出事件并委托给presenter显示：

```python
class AgentOutputObserver(IEventObserver):
    """观察并处理agent输出事件，使用presenter进行显示"""
    
    async def on_event(self, event: Event):
        if event.event_type == EventType.AGENT_RESPONSE:
            # 处理agent响应，调用presenter显示
            presenter.present_constellation_agent_response(response)
        elif event.event_type == EventType.AGENT_ACTION:
            # 处理agent动作，调用presenter显示
            presenter.present_constellation_editing_actions(actions)
```

**关键特性：**
- ✅ 解耦：Agent不直接调用presenter
- ✅ 可扩展：可添加更多observer处理同一事件
- ✅ 一致性：保持原有的打印逻辑不变

### 3. **更新ConstellationAgent** (`galaxy/agents/constellation_agent.py`)

将`print_response`方法改为发布事件：

```python
def print_response(self, response: ConstellationAgentResponse, print_action: bool = False):
    """发布agent响应事件而非直接打印"""
    event = AgentEvent(
        event_type=EventType.AGENT_RESPONSE,
        source_id=self.name,
        timestamp=time.time(),
        agent_name=self.name,
        agent_type="constellation",
        output_type="response",
        output_data={**response.model_dump(), "print_action": print_action},
    )
    asyncio.create_task(get_event_bus().publish_event(event))
```

### 4. **更新处理策略** 

#### `base_constellation_strategy.py`
- 将`print_actions`改为`async publish_actions`抽象方法
- 在action execution中调用`await self.publish_actions(agent, action_list_info)`

#### `constellation_editing_strategy.py`
实现`publish_actions`发布编辑动作事件：

```python
async def publish_actions(self, agent, actions):
    """发布constellation编辑动作事件"""
    event = AgentEvent(
        event_type=EventType.AGENT_ACTION,
        source_id=agent.name,
        agent_name=agent.name,
        agent_type="constellation",
        output_type="action",
        output_data={
            "action_type": "constellation_editing",
            "actions": [action.model_dump() for action in actions.actions],
        },
    )
    await get_event_bus().publish_event(event)
```

#### `constellation_creation_strategy.py`
实现`publish_actions`为空操作（保持原逻辑）：

```python
async def publish_actions(self, agent, actions):
    """创建模式不发布动作事件"""
    pass  # 保持原有逻辑
```

### 5. **注册Observer** (`galaxy/session/galaxy_session.py`)

在`_setup_observers`方法中注册`AgentOutputObserver`：

```python
def _setup_observers(self):
    # ... 其他observers ...
    
    # Agent output observer for handling agent responses and actions
    agent_output_observer = AgentOutputObserver(presenter_type="rich")
    self._observers.append(agent_output_observer)
    
    # ... 订阅到event bus ...
```

## 🔄 工作流程

### 响应流程
```
ConstellationAgent.print_response()
    ↓ 发布 AGENT_RESPONSE 事件
EventBus
    ↓ 通知订阅者
AgentOutputObserver.on_event()
    ↓ 委托给Presenter
Presenter.present_constellation_agent_response()
    ↓ 显示到终端
终端输出（保持原有格式）
```

### 动作流程
```
Strategy.publish_actions()
    ↓ 发布 AGENT_ACTION 事件
EventBus
    ↓ 通知订阅者
AgentOutputObserver.on_event()
    ↓ 委托给Presenter
Presenter.present_constellation_editing_actions()
    ↓ 显示到终端
终端输出（保持原有格式）
```

## ✨ 优势

1. **解耦架构**
   - Agent不需要知道如何显示输出
   - Presenter逻辑可独立修改
   - 易于单元测试

2. **可扩展性**
   - 可添加多个observer处理同一事件
   - 例如：WebSocketObserver、LoggingObserver、MetricsObserver等

3. **一致性**
   - 所有输出通过事件系统
   - 与现有的task/constellation事件系统保持一致

4. **向后兼容**
   - 保持原有的打印逻辑和格式
   - 不影响现有功能

5. **实时性**
   - 异步事件发布，不阻塞agent执行
   - 支持实时推送到多个订阅者（如WebSocket）

## 🚀 未来扩展

基于这个架构，可以轻松添加：

### WebSocket Observer
```python
class WebSocketObserver(IEventObserver):
    async def on_event(self, event: AgentEvent):
        # 推送到Web前端
        await websocket.send_json({
            "type": event.output_type,
            "data": event.output_data
        })
```

### Logging Observer
```python
class OutputLoggingObserver(IEventObserver):
    async def on_event(self, event: AgentEvent):
        # 记录所有输出到文件
        logger.info(f"{event.agent_name}: {event.output_data}")
```

### Metrics Observer
```python
class OutputMetricsObserver(IEventObserver):
    async def on_event(self, event: AgentEvent):
        # 收集输出指标
        self.track_response_time(event)
        self.track_action_count(event)
```

## 📝 使用示例

原有代码无需修改，自动使用新的事件系统：

```python
# Agent代码（自动发布事件）
agent.print_response(response)  # 内部发布AGENT_RESPONSE事件

# Strategy代码（自动发布事件）
await self.publish_actions(agent, actions)  # 内部发布AGENT_ACTION事件

# Observer自动处理并显示
# 终端输出保持原有格式
```

## 🔧 配置

默认使用"rich" presenter，可通过参数自定义：

```python
agent_output_observer = AgentOutputObserver(presenter_type="text")
```

## 📊 事件数据结构

### AGENT_RESPONSE Event
```python
{
    "event_type": "agent_response",
    "source_id": "ConstellationAgent",
    "timestamp": 1699401234.567,
    "agent_name": "ConstellationAgent",
    "agent_type": "constellation",
    "output_type": "response",
    "output_data": {
        "thought": "...",
        "plan": "...",
        "status": "CONTINUE",
        "print_action": False
    }
}
```

### AGENT_ACTION Event
```python
{
    "event_type": "agent_action",
    "source_id": "ConstellationAgent",
    "timestamp": 1699401234.567,
    "agent_name": "ConstellationAgent",
    "agent_type": "constellation",
    "output_type": "action",
    "output_data": {
        "action_type": "constellation_editing",
        "actions": [
            {
                "function": "add_task",
                "arguments": {...},
                "result": {...}
            }
        ]
    }
}
```

## 🎯 总结

这个重构将Constellation Agent的输出系统从直接调用改为事件驱动，为未来的Web UI、实时监控、日志系统等功能奠定了基础，同时保持了原有功能的完全兼容。
