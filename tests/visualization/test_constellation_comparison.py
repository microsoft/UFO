#!/usr/bin/env python3
"""
Test script for constellation modification with automatic comparison.
"""

import asyncio
import pytest
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath("."))

from galaxy.constellation import TaskConstellation, TaskStar, TaskStarLine
from galaxy.core.events import ConstellationEvent, EventType
from galaxy.session.observers import DAGVisualizationObserver
from rich.console import Console


@pytest.mark.asyncio
async def test_constellation_comparison():
    """Test constellation modification with automatic comparison."""

    console = Console()
    console.print(
        "[bold blue]🧪 Testing Constellation Modification Comparison[/bold blue]\n"
    )

    # Initialize observer
    observer = DAGVisualizationObserver(enable_visualization=True, console=console)

    # Create original constellation
    console.print("[cyan]Creating original constellation...[/cyan]")
    old_constellation = TaskConstellation("test-constellation", "Test Constellation")

    # Add some tasks to original
    task1 = TaskStar(
        task_id="task1",
        name="First Task",
        description="Original task 1",
        target_device_id="device1",
    )
    task2 = TaskStar(
        task_id="task2",
        name="Second Task",
        description="Original task 2",
        target_device_id="device1",
    )

    old_constellation.add_task(task1)
    old_constellation.add_task(task2)

    # Create dependency object
    from galaxy.constellation import TaskStarLine

    dep1 = TaskStarLine(
        from_task_id=task1.task_id,
        to_task_id=task2.task_id,
        condition_description="task1 must complete before task2",
    )
    old_constellation.add_dependency(dep1)

    console.print(
        f"Original constellation: {old_constellation.task_count} tasks, {len(old_constellation.dependencies)} dependencies\n"
    )

    # Create modified constellation
    console.print("[cyan]Creating modified constellation...[/cyan]")
    new_constellation = TaskConstellation("test-constellation", "Test Constellation")

    # Copy existing tasks
    new_constellation.add_task(task1)
    new_constellation.add_task(task2)
    new_constellation.add_dependency(dep1)

    # Add new tasks
    task3 = TaskStar(
        task_id="task3",
        name="Third Task",
        description="Newly added task",
        target_device_id="device2",
    )
    task4 = TaskStar(
        task_id="task4",
        name="Fourth Task",
        description="Another new task",
        target_device_id="device2",
    )

    new_constellation.add_task(task3)
    new_constellation.add_task(task4)

    # Add new dependencies
    dep2 = TaskStarLine(
        from_task_id=task2.task_id,
        to_task_id=task3.task_id,
        condition_description="task2 enables task3",
    )
    dep3 = TaskStarLine(
        from_task_id=task3.task_id,
        to_task_id=task4.task_id,
        condition_description="task3 must complete before task4",
    )
    new_constellation.add_dependency(dep2)
    new_constellation.add_dependency(dep3)

    # Modify existing task (simulated by changing description)
    task1.description = "Modified task 1 description"

    console.print(
        f"Modified constellation: {new_constellation.task_count} tasks, {len(new_constellation.dependencies)} dependencies\n"
    )

    # Test 1: Constellation modification with automatic comparison
    console.print(
        "[yellow]Test 1: Constellation modification with old/new comparison[/yellow]"
    )

    event = ConstellationEvent(
        event_type=EventType.CONSTELLATION_MODIFIED,
        source_id="test_system",
        timestamp=datetime.now().timestamp(),
        data={
            "old_constellation": old_constellation,
            "new_constellation": new_constellation,
        },
        constellation_id="test-constellation",
        constellation_state="modified",
    )

    await observer.on_event(event)

    console.print("\n" + "=" * 80 + "\n")

    # Test 2: New constellation (no old constellation for comparison)
    console.print(
        "[yellow]Test 2: New constellation creation (no old constellation)[/yellow]"
    )

    brand_new_constellation = TaskConstellation("brand-new", "Brand New Constellation")
    brand_new_constellation.add_task(
        TaskStar("new_task", "New Task", "A completely new task")
    )

    event2 = ConstellationEvent(
        event_type=EventType.CONSTELLATION_MODIFIED,
        source_id="test_system",
        timestamp=datetime.now().timestamp(),
        data={"new_constellation": brand_new_constellation},
        constellation_id="brand-new",
        constellation_state="created",
    )

    await observer.on_event(event2)

    console.print("\n" + "=" * 80 + "\n")

    # Test 3: Task removal scenario
    console.print("[yellow]Test 3: Task removal scenario[/yellow]")

    # Create constellation with tasks removed
    removed_constellation = TaskConstellation(
        "test-constellation", "Test Constellation"
    )
    removed_constellation.add_task(task1)  # Only keep task1, remove task2

    event3 = ConstellationEvent(
        event_type=EventType.CONSTELLATION_MODIFIED,
        source_id="test_system",
        timestamp=datetime.now().timestamp(),
        data={
            "old_constellation": old_constellation,
            "new_constellation": removed_constellation,
        },
        constellation_id="test-constellation",
        constellation_state="modified",
    )

    await observer.on_event(event3)

    console.print("\n[green]✅ All constellation comparison tests completed![/green]")


if __name__ == "__main__":
    asyncio.run(test_constellation_comparison())
