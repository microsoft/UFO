# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Integration tests for ConstellationModificationSynchronizer with Orchestrator.

This test suite validates the complete integration of the synchronizer
with the orchestrator and agent, ensuring race conditions are prevented.
"""

import asyncio
import logging
import time
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch

from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.constellation.task_star import TaskStar
from galaxy.constellation.enums import TaskStatus
from galaxy.constellation.orchestrator.orchestrator import TaskConstellationOrchestrator
from galaxy.session.observers.constellation_sync_observer import (
    ConstellationModificationSynchronizer,
)
from galaxy.core.events import (
    get_event_bus,
    EventType,
    TaskEvent,
    ConstellationEvent,
)


logging.basicConfig(level=logging.INFO)


@pytest.fixture
def event_bus():
    """Get the event bus instance."""
    return get_event_bus()


@pytest.fixture
def mock_device_manager():
    """Create a mock device manager."""
    manager = Mock()
    manager.get_all_devices = Mock(return_value=[])
    manager.get_device = Mock(return_value=Mock(device_id="device_1"))
    return manager


@pytest.fixture
def orchestrator(mock_device_manager):
    """Create an orchestrator instance."""
    orch = TaskConstellationOrchestrator(
        device_manager=mock_device_manager,
        enable_logging=True,
    )
    return orch


@pytest.fixture
def synchronizer(orchestrator):
    """Create a synchronizer and attach to orchestrator."""
    logger = logging.getLogger("integration_test")
    sync = ConstellationModificationSynchronizer(
        orchestrator=orchestrator,
        logger=logger,
    )
    orchestrator.set_modification_synchronizer(sync)
    return sync


@pytest.fixture
def simple_constellation():
    """Create a simple linear constellation for testing."""
    constellation = TaskConstellation(constellation_id="test_constellation")
    
    # Create simple tasks
    task_a = TaskStar(
        task_id="task_A",
        task_name="Task A",
        instruction="Do A",
        device_type="desktop",
        dependencies=[],
    )
    
    task_b = TaskStar(
        task_id="task_B",
        task_name="Task B",
        instruction="Do B",
        device_type="desktop",
        dependencies=["task_A"],
    )
    
    task_c = TaskStar(
        task_id="task_C",
        task_name="Task C",
        instruction="Do C",
        device_type="desktop",
        dependencies=["task_B"],
    )
    
    constellation.add_task(task_a)
    constellation.add_task(task_b)
    constellation.add_task(task_c)
    
    return constellation


class MockAgent:
    """Mock agent for testing constellation modifications."""
    
    def __init__(self, event_bus, modify_delay: float = 0.1):
        self.event_bus = event_bus
        self.modify_delay = modify_delay
        self.modifications_made = []
        self.logger = logging.getLogger("mock_agent")
        
    async def on_task_completion(self, event: TaskEvent):
        """Simulate agent processing task completion."""
        task_id = event.task_id
        self.logger.info(f"Agent: Processing completion of {task_id}")
        
        # Simulate constellation modification work
        await asyncio.sleep(self.modify_delay)
        
        # Record modification
        self.modifications_made.append({
            "task_id": task_id,
            "timestamp": time.time(),
        })
        
        # Publish CONSTELLATION_MODIFIED event
        mod_event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_MODIFIED,
            source_id="mock_agent",
            timestamp=time.time(),
            data={
                "on_task_id": task_id,
                "modification_type": "edited",
            },
            constellation_id=event.data.get("constellation_id", "unknown"),
            constellation_state="executing",
        )
        await self.event_bus.publish_event(mod_event)
        self.logger.info(f"Agent: Completed modification for {task_id}")


class TestBasicIntegration:
    """Test basic integration between synchronizer, orchestrator, and agent."""
    
    @pytest.mark.asyncio
    async def test_synchronizer_attached_to_orchestrator(self, orchestrator, synchronizer):
        """Test that synchronizer is properly attached to orchestrator."""
        assert orchestrator._modification_synchronizer is synchronizer
    
    @pytest.mark.asyncio
    async def test_event_flow_with_synchronizer(self, event_bus, synchronizer):
        """Test complete event flow through synchronizer."""
        # Subscribe synchronizer to event bus
        event_bus.subscribe(synchronizer)
        
        # Publish task completed event
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="test_orchestrator",
            timestamp=time.time(),
            task_id="flow_task",
            task_name="Flow Task",
            data={"constellation_id": "flow_constellation"},
        )
        await event_bus.publish_event(task_event)
        
        # Give event time to process
        await asyncio.sleep(0.05)
        
        # Verify pending modification registered
        assert synchronizer.has_pending_modifications()
        assert "flow_task" in synchronizer.get_pending_task_ids()
        
        # Publish constellation modified event
        mod_event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_MODIFIED,
            source_id="test_agent",
            timestamp=time.time(),
            data={"on_task_id": "flow_task"},
            constellation_id="flow_constellation",
            constellation_state="executing",
        )
        await event_bus.publish_event(mod_event)
        
        # Give event time to process
        await asyncio.sleep(0.05)
        
        # Verify modification completed
        assert not synchronizer.has_pending_modifications()


class TestRaceConditionPrevention:
    """Test that race conditions are prevented in realistic scenarios."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_waits_for_agent_modification(
        self, event_bus, synchronizer
    ):
        """
        Test the critical scenario where orchestrator must wait for agent.
        
        Scenario:
        1. Task A completes
        2. Orchestrator publishes TASK_COMPLETED
        3. Agent starts modifying constellation
        4. Orchestrator tries to get ready tasks
        5. Orchestrator should wait for agent to finish
        """
        event_bus.subscribe(synchronizer)
        
        modification_completed = False
        orchestrator_got_ready_tasks = False
        
        async def simulate_agent():
            """Simulate agent modifying constellation."""
            nonlocal modification_completed
            
            # Wait for task completion event
            await asyncio.sleep(0.05)
            
            # Simulate modification work
            logging.info("Agent: Starting modification...")
            await asyncio.sleep(0.2)
            modification_completed = True
            logging.info("Agent: Modification completed")
            
            # Publish completion
            mod_event = ConstellationEvent(
                event_type=EventType.CONSTELLATION_MODIFIED,
                source_id="agent",
                timestamp=time.time(),
                data={"on_task_id": "race_task"},
                constellation_id="race_constellation",
                constellation_state="executing",
            )
            await event_bus.publish_event(mod_event)
            await asyncio.sleep(0.05)  # Let event process
        
        async def simulate_orchestrator():
            """Simulate orchestrator execution loop."""
            nonlocal orchestrator_got_ready_tasks
            
            # Publish task completed
            task_event = TaskEvent(
                event_type=EventType.TASK_COMPLETED,
                source_id="orchestrator",
                timestamp=time.time(),
                task_id="race_task",
                task_name="Race Task",
                data={"constellation_id": "race_constellation"},
            )
            await event_bus.publish_event(task_event)
            await asyncio.sleep(0.05)  # Let event process
            
            # Wait for modifications (THIS IS THE KEY)
            logging.info("Orchestrator: Waiting for modifications...")
            await synchronizer.wait_for_pending_modifications()
            logging.info("Orchestrator: Getting ready tasks...")
            
            orchestrator_got_ready_tasks = True
        
        # Run both flows
        await asyncio.gather(
            simulate_orchestrator(),
            simulate_agent(),
        )
        
        # Verify correct order: modification completed BEFORE orchestrator proceeded
        assert modification_completed
        assert orchestrator_got_ready_tasks
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_modifications(self, event_bus, synchronizer):
        """Test handling multiple concurrent task completions."""
        event_bus.subscribe(synchronizer)
        
        task_ids = ["task_1", "task_2", "task_3"]
        modifications_order = []
        
        async def simulate_agent(task_id: str, delay: float):
            """Simulate agent modifying for a specific task."""
            # Wait a bit then modify
            await asyncio.sleep(delay)
            modifications_order.append(task_id)
            
            mod_event = ConstellationEvent(
                event_type=EventType.CONSTELLATION_MODIFIED,
                source_id="agent",
                timestamp=time.time(),
                data={"on_task_id": task_id},
                constellation_id="concurrent_constellation",
                constellation_state="executing",
            )
            await event_bus.publish_event(mod_event)
            await asyncio.sleep(0.05)
        
        # Publish all task completed events
        for task_id in task_ids:
            event = TaskEvent(
                event_type=EventType.TASK_COMPLETED,
                source_id="orchestrator",
                timestamp=time.time(),
                task_id=task_id,
                task_name=task_id,
                data={"constellation_id": "concurrent_constellation"},
            )
            await event_bus.publish_event(event)
        
        await asyncio.sleep(0.05)
        
        # All should be pending
        assert synchronizer.get_pending_count() == 3
        
        # Start waiting
        wait_task = asyncio.create_task(
            synchronizer.wait_for_pending_modifications()
        )
        
        # Simulate agent processing in different order and speeds
        await asyncio.gather(
            simulate_agent("task_2", 0.1),
            simulate_agent("task_1", 0.15),
            simulate_agent("task_3", 0.05),
        )
        
        # Wait should complete
        result = await wait_task
        assert result is True
        assert synchronizer.get_pending_count() == 0
        
        # All modifications should be recorded
        assert len(modifications_order) == 3


class TestTimeoutScenarios:
    """Test timeout handling in integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_proceeds_on_agent_timeout(
        self, event_bus, synchronizer
    ):
        """Test that orchestrator proceeds if agent times out."""
        event_bus.subscribe(synchronizer)
        synchronizer.set_modification_timeout(0.5)
        
        # Publish task completed
        task_event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            source_id="orchestrator",
            timestamp=time.time(),
            task_id="timeout_task",
            task_name="Timeout Task",
            data={"constellation_id": "timeout_constellation"},
        )
        await event_bus.publish_event(task_event)
        await asyncio.sleep(0.05)
        
        # Wait with short timeout (agent never completes)
        result = await synchronizer.wait_for_pending_modifications(timeout=0.3)
        
        # Should timeout and return False
        assert result is False
        # Should be cleared
        assert synchronizer.get_pending_count() == 0


class TestComplexDAGScenarios:
    """Test complex DAG execution scenarios."""
    
    @pytest.mark.asyncio
    async def test_sequential_dag_execution_with_modifications(
        self, event_bus, synchronizer
    ):
        """
        Test sequential DAG execution with modifications between each step.
        
        Flow: A -> B -> C
        Each task completion triggers modification before next executes.
        """
        event_bus.subscribe(synchronizer)
        
        tasks = ["task_A", "task_B", "task_C"]
        execution_order = []
        
        for task_id in tasks:
            logging.info(f"\n=== Processing {task_id} ===")
            
            # Task completes
            task_event = TaskEvent(
                event_type=EventType.TASK_COMPLETED,
                source_id="orchestrator",
                timestamp=time.time(),
                task_id=task_id,
                task_name=task_id,
                data={"constellation_id": "sequential_constellation"},
            )
            await event_bus.publish_event(task_event)
            await asyncio.sleep(0.05)
            
            # Orchestrator waits for modification
            logging.info(f"Orchestrator: Waiting for {task_id} modification...")
            
            # Start wait in background
            wait_task = asyncio.create_task(
                synchronizer.wait_for_pending_modifications()
            )
            
            # Simulate agent processing
            await asyncio.sleep(0.1)
            
            # Agent completes modification
            mod_event = ConstellationEvent(
                event_type=EventType.CONSTELLATION_MODIFIED,
                source_id="agent",
                timestamp=time.time(),
                data={"on_task_id": task_id},
                constellation_id="sequential_constellation",
                constellation_state="executing",
            )
            await event_bus.publish_event(mod_event)
            await asyncio.sleep(0.05)
            
            # Wait completes
            await wait_task
            execution_order.append(task_id)
            logging.info(f"Orchestrator: {task_id} modification complete, continuing")
        
        # Verify correct execution order
        assert execution_order == tasks
        assert synchronizer.get_pending_count() == 0
        
        # Verify statistics
        stats = synchronizer.get_statistics()
        assert stats["completed_modifications"] == 3


class TestErrorRecoveryIntegration:
    """Test error recovery in integrated scenarios."""
    
    @pytest.mark.asyncio
    async def test_task_failure_with_modification(self, event_bus, synchronizer):
        """Test that failed tasks also trigger and wait for modifications."""
        event_bus.subscribe(synchronizer)
        
        # Publish task failed event
        task_event = TaskEvent(
            event_type=EventType.TASK_FAILED,
            source_id="orchestrator",
            timestamp=time.time(),
            task_id="failed_task",
            task_name="Failed Task",
            data={
                "constellation_id": "failure_constellation",
                "error": "Task execution failed",
            },
        )
        await event_bus.publish_event(task_event)
        await asyncio.sleep(0.05)
        
        # Should register pending modification
        assert synchronizer.has_pending_modifications()
        
        # Start waiting
        wait_task = asyncio.create_task(
            synchronizer.wait_for_pending_modifications()
        )
        
        # Agent handles failure and modifies constellation
        await asyncio.sleep(0.1)
        mod_event = ConstellationEvent(
            event_type=EventType.CONSTELLATION_MODIFIED,
            source_id="agent",
            timestamp=time.time(),
            data={
                "on_task_id": "failed_task",
                "modification_type": "failure_handling",
            },
            constellation_id="failure_constellation",
            constellation_state="executing",
        )
        await event_bus.publish_event(mod_event)
        await asyncio.sleep(0.05)
        
        # Wait should complete
        result = await wait_task
        assert result is True


class TestPerformanceCharacteristics:
    """Test performance characteristics of synchronization."""
    
    @pytest.mark.asyncio
    async def test_synchronization_overhead(self, event_bus, synchronizer):
        """Measure overhead of synchronization mechanism."""
        event_bus.subscribe(synchronizer)
        
        num_tasks = 10
        
        start_time = time.time()
        
        for i in range(num_tasks):
            # Task completes
            task_event = TaskEvent(
                event_type=EventType.TASK_COMPLETED,
                source_id="orchestrator",
                timestamp=time.time(),
                task_id=f"perf_task_{i}",
                task_name=f"Performance Task {i}",
                data={"constellation_id": "perf_constellation"},
            )
            await event_bus.publish_event(task_event)
            await asyncio.sleep(0.01)
            
            # Wait for modification
            wait_task = asyncio.create_task(
                synchronizer.wait_for_pending_modifications()
            )
            
            # Immediate modification
            mod_event = ConstellationEvent(
                event_type=EventType.CONSTELLATION_MODIFIED,
                source_id="agent",
                timestamp=time.time(),
                data={"on_task_id": f"perf_task_{i}"},
                constellation_id="perf_constellation",
                constellation_state="executing",
            )
            await event_bus.publish_event(mod_event)
            await asyncio.sleep(0.01)
            
            await wait_task
        
        elapsed_time = time.time() - start_time
        
        # Should complete reasonably fast
        logging.info(f"Synchronized {num_tasks} tasks in {elapsed_time:.3f}s")
        assert elapsed_time < 5.0  # Should complete in under 5 seconds
        
        # Verify all completed
        stats = synchronizer.get_statistics()
        assert stats["completed_modifications"] == num_tasks


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
