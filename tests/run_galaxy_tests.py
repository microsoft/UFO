# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test runner for Galaxy Agent State Machine refactoring

This script runs all tests for the refactored Galaxy Agent State Machine,
including unit tests and integration tests covering various scenarios.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_test_suite():
    """Run the complete test suite for Galaxy Agent State Machine."""

    # Get the root directory
    root_dir = Path(__file__).parent.parent.parent.parent
    os.chdir(root_dir)

    print("🚀 Running Galaxy Agent State Machine Test Suite")
    print("=" * 60)

    # Test files to run
    test_files = [
        # Unit tests
        "tests/unit/galaxy/agents/test_galaxy_agent_states.py",
        "tests/unit/galaxy/session/test_galaxy_round_refactored.py",
        "tests/unit/galaxy/session/test_observers_refactored.py",
        # Integration tests
        "tests/integration/galaxy/test_galaxy_state_machine_integration.py",
    ]

    failed_tests = []
    passed_tests = []

    for test_file in test_files:
        print(f"\n📋 Running: {test_file}")
        print("-" * 40)

        try:
            # Run pytest for the specific test file
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    test_file,
                    "-v",
                    "--tb=short",
                    "--no-header",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                print(f"✅ PASSED: {test_file}")
                passed_tests.append(test_file)

                # Show summary of passed tests
                lines = result.stdout.split("\n")
                for line in lines:
                    if "passed" in line and ("failed" in line or "error" in line):
                        print(f"   📊 {line.strip()}")
                        break

            else:
                print(f"❌ FAILED: {test_file}")
                failed_tests.append(test_file)

                # Show error details
                print("Error output:")
                print(result.stdout)
                if result.stderr:
                    print("Stderr:")
                    print(result.stderr)

        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT: {test_file}")
            failed_tests.append(test_file)

        except Exception as e:
            print(f"💥 EXCEPTION: {test_file} - {e}")
            failed_tests.append(test_file)

    # Final summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUITE SUMMARY")
    print("=" * 60)

    print(f"✅ Passed: {len(passed_tests)}")
    for test in passed_tests:
        print(f"   • {test}")

    if failed_tests:
        print(f"\n❌ Failed: {len(failed_tests)}")
        for test in failed_tests:
            print(f"   • {test}")

    total_tests = len(test_files)
    success_rate = (len(passed_tests) / total_tests) * 100 if total_tests > 0 else 0

    print(f"\n📊 Success Rate: {success_rate:.1f}% ({len(passed_tests)}/{total_tests})")

    if failed_tests:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return False
    else:
        print("\n🎉 All tests passed! Galaxy Agent State Machine refactoring is ready.")
        return True


def run_specific_test_scenarios():
    """Run specific test scenarios mentioned in the requirements."""

    print("\n🎯 Running Specific Scenario Tests")
    print("=" * 60)

    scenarios = [
        {
            "name": "Constellation execution to completion without updates",
            "test": "tests/integration/galaxy/test_galaxy_state_machine_integration.py::TestConstellationExecutionToCompletion::test_constellation_completes_without_updates",
        },
        {
            "name": "Constellation execution with mid-execution agent termination",
            "test": "tests/integration/galaxy/test_galaxy_state_machine_integration.py::TestMidExecutionAgentTermination::test_agent_terminates_mid_execution",
        },
        {
            "name": "Constellation completion followed by agent adding new tasks",
            "test": "tests/integration/galaxy/test_galaxy_state_machine_integration.py::TestConstellationWithNewTaskAddition::test_constellation_expansion_after_completion",
        },
        {
            "name": "Race condition handling between task completion and constellation updates",
            "test": "tests/integration/galaxy/test_galaxy_state_machine_integration.py::TestRaceConditionHandling::test_race_condition_handling",
        },
        {
            "name": "Complex multi-round scenarios",
            "test": "tests/integration/galaxy/test_galaxy_state_machine_integration.py::TestComplexMultiRoundScenarios::test_multi_round_execution_with_state_persistence",
        },
    ]

    passed_scenarios = []
    failed_scenarios = []

    for scenario in scenarios:
        print(f"\n🔬 Testing: {scenario['name']}")
        print("-" * 40)

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", scenario["test"], "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                print(f"✅ PASSED: {scenario['name']}")
                passed_scenarios.append(scenario["name"])
            else:
                print(f"❌ FAILED: {scenario['name']}")
                failed_scenarios.append(scenario["name"])
                print("Error details:")
                print(
                    result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
                )

        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT: {scenario['name']}")
            failed_scenarios.append(scenario["name"])
        except Exception as e:
            print(f"💥 EXCEPTION: {scenario['name']} - {e}")
            failed_scenarios.append(scenario["name"])

    print(f"\n📊 Scenario Test Results:")
    print(f"   ✅ Passed: {len(passed_scenarios)}")
    print(f"   ❌ Failed: {len(failed_scenarios)}")

    return len(failed_scenarios) == 0


def check_test_coverage():
    """Check test coverage for the refactored components."""

    print("\n📈 Checking Test Coverage")
    print("=" * 60)

    components_to_test = [
        "ufo/galaxy/agents/galaxy_agent_states.py",
        "ufo/galaxy/session/galaxy_session.py",
        "ufo/galaxy/session/observers.py",
    ]

    try:
        # Run coverage analysis
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--cov=ufo.galaxy.agents.galaxy_agent_states",
                "--cov=ufo.galaxy.session.galaxy_session",
                "--cov=ufo.galaxy.session.observers",
                "--cov-report=term-missing",
                "--cov-report=html",
                "tests/unit/galaxy/",
                "tests/integration/galaxy/",
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )

        print("Coverage Report:")
        print(result.stdout)

        if "html" in result.stdout:
            print("\n📄 HTML coverage report generated in htmlcov/")

    except subprocess.TimeoutExpired:
        print("⏰ Coverage analysis timed out")
    except Exception as e:
        print(f"💥 Coverage analysis failed: {e}")


def main():
    """Main test runner."""

    print("🧪 Galaxy Agent State Machine Test Runner")
    print("Testing the refactored state machine implementation")
    print("=" * 60)

    # Run full test suite
    suite_success = run_test_suite()

    # Run specific scenarios
    scenario_success = run_specific_test_scenarios()

    # Check coverage
    check_test_coverage()

    # Final status
    print("\n" + "=" * 60)
    if suite_success and scenario_success:
        print("🎉 ALL TESTS PASSED! Refactoring is complete and ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review and fix issues before deployment.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
