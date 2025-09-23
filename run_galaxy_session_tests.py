#!/usr/bin/env python3
"""
Galaxy Session Test Runner

Convenient script to run all Galaxy Session tests from the root directory.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_test(test_file, description):
    """Run a single test file and report results."""
    print(f"\n{'=' * 60}")
    print(f"🧪 Running: {description}")
    print(f"📁 File: {test_file}")
    print("=" * 60)

    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=False,
            text=True,
            cwd=Path(__file__).parent,
        )

        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False

    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main():
    """Run all Galaxy Session tests."""
    print("🚀 Galaxy Session Test Suite Runner")
    print("=" * 60)

    tests = [
        (
            "tests/galaxy/session/test_galaxy_session.py",
            "Basic GalaxySession Functionality",
        ),
        (
            "tests/galaxy/session/test_galaxy_session_integration.py",
            "Integration Tests",
        ),
        (
            "tests/galaxy/session/test_galaxy_session_proper_mock.py",
            "Proper Mocking Tests",
        ),
        (
            "tests/galaxy/session/test_galaxy_session_final.py",
            "Final Comprehensive Tests",
        ),
    ]

    passed = 0
    total = len(tests)

    for test_file, description in tests:
        if os.path.exists(test_file):
            if run_test(test_file, description):
                passed += 1
        else:
            print(f"⚠️  Test file not found: {test_file}")

    print(f"\n{'=' * 60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
