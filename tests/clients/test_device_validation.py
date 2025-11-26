#!/usr/bin/env python3
"""
测试 Constellation Client 注册时的设备验证机制
"""

import asyncio
import logging
import sys
import os

# 设置路径
sys.path.insert(0, os.path.abspath("."))

from galaxy.client.config_loader import ConstellationConfig
from galaxy.client.constellation_client import ConstellationClient

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_device_validation():
    """测试设备验证机制"""

    print("=" * 80)
    print("🔍 测试 Constellation Client 设备验证机制")
    print("=" * 80)

    # 测试1: 尝试连接到不存在的设备
    print("\n[1] 测试连接到不存在的设备...")

    try:
        # 创建一个指向不存在设备的配置
        invalid_config = ConstellationConfig(
            constellation_id="test_validation",
            devices={
                "nonexistent_device": {
                    "server_url": "ws://localhost:5000/ws",
                    "capabilities": ["testing"],
                    "metadata": {"test": "invalid_device"},
                }
            },
            heartbeat_interval=30.0,
            max_concurrent_tasks=2,
        )

        # 尝试创建并初始化客户端
        constellation_client = ConstellationClient(invalid_config)

        print("🚀 正在尝试初始化并连接到不存在的设备...")

        try:
            await constellation_client.initialize()
            print("❌ 意外成功：客户端应该无法连接到不存在的设备")
        except Exception as e:
            print(f"✅ 预期失败：无法连接到不存在的设备 - {e}")

        await constellation_client.shutdown()

    except Exception as e:
        print(f"✅ 测试按预期失败：{e}")

    # 测试2: 先连接一个真实设备，再测试 constellation
    print("\n[2] 测试完整的设备验证流程...")

    try:
        # 加载正确的配置
        valid_config = ConstellationConfig.from_yaml("config/constellation_sample.yaml")

        print(f"📋 加载配置成功，设备数量: {len(valid_config.devices)}")
        for device_id in valid_config.devices:
            print(f"   设备: {device_id}")

        # 创建客户端
        constellation_client = ConstellationClient(valid_config)

        print("🚀 正在初始化 constellation client...")
        await constellation_client.initialize()

        # 检查连接状态
        connected_devices = constellation_client.get_connected_devices()
        print(f"✅ 成功连接的设备: {connected_devices}")

        # 测试连接稳定性
        print("⏳ 等待 5 秒测试连接稳定性...")
        await asyncio.sleep(5)

        final_devices = constellation_client.get_connected_devices()
        print(f"📊 最终连接状态: {final_devices}")

        await constellation_client.shutdown()
        print("✅ 客户端已正常关闭")

    except Exception as e:
        print(f"❌ 有效配置测试失败: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 80)
    print("🎯 设备验证机制测试完成")
    print("   请检查服务器日志确认验证逻辑是否正确执行")
    print("=" * 80)


async def main():
    """主函数"""
    try:
        await test_device_validation()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
