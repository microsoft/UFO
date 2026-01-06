#!/usr/bin/env python3
"""
测试 WebSocket 客户端类型区分功能
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


class TestWSClient:
    """测试用的 WebSocket 客户端"""

    def __init__(
        self,
        client_id: str,
        client_type: str = "device",
        server_url: str = "ws://localhost:5000/ws",
    ):
        self.client_id = client_id
        self.client_type = client_type
        self.server_url = server_url
        self.websocket = None

    async def connect(self):
        """连接到服务器并注册"""
        try:
            self.websocket = await websockets.connect(self.server_url)

            # 创建注册消息
            metadata = {}
            if self.client_type == "constellation":
                metadata = {
                    "type": "constellation_client",
                    "constellation_id": "test_constellation",
                    "device_id": (
                        self.client_id.split("@")[-1]
                        if "@" in self.client_id
                        else self.client_id
                    ),
                    "capabilities": ["task_distribution", "session_management"],
                    "version": "2.0",
                }
            else:
                metadata = {
                    "type": "device_client",
                    "capabilities": ["web_browsing", "file_management"],
                    "os": "windows",
                    "version": "1.0",
                }

            registration_message = ClientMessage(
                type=ClientMessageType.REGISTER,
                client_id=self.client_id,
                status=TaskStatus.OK,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata=metadata,
            )

            await self.websocket.send(registration_message.model_dump_json())
            logger.info(
                f"[{self.client_type.upper()}] {self.client_id} registered successfully"
            )
            return True

        except Exception as e:
            logger.error(
                f"[{self.client_type.upper()}] Failed to connect {self.client_id}: {e}"
            )
            return False

    async def send_heartbeat(self):
        """发送心跳消息"""
        if not self.websocket:
            return False

        try:
            heartbeat_message = ClientMessage(
                type=ClientMessageType.HEARTBEAT,
                client_id=self.client_id,
                status=TaskStatus.OK,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            await self.websocket.send(heartbeat_message.model_dump_json())
            logger.info(f"[{self.client_type.upper()}] {self.client_id} sent heartbeat")
            return True

        except Exception as e:
            logger.error(
                f"[{self.client_type.upper()}] Failed to send heartbeat from {self.client_id}: {e}"
            )
            return False

    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            logger.info(f"[{self.client_type.upper()}] {self.client_id} disconnected")


async def test_client_types():
    """测试不同类型的客户端"""

    print("=" * 80)
    print("🧪 测试 WebSocket 客户端类型区分功能")
    print("=" * 80)

    # 创建测试客户端
    device_client = TestWSClient("device_001", "device")
    constellation_client = TestWSClient(
        "test_constellation@client_001", "constellation"
    )

    try:
        # 1. 连接设备客户端
        print("\n[1] 连接设备客户端...")
        device_connected = await device_client.connect()
        if device_connected:
            print("✅ 设备客户端连接成功")
        else:
            print("❌ 设备客户端连接失败")
            return

        # 2. 连接星座客户端
        print("\n[2] 连接星座客户端...")
        constellation_connected = await constellation_client.connect()
        if constellation_connected:
            print("✅ 星座客户端连接成功")
        else:
            print("❌ 星座客户端连接失败")
            return

        # 3. 发送心跳测试
        print("\n[3] 发送心跳测试...")
        await device_client.send_heartbeat()
        await constellation_client.send_heartbeat()

        # 4. 等待一段时间观察日志
        print("\n[4] 等待 5 秒观察服务器日志...")
        await asyncio.sleep(5)

        print("\n✅ 客户端类型区分测试完成")

    except Exception as e:
        logger.error(f"测试过程中出错: {e}")

    finally:
        # 清理连接
        print("\n[5] 清理连接...")
        await device_client.disconnect()
        await constellation_client.disconnect()


async def main():
    """主函数"""
    try:
        await test_client_types()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
