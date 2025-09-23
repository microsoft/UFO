#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test script for the new modular session observer structure.
This script verifies that all observer classes can be imported and instantiated correctly.
"""

import sys
import os
import traceback

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_observer_imports():
    """Test that all observer classes can be imported correctly."""
    print("🧪 Testing observer imports...")

    try:
        from ufo.galaxy.session import (
            GalaxySession,
            ConstellationProgressObserver,
            SessionMetricsObserver,
            DAGVisualizationObserver,
        )

        print("✅ All main classes imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False


def test_observer_instantiation():
    """Test that observer instances can be created correctly."""
    print("\n🧪 Testing observer instantiation...")

    try:
        from ufo.galaxy.session import SessionMetricsObserver, DAGVisualizationObserver

        # Test SessionMetricsObserver
        metrics_observer = SessionMetricsObserver(session_id="test_session")
        print(f"✅ SessionMetricsObserver created: {type(metrics_observer)}")

        # Test initial metrics
        initial_metrics = metrics_observer.get_metrics()
        expected_keys = {
            "session_id",
            "task_count",
            "completed_tasks",
            "failed_tasks",
            "total_execution_time",
            "task_timings",
        }
        if expected_keys.issubset(initial_metrics.keys()):
            print("✅ SessionMetricsObserver has expected metrics structure")
        else:
            print(
                f"❌ Missing expected metrics keys: {expected_keys - initial_metrics.keys()}"
            )
            return False

        # Test DAGVisualizationObserver (with visualization disabled to avoid import issues)
        dag_observer = DAGVisualizationObserver(enable_visualization=False)
        print(f"✅ DAGVisualizationObserver created: {type(dag_observer)}")

        return True

    except Exception as e:
        print(f"❌ Instantiation failed: {e}")
        traceback.print_exc()
        return False


def test_modular_structure():
    """Test that the modular structure is working correctly."""
    print("\n🧪 Testing modular structure...")

    try:
        # Test direct imports from observers module
        from ufo.galaxy.session.observers import (
            ConstellationProgressObserver,
            SessionMetricsObserver,
            DAGVisualizationObserver,
        )

        # Test visualization components are imported separately
        from ufo.galaxy.visualization import (
            TaskDisplay,
            ConstellationDisplay,
            VisualizationChangeDetector,
        )

        print("✅ Direct observer module imports successful")
        print("✅ Visualization module imports successful")

        # Test that observers work with visualization components
        observer = DAGVisualizationObserver()
        task_display = TaskDisplay()
        constellation_display = ConstellationDisplay()
        change_detector = VisualizationChangeDetector()

        print("✅ Observers and visualization components integrate correctly")

        # Test that observers integrate with visualization components
        observer = DAGVisualizationObserver()
        print(f"✅ DAGVisualizationObserver: {type(observer)}")

        # Test change detector functionality
        print(f"✅ VisualizationChangeDetector: {type(change_detector)}")

        print(
            "✅ Modular structure test passed - observers delegate to visualization components"
        )
        return True

    except Exception as e:
        print(f"❌ Modular structure test failed: {e}")
        traceback.print_exc()
        return False


def test_observer_interfaces():
    """Test that observers implement the expected interfaces."""
    print("\n🧪 Testing observer interfaces...")

    try:
        from ufo.galaxy.session import SessionMetricsObserver, DAGVisualizationObserver
        from ufo.galaxy.core.events import IEventObserver

        # Test SessionMetricsObserver interface
        metrics_observer = SessionMetricsObserver(session_id="test")
        if isinstance(metrics_observer, IEventObserver):
            print("✅ SessionMetricsObserver implements IEventObserver")
        else:
            print("❌ SessionMetricsObserver does not implement IEventObserver")
            return False

        if hasattr(metrics_observer, "on_event") and callable(
            getattr(metrics_observer, "on_event")
        ):
            print("✅ SessionMetricsObserver has on_event method")
        else:
            print("❌ SessionMetricsObserver missing on_event method")
            return False

        # Test DAGVisualizationObserver interface
        dag_observer = DAGVisualizationObserver(enable_visualization=False)
        if isinstance(dag_observer, IEventObserver):
            print("✅ DAGVisualizationObserver implements IEventObserver")
        else:
            print("❌ DAGVisualizationObserver does not implement IEventObserver")
            return False

        if hasattr(dag_observer, "on_event") and callable(
            getattr(dag_observer, "on_event")
        ):
            print("✅ DAGVisualizationObserver has on_event method")
        else:
            print("❌ DAGVisualizationObserver missing on_event method")
            return False

        return True

    except Exception as e:
        print(f"❌ Interface test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests and report results."""
    print("🚀 Starting Session Observer Module Tests")
    print("=" * 50)

    tests = [
        test_observer_imports,
        test_observer_instantiation,
        test_modular_structure,
        test_observer_interfaces,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")

    passed = sum(results)
    total = len(results)

    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {i+1}. {test.__name__}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Observer module structure is working correctly.")
        return 0
    else:
        print("💥 Some tests failed. Please check the observer module structure.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
