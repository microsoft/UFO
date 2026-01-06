"""
Device Info Feature Demo

This script demonstrates the device info collection functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ufo.client.device_info_provider import DeviceInfoProvider


def demo_device_info_collection():
    """Demonstrate device info collection"""

    print("=" * 80)
    print("Device Information Collection Demo")
    print("=" * 80)

    # Collect system information
    print("\n📊 Collecting device system information...")

    try:
        device_info = DeviceInfoProvider.collect_system_info(
            client_id="demo_device_001",
            custom_metadata={"demo": True, "purpose": "testing"},
        )

        print("\n✅ System information collected successfully!")
        print("\n" + "-" * 80)
        print("Device System Information:")
        print("-" * 80)

        print(f"Device ID:       {device_info.device_id}")
        print(f"Platform:        {device_info.platform}")
        print(f"OS Version:      {device_info.os_version}")
        print(f"Platform Type:   {device_info.platform_type}")
        print(f"CPU Cores:       {device_info.cpu_count}")
        print(f"Total Memory:    {device_info.memory_total_gb} GB")
        print(f"Hostname:        {device_info.hostname}")
        print(f"IP Address:      {device_info.ip_address}")
        print(f"Schema Version:  {device_info.schema_version}")

        print(f"\nSupported Features ({len(device_info.supported_features)}):")
        for feature in device_info.supported_features:
            print(f"  • {feature}")

        if device_info.custom_metadata:
            print(f"\nCustom Metadata:")
            for key, value in device_info.custom_metadata.items():
                print(f"  • {key}: {value}")

        print("\n" + "-" * 80)
        print("Dictionary Representation:")
        print("-" * 80)

        info_dict = device_info.to_dict()
        import json

        print(json.dumps(info_dict, indent=2))

        print("\n" + "=" * 80)
        print("✅ Demo completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error collecting device info: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(demo_device_info_collection())
