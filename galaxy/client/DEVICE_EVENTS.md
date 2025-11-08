# 设备事件系统使用指南

## 概述

设备事件系统允许你监听和响应设备管理器中的设备连接、断连和状态变化事件。所有事件都包含完整的设备注册表快照，让你可以随时了解所有设备的当前状态。

## 事件类型

系统提供三种设备相关事件：

1. **DEVICE_CONNECTED** - 设备成功连接时触发
2. **DEVICE_DISCONNECTED** - 设备断开连接时触发
3. **DEVICE_STATUS_CHANGED** - 设备状态改变时触发（例如：IDLE ↔ BUSY）

## DeviceEvent 结构

所有设备事件都使用 `DeviceEvent` 类，包含以下字段：

```python
@dataclass
class DeviceEvent(Event):
    device_id: str                          # 触发事件的设备ID
    device_status: str                      # 当前设备状态
    device_info: Dict[str, Any]             # 当前设备的详细信息
    all_devices: Dict[str, Dict[str, Any]]  # 所有设备的状态快照
```

### device_info 字段内容

```python
{
    "device_id": "device_001",
    "status": "idle",
    "os": "Windows",
    "server_url": "ws://localhost:8000",
    "capabilities": ["ui_control", "file_access"],
    "metadata": {...},
    "last_heartbeat": "2025-11-08T10:30:00",
    "connection_attempts": 0,
    "max_retries": 5,
    "current_task_id": None
}
```

### all_devices 字段内容

包含 device_registry 中所有设备的状态信息：

```python
{
    "device_001": {
        "device_id": "device_001",
        "status": "idle",
        "os": "Windows",
        ...
    },
    "device_002": {
        "device_id": "device_002",
        "status": "busy",
        "os": "macOS",
        ...
    }
}
```

## 使用示例

### 1. 创建设备事件观察者

```python
from galaxy.core.events import IEventObserver, EventType, DeviceEvent

class DeviceMonitor(IEventObserver):
    """监控设备连接状态的观察者"""
    
    async def on_event(self, event):
        if isinstance(event, DeviceEvent):
            if event.event_type == EventType.DEVICE_CONNECTED:
                await self._handle_device_connected(event)
            elif event.event_type == EventType.DEVICE_DISCONNECTED:
                await self._handle_device_disconnected(event)
            elif event.event_type == EventType.DEVICE_STATUS_CHANGED:
                await self._handle_device_status_changed(event)
    
    async def _handle_device_connected(self, event: DeviceEvent):
        print(f"✅ Device {event.device_id} connected")
        print(f"   OS: {event.device_info['os']}")
        print(f"   Total devices: {len(event.all_devices)}")
    
    async def _handle_device_disconnected(self, event: DeviceEvent):
        print(f"❌ Device {event.device_id} disconnected")
        print(f"   Remaining devices: {len(event.all_devices) - 1}")
    
    async def _handle_device_status_changed(self, event: DeviceEvent):
        print(f"🔄 Device {event.device_id} status: {event.device_status}")
        if event.device_status == "busy":
            task_id = event.device_info.get("current_task_id")
            print(f"   Executing task: {task_id}")
```

### 2. 订阅设备事件

```python
from galaxy.core.events import get_event_bus, EventType
from galaxy.client.device_manager import ConstellationDeviceManager

# 创建设备管理器
manager = ConstellationDeviceManager()

# 创建观察者
monitor = DeviceMonitor()

# 获取事件总线并订阅设备事件
event_bus = get_event_bus()
event_bus.subscribe(
    monitor,
    event_types={
        EventType.DEVICE_CONNECTED,
        EventType.DEVICE_DISCONNECTED,
        EventType.DEVICE_STATUS_CHANGED,
    }
)

# 或者订阅所有事件
# event_bus.subscribe(monitor)  # 订阅所有事件
```

### 3. 监控所有设备状态

```python
class DeviceRegistryMonitor(IEventObserver):
    """实时监控设备注册表的完整状态"""
    
    def __init__(self):
        self.device_history = []
    
    async def on_event(self, event):
        if isinstance(event, DeviceEvent):
            # 记录设备注册表快照
            snapshot = {
                "timestamp": event.timestamp,
                "event_type": event.event_type.value,
                "triggered_by": event.device_id,
                "all_devices": event.all_devices.copy()
            }
            self.device_history.append(snapshot)
            
            # 分析设备状态分布
            status_counts = {}
            for device_id, device_info in event.all_devices.items():
                status = device_info["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"📊 Device Status Distribution:")
            for status, count in status_counts.items():
                print(f"   {status}: {count}")
```

### 4. WebSocket 实时推送（示例）

```python
from galaxy.webui.websocket_observer import WebSocketObserver

class DeviceWebSocketObserver(WebSocketObserver):
    """将设备事件推送到 Web UI"""
    
    async def on_event(self, event):
        if isinstance(event, DeviceEvent):
            # 准备发送给前端的数据
            message = {
                "type": "device_event",
                "event_type": event.event_type.value,
                "device_id": event.device_id,
                "device_status": event.device_status,
                "device_info": event.device_info,
                "all_devices": event.all_devices,
                "timestamp": event.timestamp
            }
            
            # 广播给所有连接的 WebSocket 客户端
            await self.broadcast(message)
```

### 5. 设备负载均衡器

```python
class DeviceLoadBalancer(IEventObserver):
    """根据设备状态进行负载均衡"""
    
    def __init__(self):
        self.idle_devices = []
    
    async def on_event(self, event):
        if isinstance(event, DeviceEvent):
            # 更新空闲设备列表
            self.idle_devices = [
                device_id
                for device_id, device_info in event.all_devices.items()
                if device_info["status"] == "idle"
            ]
            
            print(f"💡 Available devices: {len(self.idle_devices)}")
    
    def get_next_available_device(self):
        """获取下一个可用设备（简单轮询）"""
        if self.idle_devices:
            return self.idle_devices[0]
        return None
```

## 事件触发时机

### DEVICE_CONNECTED

- 设备成功连接并完成初始化
- 重连成功后
- 设备状态已设置为 IDLE

### DEVICE_DISCONNECTED

- 主动断开连接（调用 `disconnect_device()`）
- 检测到设备异常断开
- 连接丢失或超时

### DEVICE_STATUS_CHANGED

- 设备开始执行任务（IDLE → BUSY）
- 设备完成任务（BUSY → IDLE）
- 任务失败或超时（BUSY → IDLE）

## 注意事项

1. **事件是异步的** - 所有事件处理函数必须是 async 函数
2. **包含完整快照** - 每个事件都包含所有设备的状态，无需额外查询
3. **事件顺序** - 事件按发生顺序发布，但处理可能并发执行
4. **错误处理** - 观察者中的异常不会影响其他观察者或事件发布者

## 完整示例

```python
import asyncio
from galaxy.client.device_manager import ConstellationDeviceManager
from galaxy.core.events import get_event_bus, EventType, IEventObserver, DeviceEvent

class DeviceLogger(IEventObserver):
    async def on_event(self, event):
        if isinstance(event, DeviceEvent):
            print(f"\n{'='*60}")
            print(f"Event: {event.event_type.value}")
            print(f"Device: {event.device_id}")
            print(f"Status: {event.device_status}")
            print(f"Total Devices: {len(event.all_devices)}")
            print(f"{'='*60}\n")

async def main():
    # 创建设备管理器
    manager = ConstellationDeviceManager()
    
    # 创建并订阅观察者
    logger = DeviceLogger()
    event_bus = get_event_bus()
    event_bus.subscribe(
        logger,
        event_types={
            EventType.DEVICE_CONNECTED,
            EventType.DEVICE_DISCONNECTED,
            EventType.DEVICE_STATUS_CHANGED,
        }
    )
    
    # 注册设备
    await manager.register_device(
        device_id="device_001",
        server_url="ws://localhost:8000",
        os="Windows",
        capabilities=["ui_control"]
    )
    
    # 执行任务
    await manager.assign_task_to_device(
        task_id="task_001",
        device_id="device_001",
        task_description="Test task",
        task_data={}
    )
    
    # 断开连接
    await manager.disconnect_device("device_001")

if __name__ == "__main__":
    asyncio.run(main())
```

## 调试技巧

启用详细日志查看事件发布过程：

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("galaxy.client.device_manager")
logger.setLevel(logging.DEBUG)
```

查看事件发布日志：
```
📢 Published device_connected event for device device_001
📢 Published device_status_changed event for device device_001
📢 Published device_disconnected event for device device_001
```
