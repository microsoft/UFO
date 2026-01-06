#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Run all cancellation-related tests.

This script runs all unit and integration tests for the task cancellation mechanism.
"""

import subprocess
import sys
from pathlib import Path

# Test files to run
TEST_FILES = [
    "tests/galaxy/client/test_galaxy_client_cancellation.py",
    "tests/galaxy/session/test_session_cancellation.py",
    "tests/galaxy/constellation/test_orchestrator_cancellation.py",
    "tests/galaxy/webui/test_webui_stop_integration.py",
]


def run_tests():
    """Run all cancellation tests."""
    print("=" * 80)
    print("Running Task Cancellation Tests")
    print("=" * 80)
    print()

    all_passed = True

    for test_file in TEST_FILES:
        print(f"\n{'=' * 80}")
        print(f"Running: {test_file}")
        print(f"{'=' * 80}\n")

        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "-s"],
            cwd=Path(__file__).parent.parent,
        )

        if result.returncode != 0:
            all_passed = False
            print(f"\n❌ FAILED: {test_file}\n")
        else:
            print(f"\n✅ PASSED: {test_file}\n")

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ All cancellation tests PASSED!")
    else:
        print("❌ Some tests FAILED. Please check the output above.")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_tests())
