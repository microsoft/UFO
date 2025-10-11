# assign_task_to_device 快速测试指南

## 快速开始

```bash
# 1. 激活环境
.\scripts\activate.ps1

# 2. 运行测试
python -m pytest tests/galaxy/client/test_device_manager_assign_task.py -v
```

## 测试结果摘要

✅ **13/13 测试全部通过** (执行时间: ~10秒)

## 测试列表

### 基础功能 ✅
- `test_assign_task_to_idle_device` - IDLE设备立即执行
- `test_device_state_transitions` - 状态转换验证
- `test_assign_task_to_busy_device_queues_task` - BUSY设备任务排队
- `test_sequential_task_processing` - 顺序处理验证

### 错误处理 ✅
- `test_task_execution_error_handling` - 单任务错误处理
- `test_error_handling_with_queued_tasks` - 队列错误处理

### 边界条件 ✅
- `test_assign_task_to_unregistered_device` - 未注册设备
- `test_assign_task_to_disconnected_device` - 未连接设备

### 高级功能 ✅
- `test_queue_status_queries` - 队列状态查询
- `test_concurrent_tasks_multiple_devices` - 多设备并发
- `test_task_timeout` - 超时处理
- `test_task_request_creation` - 参数验证

### 集成测试 ✅
- `test_realistic_workflow` - 真实场景模拟

## 关键验证点

### 1. 设备状态管理 ✅
```python
# IDLE → BUSY → IDLE
device.status == DeviceStatus.IDLE  # 初始
device.status == DeviceStatus.BUSY  # 执行中
device.status == DeviceStatus.IDLE  # 完成后
```

### 2. 任务排队机制 ✅
```python
# 设备BUSY时任务自动排队
queue_status["queue_size"] == 2
queue_status["queued_task_ids"] == ["task_002", "task_003"]
```

### 3. 顺序执行 ✅
```python
# 任务按提交顺序执行
execution_order == ["task_001", "task_002", "task_003"]
```

### 4. 错误恢复 ✅
```python
# 任务失败后设备恢复IDLE
device.status == DeviceStatus.IDLE  # 即使出错
```

## 运行特定测试

```bash
# 运行单个测试
pytest tests/galaxy/client/test_device_manager_assign_task.py::TestAssignTaskToDevice::test_assign_task_to_idle_device -v

# 运行错误处理测试
pytest tests/galaxy/client/test_device_manager_assign_task.py::TestAssignTaskToDevice::test_task_execution_error_handling -v

# 运行集成测试
pytest tests/galaxy/client/test_device_manager_assign_task.py::TestAssignTaskIntegration -v
```

## Mock 验证

所有测试使用完整的 mock，无需真实设备：

```python
# Mock connection manager
device_manager.connection_manager.send_task_to_device = AsyncMock(
    return_value=ExecutionResult(...)
)

# Mock event manager
device_manager.event_manager.notify_task_completed = AsyncMock()
```

## 测试数据

```python
# 标准设备
device_id = "test_device_001"
server_url = "ws://localhost:5000/ws"

# 标准任务
task_request = TaskRequest(
    task_id="task_001",
    device_id=device_id,
    request="Test task",
    task_name="task_001",
    metadata={},
    timeout=300.0,
)

# 预期结果
result = ExecutionResult(
    task_id="task_001",
    status="completed",
    result={},
    metadata={"message": "Success"},
)
```

## 验证的核心功能

| 功能 | 状态 | 测试数量 |
|------|------|---------|
| 任务分配 | ✅ | 4 |
| 状态管理 | ✅ | 3 |
| 队列机制 | ✅ | 3 |
| 错误处理 | ✅ | 2 |
| 并发支持 | ✅ | 1 |

## 问题排查

如果测试失败，检查：

1. ✅ ExecutionResult 参数是否正确
   ```python
   # 正确 ✅
   ExecutionResult(task_id=..., status="completed", ...)
   
   # 错误 ❌
   ExecutionResult(success=True, ...)  # 旧API
   ```

2. ✅ 异步mock是否使用 AsyncMock
   ```python
   # 正确 ✅
   manager.connection_manager.send_task = AsyncMock()
   
   # 错误 ❌
   manager.connection_manager.send_task = Mock()  # 同步
   ```

3. ✅ 设备状态是否正确设置
   ```python
   # 测试前必须设置为IDLE
   device_manager.device_registry.update_device_status(
       device_id, DeviceStatus.IDLE
   )
   ```

## 性能指标

- 平均测试时间: ~0.8秒/测试
- 总执行时间: ~10秒
- 并发任务数: 最多6个（多设备测试）
- 队列深度: 最多3个任务

## 下一步

查看完整文档：
- `docs/assign_task_to_device_test_report.md` - 详细测试报告
- `docs/task_queue_implementation.md` - 实现文档
