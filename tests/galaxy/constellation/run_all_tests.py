"""
Run all constellation parsing tests.

This script runs all the constellation parsing validation tests in sequence.
"""

import subprocess
import sys
from pathlib import Path

# Get the directory where this script is located
test_dir = Path(__file__).parent


def run_test(test_file: str, description: str) -> bool:
    """Run a single test file and return success status."""
    print("\n" + "=" * 80)
    print(f"Running: {description}")
    print("=" * 80)

    test_path = test_dir / test_file
    result = subprocess.run(
        [sys.executable, str(test_path)], capture_output=False, text=True
    )

    success = result.returncode == 0
    if success:
        print(f"\n[OK] {description} PASSED")
    else:
        print(f"\n[FAIL] {description} FAILED (exit code: {result.returncode})")

    return success


def main():
    """Run all constellation parsing tests."""
    print("=" * 80)
    print("CONSTELLATION PARSING TEST SUITE")
    print("=" * 80)
    print(
        "\nThis suite tests TaskConstellation.from_json() parsing with real log data."
    )
    print("Log file: logs/galaxy/task_1/response.log\n")

    tests = [
        ("test_constellation_parsing.py", "Main Parsing Test"),
        ("test_constellation_parsing_debug.py", "JSON Structure Debug"),
        ("test_constellation_tasks_debug.py", "Tasks Field Debug"),
        ("test_constellation_summary.py", "Comprehensive Summary"),
    ]

    results = []
    for test_file, description in tests:
        success = run_test(test_file, description)
        results.append((description, success))

    # Print final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "[OK] PASSED" if success else "[FAIL] FAILED"
        print(f"{status}: {description}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\nSee docs/CONSTELLATION_PARSING_TEST_REPORT.md for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
