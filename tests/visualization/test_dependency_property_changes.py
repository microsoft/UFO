#!/usr/bin/env python
"""
Test script for dependency property change detection and visualization.
"""

import asyncio
import pytest
from galaxy.constellation import TaskConstellation, TaskStar, TaskStarLine
from galaxy.session.observers import DAGVisualizationObserver
from galaxy.core.events import ConstellationEvent, EventType


@pytest.mark.asyncio
async def test_dependency_property_changes():
    """Test dependency property change detection."""
    print("🧪 Testing Dependency Property Change Detection\n")

    # Create observer (no context needed for this test)
    observer = DAGVisualizationObserver()

    # Create original constellation
    print("Creating original constellation...")
    original_constellation = TaskConstellation(
        "test-constellation", "Test Constellation"
    )

    task1 = TaskStar("task1", "First Task")
    task2 = TaskStar("task2", "Second Task")

    # Original dependency with specific properties
    dep1 = TaskStarLine("task1", "task2")
    dep1.trigger_action = "original_action"
    dep1.trigger_actor = "original_actor"
    dep1.condition = "original_condition"
    dep1.keyword = "original_keyword"

    original_constellation.add_task(task1)
    original_constellation.add_task(task2)
    original_constellation.add_dependency(dep1)

    print(
        f"Original constellation: {len(original_constellation.tasks)} tasks, {len(original_constellation.dependencies)} dependencies"
    )

    # Create modified constellation with changed dependency properties
    print("\nCreating modified constellation with changed dependency properties...")
    modified_constellation = TaskConstellation(
        "test-constellation", "Test Constellation"
    )

    task1_mod = TaskStar("task1", "First Task")
    task2_mod = TaskStar("task2", "Second Task")

    # Modified dependency with different properties
    dep1_mod = TaskStarLine("task1", "task2")
    dep1_mod.trigger_action = "modified_action"  # Changed
    dep1_mod.trigger_actor = "original_actor"  # Same
    dep1_mod.condition = "modified_condition"  # Changed
    dep1_mod.keyword = "original_keyword"  # Same

    modified_constellation.add_task(task1_mod)
    modified_constellation.add_task(task2_mod)
    modified_constellation.add_dependency(dep1_mod)

    print(
        f"Modified constellation: {len(modified_constellation.tasks)} tasks, {len(modified_constellation.dependencies)} dependencies"
    )

    # Test dependency property change detection
    print("\nTest: Dependency property modification detection")

    import time

    event = ConstellationEvent(
        event_type=EventType.CONSTELLATION_MODIFIED,
        source_id="test-source",
        timestamp=time.time(),
        data={
            "old_constellation": original_constellation,
            "new_constellation": modified_constellation,
            "modification_type": "dependency_properties_updated",
        },
        constellation_id="test-constellation",
        constellation_state="modified",
    )

    await observer.on_event(event)

    print("=" * 80)

    # Test 2: Multiple property changes
    print("\nTest 2: Multiple dependency property changes")

    # Create another modified constellation with more changes
    multi_mod_constellation = TaskConstellation(
        "test-constellation", "Test Constellation"
    )

    task1_multi = TaskStar("task1", "First Task")
    task2_multi = TaskStar("task2", "Second Task")

    # More extensively modified dependency
    dep1_multi = TaskStarLine("task1", "task2")
    dep1_multi.trigger_action = "completely_new_action"  # Changed
    dep1_multi.trigger_actor = "completely_new_actor"  # Changed
    dep1_multi.condition = "completely_new_condition"  # Changed
    dep1_multi.keyword = "completely_new_keyword"  # Changed

    multi_mod_constellation.add_task(task1_multi)
    multi_mod_constellation.add_task(task2_multi)
    multi_mod_constellation.add_dependency(dep1_multi)

    event2 = ConstellationEvent(
        event_type=EventType.CONSTELLATION_MODIFIED,
        source_id="test-source",
        timestamp=time.time(),
        data={
            "old_constellation": original_constellation,
            "new_constellation": multi_mod_constellation,
            "modification_type": "dependency_properties_updated",
        },
        constellation_id="test-constellation",
        constellation_state="modified",
    )

    await observer.on_event(event2)

    print("✅ All dependency property change tests completed!")


if __name__ == "__main__":
    asyncio.run(test_dependency_property_changes())
