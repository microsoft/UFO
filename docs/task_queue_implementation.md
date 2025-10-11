# 任务队列和设备状态管理实现

## 概述

本次更新为 Constellation Device Manager 添加了任务队列和设备状态管理功能，确保：
1. 设备在执行任务时状态为 `BUSY`
2. 当设备忙碌时，新任务会自动排队
3. 任务按顺序执行，完成后自动处理队列中的下一个任务

## 主要变更

### 1. 新增设备状态

在 `DeviceStatus` 枚举中添加了两个新状态：

```python
class DeviceStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    REGISTERING = "registering"
    BUSY = "busy"          # 设备正在执行任务
    IDLE = "idle"          # 设备已连接且空闲，可接受任务
```

### 2. DeviceInfo 增强

在 `DeviceInfo` 中添加了当前任务追踪：

```python
@dataclass
class DeviceInfo:
    # ... 其他字段 ...
    current_task_id: Optional[str] = None  # 追踪当前执行的任务
```

### 3. 新组件：TaskQueueManager

创建了专门的任务队列管理器 `TaskQueueManager`，负责：
- 任务入队/出队
- 任务执行状态追踪
- 异步结果管理（使用 asyncio.Future）
- 任务取消

**主要方法：**
- `enqueue_task()`: 将任务加入队列
- `dequeue_task()`: 从队列取出下一个任务
- `complete_task()`: 标记任务完成
- `fail_task()`: 标记任务失败
- `cancel_all_tasks()`: 取消所有排队任务

### 4. DeviceRegistry 增强

添加了设备状态管理方法：

- `set_device_busy(device_id, task_id)`: 设置设备为忙碌状态
- `set_device_idle(device_id)`: 设置设备为空闲状态
- `is_device_busy(device_id)`: 检查设备是否忙碌
- `get_current_task(device_id)`: 获取当前执行的任务ID

### 5. ConstellationDeviceManager 核心更改

#### 5.1 任务分配流程 (`assign_task_to_device`)

```python
async def assign_task_to_device(task_id, device_id, task_description, task_data, timeout):
    # 检查设备是否忙碌
    if device_is_busy:
        # 将任务加入队列
        future = task_queue_manager.enqueue_task(device_id, task_request)
        # 等待任务完成
        result = await future
        return result
    else:
        # 立即执行任务
        return await _execute_task_on_device(device_id, task_request)
```

#### 5.2 任务执行流程 (`_execute_task_on_device`)

```python
async def _execute_task_on_device(device_id, task_request):
    try:
        # 1. 设置设备为 BUSY
        device_registry.set_device_busy(device_id, task_id)
        
        # 2. 执行任务
        result = await connection_manager.send_task_to_device(...)
        
        # 3. 通知任务完成
        await event_manager.notify_task_completed(...)
        
        return result
    finally:
        # 4. 设置设备为 IDLE
        device_registry.set_device_idle(device_id)
        
        # 5. 处理队列中的下一个任务
        await _process_next_queued_task(device_id)
```

#### 5.3 队列处理 (`_process_next_queued_task`)

任务完成后，自动检查队列并处理下一个任务：

```python
async def _process_next_queued_task(device_id):
    if has_queued_tasks:
        next_task = dequeue_task(device_id)
        # 异步执行下一个任务（不阻塞）
        asyncio.create_task(_execute_task_on_device(device_id, next_task))
```

### 6. 新增查询方法

#### 6.1 `get_device_status(device_id)`

增强版设备状态查询，包含队列信息：

```python
{
    "device_id": "device_001",
    "status": "busy",
    "current_task_id": "task_001",
    "queued_tasks": 2,
    "queued_task_ids": ["task_002", "task_003"],
    # ... 其他设备信息 ...
}
```

#### 6.2 `get_task_queue_status(device_id)`

专门的任务队列状态查询：

```python
{
    "device_id": "device_001",
    "is_busy": true,
    "current_task_id": "task_001",
    "queue_size": 2,
    "queued_task_ids": ["task_002", "task_003"],
    "pending_task_ids": ["task_001", "task_002", "task_003"]
}
```

## 使用示例

### 基本用法

```python
# 创建设备管理器
manager = ConstellationDeviceManager()

# 注册并连接设备
await manager.register_device(
    device_id="device_001",
    server_url="ws://localhost:5000/ws",
    auto_connect=True
)

# 提交多个任务到同一设备
task1 = asyncio.create_task(
    manager.assign_task_to_device(
        task_id="task_001",
        device_id="device_001",
        task_description="Open app",
        task_data={"app": "notepad"}
    )
)

task2 = asyncio.create_task(
    manager.assign_task_to_device(
        task_id="task_002",
        device_id="device_001",
        task_description="Type text",
        task_data={"text": "Hello"}
    )
)

# 任务1会立即执行，任务2会自动排队
# 等待所有任务完成
results = await asyncio.gather(task1, task2)
```

### 查询队列状态

```python
# 获取设备状态
status = manager.get_device_status("device_001")
print(f"Status: {status['status']}")
print(f"Queue size: {status['queued_tasks']}")

# 获取详细队列信息
queue_status = manager.get_task_queue_status("device_001")
print(f"Is busy: {queue_status['is_busy']}")
print(f"Queued tasks: {queue_status['queued_task_ids']}")
```

## 工作流程

1. **设备连接**：设备连接成功后，状态设为 `IDLE`
2. **任务提交**：
   - 如果设备是 `IDLE`，立即执行任务并设为 `BUSY`
   - 如果设备是 `BUSY`，任务加入队列
3. **任务执行**：
   - 设备执行任务时状态为 `BUSY`
   - `current_task_id` 记录当前任务
4. **任务完成**：
   - 设备状态恢复为 `IDLE`
   - 自动检查队列并执行下一个任务
5. **队列处理**：循环执行直到队列为空

## 关键特性

### 1. 自动队列管理
- 无需手动管理队列
- 任务自动按顺序执行
- 支持并发提交任务

### 2. 异步结果等待
- 使用 `asyncio.Future` 机制
- 排队的任务可以被 await
- 支持超时和异常处理

### 3. 状态一致性
- 设备状态与任务执行同步
- 队列状态实时更新
- 支持状态查询

### 4. 错误处理
- 任务失败不会阻塞队列
- 异常会传播给调用者
- 自动继续处理下一个任务

### 5. 清理和关闭
- `shutdown()` 时自动取消所有排队任务
- 正在执行的任务会完成
- 队列中的任务会被取消

## 测试

运行示例程序：

```bash
python -m galaxy.client.examples.task_queue_example
```

## 注意事项

1. **并发安全**：TaskQueueManager 使用 deque，在单线程异步环境中是安全的
2. **超时处理**：任务超时由 connection_manager 处理，不影响队列
3. **设备断开**：设备断开时，应调用 `cancel_all_tasks()` 清理队列
4. **状态转换**：
   - `IDLE` ↔ `BUSY`（正常任务执行）
   - 不应该直接从 `DISCONNECTED` 到 `BUSY`

## 未来改进

1. 任务优先级队列
2. 任务取消功能（单个任务）
3. 队列大小限制
4. 任务重试机制
5. 任务执行统计
