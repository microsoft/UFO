# Session Architecture - Quick Reference

## 类继承关系速查

```
BaseSession
├── WindowsBaseSession (有 HostAgent)
│   ├── Session
│   ├── ServiceSession
│   ├── FollowerSession
│   ├── FromFileSession
│   └── OpenAIOperatorSession
└── LinuxBaseSession (无 HostAgent)
    ├── LinuxSession
    └── LinuxServiceSession
```

## 快速创建 Session

### 使用工厂模式（推荐）

```python
from ufo.module.session_pool import SessionFactory

factory = SessionFactory()

# Windows 普通会话
sessions = factory.create_session(
    task="task_name",
    mode="normal",
    plan="",
    request="your request here"
)

# Linux 普通会话
sessions = factory.create_session(
    task="task_name",
    mode="normal",
    plan="",
    request="your request here",
    platform_override="linux",
    application_name="firefox"
)

# Windows 服务会话
session = factory.create_service_session(
    task="task_name",
    should_evaluate=False,
    id="session_id",
    request="your request",
    websocket=websocket
)

# Linux 服务会话
session = factory.create_service_session(
    task="task_name",
    should_evaluate=False,
    id="session_id",
    request="your request",
    websocket=websocket,
    application_name="app_name",
    platform_override="linux"
)
```

### 直接创建

```python
# Windows
from ufo.module.sessions.session import Session
session = Session(task, should_evaluate, id, request, mode)

# Linux
from ufo.module.sessions.linux_session import LinuxSession
session = LinuxSession(task, should_evaluate, id, request, mode, application_name)
```

## 支持的模式

| 平台 | normal | service | follower | batch_normal | operator |
|------|--------|---------|----------|--------------|----------|
| Windows | ✓ | ✓ | ✓ | ✓ | ✓ |
| Linux | ✓ | ✓ | ✗ | ✗ | ✗ |

## 关键差异

| 特性 | Windows Session | Linux Session |
|------|-----------------|---------------|
| HostAgent | ✓ 有 | ✗ 无 |
| 架构 | HostAgent → AppAgent | 直接 AppAgent |
| application_name | 可选 | **必需** |
| 任务规划 | HostAgent 负责 | AppAgent 直接执行 |

## 常用属性和方法

```python
session = ...  # 任意 Session 实例

# 属性
session.host_agent          # Windows: HostAgent, Linux: None
session.context             # Context 对象
session.total_rounds        # 总轮数
session.current_round       # 当前轮
session.cost               # 总成本

# 方法
await session.run()        # 运行 session
session.is_finished()      # 是否完成
session.add_round(id, round)  # 添加轮次
```

## 抽象方法（子类必须实现）

```python
class MySession(WindowsBaseSession):  # 或 LinuxBaseSession
    
    def _init_agents(self):
        """初始化 agents（可选择覆盖）"""
        super()._init_agents()
    
    def create_new_round(self):
        """创建新轮次"""
        pass
    
    def next_request(self):
        """获取下一个请求"""
        pass
    
    def request_to_evaluate(self):
        """获取用于评估的请求"""
        pass
```

## 平台检测

```python
import platform

# 自动检测
current = platform.system().lower()  # 'windows' 或 'linux'

# 手动指定
factory.create_session(..., platform_override="linux")
```

## 错误处理

```python
try:
    sessions = factory.create_session(
        task="task",
        mode="unsupported_mode",
        plan="",
        request=""
    )
except ValueError as e:
    print(f"Unsupported mode: {e}")

try:
    sessions = factory.create_session(
        task="task",
        mode="normal",
        plan="",
        request="",
        platform_override="macos"  # 不支持
    )
except NotImplementedError as e:
    print(f"Platform not supported: {e}")
```

## 最佳实践

1. **优先使用 SessionFactory**
   ```python
   # 好
   factory = SessionFactory()
   sessions = factory.create_session(...)
   
   # 可以，但不推荐
   session = Session(...)
   ```

2. **Linux 会话总是指定 application_name**
   ```python
   # 好
   sessions = factory.create_session(
       ..., 
       platform_override="linux",
       application_name="firefox"
   )
   
   # 坏 - 可能失败
   sessions = factory.create_session(
       ..., 
       platform_override="linux"
   )
   ```

3. **检查 host_agent 存在性**
   ```python
   if session.host_agent:
       # Windows session
       host_agent = session.host_agent
   else:
       # Linux session
       # 直接使用 app agent
   ```

4. **使用类型提示**
   ```python
   from ufo.module.basic import BaseSession
   from ufo.module.sessions.session import Session
   from ufo.module.sessions.linux_session import LinuxSession
   
   def process_session(session: BaseSession) -> None:
       # 可以处理任何平台的 session
       pass
   ```

## 配置文件

确保配置文件中包含必要的设置：

```yaml
# config.yaml
EVA_SESSION: false
EVA_ROUND: false
MAX_STEP: 100
MAX_ROUND: 10

APP_AGENT:
  VISUAL_MODE: true
  API_MODEL: "gpt-4-vision-preview"

HOST_AGENT:  # 仅 Windows 需要
  VISUAL_MODE: true
  API_MODEL: "gpt-4-vision-preview"

APPAGENT_PROMPT: "prompts/app_agent.txt"
HOSTAGENT_PROMPT: "prompts/host_agent.txt"
```

## 调试技巧

```python
# 打印 session 信息
print(f"Session type: {session.__class__.__name__}")
print(f"Platform: {session.context.get(ContextNames.PLATFORM)}")
print(f"Has HostAgent: {session.host_agent is not None}")
print(f"Mode: {session.context.get(ContextNames.MODE)}")

# 检查 session 状态
print(f"Finished: {session.is_finished()}")
print(f"Total rounds: {session.total_rounds}")
print(f"Current cost: ${session.cost:.2f}")

# 访问 context
from ufo.module.context import ContextNames
app_name = session.context.get(ContextNames.APPLICATION_PROCESS_NAME)
print(f"Application: {app_name}")
```

## 常见问题速查

**Q: Linux session 不工作？**
A: 检查是否提供了 `application_name` 参数

**Q: 如何知道使用的是哪个平台？**
A: `session.context.get(ContextNames.PLATFORM)` 或检查 `session.host_agent` 是否为 None

**Q: 可以混用 Windows 和 Linux session 吗？**
A: 技术上可以，但不推荐。每个平台的环境是独立的。

**Q: 如何添加新的 session 类型？**
A: 继承对应的 `PlatformBaseSession`，实现抽象方法，在 `SessionFactory` 中添加创建逻辑

## 相关文件

- `ufo/module/basic.py` - BaseSession
- `ufo/module/sessions/platform_session.py` - 平台基类
- `ufo/module/sessions/session.py` - Windows sessions
- `ufo/module/sessions/service_session.py` - Windows service
- `ufo/module/sessions/linux_session.py` - Linux sessions
- `ufo/module/session_pool.py` - SessionFactory
- `docs/session_architecture_guide.md` - 详细文档
- `examples/session_architecture_examples.py` - 示例代码
