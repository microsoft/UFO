# Session Architecture Refactoring - Usage Guide

## 概述

UFO 的 Session 架构已重构为支持多平台（Windows 和 Linux），采用清晰的继承层次和灵活的工厂模式。

## 架构层次

```
BaseSession (抽象基类)
├── WindowsBaseSession (Windows 平台基类)
│   ├── Session (普通 Windows Session)
│   ├── ServiceSession (Windows 服务 Session)
│   ├── FollowerSession (Windows Follower)
│   ├── FromFileSession (Windows 文件模式)
│   └── OpenAIOperatorSession (继承自 Session)
└── LinuxBaseSession (Linux 平台基类)
    ├── LinuxSession (普通 Linux Session)
    └── LinuxServiceSession (Linux 服务 Session)
```

## 主要特点

### 1. **平台抽象**
- `BaseSession`: 定义所有平台共享的基础功能
- `WindowsBaseSession`: Windows 特定功能（包含 HostAgent）
- `LinuxBaseSession`: Linux 特定功能（无 HostAgent，直接使用 AppAgent）

### 2. **核心差异**

#### Windows Sessions
- 使用两层架构：HostAgent -> AppAgent
- HostAgent 负责任务规划和应用选择
- AppAgent 执行具体操作

#### Linux Sessions
- 使用单层架构：直接使用 AppAgent
- 无需 HostAgent，简化流程
- 直接针对指定应用执行任务

### 3. **Session 类型**

| 平台 | 模式 | Session 类 | 说明 |
|------|------|-----------|------|
| Windows | normal | Session | 普通交互式会话 |
| Windows | service | ServiceSession | WebSocket 服务模式 |
| Windows | follower | FollowerSession | 跟随计划文件执行 |
| Windows | batch_normal | FromFileSession | 批量文件处理 |
| Windows | operator | OpenAIOperatorSession | OpenAI Operator 模式 |
| Linux | normal | LinuxSession | 普通交互式会话 |
| Linux | service | LinuxServiceSession | WebSocket 服务模式 |

## 使用方法

### 1. 使用 SessionFactory（推荐）

#### Windows 普通会话
```python
from ufo.module.session_pool import SessionFactory

factory = SessionFactory()
sessions = factory.create_session(
    task="my_task",
    mode="normal",
    plan="",
    request="Open Word and create a new document"
)
```

#### Linux 普通会话
```python
sessions = factory.create_session(
    task="my_task",
    mode="normal",
    plan="",
    request="Open Firefox and search for Python",
    platform_override="linux",  # 可选，自动检测
    application_name="firefox"  # Linux 需要指定应用
)
```

#### Windows 服务会话
```python
sessions = factory.create_session(
    task="service_task",
    mode="service",
    plan="",
    request="Create a PowerPoint presentation",
    websocket=my_websocket
)
```

#### Linux 服务会话
```python
sessions = factory.create_session(
    task="service_task",
    mode="service",
    plan="",
    request="Edit configuration file",
    platform_override="linux",
    application_name="gedit",
    websocket=my_websocket
)
```

### 2. 使用便捷方法创建服务会话

```python
# 自动检测平台
session = factory.create_service_session(
    task="my_service",
    should_evaluate=False,
    id="session_001",
    request="Open application",
    websocket=my_websocket,
    application_name="firefox"  # Linux 使用，Windows 忽略
)

# 显式指定平台
session = factory.create_service_session(
    task="my_service",
    should_evaluate=False,
    id="session_002",
    request="Open LibreOffice",
    websocket=my_websocket,
    application_name="libreoffice",
    platform_override="linux"
)
```

### 3. 直接创建 Session 实例

#### Windows
```python
from ufo.module.sessions.session import Session
from ufo.module.sessions.service_session import ServiceSession

# 普通会话
session = Session(
    task="task1",
    should_evaluate=True,
    id=0,
    request="Open Excel",
    mode="normal"
)

# 服务会话
service_session = ServiceSession(
    task="task2",
    should_evaluate=False,
    id="service_001",
    request="Create document",
    websocket=my_websocket
)
```

#### Linux
```python
from ufo.module.sessions.linux_session import LinuxSession, LinuxServiceSession

# 普通会话
linux_session = LinuxSession(
    task="linux_task",
    should_evaluate=True,
    id=0,
    request="Open terminal",
    mode="normal",
    application_name="gnome-terminal"
)

# 服务会话
linux_service = LinuxServiceSession(
    task="linux_service",
    should_evaluate=False,
    id="linux_001",
    request="Edit file",
    websocket=my_websocket,
    application_name="vim"
)
```

## 扩展指南

### 添加新的 Windows Session 类型

1. 继承 `WindowsBaseSession`
2. 实现必需的抽象方法

```python
from ufo.module.sessions.platform_session import WindowsBaseSession

class MyWindowsSession(WindowsBaseSession):
    def create_new_round(self):
        # 实现逻辑
        pass
    
    def next_request(self):
        # 实现逻辑
        pass
    
    def request_to_evaluate(self):
        # 实现逻辑
        pass
```

### 添加新的 Linux Session 类型

1. 继承 `LinuxBaseSession`
2. 实现必需的抽象方法
3. 在 `SessionFactory` 中添加创建逻辑

```python
from ufo.module.sessions.platform_session import LinuxBaseSession

class MyLinuxSession(LinuxBaseSession):
    def create_new_round(self):
        # 实现逻辑（无需 HostAgent）
        pass
    
    def next_request(self):
        # 实现逻辑
        pass
    
    def request_to_evaluate(self):
        # 实现逻辑
        pass
```

### 添加新平台支持（如 macOS）

1. 在 `platform_session.py` 中创建 `MacOSBaseSession`
2. 实现 `_init_agents()` 方法
3. 创建具体的 macOS Session 类
4. 在 `SessionFactory` 中添加 macOS 分支

```python
# platform_session.py
class MacOSBaseSession(BaseSession):
    def _init_agents(self):
        # macOS 特定的 agent 初始化
        pass

# SessionFactory
def _create_macos_session(self, task, mode, plan, request, **kwargs):
    if mode == "normal":
        return [MacOSSession(...)]
    # ...
```

## 设计优势

1. **符合 SOLID 原则**
   - 单一职责：每个类只负责一个平台或功能
   - 开闭原则：扩展开放，修改关闭
   - 里氏替换：子类可替换父类
   - 接口隔离：平台特定方法在对应基类
   - 依赖倒置：依赖抽象而非具体实现

2. **清晰的职责分离**
   - 平台无关逻辑在 `BaseSession`
   - 平台特定逻辑在对应的 `PlatformBaseSession`
   - 具体功能在各自的 Session 子类

3. **易于测试和维护**
   - 模块化设计便于单元测试
   - 清晰的继承关系便于理解和维护
   - 工厂模式集中创建逻辑

4. **向后兼容**
   - 现有的 Windows Session 代码无需修改
   - 逐步迁移到新架构
   - 支持混合使用

## 迁移指南

### 从旧代码迁移

**旧代码：**
```python
from ufo.module.sessions.session import Session

session = Session(task="task1", should_evaluate=True, id=0, request="Open Word")
```

**新代码（无需修改）：**
```python
# Session 现在继承自 WindowsBaseSession，向后兼容
from ufo.module.sessions.session import Session

session = Session(task="task1", should_evaluate=True, id=0, request="Open Word")
```

**推荐使用工厂模式：**
```python
from ufo.module.session_pool import SessionFactory

factory = SessionFactory()
sessions = factory.create_session(
    task="task1",
    mode="normal",
    plan="",
    request="Open Word"
)
session = sessions[0]
```

## 注意事项

1. **Linux 会话需要指定应用名称**
   ```python
   # 正确
   LinuxSession(..., application_name="firefox")
   
   # 错误 - 可能导致问题
   LinuxSession(...)  # application_name 为 None
   ```

2. **平台检测**
   - 默认使用 `platform.system()` 自动检测
   - 可通过 `platform_override` 参数覆盖
   - 用于测试和跨平台开发

3. **HostAgent 访问**
   ```python
   # Windows Session
   host_agent = session.host_agent  # 返回 HostAgent 实例
   
   # Linux Session
   host_agent = session.host_agent  # 返回 None
   ```

4. **扩展 SessionFactory**
   - 添加新模式时更新 `_create_windows_session` 或 `_create_linux_session`
   - 保持一致的参数命名和错误处理

## 常见问题

**Q: 为什么 Linux 不需要 HostAgent？**
A: Linux 环境下的 GUI 应用通常更独立，不需要复杂的应用选择和切换逻辑。直接使用 AppAgent 可以简化架构并提高效率。

**Q: 如何在 Windows 上测试 Linux Session？**
A: 使用 `platform_override` 参数：
```python
sessions = factory.create_session(
    ...,
    platform_override="linux"
)
```

**Q: 可以混合使用不同平台的 Session 吗？**
A: 理论上可以，但不推荐。每个平台的 Session 设计用于各自的环境。

**Q: 如何添加新的 Session 模式？**
A: 
1. 继承对应的平台基类
2. 实现必需方法
3. 在 `SessionFactory` 中添加创建逻辑

## 相关文件

- `ufo/module/basic.py` - BaseSession 和 BaseRound
- `ufo/module/sessions/platform_session.py` - 平台基类
- `ufo/module/sessions/session.py` - Windows Session 实现
- `ufo/module/sessions/service_session.py` - Windows ServiceSession
- `ufo/module/sessions/linux_session.py` - Linux Session 实现
- `ufo/module/session_pool.py` - SessionFactory 和 SessionPool
