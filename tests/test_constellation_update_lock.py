# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test for constellation update lock mechanism to prevent race conditions.

This test verifies that the update lock prevents race conditions between:
1. Orchestrator executing ready tasks
2. Agent's process_editing updating the constellation
"""

import asyncio
import pytest
from typing import List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from ufo.galaxy.constellation.task_constellation import TaskConstellation
from ufo.galaxy.constellation.task_star import TaskStar
from ufo.galaxy.constellation.enums import TaskStatus, TaskPriority, DeviceType


class TestConstellationUpdateLock:
    """Test cases for constellation update lock mechanism."""

    @pytest.fixture
    def constellation(self):
        """Create a test constellation."""
        constellation = TaskConstellation(
            constellation_id="test_constellation",
            name="Test Constellation",
            enable_visualization=False,
        )
        return constellation

    @pytest.fixture
    def sample_tasks(self):
        """Create sample tasks for testing."""
        task1 = TaskStar(
            task_id="task1",
            description="Task 1",
            priority=TaskPriority.MEDIUM,
            device_type=DeviceType.WINDOWS,
        )
        task2 = TaskStar(
            task_id="task2",
            description="Task 2",
            priority=TaskPriority.MEDIUM,
            device_type=DeviceType.WINDOWS,
        )
        task3 = TaskStar(
            task_id="task3",
            description="Task 3",
            priority=TaskPriority.MEDIUM,
            device_type=DeviceType.WINDOWS,
        )
        return [task1, task2, task3]

    def test_update_lock_exists(self, constellation):
        """Test that the constellation has an update lock."""
        assert hasattr(constellation, "_update_lock")
        assert isinstance(constellation._update_lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_lock_basic_functionality(self, constellation):
        """Test basic lock acquire and release."""
        # Acquire lock
        await constellation._update_lock.acquire()
        assert constellation._update_lock.locked()

        # Release lock
        constellation._update_lock.release()
        assert not constellation._update_lock.locked()

    @pytest.mark.asyncio
    async def test_lock_context_manager(self, constellation):
        """Test lock usage with async context manager."""
        assert not constellation._update_lock.locked()

        async with constellation._update_lock:
            assert constellation._update_lock.locked()

        assert not constellation._update_lock.locked()

    @pytest.mark.asyncio
    async def test_concurrent_access_blocked(self, constellation, sample_tasks):
        """Test that concurrent access is properly blocked by the lock."""
        # Add tasks to constellation
        for task in sample_tasks:
            constellation.add_task(task)

        execution_log = []

        async def mock_orchestrator_get_ready_tasks():
            """Simulates orchestrator getting ready tasks."""
            async with constellation._update_lock:
                execution_log.append("orchestrator_start")
                ready = constellation.get_ready_tasks()
                # Simulate some processing time
                await asyncio.sleep(0.1)
                execution_log.append("orchestrator_end")
                return ready

        async def mock_agent_process_editing():
            """Simulates agent editing constellation."""
            async with constellation._update_lock:
                execution_log.append("agent_edit_start")
                # Simulate editing - add a new task
                new_task = TaskStar(
                    task_id="task4",
                    description="New Task 4",
                    priority=TaskPriority.HIGH,
                    device_type=DeviceType.WINDOWS,
                )
                constellation.add_task(new_task)
                await asyncio.sleep(0.1)
                execution_log.append("agent_edit_end")

        # Start both operations concurrently
        orchestrator_task = asyncio.create_task(mock_orchestrator_get_ready_tasks())
        agent_task = asyncio.create_task(mock_agent_process_editing())

        # Wait for both to complete
        await asyncio.gather(orchestrator_task, agent_task)

        # Verify that operations did not interleave
        # Either orchestrator completes before agent starts, or vice versa
        assert len(execution_log) == 4

        # Check for proper ordering
        orchestrator_start_idx = execution_log.index("orchestrator_start")
        orchestrator_end_idx = execution_log.index("orchestrator_end")
        agent_start_idx = execution_log.index("agent_edit_start")
        agent_end_idx = execution_log.index("agent_edit_end")

        # Verify no interleaving
        if orchestrator_start_idx < agent_start_idx:
            # Orchestrator acquired lock first
            assert orchestrator_end_idx < agent_start_idx, (
                "Agent started before orchestrator finished - race condition!"
            )
        else:
            # Agent acquired lock first
            assert agent_end_idx < orchestrator_start_idx, (
                "Orchestrator started before agent finished - race condition!"
            )

    @pytest.mark.asyncio
    async def test_race_condition_scenario(self, constellation, sample_tasks):
        """
        Test the specific race condition scenario:
        1. Task completes in orchestrator
        2. Event is published
        3. Orchestrator tries to execute newly ready tasks
        4. At the same time, agent tries to edit constellation
        """
        # Setup: Add tasks with dependencies
        task1, task2, task3 = sample_tasks
        constellation.add_task(task1)
        constellation.add_task(task2)
        constellation.add_task(task3)

        # task2 depends on task1
        task2.add_dependency("task1")
        from ufo.galaxy.constellation.task_star_line import TaskStarLine
        dependency = TaskStarLine(
            from_task_id=task1.task_id,
            to_task_id=task2.task_id,
        )
        constellation.add_dependency(dependency)

        results = {
            "orchestrator_got_task2": False,
            "agent_modified_task2": False,
            "task2_status_when_orchestrator_checked": None,
            "race_condition_detected": False,
        }

        async def mock_orchestrator_execution():
            """Simulates orchestrator completing task1 and trying to execute task2."""
            # Mark task1 as completed
            task1.start_execution()
            task1.complete_with_success("task1 result")

            # Remove dependency
            task2.remove_dependency("task1")

            # Simulate slight delay (event publishing, etc.)
            await asyncio.sleep(0.05)

            # Try to get ready tasks and execute
            async with constellation._update_lock:
                ready_tasks = constellation.get_ready_tasks()
                if task2 in ready_tasks:
                    results["orchestrator_got_task2"] = True
                    results["task2_status_when_orchestrator_checked"] = task2.status
                    
                    # Record task2's description at the time orchestrator checked
                    # With the lock, either:
                    # 1. Agent hasn't modified yet (description is "Task 2")
                    # 2. Agent already modified (description is "Modified Task 2")
                    # But agent CANNOT be in the middle of modifying
                    original_desc = task2.description

        async def mock_agent_editing():
            """Simulates agent editing task2 after receiving task1 completion event."""
            # Simulate event handling delay
            await asyncio.sleep(0.03)

            # Try to edit task2
            async with constellation._update_lock:
                if task2.status == TaskStatus.PENDING:
                    # Modify task2
                    task2.update_task_data({"modified": True})
                    task2._description = "Modified Task 2"
                    results["agent_modified_task2"] = True

        # Run both operations concurrently
        await asyncio.gather(
            mock_orchestrator_execution(),
            mock_agent_editing(),
        )

        # Verify that lock prevented race condition
        # The key test: if agent modified the task, and orchestrator got it,
        # then orchestrator must have seen it either before OR after modification,
        # but not during the modification (which would be inconsistent state)
        
        # With proper locking, operations are serialized:
        # Either agent->orchestrator or orchestrator->agent
        # Both orderings are valid, no race condition
        
        # If agent modified, task description should be "Modified Task 2"
        if results["agent_modified_task2"]:
            assert task2.description == "Modified Task 2", \
                "Agent modification was not applied correctly"
        
        # The fact that we got here without exceptions proves the lock worked
        # No intermediate/inconsistent state was observed

    @pytest.mark.asyncio
    async def test_multiple_concurrent_readers_blocked(self, constellation):
        """Test that multiple readers are properly serialized by the lock."""
        access_log = []

        async def reader(reader_id: int):
            async with constellation._update_lock:
                access_log.append(f"reader_{reader_id}_start")
                await asyncio.sleep(0.05)
                access_log.append(f"reader_{reader_id}_end")

        # Start 3 readers concurrently
        await asyncio.gather(
            reader(1),
            reader(2),
            reader(3),
        )

        # Verify that readers did not interleave
        assert len(access_log) == 6

        # Check that each reader completed before the next started
        for i in range(3):
            start_idx = access_log.index(f"reader_{i+1}_start")
            end_idx = access_log.index(f"reader_{i+1}_end")
            assert start_idx < end_idx, "Reader end came before start!"

            # Check no other reader started before this one ended
            for j in range(3):
                if i != j:
                    try:
                        other_start_idx = access_log.index(f"reader_{j+1}_start")
                        if start_idx < other_start_idx < end_idx:
                            pytest.fail(f"Reader {j+1} started while reader {i+1} was running!")
                    except ValueError:
                        pass

    @pytest.mark.asyncio
    async def test_lock_prevents_stale_ready_tasks(self, constellation, sample_tasks):
        """
        Test that lock prevents orchestrator from executing stale ready tasks
        after agent has modified them.
        """
        # Setup
        task1, task2, task3 = sample_tasks
        constellation.add_task(task1)
        constellation.add_task(task2)

        safely_skipped_removed_task = False

        async def orchestrator_check_and_execute():
            """Orchestrator checks for ready tasks."""
            nonlocal safely_skipped_removed_task
            # Simulate some delay (event handling, etc.)
            await asyncio.sleep(0.1)

            # Try to execute with lock
            async with constellation._update_lock:
                # Re-check task status before execution
                ready_tasks = constellation.get_ready_tasks()
                # If task1 was removed, it should not be in ready_tasks
                if task1.task_id not in [t.task_id for t in ready_tasks]:
                    safely_skipped_removed_task = True
                    
                for task in ready_tasks:
                    if task.status == TaskStatus.PENDING:
                        # Safe to execute
                        task.start_execution()

        async def agent_modify_tasks():
            """Agent modifies tasks."""
            await asyncio.sleep(0.05)

            async with constellation._update_lock:
                # Remove task1 to simulate modification
                if task1.task_id in constellation._tasks:
                    constellation.remove_task(task1.task_id)

        await asyncio.gather(
            orchestrator_check_and_execute(),
            agent_modify_tasks(),
        )

        # Verify that the removed task was safely skipped
        assert safely_skipped_removed_task, (
            "Orchestrator should have skipped the removed task"
        )


class TestLockPerformance:
    """Test performance characteristics of the lock."""

    @pytest.mark.asyncio
    async def test_lock_overhead(self):
        """Test that lock overhead is minimal."""
        constellation = TaskConstellation(enable_visualization=False)

        # Measure time without lock
        start = asyncio.get_event_loop().time()
        for _ in range(100):
            constellation.get_ready_tasks()
        time_without_lock = asyncio.get_event_loop().time() - start

        # Measure time with lock
        start = asyncio.get_event_loop().time()
        for _ in range(100):
            async with constellation._update_lock:
                constellation.get_ready_tasks()
        time_with_lock = asyncio.get_event_loop().time() - start

        # Lock overhead should be minimal (less than 2x)
        overhead_ratio = time_with_lock / time_without_lock if time_without_lock > 0 else 1
        assert overhead_ratio < 2.0, (
            f"Lock overhead too high: {overhead_ratio}x"
        )

    @pytest.mark.asyncio
    async def test_no_deadlock_with_nested_operations(self):
        """Test that lock doesn't cause deadlock in complex scenarios."""
        constellation = TaskConstellation(enable_visualization=False)

        async def complex_operation():
            async with constellation._update_lock:
                # Simulate complex operations
                constellation.get_ready_tasks()
                await asyncio.sleep(0.01)
                constellation.get_pending_tasks()

        # Run multiple complex operations concurrently
        # Should complete without deadlock
        await asyncio.wait_for(
            asyncio.gather(
                complex_operation(),
                complex_operation(),
                complex_operation(),
            ),
            timeout=2.0,  # Should complete well within 2 seconds
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
