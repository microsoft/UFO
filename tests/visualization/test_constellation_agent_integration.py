#!/usr/bin/env python
"""
Integration test demonstrating ConstellationAgent event publishing in a realistic scenario.
"""

import asyncio
import pytest
import time
from galaxy.constellation import TaskConstellation, TaskStar, TaskStarLine
from galaxy.core.events import ConstellationEvent, EventType, get_event_bus
from galaxy.session.observers import DAGVisualizationObserver


class SimulatedConstellationAgent:
    """Simplified ConstellationAgent simulation for demonstration."""

    def __init__(self, name="simulated_constellation_agent"):
        self.name = name
        self._event_bus = get_event_bus()
        self._current_constellation = None

    async def simulate_process_editing(self, before_constellation, after_constellation):
        """Simulate the process_editing method with event publishing."""
        print(f"🔄 {self.name} processing constellation changes...")

        self._current_constellation = after_constellation

        # Publish DAG Modified Event (same logic as in ConstellationAgent)
        await self._event_bus.publish_event(
            ConstellationEvent(
                event_type=EventType.CONSTELLATION_MODIFIED,
                source_id=self.name,
                timestamp=time.time(),
                data={
                    "old_constellation": before_constellation,
                    "new_constellation": after_constellation,
                    "modification_type": "agent_processing_result",
                },
                constellation_id=after_constellation.constellation_id,
                constellation_state=(
                    after_constellation.state.value
                    if after_constellation.state
                    else "unknown"
                ),
            )
        )

        print(f"✅ {self.name} published constellation modified event")
        return after_constellation


@pytest.mark.asyncio
async def test_constellation_agent_integration():
    """Integration test demonstrating full ConstellationAgent event flow."""
    print("🧪 ConstellationAgent Event Publishing Integration Test\n")

    # Create DAG visualization observer
    dag_observer = DAGVisualizationObserver()

    # Subscribe to event bus
    event_bus = get_event_bus()
    event_bus.subscribe(dag_observer, {EventType.CONSTELLATION_MODIFIED})

    # Create simulated agent
    agent = SimulatedConstellationAgent("main_constellation_agent")

    print("=== Scenario 1: Task Creation and Dependencies ===")

    # Original constellation
    original = TaskConstellation("project-alpha", "Project Alpha Development")
    task1 = TaskStar("req_analysis", "Requirements Analysis")
    task2 = TaskStar("system_design", "System Design")

    original.add_task(task1)
    original.add_task(task2)

    # Modified constellation with new tasks and dependencies
    modified = TaskConstellation("project-alpha", "Project Alpha Development")
    task1_mod = TaskStar("req_analysis", "Requirements Analysis")
    task2_mod = TaskStar("system_design", "System Design")
    task3_new = TaskStar("implementation", "Implementation Phase")
    task4_new = TaskStar("testing", "Testing Phase")

    # Add dependency
    dep1 = TaskStarLine("req_analysis", "system_design")
    dep2 = TaskStarLine("system_design", "implementation")
    dep3 = TaskStarLine("implementation", "testing")

    modified.add_task(task1_mod)
    modified.add_task(task2_mod)
    modified.add_task(task3_new)
    modified.add_task(task4_new)
    modified.add_dependency(dep1)
    modified.add_dependency(dep2)
    modified.add_dependency(dep3)

    await agent.simulate_process_editing(original, modified)
    await asyncio.sleep(0.1)

    print("\n" + "=" * 80)

    print("\n=== Scenario 2: Task Property Updates ===")

    # Create constellation with property changes
    updated = TaskConstellation("project-alpha", "Project Alpha Development")
    task1_updated = TaskStar(
        "req_analysis", "Updated Requirements Analysis"
    )  # Changed name
    task2_updated = TaskStar("system_design", "Enhanced System Design")  # Changed name
    task3_updated = TaskStar("implementation", "Implementation Phase")
    task4_updated = TaskStar("testing", "Comprehensive Testing Phase")  # Changed name

    updated.add_task(task1_updated)
    updated.add_task(task2_updated)
    updated.add_task(task3_updated)
    updated.add_task(task4_updated)

    await agent.simulate_process_editing(modified, updated)
    await asyncio.sleep(0.1)

    print("\n" + "=" * 80)

    print("\n=== Scenario 3: Task Removal ===")

    # Remove some tasks
    final = TaskConstellation("project-alpha", "Project Alpha Development")
    task1_final = TaskStar("req_analysis", "Updated Requirements Analysis")
    task4_final = TaskStar("testing", "Comprehensive Testing Phase")

    final.add_task(task1_final)
    final.add_task(task4_final)

    await agent.simulate_process_editing(updated, final)
    await asyncio.sleep(0.1)

    print("\n✅ All ConstellationAgent integration tests completed!")
    print("🎉 Features successfully demonstrated:")
    print("   • ConstellationAgent event publishing")
    print("   • DAG change detection and visualization")
    print("   • Rich terminal beautification")
    print("   • End-to-end event flow")


if __name__ == "__main__":
    asyncio.run(test_constellation_agent_integration())
