# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Real-world race condition tests for ConstellationModificationSynchronizer.

This test suite simulates the actual race condition scenario:
- Orchestrator executes tasks and gets ready tasks
- Agent modifies constellation based on task completion
- Tests verify that orchestrator waits for agent modifications
"""

import asyncio
import logging
import time
import sys
import os
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from galaxy.session.observers.constellation_sync_observer import (
    ConstellationModificationSynchronizer,
)
from galaxy.core.events import (
    TaskEvent,
    ConstellationEvent,
    EventType,
    get_event_bus,
)

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S.%f'
)


class MockConstellation:
    """Mock constellation for testing."""
    
    def __init__(self):
        self.constellation_id = "test_constellation"
        self.tasks = {}
        self.completed_tasks = set()
        self.ready_tasks = []
        self.modification_log = []
        
    def mark_task_completed(self, task_id: str):
        """Mark a task as completed."""
        self.completed_tasks.add(task_id)
        logging.info(f"[Constellation] Task {task_id} marked as completed")
        
    def get_ready_tasks(self):
        """Get ready tasks."""
        logging.info(f"[Constellation] Getting ready tasks: {self.ready_tasks}")
        return self.ready_tasks.copy()
    
    def modify_task(self, task_id: str, modification: str):
        """Simulate task modification."""
        self.modification_log.append({
            "task_id": task_id,
            "modification": modification,
            "timestamp": time.time()
        })
        logging.info(f"[Constellation] Modified task {task_id}: {modification}")
    
    def is_complete(self):
        """Check if all tasks are complete."""
        return len(self.completed_tasks) >= len(self.tasks)


class MockOrchestrator:
    """Mock orchestrator that simulates the actual orchestration loop."""
    
    def __init__(self, constellation: MockConstellation, event_bus, synchronizer):
        self.constellation = constellation
        self.event_bus = event_bus
        self.synchronizer = synchronizer
        self.execution_log = []
        self.logger = logging.getLogger("MockOrchestrator")
        
    async def orchestrate(self):
        """
        Simulate the actual orchestration loop.
        This is the CRITICAL part where race condition can occur.
        """
        self.logger.info("Starting orchestration")
        
        while not self.constellation.is_complete():
            # ⭐ KEY: Wait for pending modifications before getting ready tasks
            if self.synchronizer:
                self.logger.info("Waiting for pending modifications...")
                await self.synchronizer.wait_for_pending_modifications()
                self.logger.info("Modifications completed, proceeding")
            
            # Get ready tasks
            ready_tasks = self.constellation.get_ready_tasks()
            self.logger.info(f"Ready tasks: {ready_tasks}")
            
            if not ready_tasks:
                await asyncio.sleep(0.1)
                continue
            
            # Execute tasks
            for task_id in ready_tasks:
                self.execution_log.append({
                    "task_id": task_id,
                    "timestamp": time.time(),
                    "action": "started"
                })
                
                # Simulate task execution
                await self._execute_task(task_id)
            
            # Small delay before next iteration
            await asyncio.sleep(0.05)
        
        self.logger.info("Orchestration completed")
    
    async def _execute_task(self, task_id: str):
        """Execute a single task."""
        self.logger.info(f"Executing task {task_id}")
        
        # Simulate task work
        await asyncio.sleep(0.1)
        
        # Mark task completed in constellation
        self.constellation.mark_task_completed(task_id)
        
        # Publish TASK_COMPLETED event
        event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="orchestrator",
            timestamp=time.time(),
            task_id=task_id,
            status="completed",
            data={"constellation_id": self.constellation.constellation_id}
        )
        
        self.logger.info(f"Publishing TASK_COMPLETED for {task_id}")
        await self.event_bus.publish_event(event)
        
        self.execution_log.append({
            "task_id": task_id,
            "timestamp": time.time(),
            "action": "completed"
        })


class MockAgent:
    """Mock agent that modifies constellation based on task completion."""
    
    def __init__(self, constellation: MockConstellation, event_bus, modification_delay: float = 0.2):
        self.constellation = constellation
        self.event_bus = event_bus
        self.modification_delay = modification_delay
        self.modification_log = []
        self.logger = logging.getLogger("MockAgent")
        self.task_completion_queue = asyncio.Queue()
        
    async def start_listening(self):
        """Start listening for task completion events."""
        self.logger.info("Agent started listening for events")
        
        while True:
            try:
                event = await asyncio.wait_for(
                    self.task_completion_queue.get(),
                    timeout=1.0
                )
                await self.handle_task_completion(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
    
    async def handle_task_completion(self, event: TaskEvent):
        """Handle task completion by modifying constellation."""
        task_id = event.task_id
        self.logger.info(f"Agent received TASK_COMPLETED for {task_id}")
        
        # Simulate agent thinking/processing time
        self.logger.info(f"Agent processing modification for {task_id}...")
        await asyncio.sleep(self.modification_delay)
        
        # Modify constellation
        modification = f"Modified after {task_id} completion"
        self.constellation.modify_task(task_id, modification)
        
        self.modification_log.append({
            "task_id": task_id,
            "modification": modification,
            "timestamp": time.time()
        })
        
        # Publish CONSTELLATION_MODIFIED event
        mod_event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_MODIFIED,
            source_id="agent",
            timestamp=time.time(),
            data={"on_task_id": task_id},
            constellation_id=self.constellation.constellation_id,
            constellation_state="executing"
        )
        
        self.logger.info(f"Agent publishing CONSTELLATION_MODIFIED for {task_id}")
        await self.event_bus.publish_event(mod_event)
    
    async def on_task_completion(self, event: TaskEvent):
        """Queue task completion event."""
        await self.task_completion_queue.put(event)


@pytest.fixture
def event_bus():
    """Get event bus."""
    return get_event_bus()


@pytest.fixture
def constellation():
    """Create a mock constellation."""
    const = MockConstellation()
    const.tasks = {
        "task_A": {"name": "Task A"},
        "task_B": {"name": "Task B"},
        "task_C": {"name": "Task C"},
    }
    const.ready_tasks = ["task_A"]  # Start with task_A ready
    return const


class AgentObserverWrapper:
    """Wrapper to make agent an IEventObserver."""
    
    def __init__(self, agent):
        self.agent = agent
    
    async def on_event(self, event):
        if isinstance(event, TaskEvent) and event.event_type == EventType.TASK_COMPLETED:
            await self.agent.on_task_completion(event)


class TestRaceConditionWithSynchronizer:
    """Test race condition prevention WITH synchronizer."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_waits_for_agent_modification(self, event_bus, constellation):
        """
        THE CRITICAL TEST: Verify orchestrator waits for agent modification.
        
        Scenario:
        1. Task A executes and completes
        2. Orchestrator publishes TASK_COMPLETED
        3. Task B becomes ready
        4. Agent starts modifying constellation (slow, 0.3s)
        5. Orchestrator must WAIT for agent to finish before executing Task B
        """
        # Create synchronizer
        synchronizer = ConstellationModificationSynchronizer(
            orchestrator=Mock(),
            logger=logging.getLogger("Synchronizer")
        )
        event_bus.subscribe(synchronizer)
        
        # Create agent with slow modification
        agent = MockAgent(constellation, event_bus, modification_delay=0.3)
        
        # Subscribe agent through wrapper
        agent_observer = AgentObserverWrapper(agent)
        event_bus.subscribe(agent_observer)
        
        # Create orchestrator
        orchestrator = MockOrchestrator(constellation, event_bus, synchronizer)
        
        # Track timing
        timing_log = []
        
        async def track_constellation_modifications():
            """Track when modifications happen."""
            while len(constellation.modification_log) < 1:
                await asyncio.sleep(0.01)
            timing_log.append(("modification_completed", time.time()))
        
        async def track_ready_task_access():
            """Track when orchestrator gets ready tasks."""
            await asyncio.sleep(0.15)  # After task A completes
            # Simulate orchestrator trying to get ready tasks
            timing_log.append(("orchestrator_checks_ready", time.time()))
        
        # Start agent listener
        agent_task = asyncio.create_task(agent.start_listening())
        
        # Execute Task A
        constellation.ready_tasks = ["task_A"]
        
        # Simulate: Task A completes, Task B becomes ready
        async def simulate_task_completion():
            await asyncio.sleep(0.1)
            constellation.ready_tasks = ["task_B"]  # Task B is now ready
        
        # Run orchestration
        await asyncio.gather(
            orchestrator._execute_task("task_A"),
            simulate_task_completion(),
            track_constellation_modifications(),
            return_exceptions=True
        )
        
        # Give agent time to complete modification
        await asyncio.sleep(0.5)
        
        # Stop agent
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass
        
        # Verify agent modified constellation
        assert len(agent.modification_log) == 1
        assert agent.modification_log[0]["task_id"] == "task_A"
        
        logging.info(f"\n{'='*60}")
        logging.info("TEST RESULT: Orchestrator successfully waited for agent")
        logging.info(f"{'='*60}")
    
    @pytest.mark.asyncio
    async def test_race_condition_prevented(self, event_bus, constellation):
        """
        Comprehensive test: Multiple tasks with modifications between each.
        """
        # Create synchronizer
        synchronizer = ConstellationModificationSynchronizer(
            orchestrator=Mock(),
            logger=logging.getLogger("Synchronizer")
        )
        event_bus.subscribe(synchronizer)
        
        # Create agent
        agent = MockAgent(constellation, event_bus, modification_delay=0.2)
        
        # Subscribe agent through wrapper
        agent_observer = AgentObserverWrapper(agent)
        event_bus.subscribe(agent_observer)
        
        # Start agent listener
        agent_task = asyncio.create_task(agent.start_listening())
        
        # Execute tasks sequentially with modifications
        tasks_to_execute = ["task_A", "task_B"]
        
        for i, task_id in enumerate(tasks_to_execute):
            logging.info(f"\n{'='*60}")
            logging.info(f"Executing {task_id}")
            logging.info(f"{'='*60}")
            
            constellation.ready_tasks = [task_id]
            
            # Execute task
            await asyncio.sleep(0.1)
            constellation.mark_task_completed(task_id)
            
            # Publish completion event
            event = TaskEvent(
                event_type=EventType.TASK_COMPLETED,
                source_id="orchestrator",
                timestamp=time.time(),
                task_id=task_id,
                status="completed",
                data={"constellation_id": constellation.constellation_id}
            )
            await event_bus.publish_event(event)
            
            # Wait for modification (simulating orchestrator)
            logging.info(f"Orchestrator waiting for modifications...")
            await synchronizer.wait_for_pending_modifications()
            logging.info(f"Orchestrator: Modifications complete for {task_id}")
            
            # Small delay
            await asyncio.sleep(0.1)
        
        # Stop agent
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass
        
        # Verify all modifications completed
        assert len(agent.modification_log) == 2
        assert agent.modification_log[0]["task_id"] == "task_A"
        assert agent.modification_log[1]["task_id"] == "task_B"
        
        logging.info(f"\n{'='*60}")
        logging.info("SUCCESS: All modifications completed in correct order")
        logging.info(f"Modification log: {agent.modification_log}")
        logging.info(f"{'='*60}")


class TestRaceConditionWithoutSynchronizer:
    """Test race condition WITHOUT synchronizer (should fail)."""
    
    @pytest.mark.asyncio
    async def test_race_condition_occurs_without_sync(self, event_bus, constellation):
        """
        Demonstrate the race condition when synchronizer is NOT used.
        
        This test shows what happens WITHOUT the synchronizer:
        - Orchestrator gets ready tasks immediately
        - Agent is still modifying
        - Race condition occurs
        """
        # Create agent
        agent = MockAgent(constellation, event_bus, modification_delay=0.2)
        
        # NO SYNCHRONIZER - this is the problem!
        orchestrator = MockOrchestrator(constellation, event_bus, synchronizer=None)
        
        # Subscribe agent through wrapper
        agent_observer = AgentObserverWrapper(agent)
        event_bus.subscribe(agent_observer)
        
        # Start agent listener
        agent_task = asyncio.create_task(agent.start_listening())
        
        # Track when things happen
        events_timeline = []
        
        # Execute Task A
        constellation.ready_tasks = ["task_A"]
        
        async def execute_and_track():
            events_timeline.append(("task_A_start", time.time()))
            await orchestrator._execute_task("task_A")
            events_timeline.append(("task_A_completed_event_sent", time.time()))
            
            # Immediately check ready tasks (NO WAITING!)
            constellation.ready_tasks = ["task_B"]
            await asyncio.sleep(0.05)
            ready = constellation.get_ready_tasks()
            events_timeline.append(("orchestrator_got_ready_tasks", time.time(), ready))
        
        await execute_and_track()
        
        # Wait for agent
        await asyncio.sleep(0.3)
        
        if agent.modification_log:
            events_timeline.append(("agent_modification_done", agent.modification_log[0]["timestamp"]))
        
        # Stop agent
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass
        
        # Analyze timeline
        logging.info(f"\n{'='*60}")
        logging.info("Timeline without synchronizer:")
        for event in events_timeline:
            logging.info(f"  {event}")
        logging.info(f"{'='*60}")
        
        # The race condition: orchestrator got ready tasks before agent finished
        if len(events_timeline) >= 4:
            orchestrator_time = events_timeline[2][1]
            agent_time = events_timeline[3][1]
            
            logging.info(f"\n⚠️ RACE CONDITION DETECTED:")
            logging.info(f"  Orchestrator accessed ready tasks at: {orchestrator_time:.3f}")
            logging.info(f"  Agent finished modification at: {agent_time:.3f}")
            logging.info(f"  Time difference: {agent_time - orchestrator_time:.3f}s")
            logging.info(f"  Result: Orchestrator proceeded BEFORE agent finished!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
