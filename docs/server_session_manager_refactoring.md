# Server SessionManager 重构总结

## 改动概述

SessionManager 已重构为使用 SessionFactory，支持创建 Windows 和 Linux 的 Service Session。

## 主要改动

### 1. SessionManager (ufo/server/services/session_manager.py)

#### 改动前
```python
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, ServiceSession] = {}
        # ...
    
    def get_or_create_session(
        self, session_id, task_name, request, websocket
    ) -> ServiceSession:
        session = ServiceSession(...)  # 只能创建 Windows Session
```

#### 改动后
```python
class SessionManager:
    def __init__(self, platform_override: Optional[str] = None):
        self.sessions: Dict[str, BaseSession] = {}
        self.platform = platform_override or platform.system().lower()
        self.session_factory = SessionFactory()
    
    def get_or_create_session(
        self,
        session_id,
        task_name,
        request,
        websocket,
        application_name: Optional[str] = None,  # 新增：Linux 需要
        platform_override: Optional[str] = None,  # 新增：平台覆盖
    ) -> BaseSession:
        session = self.session_factory.create_service_session(
            task=task_name,
            should_evaluate=configs.get("EVA_SESSION", False),
            id=session_id,
            request=request or "",
            websocket=websocket,
            application_name=application_name,
            platform_override=target_platform,
        )
```

**关键变化：**
- ✅ 添加 `platform_override` 参数支持平台检测和覆盖
- ✅ 添加 `application_name` 参数支持 Linux 应用指定
- ✅ 使用 `SessionFactory` 创建平台特定的 Session
- ✅ Sessions 类型从 `ServiceSession` 改为 `BaseSession`
- ✅ 添加详细的日志记录（包含平台和应用信息）

### 2. App.py (ufo/server/app.py)

#### 改动前
```python
def parse_args():
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    return parser.parse_args()

session_manager = SessionManager()
```

#### 改动后
```python
def parse_args():
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument(
        "--platform",
        type=str,
        default=None,
        choices=["windows", "linux"],
        help="Platform override (auto-detected if not specified)"
    )
    return parser.parse_args()

cli_args = parse_args()
session_manager = SessionManager(platform_override=cli_args.platform)
```

**关键变化：**
- ✅ 添加 `--platform` 命令行参数
- ✅ 提前解析参数以获取平台配置
- ✅ 将平台配置传递给 SessionManager

### 3. Handler.py (ufo/server/ws/handler.py)

#### 改动前
```python
session = self.session_manager.get_or_create_session(
    session_id, task_name, data.request, target_ws
)
```

#### 改动后
```python
# 从 metadata 提取平台和应用信息
platform_override = None
application_name = None
if data.metadata:
    platform_override = data.metadata.get("platform")
    application_name = data.metadata.get("application_name")

session = self.session_manager.get_or_create_session(
    session_id=session_id,
    task_name=task_name,
    request=data.request,
    websocket=target_ws,
    application_name=application_name,
    platform_override=platform_override,
)
```

**关键变化：**
- ✅ 从 `ClientMessage.metadata` 中提取平台信息
- ✅ 支持客户端指定平台和应用
- ✅ 使用命名参数提高可读性

## 新增功能

### 1. 平台检测

```python
# 自动检测
manager = SessionManager()  # 使用 platform.system()

# 手动指定
manager = SessionManager(platform_override="linux")

# 命令行指定
python -m ufo.server.app --platform linux
```

### 2. Linux Service Session 支持

```python
# 创建 Linux Service Session
session = manager.get_or_create_session(
    session_id="linux_001",
    task_name="firefox_task",
    request="Open Firefox",
    websocket=websocket,
    application_name="firefox",  # Linux 必需
    platform_override="linux"
)

# Session 类型
assert session.__class__.__name__ == "LinuxServiceSession"
assert session.host_agent is None
```

### 3. 客户端 Metadata 支持

客户端可以在 WebSocket 消息中指定平台：

```json
{
  "type": "TASK",
  "request": "Open Firefox",
  "metadata": {
    "platform": "linux",
    "application_name": "firefox"
  }
}
```

## 使用示例

### Windows（无需改动）

```bash
# 启动服务器
python -m ufo.server.app

# 或显式指定
python -m ufo.server.app --platform windows
```

### Linux

```bash
# 启动服务器
python -m ufo.server.app --platform linux

# 客户端发送任务
{
  "type": "TASK",
  "request": "Open Firefox and search",
  "metadata": {
    "platform": "linux",
    "application_name": "firefox"
  }
}
```

## 向后兼容性

✅ 完全向后兼容！现有的 Windows 客户端无需任何修改：

```python
# 旧代码继续工作
session = manager.get_or_create_session(
    session_id, task_name, request, websocket
)
# 自动创建 Windows Session（如果在 Windows 上）
```

## 测试

### 单元测试需要更新

```python
# 旧测试
manager = SessionManager()
session = manager.get_or_create_session(id, task, req, ws)
assert isinstance(session, ServiceSession)

# 新测试
manager = SessionManager(platform_override="windows")
session = manager.get_or_create_session(
    session_id=id, task_name=task, request=req, websocket=ws
)
assert isinstance(session, BaseSession)  # 或更具体的类型检查
```

## 文件清单

### 修改的文件
1. `ufo/server/services/session_manager.py` - 使用 SessionFactory
2. `ufo/server/app.py` - 添加平台参数
3. `ufo/server/ws/handler.py` - 支持 metadata 提取

### 新增的文档
1. `docs/server_linux_support_guide.md` - Linux 支持完整指南

## 依赖关系

```
app.py
  └─> SessionManager(platform_override)
       └─> SessionFactory
            ├─> WindowsBaseSession
            │    └─> ServiceSession
            └─> LinuxBaseSession
                 └─> LinuxServiceSession
```

## 配置示例

### 启动参数

```bash
# 自动检测平台
python -m ufo.server.app

# Windows
python -m ufo.server.app --platform windows --port 5000

# Linux
python -m ufo.server.app --platform linux --port 8080 --host 0.0.0.0
```

### 客户端 Metadata

```python
# Windows 客户端（metadata 可选）
{
    "type": "TASK",
    "request": "Open Word"
}

# Linux 客户端（metadata 必需）
{
    "type": "TASK",
    "request": "Open Firefox",
    "metadata": {
        "platform": "linux",
        "application_name": "firefox"
    }
}
```

## 注意事项

1. **Linux Session 必须指定 application_name**
   - 通过 `metadata.application_name` 或
   - 通过 `get_or_create_session(application_name=...)`

2. **平台检测优先级**
   - ClientMessage.metadata.platform（最高）
   - get_or_create_session 的 platform_override
   - SessionManager 的 platform
   - 系统自动检测（最低）

3. **Session 类型**
   - Windows: `ServiceSession` (继承自 `WindowsBaseSession`)
   - Linux: `LinuxServiceSession` (继承自 `LinuxBaseSession`)

## 下一步

- [ ] 更新单元测试和集成测试
- [ ] 实现 Linux UI 自动化驱动
- [ ] 添加更多 Linux 应用支持
- [ ] 优化错误消息和日志
- [ ] 添加性能监控

## 相关文档

- `docs/session_architecture_guide.md` - Session 架构总体设计
- `docs/session_refactoring_summary.md` - Session 重构总结
- `docs/server_linux_support_guide.md` - Server Linux 支持指南
