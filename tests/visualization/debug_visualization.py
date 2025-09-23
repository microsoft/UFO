#!/usr/bin/env python3
"""
Debug visualization issues.
"""

import asyncio
from ufo.galaxy.session.observers import DAGVisualizationObserver
from ufo.galaxy.constellation.task_constellation import TaskConstellation
from ufo.galaxy.constellation.task_star import TaskStar


async def debug_visualization():
    """Debug visualization setup."""
    print("🔍 Debugging DAGVisualizationObserver...")

    # Create visualization observer
    viz_observer = DAGVisualizationObserver(enable_visualization=True)

    print(f"✅ Visualization enabled: {viz_observer.enable_visualization}")
    print(f"✅ Visualizer initialized: {viz_observer._visualizer is not None}")

    if viz_observer._visualizer:
        print(f"✅ Console available: {viz_observer._visualizer._console is not None}")

        # Test direct console output
        print("\n🎨 Testing direct Rich console output...")
        from rich.panel import Panel
        from rich.text import Text

        test_text = Text()
        test_text.append("🚀 ", style="bold green")
        test_text.append("Direct Rich Test", style="bold yellow")

        panel = Panel(
            test_text,
            title="[bold green]🧪 Rich Test Panel[/bold green]",
            border_style="green",
            width=60,
        )

        viz_observer._visualizer._console.print(panel)

        # Test constellation
        constellation = TaskConstellation("debug_test")
        task = TaskStar(
            task_id="debug_task",
            name="Debug Task",
            description="Testing visualization",
            target_device_id="device_1",
        )
        constellation.add_task(task)

        print(f"\n🔍 Testing with constellation: {constellation.constellation_id}")
        print(f"   Task count: {constellation.task_count}")

        # Test display methods directly
        print("\n📊 Testing constellation overview...")
        viz_observer._visualizer.display_constellation_overview(
            constellation, "🧪 Debug Test"
        )

    else:
        print("❌ Visualizer not initialized - checking why...")
        try:
            from ufo.galaxy.visualization.dag_visualizer import DAGVisualizer

            print("✅ DAGVisualizer import successful")
        except ImportError as e:
            print(f"❌ DAGVisualizer import failed: {e}")


if __name__ == "__main__":
    asyncio.run(debug_visualization())
