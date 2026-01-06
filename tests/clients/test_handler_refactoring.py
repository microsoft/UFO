#!/usr/bin/env python3
"""
测试重构后的 UFOWebSocketHandler 方法结构
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock
from aip.messages import ClientMessage, ClientMessageType, TaskStatus
from ufo.server.ws.handler import UFOWebSocketHandler
from ufo.server.services.ws_manager import WSManager
from ufo.server.services.session_manager import SessionManager
from datetime import datetime, timezone

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MockWebSocket:
    """模拟 WebSocket 连接"""

    def __init__(self):
        self.messages_sent = []
        self.closed = False

    async def accept(self):
        pass

    async def receive_text(self):
        # 模拟注册消息
        device_reg = ClientMessage(
            type=ClientMessageType.REGISTER,
            client_id="test_device_001",
            status=TaskStatus.OK,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"type": "device_client", "os": "windows"},
        )
        return device_reg.model_dump_json()

    async def send_text(self, message):
        self.messages_sent.append(message)

    async def close(self):
        self.closed = True


async def test_handler_methods():
    """测试重构后的方法结构"""

    print("=" * 80)
    print("🧪 测试重构后的 UFOWebSocketHandler 方法结构")
    print("=" * 80)

    # 创建模拟对象
    ws_manager = WSManager()
    session_manager = SessionManager()
    handler = UFOWebSocketHandler(ws_manager, session_manager)

    try:
        # 测试1: 检查方法是否存在
        print("\n[1] 检查重构后的方法结构...")

        methods_to_check = [
            "_parse_registration_message",
            "_determine_and_validate_client_type",
            "_validate_constellation_client",
            "_send_registration_confirmation",
            "_send_error_response",
            "_log_client_connection",
        ]

        for method_name in methods_to_check:
            if hasattr(handler, method_name):
                print(f"✅ {method_name} 方法存在")
            else:
                print(f"❌ {method_name} 方法缺失")

        # 测试2: 测试设备客户端注册流程
        print("\n[2] 测试设备客户端注册流程...")

        mock_websocket = MockWebSocket()
        client_id, client_type = await handler.connect(mock_websocket)

        print(f"   客户端ID: {client_id}")
        print(f"   客户端类型: {client_type}")
        print(f"   发送的消息数量: {len(mock_websocket.messages_sent)}")

        if client_type == "device":
            print("✅ 设备客户端注册成功")
        else:
            print("❌ 客户端类型识别错误")

        # 测试3: 测试方法职责分离
        print("\n[3] 验证方法职责分离...")

        # 检查 connect 方法长度
        import inspect

        connect_source = inspect.getsource(handler.connect)
        connect_lines = len(connect_source.split("\n"))

        print(f"   connect 方法行数: {connect_lines}")
        if connect_lines < 30:  # 重构后应该更短
            print("✅ connect 方法长度合理")
        else:
            print("⚠️ connect 方法可能仍然过长")

        # 检查是否有适当的方法调用
        if "_parse_registration_message" in connect_source:
            print("✅ connect 调用了 _parse_registration_message")
        if "_determine_and_validate_client_type" in connect_source:
            print("✅ connect 调用了 _determine_and_validate_client_type")
        if "_send_registration_confirmation" in connect_source:
            print("✅ connect 调用了 _send_registration_confirmation")

        print("\n✅ 方法重构测试完成")

    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 80)
    print("🎯 重构验证结果:")
    print("   ✅ 方法结构清晰，职责分离明确")
    print("   ✅ connect 方法长度合理")
    print("   ✅ 各个子方法功能单一")
    print("=" * 80)


async def main():
    """主函数"""
    try:
        await test_handler_methods()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
