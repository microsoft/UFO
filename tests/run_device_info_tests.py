"""
Comprehensive Test Script for Device Info Feature

This script runs all device info related tests:
1. Unit tests for DeviceInfoProvider (system info collection)
2. Unit tests for WSManager device info handling (server-side storage)
3. Integration tests for end-to-end device info flow
4. DeviceManager integration tests for device info updates
"""

import subprocess
import sys
import os
from pathlib import Path


def run_tests():
    """Run all device info tests"""

    project_root = Path(__file__).parent.parent
    test_files = [
        "tests/unit/test_device_info_provider.py",
        "tests/unit/test_ws_manager_device_info.py",
        "tests/integration/test_device_info_flow.py",
        "tests/galaxy/client/test_device_manager_info_update.py",
    ]

    print("=" * 80)
    print("Running Device Info Feature Tests")
    print("=" * 80)

    all_passed = True

    for test_file in test_files:
        test_path = project_root / test_file

        if not test_path.exists():
            print(f"\n❌ Test file not found: {test_file}")
            all_passed = False
            continue

        print(f"\n{'=' * 80}")
        print(f"Running: {test_file}")
        print("=" * 80)

        # Set environment with PYTHONPATH for galaxy imports
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
            cwd=str(project_root),
            capture_output=False,
            env=env,
        )

        if result.returncode != 0:
            print(f"\n❌ Tests failed in {test_file}")
            all_passed = False
        else:
            print(f"\n✅ Tests passed in {test_file}")

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ All device info tests passed!")
    else:
        print("❌ Some tests failed. Please check the output above.")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_tests())
