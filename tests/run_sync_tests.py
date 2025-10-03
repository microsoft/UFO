# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test runner script for ConstellationModificationSynchronizer tests.

This script runs all tests related to the synchronization mechanism
and generates a comprehensive report.
"""

import sys
import subprocess
import os


def run_tests():
    """Run all synchronization tests."""
    print("=" * 80)
    print("Running ConstellationModificationSynchronizer Tests")
    print("=" * 80)
    print()
    
    # Test files to run
    test_files = [
        "tests/test_constellation_sync_observer.py",
        "tests/test_constellation_sync_integration.py",
    ]
    
    results = {}
    
    for test_file in test_files:
        print(f"\n{'=' * 80}")
        print(f"Running: {test_file}")
        print('=' * 80)
        
        # Run pytest with verbose output
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            test_file,
            "-v",
            "-s",
            "--tb=short",
            "--color=yes",
        ]
        
        result = subprocess.run(cmd, capture_output=False)
        results[test_file] = result.returncode
        
        print()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for test_file, returncode in results.items():
        status = "✅ PASSED" if returncode == 0 else "❌ FAILED"
        print(f"{status} - {test_file}")
        if returncode != 0:
            all_passed = False
    
    print("=" * 80)
    
    if all_passed:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
