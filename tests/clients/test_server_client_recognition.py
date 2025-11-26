#!/usr/bin/env python3
"""
测试服务器端的客户端类型识别功能
通过检查服务器日志来验证是否正确区分了客户端类型
"""

import asyncio
import json
import logging
import sys
import websockets
from datetime import datetime, timezone
from aip.messages import ClientMessage, ClientMessageType, TaskStatus

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_server_client_recognition():
    """测试服务器是否能正确识别客户端类型"""

    print("=" * 80)
    print("🔍 测试服务器端客户端类型识别")
    print("=" * 80)

    server_url = "ws://localhost:5000/ws"

    # 测试1: 连接一个普通设备客户端
    print("\n[1] 测试普通设备客户端识别...")

    try:
        # 连接设备客户端
        device_ws = await websockets.connect(server_url)

        device_reg = ClientMessage(
            type=ClientMessageType.REGISTER,
            client_id="test_device_001",
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                "type": "device_client",
                "os": "windows",
                "capabilities": ["web_browsing", "file_management"],
            },
        )

        await device_ws.send(device_reg.model_dump_json())
        print("📱 设备客户端注册消息已发送")

        # 发送心跳
        await asyncio.sleep(1)
        heartbeat = ClientMessage(
            type=ClientMessageType.HEARTBEAT,
            client_id="test_device_001",
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await device_ws.send(heartbeat.model_dump_json())
        print("💓 设备客户端心跳已发送")

        await device_ws.close()
        print("✅ 设备客户端测试完成")

    except Exception as e:
        print(f"❌ 设备客户端测试失败: {e}")

    # 测试2: 连接一个星座客户端
    print("\n[2] 测试星座客户端识别...")

    try:
        # 连接星座客户端
        constellation_ws = await websockets.connect(server_url)

        constellation_reg = ClientMessage(
            type=ClientMessageType.REGISTER,
            client_id="test_constellation@client_001",
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                "type": "constellation_client",
                "constellation_id": "test_constellation",
                "device_id": "client_001",
                "capabilities": ["task_distribution", "session_management"],
                "version": "2.0",
            },
        )

        await constellation_ws.send(constellation_reg.model_dump_json())
        print("🌟 星座客户端注册消息已发送")

        # 发送心跳
        await asyncio.sleep(1)
        heartbeat = ClientMessage(
            type=ClientMessageType.HEARTBEAT,
            client_id="test_constellation@client_001",
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await constellation_ws.send(heartbeat.model_dump_json())
        print("💓 星座客户端心跳已发送")

        await constellation_ws.close()
        print("✅ 星座客户端测试完成")

    except Exception as e:
        print(f"❌ 星座客户端测试失败: {e}")

    print("\n" + "=" * 80)
    print("🎯 测试完成！请检查服务器日志以确认:")
    print("   - 设备客户端应该显示: 📱 Device client test_device_001 connected")
    print(
        "   - 星座客户端应该显示: 🌟 Constellation client test_constellation@client_001 connected"
    )
    print("   - 消息处理应该有相应的emoji标识")
    print("=" * 80)


async def main():
    """主函数"""
    try:
        await test_server_client_recognition()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
