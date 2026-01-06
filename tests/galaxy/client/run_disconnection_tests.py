#!/usr/bin/env python
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Quick test runner for device disconnection and reconnection tests.

Usage:
    python tests/galaxy/client/run_disconnection_tests.py
"""

import sys
import subprocess


def main():
    """Run disconnection/reconnection tests"""

    print("=" * 70)
    print("🧪 Device Disconnection and Reconnection Tests")
    print("=" * 70)
    print()

    test_file = "tests/galaxy/client/test_device_disconnection_reconnection.py"

    # Run tests with verbose output
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_file,
        "-v",
        "--tb=short",
        "--color=yes",
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)

    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. See output above.")
    print("=" * 70)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
