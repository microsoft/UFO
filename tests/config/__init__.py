# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test suite runner for configuration system.

Run all tests:
    python -m pytest tests/config/

Run specific test file:
    python -m pytest tests/config/test_config_loader.py

Run with coverage:
    python -m pytest tests/config/ --cov=config --cov-report=html

Run verbose:
    python -m pytest tests/config/ -v
"""

import unittest


def run_all_tests():
    """Discover and run all tests in the config test suite."""
    loader = unittest.TestLoader()
    start_dir = "tests/config"
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys

    success = run_all_tests()
    sys.exit(0 if success else 1)
