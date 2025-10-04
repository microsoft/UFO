# UFO Server - Linux Support Guide

## 概述

UFO Server 现在支持 Linux 平台的 Service Session！通过 SessionFactory 和平台检测机制，可以在 Windows 和 Linux 上无缝运行 UFO 服务。

## 架构更新

### SessionManager 重构

`SessionManager` 已重构为使用 `SessionFactory`，支持创建平台特定的 Service Session：

```python
# 旧架构
session = ServiceSession(...)  # 仅支持 Windows

# 新架构
session = SessionFactory.create_service_session(
    ...,
    platform_override="linux",  # 支持 Windows 和 Linux
    application_name="firefox"
)
```

### 关键组件

1. **SessionManager** - 管理所有活动会话
   - 使用 `SessionFactory` 创建会话
   - 支持平台检测和覆盖
   - 支持 Linux 应用名称参数

2. **UFOWebSocketHandler** - 处理 WebSocket 连接
   - 从 `ClientMessage.metadata` 中提取平台信息
   - 支持动态平台选择

3. **app.py** - 服务入口
   - 支持 `--platform` 命令行参数
   - 自动平台检测

## 启动服务器

### Windows（默认）

```bash
# 自动检测为 Windows
python -m ufo.server.app

# 显式指定 Windows
python -m ufo.server.app --platform windows

# 自定义端口
python -m ufo.server.app --port 8000 --host 127.0.0.1
```

### Linux

```bash
# 自动检测为 Linux
python -m ufo.server.app

# 显式指定 Linux
python -m ufo.server.app --platform linux

# 自定义配置
python -m ufo.server.app --platform linux --port 8080 --host 0.0.0.0
```

### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--host` | `0.0.0.0` | 服务器主机地址 |
| `--port` | `5000` | 服务器端口 |
| `--platform` | `None` | 平台覆盖（`windows` 或 `linux`）<br>不指定时自动检测 |

## 客户端使用

### WebSocket 连接

#### 注册消息

```json
{
  "type": "REGISTER",
  "status": "PENDING",
  "client_type": "DEVICE",
  "client_id": "my_client_001",
  "timestamp": "2025-10-04T12:00:00Z"
}
```

#### 任务消息（Windows）

```json
{
  "type": "TASK",
  "status": "PENDING",
  "client_type": "DEVICE",
  "client_id": "my_client_001",
  "session_id": "session_001",
  "task_name": "windows_task",
  "request": "Open Microsoft Word and create a document",
  "timestamp": "2025-10-04T12:00:00Z"
}
```

#### 任务消息（Linux）

```json
{
  "type": "TASK",
  "status": "PENDING",
  "client_type": "DEVICE",
  "client_id": "linux_client_001",
  "session_id": "linux_session_001",
  "task_name": "linux_task",
  "request": "Open Firefox and search for Python",
  "timestamp": "2025-10-04T12:00:00Z",
  "metadata": {
    "platform": "linux",
    "application_name": "firefox"
  }
}
```

**重要：** Linux 任务必须在 `metadata` 中指定：
- `platform`: `"linux"`
- `application_name`: 目标应用名称（如 `"firefox"`, `"gedit"`, `"libreoffice"` 等）

### Python 客户端示例

#### Windows 客户端

```python
import asyncio
import json
import websockets

async def windows_client():
    uri = "ws://localhost:5000/ws"
    
    async with websockets.connect(uri) as websocket:
        # 注册
        register_msg = {
            "type": "REGISTER",
            "status": "PENDING",
            "client_type": "DEVICE",
            "client_id": "windows_client_001",
            "timestamp": "2025-10-04T12:00:00Z"
        }
        await websocket.send(json.dumps(register_msg))
        response = await websocket.recv()
        print(f"Registration response: {response}")
        
        # 发送任务
        task_msg = {
            "type": "TASK",
            "status": "PENDING",
            "client_id": "windows_client_001",
            "session_id": "win_session_001",
            "task_name": "word_task",
            "request": "Open Word and create a new document",
            "timestamp": "2025-10-04T12:00:00Z"
        }
        await websocket.send(json.dumps(task_msg))
        
        # 接收结果
        while True:
            response = await websocket.recv()
            print(f"Response: {response}")
            data = json.loads(response)
            if data.get("type") == "TASK_END":
                break

asyncio.run(windows_client())
```

#### Linux 客户端

```python
import asyncio
import json
import websockets

async def linux_client():
    uri = "ws://localhost:5000/ws"
    
    async with websockets.connect(uri) as websocket:
        # 注册
        register_msg = {
            "type": "REGISTER",
            "status": "PENDING",
            "client_type": "DEVICE",
            "client_id": "linux_client_001",
            "timestamp": "2025-10-04T12:00:00Z"
        }
        await websocket.send(json.dumps(register_msg))
        response = await websocket.recv()
        print(f"Registration response: {response}")
        
        # 发送 Linux 任务
        task_msg = {
            "type": "TASK",
            "status": "PENDING",
            "client_id": "linux_client_001",
            "session_id": "linux_session_001",
            "task_name": "firefox_task",
            "request": "Open Firefox and search for Python tutorials",
            "timestamp": "2025-10-04T12:00:00Z",
            "metadata": {
                "platform": "linux",
                "application_name": "firefox"
            }
        }
        await websocket.send(json.dumps(task_msg))
        
        # 接收结果
        while True:
            response = await websocket.recv()
            print(f"Response: {response}")
            data = json.loads(response)
            if data.get("type") == "TASK_END":
                break

asyncio.run(linux_client())
```

## SessionManager API

### 初始化

```python
from ufo.server.services.session_manager import SessionManager

# 自动检测平台
manager = SessionManager()

# Windows 专用
manager = SessionManager(platform_override="windows")

# Linux 专用
manager = SessionManager(platform_override="linux")
```

### 创建会话

```python
# Windows 会话
session = manager.get_or_create_session(
    session_id="win_session_001",
    task_name="windows_task",
    request="Open Excel",
    websocket=websocket
)

# Linux 会话
session = manager.get_or_create_session(
    session_id="linux_session_001",
    task_name="linux_task",
    request="Open Firefox",
    websocket=websocket,
    application_name="firefox",
    platform_override="linux"
)
```

### 获取结果

```python
# 通过 session_id
result = manager.get_result("session_001")

# 通过 task_name
result = manager.get_result_by_task("firefox_task")
```

## 平台特性对比

| 特性 | Windows | Linux |
|------|---------|-------|
| HostAgent | ✓ | ✗ |
| 自动应用检测 | ✓ | ✗（需指定） |
| 多应用切换 | ✓ | 单应用 |
| application_name | 可选 | **必需** |
| WebSocket 支持 | ✓ | ✓ |
| 命令执行 | ✓ | ✓ |

## 支持的 Linux 应用

常见的 Linux GUI 应用（需要相应的自动化支持）：

- **浏览器**: `firefox`, `chrome`, `chromium`
- **办公**: `libreoffice`, `libreoffice-writer`, `libreoffice-calc`
- **编辑器**: `gedit`, `vim`, `code` (VS Code)
- **终端**: `gnome-terminal`, `konsole`, `xterm`
- **文件管理**: `nautilus`, `dolphin`, `thunar`

**注意：** 实际支持的应用取决于系统中安装的 UI 自动化工具和驱动。

## 配置文件

确保 `config.yaml` 包含必要的配置：

```yaml
# 通用配置
EVA_SESSION: false
MAX_STEP: 100
MAX_ROUND: 10

# Agent 配置
APP_AGENT:
  VISUAL_MODE: true
  API_MODEL: "gpt-4-vision-preview"

# Windows 特定（Linux 不需要）
HOST_AGENT:
  VISUAL_MODE: true
  API_MODEL: "gpt-4-vision-preview"

# Prompts
APPAGENT_PROMPT: "prompts/app_agent.txt"
HOSTAGENT_PROMPT: "prompts/host_agent.txt"

# 服务器配置
SERVER:
  HOST: "0.0.0.0"
  PORT: 5000
```

## 错误处理

### 常见错误

#### 1. Linux 会话缺少 application_name

**错误信息：**
```
ERROR - No application_name provided for Linux session
```

**解决方法：**
在 `ClientMessage.metadata` 中添加 `application_name`：
```json
{
  "metadata": {
    "platform": "linux",
    "application_name": "firefox"
  }
}
```

#### 2. 平台不支持

**错误信息：**
```
NotImplementedError: Platform macos is not supported yet
```

**解决方法：**
只使用支持的平台：`windows` 或 `linux`

#### 3. 应用未安装

**错误信息：**
```
ERROR - Application 'firefox' not found
```

**解决方法：**
确保目标应用已安装且在系统 PATH 中

## 调试技巧

### 启用详细日志

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### 检查会话类型

```python
session = manager.get_or_create_session(...)
print(f"Session type: {session.__class__.__name__}")
print(f"Platform: {session.context.get(ContextNames.PLATFORM)}")
print(f"Has HostAgent: {session.host_agent is not None}")
```

### 查看活动会话

```python
for session_id, session in manager.sessions.items():
    print(f"Session {session_id}:")
    print(f"  Type: {session.__class__.__name__}")
    print(f"  Platform: {session.context.get(ContextNames.PLATFORM)}")
    print(f"  Status: {'Running' if not session.is_finished() else 'Finished'}")
```

## 最佳实践

1. **总是为 Linux 指定 application_name**
   ```python
   # 好
   metadata = {"platform": "linux", "application_name": "firefox"}
   
   # 坏 - 会失败
   metadata = {"platform": "linux"}
   ```

2. **使用平台检测而非硬编码**
   ```python
   # 好 - 自动检测
   manager = SessionManager()
   
   # 可以，但不灵活
   manager = SessionManager(platform_override="windows")
   ```

3. **正确处理 WebSocket 消息**
   ```python
   # 检查任务状态
   if response["type"] == "TASK_END":
       if response["status"] == "COMPLETED":
           print("Success!")
       else:
           print(f"Failed: {response.get('error')}")
   ```

4. **清理会话**
   ```python
   # 任务完成后移除会话
   manager.remove_session(session_id)
   ```

## 测试

### 单元测试

```python
import pytest
from ufo.server.services.session_manager import SessionManager

def test_create_windows_session():
    manager = SessionManager(platform_override="windows")
    session = manager.get_or_create_session(
        session_id="test_win",
        task_name="test",
        request="test"
    )
    assert session.host_agent is not None

def test_create_linux_session():
    manager = SessionManager(platform_override="linux")
    session = manager.get_or_create_session(
        session_id="test_linux",
        task_name="test",
        request="test",
        application_name="firefox",
        platform_override="linux"
    )
    assert session.host_agent is None
```

### 集成测试

参考 `tests/clients/` 目录下的测试文件。

## 迁移指南

### 从旧版本迁移

**旧代码（仅 Windows）：**
```python
session_manager = SessionManager()
session = session_manager.get_or_create_session(
    session_id, task_name, request, websocket
)
```

**新代码（支持多平台）：**
```python
# Windows - 无需改动
session_manager = SessionManager()
session = session_manager.get_or_create_session(
    session_id, task_name, request, websocket
)

# Linux - 添加参数
session = session_manager.get_or_create_session(
    session_id=session_id,
    task_name=task_name,
    request=request,
    websocket=websocket,
    application_name="firefox",
    platform_override="linux"
)
```

## 相关文件

- `ufo/server/app.py` - 服务入口
- `ufo/server/services/session_manager.py` - Session 管理器
- `ufo/server/ws/handler.py` - WebSocket 处理器
- `ufo/module/session_pool.py` - SessionFactory
- `ufo/module/sessions/linux_session.py` - Linux Session 实现
- `docs/session_architecture_guide.md` - Session 架构文档

## 常见问题

**Q: 如何同时支持 Windows 和 Linux 客户端？**
A: 使用默认的自动检测，让客户端在 metadata 中指定平台。

**Q: Linux 上必须指定 application_name 吗？**
A: 是的，Linux Session 需要知道要控制哪个应用。

**Q: 可以在 Windows 上创建 Linux Session 吗？**
A: 可以创建 Session 对象，但实际执行会失败，因为 Linux 自动化工具不可用。

**Q: 如何添加新的 Linux 应用支持？**
A: 需要在 UI 自动化层面添加对应的驱动和控制逻辑。

## 下一步

- 实现 Linux UI 自动化驱动
- 添加更多 Linux 应用支持
- 优化跨平台性能
- 添加平台特定的配置选项
