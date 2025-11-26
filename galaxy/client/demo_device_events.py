#!/usr/bin/env python
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
设备事件系统演示脚本

演示如何监听和响应设备连接、断连和状态变化事件。
"""

import asyncio
import logging
from typing import Any, Dict

from galaxy.core.events import DeviceEvent, EventType, IEventObserver, get_event_bus

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class DeviceEventMonitor(IEventObserver):
    """设备事件监控器"""

    def __init__(self, name: str = "DeviceMonitor"):
        self.name = name
        self.event_count = 0

    async def on_event(self, event: Any) -> None:
        """处理事件"""
        if isinstance(event, DeviceEvent):
            self.event_count += 1
            await self._handle_device_event(event)

    async def _handle_device_event(self, event: DeviceEvent) -> None:
        """处理设备事件"""
        print("\n" + "=" * 80)
        print(f"🔔 [{self.name}] Device Event #{self.event_count}")
        print("=" * 80)

        print(f"\n📋 Event Type: {event.event_type.value}")
        print(f"⏰ Timestamp: {event.timestamp}")
        print(f"📍 Source: {event.source_id}")

        print(f"\n📱 Device Information:")
        print(f"   Device ID: {event.device_id}")
        print(f"   Status: {event.device_status}")

        device_info = event.device_info
        print(f"   OS: {device_info.get('os', 'N/A')}")
        print(f"   Server URL: {device_info.get('server_url', 'N/A')}")
        print(f"   Capabilities: {device_info.get('capabilities', [])}")
        print(f"   Current Task: {device_info.get('current_task_id', 'None')}")
        print(f"   Connection Attempts: {device_info.get('connection_attempts', 0)}")

        print(f"\n📊 Device Registry Snapshot:")
        print(f"   Total Devices: {len(event.all_devices)}")

        # 统计各状态设备数量
        status_counts: Dict[str, int] = {}
        for device_id, info in event.all_devices.items():
            status = info["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        print(f"\n   Status Distribution:")
        for status, count in sorted(status_counts.items()):
            print(f"      {status}: {count}")

        # 显示所有设备列表
        print(f"\n   Devices List:")
        for device_id, info in event.all_devices.items():
            status_icon = self._get_status_icon(info["status"])
            task_info = (
                f" (Task: {info['current_task_id']})"
                if info.get("current_task_id")
                else ""
            )
            print(f"      {status_icon} {device_id} [{info['status']}]{task_info}")

        print("\n" + "=" * 80 + "\n")

    @staticmethod
    def _get_status_icon(status: str) -> str:
        """获取状态图标"""
        icons = {
            "connected": "🟢",
            "disconnected": "🔴",
            "idle": "🟢",
            "busy": "🟡",
            "failed": "🔴",
            "connecting": "🟠",
        }
        return icons.get(status, "⚪")


class DeviceStatisticsMonitor(IEventObserver):
    """设备统计监控器 - 简化版本，只显示摘要"""

    def __init__(self):
        self.total_events = 0
        self.connected_count = 0
        self.disconnected_count = 0
        self.status_changed_count = 0

    async def on_event(self, event: Any) -> None:
        """处理事件"""
        if isinstance(event, DeviceEvent):
            self.total_events += 1

            if event.event_type == EventType.DEVICE_CONNECTED:
                self.connected_count += 1
            elif event.event_type == EventType.DEVICE_DISCONNECTED:
                self.disconnected_count += 1
            elif event.event_type == EventType.DEVICE_STATUS_CHANGED:
                self.status_changed_count += 1

    def print_statistics(self) -> None:
        """打印统计信息"""
        print("\n" + "=" * 80)
        print("📈 Device Event Statistics")
        print("=" * 80)
        print(f"Total Events: {self.total_events}")
        print(f"  - Connected: {self.connected_count}")
        print(f"  - Disconnected: {self.disconnected_count}")
        print(f"  - Status Changed: {self.status_changed_count}")
        print("=" * 80 + "\n")


async def demo_device_events():
    """演示设备事件系统"""
    print("\n🚀 Device Event System Demo\n")

    # 获取事件总线
    event_bus = get_event_bus()

    # 创建观察者
    detailed_monitor = DeviceEventMonitor("DetailedMonitor")
    stats_monitor = DeviceStatisticsMonitor()

    # 订阅设备事件
    event_bus.subscribe(
        detailed_monitor,
        event_types={
            EventType.DEVICE_CONNECTED,
            EventType.DEVICE_DISCONNECTED,
            EventType.DEVICE_STATUS_CHANGED,
        },
    )

    event_bus.subscribe(
        stats_monitor,
        event_types={
            EventType.DEVICE_CONNECTED,
            EventType.DEVICE_DISCONNECTED,
            EventType.DEVICE_STATUS_CHANGED,
        },
    )

    print("✅ Event monitors subscribed to device events")
    print("\n💡 To see real device events, use the ConstellationDeviceManager")
    print("   and register/connect actual devices.\n")

    # 显示示例代码
    print("=" * 80)
    print("📝 Example Usage Code:")
    print("=" * 80)
    print(
        """
from galaxy.client.device_manager import ConstellationDeviceManager

# 创建设备管理器
manager = ConstellationDeviceManager()

# 注册并连接设备 (将自动发布 DEVICE_CONNECTED 事件)
await manager.register_device(
    device_id="my_device",
    server_url="ws://localhost:8000",
    os="Windows",
    capabilities=["ui_control"]
)

# 分配任务 (将发布 DEVICE_STATUS_CHANGED 事件: IDLE -> BUSY -> IDLE)
result = await manager.assign_task_to_device(
    task_id="task_001",
    device_id="my_device",
    task_description="Test task",
    task_data={}
)

# 断开设备 (将发布 DEVICE_DISCONNECTED 事件)
await manager.disconnect_device("my_device")
"""
    )
    print("=" * 80 + "\n")

    # 显示统计信息
    stats_monitor.print_statistics()


if __name__ == "__main__":
    asyncio.run(demo_device_events())
