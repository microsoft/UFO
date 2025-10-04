# UFO Client - Platform Support Guide

## 概述

UFO Client 现在支持平台选择功能！可以通过命令行参数指定平台（Windows 或 Linux）和目标应用，如果不指定则自动检测系统平台。

## 新增功能

### 命令行参数

#### `--platform`
指定客户端运行的平台类型。

- **类型**: 字符串
- **可选值**: `windows` | `linux`
- **默认值**: 自动检测（使用 `platform.system()`）
- **说明**: 
  - 如果不指定，自动检测当前系统平台
  - 用于显式指定要连接的服务器平台类型

#### `--application-name`
指定目标应用程序名称（Linux 平台必需）。

- **类型**: 字符串
- **默认值**: None
- **说明**:
  - **Linux 必需**: Linux 平台必须指定目标应用
  - **Windows 可选**: Windows 平台可选，由 HostAgent 自动选择
  - 示例: `firefox`, `gedit`, `libreoffice`, `gnome-terminal`

## 使用方法

### Windows 客户端

#### 自动检测（推荐）
```bash
# 在 Windows 系统上运行，自动检测为 windows
python -m ufo.client.client --ws --request "Open Word and create a document"
```

#### 显式指定
```bash
# 显式指定 Windows 平台
python -m ufo.client.client \
  --ws \
  --platform windows \
  --request "Open Excel and create a spreadsheet"
```

### Linux 客户端

#### 自动检测 + 指定应用
```bash
# 在 Linux 系统上运行，自动检测平台，指定应用
python -m ufo.client.client \
  --ws \
  --application-name firefox \
  --request "Open Firefox and search for Python tutorials"
```

#### 显式指定平台和应用
```bash
# 显式指定 Linux 平台和应用
python -m ufo.client.client \
  --ws \
  --platform linux \
  --application-name gedit \
  --request "Open gedit and create a new file"
```

## 完整命令行参数示例

### Windows 示例

```bash
# 基本使用
python -m ufo.client.client \
  --ws \
  --client-id "windows_client_001" \
  --ws-server "ws://localhost:5000/ws" \
  --request "Open Notepad"

# 带任务名称
python -m ufo.client.client \
  --ws \
  --platform windows \
  --task_name "word_document_task" \
  --request "Create a Word document with title 'Meeting Notes'"

# 自定义服务器和日志
python -m ufo.client.client \
  --ws \
  --ws-server "ws://192.168.1.100:8080/ws" \
  --log-level DEBUG \
  --request "Open PowerPoint"
```

### Linux 示例

```bash
# Firefox 浏览器
python -m ufo.client.client \
  --ws \
  --platform linux \
  --application-name firefox \
  --request "Search for Python documentation"

# gedit 编辑器
python -m ufo.client.client \
  --ws \
  --application-name gedit \
  --task_name "edit_config" \
  --request "Open and edit configuration file"

# LibreOffice Writer
python -m ufo.client.client \
  --ws \
  --platform linux \
  --application-name libreoffice-writer \
  --request "Create a new document"

# 完整配置
python -m ufo.client.client \
  --ws \
  --client-id "linux_client_002" \
  --platform linux \
  --application-name gnome-terminal \
  --ws-server "ws://server.example.com:5000/ws" \
  --task_name "terminal_task" \
  --request "Open terminal and run commands" \
  --log-level INFO \
  --max-retries 5
```

## 参数详解

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--ws` | 是 | - | 启用 WebSocket 模式 |
| `--client-id` | 否 | `client_001` | 客户端 ID |
| `--ws-server` | 否 | `ws://localhost:5000/ws` | WebSocket 服务器地址 |
| `--platform` | 否 | 自动检测 | 平台类型 (`windows` 或 `linux`) |
| `--application-name` | Linux 必需 | None | 目标应用名称 |
| `--request` | 否 | None | 任务请求文本 |
| `--task_name` | 否 | UUID | 任务名称 |
| `--log-level` | 否 | `INFO` | 日志级别 |
| `--max-retries` | 否 | `5` | 最大重试次数 |

## 平台检测逻辑

```python
# 1. 命令行指定平台（最高优先级）
--platform linux

# 2. 未指定时自动检测
import platform
detected = platform.system().lower()  # 'windows', 'linux', 'darwin', etc.

# 3. 不支持的平台默认为 windows
if detected not in ['windows', 'linux']:
    platform = 'windows'
```

## 内部实现

### UFOClient 类

```python
class UFOClient:
    def __init__(
        self,
        mcp_server_manager: MCPServerManager,
        computer_manager: ComputerManager,
        client_id: Optional[str] = None,
        platform: Optional[str] = None,           # 新增
        application_name: Optional[str] = None,   # 新增
    ):
        self.client_id = client_id or "client_001"
        self.platform = platform                   # 存储平台信息
        self.application_name = application_name   # 存储应用名称
```

### WebSocket 消息格式

**发送的任务消息：**
```json
{
  "type": "TASK",
  "request": "Open Firefox and search",
  "task_name": "firefox_task",
  "session_id": "session_001",
  "client_id": "linux_client_001",
  "status": "CONTINUE",
  "timestamp": "2025-10-04T12:00:00Z",
  "metadata": {
    "platform": "linux",
    "application_name": "firefox"
  }
}
```

**注意：**
- `metadata` 字段包含平台和应用信息
- 服务器端使用这些信息创建相应的 Session

## 日志输出

### 启动时
```
INFO - Platform detected/specified: linux
INFO - UFO Client initialized for platform: linux
INFO - Target application: firefox
INFO - [WS] Connecting to ws://localhost:5000/ws
INFO - [WS] Registered as linux_client_001
```

### 发送任务时
```
INFO - [WS] Starting task: Open Firefox
INFO - [WS] Sending task with platform: linux, app: firefox
```

## 常见场景

### 场景 1: Windows 开发环境
```bash
# 在 Windows 上开发，连接本地服务器
python -m ufo.client.client --ws --request "Open Visual Studio Code"
# 自动检测为 windows，无需指定 --platform
```

### 场景 2: Linux 生产环境
```bash
# 在 Linux 服务器上运行
python -m ufo.client.client \
  --ws \
  --application-name firefox \
  --ws-server "ws://production-server:5000/ws" \
  --request "Monitor dashboard"
# 自动检测为 linux
```

### 场景 3: 跨平台测试
```bash
# 在 Windows 上测试 Linux 客户端行为
python -m ufo.client.client \
  --ws \
  --platform linux \
  --application-name firefox \
  --request "Test task"
# 显式指定 linux 平台
```

### 场景 4: 批处理脚本

**Windows 批处理 (run_windows_client.bat):**
```batch
@echo off
python -m ufo.client.client ^
  --ws ^
  --platform windows ^
  --client-id "batch_client_%DATE%_%TIME%" ^
  --request "Daily report generation"
```

**Linux Shell 脚本 (run_linux_client.sh):**
```bash
#!/bin/bash
python -m ufo.client.client \
  --ws \
  --platform linux \
  --application-name firefox \
  --client-id "batch_client_$(date +%Y%m%d_%H%M%S)" \
  --request "Daily dashboard check"
```

## 错误处理

### 错误 1: Linux 平台缺少应用名称
```
WARNING - Linux platform specified but no application_name provided
```
**解决方法：** 添加 `--application-name` 参数

### 错误 2: 不支持的平台
```
INFO - Platform detected/specified: darwin
WARNING - Unsupported platform darwin, using windows as default
```
**说明：** macOS 等不支持的平台会回退到 Windows

### 错误 3: 服务器连接失败
```
ERROR - [WS] Connection closed: Connection refused
INFO - [WS] Retrying in 2s...
```
**解决方法：** 检查服务器地址和端口，确保服务器正在运行

## 最佳实践

### 1. 总是为 Linux 指定应用名称
```bash
# 好
python -m ufo.client.client --ws --application-name firefox --request "..."

# 坏（可能失败）
python -m ufo.client.client --ws --request "..."
```

### 2. 使用有意义的客户端 ID
```bash
# 好 - 便于追踪和调试
--client-id "jenkins_build_123"
--client-id "user_alice_desktop"

# 可以但不推荐
--client-id "client_001"
```

### 3. 生产环境使用显式配置
```bash
# 生产环境 - 显式指定所有关键参数
python -m ufo.client.client \
  --ws \
  --platform linux \
  --application-name firefox \
  --ws-server "ws://prod-server:5000/ws" \
  --client-id "prod_client_001" \
  --log-level INFO \
  --max-retries 10
```

### 4. 开发环境使用默认值
```bash
# 开发环境 - 使用自动检测
python -m ufo.client.client --ws --request "Test task"
```

## 与服务器配合使用

### 服务器端启动
```bash
# Windows 服务器
python -m ufo.server.app --platform windows --port 5000

# Linux 服务器
python -m ufo.server.app --platform linux --port 5000

# 自动检测
python -m ufo.server.app
```

### 客户端连接
```bash
# 连接到 Windows 服务器
python -m ufo.client.client \
  --ws \
  --ws-server "ws://windows-server:5000/ws" \
  --request "Open Word"

# 连接到 Linux 服务器
python -m ufo.client.client \
  --ws \
  --ws-server "ws://linux-server:5000/ws" \
  --application-name firefox \
  --request "Open Firefox"
```

## 配置文件支持（未来功能）

**config.yaml 示例：**
```yaml
client:
  client_id: "my_client_001"
  platform: "linux"
  application_name: "firefox"
  ws_server: "ws://localhost:5000/ws"
  max_retries: 5
  log_level: "INFO"
```

**使用配置文件（计划中）：**
```bash
python -m ufo.client.client --config config.yaml --ws
```

## 调试技巧

### 启用详细日志
```bash
python -m ufo.client.client \
  --ws \
  --log-level DEBUG \
  --platform linux \
  --application-name firefox \
  --request "Debug task"
```

### 查看发送的消息
```python
# 在日志中查看
[WS] Sending task with platform: linux, app: firefox
[WS] Registered as linux_client_001
```

### 测试连接
```bash
# 简单连接测试（不发送任务）
python -m ufo.client.client --ws
# 应该能看到 "Registered as client_001"
```

## 相关文档

- `docs/server_linux_support_guide.md` - 服务器端 Linux 支持
- `docs/session_architecture_guide.md` - Session 架构设计
- `ufo/client/client.py` - 客户端入口
- `ufo/client/ufo_client.py` - UFOClient 实现
- `ufo/client/websocket.py` - WebSocket 客户端

## 常见问题

**Q: 不指定 --platform 会怎样？**
A: 自动检测系统平台（`platform.system()`）

**Q: Windows 需要指定 --application-name 吗？**
A: 不需要，Windows 有 HostAgent 自动选择应用

**Q: Linux 必须指定 --application-name 吗？**
A: 是的，Linux 需要知道要控制哪个应用

**Q: 可以在 Windows 上指定 --platform linux 吗？**
A: 可以，但实际执行会失败（Linux 自动化工具不可用）

**Q: 如何查看当前平台？**
A: 查看启动日志中的 "Platform detected/specified: ..."

## 总结

UFO Client 现在支持：
- ✅ 自动平台检测
- ✅ 手动平台覆盖
- ✅ Linux 应用名称指定
- ✅ 通过 metadata 传递平台信息
- ✅ 详细的日志记录

使用这些功能，可以在 Windows 和 Linux 上无缝运行 UFO 客户端！
