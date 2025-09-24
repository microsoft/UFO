#!/usr/bin/env python3
"""
Test script for ConstellationAgent queue methods.
"""

import asyncio
import time
from ufo.galaxy.agents.constellation_agent import ConstellationAgent
from ufo.galaxy.constellation.orchestrator.orchestrator import (
    TaskConstellationOrchestrator,
)
from ufo.galaxy.core.events import TaskEvent, ConstellationEvent, EventType


async def test_constellation_agent_queues():
    """
    Test the add_task_event and add_constellation_event methods.
    """
    # Create a mock orchestrator (you might need to adjust this based on actual implementation)
    orchestrator = None  # For now, we'll test with None

    # Create ConstellationAgent instance
    agent = ConstellationAgent(orchestrator=orchestrator, name="test_agent")

    # Test 1: Valid TaskEvent
    print("Test 1: Adding valid TaskEvent...")
    task_event = TaskEvent(
        event_type=EventType.TASK_COMPLETED,
        source_id="test_source",
        timestamp=time.time(),
        data={"result": "success"},
        task_id="task_001",
        status="completed",
        result="Task completed successfully",
    )

    try:
        await agent.add_task_event(task_event)
        print("✅ Successfully added TaskEvent")
    except Exception as e:
        print(f"❌ Failed to add TaskEvent: {e}")

    # Test 2: Invalid event type for task queue
    print("\nTest 2: Adding invalid event type to task queue...")
    constellation_event = ConstellationEvent(
        event_type=EventType.CONSTELLATION_COMPLETED,
        source_id="test_source",
        timestamp=time.time(),
        data={"status": "completed"},
        constellation_id="const_001",
        constellation_state="completed",
    )

    try:
        await agent.add_task_event(constellation_event)
        print("❌ Should have failed but didn't")
    except TypeError as e:
        print(f"✅ Correctly rejected invalid type: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Test 3: Valid ConstellationEvent
    print("\nTest 3: Adding valid ConstellationEvent...")
    try:
        await agent.add_constellation_event(constellation_event)
        print("✅ Successfully added ConstellationEvent")
    except Exception as e:
        print(f"❌ Failed to add ConstellationEvent: {e}")

    # Test 4: Invalid event type for constellation queue
    print("\nTest 4: Adding invalid event type to constellation queue...")
    try:
        await agent.add_constellation_event(task_event)
        print("❌ Should have failed but didn't")
    except TypeError as e:
        print(f"✅ Correctly rejected invalid type: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Test 5: Adding wrong type (string) to task queue
    print("\nTest 5: Adding string to task queue...")
    try:
        await agent.add_task_event("not_an_event")
        print("❌ Should have failed but didn't")
    except TypeError as e:
        print(f"✅ Correctly rejected string: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_constellation_agent_queues())
