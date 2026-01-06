# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Observer Module Structure Test

This test verifies the new modular observer structure works correctly
and all modules can be imported and used independently.
"""

import sys
import os

# Add project root to path for testing
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, project_root)


def test_modular_imports():
    """Test that all observer modules can be imported from the new structure."""

    print("Testing modular observer imports...")

    # Test main observer imports
    try:
        from galaxy.session.observers import (
            ConstellationProgressObserver,
            SessionMetricsObserver,
            DAGVisualizationObserver,
        )

        print("✓ Main observer imports successful")
    except ImportError as e:
        print(f"✗ Main observer import failed: {e}")
        return False

    # Test individual module imports
    try:
        from galaxy.session.observers.base_observer import (
            ConstellationProgressObserver as DirectProgressObserver,
            SessionMetricsObserver as DirectMetricsObserver,
        )

        print("✓ Direct base_observer imports successful")
    except ImportError as e:
        print(f"✗ Direct base_observer import failed: {e}")
        return False

    try:
        from galaxy.session.observers.dag_visualization_observer import (
            DAGVisualizationObserver as DirectDAGObserver,
        )

        print("✓ Direct dag_visualization_observer import successful")
    except ImportError as e:
        print(f"✗ Direct dag_visualization_observer import failed: {e}")
        return False

    # Test that imports are the same objects
    assert ConstellationProgressObserver is DirectProgressObserver
    assert SessionMetricsObserver is DirectMetricsObserver
    assert DAGVisualizationObserver is DirectDAGObserver
    print("✓ Import consistency verified")

    return True


def test_observer_modules():
    """Test that observer modules are properly structured."""

    print("\nTesting observer module structure...")

    from galaxy.session.observers import (
        ConstellationProgressObserver,
        SessionMetricsObserver,
        DAGVisualizationObserver,
    )

    # Check module locations
    expected_modules = {
        ConstellationProgressObserver: "ufo.galaxy.session.observers.base_observer",
        SessionMetricsObserver: "ufo.galaxy.session.observers.base_observer",
        DAGVisualizationObserver: "ufo.galaxy.session.observers.dag_visualization_observer",
    }

    for observer_class, expected_module in expected_modules.items():
        actual_module = observer_class.__module__
        if actual_module == expected_module:
            print(f"✓ {observer_class.__name__} in correct module: {actual_module}")
        else:
            print(
                f"✗ {observer_class.__name__} in wrong module: {actual_module} (expected: {expected_module})"
            )
            return False

    return True


def test_observer_instantiation():
    """Test that observers can be instantiated with mock parameters."""

    print("\nTesting observer instantiation...")

    from galaxy.session.observers import (
        ConstellationProgressObserver,
        SessionMetricsObserver,
        DAGVisualizationObserver,
    )
    from unittest.mock import Mock

    try:
        # Test ConstellationProgressObserver
        mock_agent = Mock()
        mock_context = Mock()
        progress_observer = ConstellationProgressObserver(
            agent=mock_agent, context=mock_context
        )
        assert progress_observer.agent == mock_agent
        assert progress_observer.context == mock_context
        print("✓ ConstellationProgressObserver instantiation successful")

        # Test SessionMetricsObserver
        metrics_observer = SessionMetricsObserver(session_id="test_session")
        assert metrics_observer.metrics["session_id"] == "test_session"
        print("✓ SessionMetricsObserver instantiation successful")

        # Test DAGVisualizationObserver
        dag_observer = DAGVisualizationObserver(enable_visualization=False)
        assert dag_observer.enable_visualization == False
        print("✓ DAGVisualizationObserver instantiation successful")

        return True

    except Exception as e:
        print(f"✗ Observer instantiation failed: {e}")
        return False


def test_backward_compatibility():
    """Test that existing imports still work."""

    print("\nTesting backward compatibility...")

    try:
        # Test imports that existing code uses
        from galaxy.session.observers import ConstellationProgressObserver
        from galaxy.session import GalaxySession

        # Test that GalaxySession can still import observers
        import galaxy.session.galaxy_session as gs_module

        # Check that galaxy_session.py can access the observers
        assert hasattr(gs_module, "ConstellationProgressObserver")
        assert hasattr(gs_module, "SessionMetricsObserver")
        assert hasattr(gs_module, "DAGVisualizationObserver")

        print("✓ Backward compatibility maintained")
        return True

    except Exception as e:
        print(f"✗ Backward compatibility test failed: {e}")
        return False


def main():
    """Run all modular observer tests."""

    print("=" * 60)
    print("MODULAR OBSERVER STRUCTURE TESTS")
    print("=" * 60)

    tests = [
        test_modular_imports,
        test_observer_modules,
        test_observer_instantiation,
        test_backward_compatibility,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"Test {test.__name__} failed")
        except Exception as e:
            print(f"Test {test.__name__} crashed: {e}")

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("🎉 All modular observer tests passed! The refactoring was successful.")
        return True
    else:
        print("❌ Some tests failed. Please check the modular structure.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
