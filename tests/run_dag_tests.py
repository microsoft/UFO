#!/usr/bin/env python3
"""
Test runner for DAG visualization tests.

This script runs all DAG visualization tests in the correct order.
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)


def run_test(test_file: str, test_name: str) -> bool:
    """Run a single test file and return success status."""
    print(f"\n{'='*60}")
    print(f"🧪 Running {test_name}")
    print(f"📁 File: {test_file}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        # Run the test
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=project_root,
            capture_output=False,  # Show output in real-time
            text=True,
        )

        end_time = time.time()
        duration = end_time - start_time

        if result.returncode == 0:
            print(f"\n✅ {test_name} PASSED ({duration:.2f}s)")
            return True
        else:
            print(f"\n❌ {test_name} FAILED ({duration:.2f}s)")
            print(f"Exit code: {result.returncode}")
            return False

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n💥 {test_name} ERROR ({duration:.2f}s): {e}")
        return False


def main():
    """Run all DAG visualization tests."""
    print("🌌 DAG Visualization Test Suite")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Define test order (from simple to complex)
    tests = [
        {"file": "tests/visualization/test_dag_simple.py", "name": "Simple DAG Test"},
        {
            "file": "tests/visualization/test_dag_mock.py",
            "name": "Mock DAG Visualization Test",
        },
        {
            "file": "tests/visualization/test_dag_demo.py",
            "name": "Interactive DAG Demo",
        },
        {
            "file": "tests/integration/test_e2e_galaxy.py",
            "name": "End-to-End Galaxy Integration Test",
        },
        {
            "file": "tests/integration/test_e2e_simplified.py",
            "name": "End-to-End Galaxy Integration Test (Simplified)",
        },
    ]

    # Track results
    results = {"total": len(tests), "passed": 0, "failed": 0, "start_time": time.time()}

    # Run each test
    for test in tests:
        test_file = os.path.join(project_root, test["file"])

        if not os.path.exists(test_file):
            print(f"❌ Test file not found: {test_file}")
            results["failed"] += 1
            continue

        success = run_test(test_file, test["name"])

        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Small delay between tests
        time.sleep(1)

    # Calculate final results
    total_time = time.time() - results["start_time"]
    success_rate = (
        (results["passed"] / results["total"]) * 100 if results["total"] > 0 else 0
    )

    # Print summary
    print("\n" + "=" * 80)
    print("🎯 TEST SUITE SUMMARY")
    print("=" * 80)
    print(f"📊 Total Tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    print(f"⏱️  Total Time: {total_time:.2f} seconds")
    print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if results["failed"] == 0:
        print("\n🎉 All tests passed! DAG visualization is working correctly.")
        return 0
    else:
        print(
            f"\n⚠️  {results['failed']} test(s) failed. Please check the output above."
        )
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
