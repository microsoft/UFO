#!/usr/bin/env python3
"""
Test script specifically for individual event visualization.
"""

import asyncio
import time
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.constellation.task_star import TaskStar
from galaxy.core.events import (
    get_event_bus,
    EventType,
    TaskEvent,
    ConstellationEvent,
)
from galaxy.session.observers import DAGVisualizationObserver
from galaxy.constellation.enums import TaskStatus


#!/usr/bin/env python3
"""
Test script specifically for individual event visualization.
"""

import asyncio
import time
import pytest
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.constellation.task_star import TaskStar
from galaxy.core.events import (
    get_event_bus,
    EventType,
    TaskEvent,
    ConstellationEvent,
)
from galaxy.session.observers import DAGVisualizationObserver


@pytest.mark.asyncio
async def test_individual_events():
    """Test individual event visualizations."""
    print("🎯 Testing Individual Event Visualizations...")

    # Create event bus and visualization observer
    event_bus = get_event_bus()
    viz_observer = DAGVisualizationObserver(enable_visualization=True)

    # Subscribe to all event types
    event_bus.subscribe(
        observer=viz_observer,
        event_types={
            EventType.CONSTELLATION_STARTED,
            EventType.CONSTELLATION_COMPLETED,
            EventType.CONSTELLATION_MODIFIED,
            EventType.TASK_STARTED,
            EventType.TASK_COMPLETED,
            EventType.TASK_FAILED,
        },
    )

    # Create a test constellation
    constellation = TaskConstellation("individual_test")
    task = TaskStar(
        task_id="test_task",
        name="Test Task",
        description="A sample task for testing visualization",
        target_device_id="device_1",
        task_data={"command": "test_command"},
        tips=["This is a test tip", "Another helpful hint"],
    )
    constellation.add_task(task)

    # Store constellation in viz observer for event handling
    viz_observer._constellations[constellation.constellation_id] = constellation

    print("\n🚀 Testing TASK_STARTED event...")
    task_started_event = TaskEvent(
        event_type=EventType.TASK_STARTED,
        source_id="test_script",
        timestamp=time.time(),
        data={"constellation_id": constellation.constellation_id},
        task_id="test_task",
        status=TaskStatus.RUNNING.value,
    )
    await event_bus.publish_event(task_started_event)
    await asyncio.sleep(1)

    print("\n✅ Testing TASK_COMPLETED event...")
    task_completed_event = TaskEvent(
        event_type=EventType.TASK_COMPLETED,
        source_id="test_script",
        timestamp=time.time(),
        data={
            "constellation_id": constellation.constellation_id,
            "newly_ready_tasks": ["next_task_1", "next_task_2"],
        },
        task_id="test_task",
        status=TaskStatus.COMPLETED.value,
        result={"output": "Task completed successfully", "score": 95.5},
    )
    await event_bus.publish_event(task_completed_event)
    await asyncio.sleep(1)

    print("\n❌ Testing TASK_FAILED event...")
    task_failed_event = TaskEvent(
        event_type=EventType.TASK_FAILED,
        source_id="test_script",
        timestamp=time.time(),
        data={
            "constellation_id": constellation.constellation_id,
            "newly_ready_tasks": [],
        },
        task_id="test_task",
        status=TaskStatus.FAILED.value,
        error=Exception("Sample error: Connection timeout occurred"),
    )
    await event_bus.publish_event(task_failed_event)
    await asyncio.sleep(1)

    print("\n🔄 Testing CONSTELLATION_MODIFIED event...")
    modification_event = ConstellationEvent(
        event_type=EventType.CONSTELLATION_MODIFIED,
        source_id="test_script",
        timestamp=time.time(),
        data={
            "constellation": constellation,
            "modification_type": "task_properties_updated",
            "added_tasks": [],
            "removed_tasks": [],
            "added_dependencies": [],
            "removed_dependencies": [],
            "modified_tasks": ["test_task"],
        },
        constellation_id=constellation.constellation_id,
        constellation_state="modified",
    )
    await event_bus.publish_event(modification_event)
    await asyncio.sleep(1)

    print("\n🎉 Individual event visualization tests completed!")


if __name__ == "__main__":
    asyncio.run(test_individual_events())
