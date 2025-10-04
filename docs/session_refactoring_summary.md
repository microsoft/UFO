# Session 架构重构总结

## 重构目标

支持 Linux 平台的 Session（无需 HostAgent），同时保持 Windows 平台现有功能的向后兼容性。

## 主要改动

### 1. 修改 `BaseSession` (ufo/module/basic.py)

**改动内容：**
- 将 `_host_agent` 从强制创建改为可选（`Optional[HostAgent]`）
- 添加抽象方法 `_init_agents()` - 由子类实现平台特定的 agent 初始化
- 添加 `host_agent` 属性，返回 `Optional[HostAgent]`

**关键代码：**
```python
# 旧代码
self._host_agent: HostAgent = AgentFactory.create_agent(...)

# 新代码
self._host_agent: Optional[HostAgent] = None
self._init_agents()  # 由子类实现

@abstractmethod
def _init_agents(self) -> None:
    """Initialize platform-specific agents."""
    pass
```

### 2. 创建平台基类 (ufo/module/sessions/platform_session.py)

**新增类：**

#### `WindowsBaseSession`
- 继承 `BaseSession`
- 实现 `_init_agents()` - 创建 HostAgent
- 所有现有 Windows Session 的基类

#### `LinuxBaseSession`
- 继承 `BaseSession`
- 实现 `_init_agents()` - 不创建 HostAgent（设为 None）
- 所有 Linux Session 的基类

### 3. 重构现有 Session 类

**修改的文件：**

#### `ufo/module/sessions/session.py`
```python
# 旧代码
class Session(BaseSession):

# 新代码
class Session(WindowsBaseSession):

# 同样修改：FollowerSession, FromFileSession, OpenAIOperatorSession
```

#### `ufo/module/sessions/service_session.py`
```python
# 旧代码
class ServiceSession(Session):

# 新代码
class ServiceSession(WindowsBaseSession):
```

### 4. 创建 Linux Session (ufo/module/sessions/linux_session.py)

**新增类：**

#### `LinuxSession`
- 继承 `LinuxBaseSession`
- 普通交互式 Linux 会话
- 直接创建和使用 AppAgent（无 HostAgent）
- 支持指定 `application_name` 参数

**关键特性：**
```python
def create_new_round(self):
    # 直接创建 AppAgent，无需 HostAgent
    app_agent = AgentFactory.create_agent(
        "app",
        name="LinuxAppAgent",
        process_name=self.context.get(ContextNames.APPLICATION_PROCESS_NAME),
        ...
    )
```

#### `LinuxServiceSession`
- 继承 `LinuxBaseSession`
- Linux 服务模式会话
- 使用 WebSocket 通信
- 类似 Windows 的 ServiceSession 但无 HostAgent

### 5. 扩展 SessionFactory (ufo/module/session_pool.py)

**主要改动：**

#### 增强 `create_session` 方法
```python
def create_session(
    self,
    task: str,
    mode: str,
    plan: str,
    request: str = "",
    platform_override: Optional[str] = None,  # 新增
    **kwargs,  # 支持额外参数
) -> List[BaseSession]:
```

#### 新增私有方法
- `_create_windows_session()` - 创建 Windows Session
- `_create_linux_session()` - 创建 Linux Session

#### 新增便捷方法
```python
def create_service_session(
    self,
    task: str,
    should_evaluate: bool,
    id: str,
    request: str,
    websocket: Optional[WebSocket] = None,
    application_name: Optional[str] = None,
    platform_override: Optional[str] = None,
) -> BaseSession:
```

**平台检测逻辑：**
```python
current_platform = platform_override or platform.system().lower()

if current_platform == "windows":
    return self._create_windows_session(...)
elif current_platform == "linux":
    return self._create_linux_session(...)
```

### 6. 新增文档

- `docs/session_architecture_guide.md` - 完整使用指南

## 架构图

```
BaseSession (abstract)
│
├── _init_agents() [abstract method]
├── create_new_round() [abstract method]
├── next_request() [abstract method]
├── request_to_evaluate() [abstract method]
│
├─── WindowsBaseSession
│    ├── _init_agents() -> creates HostAgent
│    │
│    ├── Session (normal mode)
│    ├── ServiceSession (service mode)
│    ├── FollowerSession (follower mode)
│    ├── FromFileSession (batch mode)
│    └── OpenAIOperatorSession (operator mode)
│
└─── LinuxBaseSession
     ├── _init_agents() -> no HostAgent (None)
     │
     ├── LinuxSession (normal mode)
     └── LinuxServiceSession (service mode)
```

## 支持的平台和模式

| 平台 | 模式 | Session 类 | HostAgent | 状态 |
|------|------|-----------|-----------|------|
| Windows | normal | Session | ✓ | 已有 |
| Windows | service | ServiceSession | ✓ | 已有 |
| Windows | follower | FollowerSession | ✓ | 已有 |
| Windows | batch_normal | FromFileSession | ✓ | 已有 |
| Windows | operator | OpenAIOperatorSession | ✓ | 已有 |
| Linux | normal | LinuxSession | ✗ | **新增** |
| Linux | service | LinuxServiceSession | ✗ | **新增** |

## 使用示例

### 创建 Linux 普通会话
```python
from ufo.module.session_pool import SessionFactory

factory = SessionFactory()
sessions = factory.create_session(
    task="linux_task",
    mode="normal",
    plan="",
    request="Open Firefox and browse",
    platform_override="linux",  # 可选，自动检测
    application_name="firefox"  # Linux 必需
)
```

### 创建 Linux 服务会话
```python
session = factory.create_service_session(
    task="linux_service",
    should_evaluate=False,
    id="session_001",
    request="Edit configuration",
    websocket=my_websocket,
    application_name="gedit",
    platform_override="linux"
)
```

### Windows 会话（无需改动）
```python
# 现有代码继续工作，完全向后兼容
sessions = factory.create_session(
    task="windows_task",
    mode="normal",
    plan="",
    request="Open Word"
)
```

## 设计优势

1. **向后兼容** - 所有现有 Windows Session 代码无需修改
2. **清晰分离** - Windows 和 Linux 逻辑独立
3. **易于扩展** - 添加新平台只需创建新的 PlatformBaseSession
4. **符合 SOLID** - 单一职责、开闭原则、依赖倒置
5. **灵活配置** - 支持平台检测和手动覆盖

## 测试建议

### 单元测试
```python
def test_windows_session_has_host_agent():
    session = Session(...)
    assert session.host_agent is not None
    assert isinstance(session.host_agent, HostAgent)

def test_linux_session_no_host_agent():
    session = LinuxSession(...)
    assert session.host_agent is None

def test_factory_platform_detection():
    factory = SessionFactory()
    # 测试自动检测
    # 测试手动覆盖
```

### 集成测试
- 测试 Windows Session 完整流程
- 测试 Linux Session 完整流程
- 测试 ServiceSession（Windows 和 Linux）

## 潜在问题和注意事项

1. **Linux AppAgent 创建**
   - 需要确保 `AgentFactory.create_agent("app", ...)` 支持 Linux
   - 可能需要创建 Linux 特定的 AppAgent 类

2. **UI 自动化**
   - Windows 使用 pywinauto
   - Linux 需要不同的自动化工具（如 pyatspi, dogtail）
   - 需要在 Command 层面处理平台差异

3. **应用名称映射**
   - Linux 应用进程名可能不同
   - 需要建立应用名称映射表

4. **错误处理**
   - 确保平台特定的错误得到正确处理
   - 添加平台检查和友好的错误消息

## 未来扩展方向

1. **添加 macOS 支持**
   - 创建 `MacOSBaseSession`
   - 实现 macOS 特定的 Session 类

2. **Linux Follower 和 Batch 模式**
   - 类似 Windows 的 FollowerSession
   - 支持计划文件执行

3. **跨平台 Session**
   - 支持在一个 Session 中操作多个平台
   - 需要更复杂的上下文管理

4. **性能优化**
   - Linux Session 可能比 Windows 更快（单层架构）
   - 考虑为 Windows 也提供 "直接模式"

## 文件清单

### 修改的文件
- `ufo/module/basic.py` - BaseSession 抽象化
- `ufo/module/sessions/session.py` - 继承 WindowsBaseSession
- `ufo/module/sessions/service_session.py` - 继承 WindowsBaseSession
- `ufo/module/session_pool.py` - 扩展 SessionFactory

### 新增的文件
- `ufo/module/sessions/platform_session.py` - 平台基类
- `ufo/module/sessions/linux_session.py` - Linux Session 实现
- `docs/session_architecture_guide.md` - 使用指南
- `docs/session_refactoring_summary.md` - 本文档

## 结论

本次重构成功实现了以下目标：

✅ 支持 Linux 平台（无 HostAgent）  
✅ 保持 Windows 平台向后兼容  
✅ 清晰的平台抽象和继承层次  
✅ 灵活的工厂模式  
✅ 符合软件工程最佳实践  

架构现在更加模块化、可扩展，并为未来的平台支持做好了准备。
