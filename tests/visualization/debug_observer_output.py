#!/usr/bin/env python3
"""
Debug script to test constellation comparison visualization output.
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


async def test_observer_output():
    """Test that the observer actually produces visible output."""

    console = Console()
    console.print("[bold blue]🔍 Testing Observer Visualization Output[/bold blue]\n")

    # Initialize observer with explicit console
    observer = DAGVisualizationObserver(enable_visualization=True, console=console)

    console.print("[cyan]Checking observer initialization...[/cyan]")
    console.print(f"Observer enabled: {observer.enable_visualization}")
    console.print(f"Observer visualizer: {observer._visualizer}")

    if observer._visualizer:
        console.print(f"Visualizer console: {observer._visualizer.console}")

        # Test direct visualizer call
        console.print("\n[yellow]Testing direct visualizer call...[/yellow]")

        # Create simple constellation for testing
        test_constellation = TaskConstellation("test", "Test Constellation")
        test_task = TaskStar("test_task", "Test Task", "A simple test task")
        test_constellation.add_task(test_task)

        observer._visualizer.display_constellation_overview(
            test_constellation, "Direct Test"
        )

        console.print("\n[green]✅ Direct visualizer test completed[/green]")

        # Test through observer event
        console.print("\n[yellow]Testing observer event handling...[/yellow]")

        event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_MODIFIED,
            source_id="test_system",
            timestamp=datetime.now().timestamp(),
            data={"new_constellation": test_constellation},
            constellation_id="test",
            constellation_state="modified",
        )

        console.print("Calling observer.on_event()...")
        await observer.on_event(event)

        console.print("\n[green]✅ Observer event test completed[/green]")
    else:
        console.print("[red]❌ Visualizer not initialized[/red]")


if __name__ == "__main__":
    asyncio.run(test_observer_output())
