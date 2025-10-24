# Server 重启自动重连功能 - 完整实现

## ✅ 修复总结

成功实现了 server 重启后的自动重连功能。现在当 server 被 kill 然后重启时，设备会自动重新连接。

### 🎯 核心修改

**文件**: `galaxy/client/device_manager.py`

1. **修改 `connect_device()` 方法**：添加 `is_reconnection` 参数
   - `is_reconnection=False`（默认）：正常连接，会增加 `connection_attempts`
   - `is_reconnection=True`：重连场景，**不增加** `connection_attempts`
   - 重连有自己的循环计数器，避免混淆

2. **完全重写 `_reconnect_device()` 方法**：实现循环重试
   ```python
   async def _reconnect_device(self, device_id: str) -> None:
       """持续重试直到成功或达到最大次数"""
       retry_count = 0
       max_retries = device_info.max_retries  # 默认 5
       
       while retry_count < max_retries:
           await asyncio.sleep(self.reconnect_delay)  # 等待 5 秒
           retry_count += 1
           
           # 尝试重连
           success = await self.connect_device(device_id, is_reconnection=True)
           
           if success:
               # 成功 - 重置计数器并退出
               self.device_registry.reset_connection_attempts(device_id)
               return
           # 失败 - 继续下一次重试
       
       # 所有重试都失败 - 标记为 FAILED
       self.device_registry.update_device_status(device_id, DeviceStatus.FAILED)
   ```

3. **简化 `_handle_device_disconnection()` 方法**：
   - 移除检查 `connection_attempts < max_retries` 的逻辑
   - 总是安排重连，让 `_reconnect_device()` 自己管理重试

---

## 📊 测试覆盖

### 新增测试文件
**`tests/galaxy/client/test_server_restart_reconnection.py`** - 7 个测试

#### Test 1: Server 重启自动重连 ⭐
```python
test_server_restart_automatic_reconnection()
```
**场景**：
```
t=0: 设备已连接
t=1: Server 被 kill → 设备断连
t=2: 重连尝试 1 失败（server 还未启动）
t=3: 重连尝试 2 失败（server 还未启动）
t=4: Server 重启
t=5: 重连尝试 3 成功 ✅
```
✅ 验证：设备自动重连成功，状态变为 IDLE

#### Test 2: 多次重试
```python
test_reconnection_with_multiple_retries()
```
✅ 验证：
- 精确重试 3 次（max_retries=3）
- 每次重试间隔 ~1 秒
- 所有失败后状态变为 FAILED

#### Test 3: 首次重连成功
```python
test_reconnection_succeeds_on_first_attempt()
```
✅ 验证：Server 立即可用时，第一次重连就成功

#### Test 4: is_reconnection 参数
```python
test_is_reconnection_flag_prevents_attempt_increment()
```
✅ 验证：`connect_device(is_reconnection=True)` 不增加 `connection_attempts`

#### Test 5: 正常连接计数
```python
test_normal_connection_increments_attempts()
```
✅ 验证：`connect_device(is_reconnection=False)` 会增加 `connection_attempts`

#### Test 6: 完整集成测试 ⭐⭐⭐
```python
test_full_server_restart_scenario_integration()
```
**最接近真实场景的测试**：
```
✅ Step 1: Device linux_agent_1 initially connected
🔌 Step 2: Simulating server killed
✅ Step 3: Device status → DISCONNECTED
⚠️ Step 4: Reconnection attempts 1-2 failed (server still down)
   Attempts made so far: 2
🔄 Step 5: Server restarted (online)
✅ Step 6: Device linux_agent_1 auto-reconnected successfully!
   Final status: idle
   Total connection attempts made: 3
   Connection attempts counter (reset): 0
```

#### Test 7: 最大重试后停止
```python
test_reconnection_stops_after_max_retries()
```
✅ 验证：达到 max_retries 后停止，状态变为 FAILED

---

## 🧪 测试结果

### 所有测试通过 ✅

```bash
# 新增 server 重启测试
tests/galaxy/client/test_server_restart_reconnection.py::test_server_restart_automatic_reconnection PASSED
tests/galaxy/client/test_server_restart_reconnection.py::test_reconnection_with_multiple_retries PASSED
tests/galaxy/client/test_server_restart_reconnection.py::test_reconnection_succeeds_on_first_attempt PASSED
tests/galaxy/client/test_server_restart_reconnection.py::test_is_reconnection_flag_prevents_attempt_increment PASSED
tests/galaxy/client/test_server_restart_reconnection.py::test_normal_connection_increments_attempts PASSED
tests/galaxy/client/test_server_restart_reconnection.py::test_full_server_restart_scenario_integration PASSED
tests/galaxy/client/test_server_restart_reconnection.py::test_reconnection_stops_after_max_retries PASSED

# 所有断连相关测试
====================================================================
32 passed, 3 warnings in 28.50s
====================================================================
```

### 测试分类统计

| 测试类别 | 测试文件 | 测试数量 | 结果 |
|---------|---------|---------|------|
| 待处理任务取消 | test_pending_task_cancellation.py | 5 | ✅ 全部通过 |
| 任务失败处理 | test_device_disconnection_task_handling.py | 5 | ✅ 全部通过 |
| 断连重连逻辑 | test_device_disconnection_reconnection.py | 15 | ✅ 全部通过 |
| **Server 重启** | **test_server_restart_reconnection.py** | **7** | **✅ 全部通过** |
| **总计** | **4 个文件** | **32** | **✅ 100%** |

---

## 🔄 重连流程详解

### 修复前的问题

```
t=0: Server 断连
t=5: 重连尝试 1 - 失败（connection_attempts = 1）
❌ 重连停止！没有再次尝试

问题：
1. _reconnect_device() 只尝试一次
2. 每次调用 connect_device() 都增加 connection_attempts
3. 断连后检查 connection_attempts < max_retries 决定是否重连
4. 如果 server 重启慢，第一次重连就失败，导致 connection_attempts = max_retries
5. 不再尝试重连
```

### 修复后的流程

```
t=0: Server 断连
    ↓
_handle_device_disconnection() 调用
    ↓
总是安排重连（不检查 connection_attempts）
    ↓
_reconnect_device() 开始循环
    ↓
┌─────────────────────────────────────┐
│  retry_count = 0                    │
│  while retry_count < max_retries:   │ ← 独立的重试计数器
│      await sleep(5.0)               │
│      retry_count += 1               │
│                                     │
│      # 尝试重连                      │
│      success = await connect_device │
│          (is_reconnection=True)     │ ← 不增加 connection_attempts
│                                     │
│      if success:                    │
│          reset_connection_attempts()│
│          return  # 成功退出         │
│      # 否则继续循环                  │
└─────────────────────────────────────┘
    │
    ↓ (所有重试都失败)
status = FAILED
```

---

## 🎯 关键改进

### 1. 分离重连计数器

**修复前**：
- 使用 `connection_attempts` 作为唯一计数器
- 初次连接和重连共享同一个计数器
- 容易导致混淆

**修复后**：
- `connection_attempts`：只用于初次连接
- `retry_count`（局部变量）：用于重连循环
- 清晰分离，互不影响

### 2. 持续重试而不是单次

**修复前**：
```python
async def _reconnect_device(self, device_id: str) -> None:
    await asyncio.sleep(5.0)
    success = await self.connect_device(device_id)
    # 只尝试一次就结束
```

**修复后**：
```python
async def _reconnect_device(self, device_id: str) -> None:
    while retry_count < max_retries:
        await asyncio.sleep(5.0)
        success = await self.connect_device(device_id, is_reconnection=True)
        if success:
            return  # 成功就退出
        # 失败就继续循环
```

### 3. 总是安排重连

**修复前**：
```python
# 检查是否应该重连
if device_info.connection_attempts < device_info.max_retries:
    self._schedule_reconnection(device_id)
else:
    # 不重连
    device_info.status = DeviceStatus.FAILED
```

**修复后**：
```python
# 总是安排重连，让重连循环自己决定何时停止
self._schedule_reconnection(device_id)
```

---

## 📝 使用示例

### 场景：Server 维护重启

```python
# 1. 设备正常运行
device_manager = ConstellationDeviceManager(
    task_name="my_task",
    heartbeat_interval=30.0,
    reconnect_delay=5.0,  # 每次重试等待 5 秒
)

await device_manager.register_device(
    device_id="linux_agent_1",
    server_url="ws://localhost:8765",
    os="Linux",
    max_retries=5,  # 最多重试 5 次
)

await device_manager.connect_device("linux_agent_1")
# ✅ 设备已连接，状态: IDLE

# 2. Server 被 kill 进行维护
#    (系统自动检测到断连)

# 日志输出：
# 🔌 Device linux_agent_1 disconnected, cleaning up...
# 🔄 Scheduling automatic reconnection for device linux_agent_1 (max retries: 5)
# 🔄 Reconnection attempt 1/5 for device linux_agent_1
# ⚠️ Reconnection attempt 1/5 failed for device linux_agent_1
# 🔄 Reconnection attempt 2/5 for device linux_agent_1
# ⚠️ Reconnection attempt 2/5 failed for device linux_agent_1

# 3. Server 重启完成（30秒后）

# 日志输出：
# 🔄 Reconnection attempt 3/5 for device linux_agent_1
# ✅ Successfully reconnected to device linux_agent_1 on attempt 3/5

# ✅ 设备自动重连，状态: IDLE，可以继续执行任务
```

### 配置参数

```python
# 在 device_manager 初始化时设置
device_manager = ConstellationDeviceManager(
    reconnect_delay=5.0,  # 每次重试间隔（秒）
)

# 在注册设备时设置
device_manager.register_device(
    device_id="device_1",
    max_retries=5,  # 最多重试次数
    # ...
)

# 推荐配置：
# - reconnect_delay: 5-10 秒
# - max_retries: 3-5 次
# - 总重试时间 = reconnect_delay × max_retries
#   例如: 5秒 × 5次 = 25秒
```

---

## 🚀 实际场景验证

### 场景 1: Server 短暂重启（< 10 秒）

```
t=0:  Server kill
t=5:  第 1 次重连 → 失败
t=8:  Server 启动完成
t=10: 第 2 次重连 → 成功 ✅
```
**结果**：设备在 10 秒内自动重连

### 场景 2: Server 长时间维护（20 秒）

```
t=0:  Server kill
t=5:  第 1 次重连 → 失败
t=10: 第 2 次重连 → 失败
t=15: 第 3 次重连 → 失败
t=20: Server 启动完成
t=20: 第 4 次重连 → 成功 ✅
```
**结果**：设备在 20 秒内自动重连

### 场景 3: Server 永久下线

```
t=0:  Server kill（不再启动）
t=5:  第 1 次重连 → 失败
t=10: 第 2 次重连 → 失败
t=15: 第 3 次重连 → 失败
t=20: 第 4 次重连 → 失败
t=25: 第 5 次重连 → 失败
状态: FAILED ❌
```
**结果**：5 次重试后标记为 FAILED，停止重连

---

## 📊 性能影响

### 资源占用

- ✅ **CPU**: 极低（大部分时间在 `asyncio.sleep`）
- ✅ **内存**: 每个设备一个重连任务（< 1KB）
- ✅ **网络**: 每 5 秒一次连接尝试（只在断连时）

### 时间成本

| 场景 | Server 重启时间 | 重连成功时间 | 总延迟 |
|------|----------------|-------------|--------|
| 快速重启 | 5 秒 | 第 2 次尝试 | ~10 秒 |
| 正常重启 | 15 秒 | 第 3 次尝试 | ~15 秒 |
| 慢速重启 | 25 秒 | 第 5 次尝试 | ~25 秒 |
| 永久下线 | N/A | 失败 | ~25 秒后放弃 |

---

## ✅ 验证清单

- [x] Server kill 后设备检测到断连
- [x] 自动开始重连循环
- [x] 每次重试等待 `reconnect_delay` 秒
- [x] Server 重启后自动重连成功
- [x] 重连成功后状态变为 IDLE
- [x] `connection_attempts` 重置为 0
- [x] 可以继续执行新任务
- [x] 达到 `max_retries` 后停止
- [x] 所有重试失败后状态变为 FAILED
- [x] 32 个测试全部通过
- [x] 文档完整

---

**实现日期**: 2025-10-24  
**测试状态**: ✅ 32/32 通过  
**生产就绪**: ✅ 是

---

## 🔗 相关文档

- `docs/device_disconnection_complete_flow.md` - 完整断连流程
- `docs/device_disconnection_pending_task_fix.md` - 待处理任务取消
- `docs/device_disconnection_quick_fix_summary.md` - 快速参考
- `tests/galaxy/client/test_server_restart_reconnection.py` - Server 重启测试
