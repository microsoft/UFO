#!/usr/bin/env python3
"""
Debug script for constellation modification event handling.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath("."))

from galaxy.constellation import TaskConstellation, TaskStar, TaskStarLine
from galaxy.core.events import ConstellationEvent, EventType
from galaxy.session.observers import DAGVisualizationObserver
from rich.console import Console


async def test_constellation_modified_handling():
    """Test constellation modified event handling with debug output."""

    console = Console()
    console.print(
        "[bold blue]🔍 Testing Constellation Modified Event Handling[/bold blue]\n"
    )

    # Initialize observer with explicit console
    observer = DAGVisualizationObserver(enable_visualization=True, console=console)

    # Create old constellation
    old_constellation = TaskConstellation("test", "Test Constellation")
    task1 = TaskStar("task1", "Task 1", "First task")
    old_constellation.add_task(task1)

    # Create new constellation with modifications
    new_constellation = TaskConstellation("test", "Test Constellation")
    new_constellation.add_task(task1)
    task2 = TaskStar("task2", "Task 2", "Second task")
    new_constellation.add_task(task2)

    # Add dependency
    dep = TaskStarLine(
        from_task_id="task1",
        to_task_id="task2",
        condition_description="Task1 must complete before Task2",
    )
    new_constellation.add_dependency(dep)

    console.print(f"Old constellation: {old_constellation.task_count} tasks")
    console.print(f"New constellation: {new_constellation.task_count} tasks")

    # Create event
    event = ConstellationEvent(
        event_type=EventType.CONSTELLATION_MODIFIED,
        source_id="test_system",
        timestamp=datetime.now().timestamp(),
        data={
            "old_constellation": old_constellation,
            "new_constellation": new_constellation,
        },
        constellation_id="test",
        constellation_state="modified",
    )

    console.print("\n[yellow]Calling observer.on_event() with debug info...[/yellow]")

    # Add some debug prints to the observer temporarily
    original_handle = observer._handle_constellation_modified

    async def debug_handle_constellation_modified(event, constellation):
        console.print(f"[cyan]DEBUG: _handle_constellation_modified called[/cyan]")
        console.print(
            f"[cyan]DEBUG: event.data = {event.data.keys() if event.data else 'None'}[/cyan]"
        )
        console.print(f"[cyan]DEBUG: constellation = {constellation}[/cyan]")
        console.print(
            f"[cyan]DEBUG: observer._visualizer = {observer._visualizer}[/cyan]"
        )

        result = await original_handle(event, constellation)
        console.print(f"[cyan]DEBUG: _handle_constellation_modified finished[/cyan]")
        return result

    observer._handle_constellation_modified = debug_handle_constellation_modified

    await observer.on_event(event)

    console.print("\n[green]✅ Event handling test completed[/green]")


if __name__ == "__main__":
    asyncio.run(test_constellation_modified_handling())
