#!/usr/bin/env python3

"""
Quick test to verify color display in constellation_modified method.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from galaxy.visualization.constellation_display import ConstellationDisplay
from rich.console import Console


# Mock constellation class for testing
class MockConstellation:
    def __init__(self):
        self.name = "Test Constellation"
        self.constellation_id = "12345678-abcd-efgh-ijkl-mnopqrstuvwx"
        self.state = "EXECUTING"

    def get_statistics(self):
        return {
            "total_tasks": 10,
            "total_dependencies": 8,
            "completed_tasks": 3,
            "failed_tasks": 1,
            "running_tasks": 2,
            "ready_tasks": 4,
        }


def test_color_display():
    """Test that colors are properly displayed in modification display."""
    console = Console()
    display = ConstellationDisplay(console)

    # Create mock constellation
    constellation = MockConstellation()

    # Create test changes with different types
    changes = {
        "modification_type": "tasks_added",
        "added_tasks": ["task1", "task2", "task3"],
        "removed_tasks": ["old_task"],
        "added_dependencies": [("task1", "task2"), ("task2", "task3")],
        "removed_dependencies": [("old_dep1", "old_dep2")],
        "modified_tasks": ["modified_task1"],
    }

    additional_info = {"timestamp": "2025-09-23 14:30:00", "user": "test_user"}

    print("Testing constellation modification display with colors:")
    print("=" * 60)

    # Display the modification
    display.display_constellation_modified(constellation, changes, additional_info)

    print("\n" + "=" * 60)
    print("✅ Color test completed!")


if __name__ == "__main__":
    test_color_display()
