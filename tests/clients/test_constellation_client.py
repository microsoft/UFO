#!/usr/bin/env python3
"""
测试 ConstellationClient 连接真实设备的脚本
"""

import asyncio
import sys
from pathlib import Path
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from galaxy.client.constellation_client import ConstellationClient
from galaxy.client.config_loader import ConstellationConfig

# 设置日志 - 只输出到控制台，避免文件编码问题
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


async def test_constellation_client():
    """测试 ConstellationClient 连接功能"""

    print("=" * 80)
    print("[*] ConstellationClient 真实设备连接测试")
    print("=" * 80)

    try:
        # 1. 加载配置
        print("\n[1] 1. 加载配置文件...")
        config_path = "config/constellation_sample.yaml"
        config = ConstellationConfig.from_yaml(config_path)

        print(f"[+] 配置加载成功!")
        print(f"   星群ID: {config.constellation_id}")
        print(f"   设备数量: {len(config.devices)}")
        for i, device in enumerate(config.devices, 1):
            print(f"   设备{i}: {device.device_id} -> {device.server_url}")

        # 2. 创建客户端
        print("\n[2] 2. 创建 ConstellationClient...")
        client = ConstellationClient(config=config)

        # 3. 初始化并注册设备
        print("\n[3] 3. 初始化客户端并注册设备...")
        registration_results = await client.initialize()

        print("[*] 设备注册结果:")
        success_count = 0
        for device_id, success in registration_results.items():
            status = "[+] 成功" if success else "[-] 失败"
            print(f"   {device_id}: {status}")
            if success:
                success_count += 1

        print(
            f"\n[*] 注册统计: {success_count}/{len(registration_results)} 设备注册成功"
        )

        if success_count == 0:
            print("[-] 没有设备注册成功，停止测试")
            return False

        # 4. 检查连接状态
        print("\n[4] 4. 检查设备连接状态...")
        connected_devices = client.get_connected_devices()
        print(f"连接的设备: {connected_devices}")

        for device_id in connected_devices:
            status = client.get_device_status(device_id)
            print(f"   {device_id}: {status}")

        # 5. 获取星群信息
        print("\n[5] 5. 星群信息总结:")
        constellation_info = client.get_constellation_info()
        print(f"   星群ID: {constellation_info['constellation_id']}")
        print(f"   已连接设备: {constellation_info['connected_devices']}")
        print(f"   总设备数: {constellation_info['total_devices']}")
        print(
            f"   心跳间隔: {constellation_info['configuration']['heartbeat_interval']}s"
        )
        print(
            f"   最大并发任务: {constellation_info['configuration']['max_concurrent_tasks']}"
        )

        # 6. 等待一段时间观察连接稳定性
        if connected_devices:
            print("\n[6] 6. 测试连接稳定性 (等待 10 秒)...")
            await asyncio.sleep(10)

            # 再次检查连接状态
            final_connected = client.get_connected_devices()
            print(f"10秒后连接状态: {final_connected}")

            if len(final_connected) == len(connected_devices):
                print("[+] 连接稳定")
            else:
                print("[!] 连接不稳定，有设备断开")

        # 7. 测试配置验证
        print("\n[7] 7. 配置验证测试...")
        validation = client.validate_config()
        if validation["valid"]:
            print("[+] 配置验证通过")
        else:
            print("[-] 配置验证失败:")
            for error in validation["errors"]:
                print(f"   错误: {error}")
            for warning in validation["warnings"]:
                print(f"   警告: {warning}")

        # 8. 清理
        print("\n[8] 8. 清理连接...")
        await client.shutdown()
        print("[+] 客户端已关闭")

        return success_count > 0

    except Exception as e:
        print(f"\n[-] 测试过程中出现错误: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_device_operations():
    """测试设备操作功能"""

    print("\n" + "=" * 80)
    print("[*] 设备操作功能测试")
    print("=" * 80)

    try:
        # 使用配置创建客户端
        config = ConstellationConfig.from_yaml("config/constellation_sample.yaml")
        client = ConstellationClient(config=config)

        # 测试手动添加设备
        print("\n[+] 测试手动添加设备...")
        added = await client.add_device_to_config(
            device_id="test_device_manual",
            server_url="ws://localhost:5001/ws",
            capabilities=["testing", "manual"],
            metadata={"test": True},
            auto_connect=False,  # 不自动连接，避免连接错误
            register_immediately=False,
        )

        if added:
            print("[+] 手动添加设备成功")
            config_summary = client.get_config_summary()
            print(f"   当前设备总数: {config_summary['devices_count']}")
        else:
            print("[-] 手动添加设备失败")

        # 清理
        await client.shutdown()
        return True

    except Exception as e:
        print(f"[-] 设备操作测试失败: {e}")
        return False


async def main():
    """主测试函数"""

    print("[*] 开始 ConstellationClient 测试套件")

    # 测试1: 基础连接测试
    connection_test_passed = await test_constellation_client()

    # 测试2: 设备操作测试
    operations_test_passed = await test_device_operations()

    # 总结
    print("\n" + "=" * 80)
    print("[*] 测试结果总结")
    print("=" * 80)

    tests = [
        ("连接测试", connection_test_passed),
        ("设备操作测试", operations_test_passed),
    ]

    passed_count = 0
    for test_name, passed in tests:
        status = "[+] 通过" if passed else "[-] 失败"
        print(f"   {test_name}: {status}")
        if passed:
            passed_count += 1

    print(f"\n总体结果: {passed_count}/{len(tests)} 测试通过")

    if passed_count == len(tests):
        print("[+] 所有测试都通过了！ConstellationClient 工作正常。")
    else:
        print("[!] 部分测试失败，请检查配置和服务器状态。")


if __name__ == "__main__":
    asyncio.run(main())
