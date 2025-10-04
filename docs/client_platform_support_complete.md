# UFO Client Platform Support - 重构完成 ✅

## 🎉 完成摘要

UFO Client 已成功添加平台支持功能，可以通过命令行参数指定平台和应用，或自动检测系统平台！

## ✅ 完成的工作

### 1. **client.py** - 命令行参数支持
- ✅ 添加 `import platform as platform_module`
- ✅ 添加 `--platform` 参数（`windows` | `linux`）
- ✅ 添加 `--application-name` 参数（Linux 必需）
- ✅ 实现自动平台检测逻辑
- ✅ 传递平台信息到 UFOClient
- ✅ 添加启动日志

### 2. **ufo_client.py** - UFOClient 类扩展
- ✅ 添加 `platform` 参数到 `__init__`
- ✅ 添加 `application_name` 参数到 `__init__`
- ✅ 存储平台和应用信息为实例属性

### 3. **websocket.py** - WebSocket 消息增强
- ✅ 在 `start_task` 中构建 `metadata`
- ✅ 将 `platform` 和 `application_name` 添加到 metadata
- ✅ 发送 metadata 到服务器
- ✅ 添加详细日志记录

### 4. **文档**
- ✅ `docs/client_platform_support_guide.md` - 完整使用指南

## 📊 架构变化

### 改动前
```python
# 客户端固定行为，无法指定平台
client = UFOClient(
    mcp_server_manager=mcp_server_manager,
    computer_manager=computer_manager,
    client_id=args.client_id,
)
```

### 改动后
```python
# 支持平台和应用配置
client = UFOClient(
    mcp_server_manager=mcp_server_manager,
    computer_manager=computer_manager,
    client_id=args.client_id,
    platform=args.platform,           # 新增
    application_name=args.application_name,  # 新增
)
```

## 🚀 使用方法

### Windows 客户端（自动检测）
```bash
python -m ufo.client.client --ws --request "Open Word"
```

### Linux 客户端（指定应用）
```bash
python -m ufo.client.client \
  --ws \
  --application-name firefox \
  --request "Open Firefox and search"
```

### 显式指定平台
```bash
# Windows
python -m ufo.client.client --ws --platform windows --request "Open Excel"

# Linux
python -m ufo.client.client \
  --ws \
  --platform linux \
  --application-name gedit \
  --request "Edit file"
```

## 📝 关键特性

### 1. 自动平台检测 ✅
```python
# 在 client.py 中
if args.platform is None:
    detected_platform = platform_module.system().lower()
    if detected_platform in ["windows", "linux"]:
        args.platform = detected_platform
    else:
        args.platform = "windows"  # 默认回退
```

### 2. Metadata 传递 ✅
```python
# 在 websocket.py 中
metadata = {}
if self.ufo_client.platform:
    metadata["platform"] = self.ufo_client.platform
if self.ufo_client.application_name:
    metadata["application_name"] = self.ufo_client.application_name

client_message = ClientMessage(
    ...
    metadata=metadata if metadata else None,
)
```

### 3. 日志记录 ✅
```
INFO - Platform detected/specified: linux
INFO - UFO Client initialized for platform: linux
INFO - Target application: firefox
INFO - [WS] Sending task with platform: linux, app: firefox
```

## 📋 新增命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--platform` | 字符串 | 自动检测 | 平台类型（`windows` 或 `linux`） |
| `--application-name` | 字符串 | None | 目标应用名称（Linux 必需） |

## 🔄 数据流

```
1. 命令行参数
   └─> --platform linux --application-name firefox

2. client.py
   └─> 解析参数，自动检测平台
       └─> args.platform = "linux"
       └─> args.application_name = "firefox"

3. UFOClient
   └─> 存储平台信息
       └─> self.platform = "linux"
       └─> self.application_name = "firefox"

4. WebSocket 消息
   └─> 构建 metadata
       └─> metadata = {
             "platform": "linux",
             "application_name": "firefox"
           }

5. 服务器端
   └─> 接收 metadata
       └─> 创建 LinuxServiceSession
```

## ✨ 平台对比

| 特性 | Windows | Linux |
|------|---------|-------|
| `--platform` | 可选（自动检测） | 可选（自动检测） |
| `--application-name` | 可选 | **必需** |
| 自动检测 | ✓ | ✓ |
| Metadata 发送 | ✓ | ✓ |

## 🎯 完整示例

### Windows 完整示例
```bash
python -m ufo.client.client \
  --ws \
  --client-id "windows_client_001" \
  --ws-server "ws://localhost:5000/ws" \
  --platform windows \
  --task_name "word_task" \
  --request "Create a Word document" \
  --log-level INFO \
  --max-retries 5
```

### Linux 完整示例
```bash
python -m ufo.client.client \
  --ws \
  --client-id "linux_client_001" \
  --ws-server "ws://localhost:5000/ws" \
  --platform linux \
  --application-name firefox \
  --task_name "browser_task" \
  --request "Open Firefox and browse" \
  --log-level DEBUG \
  --max-retries 3
```

## 📁 修改的文件

| 文件 | 改动 | 行数 |
|------|------|------|
| `ufo/client/client.py` | 添加平台参数和自动检测 | +30 |
| `ufo/client/ufo_client.py` | 添加 platform/application_name 属性 | +6 |
| `ufo/client/websocket.py` | 添加 metadata 构建和发送 | +15 |
| `docs/client_platform_support_guide.md` | 新增完整使用指南 | +600 |

## 🔍 代码变化详情

### client.py
```python
# 新增导入
import platform as platform_module

# 新增参数
parser.add_argument("--platform", ...)
parser.add_argument("--application-name", ...)

# 自动检测逻辑
if args.platform is None:
    detected_platform = platform_module.system().lower()
    # ...

# 传递给 UFOClient
client = UFOClient(..., platform=args.platform, application_name=args.application_name)
```

### ufo_client.py
```python
def __init__(
    self,
    ...,
    platform: Optional[str] = None,           # 新增
    application_name: Optional[str] = None,   # 新增
):
    self.platform = platform                   # 新增
    self.application_name = application_name   # 新增
```

### websocket.py
```python
# 构建 metadata
metadata = {}
if self.ufo_client.platform:
    metadata["platform"] = self.ufo_client.platform
if self.ufo_client.application_name:
    metadata["application_name"] = self.ufo_client.application_name

# 添加到消息
client_message = ClientMessage(..., metadata=metadata if metadata else None)

# 日志
self.logger.info(f"[WS] Sending task with platform: {platform}, app: {app}")
```

## ⚠️ 重要提示

### Linux 必须指定应用
```bash
# ❌ 错误 - Linux 缺少应用名称
python -m ufo.client.client --ws --platform linux --request "..."

# ✅ 正确
python -m ufo.client.client --ws --platform linux --application-name firefox --request "..."
```

### 平台检测优先级
1. `--platform` 命令行参数（最高）
2. 系统自动检测 `platform.system()`
3. 默认回退到 `windows`（如果检测失败）

## 🧪 测试建议

### 单元测试
```python
def test_windows_auto_detect():
    # 在 Windows 上运行应自动检测
    # 验证 args.platform == "windows"
    pass

def test_linux_with_app_name():
    # Linux + application_name
    # 验证 metadata 正确构建
    pass

def test_metadata_sent():
    # 验证 WebSocket 消息包含 metadata
    pass
```

### 集成测试
```bash
# 1. 启动服务器
python -m ufo.server.app --platform linux

# 2. 启动客户端
python -m ufo.client.client \
  --ws \
  --application-name firefox \
  --request "Test task"

# 3. 验证服务器创建了 LinuxServiceSession
```

## 📚 相关文档

- `docs/client_platform_support_guide.md` - 客户端使用指南
- `docs/server_linux_support_guide.md` - 服务器端 Linux 支持
- `docs/session_architecture_guide.md` - Session 架构设计
- `docs/server_refactoring_complete.md` - 服务器重构总结

## 🎊 总结

UFO Client 平台支持已完成：

✅ 添加 `--platform` 和 `--application-name` 参数  
✅ 实现自动平台检测  
✅ 通过 metadata 传递平台信息  
✅ 支持 Windows 和 Linux  
✅ 详细的日志记录  
✅ 完善的文档  

现在客户端可以：
- 🔍 自动检测系统平台
- ⚙️ 手动指定平台和应用
- 📡 通过 WebSocket 传递配置到服务器
- 📝 提供清晰的日志输出

完美配合服务器端的平台支持，实现了完整的 Windows 和 Linux 跨平台架构！🚀
