# UFO Server - SessionManager 重构完成 ✅

## 🎉 重构完成摘要

SessionManager 已成功重构，现在使用 SessionFactory 创建平台特定的 Service Session，支持 Windows 和 Linux！

## ✅ 完成的工作

### 1. **SessionManager 重构** ✅
- ✅ 添加 `SessionFactory` 集成
- ✅ 添加 `platform_override` 参数支持
- ✅ 添加 `application_name` 参数（Linux 必需）
- ✅ 自动平台检测（使用 `platform.system()`）
- ✅ 从 `Dict[str, ServiceSession]` 改为 `Dict[str, BaseSession]`
- ✅ 增强日志记录（平台、应用、Session 类型）

### 2. **App.py 更新** ✅
- ✅ 添加 `--platform` 命令行参数
- ✅ 支持 `windows` 和 `linux` 选项
- ✅ 提前解析参数以配置 SessionManager
- ✅ 启动日志显示平台信息

### 3. **Handler.py 增强** ✅
- ✅ 从 `ClientMessage.metadata` 提取平台信息
- ✅ 支持 `platform` 和 `application_name` metadata
- ✅ 传递平台参数到 SessionManager
- ✅ 使用命名参数提高代码可读性

### 4. **文档完善** ✅
- ✅ `docs/server_linux_support_guide.md` - 完整使用指南
- ✅ `docs/server_session_manager_refactoring.md` - 重构总结
- ✅ 包含客户端示例、API 文档、最佳实践

## 📊 架构对比

### 改动前
```
app.py
  └─> SessionManager()
       └─> ServiceSession()  # 仅 Windows
```

### 改动后
```
app.py (--platform)
  └─> SessionManager(platform_override)
       └─> SessionFactory
            ├─> ServiceSession (Windows)
            └─> LinuxServiceSession (Linux)
```

## 🚀 使用方法

### 启动服务器

```bash
# Windows（自动检测）
python -m ufo.server.app

# Linux（自动检测）
python -m ufo.server.app

# 显式指定平台
python -m ufo.server.app --platform linux --port 8080
```

### 客户端消息

**Windows:**
```json
{
  "type": "TASK",
  "request": "Open Word"
}
```

**Linux:**
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

## 📝 修改的文件

| 文件 | 改动 | 说明 |
|------|------|------|
| `ufo/server/services/session_manager.py` | 重构 | 使用 SessionFactory |
| `ufo/server/app.py` | 更新 | 添加 --platform 参数 |
| `ufo/server/ws/handler.py` | 增强 | 支持 metadata 提取 |
| `docs/server_linux_support_guide.md` | 新增 | 使用指南 |
| `docs/server_session_manager_refactoring.md` | 新增 | 重构总结 |

## 🔑 关键特性

1. **向后兼容** ✅
   - 现有 Windows 客户端无需修改
   - 自动检测平台

2. **灵活配置** ✅
   - 命令行参数覆盖
   - 客户端 metadata 覆盖
   - 多层次平台选择

3. **清晰日志** ✅
   ```
   INFO - SessionManager initialized for platform: linux
   INFO - Created new linux session: session_001 (type: LinuxServiceSession, app: firefox)
   ```

4. **类型安全** ✅
   - 使用 `BaseSession` 作为公共类型
   - 支持不同平台的 Session 子类

## 📖 平台支持

| 平台 | Session 类型 | HostAgent | application_name |
|------|-------------|-----------|------------------|
| Windows | ServiceSession | ✓ | 可选 |
| Linux | LinuxServiceSession | ✗ | **必需** |

## 🎯 关键改进

1. **SessionManager 更灵活**
   - 支持多平台
   - 使用工厂模式
   - 易于扩展（添加 macOS）

2. **Server 更智能**
   - 自动平台检测
   - 命令行配置
   - 客户端动态选择

3. **代码更清晰**
   - 职责分离
   - 命名参数
   - 详细日志

## ⚠️ 重要提示

### Linux Session 必需参数

Linux Session **必须**提供 `application_name`：

```python
# ❌ 错误 - 缺少 application_name
session = manager.get_or_create_session(
    session_id="linux_001",
    platform_override="linux"
)

# ✅ 正确
session = manager.get_or_create_session(
    session_id="linux_001",
    application_name="firefox",
    platform_override="linux"
)
```

### 平台覆盖优先级

1. `ClientMessage.metadata.platform`（最高）
2. `get_or_create_session(platform_override=...)`
3. `SessionManager(platform_override=...)`
4. 系统自动检测（最低）

## 🧪 测试建议

### 单元测试

```python
def test_windows_session():
    manager = SessionManager(platform_override="windows")
    session = manager.get_or_create_session(...)
    assert isinstance(session, ServiceSession)
    assert session.host_agent is not None

def test_linux_session():
    manager = SessionManager(platform_override="linux")
    session = manager.get_or_create_session(
        application_name="firefox",
        platform_override="linux",
        ...
    )
    assert isinstance(session, LinuxServiceSession)
    assert session.host_agent is None
```

### 集成测试

1. 启动服务器：`python -m ufo.server.app --platform linux`
2. 连接 WebSocket 客户端
3. 发送带 metadata 的任务消息
4. 验证创建的 Session 类型

## 📚 相关文档

- `docs/session_architecture_guide.md` - Session 架构设计
- `docs/session_refactoring_summary.md` - Session 重构总结
- `docs/server_linux_support_guide.md` - Server Linux 支持
- `docs/server_session_manager_refactoring.md` - 本次重构详情
- `examples/session_architecture_examples.py` - 代码示例

## 🚧 下一步工作

- [ ] 更新现有测试用例
- [ ] 实现 Linux UI 自动化驱动
- [ ] 添加更多 Linux 应用支持
- [ ] 性能测试和优化
- [ ] 添加集成测试示例

## ✨ 总结

SessionManager 重构已完成，完全符合之前的 Session 架构设计：

✅ 使用 SessionFactory 创建 Session  
✅ 支持 Windows 和 Linux 平台  
✅ 保持向后兼容性  
✅ 灵活的配置选项  
✅ 清晰的代码结构  
✅ 完善的文档  

现在 UFO Server 可以在 Windows 和 Linux 上运行，通过统一的 API 为不同平台的客户端提供服务！🎊
